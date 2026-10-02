from inspect import cleandoc

import pytest

from selectolax.lexbor import LexborHTMLParser


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


def test_fragment_root_html_pretty_serialization():
    html = "<div><span>Hello</span></div>\n<span>World</span>"
    p = LexborHTMLParser(html, is_fragment=True)
    assert p.root.html_pretty(skip_ws_nodes=True) == clean_doc(
        """
        <div>
          <span>
            "Hello"
          </span>
        </div>
        <span>
          "World"
        </span>
        """
    )
    assert p.html_pretty(skip_ws_nodes=True) == clean_doc(
        """
        <div>
          <span>
            "Hello"
          </span>
        </div>
        <span>
          "World"
        </span>
        """
    )


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


def test_fragment_parser_accepts_explicit_fragment_context_defaults():
    parser = LexborHTMLParser(
        "<div id='test'>content</div>",
        is_fragment=True,
        fragment_tag="div",
        fragment_namespace="html",
    )
    assert parser.html == '<div id="test">content</div>'


def test_fragment_parser_accepts_namespace_uri():
    parser = LexborHTMLParser(
        "<title>SVG</title>",
        is_fragment=True,
        fragment_tag="svg",
        fragment_namespace="http://www.w3.org/2000/svg",
    )
    assert parser.root.tag == "title"
    assert parser.html == "<title>SVG</title>"


def test_fragment_parser_rejects_unknown_fragment_tag():
    with pytest.raises(ValueError, match="Unknown fragment tag"):
        LexborHTMLParser("<div></div>", is_fragment=True, fragment_tag="not-a-real-tag")


def test_fragment_parser_rejects_unknown_fragment_namespace():
    with pytest.raises(ValueError, match="Unknown fragment namespace"):
        LexborHTMLParser(
            "<div></div>", is_fragment=True, fragment_namespace="not-a-real-namespace"
        )


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


def test_fragment_text_extraction_multiple_nodes():
    html = "<p>1</p><p>2</p>"
    p = LexborHTMLParser(html, is_fragment=True)
    assert p.text(deep=False) == ""
    assert p.text(deep=True, separator=" ", strip=True) == "1 2"


def test_fragment_iter_multiple_nodes():
    html = "<p>1</p><p>2</p>"
    p = LexborHTMLParser(html, is_fragment=True)
    assert len(list(p.root.iter())) == 2


def test_fragment_empty_html():
    html = ""
    tree = LexborHTMLParser(html, is_fragment=True)
    assert tree.html == ""


def test_empty_fragment_has_no_root():
    tree = LexborHTMLParser("", is_fragment=True)
    assert tree.root is None
    assert tree.body is None
    assert tree.head is None


def test_empty_fragment_css_returns_empty_list():
    tree = LexborHTMLParser("", is_fragment=True)
    assert tree.css("div") == []
    assert tree.css("div, span") == []
    # the selector is not even compiled, but must still raise nothing
    assert tree.css("!!! invalid") == []


def test_empty_fragment_css_first_returns_default():
    tree = LexborHTMLParser("", is_fragment=True)
    assert tree.css_first("div") is None
    assert tree.css_first("div", default="fallback") == "fallback"
    assert tree.css_first("div", default=0) == 0
    assert tree.css_first("div", strict=True) is None
    assert tree.css_first("div", "fallback", True) == "fallback"


@pytest.mark.parametrize(
    "method, args",
    [
        ("css_matches", ("div",)),
        ("any_css_matches", (("div", "span"),)),
        ("scripts_contain", ("needle",)),
        ("script_srcs_contain", (("needle",),)),
    ],
)
def test_empty_fragment_match_helpers_return_false(method, args):
    tree = LexborHTMLParser("", is_fragment=True)
    assert getattr(tree, method)(*args) is False


def test_empty_fragment_mutating_methods_are_noops():
    tree = LexborHTMLParser("", is_fragment=True)
    assert tree.merge_text_nodes() is None
    assert tree.unwrap_tags(["div", "span"]) is None
    assert tree.unwrap_tags(["div"], delete_empty=True) is None
    assert tree.html == ""


def test_empty_fragment_inner_html_getter_returns_empty_string():
    tree = LexborHTMLParser("", is_fragment=True)
    assert tree.inner_html == ""


def test_empty_fragment_inner_html_setter_is_noop():
    tree = LexborHTMLParser("", is_fragment=True)
    tree.inner_html = "<p>ignored</p>"
    assert tree.inner_html == ""
    assert tree.html == ""
    assert tree.root is None


