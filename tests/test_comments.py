import time

import pytest

from selectolax.lexbor import (
    LexborHTMLParser,
    extract_html_comment,
)


def test_comment_content_property() -> None:
    parser = LexborHTMLParser("<div><span><!-- hello --></span><title>X</title></div>")
    span = parser.css_first("span")
    assert span is not None
    text_node = span.first_child
    assert text_node is not None
    assert text_node.is_comment_node
    assert text_node.comment_content == "hello"


@pytest.mark.parametrize(
    "source,expected",
    [
        ("<!--a-->", "a"),
        ("<!--  a  -->", "a"),
        ("<!--\n\ta\n-->", "a"),
        ("<!---->", ""),
        ("<!-->", ""),
    ],
)
def test_comment_content_of_variants(source: str, expected: str) -> None:
    node = LexborHTMLParser(source, is_fragment=True).root
    assert node is not None
    assert node.comment_content == expected


def test_comment_content_is_scoped_to_its_own_node() -> None:
    parser = LexborHTMLParser("<!--a--><!--b-->", is_fragment=True)
    root = parser.root
    assert root is not None
    assert root.comment_content == "a"
    second = root.next
    assert second is not None
    assert second.comment_content == "b"


def test_comment_content_handles_an_unterminated_comment() -> None:
    node = LexborHTMLParser("<!--a--", is_fragment=True).root
    assert node is not None
    assert node.comment_content == "a"


def test_fragment_comment_content():
    html = "<!-- comment -->"
    parser = LexborHTMLParser(html, is_fragment=True)
    comment_node = parser.root
    assert comment_node.comment_content == "comment"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("<!--a-->", "a"),
        ("  <!--a-->  ", "a"),
        ("<!-- a -->", "a"),
        ("<!--\n a \n-->", "a"),
        ("<!--  -->", ""),
        ("<!---->", ""),
        ("<!----->", "-"),
        ("<!--a-->b-->", "a-->b"),
    ],
)
def test_extract_html_comment(text: str, expected: str):
    assert extract_html_comment(text) == expected


@pytest.mark.parametrize(
    "text",
    ["", " ", "<!----", "<!--", "-->", "a<!--b-->", "<!-->", "<!--->"],
)
def test_extract_html_comment_rejects_non_comments(text: str):
    with pytest.raises(ValueError, match="not a valid HTML comment"):
        extract_html_comment(text)


@pytest.mark.parametrize("size", [1000, 5000, 20000])
def test_extract_html_comment_is_linear(size: int):
    text = "<!--" + " " * size + "x"
    started = time.perf_counter()
    with pytest.raises(ValueError):
        extract_html_comment(text)
    assert time.perf_counter() - started < 1.0
