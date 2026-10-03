"""Tests for functionality that is only supported by lexbor backend."""

from gc import collect as gc_collect
from inspect import cleandoc

import pytest

from selectolax.lexbor import (
    LexborDocumentOptions,
    LexborHTMLParser,
    SelectolaxError,
)


def clean_doc(text: str) -> str:
    return f"{cleandoc(text)}\n"


def _top_level_nodes(parser):
    """The fragment's top-level nodes, reached the way the library reaches them."""
    node = parser.root
    while node is not None:
        yield node
        node = node.next


def test_reads_inner_html():
    html = """<div id="main"><div>Hi</div><div id="updated">2025-09-27</div></div>"""
    parser = LexborHTMLParser(html)
    actual = parser.css_first("#main").inner_html
    expected = """<div>Hi</div><div id="updated">2025-09-27</div>"""
    assert actual == expected


def test_sets_inner_html():
    html = """<div id="main"><div>Hi</div><div id="updated">2025-09-27</div></div>"""
    parser = LexborHTMLParser(html)
    expected = "<span>Test</span>"
    parser.css_first("#main").inner_html = "<span>Test</span>"
    actual = parser.css_first("#main").inner_html
    assert actual == expected


def test_html_pretty_document():
    parser = LexborHTMLParser("<div><span>Hello</span><!-- note --></div>")
    assert parser.html_pretty() == clean_doc(
        """
        <html>
          <head>
          </head>
          <body>
            <div>
              <span>
                "Hello"
              </span>
              <!--  note  -->
            </div>
          </body>
        </html>
        """
    )


def test_html_pretty_node_with_options():
    parser = LexborHTMLParser("<div><span>Hello</span><!-- note --></div>")
    node = parser.css_first("div")
    assert node.html_pretty(skip_comment=True) == clean_doc(
        """
        <div>
          <span>
            "Hello"
          </span>
        </div>
        """
    )


def test_html_pretty_skip_ws_nodes_option():
    parser = LexborHTMLParser("<div>\n</div><span></span>", is_fragment=True)
    assert parser.html_pretty(skip_ws_nodes=True) == clean_doc(
        """
        <div>
        </div>
        <span>
        </span>
        """
    )


def test_inner_html_pretty_node_with_options():
    parser = LexborHTMLParser("<div><span>Hello</span><!-- note --></div>")
    node = parser.css_first("div")
    assert node.inner_html_pretty(skip_comment=True) == clean_doc(
        """
        <span>
          "Hello"
        </span>
        """
    )


def test_inner_html_pretty_parser():
    parser = LexborHTMLParser("<div><span>Hello</span></div>", is_fragment=True)
    assert parser.inner_html_pretty(skip_ws_nodes=True) == clean_doc(
        """
        <span>
          "Hello"
        </span>
        """
    )


def test_html_pretty_rejects_negative_indent():
    parser = LexborHTMLParser("<div>Hello</div>")
    with pytest.raises(ValueError):
        parser.html_pretty(indent=-1)


def test_inner_html_pretty_rejects_negative_indent():
    parser = LexborHTMLParser("<div>Hello</div>")
    with pytest.raises(ValueError):
        parser.inner_html_pretty(indent=-1)


def test_checking_attributes_does_not_segfault():
    parser = LexborHTMLParser("")
    root_node = parser.root
    assert root_node is not None
    for node in root_node.traverse():
        parent = node.parent
        assert parent is not None
        parent = parent.attributes.get("anything")


def test_node_cloning():
    parser = LexborHTMLParser("<div id='main'>123</div>")
    new_node = parser.css_first("#main").clone()
    new_node.inner_html = "<div>new</div>"
    assert parser.css_first("#main").html != new_node.html
    assert new_node.html == '<div id="main"><div>new</div></div>'


def test_double_unwrap_does_not_segfault():
    html = """<div><div><div></div></div></div>"""
    outer_div = LexborHTMLParser(html, is_fragment=True).root
    some_set = set()

    inner_div = outer_div.child
    assert inner_div is not None
    inner_div.unwrap()
    inner_div.unwrap()
    some_set.add(outer_div.parent)
    some_set.add(outer_div.parent)


def test_unicode_selector_works():
    html = '<span data-original-title="Pneu renforcé"></span>'
    tree = LexborHTMLParser(html)
    node = tree.css_first('span[data-original-title="Pneu renforcé"]')
    assert node.tag == "span"


def test_node_type_helpers():
    html = "<div id='main'>text<!--comment--></div>"
    parser = LexborHTMLParser(html)

    div_node = parser.css_first("#main")
    assert div_node.is_element_node
    assert not div_node.is_text_node

    text_node = div_node.first_child
    assert text_node is not None
    assert text_node.is_text_node
    assert not text_node.is_element_node

    comment_node = div_node.last_child
    assert comment_node is not None
    assert comment_node.is_comment_node
    assert not comment_node.is_text_node

    document_node = parser.root.parent
    assert document_node is not None
    assert document_node.is_document_node
    assert not document_node.is_element_node


def test_text_honors_skip_empty_flag():
    parser = LexborHTMLParser("<div><span>value</span><title>\n   \n</title></div>")
    span = parser.css_first("span")
    assert span is not None
    assert span.text(deep=False, skip_empty=False) == "value"
    assert span.text(deep=False, skip_empty=True) == "value"
    title = parser.css_first("title")
    assert title is not None
    assert title.text(deep=False, skip_empty=False) == "\n   \n"
    assert title.text(deep=False, skip_empty=True) == ""


def test_text_lexbor_on_empty_strings():
    parser = LexborHTMLParser("<div></div>")
    div = parser.css_first("div")
    assert div is not None
    assert div.text_lexbor() == ""

    parser = LexborHTMLParser("<div><p></p><p>foo</p></div>")
    div = parser.css_first("div")
    assert div is not None
    assert div.text_lexbor() == "foo"

    parser = LexborHTMLParser("")
    assert parser.root.text_lexbor() == ""


@pytest.mark.parametrize(
    "html",
    [
        "hello",
        "a<span>s</span>",
        "lead<span>x</span>tail",
        "<div>a</div><span>s</span>",
        "<div><i>x</i>y</div>",
        "a<b>c</b>d",
        "<!--k--><b>c</b>",
        "only text",
        "<div>one</div><div>two</div>",
    ],
)
def test_text_lexbor_covers_whole_fragment(html):
    """``text_lexbor()`` must widen like ``text()`` does on a fragment root."""
    parser = LexborHTMLParser(html, is_fragment=True)
    root = parser.root
    assert root.text_lexbor() == parser.text()
    assert root.text_lexbor() == root.text()


