from lxml.cssselect import CSSSelector
from lxml.html import fromstring

from selectolax.parser import HtmlParser
import timeit

html = open('google.html').read()
selector = "cite._Rm"


def modest_parser(html, selector):
    links = [node.text for node in HtmlParser(html).css(selector).find()]
    assert len(links) == 9
    return links


def lxml_parser(html, selector):
    sel = CSSSelector(selector)
    h = fromstring(html)

    links = [e.text for e in sel(h)]
    assert len(links) == 9
    return links


print('lxml', timeit.timeit('lxml_parser(html, selector)', number=1000, globals=globals()))
print('modest', timeit.timeit('modest_parser(html, selector)', number=1000, globals=globals()))

