from gc import collect as gc_collect

import pytest

from selectolax.lexbor import LexborHTMLParser


def test_node_cloning():
    parser = LexborHTMLParser("<div id='main'>123</div>")
    new_node = parser.css_first("#main").clone()
    new_node.inner_html = "<div>new</div>"
    assert parser.css_first("#main").html != new_node.html
    assert new_node.html == '<div id="main"><div>new</div></div>'


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


def test_clone():
    html_parser = LexborHTMLParser("""<h1>Welcome</h1>""")
    clone = html_parser.clone()
    html_parser.root.css_first("h1").decompose()
    del html_parser
    assert clone.html == "<html><head></head><body><h1>Welcome</h1></body></html>"


def test_clone_handling():
    html_parser = LexborHTMLParser("<div>test</div>")

    cloned = html_parser.clone()
    assert cloned.html is not None

    assert html_parser.html is not None
