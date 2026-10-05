import pytest

from selectolax.lexbor import (
    LexborAttributes,
    LexborHTMLParser,
    create_tag,
)

_SHARED_LOCAL_NAME = [
    ('<svg><use href="/plain" xlink:href="/xlinked"></use></svg>', "use"),
    ('<svg><use xlink:href="/xlinked" href="/plain"></use></svg>', "use"),
    ('<math><mi xlink:href="/xlinked" href="/plain"></mi></math>', "mi"),
    ('<div xlink:href="/xlinked" href="/plain"></div>', "div"),
]


def test_attrs_reject_non_element_nodes():
    parser = LexborHTMLParser("<div>hello<!--comment--></div>")
    div = parser.css_first("div")
    text_node = div.first_child
    comment_node = div.last_child

    assert text_node is not None
    assert comment_node is not None
    assert text_node.is_text_node
    assert comment_node.is_comment_node

    with pytest.raises(TypeError, match="element nodes"):
        _ = text_node.attrs

    with pytest.raises(TypeError, match="element nodes"):
        _ = comment_node.attrs


def test_attributes_sget():
    html = '<div id="test" class="foo" empty></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None
    attrs = div.attrs
    assert attrs.sget("id") == "test"
    assert attrs.sget("class") == "foo"
    assert attrs.sget("empty") == ""  # Empty attributes return empty string
    assert attrs.sget("missing", "default") == "default"


def test_attributes_keys_values_items():
    html = '<div id="test" class="foo" data-value="123"></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None
    attrs = div.attrs

    keys = list(attrs.keys())
    assert "id" in keys
    assert "class" in keys
    assert "data-value" in keys

    values = list(attrs.values())
    assert "test" in values
    assert "foo" in values
    assert "123" in values

    items = dict(attrs.items())
    assert items["id"] == "test"
    assert items["class"] == "foo"
    assert items["data-value"] == "123"


def test_attributes_len_and_contains():
    html = '<div id="test" class="foo"></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None
    attrs = div.attrs

    assert len(attrs) == 2
    assert "id" in attrs
    assert "class" in attrs
    assert "missing" not in attrs


def test_attributes_get():
    html = '<div id="test" empty></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None
    attrs = div.attrs

    assert attrs.get("id") == "test"
    assert attrs.get("empty") is None  # Empty attributes return None
    assert attrs.get("missing") is None
    assert attrs.get("missing", "default") == "default"


def test_attributes_modification():
    html = '<div id="original"></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None
    attrs = div.attrs

    # new attribute
    attrs["new_attr"] = "new_value"
    assert attrs["new_attr"] == "new_value"

    # existing attribute
    attrs["id"] = "modified"
    assert attrs["id"] == "modified"

    # empty attribute
    attrs["empty"] = None
    assert attrs["empty"] is None

    # deleting attribute
    del attrs["id"]
    assert "id" not in attrs

    try:
        del attrs["nonexistent"]
        assert False, "Should have raised KeyError"
    except KeyError:
        pass


def test_attrs_setitem_rejects_non_str_values():
    parser = LexborHTMLParser('<div id="a"></div>')
    div = parser.root.css_first("div")
    attrs = div.attrs

    for value in (5, 0, 1.5, b"bytes", b"", [1], (), {"a": 1}, True, object()):
        with pytest.raises(TypeError, match="Expected str or unicode"):
            attrs["x"] = value

    assert "x" not in attrs
    assert div.html == '<div id="a"></div>'

    attrs["x"] = "value"
    assert attrs["x"] == "value"
    attrs["x"] = ""
    assert attrs["x"] == ""
    attrs["x"] = "ünïcödé 中文"
    assert attrs["x"] == "ünïcödé 中文"
    attrs["x"] = None
    assert attrs["x"] is None
    assert div.html == '<div id="a" x=""></div>'


def test_attrs_setitem_rejects_non_str_keys():
    parser = LexborHTMLParser('<div id="a"></div>')
    attrs = parser.root.css_first("div").attrs

    with pytest.raises(TypeError, match="expected str"):
        attrs[b"id"] = "b"
    assert attrs["id"] == "a"


