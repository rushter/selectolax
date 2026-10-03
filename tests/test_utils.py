"""
We'are testing only our own code.
Many functionality are already tested in the Lexbor engine, so there is no reason to test every case.
"""

from __future__ import annotations

import pytest

from selectolax.lexbor import (
    LexborHTMLParser,
    LexborNode,
    SelectolaxError,
    create_tag,
    parse_fragment,
)


@pytest.mark.parametrize("tag", ["p", "header", "div", "span", "custom-element"])
def test_create_tag(tag: str):
    node = create_tag(tag)
    assert isinstance(node, LexborNode)
    assert node.tag == tag
    assert node.html == f"<{tag}></{tag}>"


def test_create_tag_uses_the_fragment_parser():
    # create_tag() builds its node through `is_fragment=True`, so it no longer
    # depends on the removed fragment-type guessing helpers. A fragment parser
    # does not synthesize <html>/<head>/<body>.
    node = create_tag("div")
    assert node.parser.html == "<div></div>"
    assert node.parser.head is None
    assert node.parser.body is None


def test_parse_fragment_is_removed():
    with pytest.raises(SelectolaxError, match="is_fragment=True"):
        parse_fragment("<div>x</div>")


def test_fragment_parser_is_the_replacement():
    parser = LexborHTMLParser("<div>x</div><p>y</p>", is_fragment=True)
    assert parser.html == "<div>x</div><p>y</p>"
    assert [n.tag for n in parser.root.iter(include_text=True)] == ["div", "p"]
