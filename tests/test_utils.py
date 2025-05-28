"""
We'are testing only our own code.
Many functionality are already tested in the Modest engine, so there is no reason to test every case.
"""

from typing import Callable, NamedTuple, Sequence, Type, Union

import pytest
from selectolax.parser import HTMLParser, Node, create_tag, parse_fragment
from selectolax.lexbor import (
    LexborHTMLParser,
    LexborNode,
    create_tag as lexbor_create_tag,
    parse_fragment as lexbor_parse_fragment,
)


class Impl(NamedTuple):
    parser: Union[Type[HTMLParser], Type[LexborHTMLParser]]
    node: Union[Type[Node], Type[LexborNode]]
    tag_fn: Callable[[str], Union[Node, LexborNode]]
    parse_fragment_fn: Callable[[str], Sequence[Union[Node, LexborNode]]]


_IMPL_PARAMETRIZER = (
    "impl",
    (
        Impl(
            parser=HTMLParser,
            node=Node,
            tag_fn=create_tag,
            parse_fragment_fn=parse_fragment,
        ),
        Impl(
            parser=LexborHTMLParser,
            node=LexborNode,
            tag_fn=lexbor_create_tag,
            parse_fragment_fn=lexbor_parse_fragment,
        ),
    ),
)


@pytest.mark.parametrize(*_IMPL_PARAMETRIZER)
def test_create_tag(impl: Impl):
    node = impl.tag_fn("p")
    assert isinstance(node, impl.node)
    assert node.html == "<p></p>"


@pytest.mark.parametrize(*_IMPL_PARAMETRIZER)
def test_create_header_tag(impl: Impl):
    node = impl.tag_fn("header")
    assert isinstance(node, impl.node)
    assert node.html == "<header></header>"


# Cases to test parse_fragment():
# - <doctyle> + <html> only
# - HTML with <head>
# - HTML with <body>
# - HTML with <doctype>, <head> and <body>
# - <head> and <body> only without <html>
# - <head> only
# - <body> only
# - <link> and <meta>'s only (as content of <head>)
# - <div>, <script> (as content of <body>)
# - <link> and <div> next to each other (as invalid HTML, but valid fragment)


@pytest.mark.parametrize(*_IMPL_PARAMETRIZER)
def test_parse_fragment_doctype_html(impl: Impl):
    html = "<!DOCTYPE html><html></html>"
    nodes = impl.parse_fragment_fn(html)
    assert len(nodes) == 1
    assert nodes[0].tag == "html"
    assert nodes[0].html == "<html></html>"
    assert nodes[0].parser.html == "<!DOCTYPE html><html></html>"

    assert len(nodes[0].parser.css("head")) == 0
    assert len(nodes[0].parser.css("body")) == 0


@pytest.mark.parametrize(*_IMPL_PARAMETRIZER)
def test_parse_fragment_html_with_head(impl: Impl):
    html = '<!DOCTYPE html><html><head><link href="http://"></head></html>'
    nodes = impl.parse_fragment_fn(html)
    assert len(nodes) == 1
    assert nodes[0].tag == "html"
    assert nodes[0].html == '<html><head><link href="http://"></head></html>'
    assert (
        nodes[0].parser.html
        == '<!DOCTYPE html><html><head><link href="http://"></head></html>'
    )

    assert len(nodes[0].parser.css("head")) == 1
    assert len(nodes[0].parser.css("body")) == 0


@pytest.mark.parametrize(*_IMPL_PARAMETRIZER)
def test_parse_fragment_html_with_body(impl: Impl):
    html = '<!DOCTYPE html><html><body><div><script src="http://"></script></div></body></html>'
    nodes = impl.parse_fragment_fn(html)
    assert len(nodes) == 1
    assert nodes[0].tag == "html"
    assert (
        nodes[0].html
        == '<html><body><div><script src="http://"></script></div></body></html>'
    )
    assert (
        nodes[0].parser.html
        == '<!DOCTYPE html><html><body><div><script src="http://"></script></div></body></html>'
    )

    assert len(nodes[0].parser.css("head")) == 0
    assert len(nodes[0].parser.css("body")) == 1


