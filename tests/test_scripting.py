from selectolax.lexbor import LexborHTMLParser

HEAD_NOSCRIPT_HTML = (
    "<html><head>"
    '<noscript><img src="pixel.gif"></noscript>'
    '<link rel="canonical" href="/a">'
    '<meta name="description" content="d">'
    "</head><body><p>x</p></body></html>"
)


def test_scripting_is_off_by_default():
    parser = LexborHTMLParser(HEAD_NOSCRIPT_HTML)
    assert parser.css_first("head link") is None
    assert parser.css_first("body link") is not None
    assert parser.css_first("body meta") is not None


def test_scripting_keeps_head_elements_after_a_head_noscript_in_head():
    parser = LexborHTMLParser(HEAD_NOSCRIPT_HTML, scripting=True)
    assert parser.css_first("head link").attributes["href"] == "/a"
    assert parser.css_first("head meta").attributes["content"] == "d"
    assert parser.css_first("head noscript") is not None
    assert parser.css_first("body img") is None


def test_scripting_makes_noscript_content_one_text_node():
    parser = LexborHTMLParser(HEAD_NOSCRIPT_HTML, scripting=True)
    children = list(parser.css_first("noscript").iter(include_text=True))
    assert len(children) == 1
    assert children[0].is_text_node
    assert children[0].text_content == '<img src="pixel.gif">'


def test_noscript_in_body_holds_markup_without_scripting():
    html = "<body><noscript><p>no js</p></noscript></body>"
    assert LexborHTMLParser(html).css_first("noscript p") is not None
    assert LexborHTMLParser(html, scripting=True).css_first("noscript p") is None


def test_scripting_round_trips_noscript_content():
    parser = LexborHTMLParser(HEAD_NOSCRIPT_HTML, scripting=True)
    assert '<noscript><img src="pixel.gif"></noscript>' in parser.html


def test_scripting_applies_to_html_parsed_into_the_document_later():
    parser = LexborHTMLParser("<div></div>", scripting=True)
    parser.css_first("div").inner_html = "<noscript><p>no js</p></noscript>"
    assert parser.css_first("noscript p") is None


def test_scripting_applies_to_fragments():
    html = "<noscript><p>no js</p></noscript>"
    assert LexborHTMLParser(html, is_fragment=True).css_first("noscript p") is not None
    fragment = LexborHTMLParser(html, is_fragment=True, scripting=True)
    assert fragment.css_first("noscript p") is None


def test_clone_keeps_scripting():
    parser = LexborHTMLParser(HEAD_NOSCRIPT_HTML, scripting=True)
    cloned = parser.clone()
    assert cloned.html == parser.html
    cloned.css_first("p").inner_html = "<noscript><b>no js</b></noscript>"
    assert cloned.css_first("noscript b") is None
