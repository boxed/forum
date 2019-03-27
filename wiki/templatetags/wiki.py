from django import template
from django.utils.safestring import mark_safe
from pyparsing import QuotedString

register = template.Library()


def wiki_link_to_anchor_tag(start, lenth, tokens):
    return f'<a href="../{tokens[0]}/">{tokens[0]}</a>'


urlRef = QuotedString("[", endQuoteChar="]").setParseAction(wiki_link_to_anchor_tag)

wikiMarkup = urlRef


def wiki_render(s):
    return mark_safe(wikiMarkup.transformString(s))  # TODO: yea, this isn't safe...


@register.filter
def wiki(value):
    return wiki_render(value)
