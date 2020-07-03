from django import template
from django.utils.safestring import mark_safe
from pyparsing import QuotedString, Literal, Char, printables

register = template.Library()


def nil_parse_action(start, length, tokens):
    return ''


def wiki_link_parse_action(start, length, tokens):
    title = tokens[0].replace('"', '&quot;')
    if ';' in title:
        context, _, title = title.partition(';')
        if '://' in context:
            return f'<a href="{context}">{title}</a>'
        else:

            return f'<a href="/wiki/{context}/{title}/">{title}</a>'
    else:
        return f'<a href="../{title}/">{tokens[0]}</a>'


link = QuotedString("[", endQuoteChar="]").setParseAction(wiki_link_parse_action)


def wiki_quote_parse_action(start, length, tokens):
    return f'<blockquote>{tokens[0]}</blockquote>'


quote = QuotedString('{quote}', endQuoteChar='{quote}').setParseAction(wiki_quote_parse_action)


def wiki_bold_parse_action(start, length, tokens):
    return f'<b>{tokens[0]}</b>'


bold = QuotedString('**', endQuoteChar='**').setParseAction(wiki_bold_parse_action)


def wiki_italic_parse_action(start, length, tokens):
    return f'<i>{tokens[0]}</i>'


italic = QuotedString('~~', endQuoteChar='~~').setParseAction(wiki_italic_parse_action)


def wiki_underline_parse_action(start, length, tokens):
    return f'<u>{tokens[0]}</u>'


underline = QuotedString('__', endQuoteChar='__').setParseAction(wiki_underline_parse_action)


def literal_parse_action(start, length, tokens):
    return tokens[0]


literal = Literal('\\').setParseAction(nil_parse_action) + Char(printables).setParseAction(literal_parse_action)

divider = Literal('{divider}').setParseAction(lambda start, length, tokens: '<hr>')

wikiMarkup = literal | link | quote | bold | italic | underline | divider


def wiki_render(s):
    return mark_safe(wikiMarkup.transformString(s))


@register.filter
def wiki(value):
    return wiki_render(value)
