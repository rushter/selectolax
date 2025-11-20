"""Tests for functionality that is only supported by lexbor backend."""

from selectolax.lexbor import LexborHTMLParser, parse_fragment


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
    parser = LexborHTMLParser("<div><span>value</span></div>")
    span = parser.css_first("span")
    assert span is not None

    assert span.text(deep=False, skip_empty=False) == "value"
    assert span.text(deep=False, skip_empty=True) == ""


def test_iter_includes_text_nodes_when_requested():
    parser = LexborHTMLParser("<div>hello</div>")
    div_node = parser.css_first("div")
    assert div_node is not None

    assert list(div_node.iter()) == []

    text_nodes = list(div_node.iter(include_text=True, skip_empty=False))
    assert len(text_nodes) == 1
    assert text_nodes[0].is_text_node
    assert text_nodes[0].text(deep=False, skip_empty=False) == "hello"


def test_traverse_respects_skip_empty_on_text_nodes():
    parser = LexborHTMLParser("<div>outer<span>inner</span></div>")
    root = parser.css_first("div")
    assert root is not None

    nodes_with_text = list(root.traverse(include_text=True, skip_empty=False))
    # div, text "outer", span, text "inner"
    assert [node.tag if not node.is_text_node else "#text" for node in nodes_with_text] == [
        "div",
        "#text",
        "span",
        "#text",
    ]
    assert nodes_with_text[1].text(deep=False, skip_empty=False) == "outer"
    assert nodes_with_text[3].text(deep=False, skip_empty=False) == "inner"

    nodes_without_text = list(root.traverse(include_text=False, skip_empty=True))
    # When text nodes are not requested, only element nodes are yielded.
    assert [node.tag for node in nodes_without_text] == ["div", "span"]


def test_is_empty_text_node_property():
    parser = LexborHTMLParser("<div><span>\n \n</span><span>X</span></div>")
    text_node = parser.root.first_child.first_child
    assert text_node.is_empty_text_node
    text_node = parser.root.last_child.first_child
    assert not text_node.is_empty_text_node
