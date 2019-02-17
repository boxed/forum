import base64
import hashlib
import os
import re
from datetime import datetime

#from lxml.html.clean import clean_html  # TODO: use to clean on the way in? this thing adds a p tag so need to strip that
from django.db import connection, transaction
from django.db.models import Q, BinaryField
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Template
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from tri.form import register_field_factory, Form, Field
from tri.form.compat import render
from tri.form.views import create_or_edit_object
from tri.table import render_table_to_response, Column

# from forum2.forum import AreaPaginator
from forum2.forum import AreaPaginator, PAGE_SIZE
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
        HackySingleSignOn.objects.create(user=form.extra.user, session_key=request.session.session_key, expire_data=request.session.expire_date)

        return HttpResponse('OK')

    return render(request, 'login.html', context=dict(form=form, url='/'))


def areas(request):
    return render_table_to_response(request, table__model=Area)


def pre_format(s):
    s = s.replace('\t', '    ')
    s = re.sub('^( +)', lambda m: '&nbsp;' * len(m.groups()[0]), s, flags=re.MULTILINE)
    s = s.replace('\n', '<br>')
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

        if instance.parent and not instance.parent.has_replies:
            Message.objects.filter(pk=instance.parent.pk).update(has_replies=True)  # Don't use normal save() to avoid the auto_add field update

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
        redirect=lambda request, redirect_to, form: HttpResponseRedirect(redirect_to + f'?time={request.GET["time"]}#firstnew'),
        render=render,
        form__include=['subject', 'body', 'parent', 'area', 'user'],
        render__context__area=area,
        render__context__parent=parent,
        template_name='area/write.html',
    )


def area(request, area_pk):
    t = Time.objects.get_or_create(user=request.user, data=area_pk, system='area', defaults=dict(time=datetime(2001, 1, 1)))[0]
    show_hidden = False

    def unread_from_here_href(row: Message, **_):
        GET = request.GET.copy()
        GET.setlist('unread_from_here', [row.last_changed_time.isoformat()])
        return mark_safe('?' + GET.urlencode() + "&")

    if 'time' in request.GET:
        unread2_time = datetime.fromisoformat(request.GET['time'])
    else:
        unread2_time = datetime.now()

    # NOTE: there's a t.save() at the very bottom of this function
    if 'unread_from_here' in request.GET:
        t.time = datetime.fromisoformat(request.GET['unread_from_here'])

    area = Area.objects.get(pk=area_pk)

    # TODO: show many pages at once if unread? Right now we show the first unread page.
    start_page = None
    if 'page' not in request.GET:
        # Find first unread page
        try:
            first_unread_message = Message.objects.filter(area=area, last_changed_time__gte=t.time).order_by('path')[0]
            messages_before_first_unread = area.message_set.filter(path__lt=first_unread_message.path).count()
            start_page = messages_before_first_unread // PAGE_SIZE
        except IndexError:
            pass

    messages = Message.objects.filter(area__pk=area_pk).prefetch_related('user', 'area')
    if not show_hidden:
        messages = messages.filter(visible=True)

    paginator = AreaPaginator(messages)

    def is_unread(row, **_):
        return row.last_changed_time >= t.time

    def is_unread2(row, **_):
        return row.last_changed_time >= unread2_time and not is_unread(row=row)

    def preprocess_data(data, table, **_):
        data = list(data)
        firstnew = None
        for d in data:
            if is_unread(row=d):
                firstnew = d
                break
        table.extra.unread = firstnew != None
        firstnew = firstnew or data[-1]
        firstnew.firstnew = True
        return data

    result = render_table_to_response(
        request,
        template=get_template('area.html'),
        paginator=paginator,
        context=dict(
            area=area,
            showHidden=show_hidden,
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
        table__row__template=get_template('area/dynamic-message.html'),
        table__row__attrs=dict(
            id=lambda row, **_: row.pk,
            class__indent_0=lambda row, **_: row.indent == 0,
            class__message=True,
            class__current_user=lambda row, **_: request.user == row.user,
            class__other_user=lambda row, **_: request.user != row.user,
            class__unread=is_unread,
            class__unread2=is_unread2,
        ),
        table__attrs__cellpadding='0',
        table__attrs__cellspacing='0',
        table__attrs__id='firstnewtable',
        table__attrs__align='center',
        table__attrs__class__areatable=True,
        page=start_page,
    )
    if 'unread_from_here' not in request.GET:
        t.time = datetime.now()

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
