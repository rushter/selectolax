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

* Average time of 5 experiments to parse and retrieve urls from 1000 Google SERP pages.

+------------+------------+--------------+
| Package    | Time       | Memory (peak)|
+============+============+==============+
| selectolax | 2.33 sec.  | 20.3 MB      |
+------------+------------+--------------+
| lxml       | 19.01 sec. | 18.5 MB      |
+------------+------------+--------------+

License
-------

* Modest engine — `LGPL2.1 <https://github.com/lexborisov/Modest/blob/master/LICENSE>`_.
* selectolax - `MIT <https://github.com/rushter/selectolax/blob/master/LICENSE>`_.

