from itertools import groupby
from secrets import token_hex
from typing import (
    Callable,
    Dict,
    Union,
)

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from tri_declarative import (
    dispatch,
    EMPTY,
    declarative,
    Refinable,
    RefinableObject,
    sort_after,
    Namespace,
    with_meta,
    class_shortcut,
)
from tri_form import (
    Field,
    handle_dispatch,
    dispatch_prefix_and_remaining_from_key,
    DISPATCH_PATH_SEPARATOR,
    Link,
    render_attrs,
)

from tri_form import Form as BaseForm
from tri_form.compat import (
    slugify,
    HttpResponse,
    ValidationError,
    format_html,
    Template,
    render_template,
)

from .models import ResetCode

# TODO: `show` param on PageContent


def get_dispatch_http_param(request):
    for key, value in request.GET.items():
        if key.startswith(DISPATCH_PATH_SEPARATOR):
            return key, value


class WithEndpoint(RefinableObject):
    name = Refinable()
    """ :type: str """
    endpoint_dispatch_prefix = Refinable()  # The full path, e.g. '/grand_parent_name/parent_name/name'
    """ :type: str """
    endpoint = Refinable()
    """ :type: tri.declarative.Namespace """

    def endpoint_dispatch(self, key, value):
        prefix, remaining_key = dispatch_prefix_and_remaining_from_key(key)
        handler = self.endpoint.get(prefix, None)
        if handler is not None:
            return handler(form=self, key=remaining_key, value=value)


class Form(WithEndpoint, BaseForm):
    actions = Refinable()
    container = Refinable()

    @dispatch(
        container__attrs=EMPTY,
    )
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # if self.request.method == 'POST' and self.is_target() and self.is_valid():
    #     pass


class PageContent(WithEndpoint):
    group = Refinable()

    @dispatch(
        group='contents'
    )
    def __init__(self, **kwargs):
        super(PageContent, self).__init__(**kwargs)

    def render2(self, **_):
        raise NotImplementedError()

    def respond(self, request):
        pass


class FormContent(Form, PageContent):
    on_valid: Dict[str, Callable] = Refinable()

    def render2(self, request, style='table'):
        assert style == 'table'
        csrf_token = 'TODO!'
        return format_html(
            '<form{}><table{}><input type="hidden" name="csrfmiddlewaretoken" value="{}"/>{}{}{}</table></form>',
            self.rendered_attrs,
            render_attrs(self.container.attrs),
            csrf_token,
            self.render_errors(request, style=style),
            self.render(style=style, template_name=None),
            self.render_actions(request, style=style),
        )

    def render_errors(self, request, style):
        assert style == 'table'
        if self.errors:
            return render_template(request, Template("""
                <tr>
                    <td colspan="99">
                        {% for error in form.errors %}
                            <div class="error">{{ error }}</div>
                        {% endfor %}
                    </td>
                </tr>
                """), context=dict(form=self))
        else:
            return ''

    def render_actions(self, request, style):
        assert style == 'table'
        return render_template(request, Template("""
            <tr>
                <td colspan="99">
                    {{ form.rendered_links }}
                </td>
            </tr>
            """), context=dict(form=self))

    def respond(self, request):
        if self.is_target() and self.is_valid():
            on_valid = self.on_valid.get(request.method)
            if on_valid is not None:
                result = on_valid(form=self)
                if result is not None:
                    return result


class InvalidDispatch(Exception):
    pass


class Group:
    def __init__(self, name, items):
        self.name = name
        self.slug = slugify(name)
        self.items = sort_after(items)

    def render2(self, request):
        return '\n\n'.join(x.render2(request=request) for x in self.items)


def group_and_sort(items):
    grouped = groupby((item for item in items.values() if item.group is not None), key=lambda item: item.group)
    return [Group(g, lg) for g, lg in grouped]


