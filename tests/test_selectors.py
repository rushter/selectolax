import pytest

from selectolax.lexbor import (
    LexborHTMLParser,
    SelectolaxError,
)

_LENGTH_FILTER_STATES_HTML = (
    "<div>"
    "<a href=''>empty value</a>"
    "<a href>valueless</a>"
    "<a>absent</a>"
    "<a href='long-value'>long</a>"
    "</div>"
)


def test_unicode_selector_works():
    html = '<span data-original-title="Pneu renforcé"></span>'
    tree = LexborHTMLParser(html)
    node = tree.css_first('span[data-original-title="Pneu renforcé"]')
    assert node.tag == "span"


def test_selector_text_contains():
    html = """
    <div>
        <p>Hello world</p>
        <p>Goodbye world</p>
        <span>No match here</span>
    </div>
    """
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    selector = root.select("p").text_contains("Hello")
    assert len(selector.matches) == 1
    assert selector.matches[0].text() == "Hello world"
    assert selector.any_matches is True


def test_selector_any_text_contains():
    html = """
    <div>
        <p>Hello world</p>
        <p>Goodbye world</p>
        <span>No match here</span>
    </div>
    """
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    assert root.select("p").any_text_contains("Hello") is True
    assert root.select("p").any_text_contains("world") is True
    assert root.select("p").any_text_contains("nomatch") is False


def test_selector_attribute_longer_than():
    html = """
    <div>
        <a href="short">Link 1</a>
        <a href="http://very-long-url.com/path">Link 2</a>
        <a href="medium">Link 3</a>
    </div>
    """
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    selector = root.select("a").attribute_longer_than("href", 10)
    assert len(selector.matches) == 1
    href = selector.matches[0].attributes["href"]
    assert href is not None
    assert "very-long-url" in href


def test_selector_any_attribute_longer_than():
    html = """
    <div>
        <a href="short">Link 1</a>
        <a href="http://very-long-url.com/path">Link 2</a>
        <a href="medium">Link 3</a>
    </div>
    """
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    assert root.select("a").any_attribute_longer_than("href", 10) is True
    assert root.select("a").any_attribute_longer_than("href", 50) is False


def test_selector_attribute_longer_than_with_start():
    html = """
    <div>
        <a href="http://short.com">Link 1</a>
        <a href="http://very-long-domain-name.com/path">Link 2</a>
        <a href="http://medium.com">Link 3</a>
    </div>
    """
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    selector = root.select("a").attribute_longer_than("href", 15, "http://")
    assert len(selector.matches) == 1
    href = selector.matches[0].attributes["href"]
    assert href is not None
    assert "very-long-domain-name" in href


def test_selector_chaining():
    html = """
    <div>
        <p class="important">Hello world</p>
        <p class="normal">Goodbye world</p>
        <p class="important">Important stuff</p>
        <span class="important">Not a paragraph</span>
    </div>
    """
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    selector = root.select("p").text_contains("world").attribute_longer_than("class", 6)
    assert len(selector.matches) == 1
    assert selector.matches[0].text() == "Hello world"
    assert selector.matches[0].attributes["class"] == "important"


def test_selector_empty_matches():
    html = "<div><p>Hello</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    selector = root.select("div").text_contains("nomatch")
    assert len(selector.matches) == 0
    assert selector.any_matches is False
    assert bool(selector) is False


def test_parser_select_method_returns_lexbor_selector():
    html = "<div><p>First</p><p>Second</p><p>Third</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None

    selector = root.select("p")
    assert hasattr(selector, "matches")
    assert hasattr(selector, "any_matches")
    assert hasattr(selector, "text_contains")
    assert len(selector.matches) == 3

    filtered = selector.text_contains("Second")
    assert len(filtered.matches) == 1
    assert filtered.matches[0].text() == "Second"


def test_parser_select_with_no_matches():
    html = "<div><p>Content</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None

    selector = root.select("span")
    assert len(selector.matches) == 0
    assert selector.any_matches is False
    assert bool(selector) is False


def test_parser_select_with_query():
    html = "<div><p class='important'>Important</p><p>Normal</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None

    selector = root.select("p.important")
    assert len(selector.matches) == 1
    assert selector.matches[0].text() == "Important"


def test_css_selector_invalid_syntax():
    html = "<div><p>Test</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None

    with pytest.raises(SelectolaxError):
        root.css("[invalid&]")


def test_selector_attribute_longer_than_edge_cases():
    html = "<div><a href='short'>Link1</a><a>Link2</a><a href=''>Link3</a></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None

    selector = root.select("a")
    result = selector.attribute_longer_than("href", 0)
    assert len(result.matches) == 1


