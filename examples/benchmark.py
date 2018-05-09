# coding:utf-8
import glob
import os
import shutil
import timeit
from statistics import mean

from lxml.html import fromstring
from selectolax.parser import HTMLParser

pages = glob.glob('examples/pages/*.html')
html_pages = [open(x, encoding='utf-8', errors='ignore').read() for x in pages]

selector_css = "cite.iUh30"
selector_xpath = '//cite[contains(@class, "iUh30")]'


def modest_parser(html_pages, selector):
    all_links = []
    for page in html_pages:
        links = [node.text(deep=False) for node in HTMLParser(page).css(selector)]
        assert len(links) >= 6
        all_links.extend(links)

    return all_links


def lxml_parser(html_pages, selector):
    all_links = []
    for page in html_pages:
        h = fromstring(page)
        links = [e.text for e in h.xpath(selector)]
        assert len(links) >= 6
        all_links.extend(links)
    return all_links


print('modest', mean(timeit.repeat('modest_parser(html_pages, selector_css)', globals=globals(), repeat=10, number=1)))
print('lxml', mean(timeit.repeat('lxml_parser(html_pages, selector_xpath)', globals=globals(), repeat=10, number=1)))
