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
From PyPI using pip:

.. code-block:: bash

        pip install selectolax 

Development version from github:

.. code-block:: bash       

        git clone --recursive  https://github.com/rushter/selectolax
        cd selectolax
        pip -r requirements_dev.txt
        python setup.py install


Examples
--------

.. code:: python

        from selectolax.parser import HTMLParser

        html = "<div><p id=p1><p id=p2><p id=p3><a>link</a><p id=p4><p id=p5>text<p id=p6></div>"
        selector = "div > :nth-child(2n+1):not(:has(a))"

        for node in HTMLParser(html).css(selector):
            print(node.attributes, node.text(), node.tag)
            print(node.parent.tag)
            print(node.html)


* `Detailed overview <https://github.com/rushter/selectolax/blob/master/examples/walkthrough.ipynb>`_
 
Simple Benchmark
----------------

* Average of 10 experiments to parse and retrieve URLs from 800 Google SERP pages.

+------------+------------+--------------+
| Package    | Time       | Memory (peak)|
+============+============+==============+
| selectolax | 2.38 sec.  | 768.11 MB    |
+------------+------------+--------------+
| lxml       | 18.67 sec. | 769.21 MB    |
+------------+------------+--------------+

Links
-----

*  `selectolax API reference <http://selectolax.readthedocs.io/en/latest/parser.html>`_
*  `Detailed overview <https://github.com/rushter/selectolax/blob/master/examples/walkthrough.ipynb>`_
*  `Modest introduction <https://lexborisov.github.io/Modest/>`_
*  `Modest benchmark <http://lexborisov.github.io/benchmark-html-persers/>`_
*  `Python benchmark <https://rushter.com/blog/python-fast-html-parser/>`_


License
-------

* Modest engine — `LGPL2.1 <https://github.com/lexborisov/Modest/blob/master/LICENSE>`_
* selectolax - `MIT <https://github.com/rushter/selectolax/blob/master/LICENSE>`_