def test_fragment_attrs():
    html = "<div id='test' class='foo bar' data-value='123'></div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    div = parser.root
    assert div.attributes == {"id": "test", "class": "foo bar", "data-value": "123"}
    assert div.attrs["id"] == "test"
    div.attrs["new"] = "value"
    assert div.attributes == {
        "id": "test",
        "class": "foo bar",
        "data-value": "123",
        "new": "value",
    }


def test_attributes_access_on_non_element():
    html = "<!-- comment --><div>text</div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    root = parser.root
    assert root is not None

    comment_node = root
    assert comment_node.is_comment_node

    attrs = comment_node.attributes
    assert isinstance(attrs, dict)
    assert len(attrs) == 0

    text_node = root.css_first("div").first_child
    assert text_node is not None
    assert text_node.is_text_node

    text_attrs = text_node.attributes
    assert isinstance(text_attrs, dict)
    assert len(text_attrs) == 0


def test_attributes():
    html = "<div><p id='p3'>text</p></div>"
    selector = "p#p3"
    for node in LexborHTMLParser(html).css(selector):
        assert "id" in node.attributes
        assert node.attributes["id"] == "p3"

    html = "<div><p attr>text</p></div>"
    selector = "p"
    nodes = LexborHTMLParser(html).css(selector)
    assert len(nodes) == 1
    for node in nodes:
        assert "attr" in node.attributes
        assert node.attributes["attr"] is None


def test_malformed_attributes():
    html = '<div> <meta name="description" content="ÐÐ°Ñ"Ð " /></div>'
    html_parser = LexborHTMLParser(html)

    for tag in html_parser.tags("meta"):
        assert tag


def test_attrs_adds_attribute():
    html_parser = LexborHTMLParser('<div id="id"></div>')
    node = html_parser.css_first("div")
    node.attrs["new_att"] = "new"
    assert node.attributes == {"id": "id", "new_att": "new"}


def test_attrs_sets_attribute():
    html_parser = LexborHTMLParser('<div id="id"></div>')
    node = html_parser.css_first("div")
    node.attrs["id"] = "new_id"
    assert node.attributes == {"id": "new_id"}


def test_attrs_removes_attribute():
    html_parser = LexborHTMLParser('<div id="id"></div>')
    node = html_parser.css_first("div")
    del node.attrs["id"]
    assert node.attributes == {}


def test_attrs_test_dict_features():
    html_parser = LexborHTMLParser('<div id="id" v data-id="foo"></div>')
    node = html_parser.css_first("div")
    node.attrs["new_att"] = "new"
    assert list(node.attrs.keys()) == ["id", "v", "data-id", "new_att"]
    assert list(node.attrs.values()) == ["id", None, "foo", "new"]
    assert len(node.attrs) == 4
    assert node.attrs.get("unknown_field", "default_value") == "default_value"
    assert "id" in node.attrs
    assert "vid" not in node.attrs


def test_attrs_keep_document_alive():
    # LexborAttributes holds a borrowed pointer into the owning document, so it
    # has to keep the parser alive by itself. Here the parser is a temporary and
    # is freed by reference counting as soon as `.attrs` is evaluated.
    attrs = (
        LexborHTMLParser('<div id="id" data-x="1">text</div>').css_first("div").attrs
    )

    assert list(attrs) == ["id", "data-x"]
    assert attrs["id"] == "id"
    assert attrs["data-x"] == "1"


def test_attributes_keeps_both_names_of_a_shared_local_name():
    for html, selector in _SHARED_LOCAL_NAME:
        node = LexborHTMLParser(html).css_first(selector)
        assert node.attributes == {"href": "/plain", "xlink:href": "/xlinked"}, html


def test_attrs_iteration_yields_each_attribute_once():
    for html, selector in _SHARED_LOCAL_NAME:
        node = LexborHTMLParser(html).css_first(selector)
        assert sorted(node.attrs) == ["href", "xlink:href"], html
        assert len(node.attrs) == 2, html