def test_text_lexbor_on_a_text_node_reports_only_itself():
    """Widening must not make a text node report its siblings too."""
    parser = LexborHTMLParser("<div>hi</div><p>yo</p>")
    for tag, expected in (("div", "hi"), ("p", "yo")):
        text_node = parser.css_first(tag).first_child
        assert text_node.is_text_node
        assert text_node.text_lexbor() == expected


def test_merge_text_nodes_merges_top_level_runs_of_a_fragment():
    parser = LexborHTMLParser("<div>1</div><p><i>a</i></p>", is_fragment=True)

    # Unwrapping the <p> lifts its <i> to the top level, then two text nodes get
    # inserted in front of it, forming a run of adjacent text nodes that lives
    # beside the fragment root rather than inside it.
    parser.root.next.unwrap()
    node = parser.root.next
    node.insert_before("X")
    node.insert_before("Y")

    top_level = [(n.tag, n.text_content) for n in _top_level_nodes(parser)]
    assert top_level == [("div", None), ("-text", "X"), ("-text", "Y"), ("i", None)]

    parser.merge_text_nodes()
    assert [(n.tag, n.text_content) for n in _top_level_nodes(parser)] == [
        ("div", None),
        ("-text", "XY"),
        ("i", None),
    ]


def test_merge_text_nodes_on_a_non_root_node_stays_scoped():
    parser = LexborHTMLParser("<div>1</div><p><i>a</i></p>", is_fragment=True)
    parser.root.next.unwrap()
    node = parser.root.next
    node.insert_before("X")
    node.insert_before("Y")

    node.merge_text_nodes()

    assert [(n.tag, n.text_content) for n in _top_level_nodes(parser)] == [
        ("div", None),
        ("-text", "X"),
        ("-text", "Y"),
        ("i", None),
    ]


def test_merge_text_nodes_on_a_detached_fragment_root_is_a_safe_noop():
    parser = LexborHTMLParser("<div>a<span>s</span></div><p>b</p>", is_fragment=True)
    root = parser.root
    root.decompose()

    root.merge_text_nodes()

    assert root.text() == ""
    assert root.text_lexbor() == ""
    assert parser.html == "<p>b</p>"


def test_attrs_reject_non_element_nodes():
    parser = LexborHTMLParser("<div>hello<!--comment--></div>")
    div = parser.css_first("div")
    text_node = div.first_child
    comment_node = div.last_child

    assert text_node is not None
    assert comment_node is not None
    assert text_node.is_text_node
    assert comment_node.is_comment_node

    with pytest.raises(TypeError, match="element nodes"):
        _ = text_node.attrs

    with pytest.raises(TypeError, match="element nodes"):
        _ = comment_node.attrs


def test_id_of_non_element_nodes_returns_none():
    parser = LexborHTMLParser("<!DOCTYPE html><div id='real'>text<!--note--></div>")
    div = parser.css_first("div")

    text_node = div.first_child
    comment_node = div.last_child
    document_node = parser.root.parent
    doctype_node = parser.root.prev

    assert text_node is not None and text_node.is_text_node
    assert comment_node is not None and comment_node.is_comment_node
    assert document_node is not None and document_node.is_document_node

    assert text_node.id is None
    assert comment_node.id is None
    assert document_node.id is None
    assert doctype_node.id is None

    assert div.id == "real"


def test_id_of_element_nodes():
    parser = LexborHTMLParser(
        "<div id='a'><span id='b'>x</span></div><i id=''></i><p></p>"
    )
    assert parser.css_first("div").id == "a"
    assert parser.css_first("span").id == "b"
    assert parser.css_first("i").id == ""
    assert parser.css_first("p").id is None


def test_inner_html_setter_rejects_non_element_nodes():
    """Regression test: lexbor grafts children onto any node type.

    Assigning ``inner_html`` on a text or comment node used to attach element
    children to it, leaving the node with a type that no longer matches its
    contents. Every accessor then disagreed: ``.html`` included the injected
    markup, ``.text(deep=True)`` counted it as text, but ``.text_content``,
    ``.text(deep=False)`` and ``.text_lexbor()`` ignored it.
    """
    parser = LexborHTMLParser("<div>hello<p>world</p><!--note--></div>")
    div = parser.css_first("div")
    non_elements = [
        node for node in div.iter(include_text=True) if not node.is_element_node
    ]
    assert [node.tag for node in non_elements] == ["-text", "-comment"]

    before = parser.html
    for node in non_elements:
        with pytest.raises(TypeError, match="element nodes"):
            node.inner_html = "<b>injected</b>"

    assert parser.html == before


def test_inner_html_setter_rejects_document_node():
    parser = LexborHTMLParser("<div>hi</div>")
    document = parser.css_first("div").parent.parent.parent
    assert document is not None
    assert document.is_document_node

    before = parser.html
    with pytest.raises(TypeError, match="element nodes"):
        document.inner_html = "<b>injected</b>"

    assert parser.html == before


def test_tag_of_document_node_is_document():
    doctypes = [
        "<!DOCTYPE html>",
        "<!DOCTYPE svg>",
        '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "x.dtd">',
    ]
    for doctype in [*doctypes, None]:
        html = f"{doctype or ''}<div>hi</div>"
        document = LexborHTMLParser(html).root.parent
        assert document is not None
        assert document.is_document_node
        assert document.tag == "-document"
        assert repr(document) == "<LexborNode -document>"


def test_tag_of_non_element_nodes():
    parser = LexborHTMLParser("<!DOCTYPE html><div>text<!--comment--></div>")
    div = parser.css_first("div")

    assert div.tag == "div"
    assert div.first_child.tag == "-text"
    assert div.last_child.tag == "-comment"
    assert parser.root.prev.tag == "-doctype"
    assert parser.root.parent.tag == "-document"


def test_sets_inner_html_on_html_keeps_head_and_body_in_sync():
    """Regression test: parser.head/parser.body used to dangle.

    ``lxb_html_element_inner_html_set`` replaces the children of ``<html>``
    directly, bypassing the insertion modes that normally populate the
    document's cached head/body pointers. Those pointers then referenced
    destroyed nodes while ``parser.html`` walked the live tree, so the two
    disagreed about the same document.
    """
    parser = LexborHTMLParser(
        "<html><head><title>Title</title></head><body><div>hi</div></body></html>"
    )
    parser.root.inner_html = "<main>new</main>"

    assert parser.html == "<html><head></head><body><main>new</main></body></html>"
    assert parser.head is not None
    assert parser.body is not None
    assert parser.head.tag == "head"
    assert parser.body.tag == "body"
    assert parser.head.html == "<head></head>"
    assert parser.body.html == "<body><main>new</main></body>"
    assert parser.body.text() == "new"


