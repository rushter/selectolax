from selectolax.lexbor import (
    LexborDocumentOptions,
    LexborHTMLParser,
)

SELECTED_CONTENT_HTML = (
    "<select><button><selectedcontent></selectedcontent></button>"
    "<option>a</option><option selected>b</option></select>"
)


def test_document_options_enum_values():
    assert LexborDocumentOptions.UNDEF == 0
    assert LexborDocumentOptions.WO_EVENTS == 1


def test_document_options_default_enables_events():
    parser = LexborHTMLParser(SELECTED_CONTENT_HTML)
    selectedcontent = parser.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent>b</selectedcontent>"


def test_document_options_wo_events_disables_events():
    parser = LexborHTMLParser(
        SELECTED_CONTENT_HTML, options=LexborDocumentOptions.WO_EVENTS
    )
    selectedcontent = parser.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"


def test_document_options_accepts_plain_int():
    parser = LexborHTMLParser(
        SELECTED_CONTENT_HTML, options=int(LexborDocumentOptions.WO_EVENTS)
    )
    selectedcontent = parser.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"


def test_document_options_combined_with_bitwise_or():
    options = LexborDocumentOptions.WO_EVENTS | LexborDocumentOptions.UNDEF
    assert options == LexborDocumentOptions.WO_EVENTS
    parser = LexborHTMLParser(SELECTED_CONTENT_HTML, options=options)
    selectedcontent = parser.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"


def test_document_options_combined_as_plain_int():
    options = LexborDocumentOptions.WO_EVENTS.value | LexborDocumentOptions.UNDEF.value
    parser = LexborHTMLParser(SELECTED_CONTENT_HTML, options=options)
    selectedcontent = parser.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"


def test_document_options_fragment_wo_events():
    parser = LexborHTMLParser(
        SELECTED_CONTENT_HTML,
        is_fragment=True,
        options=LexborDocumentOptions.WO_EVENTS,
    )
    selectedcontent = parser.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"


def test_document_options_property_reflects_constructor_argument():
    parser = LexborHTMLParser(SELECTED_CONTENT_HTML)
    assert parser.options == LexborDocumentOptions.UNDEF

    parser = LexborHTMLParser(
        SELECTED_CONTENT_HTML, options=LexborDocumentOptions.WO_EVENTS
    )
    assert parser.options == LexborDocumentOptions.WO_EVENTS


def test_document_options_clone_preserves_options():
    parser = LexborHTMLParser(
        SELECTED_CONTENT_HTML, options=LexborDocumentOptions.WO_EVENTS
    )
    cloned = parser.clone()
    assert cloned.options == LexborDocumentOptions.WO_EVENTS
    selectedcontent = cloned.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"


def test_document_options_clone_preserves_default_options():
    parser = LexborHTMLParser(SELECTED_CONTENT_HTML)
    cloned = parser.clone()
    assert cloned.options == LexborDocumentOptions.UNDEF


def test_document_options_clone_preserves_fragment_options():
    parser = LexborHTMLParser(
        SELECTED_CONTENT_HTML,
        is_fragment=True,
        options=LexborDocumentOptions.WO_EVENTS,
    )
    cloned = parser.clone()
    assert cloned.options == LexborDocumentOptions.WO_EVENTS
    selectedcontent = cloned.css_first("selectedcontent")
    assert selectedcontent.html == "<selectedcontent></selectedcontent>"
