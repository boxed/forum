import re
from datetime import datetime

# from lxml.html.clean import clean_html  # TODO: use to clean on the way in? this thing adds a p tag so need to strip that
from django.contrib.auth import authenticate
from django.db.models import BinaryField
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import Template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from tri.form import register_field_factory, Form, Field, Link, bool_parse
from tri.form.compat import render
from tri.form.views import create_or_edit_object
from tri.table import render_table_to_response, Column

from forum2.forum import RoomPaginator, PAGE_SIZE
from forum2.forum.models import Room, Message, User, Time, bytes_from_int

register_field_factory(BinaryField, lambda **_: None)


Form.Meta.base_template = 'base.html'


def login(request):
    from django.contrib.auth import login

    if request.user.is_authenticated:
        return HttpResponse('Already logged in')

    class LoginForm(Form):
        username = Field()
        password = Field.password()

        def is_valid(self):
            if not super(LoginForm, self).is_valid():
                return False

            username = self.fields_by_name['username'].value
            password = self.fields_by_name['password'].value

            if username and password:
                user = User.objects.get(username=username)
                self.extra.user = user
                if authenticate(request=request, username=username, password=password):
                    return True

            return False

    form = LoginForm(request)

    if request.method == 'POST' and form.is_valid():
        login(request, form.extra.user)
        return HttpResponse('OK')

    return render(request, 'login.html', context=dict(form=form, url='/'))


def rooms(request):
    return render_table_to_response(request, table__model=Room)


def pre_format(s):
    s = s.replace('\t', '    ')
    s = re.sub('^( +)', lambda m: '&nbsp;' * len(m.groups()[0]), s, flags=re.MULTILINE)
    s = s.replace('\n', '<br>')
    return mark_safe(s)


def parse_datetime(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')


def write(request, room_pk):
    parent_pk = request.GET.get('parent')
    parent = Message.objects.get(pk=parent_pk) if parent_pk is not None else None
    assert parent is None or parent.room_id == room_pk
    room = Room.objects.get(pk=room_pk)

    def non_editable_single_choice(model, pk):
        return dict(
            container__attrs__style__display='none',
            editable=False,
            choices=model.objects.filter(pk=pk) if pk is not None else model.objects.none(),
            initial=model.objects.get(pk=pk) if pk is not None else None,
        )

    def on_save(instance, **_):
        if not instance.path:
            if instance.parent:
                instance.path = instance.parent.path + bytes_from_int(instance.pk)
            else:
                instance.path = bytes_from_int(instance.pk)

            instance.save()

        if instance.parent and not instance.parent.has_replies:
            Message.objects.filter(pk=instance.parent.pk).update(has_replies=True)  # Don't use normal save() to avoid the auto_add field update

    # noinspection PyShadowingNames
    def redirect(request, redirect_to, form):
        del form
        return HttpResponseRedirect(redirect_to + f'?time={request.GET["time"]}#first_new')

    return create_or_edit_object(
        request=request,
        model=Message,
        is_create=True,
        on_save=on_save,
        form__field=dict(
            text=Field.textarea,
            text__label_template='blank.html',
            parent=non_editable_single_choice(Message, parent_pk),
            room=non_editable_single_choice(Room, room_pk),
            user=non_editable_single_choice(User, request.user.pk),
        ),
        form__links=[Link.submit()],
        redirect=redirect,
        render=render,
        form__include=['text', 'parent', 'room', 'user'],
        render__context__room=room,
        render__context__parent=parent,
        template_name='room/write.html',
    )


def view_room(request, room_pk):
    room = get_object_or_404(Room, pk=room_pk)

    t = Time.objects.get_or_create(user=request.user, data=room_pk, system='room', defaults=dict(time=datetime(2001, 1, 1)))[0]
    show_hidden = bool_parse(request.GET.get('show_hidden', '0'))

    def unread_from_here_href(row: Message, **_):
        params = request.GET.copy()
        params.setlist('unread_from_here', [row.last_changed_time.isoformat()])
        return mark_safe('?' + params.urlencode() + "&")

    if 'time' in request.GET:
        unread2_time = datetime.fromisoformat(request.GET['time'])
    else:
        unread2_time = datetime.now()

    # NOTE: there's a t.save() at the very bottom of this function
    if 'unread_from_here' in request.GET:
        t.time = datetime.fromisoformat(request.GET['unread_from_here'])

    # TODO: show many pages at once if unread? Right now we show the first unread page.
    start_page = None
    if 'page' not in request.GET:
        # Find first unread page
        try:
            first_unread_message = Message.objects.filter(room=room, last_changed_time__gte=t.time).order_by('path')[0]
            messages_before_first_unread = room.message_set.filter(path__lt=first_unread_message.path).count()
            start_page = messages_before_first_unread // PAGE_SIZE
        except IndexError:
            pass

    messages = Message.objects.filter(room__pk=room_pk).prefetch_related('user', 'room')
    if not show_hidden:
        messages = messages.filter(visible=True)

    paginator = RoomPaginator(messages)

    def is_unread(row, **_):
        return row.last_changed_time >= t.time

    def is_unread2(row, **_):
        return row.last_changed_time >= unread2_time and not is_unread(row=row)

    def preprocess_data(data, table, **_):
        data = list(data)
        first_new = None
        for d in data:
            if is_unread(row=d):
                first_new = d
                break

        table.extra.unread = first_new is not None

        first_new_or_last_message = first_new
        if first_new_or_last_message is None and data:
            first_new_or_last_message = data[-1]

        if first_new_or_last_message is not None:
            # This is used by the view
            first_new_or_last_message.first_new = True

        return data

    result = render_table_to_response(
        request,
        template=get_template('room.html'),
        paginator=paginator,
        context=dict(
            room=room,
            show_hidden=show_hidden,
            time=unread2_time or t.time,
            is_subscribed=False,  # TODO:
        ),
        table__data=messages,
        table__exclude=['path'],
        table__extra_fields=[
            Column(name='unread_from_here_href', attr=None, cell__value=unread_from_here_href),
        ],
        table__preprocess_data=preprocess_data,
        table__header__template=Template(''),
        table__row__template=get_template('room/message.html'),
        table__row__attrs=dict(
            # id=lambda row, **_: row.pk,
            class__indent_0=lambda row, **_: row.indent == 0,
            class__message=True,
            class__current_user=lambda row, **_: request.user == row.user,
            class__other_user=lambda row, **_: request.user != row.user,
            class__unread=is_unread,
            class__unread2=is_unread2,
        ),
        table__attrs__cellpadding='0',
        table__attrs__cellspacing='0',
        table__attrs__id='first_newtable',
        table__attrs__align='center',
        table__attrs__class__roomtable=True,
        page=start_page,
    )
    if 'unread_from_here' not in request.GET:
        t.time = datetime.now()

    t.save()
    return result


def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect('/login/')


def delete(request, room_pk, message_pk):
    room = get_object_or_404(Room, pk=room_pk)
    message = get_object_or_404(Message, pk=message_pk)
    assert room.pk == message.room_id
    if request.method == 'POST':
        message.visible = False
        message.last_changed_by = request.user
        message.save()
        return HttpResponseRedirect(request.GET.get('next', message.room.get_absolute_url() + '#firstnew'))
    else:
        return render(request, template_name='delete.html', context=dict(next=request.headers.get('HTTP_REFERER'), message=message))
