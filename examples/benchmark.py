# coding:utf-8
"""A simple benchmark that measures speed of lxml and selectolax.

How the benchmark works
-----------------------

For each page, we extract:

1) Title
2) Number of script tag
3) The ``href`` attribute from all links
4) The content of the Meta description tag

"""
import json
import functools
import time

from lxml.html import fromstring
from bs4 import BeautifulSoup
from selectolax.parser import HTMLParser
from selectolax.lexbor import LexborHTMLParser

bad_urls = []


def bs4_parser(html_content, parser=HTMLParser):
    soup = BeautifulSoup(html_content, 'html.parser')
    title_text = soup.title.string
    assert title_text

    a_hrefs = [a.attrs.get('href', '') for a in soup.find_all('a')]
    assert len(a_hrefs) >= 5, 'href'

    num_script_tags = len(soup.find_all('script'))
    assert num_script_tags > 0, 'script'
    meta_description = soup.find('meta', attrs={"name": "description"})
    if meta_description:
        meta_content = meta_description.get('content')


def selectolax_parser(html_content, parser=HTMLParser):
    tree = parser(html_content)
    title_text = ""
    title_node = tree.css_first('title')
    if title_node:
        title_text = title_node.text()
    assert title_text

    a_hrefs = [a.attrs.get('href', '') for a in tree.css('a[href]')]
    assert len(a_hrefs) >= 5, 'href'

    num_script_tags = len(tree.css('script'))
    assert num_script_tags > 0, 'script'
    meta_description = tree.css_first('meta[name="description"]')
    if meta_description:
        meta_content = meta_description.attrs.sget('content', '')


def lxml_parser(html_content):
    tree = fromstring(html_content)
    title_text = tree.xpath('//title/text()')
    assert title_text, 'title'

    a_hrefs = [a.attrib.get('href', '') for a in tree.xpath('//a[@href]')]
    assert len(a_hrefs) >= 5, 'href'

    num_script_tags = len(tree.xpath('//script'))
    assert num_script_tags > 0, 'script'
    meta_description = tree.xpath('meta[@name="description"]')
    if meta_description:
        meta_content = meta_description[0].attrib.get('content', '')


def _perform_test(pages, parse_func):
    for page in pages:
        parse_func(page['html'])


def main():
    #
    # This file contains 754 main pages from the top internet domains (according to Alexa rank).
    # That translates to 324MB of HTML data.
    # Because of potential copyright infringements, I don't publish it.
    #
    html_pages = [json.loads(page) for page in open('pages/pages.json', 'rt')]
    available_parsers = [
        ('bs4', bs4_parser,),
        ('lxml', lxml_parser,),
        ('modest', selectolax_parser,),
        ('lexbor', functools.partial(selectolax_parser, parser=LexborHTMLParser)),
    ]
    for parser_name, parser in available_parsers:
        start = time.time()
        _perform_test(html_pages, parser)
        print('%r: %s' % (parser_name, time.time() - start))


if __name__ == '__main__':
    main()
