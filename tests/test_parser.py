# coding:utf-8
import pytest
from selectolax.parser import HTMLParser

"""
We'are testing only our own code.
Many functionality are already tested in the Modest engine, so there is no reason to test every case.
"""


def test_encoding():
    html = "<div><p id=p1><p id=p2><p id=p3><a>link</a><p id=p4><p id=p5>text<p id=p6></div>"
    html = HTMLParser(html)
    assert html._get_input_encoding() == 'UTF-8'

    html = b"<div><p id=p1><p id=p2><p id=p3><a>link</a><p id=p4><p id=p5>text<p id=p6></div>"
    html = HTMLParser(html)
    assert html._get_input_encoding() == 'UTF-8'


def test_parser():
    html = HTMLParser("")
    assert isinstance(html, HTMLParser)

    with pytest.raises(TypeError):
        HTMLParser(123)

    with pytest.raises(TypeError):
        HTMLParser("asd").css(123)