def test_head_and_body_survive_allocations_after_inner_html():
    """Regression test: the stale pointers aliased recycled memory.

    Destroyed lexbor blocks go back onto a size-keyed free list
    (``lexbor_mraw_free``), so the next same-size allocation is handed the very
    same address. Before the fix, ``parser.body`` ended up pointing at an
    unrelated live ``<span>`` created after the assignment.
    """
    parser = LexborHTMLParser(
        "<html><head><title>Title</title></head><body><div>hi</div></body></html>"
    )
    parser.root.inner_html = "<main>new</main>"

    head, body = parser.head, parser.body
    assert head is not None
    assert body is not None

    for _ in range(50):
        allocated = parser.create_node("span")
        assert allocated.mem_id != head.mem_id
        assert allocated.mem_id != body.mem_id

    assert parser.head.tag == "head"
    assert parser.body.tag == "body"
    assert parser.body.text() == "new"


@pytest.mark.parametrize("target", ["head", "body"])
def test_sets_inner_html_on_head_or_body_keeps_pointers_valid(target: str):
    """Only ``<html>`` loses its head/body children, so only it needs a refresh."""
    parser = LexborHTMLParser(
        "<html><head><title>Title</title></head><body><div>hi</div></body></html>"
    )
    node = parser.css_first(target)
    assert node is not None
    node.inner_html = "<meta charset='utf-8'>"

    head, body = parser.head, parser.body
    assert head is not None
    assert body is not None
    assert head.tag == "head"
    assert body.tag == "body"

    if target == "head":
        assert head.html == '<head><meta charset="utf-8"></head>'
        assert body.html == "<body><div>hi</div></body>"
    else:
        assert head.html == "<head><title>Title</title></head>"
        assert body.html == '<body><meta charset="utf-8"></body>'


def test_sets_inner_html_on_nested_element_keeps_head_and_body():
    parser = LexborHTMLParser(
        "<html><head><title>Title</title></head><body><div>hi</div></body></html>"
    )
    parser.css_first("div").inner_html = "<span>new</span>"

    assert parser.head is not None
    assert parser.body is not None
    assert parser.head.html == "<head><title>Title</title></head>"
    assert parser.body.html == "<body><div><span>new</span></div></body>"


def test_sets_inner_html_on_fragment_root_leaves_head_and_body_absent():
    parser = LexborHTMLParser("<div>hi</div>", is_fragment=True)
    assert parser.head is None
    assert parser.body is None

    parser.root.inner_html = "<span>new</span>"

    assert parser.head is None
    assert parser.body is None


_HEAD_BODY_HTML = (
    "<html><head><title>Title</title></head><body><div>hi</div></body></html>"
)
_EMPTY_HEAD_BODY_HTML = "<html><head></head><body></body></html>"

# Every operation that can unlink <head>/<body> from the document.
_HEAD_BODY_DETACHING_OPS = [
    "unwrap",
    "unwrap_empty",
    "decompose",
    "decompose_shallow",
    "remove",
    "replace_with",
    "strip_tags",
    "unwrap_tags",
    "parser_strip_tags",
]


@pytest.mark.parametrize("target", ["head", "body"])
@pytest.mark.parametrize("operation", _HEAD_BODY_DETACHING_OPS)
def test_head_and_body_are_cleared_once_detached(target: str, operation: str):
    """Regression test: ``parser.head`` / ``parser.body`` returned a stale node.

    Lexbor writes ``document->head`` and ``document->body`` from the parser's
    insertion modes and never clears them again, and
    ``lxb_html_document_head_element_noi`` returns that cache verbatim. So
    unlinking either element left the cache pointing at a node that was no
    longer part of the document, and ``parser.body`` happily handed out a
    detached ``<body></body>`` after ``parser.body.unwrap()``.
    """
    # ``unwrap(delete_empty=True)`` only removes a childless node, so that one
    # case needs an empty <head>/<body>.
    parser = LexborHTMLParser(
        _EMPTY_HEAD_BODY_HTML if operation == "unwrap_empty" else _HEAD_BODY_HTML
    )
    node = parser.css_first(target)
    assert node is not None

    if operation == "unwrap":
        node.unwrap()
    elif operation == "unwrap_empty":
        node.unwrap(delete_empty=True)
    elif operation == "decompose":
        node.decompose()
    elif operation == "decompose_shallow":
        node.decompose(recursive=False)
    elif operation == "remove":
        node.remove()
    elif operation == "replace_with":
        node.replace_with("<div>replacement</div>")
    elif operation == "strip_tags":
        node.strip_tags([target])
    elif operation == "unwrap_tags":
        node.unwrap_tags([target])
    elif operation == "parser_strip_tags":
        parser.strip_tags([target])
    else:  # pragma: no cover - guards against an unhandled new case
        raise AssertionError(f"unhandled operation {operation!r}")

    assert node.parent is None
    assert getattr(parser, target) is None


def test_unwrapping_html_keeps_head_and_body():
    """Removing ``<html>`` must not orphan the elements it still contains.

    ``unwrap()`` promotes ``<head>``/``<body>`` to children of the document
    rather than destroying them, so the caches stay valid and both elements
    must still be reported. Only detaching ``<head>``/``<body>`` themselves
    clears them.
    """
    parser = LexborHTMLParser(_HEAD_BODY_HTML)
    parser.css_first("html").unwrap()

    head, body = parser.head, parser.body
    assert head is not None
    assert body is not None
    assert head.tag == "head"
    assert body.tag == "body"
    assert head.parent is not None
    assert head.parent.tag == "-document"
    assert body.parent is not None
    assert body.parent.tag == "-document"
    assert head.html == "<head><title>Title</title></head>"
    assert body.html == "<body><div>hi</div></body>"


def test_detaching_body_leaves_head_reported():
    """Clearing one must not disturb the other."""
    parser = LexborHTMLParser(_HEAD_BODY_HTML)
    head_before = parser.head
    assert head_before is not None

    parser.body.unwrap()

    assert parser.body is None
    head_after = parser.head
    assert head_after is not None
    assert head_after.mem_id == head_before.mem_id
    assert head_after.html == "<head><title>Title</title></head>"
    assert parser.html == "<html><head><title>Title</title></head><div>hi</div></html>"


