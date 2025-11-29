"""Tests for functionality that is only supported by lexbor backend."""

from inspect import cleandoc

from selectolax.lexbor import LexborHTMLParser, parse_fragment


def clean_doc(text: str) -> str:
    return f"{cleandoc(text)}\n"


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


def test_checking_attributes_does_not_segfault():
    parser = LexborHTMLParser("")
    root_node = parser.root
    assert root_node is not None
    for node in root_node.traverse():
        print(node.parent)
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
    outer_div = parse_fragment(html)[0]
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
    text_node = parser.css_first("span").first_child
    assert text_node is not None
    assert text_node.is_comment_node
    assert text_node.comment_content == "hello"


def test_parser_without_top_level_tags():
    parser = LexborHTMLParser(
        "<div><span>\n \n</span><title>X</title></div>", is_fragment=False
    )
    assert parser is not None and isinstance(parser, LexborHTMLParser)
    assert (
        parser.html
        == "<html><head></head><body><div><span>\n \n</span><title>X</title></div></body></html>"
    )
    assert (
        parser.root.html
        == "<html><head></head><body><div><span>\n \n</span><title>X</title></div></body></html>"
    )
    assert parser.head is not None
    assert parser.body is not None
    parser = LexborHTMLParser(
        "<div><span>\n \n</span><title>X</title></div>", is_fragment=True
    )
    assert parser.html == "<div><span>\n \n</span><title>X</title></div>"
    assert parser.root.html == "<div><span>\n \n</span><title>X</title></div>"
    assert parser.head is None
    assert parser.body is None
    parser = LexborHTMLParser(
        "<html><body><div><span>\n \n</span><title>X</title></div></body></html>",
        is_fragment=True,
    )
    assert parser.html == "<div><span>\n \n</span><title>X</title></div>"