def test_attribute_longer_than_agrees_with_any_variant():
    """Regression test: the two filters disagreed on empty attribute values."""
    root = LexborHTMLParser(_LENGTH_FILTER_STATES_HTML).root
    assert root is not None

    kept = root.select("a").attribute_longer_than("href", -1).matches
    assert [node.text() for node in kept] == ["empty value", "long"]

    for length in (-1, 0, 4, 11, 200):
        matches = root.select("a").attribute_longer_than("href", length).matches
        assert bool(matches) is (
            root.select("a").any_attribute_longer_than("href", length)
        ), f"the two filters disagree at length={length}"


def test_attribute_longer_than_agrees_with_any_variant_with_start():
    """Regression test: the same asymmetry was reachable through ``start``."""
    html = (
        "<div>"
        "<a href='http://'>empty tail</a>"
        "<a href='http://long-tail-here'>long tail</a>"
        "<a href=''>empty value</a>"
        "<a>absent</a>"
        "</div>"
    )
    root = LexborHTMLParser(html).root
    assert root is not None

    kept = root.select("a").attribute_longer_than("href", -1, "http://").matches
    assert [node.text() for node in kept] == [
        "empty tail",
        "long tail",
        "empty value",
    ]

    for length in (-1, 0, 5, 100):
        matches = root.select("a").attribute_longer_than("href", length, "http://")
        assert bool(matches.matches) is (
            root.select("a").any_attribute_longer_than("href", length, "http://")
        ), f"the two filters disagree at length={length}, start='http://'"


def test_selector():
    html = "<span></span><div><p id='p3'>text</p></div><p></p>"
    selector = "p#p3"

    for node in LexborHTMLParser(html).css(selector):
        assert node.text() == "text"
        assert node.tag == "p"
        assert node.parent.tag == "div"
        assert node.parent.next.tag == "p"
        assert node.parent.prev.tag == "span"
        assert node.parent.last_child.attributes["id"] == "p3"


def test_css_multiple_matches():
    html = "<div></div><div></div><div></div>"
    assert len(LexborHTMLParser(html).css("div")) == 3


def test_css_matches():
    html = "<div></div><div></div><div></div>"
    assert LexborHTMLParser(html).css_matches("div")


def test_any_css_matches():
    html = "<div></div><span></span><div></div>"
    assert LexborHTMLParser(html).any_css_matches(("h1", "span"))


def test_css_one():
    html = "<span></span><div><p class='p3'>text</p><p class='p3'>sd</p></div><p></p>"

    selector = ".s3"
    assert LexborHTMLParser(html).css_first(selector) is None

    selector = "p.p3"
    assert LexborHTMLParser(html).css_first(selector).text() == "text"

    with pytest.raises(ValueError):
        LexborHTMLParser(html).css_first(selector, strict=True)


def test_css_first_default():
    html = "<span></span><div><p class='p3'>text</p><p class='p3'>sd</p></div><p></p>"
    selector = ".s3"
    assert (
        LexborHTMLParser(html).css_first(selector, default="lorem ipsum")
        == "lorem ipsum"
    )


def test_adavanced_selector():
    html_parser = LexborHTMLParser("""
    <script>
     var super_value = 100;
    </script>
    """)
    selector = html_parser.select("script").text_contains("super_value")
    assert selector.any_matches


def test_css_first_first():
    html = '<h2 class="list-details__item__partial" id="js-partial">(1:1, 0:0, 0:0, 5:3)</h2>'
    selector = "h2.list-details__item__partial"
    find_first = LexborHTMLParser(html).css_first(selector)
    assert find_first.css_first(selector) is not None


def test_any_css_matches_fails():
    html = """<h1>Test</h1>"""
    tree = LexborHTMLParser(html)
    with pytest.raises(SelectolaxError):
        tree.any_css_matches(("##",))


def test_any_attribute_longer_than_missing_attribute():
    html = """
    <div>
        <a href="http://very-long-url.example.com/path/to/page">with href</a>
        <a>no href at all</a>
        <a href="short">short href</a>
    </div>
    """
    tree = LexborHTMLParser(html)
    # Must not raise TypeError despite the middle <a> having no href
    assert tree.root.select("a").any_attribute_longer_than("href", 10) is True
    assert tree.root.select("a").any_attribute_longer_than("href", 200) is False


def test_any_attribute_longer_than_all_missing():
    html = "<div><a>one</a><a>two</a></div>"
    tree = LexborHTMLParser(html)
    assert tree.root.select("a").any_attribute_longer_than("href", 0) is False


def test_root_css():
    tree = LexborHTMLParser("test")
    assert len(tree.root.css("data")) == 0


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
