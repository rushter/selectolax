# coding:utf-8
from difflib import SequenceMatcher

import pytest
from selectolax.parser import HTMLParser, Node

"""
We'are testing only our own code.
Many functionality are already tested in the Modest engine, so there is no reason to test every case.
"""


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


def test_parser():
    html = HTMLParser("")
    assert isinstance(html, HTMLParser)

    with pytest.raises(TypeError):
        HTMLParser(123)

    with pytest.raises(TypeError):
        HTMLParser("asd").css(123)


def test_nodes():
    html = (
        '<div><p id="p1"></p><p id="p2"></p><p id="p3"><a>link</a></p>'
        '<p id="p4"></p><p id="p5">text</p><p id="p6"></p></div>'
    )
    htmlp = HTMLParser(html)

    assert isinstance(htmlp.root, Node)
    assert isinstance(htmlp.body, Node)
    html_output = htmlp.html
    assert len(html_output) >= len(html)
    assert SequenceMatcher(None, html, html_output).ratio() > 0.8
