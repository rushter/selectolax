# coding:utf-8
from selectolax.parser import HtmlParser


def test_encoding():
    html = "<div><p id=p1><p id=p2><p id=p3><a>link</a><p id=p4><p id=p5>text<p id=p6></div>"
    html = HtmlParser(html)
    assert html._get_input_encoding() == 'UTF-8'

    html = b"<div><p id=p1><p id=p2><p id=p3><a>link</a><p id=p4><p id=p5>text<p id=p6></div>"
    html = HtmlParser(html)
    html._get_input_encoding()  == 'UTF-8'
