# coding:utf-8
from difflib import SequenceMatcher

import pytest
from selectolax.parser import HTMLParser, Node
from selectolax.lexbor import LexborHTMLParser, LexborNode

"""
We'are testing only our own code.
Many functionality are already tested in the Modest engine, so there is no reason to test every case.
"""

_PARSERS_PARAMETRIZER = ("parser", (HTMLParser, LexborHTMLParser),)


def test_encoding():
    html = "<div><p id=p1><p id=p2><p id=p3><a>link</a><p id=p4><p id=p5>text<p id=p6></div>"
    html = HTMLParser(html)
    assert html.input_encoding == 'UTF-8'

    html = b"<div><p id=p1><p id=p2><p id=p3><a>link</a><p id=p4><p id=p5>text<p id=p6></div>"
    html = HTMLParser(html)
    assert html.input_encoding == 'UTF-8'

    html = "<div>Привет мир!</div>".encode('cp1251')
    assert HTMLParser(html, detect_encoding=True).input_encoding == 'WINDOWS-1251'

    html_utf = '<head><meta charset="WINDOWS-1251"></head>'.encode('utf-8')
    assert HTMLParser(html_utf, detect_encoding=True, use_meta_tags=True).input_encoding == 'WINDOWS-1251'

    # UTF-16 not ASCII-readable
    html_utf = '<head><meta charset="WINDOWS-1251"></head>'.encode('utf-16le')
    assert HTMLParser(html_utf, detect_encoding=True, use_meta_tags=True).input_encoding == 'UTF-16LE'

    # Unencodable characters in string, should not throw an exception by default
    html_unencodable = b'<div>Roboto+Condensed</div>'.decode('utf-7', errors='ignore')
    assert HTMLParser(html_unencodable).input_encoding == 'UTF-8'

    # decode_errrors='strict' should error out
    try:
        HTMLParser(html_unencodable, decode_errors='strict')
        assert False
    except Exception as e:
        assert type(e) is UnicodeEncodeError


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_parser(parser):
    html = parser("")
    assert isinstance(html, parser)

    with pytest.raises(TypeError):
        parser(123)

    with pytest.raises(TypeError):
        parser("asd").css(123)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_nodes(parser):
    html = (
        '<div><p id="p1"></p><p id="p2"></p><p id="p3"><a>link</a></p>'
        '<p id="p4"></p><p id="p5">text</p><p id="p6"></p></div>'
    )
    htmlp = parser(html)

    assert isinstance(htmlp.root, (Node, LexborNode))
    assert isinstance(htmlp.body, (Node, LexborNode))
    html_output = htmlp.html
    assert len(html_output) >= len(html)
    assert SequenceMatcher(None, html, html_output).ratio() > 0.8


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_root_css(parser):
    tree = parser('test')
    assert len(tree.root.css('data')) == 0


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_strip_tags_from_root(parser):
    html = "<body><div></div><script></script></body>"
    html_parser = parser(html)
    html_parser.root.strip_tags(['div', 'script'])
    assert html_parser.html == '<html><head></head><body></body></html>'

    with pytest.raises(TypeError):
        html_parser.strip_tags(1)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_clone(parser):
    html_parser = parser("""<h1>Welcome</h1>""")
    clone = html_parser.clone()
    html_parser.root.css_first('h1').decompose()
    del html_parser
    assert clone.html == '<html><head></head><body><h1>Welcome</h1></body></html>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_tags(parser):
    html_parser = parser("""
    <div><span><span></span></span></div>
    <div><span></span></div>
    <div><div></div></div>
    <span></span>
    <div></div>
    """)
    assert len(html_parser.tags('div')) == 5

