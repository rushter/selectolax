# selectolax Changelog

# Version 1.0.0 (Unreleased)

This release contains **breaking changes**.

The main change is that the Modest backend is no longer available.
It is outdated and unmaintained, contains bugs, and does not follow modern HTML5 standards.

The second is that `parse_fragment()` is gone. It re-implemented fragment parsing by guessing
whether the input was a document or a fragment; `LexborHTMLParser(html, is_fragment=True)` already
does this properly, so the guessing layer has been removed.

The rest of the changes fix corner cases where the bugs were happening rarely,
usually when heavily modifying the tree.

- **Breaking**: Remove the Modest backend. `selectolax.parser` is now a stub that raises `ImportError`
  on import. Use the lexbor backend (`from selectolax.lexbor import LexborHTMLParser`) instead.
- **Breaking**: Remove `parse_fragment()`.
- **Breaking**: Fix `css_matches` and `any_css_matches` missing matches outside the first top-level node of an HTML
  fragment. They now search the same scope as `css`.
- **Breaking**: Fix `tags` and `strip_tags` doing nothing on an HTML fragment. `tags` returned an empty list and
  `strip_tags` removed nothing, because the fragment was not reachable from the document node.
- **Breaking**: Fix the internal `<html>` wrapper of an HTML fragment being reported as a match.
- **Breaking**: Fix `scripts_contain` and `script_srcs_contain` missing matches outside the first top-level
  node of an HTML fragment. They now search the same scope as `css`.
- **Breaking**: Fix `scripts_contain` and `script_srcs_contain` answering from another scope's cached
  result. The cache is keyed by the node the search is rooted at rather than the node it was called on.
- **Breaking**: Fix `select()` missing matches outside the first top-level node of an HTML fragment.
  It now searches the same scope as `css`.
- **Breaking**: Fix `traverse()` covering only the first top-level node of an HTML fragment, and
  yielding nothing when the fragment starts with a text node.
- **Breaking**: Fix `attribute_longer_than` and `any_attribute_longer_than` returning inconsistent results
- **Breaking**: `attributes` and `attrs` now report an attribute's qualified name instead of its local name.
  An element carrying both `href` and `xlink:href` used to collapse them into a single `href` key.
- **Breaking**: Fix `iter()` skipping the remaining children when a node is removed during iteration
- **Breaking**: Fix an HTML fragment whose first node is text dropping the rest of the fragment.
  `LexborHTMLParser('a<span>s</span>', is_fragment=True).text()` returned `'a'` instead of `'as'`.
- Fix `scripts_contain` and `script_srcs_contain` sometimes returning wrong results due to HTML mutations.
- Fix `text_lexbor` sometimes holding temporary memory longer than needed
- Improve memory consumption, potential stack overflow and slow extraction in `merge_text_nodes()`. It is now up to 10 times faster.
- Improve speed of `__eq__`
- Fix the `inner_html` setter attaching element children to non-element nodes
- Fix `head` and `body` dangling after setting `inner_html` on the `<html>` element
- Fix `root` going stale on an HTML fragment.
- Fix a segfault when walking the tree from the root of an HTML fragment that had been detached from the
  fragment, for example by `unwrap()`.
- Avoid segfaults when hitting OOM
- Improve performance of the `text` method. Text fragments are now concatenated as raw bytes, up to 5x faster.
- Fix `skip_empty` being ignored by `text(deep=True)`
- Fix `text()` raising `UnicodeDecodeError` on undecodable bytes when `deep=False`. It now substitutes
  U+FFFD, like the deep path always did
- Fix handling of the `id` method on text nodes
- Fix `attrs[key] = value` raising `AttributeError` instead of `TypeError` when `value` is not a string
- Prevent segfaults when instantiating `LexborNode` or `LexborAttributes` directly.
- Fix `unwrap()` corrupting the tree in some cases.
- Fix `head` and `body` going stale once `<head>`/`<body>` is removed from the document.
- Fix `attrs` reading freed memory when it outlives the node it was obtained from.
- Fix memory leak in `attrs[key] = None`; it leaked the value buffer header on every call.
- Fix possible memory leak in `clone()`
- Add `encoding=True` to `LexborHTMLParser`, which detects the encoding of `bytes` input and
  transcodes it to UTF-8 before parsing.

# Version 0.4.13

- Support lexbor-only builds with `--disable-modest`
- Importing `selectolax` no longer automatically imports `selectolax.parser` and `selectolax.lexbor`
- Update lexbor

# Version 0.4.12

- Add `options` parameter to `LexborHTMLParser` to pass Lexbor document parsing options
  (for example, `LexborDocumentOptions.WO_EVENTS` to disable mutation events). Fixes #221.
- Fix `LexborHTMLParser.clone()` losing nodes for empty HTML fragments
- Allow empty elements in `text_lexbor`. Fixes #220.
- Update lexbor