def test_attrs_keys_round_trip_through_lookup():
    # Whatever iteration yields has to address the attribute it names, whichever
    # order the two attributes appear in. lxb_dom_element_attr_by_name() accepts
    # a match on either the local or the qualified name, so it could answer a
    # lookup of "href" with the value of "xlink:href".
    for html, selector in _SHARED_LOCAL_NAME:
        node = LexborHTMLParser(html).css_first(selector)
        attributes = node.attributes

        for key in node.attrs:
            assert key in node.attrs, (html, key)
            assert node.attrs[key] == attributes[key], (html, key)

        assert dict(node.attrs.items()) == attributes, html


def test_attrs_items_and_values_agree_with_lookup():
    # items() and values() read each value off the attribute it belongs to instead
    # of resolving every name again, so they still have to answer as __getitem__
    # does: valueless is None, empty is an empty string.
    node = LexborHTMLParser('<div id="a" bare empty=""></div>').css_first("div")

    assert list(node.attrs.items()) == [("id", "a"), ("bare", None), ("empty", "")]
    assert list(node.attrs.values()) == ["a", None, ""]
    assert dict(node.attrs.items()) == node.attributes


def test_attrs_removes_the_attribute_it_looked_up():
    # __delitem__ used to re-resolve the name through lexbor, which could drop
    # the attribute sharing a local name instead of the requested one.
    for html, selector in _SHARED_LOCAL_NAME:
        node = LexborHTMLParser(html).css_first(selector)
        del node.attrs["href"]

        assert node.attributes == {"xlink:href": "/xlinked"}, html
        assert "href" not in node.attrs, html


def test_attrs_prefixed_name_is_not_reachable_by_its_local_name():
    # Only `xlink:href` is set, so there is no `href` attribute to find. As with
    # Element.getAttribute() in the DOM standard, a lookup matches the qualified
    # name and must not fall back to the local name.
    node = LexborHTMLParser('<div xlink:href="/xlinked"></div>').css_first("div")

    assert node.attributes == {"xlink:href": "/xlinked"}
    assert node.attrs.get("xlink:href") == "/xlinked"
    assert node.attrs.get("href") is None
    assert "href" not in node.attrs
    with pytest.raises(KeyError):
        del node.attrs["href"]


def test_attrs_lookup_stays_case_insensitive():
    node = LexborHTMLParser('<div DATA-X="1" data-y="2"></div>').css_first("div")

    assert node.attributes == {"data-x": "1", "data-y": "2"}
    assert node.attrs["DATA-X"] == "1"
    assert node.attrs["Data-X"] == "1"
    assert "DATA-X" in node.attrs


def test_attrs_del_removes_missing_attribute():
    node = LexborHTMLParser('<div id="id"></div>').css_first("div")

    del node.attrs["id"]
    with pytest.raises(KeyError):
        del node.attrs["id"]
    with pytest.raises(KeyError):
        del node.attrs["unknown"]


def test_attrs_del_of_id_and_class_updates_the_tree():
    # lxb_dom_element_attr_remove() clears the element's cached id/class
    # pointers, so a removed id or class must stop matching selectors.
    html_parser = LexborHTMLParser('<div id="id" class="cls"></div>')
    node = html_parser.css_first("div")

    del node.attrs["id"]
    assert html_parser.css("#id") == []
    assert len(html_parser.css(".cls")) == 1

    del node.attrs["class"]
    assert html_parser.css(".cls") == []
    assert html_parser.css_first("div").attributes == {}


def test_attributes_is_not_publicly_constructible():
    with pytest.raises(TypeError, match="cannot be instantiated directly"):
        LexborAttributes()

    node = LexborHTMLParser("<div id='x' class='y'></div>").css_first("div")
    assert list(node.attrs) == ["id", "class"]


def test_empty_attribute_lexbor():
    div = create_tag("div")
    div.attrs["hidden"] = None
    assert div.html == '<div hidden=""></div>'
