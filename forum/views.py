import re
from datetime import datetime
# from lxml.html.clean import clean_html  # TODO: use to clean on the way in? this thing adds a p tag so need to strip that
from itertools import groupby

from django.http import HttpResponseRedirect
from django.shortcuts import (
    get_object_or_404,
    render,
)
from django.template import Template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from iommi import (
    Column,
    Form,
    Fragment,
    Page,
    Table,
    style,
)
from iommi.form import bool_parse
from iommi.style import (
    Style,
    register_style,
)
from tri_declarative import dispatch

from forum.models import (
    bytes_from_int,
    Message,
    Room,
    User,
)
from unread import (
    get_user_time,
    is_subscribed,
    set_time,
    set_user_time,
    subscription_data,
)
from unread.models import SubscriptionTypes

register_style(
    'forum',
    Style(
        style.base,
        Form__attrs__class__form=True,
    )
)

PAGE_SIZE = 10


def rooms(request):
    return Table(
        auto__model=Room,
        columns__name__cell__url=lambda row, **_: row.get_absolute_url(),
    )


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
            attrs__style__display='none',
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

        # set_time(item_id=room_pk, namespace='forum/room', time=instance.last_changed_time)
        set_time(identifier=f'forum/room:{room.pk}', time=instance.last_changed_time)

    # noinspection PyShadowingNames
    def redirect(redirect_to, **_):
        return HttpResponseRedirect(room.get_absolute_url() + f'?time={request.GET["time"]}#first_new')

    if message_pk:
        form = Form.edit
    else:
        form = Form.create

    class WritePage(Page):
        header = Fragment(template=Template("""
            <h1>{{ room }}</h1>
        
            <hr>
        
            {% if parent %}
                <table class="listview roomtable">
                    {% include "forum/message.html" with row=parent %}
                </table>
        
                <hr>
            {% endif %}
        """))

        create = form(
            title=None,
            auto__include=['text', 'parent', 'room', 'user'],
            auto__model=Message,
            auto__instance=message,
            fields=dict(
                text__label__template='forum/blank.html',
                parent=non_editable_single_choice(Message, parent_pk),
                room=non_editable_single_choice(Room, room_pk),
                user=non_editable_single_choice(User, request.user.pk),
            ),
            extra__on_save=on_save,
            extra__is_create=message is None,
            extra__redirect=redirect,
            extra__room=room,
            extra__parent=parent,
        )

        script = mark_safe("""
        <script>
            var x = document.getElementById("id_text")
            x.focus();
            x.selectionStart =  x.value.length;
            // TODO: fix this. Used for ctrl+enter I think
            // x.onkeydown = formKeyboardHandler;
        </script>
        """)

        def own_evaluate_parameters(self):
            return dict(page=self, room=room, parent=parent, time=request.GET["time"])

    return WritePage()


