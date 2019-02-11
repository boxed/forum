import base64
import hashlib
import os
import re
from datetime import datetime

from django.db import connection, transaction
from django.db.models import Q, BinaryField
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from tri.form import register_field_factory, Form, Field
from tri.form.compat import render
from tri.form.views import create_or_edit_object
from tri.struct import Struct
from tri.table import render_table_to_response, Column

# from forum2.forum import AreaPaginator
from forum2.forum import AreaPaginator
from forum2.forum.models import Area, Message, User, Time, HackySingleSignOn, bytes_from_int

register_field_factory(BinaryField, lambda **_: None)


Form.Meta.base_template = 'base.html'


def convert_jsp_to_django(request, input_filename):
    def convert(jsp):
        simple_replacements = [
            ('<%@page contentType="text/html;charset=UTF-8"%>', ''),
            ('<%--', '{#'),
            ('--%>', '#}'),
            ('<%@ include file=', '{% include '),
            ('<%', '{%'),
            ('%>', '%}'),
            ('javascript:', ''),
            ('</ww:if>', '{% endif %}'),
            ('</ww:else>', '{% endif %}'),
            ('<ww:else>', '{% else %}'),
            ('<sk:indent/>', '{{ row.indent_px }}'),
            ('.jsp', '.html'),
            ('cssClass(.)', 'bound_row.unread_css_class.value'),
            ('bodyEmpty(.)', 'not bound_row.body.value'),
            (' currentUser ', ' request.user '),
            (' currentUser.', ' request.user.'),
            ('{%@ taglib uri="wiki" prefix="wiki"  %}{%@ taglib uri="sk-internal" prefix="sk" %}{%@ taglib uri="webwork" prefix="ww" %}', ''),
            ('<sk:hr />', '<img src="/public/img/color.gif" width="100%" height="13" alt="---">'),
            ('/public/', '/static/'),
            ('/_common/', '/static/'),
            ('{% include "/', '{% include "'),
            ('  ', '    '),
            ('"/forum.css"', '/static/forum.css'),
            (' || ', ' or '),
            (' == true', ''),
            ('<p />', '<p></p>'),
            ('</ww:url>', ''),
            ("'", ''),
        ]

        for x, y in simple_replacements:
            jsp = jsp.replace(x, y)

        regex_replacements = [
            ('<ww:print value="@(.*?)"\s*/>', lambda m: f'{{{{ {m.groups()[0].replace("/", ".")} }}}}'),
            ('<ww:print value="(.*?)"\s*/>', lambda m: f'{{{{ {m.groups()[0].replace("/", ".")} }}}}'),
            ('<ww:url value="\'(.*?)\'"/>', '\\1'),
            ('<ww:if test="(.*?)">', lambda m: f'{{% if {m.groups()[0].replace("/", ".")} %}}'),
            ('<ww:property id="(.*?)" value="(.*?)"/>', '{% set \\1 = \\2 %}'),
            ('{% endif %}\s*{% else %}', '{% else %}'),
            ('{%@ page import=".*?" %}', ''),
            ('<jsp:useBean .*?>', ''),
            ('{%\w*\n%}', ''),
            ('<ww:param name="(.*?)" value="(.*?)"\w*/>', '&\\1=\\2'),
            ('<ww:url value="(.*?)">', '/\\1'),
            ('<sk:a value="(.*?)" (.*?)>(.*?)</sk:a>', '<a href="\\1\\3" \\2>foo</a>')
        ]

        for x, y in regex_replacements:
            jsp = re.sub(x, y, jsp)

        simple_replacements2 = [
            ('area.View.action&', '/areas/{{ area.pk }}/?'),
            ('&areaID=area/id', '')
        ]

        for x, y in simple_replacements2:
            jsp = jsp.replace(x, y)

        jsp = jsp.strip()
        return jsp

    filename = os.path.join(os.path.dirname(__file__), 'jinja2', 'area', input_filename)
    with open(filename) as f:
        jsp = f.read()
    with open(filename.replace('.jsp', '.html'), 'w') as f:
        f.write(convert(jsp))
    return HttpResponse('OK')


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
                x = hashlib.sha1()
                x.update(password.encode())
                encoded_password = base64.b64encode(x.digest()).decode()
                if user.password == encoded_password:
                    return True

            return False

    form = LoginForm(request)

    if request.method == 'POST' and form.is_valid():
        login(request, form.extra.user)

        # TODO: upgrade password hash

        HackySingleSignOn.objects.filter(user=form.extra.user).delete()
        HackySingleSignOn.objects.create(user=form.extra.user, session_key=request.session.session_key)

        return HttpResponse('OK')

    return render(request, 'login.html', context=dict(form=form, url='/'))


