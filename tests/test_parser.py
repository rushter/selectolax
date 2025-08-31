import threading
from difflib import SequenceMatcher

import pytest
from selectolax.parser import HTMLParser, Node

from selectolax.lexbor import LexborHTMLParser, LexborNode, SelectolaxError, create_tag

"""
We'are testing only our own code.
Many functionality are already tested in the Modest engine, so there is no reason to test every case.
"""

_PARSERS_PARAMETRIZER = (
    "parser",
    (HTMLParser, LexborHTMLParser),
)


def test_encoding():
    html = "<div><p id=p1><p id=p2><p id=p3><a>link</a><p id=p4><p id=p5>text<p id=p6></div>"
    html = HTMLParser(html)
    assert html.input_encoding == "UTF-8"

    html = b"<div><p id=p1><p id=p2><p id=p3><a>link</a><p id=p4><p id=p5>text<p id=p6></div>"
    html = HTMLParser(html)
    assert html.input_encoding == "UTF-8"

    html = "<div>Привет мир!</div>".encode("cp1251")
    assert HTMLParser(html, detect_encoding=True).input_encoding == "WINDOWS-1251"

    html_utf = '<head><meta charset="WINDOWS-1251"></head>'.encode("utf-8")
    assert (
        HTMLParser(html_utf, detect_encoding=True, use_meta_tags=True).input_encoding
        == "WINDOWS-1251"
    )

    # UTF-16 not ASCII-readable
    html_utf = '<head><meta charset="WINDOWS-1251"></head>'.encode("utf-16le")
    assert (
        HTMLParser(html_utf, detect_encoding=True, use_meta_tags=True).input_encoding
        == "UTF-16LE"
    )

    # Unencodable characters in string, should not throw an exception by default
    html_unencodable = b"<div>Roboto+Condensed</div>".decode("utf-7", errors="ignore")
    assert HTMLParser(html_unencodable).input_encoding == "UTF-8"

    # decode_errrors='strict' should error out
    try:
        HTMLParser(html_unencodable, decode_errors="strict")
        assert False
    except Exception as e:
        assert type(e) is UnicodeEncodeError


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_parser(parser):
    html = parser("")
    assert isinstance(html, parser)

    with pytest.raises(TypeError):
        parser(123)

    with pytest.raises(TypeError):
        parser("asd").css(123)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_malformed_data(parser):
    malformed_inputs = [
        b"\x00\x01\x02\x03",
        "<div><p><span></div>",
        "<" + "a" * 1000 + ">",
    ]

    for malformed_html in malformed_inputs:
        try:
            html_parser = parser(malformed_html)
            # Should not crash, but may return None or empty results
            result = html_parser.html
            assert result is None or isinstance(result, str)
        except (ValueError, RuntimeError, UnicodeDecodeError):
            # These exceptions are acceptable for malformed input
            pass


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_properties(parser):
    html_parser = parser("<div><p>test</p></div>")

    properties_to_test = ["root", "head", "body", "html"]

    for prop_name in properties_to_test:
        getattr(html_parser, prop_name)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_unicode_handling(parser):
    unicode_content = [
        "Hello 世界",
        "🚀🌟💫",
        "Café résumé naïve",
    ]

    for content in unicode_content:
        html = f"<div>{content}</div>"
        try:
            html_parser = parser(html)
            result = html_parser.css_first("div")
            if result:
                extracted_text = result.text()
                assert content in extracted_text
        except UnicodeEncodeError:
            # Some encoding issues might be expected
            pass


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_tag_name_validation(parser):
    """Test that tag name validation works correctly."""
    html_parser = parser("<div></div>")

    # Empty tag name should be rejected
    with pytest.raises(ValueError, match="Tag name cannot be empty"):
        html_parser.tags("")

    # Very long tag names should be rejected
    long_tag_name = "a" * 101  # Exceeds 100 character limit
    with pytest.raises(ValueError, match="Tag name is too long"):
        html_parser.tags(long_tag_name)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_nodes(parser):
    html = (
        '<div><p id="p1"></p><p id="p2"></p><p id="p3"><a>link</a></p>'
        '<p id="p4"></p><p id="p5">text</p><p id="p6"></p></div>'
    )
    htmlp = parser(html)

    assert isinstance(htmlp.root, (Node, LexborNode))
    assert isinstance(htmlp.body, (Node, LexborNode))
    html_output = htmlp.html
    assert len(html_output) >= len(html)
    assert SequenceMatcher(None, html, html_output).ratio() > 0.8


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_root_css(parser):
    tree = parser("test")
    assert len(tree.root.css("data")) == 0


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_strip_tags_from_root(parser):
    html = "<body><div></div><script></script></body>"
    html_parser = parser(html)
    html_parser.root.strip_tags(["div", "script"])
    assert html_parser.html == "<html><head></head><body></body></html>"

    with pytest.raises(TypeError):
        html_parser.strip_tags(1)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_clone(parser):
    html_parser = parser("""<h1>Welcome</h1>""")
    clone = html_parser.clone()
    html_parser.root.css_first("h1").decompose()
    del html_parser
    assert clone.html == "<html><head></head><body><h1>Welcome</h1></body></html>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_tags(parser):
    html_parser = parser("""
    <div><span><span></span></span></div>
    <div><span></span></div>
    <div><div></div></div>
    <span></span>
    <div></div>
    """)
    assert len(html_parser.tags("div")) == 5


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_preserves_doctype(parser):
    html_parser = parser("""
    <!DOCTYPE html>
    <html>
        <head><title>Test</title></head>
        <body><p>Hello World</p></body>
    </html>
    """)
    assert "<!DOCTYPE html>" in html_parser.html


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_invalid_input_types(parser):
    with pytest.raises(TypeError, match="Expected a string"):
        parser(123)

    with pytest.raises(TypeError, match="Expected a string"):
        parser([])

    with pytest.raises(TypeError, match="Expected a string"):
        parser(None)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_clone_handling(parser):
    html_parser = parser("<div>test</div>")

    cloned = html_parser.clone()
    assert cloned.html is not None

    assert html_parser.html is not None


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_concurrent_parsing(parser):
    """Test that concurrent parsing doesn't cause race conditions."""
    results = []
    errors = []
    lock = threading.Lock()

    def parse_html(content):
        try:
            html_parser = parser(content)
            result = html_parser.body.text()
            if result:
                with lock:
                    results.append(result)
        except Exception as e:
            with lock:
                errors.append(e)

    threads = []
    test_content = "<div>Content {}</div>"

    for i in range(50):
        content = test_content.format(i)
        t1 = threading.Thread(target=parse_html, args=(content,))
        threads.append(t1)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(results) == 50


