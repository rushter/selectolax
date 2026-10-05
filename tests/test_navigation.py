import pytest

from selectolax.lexbor import LexborHTMLParser
from tests.helpers import clean_doc

_HEAD_BODY_HTML = (
    "<html><head><title>Title</title></head><body><div>hi</div></body></html>"
)

_EMPTY_HEAD_BODY_HTML = "<html><head></head><body></body></html>"

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


def test_checking_attributes_does_not_segfault():
    parser = LexborHTMLParser("")
    root_node = parser.root
    assert root_node is not None
    for node in root_node.traverse():
        parent = node.parent
        assert parent is not None
        parent = parent.attributes.get("anything")


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


def test_fragment_traversal():
    html = "<div><span>Hello</span><p>World</p></div>"
    p = LexborHTMLParser(html, is_fragment=True)
    nodes = list(p.root.traverse(include_text=True))
    assert len(nodes) == 5
    assert nodes[0].tag == "div"
    assert nodes[1].tag == "span"
    assert nodes[2].tag == "-text"
    assert nodes[3].tag == "p"
    assert nodes[4].tag == "-text"


def test_fragment_navigation():
    html = "<div>First</div><span>Second</span><p>Third</p>"
    parser = LexborHTMLParser(html, is_fragment=True)
    div = parser.root
    span = div.next
    p = span.next
    assert div.tag == "div"
    assert span.tag == "span"
    assert p.tag == "p"
    assert div.prev is None
    assert span.prev.tag == "div"
    assert p.prev.tag == "span"
    assert p.next is None
    assert div.first_child.is_text_node
    assert div.last_child.is_text_node
    assert div.first_child.text_content == "First"


def test_fragment_child_alias():
    html = "<div><span>content</span></div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    div = parser.root
    assert div.child == div.first_child


def test_root_property():
    html = "<body>Hi there</body>"
    html_parser = LexborHTMLParser(html)
    assert html_parser.root.html == "<html><head></head><body>Hi there</body></html>"


def test_head_property():
    html = """
    <html lang="en">
        <head><title>rushter.com</title></head>
        <body></body>
    </html>
    """
    html_parser = LexborHTMLParser(html)
    assert html_parser.head.html == "<head><title>rushter.com</title></head>"


def test_body_property():
    html = "<body>Hi there</body>"
    html_parser = LexborHTMLParser(html)
    assert html_parser.body.html == "<body>Hi there</body>"


def test_iter_with_text():
    html = """
    <div id="description">
        <h1>Title</h1>
        text
        <div>foo</div>
        <img scr="image.jpg">
    </div>
    """
    html_parser = LexborHTMLParser(html)
    expected_tags = ["-text", "h1", "-text", "div", "-text", "img", "-text"]
    actual_tags = [
        node.tag
        for node in html_parser.css_first("#description").iter(include_text=True)
    ]
    assert expected_tags == actual_tags


def test_iter_no_text():
    html = """
    <div id="description">
        <h1>Title</h1>
        text
        <div>foo</div>
        <img scr="image.jpg">
    </div>
    """
    html_parser = LexborHTMLParser(html)
    expected_tags = ["h1", "div", "img"]
    actual_tags = [
        node.tag
        for node in html_parser.css_first("#description").iter(include_text=False)
    ]
    assert expected_tags == actual_tags


@pytest.mark.parametrize("remover", ["decompose", "remove", "unwrap"])
def test_iter_visits_every_child_when_removed_mid_iteration(remover):
    """Removing the yielded node must not end the iteration early.

    ``lxb_dom_node_remove`` clears the ``next`` pointer of the node it unlinks,
    so reading ``node.next`` after resuming from the ``yield`` used to truncate
    the walk to the first child and silently skip the rest.
    """
    tree = LexborHTMLParser("<div><p>1</p><p>2</p><p>3</p><p>4</p></div>")
    div = tree.css_first("div")

    seen = []
    for node in div.iter():
        seen.append(node.text())
        getattr(node, remover)()

    assert seen == ["1", "2", "3", "4"]
    assert tree.css("p") == []


def test_iter_reports_all_children_when_some_are_removed_mid_iteration():
    """Skipping nodes must not disturb the traversal of their siblings."""
    tree = LexborHTMLParser("<div><p>1</p><p>2</p><p>3</p><p>4</p></div>")
    div = tree.css_first("div")

    seen = []
    for node in div.iter():
        seen.append(node.text())
        if node.text() in ("1", "3"):
            node.decompose()

    assert seen == ["1", "2", "3", "4"]
    assert [node.text() for node in tree.css("p")] == ["2", "4"]


def test_node_navigation():
    html = (
        '<div id="parent"><div id="prev"></div><div id="test_node"><h1 id="child">Title</h1>'
        '<div>foo</div><img scr="image.jpg"></div><div id="next"></div></div>'
    )
    html_parser = LexborHTMLParser(html)
    main_node = html_parser.css_first("#test_node")
    assert main_node.prev.id == "prev"
    assert main_node.next.id == "next"
    assert main_node.parent.id == "parent"
    assert main_node.child.id == "child"


def test_traverse():
    html = (
        '<div id="parent"><div id="prev"></div><div id="test_node"><h1 id="child">Title</h1>'
        '<div>foo</div><img scr="image.jpg"></div><div id="next"></div></div>'
    )
    html_parser = LexborHTMLParser(html)
    actual = [node.tag for node in html_parser.root.traverse()]
    expected = ["html", "head", "body", "div", "div", "div", "h1", "div", "img", "div"]
    assert actual == expected


def test_traverse_with_text():
    html = (
        '<div id="parent"><div id="prev"></div><div id="test_node"><h1 id="child">Title</h1>'
        '<div>foo</div><img scr="image.jpg"></div><div id="next"></div></div>'
    )
    html_parser = LexborHTMLParser(html)
    actual = [node.tag for node in html_parser.root.traverse(include_text=True)]
    expected = [
        "html",
        "head",
        "body",
        "div",
        "div",
        "div",
        "h1",
        "-text",
        "div",
        "-text",
        "img",
        "div",
    ]
    assert actual == expected
