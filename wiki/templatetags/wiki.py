from django import template
from django.utils.safestring import mark_safe
from pyparsing import QuotedString

register = template.Library()


def wiki_link_to_anchor_tag(start, length, tokens):
    title = tokens[0].replace('"', '&quot;')
    return f'<a href="../{title}/">{tokens[0]}</a>'


def wiki_quote_parse_action(start, length, tokens):
    return f'<blockquote>{tokens[0]}</blockquote>'


def wiki_bold_parse_action(start, length, tokens):
    return f'<b>{tokens[0]}</b>'


urlRef = QuotedString("[", endQuoteChar="]").setParseAction(wiki_link_to_anchor_tag)

quote = QuotedString('{quote}', endQuoteChar='{quote}').setParseAction(wiki_quote_parse_action)

bold = QuotedString('**', endQuoteChar='**').setParseAction(wiki_bold_parse_action)


wikiMarkup = urlRef | quote | bold


def wiki_render(s):
    return mark_safe(wikiMarkup.transformString(s))  # TODO: yea, this isn't safe...


@register.filter
def wiki(value):
    return wiki_render(value)