def test_empty_fragment_methods_agree_with_empty_document():
    """Every root-deref helper must behave the same for a rootless fragment."""
    empty_fragment = LexborHTMLParser("", is_fragment=True)

    assert empty_fragment.css("div") == []
    assert empty_fragment.css_first("div") is None
    assert empty_fragment.css_matches("div") is False
    assert empty_fragment.any_css_matches(("div",)) is False
    assert empty_fragment.scripts_contain("x") is False
    assert empty_fragment.script_srcs_contain(("x",)) is False
    assert empty_fragment.merge_text_nodes() is None
    assert empty_fragment.inner_html == ""
    assert empty_fragment.tags("div") == []
    assert empty_fragment.text() == ""
    assert empty_fragment.select() is None


def test_non_empty_fragment_queries_still_work():
    """The root guard must not shadow normal results."""
    tree = LexborHTMLParser(
        "<div><p>a</p><script src='x.js'>y</script></div>", is_fragment=True
    )
    assert tree.root is not None
    assert len(tree.css("div")) == 1
    assert tree.css_first("p").text() == "a"
    assert tree.css_matches("p") is True
    assert tree.css_matches("table") is False
    assert tree.any_css_matches(("table", "p")) is True
    assert tree.scripts_contain("y") is True
    assert tree.script_srcs_contain(("x.js",)) is True
    assert tree.inner_html == '<p>a</p><script src="x.js">y</script>'


def test_full_document_queries_still_work():
    """A full document always has a root, so behaviour must be unchanged."""
    tree = LexborHTMLParser("<div><p>hi</p></div>")
    assert tree.root is not None
    assert len(tree.css("p")) == 1
    assert tree.css_first("p").text() == "hi"
    assert tree.css_first("table") is None
    assert tree.css_first("table", default="d") == "d"
    assert tree.css_matches("p") is True
    assert tree.any_css_matches(("p",)) is True
    assert tree.scripts_contain("nope") is False
    assert tree.merge_text_nodes() is None
    assert tree.inner_html == "<head></head><body><div><p>hi</p></div></body>"


def test_fragment_root_match_helpers_use_the_same_scope_as_css():
    """Regression test: the match helpers searched the wrong subtree.

    ``css`` evaluates a fragment root against the whole fragment, via the
    fragment wrapper, but ``css_matches``/``any_css_matches`` were handed the
    root element itself. They therefore missed matches that ``css`` returned
    whenever the match sat outside the first top-level node.
    """
    tree = LexborHTMLParser("<div>x</div><p>sibling</p>", is_fragment=True)
    root = tree.root

    assert [node.html for node in root.css("p")] == ["<p>sibling</p>"]
    assert root.css_matches("p") is True
    assert root.any_css_matches(("p",)) is True
    assert root.any_css_matches(("table", "p")) is True

    # Also reachable through the parser, which delegates to the root node.
    assert [node.html for node in tree.css("p")] == ["<p>sibling</p>"]
    assert tree.css_matches("p") is True
    assert tree.any_css_matches(("table", "p")) is True


def test_fragment_root_match_helpers_still_reject_absent_selectors():
    """Widening the scope must not turn non-matches into matches."""
    tree = LexborHTMLParser("<div>x</div><p>sibling</p>", is_fragment=True)
    root = tree.root

    assert root.css_matches("table") is False
    assert root.any_css_matches(("table",)) is False
    assert root.any_css_matches(("table", "section")) is False
    # `p` is not a child of `div`, it is a sibling of it
    assert root.css_matches("div > p") is False
    # the root node itself and its own subtree are still reachable
    assert root.css_matches("div") is True


@pytest.mark.parametrize(
    "method, args", [("css_matches", ("p",)), ("any_css_matches", (("p",),))]
)
def test_match_helpers_agree_for_non_fragment_nodes(method, args):
    """Only fragment roots change scope; ordinary nodes keep matching their subtree."""
    tree = LexborHTMLParser('<div id="a"><p>x</p><span>s</span></div>')
    div = tree.css_first("div")

    assert getattr(div, method)(*args) is True
    assert (
        getattr(div, method)(
            *(("table",) if method == "css_matches" else (("table",),))
        )
        is False
    )

    assert getattr(tree.root, method)(*args) is True
    assert getattr(tree.body, method)(*args) is True
