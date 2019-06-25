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
)

from tri_portal import (
    HtmlPageContent,
)


class Content:
    def __init__(self, *, name=None, tag=None, children_or_content, attrs=None, **more):
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

        if isinstance(children_or_content, Namespace):
            self.children = [
                Content(name=k, children_or_content=v, **more.pop(k, {}))
                for k, v in children_or_content.items()
            ]
            self.own_content = None
        else:
            self.children = []
            self.own_content = children_or_content

        assert not more, f"group data contains unknown data: {more}"

    def render2(self, request):
        rendered_children = format_html('{}\n\n' * len(self.children), *(x.render2(request=request) for x in self.children))

        if self.own_content:
            assert not self.children
            return self.own_content.render2(request=request)

        if self.tag:
            return format_html('<{}{}>{}</{}>', self.tag, render_attrs(self.attrs), rendered_children, self.tag)
        else:
            return rendered_children


@dispatch(
    item=EMPTY,
    group=EMPTY,
)
def assemble(item, group):
    # evaluate
    items = {k: v(name=k) for k, v in item.items()}

    groups = Namespace(
        {f'{item.group}__{item.name}': item for item in items.values()},
    )

    return Content(children_or_content=groups, **group)


items = dict(
    item__foo__call_target=HtmlPageContent,
    item__foo__html='foo',

    item__bar__call_target=HtmlPageContent,
    item__bar__html='bar',

    item__baz__call_target=HtmlPageContent,
    item__baz__html='baz',
)


request = Struct()

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