def test_text_does_not_duplicate_fragment_root_text_node():
    parser = LexborHTMLParser("hello", is_fragment=True)
    root = parser.root
    assert root is not None
    assert root.is_text_node
    assert root.text(deep=True) == "hello"


@pytest.mark.parametrize(
    "html, expected_text, expected_deep_false",
    [
        ("hello", "hello", "hello"),
        ("a<span>s</span>", "as", "a"),
        ("lead<span>x</span>tail", "leadxtail", "leadtail"),
        ("a<b>c</b>d", "acd", "ad"),
        ("a<!--k--><b>c</b>", "ac", "a"),
    ],
)
def test_fragment_root_text_node_covers_whole_fragment(
    html, expected_text, expected_deep_false
):
    """A fragment that starts with text must not lose its siblings.

    The root is widened to the wrapper so the walk covers every top-level node,
    which means the root's own data is reached by the walk. It must therefore
    not also be added on the side, or it would be duplicated.
    """
    parser = LexborHTMLParser(html, is_fragment=True)
    root = parser.root
    assert root.is_text_node

    assert root.text() == expected_text
    assert root.text(deep=True) == expected_text
    assert root.text(deep=False) == expected_deep_false
    assert parser.text() == expected_text


@pytest.mark.parametrize(
    "html, query, expected_count",
    [
        ("a<span>s</span><b>b</b>", "span", 1),
        ("a<span>s</span><b>b</b>", "b", 1),
        ("a<span>s</span><b>b</b>", "i", 0),
        ("lead<span>x</span>tail<b>c</b>", "b", 1),
    ],
)
def test_fragment_root_text_node_css_covers_whole_fragment(html, query, expected_count):
    """Tree walks from a text-node fragment root reach every top-level node."""
    parser = LexborHTMLParser(html, is_fragment=True)
    root = parser.root
    assert root.is_text_node

    assert len(root.css(query)) == expected_count
    assert len(root.select(query).matches) == expected_count
    assert root.css_matches(query) is (expected_count > 0)
    assert root.any_css_matches((query,)) is (expected_count > 0)
    assert (root.css_first(query) is not None) is (expected_count > 0)


def test_fragment_root_text_node_iter_covers_whole_fragment():
    parser = LexborHTMLParser("a<span>s</span><b>b</b>", is_fragment=True)
    root = parser.root
    assert root.is_text_node

    assert [node.tag for node in root.iter()] == ["span", "b"]
    assert [node.tag for node in root.iter(include_text=True)] == [
        "-text",
        "span",
        "b",
    ]


def test_text_node_fragment_root_text_node_owns_its_own_data():
    """A text node that is not a fragment root only reports itself."""
    parser = LexborHTMLParser("<div>hi</div><p>yo</p>")
    for tag in ("div", "p"):
        text_node = parser.css_first(tag).first_child
        assert text_node.is_text_node
        assert text_node.text() == text_node.text_content
        assert text_node.text(deep=True) == text_node.text_content
        assert text_node.text(deep=False) == text_node.text_content
    assert parser.css_first("div").first_child.text_content == "hi"
    assert parser.css_first("p").first_child.text_content == "yo"


def test_iter_includes_text_nodes_when_requested():
    parser = LexborHTMLParser("<div><span>value</span><title>\n   \n</title></div>")
    div = parser.css_first("div")
    children = [node for node in div.iter(include_text=True, skip_empty=True)]
    assert (
        ", ".join(
            node.tag for node in children[0].iter(include_text=True, skip_empty=True)
        )
        == "-text"
    )
    assert (
        ", ".join(
            node.tag for node in children[1].iter(include_text=True, skip_empty=True)
        )
        == ""
    )


def test_traverse_respects_skip_empty_on_text_nodes():
    parser = LexborHTMLParser("<div><span>value</span><title>\n   \n</title></div>")
    div = parser.css_first("div")
    children = [node.tag for node in div.traverse(include_text=True, skip_empty=True)]
    assert ", ".join(children) == "div, span, -text, title"


def test_traverse_with_skip_empty_on_a_full_html_document():
    html = clean_doc(
        """
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title>Title!</title>
            <!-- My crazy comment -->
          </head>
          <body>
            <p>Hello <strong>World</strong>!</p>
            <div hidden draggable="true" translate="no" contenteditable="true" tabindex="3">
              Div
            </div>
          </body>
        </html>
        """
    )
    parser = LexborHTMLParser(html)
    children = [
        (node.tag, node.text_content)
        for node in parser.root.traverse(include_text=True, skip_empty=False)
    ]
    assert children == [
        ("html", None),
        ("head", None),
        ("-text", "\n    "),
        ("meta", None),
        ("-text", "\n    "),
        ("meta", None),
        ("-text", "\n    "),
        ("title", None),
        ("-text", "Title!"),
        ("-text", "\n    "),
        ("-comment", None),
        ("-text", "\n  "),
        ("-text", "\n  "),
        ("body", None),
        ("-text", "\n    "),
        ("p", None),
        ("-text", "Hello "),
        ("strong", None),
        ("-text", "World"),
        ("-text", "!"),
        ("-text", "\n    "),
        ("div", None),
        ("-text", "\n      Div\n    "),
        ("-text", "\n  \n\n"),
    ]
    children = [
        (node.tag, node.text_content)
        for node in parser.root.traverse(include_text=True, skip_empty=True)
    ]
    assert children == [
        ("html", None),
        ("head", None),
        ("meta", None),
        ("meta", None),
        ("title", None),
        ("-text", "Title!"),
        ("-comment", None),
        ("body", None),
        ("p", None),
        ("-text", "Hello "),
        ("strong", None),
        ("-text", "World"),
        ("-text", "!"),
        ("div", None),
        ("-text", "\n      Div\n    "),
    ]


def test_is_empty_text_node_property():
    parser = LexborHTMLParser("<div><span>\n \n</span><title>X</title></div>")
    text_node = parser.css_first("span").first_child
    assert text_node.text_content == "\n \n"
    assert text_node.is_empty_text_node
    text_node = parser.css_first("title").first_child
    assert text_node.text_content == "X"
    assert not text_node.is_empty_text_node


def test_comment_content_property() -> None:
    parser = LexborHTMLParser("<div><span><!-- hello --></span><title>X</title></div>")
    span = parser.css_first("span")
    assert span is not None
    text_node = span.first_child
    assert text_node is not None
    assert text_node.is_comment_node
    assert text_node.comment_content == "hello"


