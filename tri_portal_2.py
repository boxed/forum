import os

from django.utils.html import format_html
from tri_form import render_attrs
from tri_struct import Struct

os.environ['DJANGO_SETTINGS_MODULE'] = 'forum2.settings'
import django
django.setup()


from tri_declarative import (
    dispatch,
    EMPTY,
    Namespace,
    setdefaults_path,
    class_shortcut,
)

from tri_portal import (
    HtmlPageContent,
)


class Content:
    @dispatch()
    def __init__(self, *, name=None, tag=None, content='', attrs=None, **more):
        if attrs is None:
            attrs = {}
        if more is None:
            more = {}

        if name:
            setdefaults_path(
                attrs,
                **{f'class__{name}': True}
            )

        self.attrs = attrs
        self.name = name
        self.tag = tag
        self.group = 'content'

        if isinstance(content, Namespace):
            self.children = [
                Content(name=k, content=v, **more.pop(k, {}))
                for k, v in content.items()
            ]
            self.own_content = None
        else:
            self.children = []
            self.own_content = content

        assert not more, f"group data contains unknown data: {more}"

    def render2(self, request):
        rendered_children = format_html('{}\n\n' * len(self.children), *(x.render2(request=request) for x in self.children))

        if self.own_content:
            assert not self.children
            if isinstance(self.own_content, str):
                return format_html('{}', self.own_content)
            else:
                return self.own_content.render2(request=request)

        if self.tag:
            return format_html('<{}{}>{}</{}>', self.tag, render_attrs(self.attrs), rendered_children, self.tag)
        else:
            return rendered_children

    # # TODO:
    # @classmethod
    # @class_shortcut
    # def stylesheet(cls, href):
    #     pass


@dispatch(
    item=EMPTY,
    group=EMPTY,
)
def assemble(item, group):
    # evaluate
    items = {}
    for k, v in item.items():
        if callable(v):
            v = v(name=k)
        else:
            setattr(v, 'name', k)
        items[k] = v

    groups = Namespace(
        {f'{item.group}__{item.name}': item for item in items.values()},
    )

    return Content(content=groups, **group)


request = Struct()


# <head>
#             <title>{{ page.title }}</title>
#             <link rel="stylesheet" href="//fonts.googleapis.com/css?family=Roboto:300,300italic,700,700italic">
#             <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.7.2/css/all.css" integrity="sha384-fnmOCqbTlWIlj8LyTjo7mOUStjsKC4pOpQbqyi7RrhN7udi9RwhKkMHpvLbHG9Sr" crossorigin="anonymous">
#             <link rel="stylesheet" href="/static/forum-minimalist.css" >
#             <script type="text/JavaScript" src="/static/forum.js"></script>
#             <link id="favicon" rel="shortcut icon" type="image/png" href="/static/killing-icon.png">
#             <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
#         </head>

actual = assemble(
    item=dict(
        title=Content(tag='title', content='~~title~~'),
        font=Content(tag='link', attrs__rel='stylesheet', attrs__href='//fonts.googleapis.com/css?family=Roboto:300,300italic,700,700italic'),
    )
).render2(request=request)

assert actual == '', actual


####

items = dict(
    item__foo__call_target=HtmlPageContent,
    item__foo__html='foo',

    item__bar__call_target=HtmlPageContent,
    item__bar__html='bar',

    item__baz__call_target=HtmlPageContent,
    item__baz__html='baz',
)


actual = assemble(**items).render2(request).strip()
assert actual == 'foo\n\nbar\n\nbaz', actual

actual = assemble(**items, group__contents__tag='div').render2(request).strip()
assert actual == '<div class="contents">foo\n\nbar\n\nbaz\n\n</div>', actual


actual = assemble(
    **items,
    item__foo__group='a__b',
    item__bar__group='a__b',
    group__a__tag='div',
    group__a__b__tag='div',
    group__contents__tag='div',
).render2(request).strip()
assert actual == '<div class="a"><div class="b">foo\n\nbar\n\n</div>\n\n</div>\n\n<div class="contents">baz\n\n</div>', actual

