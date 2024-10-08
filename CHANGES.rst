selectolax Changelog
====================

Version 0.3.23
-------------

Released

- Add Python 3.13 wheels
- Update lexbor

Version 0.3.21
-------------

Released

- ***Breaking change***: `lexbor` backend now includes the root node when querying CSS selectors. Same as `Modest` backend.
- Fix `css_matches` and `any_css_matches` methods for `Modest` backend on some compilers


Version 0.3.20
-------------

Released

- Fixup for 0.3.19 release
- Fix tag order for `lexbor` backend


Version 0.3.19
-------------

Released

- Increase maximum HTML size to 2.4GB


Version 0.3.18
-------------

Released

- Fix memory leak when using CSS selectors, `lexbor` backend


Version 0.3.17
-------------

Released

- Update lexbor
- Add Python 3.12 wheels


Version 0.3.16
-------------

Released

- Make HTML nodes hashable
- Pin Cython version


Version 0.3.15
-------------

Released

- Improve typing. Thanks to @nesb1

Version 0.3.14
-------------

Released

- Fix memory leak for `lexbor` backend


Version 0.3.13
-------------

Released

- Update `lexbor`


Version 0.3.12
-------------

Released

- Update `lexbor`
- Add Python 3.11 wheels


Version 0.3.11
-------------

Released

- Fix out-of-bounds bug for ``merge_text_nodes`` method.


Version 0.3.10
--------------

Released

This release does not contain any changes.
Due to a typo in the version number (`#70`_), we need to make a new release.

.. _#70: https://github.com/rushter/selectolax/issues/70

Version 0.3.9
-------------

Released

- Remove trailing separator when using ``text(deep=True, separator='x')``.
- Add a new ``merge_text_nodes`` method for Modest backend.

Version 0.3.8
-------------

Released

- Fix incorrect text handling when using ``text(deep=True)`` on a text node.

Version 0.3.7
-------------

Released

- Fix return type of HTMLParser.tags

Version 0.3.6
-------------

Released

- Improve text handling
- Add binary builds for Python 3.10 and ARM on MacOS and Linux


Version 0.3.5
-------------

Released

- Add type annotations


Version 0.3.4
--------------

Released

- Fix ``HTMLParser.html``


Version 0.3.3
--------------

Released

- Use `document` for the ``HTMLParser.html``, ``LexborHTMLParser.html``  root properties

Version 0.3.2
--------------

Released

- Fix  ``selector`` method for lexbor
- Improve text extraction for lexbor


Version 0.3.1
--------------

Released

- Fix  ``setup.py`` for Windows


Version 0.3.0
--------------

Released

- Added ``lexbor`` backend
- Fix cloning for `Modest` backend


Version 0.2.14
--------------

Released

- Added advanced Selector (the ``select`` method)
- Improved speed of ``strip_tags``
- Added ``clone`` method for the ``HtmlParser`` object
- Exposed ``detect_encoding``, ``decode_errors``, ``use_meta_tags``, ``raw_html`` attributes for ``HtmlParser``
- Added ``sget`` method to the ``attrs`` property


Version 0.2.13
--------------

Released

- Don't throw exception when encoding text as UTF-8 bytes fails (`#40`_).
- Fix Node.attrs.items() causes (`#39`_).

.. _#40: https://github.com/rushter/selectolax/issues/40
.. _#39: https://github.com/rushter/selectolax/issues/39

Version 0.2.12
--------------

Released

- Build wheels Apple Silicon

Version 0.2.11
--------------

Released

- Fix strip argument is ignored for the root node (`#35`_).
- Fix CSS parser hangs on a bad CSS selector (`#36`_).

.. _#36: https://github.com/rushter/selectolax/issues/36
.. _#35: https://github.com/rushter/selectolax/issues/35


Version 0.2.10
--------------

Released

- Fix root node property (`#32`_ ). The `root` property now points to the html tag.

.. _#32: https://github.com/rushter/selectolax/issues/32

Version 0.2.9
-------------

Released

- Fix README for PyPI

Version 0.2.8
-------------

Released

- Add wheels for Python 3.9

Version 0.2.7
-------------

Released

- Add `raw_value` attribute for `Node` objects  (`#22`_ )
- Improve node modification operations

.. _#22: https://github.com/rushter/selectolax/issues/22

Version 0.2.6
-------------

Released

-   Fix dependency on the source `Node` when inserting to or modifying destination `Node`

Version 0.2.5
-------------

Released

-   Allow to pass Node instances to `replace_with`, `insert_before` and `insert_after` methods
-   Added `insert_before` and `insert_after` methods

Version 0.2.4
-------------

Released

-   Set maximum input size to 80MB
-   Update modest

Version 0.2.3
-------------

Released

-   Rebuild PyPi wheels to support Python 3.8 and manylinux2010


Version 0.2.2
-------------

Released

-   Fix node comparison

Version 0.2.1
-------------

Released

-   Add optional `include_text` parameter for the `iter` and `traverse` methods

Version 0.2.0
-------------

Released

-   Fix `iter()` does not yield text nodes
-   Switch from TravisCI to Github Actions
-   Build and ship wheels for Windows, MacOS and Linux using Azure Pipelines
-   Add `unwrap` and `unwrap_tags` method (`#7`_ )
-   Add `replace_with` method (`#13`_ )
-   Add `attrs` property
-   Add `traverse` method

.. _#7: https://github.com/rushter/selectolax/issues/7
.. _#13: https://github.com/rushter/selectolax/issues/13
