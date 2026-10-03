"""Undecodable bytes must never raise out of a read.

Lexbor passes bytes it cannot decode through verbatim, so a single stray byte
anywhere in an untrusted document used to make ``html``, ``attributes`` and
``attrs`` raise ``UnicodeDecodeError`` while ``text()`` quietly substituted
U+FFFD. Every accessor now substitutes U+FFFD, and agrees with the others.
"""

import pytest

from selectolax.lexbor import LexborHTMLParser

# Stands in for whatever the document happened to contain.
BAD = "\N{REPLACEMENT CHARACTER}"

_PARSERS = (LexborHTMLParser,)

_PARSERS_PARAMETRIZER = (
    "parser",
    _PARSERS,
)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_bad_bytes_in_text_do_not_raise(parser):
    tree = parser(b"<div>x\xffy</div>")
    div = tree.css_first("div")

    assert div.text() == f"x{BAD}y"
    assert div.child.text_content == f"x{BAD}y"
    assert div.text_lexbor() == f"x{BAD}y"
    assert div.text(strip=True) == f"x{BAD}y"
    assert div.inner_html == f"x{BAD}y"
    assert div.html == f"<div>x{BAD}y</div>"
    assert tree.text() == f"x{BAD}y"
    assert tree.html == f"<html><head></head><body><div>x{BAD}y</div></body></html>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_lone_surrogate_bytes_do_not_raise(parser):
    """CESU-8 style surrogates are valid lexbor output but not valid UTF-8."""
    tree = parser(b"<div>x\xed\xa0\x80y</div>")
    div = tree.css_first("div")

    assert div.text() == f"x{BAD * 3}y"
    assert div.child.text_content == f"x{BAD * 3}y"
    assert div.html == f"<div>x{BAD * 3}y</div>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_every_text_accessor_agrees(parser):
    tree = parser(b"<div>x\xffy</div>")
    div = tree.css_first("div")
    expected = f"x{BAD}y"

    assert div.text() == expected
    assert div.child.text_content == expected
    assert div.text_lexbor() == expected
    assert div.text(strip=True) == expected


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_bad_bytes_in_an_attribute_value_do_not_raise(parser):
    tree = parser(b"<div a='\xff' b='ok'>x</div>")
    div = tree.css_first("div")

    assert div.attrs["a"] == BAD
    assert div.attrs.get("a") == BAD
    assert div.attrs.sget("a") == BAD
    assert "a" in div.attrs
    assert list(div.attrs.items()) == [("a", BAD), ("b", "ok")]
    assert div.attributes == {"a": BAD, "b": "ok"}
    assert div.html == f'<div a="{BAD}" b="ok">x</div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_bad_bytes_in_an_attribute_name_do_not_raise(parser):
    tree = parser(b"<div \xff='1'>x</div>")
    div = tree.css_first("div")

    assert list(div.attrs.keys()) == [BAD]
    assert list(div.attrs.items()) == [(BAD, "1")]
    assert div.attributes == {BAD: "1"}
    assert repr(div.attrs) == "<div attributes, 1 items>"
    assert div.html == f'<div {BAD}="1">x</div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_bad_bytes_in_an_id_do_not_raise(parser):
    tree = parser(b"<div id='\xff'>x</div>")

    assert tree.css_first("div").id == BAD


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_bad_bytes_in_a_tag_name_do_not_raise(parser):
    tree = parser(b"<div><\xff>x</\xff></div>")

    assert BAD in tree.html
    assert all(isinstance(node.tag, (str, type(None))) for node in tree.root.traverse())


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_selector_filters_do_not_raise_on_bad_bytes(parser):
    tree = parser(b"<a href='/x\xffy' title='t'>l</a>")

    assert tree.select("a").any_attribute_longer_than("href", 0)
    assert tree.select("a").attribute_longer_than("href", 0).any_matches
    assert tree.select("a").any_text_contains("l")


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_pretty_printing_does_not_raise_on_bad_bytes(parser):
    tree = parser(b"<div a='\xff'>x</div>")

    assert isinstance(tree.html_pretty(), str)
    assert isinstance(tree.inner_html_pretty(), str)
    assert isinstance(tree.css_first("div").html_pretty(), str)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_fragment_parsing_does_not_raise_on_bad_bytes(parser):
    tree = parser(b"<div a='\xff'>x\xffy</div>", is_fragment=True)

    assert tree.html == f'<div a="{BAD}">x{BAD}y</div>'
    assert tree.text() == f"x{BAD}y"
    assert tree.root.attributes == {"a": BAD}


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_valid_utf8_is_left_alone(parser):
    tree = parser("<p>Привет 🎉</p>".encode())

    assert tree.text() == "Привет 🎉"
    assert tree.html == "<html><head></head><body><p>Привет 🎉</p></body></html>"
    assert parser("<div title='🎉'>Привет</div>").css_first("div").attributes == {
        "title": "🎉"
    }
