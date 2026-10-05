import pytest

from selectolax.lexbor import LexborHTMLParser
from tests.helpers import clean_doc


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


def test_fragment_root_follows_unwrap():
    parser = LexborHTMLParser("<div><span>a</span></div><p>b</p>", is_fragment=True)
    parser.root.unwrap()

    # Unwrapping the first top-level node used to leave the parser pointing at
    # the detached <div>, hiding every sibling behind it.
    assert parser.html == "<span>a</span><p>b</p>"
    assert parser.root.tag == "span"
    assert parser.root.parent is None
    assert [node.tag for node in parser.root.iter()] == ["span", "p"]
    assert parser.text() == "ab"
    assert len(parser.css("span")) == 1
    assert len(parser.css("p")) == 1


def test_fragment_root_follows_decompose():
    parser = LexborHTMLParser("<div><span>a</span></div><p>b</p>", is_fragment=True)
    parser.root.decompose()

    assert parser.html == "<p>b</p>"
    assert parser.root.tag == "p"
    assert parser.text() == "b"


def test_fragment_root_follows_replace_with():
    parser = LexborHTMLParser("<div><span>a</span></div><p>b</p>", is_fragment=True)
    parser.root.replace_with("X")

    assert parser.html == "X<p>b</p>"
    assert parser.root.is_text_node


def test_fragment_root_follows_strip_tags():
    parser = LexborHTMLParser("<div><i>a</i></div><p><i>b</i></p>", is_fragment=True)
    parser.root.strip_tags(["div"])

    assert parser.html == "<p><i>b</i></p>"
    assert parser.root.tag == "p"


def test_fragment_root_follows_insert_before():
    parser = LexborHTMLParser("<div>a</div><p>b</p>", is_fragment=True)
    replacement = LexborHTMLParser("<span>x</span>", is_fragment=True)
    parser.root.insert_before(replacement.root)

    # A node inserted in front of the root used to be dropped from the
    # serialization, which starts at the root and walks its siblings.
    assert parser.html == "<span>x</span><div>a</div><p>b</p>"
    assert parser.root.tag == "span"


def test_fragment_root_tracks_until_fragment_is_empty():
    parser = LexborHTMLParser("<a>1</a><b>2</b>", is_fragment=True)

    parser.root.unwrap()
    assert parser.root.is_text_node
    assert parser.html == "1<b>2</b>"

    # Unwrapping a text node is a no-op, so the root stays where it is.
    parser.root.unwrap()
    assert parser.html == "1<b>2</b>"


def test_fragment_root_is_none_once_emptied():
    parser = LexborHTMLParser("<div>a</div>", is_fragment=True)
    parser.root.decompose()

    assert parser.root is None
    assert parser.html == ""


def test_fragment_root_survives_repeated_unwrap_of_every_top_level_node():
    parser = LexborHTMLParser("<a>1</a><b>2</b><c>3</c>", is_fragment=True)

    # Unwrapping an element lifts its text out in front of it, so the root
    # walks the text nodes first and only then the remaining elements.
    for expected_root in ("-text", "b", "-text", "c", "-text"):
        parser.root.unwrap(delete_empty=True)
        assert parser.root.tag == expected_root

    parser.root.unwrap(delete_empty=True)
    assert parser.root is None
    assert parser.html == ""


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


def test_fragment_parser_malformed_html():
    html = "<div><unclosed><span>content"
    parser = LexborHTMLParser(html, is_fragment=True)
    html_result = parser.html
    assert html_result is not None
    assert "content" in html_result


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


def test_empty_fragment_inner_html_setter_fills_the_fragment():
    tree = LexborHTMLParser("", is_fragment=True)
    tree.inner_html = "<p>filled</p>"
    assert tree.inner_html == "<p>filled</p>"
    assert tree.html == "<p>filled</p>"
    assert tree.root is not None


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
