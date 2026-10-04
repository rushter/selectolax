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


# Tags whose start tag the "in body" insertion mode drops, so parsing
# `<tag></tag>` as an HTML fragment used to produce an empty tree and make
# create_tag() return None. They have to be creatable, like any other tag.
DROPPED_BY_PARSER_TAGS = [
    "html",
    "head",
    "body",
    "caption",
    "col",
    "colgroup",
    "frame",
    "frameset",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
]

# Void elements have no end tag, so the serializer omits it.
VOID_TAGS = {"col", "frame"}


@pytest.mark.parametrize("tag", DROPPED_BY_PARSER_TAGS)
def test_create_tag_works_for_tags_dropped_by_the_parser(tag: str):
    node = create_tag(tag)
    assert node is not None
    assert isinstance(node, LexborNode)
    assert node.tag == tag
    assert node.attributes == {}
    expected = f"<{tag}>" if tag in VOID_TAGS else f"<{tag}></{tag}>"
    assert node.html == expected


def test_create_tag_does_not_parse_the_tag_name():
    # Building the node by parsing would apply the parser's aliasing and
    # end-tag handling; creating the element applies neither.
    assert create_tag("image").tag == "image"
    # `plaintext` swallows the rest of the document when parsed, so its closing
    # tag ended up as text.
    assert create_tag("plaintext").html == "<plaintext></plaintext>"


def test_create_tag_rejects_an_empty_tag_name():
    with pytest.raises(SelectolaxError):
        create_tag("")


def test_parse_fragment_is_removed():
    with pytest.raises(SelectolaxError, match="is_fragment=True"):
        parse_fragment("<div>x</div>")


def test_fragment_parser_is_the_replacement():
    parser = LexborHTMLParser("<div>x</div><p>y</p>", is_fragment=True)
    assert parser.html == "<div>x</div><p>y</p>"
    assert [n.tag for n in parser.root.iter(include_text=True)] == ["div", "p"]