# @declarative(PageContent, 'contents_dict')
@with_meta
class PageBase(RefinableObject):
    attrs = Refinable()

    head = Refinable()
    body = Refinable()
    template: Union[str, Template] = Refinable()
    title = Refinable()

    @dispatch(
        title='',
        contents=EMPTY,
        head__template=Template('<head><title>{{ page.title }}</title></head>'),
        body__template=Template('<body{{ page.rendered_attrs }}>{{ content }}</body>'),
        template=None,
    )
    def __init__(self, contents, **kwargs):
        self.unbound_contents = contents

        def bind_content(name, content):
            if isinstance(content, Namespace):
                return content(name=name)
            else:
                setattr(content, 'name', name)  # TODO: do I need to copy this thing before I do this?
                return content

        self.contents = {k: bind_content(k, v) for k, v in contents.items()}

        super().__init__(**kwargs)

    def respond(self, request):
        dispatch_http_param = get_dispatch_http_param(request)
        if dispatch_http_param:
            # We're talking to ONE thing, early return
            key, value = dispatch_http_param
            prefix, remaining_key = dispatch_prefix_and_remaining_from_key(key)

            if prefix not in self.contents:
                raise InvalidDispatch(f'{key} matched no handler, base of tree contains {self.contents.keys()}')

            x = self.contents[prefix].endpoint_dispatch(remaining_key, value)
            if x is not None:
                return x

        for content in self.contents.values():
            content.request = request

            result = content.respond(request=request)
            if result:
                return result

    def render_content(self, request):
        groups = group_and_sort(self.contents)

        return format_html(
            '{}' * len(groups),
            *[
                format_html(f'<div id="{group.name}">{group.render2(request)}</div>')
                for group in groups
            ],
        )

    def render2(self, request):

        if self.template is not None:
            return render_template(request, self.template, context=dict(content=self.render_content(request), page=self))
        else:
            return format_html('<!DOCTYPE html><html>{}{}</html>', self.render_head(request), self.render_body(request))

    def render_head(self, request):
        return render_template(request, self.head.template, context=dict(page=self))

    def render_body(self, request):
        return render_template(request, self.body.template, context=dict(page=self, content=self.render_content(request)))

    def respond_or_render(self, request):
        response = self.respond(request)
        if response:
            return response

        return HttpResponse(self.render2(request))

    def rendered_attrs(self):
        return render_attrs(self.attrs)

    @classmethod
    @class_shortcut(
        contents__form__call_target=FormContent,
        contents__form__group='center',
        contents__form__links=[Link.submit(attrs__name=lambda form, **_: form.name)],  # TODO: actions!
        attrs__class__form=True,
    )
    def form_page(cls, call_target, **kwargs):
        return call_target(**kwargs)


class Page(PageBase):  # the one in forum2
    class Meta:
        head__template = Template("""    
            <link rel="stylesheet" href="//fonts.googleapis.com/css?family=Roboto:300,300italic,700,700italic">
            <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.7.2/css/all.css" integrity="sha384-fnmOCqbTlWIlj8LyTjo7mOUStjsKC4pOpQbqyi7RrhN7udi9RwhKkMHpvLbHG9Sr" crossorigin="anonymous">
            <link rel="stylesheet" href="/static/forum-minimalist.css" >
            <script type="text/JavaScript" src="/static/forum.js"></script>
            <link id="favicon" rel="shortcut icon" type="image/png" href="/static/killing-icon.png" />
            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
        """)


# start forgot password page

def forgot_password(request):
    def parse(string_value, **_):
        try:
            return User.objects.get(Q(username=string_value) | Q(email=string_value))
        except User.DoesNotExist:
            raise ValidationError('Unknown username or email')

    def on_valid_post(form, **_):
        user = form.fields_by_name.username_or_email.value
        code = token_hex(64)
        ResetCode.objects.filter(user=user).delete()
        ResetCode.objects.create(user=user, code=code)

        # send_mail(
        #     subject=f'{settings.INSTALLATION_NAME} password reset',
        #     message=f"Your reset code is: \n{code}",
        #     from_email=settings.NO_REPLY_EMAIL,
        #     recipient_list=[user.email],
        # )
        return HttpResponseRedirect(reverse(reset_password))

    return Page.form_page(
        contents__form__on_valid__POST=on_valid_post,
        contents__form__request=request,  # TODO: this shouldn't be neccessary, fix later
        contents__form__fields=[
            Field(
                name='username_or_email',
                is_valid=lambda parsed_data, **_: (parsed_data is not None, 'Unknown username or email'),
                parse=parse,
            ),
        ],
        contents__form__actions__submit__title='Send reset email',
    ).respond_or_render(request)


def reset_password(request):
    class ResetPasswordForm(Form):
        reset_code = Field()
        new_password = Field.password()
        confirm_password = Field.password()

    form = ResetPasswordForm(request=request)

    if request.POST and form.is_valid():
        reset_code = form.fields_by_name.reset_code.value
        reset_code.user.set_password(form.fields_by_name.new_password.value)
        login(request, reset_code.user)
        reset_code.delete()
        return HttpResponseRedirect('/')

    return render(request, template_name='auth/reset_password.html', context=dict(base_template=settings.BASE_TEMPLATE, form=form))
