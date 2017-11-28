==========
selectolax
==========

.. image:: https://img.shields.io/pypi/v/selectolax.svg
        :target: https://pypi.python.org/pypi/selectolax

.. image:: https://img.shields.io/travis/rushter/selectolax.svg
        :target: https://travis-ci.org/rushter/selectolax

A fast HTML5 parser and CSS selectors using `Modest engine <https://github.com/lexborisov/Modest/>`_.

* Alpha version.


Installation
------------

.. code-block:: bash

        git clone --recursive  https://github.com/rushter/selectolax
        cd selectolax && python setup.py install


Example
-------
 
.. code:: python

        from selectolax.parser import HtmlParser

        html = "<div><p id=p1><p id=p2><p id=p3><a>link</a><p id=p4><p id=p5>text<p id=p6></div>"
        selector = "div > :nth-child(2n+1):not(:has(a))"

        for node in HtmlParser(html).css(selector):
            print(node.attributes, node.text, node.tag)
            print(node.parent.tag)
            print(node.html)


Simple Benchmark
----------------

.. code:: python

        In [1]: from lxml.cssselect import CSSSelector
           ...: from lxml.html import fromstring
           ...:
           ...: from selectolax.parser import HtmlParser
           ...: import timeit
           ...:
           ...: html = open('google.html').read()
           ...: selector = "cite._Rm"
           ...:
           ...:
           ...: def modest_parser(html, selector):
           ...:     links = [node.text for node in HtmlParser(html).css(selector)]
           ...:     assert len(links) == 9
           ...:     return links
           ...:
           ...:
           ...: def lxml_parser(html, selector):
           ...:     sel = CSSSelector(selector)
           ...:     h = fromstring(html)
           ...:
           ...:     links = [e.text for e in sel(h)]
           ...:     assert len(links) == 9
           ...:     return links
           ...:
           ...:
           ...: print('lxml', timeit.timeit('lxml_parser(html, selector)', number=1000, globals=globals()))
           ...: print('modest', timeit.timeit('modest_parser(html, selector)', number=1000, globals=globals()))
           ...:
           ...:
        lxml 17.79081910100649
        modest 2.133077474019956


License
-------

* Modest engine — `LGPL2.1 <https://github.com/lexborisov/Modest/blob/master/LICENSE>`_.
* selectolax - `MIT <https://github.com/rushter/selectolax/blob/master/LICENSE>`_.

