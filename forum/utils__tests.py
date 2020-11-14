from forum.utils import (
    pre_format_legacy,
    pre_format,
)


def test_pre_format():
    assert pre_format_legacy('') == ''
    assert pre_format_legacy('\n  foo\n   bar') == '<br>&nbsp;&nbsp;foo<br>&nbsp;&nbsp;&nbsp;bar'


def test_pre_format2():
    assert pre_format('') == ''
    assert pre_format('\n  foo\n   bar') == 'foo<br>\n\xa0\xa0\xa0bar'
    # TODO: seems like it should be this:
    # assert pre_format('\n  foo\n   bar') == '<br>\xa0\xa0foo<br>\xa0\xa0\xa0bar'
    assert pre_format('<script>foo()</script>') == '<p>&lt;script&gt;foo()&lt;/script&gt;</p>'  # TODO: the <p> tag should be stripped imo, but it's fine for now
