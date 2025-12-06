from inspect import cleandoc
import pytest
from selectolax.lexbor import LexborHTMLParser, SelectolaxError


def clean_doc(text: str) -> str:
    return f"{cleandoc(text)}\n"


def test_fragment_parser_top_level_tags():
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


def test_fragment_parser_multiple_nodes_on_the_same_level():
    html = clean_doc("""
          <meta charset="utf-8">
          <meta content="width=device-width,initial-scale=1" name="viewport">
          <title>Title!</title>
          <!-- My crazy comment -->
          <p>Hello <strong>World</strong>!</p>
    """)
    parser = LexborHTMLParser(html, is_fragment=True)
    expected_html = clean_doc("""
          <meta charset="utf-8">
          <meta content="width=device-width,initial-scale=1" name="viewport">
          <title>Title!</title>
          <!-- My crazy comment -->
          <p>Hello <strong>World</strong>!</p>

    """)
    assert parser.html == expected_html


def test_fragment_parser_whole_doc():
    html = """<html lang="en">
            <head><meta charset="utf-8"><title>Title!</title></head>
            <body><p>Lorem <strong>Ipsum</strong>!</p></body>
        </html>"""
    parser = LexborHTMLParser(html, is_fragment=True)
    expected_html = '<meta charset="utf-8"><title>Title!</title>\n            <p>Lorem <strong>Ipsum</strong>!</p>'
    html = parser.html
    assert html is not None
    assert html.strip() == expected_html


def test_fragment_parser_empty_doc():
    html = ""
    parser = LexborHTMLParser(html, is_fragment=True)
    assert parser.html is None


@pytest.mark.parametrize(
    "html, expected_html",
    [
        ("<body><div>Test</div></body>", "<div>Test</div>"),
        ("  <div>Lorep Ipsum</div>", "  <div>Lorep Ipsum</div>"),
        ("<div>Lorem</div><div>Ipsum</div>", "<div>Lorem</div><div>Ipsum</div>"),
        ("   \n  <div>Lorem Ipsum</div>  \t  ", "   \n  <div>Lorem Ipsum</div>  \t  "),
        ("<!-- Comment --><div>Content</div>", "<!-- Comment --><div>Content</div>"),
        (
            "<template><p>Inside Template</p></template>",
            "<template><p>Inside Template</p></template>",
        ),
    ],
)
def test_fragment_parser(html, expected_html):
    parser = LexborHTMLParser(html, is_fragment=True)
    assert parser.html == expected_html


def test_insert_node_fragment_parser():
    html = "<div></div>"
    p = LexborHTMLParser(html, is_fragment=True)
    p.root.insert_child("text")
    assert p.html == "<div>text</div>"


def test_insert_before_fragment_parser():
    html = "<div><span></span></div>"
    p = LexborHTMLParser(html, is_fragment=True)
    span = p.root.css_first("span")
    span.insert_before("text")
    assert p.html == "<div>text<span></span></div>"


def test_insert_after_fragment_parser():
    html = "<div><span></span></div>"
    p = LexborHTMLParser(html, is_fragment=True)
    span = p.root.css_first("span")
    span.insert_after("text")
    assert p.html == "<div><span></span>text</div>"


def test_clone_parser_fragment():
    html = "<div><span>Hello</span><p>World</p></div>"
    p = LexborHTMLParser(html, is_fragment=True)
    cloned = p.clone()
    assert cloned.html == p.html
    assert cloned is not p

    cloned.root.css_first("span").insert_child("!")
    assert cloned.html == "<div><span>Hello!</span><p>World</p></div>"
    assert p.html == "<div><span>Hello</span><p>World</p></div>"


def test_clone_node_fragment():
    html = "<div><span>Hello</span><p>World</p></div>"
    p = LexborHTMLParser(html, is_fragment=True)
    span = p.root.css_first("span")
    cloned_span = span.clone()
    assert cloned_span.html == span.html
    assert cloned_span is not span

    cloned_span.insert_child("!")
    assert cloned_span.html == "<span>Hello!</span>"
    assert span.html == "<span>Hello</span>"


def test_fragment_root_html_serialization():
    html = "<div>Hello</div><span>World</span>"
    p = LexborHTMLParser(html, is_fragment=True)
    assert p.root.html == "<div>Hello</div><span>World</span>"
    p.root.insert_child("!")
    assert p.html == "<div>Hello!</div><span>World</span>"


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


