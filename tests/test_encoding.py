"""Tests for the encoding detection behind ``LexborHTMLParser(..., encoding=True)``."""

import pytest

import selectolax.lexbor as lexbor_module
from selectolax.lexbor import LexborHTMLParser

# Encoded documents whose declared encoding is not UTF-8.
CYRILLIC = "Привет"
JAPANESE = "日本語"


def test_bytes_are_parsed_as_utf8_by_default():
    # The default has to stay exactly as it was: no detection, no transcoding,
    # and a declaration in the document means nothing.
    raw = f'<meta charset="windows-1251"><p>{CYRILLIC}</p>'.encode("windows-1251")

    parser = LexborHTMLParser(raw)

    assert parser.raw_html == raw
    assert parser.css_first("meta").attributes["charset"] == "windows-1251"
    assert parser.text() != CYRILLIC
    # The bytes are not repaired, but reading them substitutes U+FFFD rather
    # than raising: a declaration in the document still means nothing here.
    assert parser.html == (
        '<html><head><meta charset="windows-1251"></head>'
        f"<body><p>{'�' * len(CYRILLIC)}</p></body></html>"
    )


def test_meta_charset_is_honored():
    raw = f'<meta charset="windows-1251"><p>{CYRILLIC}</p>'.encode("windows-1251")

    parser = LexborHTMLParser(raw, encoding=True)

    assert parser.text() == CYRILLIC
    assert parser.html == (
        '<html><head><meta charset="windows-1251"></head>'
        f"<body><p>{CYRILLIC}</p></body></html>"
    )


def test_http_equiv_content_type_is_honored():
    raw = (
        '<meta http-equiv="Content-Type" content="text/html; charset=windows-1251">'
        f"<p>{CYRILLIC}</p>"
    ).encode("windows-1251")

    assert LexborHTMLParser(raw, encoding=True).text() == CYRILLIC


@pytest.mark.parametrize(
    "declaration",
    [
        '<meta charset="Shift_JIS">',
        "<meta charset=shift_jis>",
        "<meta charset='shift_jis'>",
        '<meta charset=" shift_jis ">',
        '<meta http-equiv="content-type" content="text/html;charset=shift_jis">',
    ],
)
def test_declaration_forms(declaration):
    raw = f"<p>{JAPANESE}</p>{declaration}".encode("shift_jis")

    assert LexborHTMLParser(raw, encoding=True).text() == JAPANESE


def test_declaration_wins_over_a_bom_free_default():
    # UTF-8 is what an undeclared document is decoded as, so a declaration that
    # says otherwise has to actually be read.
    raw = '<meta charset="iso-8859-1"><p>café</p>'.encode("iso-8859-1")

    parser = LexborHTMLParser(raw, encoding=True)

    assert parser.text() == "café"


def test_utf8_bom_is_skipped():
    raw = b"\xef\xbb\xbf" + "<p>café</p>".encode()

    assert LexborHTMLParser(raw, encoding=True).text() == "café"
    assert LexborHTMLParser(raw, encoding=True).html.startswith("<html>")


@pytest.mark.parametrize(
    "encoding,bom",
    [("utf-16-le", b"\xff\xfe"), ("utf-16-be", b"\xfe\xff")],
)
def test_utf16_bom_is_decoded(encoding, bom):
    raw = bom + "<p>café 中</p>".encode(encoding)

    assert LexborHTMLParser(raw, encoding=True).text() == "café 中"


def test_utf16_without_a_bom():
    # The XML declaration is what identifies these; the standard prescan looks
    # for it at the very start of the stream.
    raw = '<?xml version="1.0" encoding="UTF-16"?><p>café</p>'.encode("utf-16-le")

    assert LexborHTMLParser(raw, encoding=True).text() == "café"


def test_declaration_after_the_prescan_window_is_ignored():
    # The standard stops looking for a declaration after 1024 bytes, and lexbor
    # scans as far as it is allowed to. Honouring a later one would let page
    # content decide the encoding it is decoded with.
    padding = "<!--{}-->".format("x" * 1100)
    raw = f"{padding}<meta charset='windows-1251'><p>{CYRILLIC}</p>".encode(
        "windows-1251"
    )

    parser = LexborHTMLParser(raw, encoding=True)

    assert parser.text() != CYRILLIC


def test_unknown_declaration_falls_back_to_utf8():
    raw = '<meta charset="definitely-not-an-encoding"><p>café</p>'.encode()

    assert LexborHTMLParser(raw, encoding=True).text() == "café"


