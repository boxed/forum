import re

from django.db.models import Q
from django.http import HttpResponse
from django.template import Template
from django.utils.safestring import mark_safe
from tri.table import render_table_to_response, Column

from forum2.forum.models import Area, Message


def areas(request):
    return render_table_to_response(request, table__model=Area)


def pre_format(s):
    s = re.sub('^( +)', lambda m: '&nbsp;' * len(m.groups()[0]), s)
    s.replace('\n', '<br>')
    return mark_safe(s)


def area(request, pk):
    # area = Area.objects.get(pk=pk)
    return render_table_to_response(
        request,
        template='area.html',
        table__data=Message.objects.filter(area__pk=pk).prefetch_related('user'),
        table__include=['subject', 'body'],
        table__extra_fields=[
            Column(name='currentuser_or_otheruser', cell__value=lambda row, **_: 'currentuser' or 'otheruser')
        ],
        table__column__subject__cell__format=lambda value, **_: pre_format(value),
        table__column__body__cell__format=lambda value, **_: pre_format(value),
        table__header__template=Template(''),
        table__row__template='message.html',
    )


def bytes_from_int(i):
    return i.to_bytes(length=64 // 8, byteorder='big')


def update_batch(qs):
    count = 0
    for message in qs:
        if message.parent_id is None:
            message.path = bytes_from_int(message.pk)
        else:
            message.path = message.parent.path + bytes_from_int(message.pk)

        message.save()
        count += 1
    return count


def update_message_path(request):
    update_batch(Message.objects.filter(path=None, parent=None))
    while update_batch(Message.objects.filter(path=None).filter(Q(parent=None) | Q(parent__path__isnull=False))):
        pass

    return HttpResponse(f'done')
