.. image:: docs/logo.png
  :alt: selectolax logo

-------------------------

.. image:: https://img.shields.io/pypi/v/selectolax.svg
        :target: https://pypi.python.org/pypi/selectolax

A fast HTML5 parser with CSS selectors using `Modest <https://github.com/lexborisov/Modest/>`_ and
`Lexbor <https://github.com/lexbor/lexbor>`_ engines.


Installation
------------
From PyPI using pip:

.. code-block:: bash

        pip install selectolax 

Development version from GitHub:

.. code-block:: bash       

        git clone --recursive  https://github.com/rushter/selectolax
        cd selectolax
        pip install -r requirements_dev.txt
        python setup.py install

How to compile selectolax while developing:

.. code-block:: bash

    make clean
    make dev

Basic examples
--------------

.. code:: python

    In [1]: from selectolax.parser import HTMLParser
       ...:
       ...: html = """
       ...: <h1 id="title" data-updated="20201101">Hi there</h1>
       ...: <div class="post">Lorem Ipsum is simply dummy text of the printing and typesetting industry. </div>
       ...: <div class="post">Lorem ipsum dolor sit amet, consectetur adipiscing elit.</div>
       ...: """
       ...: tree = HTMLParser(html)

    In [2]: tree.css_first('h1#title').text()
    Out[2]: 'Hi there'

    In [3]: tree.css_first('h1#title').attributes
    Out[3]: {'id': 'title', 'data-updated': '20201101'}

    In [4]: [node.text() for node in tree.css('.post')]
    Out[4]:
    ['Lorem Ipsum is simply dummy text of the printing and typesetting industry. ',
     'Lorem ipsum dolor sit amet, consectetur adipiscing elit.']

.. code:: python

    In [1]: html = "<div><p id=p1><p id=p2><p id=p3><a>link</a><p id=p4><p id=p5>text<p id=p6></div>"
       ...: selector = "div > :nth-child(2n+1):not(:has(a))"

    In [2]: for node in HTMLParser(html).css(selector):
       ...:     print(node.attributes, node.text(), node.tag)
       ...:     print(node.parent.tag)
       ...:     print(node.html)
       ...:
    {'id': 'p1'}  p
    div
    <p id="p1"></p>
    {'id': 'p5'} text p
    div
    <p id="p5">text</p>


* `Detailed overview <https://github.com/rushter/selectolax/blob/master/examples/walkthrough.ipynb>`_

Available backends
------------------

Selectolax supports two backends: ``Modest`` and ``Lexbor``. By default, all examples use the Modest backend.
Most of the features between backends are almost identical, but there are still some differences.

Currently, the ``Lexbor`` backend is in **beta** and missing some of the features.

To use ``lexbor``, just import the parser and use it in the similar way to the `HTMLParser`.

.. code:: python

    In [1]: from selectolax.lexbor import LexborHTMLParser

    In [2]: html = """
       ...: <title>Hi there</title>
       ...: <div id="updated">2021-08-15</div>
       ...: """

    In [3]: parser = selectolax.lexbor.LexborHTMLParser(html)
    In [4]: parser.root.css_first("#updated").text()
    Out[4]: '2021-08-15'


Simple Benchmark
----------------

* Extract title, links, scripts and a meta tag from main pages of top 754 domains. See ``examples/benchmark.py`` for more information.

============================  ==========
Package                       Time
============================  ==========
Beautiful Soup (html.parser)  59.64 sec.
lxml                          14.48 sec.
selectolax (Modest)           2.396 sec.
selectolax (Lexbor)           2.121 sec.
============================  ==========

Links
-----

*  `selectolax API reference <http://selectolax.readthedocs.io/en/latest/parser.html>`_
*  `Detailed overview <https://github.com/rushter/selectolax/blob/master/examples/walkthrough.ipynb>`_
*  `Modest introduction <https://lexborisov.github.io/Modest/>`_
*  `Modest benchmark <http://lexborisov.github.io/benchmark-html-persers/>`_
*  `Python benchmark <https://rushter.com/blog/python-fast-html-parser/>`_
*  `Another Python benchmark <https://www.peterbe.com/plog/selectolax-or-pyquery>`_

License
-------

* Modest engine — `LGPL2.1 <https://github.com/lexborisov/Modest/blob/master/LICENSE>`_
* selectolax - `MIT <https://github.com/rushter/selectolax/blob/master/LICENSE>`_