# Version 0.4.11

- Add NULL checks for CSS selectors module to prevent crashes
- Fix html5test pretty print serialization mode checks
- Update lexbor

# Version 0.4.10

- Do not destroy nodes when stripping tags
- Allow building selectolax using older lexbor versions (#218)
- Update lexbor. Fixes crashes when parsing HTML (#217).

# Version 0.4.9

- Add an ability to specify tags and namespace for fragmented parser
- Add a new serialization mode when pretty printing: `html5test`
- Allow empty HTML fragments
- Fix attrs access for non-element nodes
- Improve buffer cleanups
- Fix duplicate text when doing `text(deep=True)` on a text node
- Improve text concatenation performance
- Improve attribute handling

# Version 0.4.8

- Add Add `html_pretty`, `inner_html_pretty` methods
- Enable free-threading
- Improve `merge_text_nodes`
- Update lexbor


# Version 0.4.7

- Fix `.text()` and `iter()` for HTML fragments when there are multiple nodes at the root level. Resolves #209.
- Update lexbor. Resolves #212.
- Breaking changes: Empty tags are now serialized to `<div value="">` instead of `<div value>`
  ([Commit 4530fed](https://github.com/lexbor/lexbor/commit/4530fed3f3a2b1c3729f7742be4f56131cb8e086)).
- Improve `unwrap_tags` and `merge_text_nodes`.

# Version 0.4.6

- Fix HTML parsing in fragment parser for `LexborHTMLParser`
- Fix memory leak in fragment parser
- Improve `skip_empty` parameter for text methods
- Add `comment_content` method
- Minor performance optimizations
- Add `create_tag` method to `LexborHTMLParser`
- Fix advanced selector (`.select()`) when attributes are empty.


# Version 0.4.5

  - Broken release. Not published to PyPi.

# Version 0.4.4

- Add `is_fragment` parameter to `LexborHTMLParser` @pygarap

- Add the ability to skip empty text nodes for lexbor backend to `.text`, `.iter`, `.traverse` @pygarap

- Add new properties to lexbor backend: `is_element_node`, `is_text_node`, `is_comment_node`, `is_document_node`.  @pygarap
- Update `lexbor` library


# Version 0.4.3

- Update `lexbor` library
- Fix missing description on PyPi.


# Version 0.4.2

- Broken release. Not published to PyPi.

# Version 0.4.1

- Fix parsing of CSS selectors that contain Unicode characters.

# Version 0.4.0

- Fix incorrect default value in docstrings for strict argument
- Fix incorrect exception handling for `any_css_matches`
- Fix docstring for `css_first` method
- Fix memory leak in `merge_text_nodes` for lexbor backend
- Update lexbor backend
- Add `.inner_html` property. Allows to get and set inner HTML of a node.
- Update various docstrings.
- Optimize performance for`css_first` in lexbor backend
- Fix segfaults when accessing attributes. Resolves #135.
- Add new `.clone` method to lexbor backend. Resolve #117.
- Improve unicode handling for malformed text. Resolves #138.
- Fix segfaults when doing double `.decompose`. Resolves #179.
- Fix sefgaults when doing double `.unwrap`. Resolves #169.
- Fix typo for tag names. Clarify available tag names.

## Version 0.3.34

Released

- Lexbor backend now supports `:lexbor-contains("abc" i)` CSS pseudo-class to match text nodes.

## Version 0.3.33

Released

- Add `merge_text_nodes` to lexbor backend. Fixes #170. @amirshukayev
- Performance improvements in Cython code. @Vizonex

## Version 0.3.32

Released

- Update lexbor. New version of lexbor fixes bugs with CSS selectors.

## Version 0.3.31

Released

- Improve type hints, add docstrings to type hints
- Prevent decomposing of the root node
- Unpin Cython version and make it Optional
- Allow empty attribute values. Fixes #165.

## Version 0.3.30

Released

- Update lexbor
- Expose `SelectolaxError` exception in lexbor.pyi

## Version 0.3.29

Released

- Feat: Add unwrap empty tags functionality. Fixes #159.

## Version 0.3.28

Released

- Fix: Update lexbor and improve HTML serialization speed. Fixes #153.
- Fix: typo in type annotations. Fixes #147.
- Fix: Fix incorrect type annotations for `LexborHTMLParser.__init__`. Fixes #144.

## Version 0.3.27

Released

- Fix: Header detected as head

## Version 0.3.26

Released

- Improve type hints

## Version 0.3.25

Released

- Feat: Add `parse_fragment()` and `create_tag()`
- Add missing typing for `Node.insert_child()`
- Add `Node.parser` to access the `HTMLParser` to which the node belongs

## Version 0.3.24

Released

- Add `Node.insert_child` method to lexbor and modest backends

## Version 0.3.23

Released

- Add Python 3.13 wheels
- Update lexbor

## Version 0.3.21

Released

- ***Breaking change***: `lexbor` backend now includes the root node when querying CSS selectors. Same as `Modest` backend.
- Fix `css_matches` and `any_css_matches` methods for `Modest` backend on some compilers

## Version 0.3.20

Released

- Fixup for 0.3.19 release
- Fix tag order for `lexbor` backend

## Version 0.3.19

Released

- Increase maximum HTML size to 2.4GB

## Version 0.3.18

Released

- Fix memory leak when using CSS selectors, `lexbor` backend

## Version 0.3.17

Released

- Update lexbor
- Add Python 3.12 wheels

## Version 0.3.16

Released

- Make HTML nodes hashable
- Pin Cython version

## Version 0.3.15

Released

- Improve typing. Thanks to @nesb1

## Version 0.3.14

Released

- Fix memory leak for `lexbor` backend

## Version 0.3.13

Released

- Update `lexbor`

## Version 0.3.12

Released

- Update `lexbor`
- Add Python 3.11 wheels

## Version 0.3.11

Released

- Fix out-of-bounds bug for `merge_text_nodes` method.

## Version 0.3.10

Released

This release does not contain any changes.
Due to a typo in the version number ([#70](https://github.com/rushter/selectolax/issues/70)), we need to make a new release.

## Version 0.3.9

Released

- Remove trailing separator when using `text(deep=True, separator='x')`.
- Add a new `merge_text_nodes` method for Modest backend.

## Version 0.3.8

Released

- Fix incorrect text handling when using `text(deep=True)` on a text node.

## Version 0.3.7

Released

- Fix return type of HTMLParser.tags

## Version 0.3.6

Released

- Improve text handling
- Add binary builds for Python 3.10 and ARM on MacOS and Linux

## Version 0.3.5

Released

- Add type annotations

## Version 0.3.4

Released

- Fix `HTMLParser.html`

## Version 0.3.3

Released

- Use `document` for the `HTMLParser.html`, `LexborHTMLParser.html` root properties

## Version 0.3.2

Released

- Fix `selector` method for lexbor
- Improve text extraction for lexbor

## Version 0.3.1

Released

- Fix `setup.py` for Windows

## Version 0.3.0

Released

- Added `lexbor` backend
- Fix cloning for `Modest` backend

## Version 0.2.14

Released

- Added advanced Selector (the `select` method)
- Improved speed of `strip_tags`
- Added `clone` method for the `HtmlParser` object
- Exposed `detect_encoding`, `decode_errors`, `use_meta_tags`, `raw_html` attributes for `HtmlParser`
- Added `sget` method to the `attrs` property

## Version 0.2.13

Released

- Don't throw exception when encoding text as UTF-8 bytes fails ([#40](https://github.com/rushter/selectolax/issues/40)).
- Fix Node.attrs.items() causes ([#39](https://github.com/rushter/selectolax/issues/39)).

## Version 0.2.12

Released

- Build wheels Apple Silicon

## Version 0.2.11

Released

- Fix strip argument is ignored for the root node ([#35](https://github.com/rushter/selectolax/issues/35)).
- Fix CSS parser hangs on a bad CSS selector ([#36](https://github.com/rushter/selectolax/issues/36)).

## Version 0.2.10

Released

- Fix root node property ([#32](https://github.com/rushter/selectolax/issues/32)). The `root` property now points to the html tag.

## Version 0.2.9

Released

- Fix README for PyPI

## Version 0.2.8

Released

- Add wheels for Python 3.9

## Version 0.2.7

Released

- Add `raw_value` attribute for `Node` objects ([#22](https://github.com/rushter/selectolax/issues/22))
- Improve node modification operations

## Version 0.2.6

Released

- Fix dependency on the source `Node` when inserting to or modifying destination `Node`

## Version 0.2.5

Released

- Allow to pass Node instances to `replace_with`, `insert_before` and `insert_after` methods
- Added `insert_before` and `insert_after` methods

## Version 0.2.4

Released

- Set maximum input size to 80MB
- Update modest

## Version 0.2.3

Released

- Rebuild PyPi wheels to support Python 3.8 and manylinux2010

## Version 0.2.2

Released

- Fix node comparison

## Version 0.2.1

Released

- Add optional `include_text` parameter for the `iter` and `traverse` methods

## Version 0.2.0

Released

- Fix `iter()` does not yield text nodes
- Switch from TravisCI to Github Actions
- Build and ship wheels for Windows, MacOS and Linux using Azure Pipelines
- Add `unwrap` and `unwrap_tags` method ([#7](https://github.com/rushter/selectolax/issues/7))
- Add `replace_with` method ([#13](https://github.com/rushter/selectolax/issues/13))
- Add `attrs` property
- Add `traverse` method
