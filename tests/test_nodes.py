import pytest

from selectolax.lexbor import (
    LexborHTMLParser,
    LexborNode,
)

_NODE_ID_CASES = [
    ("<div id='my_node'></div>", "my_node"),
    ("<div></div>", None),
]


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


def test_fragment_node_properties():
    html = "<div>Hello</div><span>World</span>"
    p = LexborHTMLParser(html, is_fragment=True)
    div = p.root
    span = p.root.next

    assert div.is_element_node is True
    assert div.is_text_node is False
    assert div.is_comment_node is False

    assert span.is_element_node is True
    assert span.is_text_node is False
    assert span.is_comment_node is False

    text_node = div.first_child
    assert text_node.is_element_node is False
    assert text_node.is_text_node is True
    assert text_node.is_comment_node is False


def test_fragment_tag_properties():
    html = "<div id='test'>content</div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    div = parser.root
    assert div.tag == "div"
    assert div.tag_id is not None
    assert div.mem_id is not None
    assert div.id == "test"


def test_fragment_eq():
    html = "<div>test</div>"
    parser1 = LexborHTMLParser(html, is_fragment=True)
    parser2 = LexborHTMLParser(html, is_fragment=True)
    assert parser1.root == parser2.root.html
    assert parser1.root == "<div>test</div>"


def test_id_property():
    html = "<p id='main_text'>text</p>"
    assert LexborHTMLParser(html).css_first("p").id == "main_text"


def test_tag_property():
    html = "<h1>text</h1>"
    assert LexborHTMLParser(html).css_first("h1").tag == "h1"


@pytest.mark.parametrize(
    "html, expected",
    _NODE_ID_CASES,
)
def test_get_node_id(html, expected):
    html_parser = LexborHTMLParser(html)
    node = html_parser.css_first("div")
    assert node.id == expected


def test_node_comparison():
    html = """
        <div>H3ll0</div><div id='tt'><p id='stext'>Lorem ipsum dolor sit amet, ea quo modus meliore platonem.</p></div>
    """
    html_parser = LexborHTMLParser(html)
    nodes = [node for node in html_parser.root.traverse(include_text=False)]
    same_node_path_one = nodes[-1].parent
    same_node_path_two = nodes[-2]
    same_node_path_three = html_parser.css_first("#tt")
    assert same_node_path_one == same_node_path_two == same_node_path_three


def test_node_comprassion_with_strings():
    html = """<div id="test"></div>"""
    html_parser = LexborHTMLParser(html)
    node = html_parser.css_first("#test")
    assert node == '<div id="test"></div>'


def test_node_comparison_fails():
    html = """<div id="test"></div>"""
    html_parser = LexborHTMLParser(html)
    node = html_parser.css_first("#test")

    assert node is not None
    assert node != 123


def test_hash_nodes():
    tree = LexborHTMLParser("""<div><p><strong>J</strong>ohn</p><p>Doe</p></div>""")
    node = tree.css_first("div")
    assert node.mem_id == hash(node)


def test_node_is_not_publicly_constructible():
    with pytest.raises(TypeError, match="cannot be instantiated directly"):
        LexborNode()

    with pytest.raises(TypeError, match="cannot be instantiated directly"):
        LexborNode(1)

    node = LexborHTMLParser("<div id='x'></div>").css_first("div")
    assert isinstance(node, LexborNode)
    assert node.id == "x"
    assert node.clone().id == "x"
