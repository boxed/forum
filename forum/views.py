import json
import re
from _sha1 import sha1
from base64 import b64encode
from datetime import datetime

# from lxml.html.clean import clean_html  # TODO: use to clean on the way in? this thing adds a p tag so need to strip that
from django.contrib.auth import authenticate
from django.db.models import BinaryField
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import Template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from tri.form import register_field_factory, Form, Field, Link, bool_parse
from tri.form.compat import render
from tri.form.views import create_or_edit_object
from tri.table import render_table_to_response, Column

from forum import RoomPaginator, PAGE_SIZE
from forum.models import Room, Message, User, bytes_from_int
from unread import get_time, set_time, set_time_for_system, DEFAULT_TIME, unread_items, get_times_by_system, get_times_for_user_by_system
from unread.models import Subscription, SubscriptionTypes

register_field_factory(BinaryField, lambda **_: None)


Form.Meta.base_template = 'forum/base.html'


def login(request):
    from django.contrib.auth import login

    if request.user.is_authenticated:
        return HttpResponse('Already logged in')

    class LoginForm(Form):
        username = Field()
        password = Field.password()
        next = Field.hidden(initial=request.GET.get('next', '/'))

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

                try:
                    username = User.objects.get(username=username)
                    if b64encode(sha1(password.encode()).digest()).decode() == user.password:
                        user.set_password(password)  # upgrade password
                        user.save()
                    authenticate(request=request, username=username, password=password)
                except User.DoesNotExist:
                    pass

            return False

    form = LoginForm(request)

    if request.method == 'POST' and form.is_valid():
        login(request, form.extra.user)
        return HttpResponseRedirect(form.fields_by_name['next'].value or '/')

    return render(request, 'forum/login.html', context=dict(form=form, url='/'))


def index(request):
    if request.user_agent.is_mobile:
        return subscriptions(request, template_name='forum/index_mobile.html')
    return render(request, template_name='forum/index.html')


def welcome(request):
    return render(request, template_name='forum/welcome.html')


def rooms(request):
    return render_table_to_response(request, table__model=Room)


def pre_format(s):
    s = s.replace('\t', '    ')
    s = re.sub('^( +)', lambda m: '&nbsp;' * len(m.groups()[0]), s, flags=re.MULTILINE)
    s = s.replace('\n', '<br>')
    return mark_safe(s)


def parse_datetime(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')


def get_object_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


def write(request, room_pk, message_pk=None):
    message = get_object_or_none(Message, pk=message_pk)
    room = get_object_or_404(Room, pk=room_pk)
    parent_pk = request.GET.get('parent')
    parent = get_object_or_404(Message, pk=parent_pk) if parent_pk is not None else None
    assert parent is None or parent.room_id == room_pk

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

        set_time_for_system(id=room_pk, system='forum_room', time=instance.last_changed_time)

    # noinspection PyShadowingNames
    def redirect(request, redirect_to, form):
        del form
        del redirect_to
        return HttpResponseRedirect(room.get_absolute_url() + f'?time={request.GET["time"]}#first_new')

    return create_or_edit_object(
        request=request,
        model=Message,
        instance=message,
        is_create=message is None,
        on_save=on_save,
        form__field=dict(
            text=Field.textarea,
            text__label_template='forum/blank.html',
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
        template_name='forum/write.html',
    )


def view_room(request, room_pk):
    # TODO: @dispatch on this view, and params to be able to customize rendering of the room
    room = get_object_or_404(Room, pk=room_pk)

    user_time = get_time(user=request.user, system='forum_room', id=room_pk)
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
        user_time = datetime.fromisoformat(request.GET['unread_from_here'])

    # TODO: show many pages at once if unread? Right now we show the first unread page.
    start_page = None
    if 'page' not in request.GET:
        # Find first unread page
        try:
            first_unread_message = Message.objects.filter(room=room, last_changed_time__gte=user_time).order_by('path')[0]
            messages_before_first_unread = room.message_set.filter(path__lt=first_unread_message.path).count()
            start_page = messages_before_first_unread // PAGE_SIZE
        except IndexError:
            pass

    messages = Message.objects.filter(room__pk=room_pk).prefetch_related('user', 'room')
    if not show_hidden:
        messages = messages.filter(visible=True)

    def is_unread(row, **_):
        return row.last_changed_time >= user_time

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
        template=get_template('forum/room.html'),
        paginator=RoomPaginator(messages),
        context=dict(
            room=room,
            show_hidden=show_hidden,
            time=unread2_time or user_time,
            is_subscribed=False,  # TODO:
        ),
        table__data=messages,
        table__exclude=['path'],
        table__extra_fields=[
            Column(name='unread_from_here_href', attr=None, cell__value=unread_from_here_href),
        ],
        table__preprocess_data=preprocess_data,
        table__header__template=Template(''),
        table__row__template=get_template('forum/message.html'),
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
        table__paginator__template='forum/blank.html',
        page=start_page,
    )
    if 'unread_from_here' not in request.GET:
        user_time = datetime.now()

    set_time(user=request.user, system='forum_room', id=room.pk, time=user_time)
    return result


def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect('/login/')


def subscriptions(request, template_name='forum/subscriptions.html'):
    s = list(Subscription.objects.filter(user=request.user, system='forum_room'))

    room_by_pk = {room.pk: room for room in Room.objects.filter(pk__in=[x.data for x in s])}

    system_time_by_id = get_times_by_system(system='forum_room', ids=[x.data for x in s])
    user_time_by_id = get_times_for_user_by_system(user=request.user, system='forum_room', ids=[x.data for x in s])

    has_unread = False

    active = []
    passive = []

    for subscription in s:
        system_time = system_time_by_id.get(subscription.data, DEFAULT_TIME)
        user_time = user_time_by_id.get(subscription.data, DEFAULT_TIME)
        room = room_by_pk[subscription.data]
        x = dict(
            url=room.get_absolute_url() + '#first_new',
            unread=user_time <= system_time,
            name=room.name,
            system_time=system_time,
            user_time=user_time,
            object=room,
        )
        if x['unread']:
            has_unread = True
        if subscription.subscription_type == SubscriptionTypes.active.name:
            active.append(x)
        else:
            assert subscription.subscription_type == SubscriptionTypes.passive.name
            passive.append(x)

    active = sorted(active, key=lambda x: x['name'].lower())
    passive = sorted(passive, key=lambda x: x['name'].lower())

    return render(
        request,
        template_name=template_name,
        context=dict(
            active=active,
            passive=passive,
            has_unread=has_unread,
        )
    )


def delete(request, room_pk, message_pk):
    room = get_object_or_404(Room, pk=room_pk)
    message = get_object_or_404(Message, pk=message_pk)
    assert room.pk == message.room_id
    if request.method == 'POST':
        message.visible = False
        message.last_changed_by = request.user
        message.save()
        return HttpResponseRedirect(request.GET.get('next', message.room.get_absolute_url() + '#first_new'))
    else:
        return render(request, template_name='forum/delete.html', context=dict(next=request.META.get('HTTP_REFERER'), message=message))


@csrf_exempt
def api_unread_simple(request):
    data = request.POST if request.method == 'POST' else request.GET
    if request.user.is_authenticated or authenticate(request=request, username=data['username'], password=data['password']):
        unread = unread_items(user=request.user)
        if unread:
            return HttpResponse(f'{len(unread)}')
        else:
            return HttpResponse(status=204)
    else:
        return HttpResponse('Failed to log in', status=403)


def api_unread(request):
    return HttpResponse(json.dumps(unread_items(user=request.user)), content_type='application/json')