def areas(request):
    return render_table_to_response(request, table__model=Area)


def pre_format(s):
    s = re.sub('^( +)', lambda m: '&nbsp;' * len(m.groups()[0]), s)
    s.replace('\n', '<br>')
    return mark_safe(s)


def parse_datetime(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')


def write(request, area_pk):
    parent_pk = request.GET.get('parent')
    parent = Message.objects.get(pk=parent_pk) if parent_pk is not None else None
    assert parent is None or parent.area_id == area_pk
    area = Area.objects.get(pk=area_pk)

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

    return create_or_edit_object(
        request=request,
        model=Message,
        is_create=True,
        on_save=on_save,
        form__field=dict(
            body=Field.textarea,
            body__required=False,
            parent=non_editable_single_choice(Message, parent_pk),
            area=non_editable_single_choice(Area, area_pk),
            user=non_editable_single_choice(User, request.user.pk),
        ),
        render=render,
        form__include=['subject', 'body', 'parent', 'area', 'user'],
        render__context__area=area,
        render__context__parent=parent,
        template_name='area/write.html',
    )


def area(request, area_pk):
    t = Time.objects.get_or_create(user=request.user, data=area_pk, system='area', defaults=dict(time=datetime(2001, 1, 1)))[0]
    user_time = t.time
    show_hidden = False

    def unread_from_here_href(row: Message, **_):
        GET = request.GET.copy()
        GET.setlist('unread_from_here', [row.last_changed_time.timestamp()])
        return mark_safe('?' + GET.urlencode() + "&")

    if 'unread_from_here' in request.GET:
        t.time = datetime.fromtimestamp(float(request.GET['unread_from_here']))
        user_time = t.time
        t.save()
    else:
        user_time = t.time
        t.time = datetime.now()

    # TODO: show first unread page, plus all other pages from that point onwards, use paginate_by?
    # First unread message:
    try:
        first_unread_message = Message.objects.filter(area__pk=4, last_changed_time__gte=t.time).order_by('path')[0]

    except IndexError:
        first_unread_message = None

    area = Area.objects.get(pk=area_pk)
    # TODO: editable: if there is no reply

    messages = Message.objects.filter(area__pk=area_pk).prefetch_related('user', 'area')
    if not show_hidden:
        messages = messages.filter(visible=True)

    paginator = AreaPaginator(messages, per_page=40)

    result = render_table_to_response(
        request,
        template=get_template('area.html'),
        paginator=paginator,
        context=dict(
            area=area,
            areaInfo=Struct(
                firstnewID=None,  # TODO:
            ),
            showHidden=show_hidden,
            unread=True,  # TODO:
            showingUnread=True,  # TODO:
            time=user_time,
            start_page='??? TODO ???',  # TODO: implement loading multiple pages if needed to get all unread
            is_subscribed=False,  # TODO:
        ),
        table__data=messages,
        table__exclude=['path'],
        table__extra_fields=[
            Column(name='unread_from_here_href', attr=None, cell__value=unread_from_here_href),
        ],
        table__column__subject__cell__format=lambda value, **_: pre_format(value),
        table__column__body__cell__format=lambda value, **_: pre_format(value),
        table__header__template=Template(''),
        table__row__template=get_template('area/dynamic-message.html'),
        table__row__attrs=dict(
            id=lambda row, **_: row.pk,
            class__indent_0=lambda row, **_: row.indent == 0,
            class__message=True,
            class__current_user=lambda row, **_: request.user == row.user,
            class__other_user=lambda row, **_: request.user != row.user,
            class__unread=lambda row, **_: user_time <= row.last_changed_time,
            # TODO: unread2

        ),
        table__attrs__cellpadding='0',
        table__attrs__cellspacing='0',
        table__attrs__id='firstnewtable',
        table__attrs__align='center',
        table__attrs__class__areatable=True,
    )
    t.save()
    return result


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

    return HttpResponse('done')


@transaction.atomic
def import_times(request):
    Time.objects.all().delete()

    cursor = connection.cursor()
    cursor.execute('select `user_id`, `data`, `system`, `time` from `times`')

    for row in cursor.fetchall():
        Time.objects.create(user_id=row[0], data=row[1], system=row[2], time=row[3])

    return HttpResponse('done')


def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect('/login/')