def test_selector_text_contains():
    html = """
    <div>
        <p>Hello world</p>
        <p>Goodbye world</p>
        <span>No match here</span>
    </div>
    """
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    selector = root.select("p").text_contains("Hello")
    assert len(selector.matches) == 1
    assert selector.matches[0].text() == "Hello world"
    assert selector.any_matches is True


def test_selector_any_text_contains():
    html = """
    <div>
        <p>Hello world</p>
        <p>Goodbye world</p>
        <span>No match here</span>
    </div>
    """
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    assert root.select("p").any_text_contains("Hello") is True
    assert root.select("p").any_text_contains("world") is True
    assert root.select("p").any_text_contains("nomatch") is False


def test_selector_attribute_longer_than():
    html = """
    <div>
        <a href="short">Link 1</a>
        <a href="http://very-long-url.com/path">Link 2</a>
        <a href="medium">Link 3</a>
    </div>
    """
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    selector = root.select("a").attribute_longer_than("href", 10)
    assert len(selector.matches) == 1
    href = selector.matches[0].attributes["href"]
    assert href is not None
    assert "very-long-url" in href


def test_selector_any_attribute_longer_than():
    html = """
    <div>
        <a href="short">Link 1</a>
        <a href="http://very-long-url.com/path">Link 2</a>
        <a href="medium">Link 3</a>
    </div>
    """
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    assert root.select("a").any_attribute_longer_than("href", 10) is True
    assert root.select("a").any_attribute_longer_than("href", 50) is False


def test_selector_attribute_longer_than_with_start():
    html = """
    <div>
        <a href="http://short.com">Link 1</a>
        <a href="http://very-long-domain-name.com/path">Link 2</a>
        <a href="http://medium.com">Link 3</a>
    </div>
    """
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    selector = root.select("a").attribute_longer_than("href", 15, "http://")
    assert len(selector.matches) == 1
    href = selector.matches[0].attributes["href"]
    assert href is not None
    assert "very-long-domain-name" in href


def test_selector_chaining():
    html = """
    <div>
        <p class="important">Hello world</p>
        <p class="normal">Goodbye world</p>
        <p class="important">Important stuff</p>
        <span class="important">Not a paragraph</span>
    </div>
    """
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    selector = root.select("p").text_contains("world").attribute_longer_than("class", 6)
    assert len(selector.matches) == 1
    assert selector.matches[0].text() == "Hello world"
    assert selector.matches[0].attributes["class"] == "important"


def test_selector_empty_matches():
    html = "<div><p>Hello</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    selector = root.select("div").text_contains("nomatch")
    assert len(selector.matches) == 0
    assert selector.any_matches is False
    assert bool(selector) is False


def test_attributes_sget():
    html = '<div id="test" class="foo" empty></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None
    attrs = div.attrs
    assert attrs.sget("id") == "test"
    assert attrs.sget("class") == "foo"
    assert attrs.sget("empty") == ""  # Empty attributes return empty string
    assert attrs.sget("missing", "default") == "default"


def test_attributes_keys_values_items():
    html = '<div id="test" class="foo" data-value="123"></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None
    attrs = div.attrs

    keys = list(attrs.keys())
    assert "id" in keys
    assert "class" in keys
    assert "data-value" in keys

    values = list(attrs.values())
    assert "test" in values
    assert "foo" in values
    assert "123" in values

    items = dict(attrs.items())
    assert items["id"] == "test"
    assert items["class"] == "foo"
    assert items["data-value"] == "123"


def test_attributes_len_and_contains():
    html = '<div id="test" class="foo"></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None
    attrs = div.attrs

    assert len(attrs) == 2
    assert "id" in attrs
    assert "class" in attrs
    assert "missing" not in attrs


def test_attributes_get():
    html = '<div id="test" empty></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None
    attrs = div.attrs

    assert attrs.get("id") == "test"
    assert attrs.get("empty") is None  # Empty attributes return None
    assert attrs.get("missing") is None
    assert attrs.get("missing", "default") == "default"


def test_attributes_modification():
    html = '<div id="original"></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None
    attrs = div.attrs

    # new attribute
    attrs["new_attr"] = "new_value"
    assert attrs["new_attr"] == "new_value"

    # existing attribute
    attrs["id"] = "modified"
    assert attrs["id"] == "modified"

    # empty attribute
    attrs["empty"] = None
    assert attrs["empty"] is None

    # deleting attribute
    del attrs["id"]
    assert "id" not in attrs

    try:
        del attrs["nonexistent"]
        assert False, "Should have raised KeyError"
    except KeyError:
        pass


def test_attrs_setitem_rejects_non_str_values():
    parser = LexborHTMLParser('<div id="a"></div>')
    div = parser.root.css_first("div")
    attrs = div.attrs

    for value in (5, 0, 1.5, b"bytes", b"", [1], (), {"a": 1}, True, object()):
        with pytest.raises(TypeError, match="Expected str or unicode"):
            attrs["x"] = value

    assert "x" not in attrs
    assert div.html == '<div id="a"></div>'

    attrs["x"] = "value"
    assert attrs["x"] == "value"
    attrs["x"] = ""
    assert attrs["x"] == ""
    attrs["x"] = "ünïcödé 中文"
    assert attrs["x"] == "ünïcödé 中文"
    attrs["x"] = None
    assert attrs["x"] is None
    assert div.html == '<div id="a" x=""></div>'


def test_attrs_setitem_rejects_non_str_keys():
    parser = LexborHTMLParser('<div id="a"></div>')
    attrs = parser.root.css_first("div").attrs

    with pytest.raises(TypeError, match="expected str"):
        attrs[b"id"] = "b"
    assert attrs["id"] == "a"


def test_node_insert_operations_with_different_types():
    html = '<div><span id="target">target</span></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    target = root.css_first("#target")
    assert target is not None

    # Test insert_before with string
    target.insert_before("before_text")
    assert "before_text<span" in root.html

    # Test insert_after with bytes
    target.insert_after(b"after_bytes")
    assert "after_bytes</div>" in root.html


def test_node_replace_with_different_types():
    html = '<div><span id="target">old</span></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    target = root.css_first("#target")
    assert target is not None

    # Test replace_with string
    target.replace_with("replaced")
    assert root.html == "<html><head></head><body><div>replaced</div></body></html>"

    # Test replace_with bytes
    html = '<div><span id="target">old</span></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    target = root.css_first("#target")
    assert target is not None

    target.replace_with(b"bytes_replaced")
    assert "bytes_replaced" in root.html