@pytest.mark.parametrize(*_IMPL_PARAMETRIZER)
def test_parse_fragment_html_with_head_and_body(impl: Impl):
    html = '<!DOCTYPE html><html><head><link href="http://"></head><body><div><script src="http://"></script></div></body></html>'  # noqa: E501
    nodes = impl.parse_fragment_fn(html)
    assert len(nodes) == 1
    assert nodes[0].tag == "html"
    assert (
        nodes[0].html
        == '<html><head><link href="http://"></head><body><div><script src="http://"></script></div></body></html>'
    )  # noqa: E501
    assert (
        nodes[0].parser.html
        == '<!DOCTYPE html><html><head><link href="http://"></head><body><div><script src="http://"></script></div></body></html>'
    )  # noqa: E501

    assert len(nodes[0].parser.css("head")) == 1
    assert len(nodes[0].parser.css("body")) == 1


@pytest.mark.parametrize(*_IMPL_PARAMETRIZER)
def test_parse_fragment_head_and_body_no_html(impl: Impl):
    html = '<head><link href="http://"></head><body><div><script src="http://"></script></div></body>'
    nodes = impl.parse_fragment_fn(html)
    assert len(nodes) == 2
    assert nodes[0].tag == "head"
    assert nodes[1].tag == "body"
    assert nodes[0].html == '<head><link href="http://"></head>'
    assert nodes[1].html == '<body><div><script src="http://"></script></div></body>'
    assert (
        nodes[0].parser.html
        == '<html><head><link href="http://"></head><body><div><script src="http://"></script></div></body></html>'
    )  # noqa: E501

    assert len(nodes[0].parser.css("head")) == 1
    assert len(nodes[0].parser.css("body")) == 1


@pytest.mark.parametrize(*_IMPL_PARAMETRIZER)
def test_parse_fragment_head_no_html(impl: Impl):
    html = '<head><link href="http://"></head>'
    nodes = impl.parse_fragment_fn(html)
    assert len(nodes) == 1
    assert nodes[0].tag == "head"
    assert nodes[0].html == '<head><link href="http://"></head>'
    assert nodes[0].parser.html == '<html><head><link href="http://"></head></html>'

    assert len(nodes[0].parser.css("head")) == 1
    assert len(nodes[0].parser.css("body")) == 0


@pytest.mark.parametrize(*_IMPL_PARAMETRIZER)
def test_parse_fragment_body_no_html(impl: Impl):
    html = '<body><div><script src="http://"></script></div></body>'
    nodes = impl.parse_fragment_fn(html)
    assert len(nodes) == 1
    assert nodes[0].tag == "body"
    assert nodes[0].html == '<body><div><script src="http://"></script></div></body>'
    assert (
        nodes[0].parser.html
        == '<html><body><div><script src="http://"></script></div></body></html>'
    )

    assert len(nodes[0].parser.css("head")) == 0
    assert len(nodes[0].parser.css("body")) == 1


@pytest.mark.parametrize(*_IMPL_PARAMETRIZER)
def test_parse_fragment_fragment(impl: Impl):
    html = '<link href="http://"><div><script src="http://"></script></div>'
    nodes = impl.parse_fragment_fn(html)
    assert len(nodes) == 2
    assert nodes[0].tag == "link"
    assert nodes[1].tag == "div"
    assert nodes[0].html == '<link href="http://">'
    assert nodes[1].html == '<div><script src="http://"></script></div>'

    # NOTE: Ideally the full HTML would NOT contain `<html>`, `<head>` and `<body>` in this case,
    # but this is technical limitation of the parser.
    # But as long as user serializes fragment nodes by as `Node.html`, they should be fine.
    assert (
        nodes[0].parser.html
        == '<html><head><link href="http://"></head><body><div><script src="http://"></script></div></body></html>'
    )  # noqa: E501
    assert len(nodes[0].parser.css("head")) == 1
    assert len(nodes[0].parser.css("body")) == 1
