#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selectolax.parser import HtmlParser


# TODO: write tests

def test_selector():
    html = "<div><p id='p3'>text</p></div>"
    selector = "p#p3"

    for node in HtmlParser(html).css(selector):
        assert node.text == 'text'
        assert node.tag == 'p'
        assert node.parent.tag == 'div'


def test_attributes():
    html = "<div><p id='p3'>text</p></div>"
    selector = "p#p3"
    for node in HtmlParser(html).css(selector):
        assert 'id' in node.attributes
        assert node.attributes['id'] == 'p3'

    html = "<div><p attr>text</p></div>"
    selector = "p#p3"
    for node in HtmlParser(html).css(selector):
        print(node.attributes)
        assert 'attr' in node.attributes
        assert node.attributes['attr'] is None