def test_node_insert_with_lexbor_node():
    html1 = "<div>content1</div>"
    html2 = "<span>content2</span>"
    parser1 = LexborHTMLParser(html1)
    parser2 = LexborHTMLParser(html2)

    root1 = parser1.root
    root2 = parser2.root
    assert root1 is not None and root2 is not None

    div1 = root1.css_first("div")
    span2 = root2.css_first("span")
    assert div1 is not None and span2 is not None

    # Insert node from another parser
    div1.insert_child(span2)
    assert "<span>content2</span>" in root1.html


def test_node_manipulation_with_fragments():
    html = "<div>First</div><span>Second</span>"
    parser = LexborHTMLParser(html, is_fragment=True)
    root = parser.root
    assert root is not None

    span = root.next
    assert span is not None

    span.insert_before("Before")
    assert parser.html == "<div>First</div>Before<span>Second</span>"

    span.insert_after("After")
    assert parser.html == "<div>First</div>Before<span>Second</span>After"

    span.insert_child("Child")
    assert parser.html == "<div>First</div>Before<span>SecondChild</span>After"


def test_merge_text_nodes_edge_cases():
    html = "<div><p><strong>J</strong>ohn<strong>D</strong>oe</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None

    # Before unwrapping - text nodes are separated by strong tags
    text_before = div.text(deep=True, separator="")
    assert "JohnDoe" in text_before

    # Unwrap strong tags - this creates adjacent text nodes
    div.unwrap_tags(["strong"])

    # After unwrapping but before merging - text nodes are adjacent
    text_after_unwrap = div.text(deep=True, separator="")
    assert "JohnDoe" in text_after_unwrap

    # After merging - should be the same since they were already adjacent
    div.merge_text_nodes()
    text_after_merge = div.text(deep=True, separator="")
    assert "JohnDoe" in text_after_merge


def test_unwrap_tags_with_nested_elements():
    html = "<div><p><span><em>Text</em></span></p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None

    div.unwrap_tags(["span", "em"])
    html = root.html
    assert html is not None
    assert "<span>" not in html and "<em>" not in html
    assert "Text" in html


def test_unwrap_tags_delete_empty():
    html = "<div><p><span></span><em>Keep</em><i></i></p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    p = root.css_first("p")
    assert p is not None

    p.unwrap_tags(["span", "i"], delete_empty=True)
    html = root.html
    assert html is not None
    assert "<span>" not in html and "<i>" not in html
    assert "<em>Keep</em>" in html


def test_parser_clone_method():
    html = "<div id='original'><p>Original content</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None

    # Clone the parser
    cloned_parser = parser.clone()
    assert cloned_parser is not parser
    assert cloned_parser.html == parser.html

    # Modify the clone
    cloned_root = cloned_parser.root
    assert cloned_root is not None
    cloned_div = cloned_root.css_first("div")
    assert cloned_div is not None
    cloned_div.attrs["id"] = "modified"

    # Original should be unchanged
    original_div = root.css_first("div")
    assert original_div is not None
    assert original_div.attrs["id"] == "original"

    # Clone should be modified
    assert cloned_div.attrs["id"] == "modified"


def test_parser_select_method_returns_lexbor_selector():
    html = "<div><p>First</p><p>Second</p><p>Third</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None

    selector = root.select("p")
    assert hasattr(selector, "matches")
    assert hasattr(selector, "any_matches")
    assert hasattr(selector, "text_contains")
    assert len(selector.matches) == 3

    filtered = selector.text_contains("Second")
    assert len(filtered.matches) == 1
    assert filtered.matches[0].text() == "Second"


def test_parser_select_with_no_matches():
    html = "<div><p>Content</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None

    selector = root.select("span")
    assert len(selector.matches) == 0
    assert selector.any_matches is False
    assert bool(selector) is False


def test_parser_select_with_query():
    html = "<div><p class='important'>Important</p><p>Normal</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None

    selector = root.select("p.important")
    assert len(selector.matches) == 1
    assert selector.matches[0].text() == "Important"


def test_css_selector_invalid_syntax():
    html = "<div><p>Test</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None

    root.css("[invalid")
    with pytest.raises(SelectolaxError):
        root.css("[invalid&]")


def test_selector_attribute_longer_than_edge_cases():
    html = "<div><a href='short'>Link1</a><a>Link2</a><a href=''>Link3</a></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None

    selector = root.select("a")
    result = selector.attribute_longer_than("href", 0)
    assert len(result.matches) == 1


_LENGTH_FILTER_STATES_HTML = (
    "<div>"
    "<a href=''>empty value</a>"
    "<a href>valueless</a>"
    "<a>absent</a>"
    "<a href='long-value'>long</a>"
    "</div>"
)


def test_attribute_longer_than_agrees_with_any_variant():
    """Regression test: the two filters disagreed on empty attribute values."""
    root = LexborHTMLParser(_LENGTH_FILTER_STATES_HTML).root
    assert root is not None

    kept = root.select("a").attribute_longer_than("href", -1).matches
    assert [node.text() for node in kept] == ["empty value", "long"]

    for length in (-1, 0, 4, 11, 200):
        matches = root.select("a").attribute_longer_than("href", length).matches
        assert bool(matches) is (
            root.select("a").any_attribute_longer_than("href", length)
        ), f"the two filters disagree at length={length}"


def test_attribute_longer_than_agrees_with_any_variant_with_start():
    """Regression test: the same asymmetry was reachable through ``start``."""
    html = (
        "<div>"
        "<a href='http://'>empty tail</a>"
        "<a href='http://long-tail-here'>long tail</a>"
        "<a href=''>empty value</a>"
        "<a>absent</a>"
        "</div>"
    )
    root = LexborHTMLParser(html).root
    assert root is not None

    kept = root.select("a").attribute_longer_than("href", -1, "http://").matches
    assert [node.text() for node in kept] == [
        "empty tail",
        "long tail",
        "empty value",
    ]

    for length in (-1, 0, 5, 100):
        matches = root.select("a").attribute_longer_than("href", length, "http://")
        assert bool(matches.matches) is (
            root.select("a").any_attribute_longer_than("href", length, "http://")
        ), f"the two filters disagree at length={length}, start='http://'"


def test_node_replace_with_empty():
    html = "<div><span>target</span></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    span = root.css_first("span")
    assert span is not None

    span.replace_with("")
    html_result = root.html
    assert html_result is not None
    assert "<span>" not in html_result
    assert parser.html == "<html><head></head><body><div></div></body></html>"


def test_double_unwrap_prevention():
    html = "<div><span>test</span></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    span = root.css_first("span")
    assert span is not None

    # First unwrap should work
    span.unwrap()

    # Second unwrap should not cause issues (already removed)
    span.unwrap()

    html_result = root.html
    assert html_result is not None
    assert "test" in html_result


