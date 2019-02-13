#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from selectolax.parser import HTMLParser

"""
We'are testing only our own code.
Many functionality are already tested in the Modest engine, so there is no reason to test every case.
"""


def test_selector():
    html = "<span></span><div><p id='p3'>text</p></div><p></p>"
    selector = "p#p3"

    for node in HTMLParser(html).css(selector):
        assert node.text() == 'text'
        assert node.tag == 'p'
        assert node.parent.tag == 'div'
        assert node.parent.next.tag == 'p'
        assert node.parent.prev.tag == 'span'
        assert node.parent.last_child.attributes['id'] == 'p3'


def test_css_one():
    html = "<span></span><div><p class='p3'>text</p><p class='p3'>sd</p></div><p></p>"

    selector = ".s3"
    assert HTMLParser(html).css_first(selector) is None

    selector = "p.p3"
    assert HTMLParser(html).css_first(selector).text() == 'text'

    with pytest.raises(ValueError):
        HTMLParser(html).css_first(selector, strict=True)


def test_css_first_default():
    html = "<span></span><div><p class='p3'>text</p><p class='p3'>sd</p></div><p></p>"
    selector = ".s3"
    assert HTMLParser(html).css_first(selector, default='lorem ipsum') == 'lorem ipsum'


def test_attributes():
    html = "<div><p id='p3'>text</p></div>"
    selector = "p#p3"
    for node in HTMLParser(html).css(selector):
        assert 'id' in node.attributes
        assert node.attributes['id'] == 'p3'

    html = "<div><p attr>text</p></div>"
    selector = "p#p3"
    for node in HTMLParser(html).css(selector):
        assert 'attr' in node.attributes
        assert node.attributes['attr'] is None


def test_decompose():
    html = "<body><div><p id='p3'>text</p></div></body>"
    html_parser = HTMLParser(html)

    for node in html_parser.tags('p'):
        node.decompose()

    assert html_parser.body.child.html == '<div></div>'


def test_strip_tags():
    html = "<body><div></div><script></script></body>"
    html_parser = HTMLParser(html)
    html_parser.strip_tags(['div', 'script'])
    assert html_parser.html == '<html><head></head><body></body></html>'

    with pytest.raises(TypeError):
        html_parser.strip_tags(1)


def test_malformed_attributes():
    html = '<div> <meta name="description" content="ÐÐ°Ñ"Ð " /></div>'
    html_parser = HTMLParser(html)

    for tag in html_parser.tags('meta'):
        assert tag