@dispatch(
    room_header_template='forum/room-header.html',
)
def render_room(request, room_pk, **kwargs):
    # TODO: @dispatch on this view, and params to be able to customize rendering of the room
    room = get_object_or_404(Room, pk=room_pk)

    user_time = get_user_time(user=request.user, identifier=f'forum/room:{room.pk}')
    show_hidden = bool_parse(request.GET.get('show_hidden', '0'))

    def unread_from_here_href(row: Message, **_):
        params = request.GET.copy()
        params.setlist('unread_from_here', [row.last_changed_time.isoformat()])
        return mark_safe('?' + params.urlencode() + "&")

    if 'time' in request.GET:
        unread2_time = datetime.fromisoformat(request.GET['time'])
    else:
        unread2_time = datetime.now()

    # NOTE: there's a set_user_time at the very bottom of this function
    if 'unread_from_here' in request.GET:
        user_time = datetime.fromisoformat(request.GET['unread_from_here'])

    if user_time < unread2_time:
        unread2_time = user_time

    # TODO: show many pages at once if unread? Right now we show the first unread page.
    def get_start_page(paginator, **_):
        # Find first unread page
        try:
            first_unread_message = Message.objects.filter(room=room, last_changed_time__gte=user_time).order_by('path')[0]
            messages_before_first_unread = room.messages.filter(path__lt=first_unread_message.path).count()
            return messages_before_first_unread // PAGE_SIZE + 1
        except IndexError:
            return paginator.number_of_pages

    messages = Message.objects.filter(room__pk=room_pk).prefetch_related('user', 'room')
    if not show_hidden:
        messages = messages.filter(visible=True)

    def is_unread(row, **_):
        return row.last_changed_time >= user_time

    def is_unread2(row, **_):
        return row.last_changed_time >= unread2_time and not is_unread(row=row)

    def preprocess_rows(rows, table, **_):
        rows = list(rows)
        first_new = None
        for d in rows:
            if is_unread(row=d):
                first_new = d
                break

        table.extra.unread = first_new is not None

        first_new_or_last_message = first_new
        if first_new_or_last_message is None and rows:
            first_new_or_last_message = rows[-1]

        if first_new_or_last_message is not None:
            # This is used by the view
            first_new_or_last_message.first_new = True

        return rows

    class RoomPage(Page):

        table = Table(
            template='forum/room.html',
            title=None,
            auto__rows=messages,
            auto__exclude=['path'],
            columns__unread_from_here_href=Column(attr=None, cell__value=unread_from_here_href),
            preprocess_rows=preprocess_rows,
            header__template=Template(''),
            row__template=get_template('forum/message.html'),
            row__attrs__class=dict(
                indent_0=lambda row, **_: row.indent == 0,
                message=True,
                current_user=lambda row, **_: request.user == row.user,
                other_user=lambda row, **_: request.user != row.user,
                unread=is_unread,
                unread2=is_unread2,
            ),
            attrs=dict(
                cellpadding='0',
                cellspacing='0',
                id='first_newtable',
                align='center',
                class__roomtable=True,
            ),
            paginator=dict(
                min_page_size=10,
                template='forum/room-footer.html',
                page=get_start_page,
            ),
            page_size=PAGE_SIZE,
        )

        def own_evaluate_parameters(self):
            return dict(
                page=self,
                room=room,
                show_hidden=show_hidden,
                time=unread2_time or user_time,
                is_subscribed=is_subscribed(user=request.user, identifier=f'forum/room:{room.pk}'),
                is_mobile=request.user_agent.is_mobile,
                **kwargs,
            )

    result = RoomPage().bind(request=request).render_to_response()
    if 'unread_from_here' not in request.GET:
        user_time = datetime.now()

    set_user_time(user=request.user, identifier=f'forum/room:{room.pk}', time=user_time)
    return result


def view_room(request, room_pk):
    return render_room(request, room_pk=room_pk)


def subscriptions(request, template_name='forum/subscriptions.html'):
    subscription_data_by_identifier = subscription_data(user=request.user)

    # TODO: these two dicts should be something you register into
    object_lookups = {
        'forum/room': lambda pks: {str(x.pk): x for x in Room.objects.filter(pk__in=pks)},
    }

    title_by_prefix = {
        'forum/room': 'Rooms',
    }

    has_unread = any(x.is_unread for x in subscription_data_by_identifier.values())

    result = []

    for prefix, items in groupby(subscription_data_by_identifier.keys(), key=lambda k: k[0]):
        object_by_suffix = object_lookups[prefix](pks=(x[1] for x in items))

        active = []
        passive = []

        for identifier, data in subscription_data_by_identifier.items():
            obj = object_by_suffix[identifier[1]]
            x = dict(
                url=obj.get_absolute_url() + '#first_new',
                unread=data.is_unread,
                name=obj.name,
                system_time=data.item_time,
                user_time=data.user_time,
                object=obj,
                identifier=':'.join(identifier),
            )
            if data.subscription_type == SubscriptionTypes.active.name:
                active.append(x)
            else:
                assert data.subscription_type == SubscriptionTypes.passive.name
                passive.append(x)

        active = sorted(active, key=lambda x: x['name'].lower())
        passive = sorted(passive, key=lambda x: x['name'].lower())

        result.append(dict(
            title=title_by_prefix[prefix],
            active=active,
            passive=passive
        ))

    return render(
        request,
        template_name=template_name,
        context=dict(
            result=result,
            has_unread=has_unread,
            is_mobile=request.user_agent.is_mobile,
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