def test_clone_complex_modifications():
    html = "<div><p>Original</p><span>Content</span></div>"
    parser = LexborHTMLParser(html)

    p_tag = parser.root.css_first("p")
    assert p_tag is not None
    p_tag.inner_html = "Modified"

    cloned = parser.clone()

    cloned_p = cloned.root.css_first("p")
    assert cloned_p is not None
    cloned_p.decompose()

    original_text = parser.root.text()
    assert "Modified" in original_text

    cloned_text = cloned.root.text()
    assert "Modified" not in cloned_text


def test_create_node_basic():
    parser = LexborHTMLParser("<div></div>")
    new_node = parser.create_node("span")
    assert new_node.tag == "span"
    assert new_node.parent is None

    parser.css_first("div").insert_child(new_node)
    expected_html = "<html><head></head><body><div><span></span></div></body></html>"
    assert parser.html == expected_html


def test_create_node_different_tags():
    parser = LexborHTMLParser("<div></div>")
    root = parser.root
    assert root is not None

    tags_to_test = ["p", "span", "div", "h1", "custom-tag"]
    for tag in tags_to_test:
        new_node = parser.create_node(tag)
        assert new_node.tag == tag
        root.insert_child(new_node)

    html = parser.html
    assert html is not None
    for tag in tags_to_test:
        assert f"<{tag}></{tag}>" in html


def test_create_node_with_attributes():
    parser = LexborHTMLParser("<div></div>")
    new_node = parser.create_node("a")
    new_node.attrs["href"] = "https://example.com"
    new_node.attrs["class"] = "link"

    parser.root.insert_child(new_node)
    html = parser.html
    assert html is not None
    assert 'href="https://example.com"' in html
    assert 'class="link"' in html


def test_create_node_empty_tag_name():
    parser = LexborHTMLParser("<div></div>")
    try:
        parser.create_node("")
        assert False, "Should have raised an exception"
    except SelectolaxError:
        pass


def test_unwrap_tags_segfault_prevention():
    # This scenario used to cause a segmentation fault because the 'span' tag
    # matches the node itself, causing it to be detached. The subsequent
    # search for 'p' would then happen on a detached node.
    html = "<div><span id='repro'><span><p>Text</p></span></span></div>"
    tree = LexborHTMLParser(html)
    node = tree.css_first("#repro")
    assert node is not None

    # Should not segfault
    node.unwrap_tags(["span", "p"])

    assert "Text" in tree.html
    assert '<span id="repro">' not in tree.html


def test_strip_tags_then_text_basic():
    html = "<html><head></head><body><script>evil();</script><p>Hello</p></body></html>"
    parser = LexborHTMLParser(html)
    parser.strip_tags(["script"])
    result = parser.root.text(separator=" ", strip=True)
    assert "Hello" in result
    assert "evil" not in result


def test_strip_tags_then_text_multiple_tags():
    html = (
        "<html><head><style>body{}</style></head><body>"
        "<script>x=1;</script>"
        "<template><div>hidden</div></template>"
        "<p>Visible</p>"
        "</body></html>"
    )
    parser = LexborHTMLParser(html)
    parser.strip_tags(["style", "script", "template"])
    result = parser.root.text(separator=" ", strip=True)
    assert "Visible" in result
    assert "hidden" not in result
    assert "body{}" not in result


def test_strip_tags_then_text_nested_targets():
    html = (
        "<html><body>"
        "<template><script>inner();</script><p>tmpl</p></template>"
        "<script>outer();</script>"
        "<p>Keep this</p>"
        "</body></html>"
    )
    parser = LexborHTMLParser(html)
    parser.strip_tags(["template", "script"])
    result = parser.root.text(separator=" ", strip=True)
    assert "Keep this" in result
    assert "inner" not in result
    assert "outer" not in result


def test_strip_tags_then_text_recursive_flag():
    html = (
        "<html><body>"
        "<div class='rm'><span>child1</span><em>child2</em></div>"
        "<p>Survivor</p>"
        "</body></html>"
    )
    parser = LexborHTMLParser(html)
    parser.strip_tags(["div"], recursive=True)
    result = parser.root.text(separator=" ", strip=True)
    assert "Survivor" in result
    assert "child1" not in result


def test_strip_tags_then_text_many_iterations():
    template = (
        "<html><head><style>.a{{}}</style></head><body>"
        "<script>var x={i};</script>"
        "<p>Content {i}</p>"
        "</body></html>"
    )
    for i in range(50):
        parser = LexborHTMLParser(template.format(i=i))
        parser.strip_tags(["style", "script"])
        text = parser.root.text(separator=" ", strip=True)
        assert f"Content {i}" in text


SELECTED_CONTENT_HTML = (
    "<select><button><selectedcontent></selectedcontent></button>"
    "<option>a</option><option selected>b</option></select>"
)


def test_document_options_enum_values():
    assert LexborDocumentOptions.UNDEF == 0
    assert LexborDocumentOptions.WO_EVENTS == 1


def test_document_options_default_enables_events():
    parser = LexborHTMLParser(SELECTED_CONTENT_HTML)
    selectedcontent = parser.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent>b</selectedcontent>"


def test_document_options_wo_events_disables_events():
    parser = LexborHTMLParser(
        SELECTED_CONTENT_HTML, options=LexborDocumentOptions.WO_EVENTS
    )
    selectedcontent = parser.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"


def test_document_options_accepts_plain_int():
    parser = LexborHTMLParser(
        SELECTED_CONTENT_HTML, options=int(LexborDocumentOptions.WO_EVENTS)
    )
    selectedcontent = parser.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"


def test_document_options_combined_with_bitwise_or():
    options = LexborDocumentOptions.WO_EVENTS | LexborDocumentOptions.UNDEF
    assert options == LexborDocumentOptions.WO_EVENTS
    parser = LexborHTMLParser(SELECTED_CONTENT_HTML, options=options)
    selectedcontent = parser.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"


def test_document_options_combined_as_plain_int():
    options = LexborDocumentOptions.WO_EVENTS.value | LexborDocumentOptions.UNDEF.value
    parser = LexborHTMLParser(SELECTED_CONTENT_HTML, options=options)
    selectedcontent = parser.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"


def test_document_options_fragment_wo_events():
    parser = LexborHTMLParser(
        SELECTED_CONTENT_HTML,
        is_fragment=True,
        options=LexborDocumentOptions.WO_EVENTS,
    )
    selectedcontent = parser.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"


