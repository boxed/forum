import re
from datetime import datetime

import mistune
from django.utils.safestring import mark_safe


class MyRenderer(mistune.HTMLRenderer):
    name = 'forum' \
           ''
    def paragraph(self, text):
        return text + '\n\n'  # this is converted to <br> in pre_format


markdown = mistune.create_markdown(renderer=MyRenderer())


def pre_format_legacy(s):
    s = s.replace('\t', '    ')
    s = re.sub('^( +)', lambda m: '&nbsp;' * len(m.groups()[0]), s, flags=re.MULTILINE)
    s = s.replace('\n', '<br>')
    return mark_safe(s)


def pre_format(s):
    s = s.replace(' ', '\xa0')
    s = markdown(s)
    s = s.replace('\t', '    ')
    # Working around a bug in mistune (https://github.com/lepture/mistune/issues/248)
    s = s.strip()
    s = s.replace('\n', '<br>\n')
    return mark_safe(s)


def parse_datetime(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')


def get_object_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None