def test_fragment_text_extraction():
    html = "<div>Hello <strong>World</strong>!</div>"
    p = LexborHTMLParser(html, is_fragment=True)
    div = p.root.css_first("div")
    assert div.text() == "Hello World!"
    assert div.text(deep=True, separator=" ", strip=True) == "Hello World !"


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


def test_fragment_inner_html():
    html = "<div><span>Hello</span><p>World</p></div>"
    p = LexborHTMLParser(html, is_fragment=True)
    div = p.root.css_first("div")
    assert div.inner_html == "<span>Hello</span><p>World</p>"
    div.inner_html = "<em>New</em> content"
    assert div.html == "<div><em>New</em> content</div>"


def test_fragment_node_operations_combined():
    html = "<div><span>Hello</span></div>"
    p = LexborHTMLParser(html, is_fragment=True)
    span = p.root.css_first("span")
    span.replace_with("Replaced")
    assert p.html == "<div>Replaced</div>"

    html2 = "<div><span></span></div>"
    p2 = LexborHTMLParser(html2, is_fragment=True)
    span2 = p2.root.css_first("span")
    span2.insert_before("Before")
    span2.insert_after("After")
    assert p2.html == "<div>Before<span></span>After</div>"


def test_fragment_replace_with_node():
    html = "<div><span>Hello</span></div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    replacement_html = "<em>Replaced</em>"
    replacement_parser = LexborHTMLParser(replacement_html, is_fragment=True)
    span = parser.root.css_first("span")
    span.replace_with(replacement_parser.root)
    assert parser.html == "<div><em>Replaced</em></div>"


def test_fragment_insert_before_node():
    base_html = "<div><span></span></div>"
    base_parser = LexborHTMLParser(base_html, is_fragment=True)
    before_html = "<strong>Before</strong>"
    before_parser = LexborHTMLParser(before_html, is_fragment=True)
    span = base_parser.root.css_first("span")
    span.insert_before(before_parser.root)
    assert base_parser.html == "<div><strong>Before</strong><span></span></div>"


def test_fragment_insert_after_node():
    base_html = "<div><span></span></div>"
    base_parser = LexborHTMLParser(base_html, is_fragment=True)
    after_html = "<em>After</em>"
    after_parser = LexborHTMLParser(after_html, is_fragment=True)
    span = base_parser.root.css_first("span")
    span.insert_after(after_parser.root)
    assert base_parser.html == "<div><span></span><em>After</em></div>"


def test_fragment_insert_child_node():
    base_html = "<div></div>"
    base_parser = LexborHTMLParser(base_html, is_fragment=True)
    child_html = "<p>Child</p>"
    child_parser = LexborHTMLParser(child_html, is_fragment=True)
    div = base_parser.root.css_first("div")
    div.insert_child(child_parser.root)
    assert base_parser.html == "<div><p>Child</p></div>"


def test_fragment_strip_tags():
    html = "<div><script>alert('test')</script><p>Hello</p><style>body { color: red; }</style></div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    parser.root.strip_tags(["script", "style"])
    assert parser.html == "<div><p>Hello</p></div>"


def test_fragment_decompose():
    html = "<div><script>alert('test')</script><p>Hello</p></div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    script = parser.root.css_first("script")
    script.decompose()
    assert parser.html == "<div><p>Hello</p></div>"


@pytest.mark.parametrize(
    "input_html, expected",
    [
        ("<html><body><div>test</div></body></html>", "<div>test</div>"),
        ("<head><title>test</title></head>", "<title>test</title>"),
        ("<body><p>test</p></body>", "<p>test</p>"),
    ],
)
def test_fragment_strips_top_level_tags(input_html, expected):
    parser = LexborHTMLParser(input_html, is_fragment=True)
    assert parser.html == expected


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


def test_fragment_attrs():
    html = "<div id='test' class='foo bar' data-value='123'></div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    div = parser.root
    assert div.attributes == {"id": "test", "class": "foo bar", "data-value": "123"}
    assert div.attrs["id"] == "test"
    div.attrs["new"] = "value"
    assert div.attributes == {
        "id": "test",
        "class": "foo bar",
        "data-value": "123",
        "new": "value",
    }


def test_fragment_child_alias():
    html = "<div><span>content</span></div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    div = parser.root
    assert div.child == div.first_child


def test_fragment_tag_properties():
    html = "<div id='test'>content</div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    div = parser.root
    assert div.tag == "div"
    assert div.tag_id is not None
    assert div.mem_id is not None
    assert div.id == "test"


