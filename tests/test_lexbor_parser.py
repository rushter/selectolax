import threading
from difflib import SequenceMatcher

import pytest

from selectolax.lexbor import LexborHTMLParser, LexborNode, SelectolaxError, create_tag

"""
We'are testing only our own code.
Many functionality are already tested in the Lexbor engine, so there is no reason to test every case.
"""


def test_parser():
    html = LexborHTMLParser("")
    assert isinstance(html, LexborHTMLParser)

    with pytest.raises(TypeError):
        LexborHTMLParser(123)

    with pytest.raises(TypeError):
        LexborHTMLParser("asd").css(123)


def test_malformed_data():
    malformed_inputs = [
        b"\x00\x01\x02\x03",
        "<div><p><span></div>",
        "<" + "a" * 1000 + ">",
    ]

    for malformed_html in malformed_inputs:
        try:
            html_parser = LexborHTMLParser(malformed_html)
            # Should not crash, but may return None or empty results
            result = html_parser.html
            assert result is None or isinstance(result, str)
        except (ValueError, RuntimeError, UnicodeDecodeError):
            # These exceptions are acceptable for malformed input
            pass


def test_properties():
    html_parser = LexborHTMLParser("<div><p>test</p></div>")

    properties_to_test = ["root", "head", "body", "html"]

    for prop_name in properties_to_test:
        getattr(html_parser, prop_name)


def test_unicode_handling():
    unicode_content = [
        "Hello 世界",
        "🚀🌟💫",
        "Café résumé naïve",
    ]

    for content in unicode_content:
        html = f"<div>{content}</div>"
        try:
            html_parser = LexborHTMLParser(html)
            result = html_parser.css_first("div")
            if result:
                extracted_text = result.text()
                assert content in extracted_text
        except UnicodeEncodeError:
            # Some encoding issues might be expected
            pass


def test_tag_name_validation():
    """Test that tag name validation works correctly."""
    html_parser = LexborHTMLParser("<div></div>")

    # Empty tag name should be rejected
    with pytest.raises(ValueError, match="Tag name cannot be empty"):
        html_parser.tags("")

    # Very long tag names should be rejected
    long_tag_name = "a" * 101  # Exceeds 100 character limit
    with pytest.raises(ValueError, match="Tag name is too long"):
        html_parser.tags(long_tag_name)


def test_nodes():
    html = (
        '<div><p id="p1"></p><p id="p2"></p><p id="p3"><a>link</a></p>'
        '<p id="p4"></p><p id="p5">text</p><p id="p6"></p></div>'
    )
    htmlp = LexborHTMLParser(html)

    assert isinstance(htmlp.root, LexborNode)
    assert isinstance(htmlp.body, LexborNode)
    html_output = htmlp.html
    assert len(html_output) >= len(html)
    assert SequenceMatcher(None, html, html_output).ratio() > 0.8


def test_root_css():
    tree = LexborHTMLParser("test")
    assert len(tree.root.css("data")) == 0


def test_strip_tags_from_root():
    html = "<body><div></div><script></script></body>"
    html_parser = LexborHTMLParser(html)
    html_parser.root.strip_tags(["div", "script"])
    assert html_parser.html == "<html><head></head><body></body></html>"

    with pytest.raises(TypeError):
        html_parser.strip_tags(1)


def test_clone():
    html_parser = LexborHTMLParser("""<h1>Welcome</h1>""")
    clone = html_parser.clone()
    html_parser.root.css_first("h1").decompose()
    del html_parser
    assert clone.html == "<html><head></head><body><h1>Welcome</h1></body></html>"


def test_tags():
    html_parser = LexborHTMLParser("""
    <div><span><span></span></span></div>
    <div><span></span></div>
    <div><div></div></div>
    <span></span>
    <div></div>
    """)
    assert len(html_parser.tags("div")) == 5


def test_preserves_doctype():
    html_parser = LexborHTMLParser("""
    <!DOCTYPE html>
    <html>
        <head><title>Test</title></head>
        <body><p>Hello World</p></body>
    </html>
    """)
    assert "<!DOCTYPE html>" in html_parser.html


def test_invalid_input_types():
    with pytest.raises(TypeError, match="Expected a string"):
        LexborHTMLParser(123)

    with pytest.raises(TypeError, match="Expected a string"):
        LexborHTMLParser([])

    with pytest.raises(TypeError, match="Expected a string"):
        LexborHTMLParser(None)


def test_clone_handling():
    html_parser = LexborHTMLParser("<div>test</div>")

    cloned = html_parser.clone()
    assert cloned.html is not None

    assert html_parser.html is not None


def test_concurrent_parsing():
    """Test that concurrent parsing doesn't cause race conditions."""
    results = []
    errors = []
    lock = threading.Lock()

    def parse_html(content):
        try:
            html_parser = LexborHTMLParser(content)
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


def test_null_pointer_safety():
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
        html_parser = LexborHTMLParser(html_content)

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


def test_css_matches_returns_bool():
    res = LexborHTMLParser("<div>test</div>").css_matches("div")
    assert isinstance(res, bool)
    assert res is True
