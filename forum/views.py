from itertools import groupby
from urllib.parse import (
    urlparse,
    parse_qs,
    urlencode,
)

from django.http import HttpResponseRedirect
from django.shortcuts import (
    get_object_or_404,
    render,
)
from django.template import Template
from django.template.loader import get_template
from django.urls import reverse
from django.utils.safestring import mark_safe
from iommi import (
    Column,
    Form,
    Fragment,
    html,
    Page,
    Table,
)
from iommi.form import bool_parse
from iommi.reinvokable import reinvokable

from forum.models import (
    bytes_from_int,
    Message,
    Room,
    User,
)
from forum.utils import (
    get_object_or_none,
    pre_format,
    pre_format_legacy,
)
from forum2 import decode_url
from unread import (
    is_subscribed,
    set_time,
    subscription_data,
    unread_handling,
)
from unread.models import SubscriptionTypes

PAGE_SIZE = 10


def rooms(request):
    return Table(
        auto__model=Room,
        columns__name__cell__url=lambda row, **_: row.get_absolute_url(),
    )


def write__on_save(instance, **_):
    if not instance.path:
        if instance.parent:
            instance.path = instance.parent.path + bytes_from_int(instance.pk)
        else:
            instance.path = bytes_from_int(instance.pk)

        instance.save()

    if instance.parent and not instance.parent.has_replies:
        Message.objects.filter(pk=instance.parent.pk).update(has_replies=True)  # Don't use normal save() to avoid the auto_add field update

    # set_time(item_id=room_pk, namespace='forum/room', time=instance.last_changed_time)
    set_time(identifier=f'forum/room:{instance.room.pk}', time=instance.last_changed_time)


def write__field__non_editable_single_choice(model, pk):
    return dict(
        attrs__style__display='none',
        editable=False,
        choices=model.objects.filter(pk=pk) if pk is not None else model.objects.none(),
        initial=model.objects.get(pk=pk) if pk is not None else None,
    )


@decode_url(Room)
@unread_handling(Room)
def write(request, *, room, message_pk=None, unread_data):
    message = get_object_or_none(Message, pk=message_pk)
    parent_pk = request.GET.get('parent')
    parent = get_object_or_404(Message, pk=parent_pk) if parent_pk is not None else None
    assert parent is None or parent.room_id == room.pk

    def redirect(request, **_):
        target = urlparse(request.META['HTTP_REFERER'])
        qs = parse_qs(target.query)
        qs['time'] = {request.GET["time"]}
        return HttpResponseRedirect(f'{target.path}?{urlencode(qs, doseq=True)}#first_new')

    if message_pk:
        form = Form.edit
    else:
        form = Form.create

    class WritePage(Page):
        create = form(
            title=None,
            auto__include=['text', 'parent', 'room', 'user'],
            auto__model=Message,
            auto__instance=message,
            attrs__action=request.get_full_path(),
            fields=dict(
                text__label__template='forum/blank.html',
                parent=write__field__non_editable_single_choice(Message, parent_pk),
                room=write__field__non_editable_single_choice(Room, room.pk),
                user=write__field__non_editable_single_choice(User, request.user.pk),
                text__input__attrs__style__width='100%',
            ),
            extra__on_save=write__on_save,
            extra__is_create=message is None,
            extra__redirect=redirect,
            extra__room=room,
            extra__parent=parent,
        )

        script = mark_safe('<script>auto_select();</script>')

        def own_evaluate_parameters(self):
            return dict(page=self, room=room, parent=parent, time=request.GET["time"], unread_data=unread_data)

    return WritePage()


def room__unread_from_here_href(table, row: Message, **_):
    params = table.get_request().GET.copy()
    params.setlist('unread_from_here', [row.last_changed_time.isoformat()])
    return mark_safe('?' + params.urlencode() + "&")


# TODO: show many pages at once if unread? Right now we show the first unread page.
def room__get_start_page(paginator, room, unread_data, **_):
    # Find first unread page
    try:
        first_unread_message = Message.objects.filter(room=room, last_changed_time__gte=unread_data.user_time).order_by('path')[0]
        messages_before_first_unread = room.messages.filter(path__lt=first_unread_message.path).count()
        return messages_before_first_unread // PAGE_SIZE + 1
    except IndexError:
        return paginator.number_of_pages


def room__rows(table, room, **_):
    messages = Message.objects.filter(room=room).prefetch_related('user', 'room')
    table.extra.show_hidden = bool_parse(table.get_request().GET.get('show_hidden', '0'))
    if not table.extra.show_hidden:
        messages = messages.filter(visible=True)
    return messages


def room__preprocess_rows(rows, table, unread_data, **_):
    rows = list(rows)
    first_new = None
    for d in rows:
        if unread_data.is_unread(d.last_changed_time):
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


class Messages(Table):
    class Meta:
        title = None
        auto__model = Message
        auto__exclude = ['path']
        rows = room__rows
        columns__unread_from_here_href = Column(attr=None, cell__value=room__unread_from_here_href)
        # Keep backwards compatibility with old (super unsafe!) forum, but use safe markdown for new messages
        columns__text__cell__format = lambda value, row, **_: pre_format(value) if row.time_created.year > 2015 else pre_format_legacy(value)
        columns__text__cell__tag = None
        preprocess_rows = room__preprocess_rows
        header__template = Template('')
        row__template = get_template('forum/message.html')
        row__attrs__class = dict(
            indent_0=lambda row, **_: row.indent == 0,
            message=True,
            current_user=lambda table, row, **_: table.get_request().user == row.user,
            other_user=lambda table, row, **_: table.get_request().user != row.user,
            unread=lambda row, unread_data, **_: unread_data.is_unread(row.last_changed_time),
            unread2=lambda row, unread_data, **_: unread_data.is_unread2(row.last_changed_time),
        )
        attrs = dict(
            cellpadding='0',
            cellspacing='0',
            id='first_newtable',
            align='center',
            class__roomtable=True,
        )
        paginator = dict(
            min_page_size=10,
            template='forum/room-footer.html',
            page=room__get_start_page,
            show_always=True,
        )
        page_size = PAGE_SIZE


class RoomPage(Page):
    @reinvokable
    def __init__(
            self,
            room,
            unread_data,
            **kwargs
    ):
        self.room = room
        self.unread_data = unread_data
        super(RoomPage, self).__init__(**kwargs)

    header = Fragment(template='forum/room-header.html')

    table = Messages()

    hr = html.hr()

    refresh = html.script(
        'start_subscription_refresh_subpage();',
        include=lambda request, **_: request.user_agent.is_mobile,
    )

    def own_evaluate_parameters(self):
        return dict(
            page=self,
            room=self.room,
            unread_data=self.unread_data,
            unread_identifier=self.unread_data.unread_identifier,
            title=self.room.name,
            time=self.unread_data.unread2_time or self.unread_data.user_time,  # TODO: handle this in UnreadData?
            is_subscribed=is_subscribed,
        )


@decode_url(Room)
@unread_handling(Room)
def view_room(request, unread_data, room):
    return RoomPage(room=room, unread_data=unread_data)


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
