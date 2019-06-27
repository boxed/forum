import os

from django.utils.html import format_html
from tri_declarative import (
    dispatch,
    EMPTY,
    refinable,
    RefinableObject,
    Namespace,
)
from tri_form import render_attrs
from tri_struct import Struct

os.environ['DJANGO_SETTINGS_MODULE'] = 'forum2.settings'
import django
django.setup()


class BoundContent(RefinableObject):
    @dispatch(
        children=EMPTY,
    )
    def __init__(self, *, name=None, tag=None, no_end_tag=False, attrs=None, children, content=None, **kwargs):
        self.name = name
        self.attrs = attrs
        self.tag = tag
        self.no_end_tag = no_end_tag
        self.children = {}
        self.content = content or ''
        for k, v in children.items():
            if isinstance(v, dict):
                v = bind(**v, name=k)
            self.children[k] = v

        super(BoundContent, self).__init__(**kwargs)

    @staticmethod
    @refinable
    def render_children(bound_content, request):
        return format_html(
            '{}\n' * len(bound_content.children),
            *[
                x.render2(request) if isinstance(x, BoundContent) else str(x)
                for x in bound_content.children.values()
            ]
        )

    @staticmethod
    @refinable
    def render(bound_content, request):
        rendered_children = bound_content.render_children(bound_content=bound_content, request=request)

        if bound_content.tag:
            if not bound_content.no_end_tag:
                return format_html(
                    '<{}{}>{}{}{}</{}>',
                    bound_content.tag,
                    render_attrs(bound_content.attrs),
                    '\n' if rendered_children else '',
                    bound_content.content,
                    rendered_children,
                    bound_content.tag,
                )
            else:
                assert not bound_content.content and not rendered_children
                return format_html(
                    '<{}{}>',
                    bound_content.tag,
                    render_attrs(bound_content.attrs),
                )
        else:
            return bound_content.content + rendered_children

    def render2(self, request):
        return self.render(bound_content=self, request=request)


def bind(**x):
    return BoundContent(**x)


request = Struct()

####
actual = bind(children=dict(foo='str')).render2(request).strip()
assert actual == 'str', actual


actual = bind(
    children=dict(
        foo='foo',
        bar='bar',
        baz='baz',
    )
).render2(request).strip()
assert actual == 'foo\nbar\nbaz', actual


actual = bind(
    children=dict(
        foo='foo',
        bar='bar',
        baz__content='baz',
        baz__tag='div',
        baz__attrs__class__baz=True,
    ),
).render2(request).strip()
assert actual == 'foo\nbar\n<div class="baz">baz</div>', actual


actual = bind(
    name='contents',
    tag='div',
    children=dict(
        foo='foo',
        bar='bar',
        baz__content='baz',
        baz__tag='div',
        baz__attrs__class__baz=True,
    ),
).render2(request).strip()
assert actual == '<div>\nfoo\nbar\n<div class="baz">baz</div>\n</div>', actual


actual = bind(render=lambda bound_content, request: 'foo').render2(request) == 'foo'


@dispatch(
    attrs__rel='stylesheet',
    tag='link',
    no_end_tag=True,
)
def stylesheet(href, **kwargs):
    return Namespace(
        attrs__href=href,
        **kwargs
    )


foo = dict(
    name='head',
    tag='head',
    children=dict(
        title=dict(
            tag='title',
            content='~~title~~',
        ),
        font=stylesheet('//fonts.googleapis.com/css?family=Roboto:300,300italic,700,700italic'),
        fontawesome=stylesheet("https://use.fontawesome.com/releases/v5.7.2/css/all.css", attrs__integrity="sha384-fnmOCqbTlWIlj8LyTjo7mOUStjsKC4pOpQbqyi7RrhN7udi9RwhKkMHpvLbHG9Sr", attrs__crossorigin="anonymous"),
        css=stylesheet("/static/forum-minimalist.css"),
        js=dict(
            tag='script',
            attrs__type="text/JavaScript",
            attrs__src="/static/forum.js",
        ),
        favicon=dict(
            tag='link',
            no_end_tag=True,
            attrs=dict(id="favicon", rel="shortcut icon", type="image/png", href="/static/killing-icon.png")
        ),
        viewport=dict(
            tag='meta',
            no_end_tag=True,
            attrs=dict(name="viewport", content="width=device-width, initial-scale=1, maximum-scale=1"),
        )
    ),
)

actual = bind(**foo).render2(request).strip()

print(actual)

expected = """<head>
<title>~~title~~</title>
<link href="//fonts.googleapis.com/css?family=Roboto:300,300italic,700,700italic" rel="stylesheet">
<link crossorigin="anonymous" href="https://use.fontawesome.com/releases/v5.7.2/css/all.css" integrity="sha384-fnmOCqbTlWIlj8LyTjo7mOUStjsKC4pOpQbqyi7RrhN7udi9RwhKkMHpvLbHG9Sr" rel="stylesheet">
<link href="/static/forum-minimalist.css" rel="stylesheet">
<script src="/static/forum.js" type="text/JavaScript"></script>
<link href="/static/killing-icon.png" id="favicon" rel="shortcut icon" type="image/png">
<meta content="width=device-width, initial-scale=1, maximum-scale=1" name="viewport">
</head>"""

assert actual == expected


assert 'testasdtest' in bind(**foo, children__css__attrs__foo='testasdtest').render2(request)