@pytest.mark.parametrize(
    "label",
    [
        # Transforms from the codec module that cannot read text. Each of these
        # used to raise from inside the codec rather than fall back: base64 and
        # friends an AssertionError out of binascii, rot13 a TypeError about
        # str.translate, idna a UnicodeError about its error handler.
        "base64",
        "base32",
        "base85",
        "hex",
        "binascii",
        "zlib",
        "bz2",
        "uu",
        "quopri",
        "rot13",
        "rot_13",
        "idna",
    ],
)
def test_declaration_naming_a_non_encoding_falls_back_to_utf8(label):
    raw = f'<meta charset="{label}"><p>Hello world</p>'.encode()

    assert LexborHTMLParser(raw, encoding=True).text() == "Hello world"


def test_ignoring_an_unusable_label_keeps_the_rest_of_the_document_intact():
    # The label is dropped, but the declaration itself is ordinary markup and
    # has to survive like any other attribute.
    raw = b'<meta charset="base64" name="x"><p id="a">Hello</p>'

    parser = LexborHTMLParser(raw, encoding=True)

    assert parser.text() == "Hello"
    assert parser.css_first("meta").attributes == {"charset": "base64", "name": "x"}
    assert parser.css_first("#a").text() == "Hello"


def test_x_user_defined_is_read_as_windows_1252():
    # 0x80 is a euro sign in windows-1252, which is what the standard maps the
    # x-user-defined label to. Python has no codec by that name.
    raw = '<meta charset="x-user-defined"><p>a\x80b</p>'.encode("latin-1")

    assert LexborHTMLParser(raw, encoding=True).text() == "a€b"


def test_invalid_bytes_become_replacement_characters():
    # 0x81 starts a two-byte sequence in gb18030 and nothing follows it, so it
    # cannot be decoded. The standard has those bytes become U+FFFD rather than
    # being kept, which would break every accessor that reads the tree back out.
    raw = b'<meta charset="gb18030"><p>ok\x81</p>'

    parser = LexborHTMLParser(raw, encoding=True)

    assert parser.text() == "ok�"
    assert parser.html == (
        '<html><head><meta charset="gb18030"></head><body><p>ok�</p></body></html>'
    )


def test_raw_html_holds_the_parsed_bytes():
    raw = f'<meta charset="windows-1251"><p>{CYRILLIC}</p>'.encode("windows-1251")

    parser = LexborHTMLParser(raw, encoding=True)

    assert parser.raw_html == f'<meta charset="windows-1251"><p>{CYRILLIC}</p>'.encode()
    assert parser.clone().raw_html == parser.raw_html


def test_text_input_is_untouched():
    html = f'<meta charset="windows-1251"><p>{CYRILLIC}</p>'

    for encoding in (False, True):
        parser = LexborHTMLParser(html, encoding=encoding)
        assert parser.text() == CYRILLIC
        assert parser.raw_html == html.encode()


def test_fragments_are_decoded_too():
    raw = f'<meta charset="windows-1251"><p>{CYRILLIC}</p>'.encode("windows-1251")

    parser = LexborHTMLParser(raw, is_fragment=True, encoding=True)

    assert parser.text() == CYRILLIC
    assert parser.root.tag == "meta"


def test_multibyte_character_across_a_chunk_boundary():
    # Transcoding walks the input in slices, so a character whose bytes land on
    # either side of a slice boundary must not come out broken.
    padding = "a" * (lexbor_module._TRANSCODE_CHUNK_SIZE - 1)
    raw = f'<meta charset="shift_jis"><p>{padding}{JAPANESE}</p>'.encode("shift_jis")

    parser = LexborHTMLParser(raw, encoding=True)

    assert parser.text() == padding + JAPANESE


def test_transcoded_input_is_size_limited(monkeypatch):
    # Decoding can grow the input, so the limit applies to the result too.
    monkeypatch.setattr(lexbor_module, "MAX_HTML_INPUT_SIZE", 16)
    raw = f'<meta charset="utf-8"><p>{"x" * 64}</p>'.encode()

    with pytest.raises(ValueError, match="too large"):
        LexborHTMLParser(raw, encoding=True)


def test_undeclared_input_keeps_its_bytes():
    # Nothing is declared, so the document is read as UTF-8 and bytes that are
    # not valid UTF-8 are left alone rather than repaired. Reading them
    # substitutes U+FFFD.
    raw = "<p>café</p>".encode("iso-8859-1")

    parser = LexborHTMLParser(raw, encoding=True)

    assert parser.raw_html == raw
    assert parser.html == "<html><head></head><body><p>caf�</p></body></html>"