def test_document_options_property_reflects_constructor_argument():
    parser = LexborHTMLParser(SELECTED_CONTENT_HTML)
    assert parser.options == LexborDocumentOptions.UNDEF

    parser = LexborHTMLParser(
        SELECTED_CONTENT_HTML, options=LexborDocumentOptions.WO_EVENTS
    )
    assert parser.options == LexborDocumentOptions.WO_EVENTS


def test_document_options_clone_preserves_options():
    parser = LexborHTMLParser(
        SELECTED_CONTENT_HTML, options=LexborDocumentOptions.WO_EVENTS
    )
    cloned = parser.clone()
    assert cloned.options == LexborDocumentOptions.WO_EVENTS
    selectedcontent = cloned.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"


def test_document_options_clone_preserves_default_options():
    parser = LexborHTMLParser(SELECTED_CONTENT_HTML)
    cloned = parser.clone()
    assert cloned.options == LexborDocumentOptions.UNDEF


def test_document_options_clone_preserves_fragment_options():
    parser = LexborHTMLParser(
        SELECTED_CONTENT_HTML,
        is_fragment=True,
        options=LexborDocumentOptions.WO_EVENTS,
    )
    cloned = parser.clone()
    assert cloned.options == LexborDocumentOptions.WO_EVENTS
    selectedcontent = cloned.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"


def test_clone_preserves_head_and_body():
    parser = LexborHTMLParser(
        "<html><head><title>t</title></head><body><div>hi</div></body></html>"
    )
    cloned = parser.clone()
    assert cloned.head is not None
    assert cloned.body is not None
    assert cloned.head.tag == "head"
    assert cloned.body.tag == "body"
    assert cloned.head.html == "<head><title>t</title></head>"
    assert cloned.body.html == "<body><div>hi</div></body>"


def test_clone_preserves_generated_head_and_body():
    parser = LexborHTMLParser("<div>hi</div>")
    assert parser.head is not None
    assert parser.body is not None
    cloned = parser.clone()
    assert cloned.head is not None
    assert cloned.body is not None


def test_clone_head_and_body_are_independent_copies():
    parser = LexborHTMLParser("<html><head></head><body><div>hi</div></body></html>")
    cloned = parser.clone()
    cloned.body.attrs["id"] = "cloned"
    cloned.head.attrs["id"] = "cloned"
    assert parser.body.attributes.get("id") is None
    assert parser.head.attributes.get("id") is None
    assert cloned.body.attributes["id"] == "cloned"
    assert cloned.head.attributes["id"] == "cloned"


def test_clone_fragment_has_no_head_and_body():
    parser = LexborHTMLParser("<div>hi</div>", is_fragment=True)
    assert parser.head is None
    assert parser.body is None
    cloned = parser.clone()
    assert cloned.head is None
    assert cloned.body is None


@pytest.mark.parametrize(
    "html,is_fragment",
    [
        ("", False),
        ("", True),
        ("   ", True),
        ("<div>hi</div>", False),
        ("<div>hi</div>", True),
        ("<!DOCTYPE html><html><head></head><body><p>x</p></body></html>", False),
        (
            (
                "<!-- top --><html><head></head>"
                "<body>hello<!-- c --><b>bold</b></body></html>"
            ),
            False,
        ),
        ("<!DOCTYPE html><!-- c --><html><head></head><body>x</body></html>", False),
        ("<div>a</div><span>b</span>", True),
        ("hello <!-- c --> world", True),
        ("<!-- c -->", True),
        ("<html><body><p>&amp; &lt; &#169; &nbsp;</p></body></html>", False),
        (
            (
                "<html><head><style>a{color:red}</style></head>"
                "<body><script>if (a < b) {}</script></body></html>"
            ),
            False,
        ),
        ("<html><body><p>one<p>two<div>three", False),
        (
            "<html><body>" + "<div>" * 30 + "deep" + "</div>" * 30 + "</body></html>",
            False,
        ),
    ],
)
def test_clone_round_trips_html(html, is_fragment):
    parser = LexborHTMLParser(html, is_fragment=is_fragment)
    cloned = parser.clone()
    assert cloned.html == parser.html
    assert cloned.raw_html == parser.raw_html


def test_clone_preserves_doctype():
    html = "<!DOCTYPE html><html><head></head><body><p>x</p></body></html>"
    cloned = LexborHTMLParser(html).clone()
    assert cloned.html == html
    assert cloned.html.startswith("<!DOCTYPE html>")


def test_clone_preserves_document_level_comments():
    html = "<!-- first --><html><head></head><body><!-- second -->x</body></html>"
    cloned = LexborHTMLParser(html).clone()
    assert cloned.html == html
    assert cloned.css_first("body").html == "<body><!-- second -->x</body>"


def test_clone_of_empty_fragment_is_empty():
    parser = LexborHTMLParser("", is_fragment=True)
    cloned = parser.clone()
    assert cloned.html == ""
    assert cloned.root is None


def test_clone_of_fragment_with_multiple_roots():
    parser = LexborHTMLParser("<div>a</div><span>b</span>", is_fragment=True)
    cloned = parser.clone()
    assert cloned.html == "<div>a</div><span>b</span>"
    assert [node.tag for node in cloned.css("div, span")] == ["div", "span"]


def test_clone_reflects_changes_made_before_cloning():
    parser = LexborHTMLParser("<html><body><div>a</div></body></html>")
    parser.css_first("div").attrs["x"] = "1"
    cloned = parser.clone()
    assert cloned.css_first("div").attributes == {"x": "1"}


def test_clone_is_independent_from_original():
    parser = LexborHTMLParser("<html><body><div id='a'><p>one</p></div></body></html>")
    cloned = parser.clone()
    cloned.css_first("p").replace_with("changed")
    cloned.css_first("div").attrs["id"] = "b"
    assert parser.css_first("p") is not None
    assert parser.css_first("div").attrs["id"] == "a"
    assert cloned.css_first("p") is None


def test_clone_remains_usable_after_original_is_collected():
    parser = LexborHTMLParser("<html><body><div id='keep'>x</div></body></html>")
    cloned = parser.clone()
    del parser
    gc_collect()
    assert cloned.css_first("div").attrs["id"] == "keep"


def test_node_clone_is_independent():
    parser = LexborHTMLParser("<div><span>a</span></div>")
    node = parser.css_first("span")
    cloned = node.clone()
    cloned.attrs["id"] = "c"
    assert node.attrs.get("id") is None
    assert cloned.attrs["id"] == "c"
