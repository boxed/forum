from itertools import groupby
from typing import Dict, Callable, Union

from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.template import (
    Template,
    RequestContext,
)
from django.utils.html import format_html
from django.utils.text import slugify
from tri_declarative import (
    Refinable,
    dispatch,
    EMPTY,
    sort_after,
    with_meta,
    RefinableObject,
    Namespace,
    class_shortcut,
    should_show,
    setdefaults_path,
)
from tri_form import DISPATCH_PATH_SEPARATOR, Form as BaseForm, render_attrs, render_template, dispatch_prefix_and_remaining_from_key, Link
from tri_table import Table, render_table


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


# @declarative(PageContent, 'contents_dict')
class PageContent(WithEndpoint):
    group = Refinable()
    after = Refinable()
    show = Refinable()

    @dispatch(
        group='contents',
        after=None,
        show=True,
    )
    def __init__(self, **kwargs):
        super(PageContent, self).__init__(**kwargs)

    def render2(self, **_):
        raise NotImplementedError()

    def respond(self, request):
        pass


class HtmlPageContent(PageContent):
    def __init__(self, *, html, **kwargs):
        self.html = html
        super().__init__(**kwargs)

    def render2(self, **_):
        return self.html


class FormContent(Form, PageContent):
    on_valid: Dict[str, Callable] = Refinable()

    def render2(self, request, style='table'):
        assert style == 'table'
        csrf_token = get_token(request)
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


class TableContent(Table, PageContent):
    def render2(self, request, **_):
        # {{ table.render_filter }}
        #
        # <div class="table-container">
        #     {% include "tri_table/table_container.html" %}
        # </div>

        return render_table(request, table=self)

    def respond(self, request):
        pass


class InvalidDispatch(Exception):
    pass


class Group:
    def __init__(self, name, items):
        self.name = name
        self.slug = slugify(name)
        self.items = sort_after(items)
        self.items = [x for x in self.items if should_show(x)]

    def render2(self, request):
        contents = format_html('{}\n\n' * len(self.items), *(x.render2(request=request) for x in self.items))
        if self.name:
            return format_html('<div class="{}">{}</div>', self.name, contents)
        return contents


def group_and_sort(items):
    grouped = groupby((item for item in items.values() if item.group is not None), key=lambda item: item.group)
    return [Group(g, lg) for g, lg in grouped]


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
        contents__title__call_target=HtmlPageContent,
        contents__title__after=-1,
        head__template=Template('<head><title>{{ page.title }}</title></head>'),
        body__template=Template('<body{{ page.rendered_attrs }}>{{ content }}</body>'),
        template=None,
    )
    def __init__(self, contents, title, **kwargs):
        setdefaults_path(
            contents,
            title__html=format_html('<h1>{}</h1>', title),
            title__show=bool(title),
        )

        self.unbound_contents = contents

        def bind_content(name, content):
            if isinstance(content, Namespace):
                return content(name=name)
            else:
                setattr(content, 'name', name)  # TODO: do I need to copy this thing before I do this?
                return content

        self.contents = {k: bind_content(k, v) for k, v in contents.items()}

        super().__init__(title=title, **kwargs)

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
                format_html('<div id="{}">{}</div>', group.name, group.render2(request))
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
        contents__form__links=[Link.submit(attrs__name=lambda form, **_: form.name)],  # TODO: actions! and move to tri.form
        attrs__class__form=True,
    )
    def form_page(cls, call_target, **kwargs):
        return call_target(**kwargs)

    @classmethod
    @class_shortcut(
        contents__table__call_target=TableContent.from_model,
        attrs__class__table=True,
    )
    def table_page(cls, call_target, **kwargs):
        return call_target(**kwargs)


class Page(PageBase):  # the one in forum2
    class Meta:
        head__template = Template("""  
        <head>  
            <title>{{ page.title }}</title>
            <link rel="stylesheet" href="//fonts.googleapis.com/css?family=Roboto:300,300italic,700,700italic">
            <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.7.2/css/all.css" integrity="sha384-fnmOCqbTlWIlj8LyTjo7mOUStjsKC4pOpQbqyi7RrhN7udi9RwhKkMHpvLbHG9Sr" crossorigin="anonymous">
            <link rel="stylesheet" href="/static/forum-minimalist.css" >
            <script type="text/JavaScript" src="/static/forum.js"></script>
            <link id="favicon" rel="shortcut icon" type="image/png" href="/static/killing-icon.png" />
            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
        </head>
        """)


def test_html_creation():
    @dispatch(
        item=EMPTY,
        group=EMPTY,
    )
    def assemble(item, group):
        return ''.join(x.render2() for x in item.values())

    items = dict(
        item__foo=HtmlPageContent(html='foo'),
        item__bar=HtmlPageContent(html='bar'),
        item__baz=HtmlPageContent(html='baz'),
    )

    assert assemble(**items) == 'foobarbaz'
    assert assemble(
        **items,
        item__foo__group='a__b',
        item__bar__group='a__b',
    ) == '<div class="a"><div class="b">foobar</div>baz</div>'
    assert assemble(
        **items,
        item__foo__group='a__b',
        item__bar__group='a__b',
        group__a__attrs__class__a=False,
        group__a__attrs__class_foo=True,
    ) == '<div class="a"><div class="b">foobar</div>baz</div>'