def test_fragment_unwrap():
    html = "<div><span>Hello</span> world</div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    span = parser.root.css_first("span")
    span.unwrap()
    assert parser.html == "<div>Hello world</div>"


def test_fragment_unwrap_tags():
    html = "<div><i>Hello</i> <b>world</b></div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    parser.root.unwrap_tags(["i", "b"])
    assert parser.html == "<div>Hello world</div>"


def test_fragment_eq():
    html = "<div>test</div>"
    parser1 = LexborHTMLParser(html, is_fragment=True)
    parser2 = LexborHTMLParser(html, is_fragment=True)
    assert parser1.root == parser2.root.html
    assert parser1.root == "<div>test</div>"


def test_fragment_text_content():
    html = "<div>Hello</div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    text_node = parser.root.first_child
    assert text_node.text_content == "Hello"
    assert parser.root.text_content is None


def test_fragment_comment_content():
    html = "<!-- comment -->"
    parser = LexborHTMLParser(html, is_fragment=True)
    comment_node = parser.root
    assert comment_node.comment_content == "comment"


def test_fragment_parser_malformed_html():
    html = "<div><unclosed><span>content"
    parser = LexborHTMLParser(html, is_fragment=True)
    html_result = parser.html
    assert html_result is not None
    assert "content" in html_result


def test_fragment_parser_empty_input():
    parser = LexborHTMLParser("", is_fragment=True)
    assert parser.root is None
    assert parser.html is None


def test_attributes_access_on_non_element():
    html = "<!-- comment --><div>text</div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    root = parser.root
    assert root is not None

    comment_node = root
    assert comment_node.is_comment_node

    attrs = comment_node.attributes
    assert isinstance(attrs, dict)
    assert len(attrs) == 0

    text_node = root.css_first("div").first_child
    assert text_node is not None
    assert text_node.is_text_node

    text_attrs = text_node.attributes
    assert isinstance(text_attrs, dict)
    assert len(text_attrs) == 0


@pytest.mark.parametrize(
    "malformed_html",
    [
        "<div><unclosed><span>content",  # Unclosed tags
        "<div><span></div>",  # Mismatched tags
        "<div><span>content</span",  # Missing closing bracket
        '<div class="unclosed>content</div>',  # Unclosed attribute
        "<div>&invalid_entity;</div>",  # Invalid entity
        "<!-- unclosed comment",  # Unclosed comment
        "<![CDATA[ unclosed cdata",  # Unclosed CDATA
    ],
)
def test_fragment_parsing_malformed_html(malformed_html):
    parser = LexborHTMLParser(malformed_html, is_fragment=True)
    html_result = parser.html
    assert html_result is None or isinstance(html_result, str)


def test_fragment_only_text():
    text_only = "Just plain text"
    parser = LexborHTMLParser(text_only, is_fragment=True)
    html_result = parser.html
    assert html_result is not None
    assert "Just plain text" in html_result


def test_fragment_only_comment():
    comment_only = "<!-- Just a comment -->"
    parser = LexborHTMLParser(comment_only, is_fragment=True)
    html_result = parser.html
    assert html_result is not None
    assert "Just a comment" in html_result


def test_fragment_mixed_content():
    mixed = "Text <!-- comment --> <div>element</div> more text"
    parser = LexborHTMLParser(mixed, is_fragment=True)
    html_result = parser.html
    assert html_result is not None
    assert "Text" in html_result
    assert "element" in html_result


def test_fragment_create_node_basic():
    parser = LexborHTMLParser("<div></div>", is_fragment=True)
    assert parser.root is not None
    new_node = parser.create_node("span")
    assert new_node.tag == "span"
    assert new_node.parent is None

    parser.root.insert_child(new_node)
    expected_html = "<div><span></span></div>"
    assert parser.html == expected_html


def test_fragment_create_node_different_tags():
    parser = LexborHTMLParser("<div></div>", is_fragment=True)
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


def test_fragment_create_node_with_attributes():
    parser = LexborHTMLParser("<div></div>", is_fragment=True)
    assert parser.root is not None
    new_node = parser.create_node("a")
    new_node.attrs["href"] = "https://example.com"
    new_node.attrs["class"] = "link"

    parser.root.insert_child(new_node)
    html = parser.html
    assert html is not None
    assert 'href="https://example.com"' in html
    assert 'class="link"' in html


def test_fragment_create_node_empty_tag_name():
    parser = LexborHTMLParser("<div></div>", is_fragment=True)
    try:
        parser.create_node("")
        assert False, "Should have raised an exception"
    except SelectolaxError:
        pass