def test_css_selector_error_handling():
    html_parser = LexborHTMLParser("<div class='test'>content</div>")

    # Invalid selector types should raise TypeError
    with pytest.raises(TypeError):
        html_parser.css(123)

    with pytest.raises(TypeError):
        html_parser.css(None)

    invalid_selectors = [
        ":::",
        "[[[",
        "div{color:red}",
        'h3:contains("some substring")',
    ]

    for selector in invalid_selectors:
        try:
            result = html_parser.css(selector)
            # Should return empty list or raise specific exception
            assert isinstance(result, list)
        except SelectolaxError:
            # Specific parsing errors are acceptable
            pass


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_null_pointer_safety(parser):
    """Test that NULL pointer checks prevent crashes."""
    # Test edge cases that might result in NULL pointers
    edge_cases = [
        "",  # Empty HTML
        "<>",  # Empty tag
        "<!>",  # Empty declaration
        "<html></html>",  # Minimal valid HTML
    ]
    properties_to_test = ["root", "head", "body", "html"]
    for html_content in edge_cases:
        html_parser = parser(html_content)

        for prop_name in properties_to_test:
            getattr(html_parser, prop_name)


def test_decompose_root_node():
    html_parser = LexborHTMLParser("<div><p>test</p></div>")
    with pytest.raises(SelectolaxError):
        html_parser.root.decompose()


def test_empty_attribute_lexbor():
    div = create_tag("div")
    div.attrs["hidden"] = None
    assert div.html == "<div hidden></div>"


def test_pseudo_class_contains():
    html = "<div><p>hello world</p><p id='main'>AwesOme t3xt</p></div>"
    parser = LexborHTMLParser(html)
    results = parser.css('p:lexbor-contains("awesome" i)')
    assert len(results) == 1
    assert results[0].text() == "AwesOme t3xt"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_css_matches_returns_bool(parser):
    res = parser("<div>test</div>").css_matches("div")
    assert isinstance(res, bool)
    assert res is True
