from inspect import cleandoc
import pytest
from selectolax.lexbor import LexborHTMLParser

# TODO:
# 1) .clone on document, .clone on node
# 2) Any kind of tree modification


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
