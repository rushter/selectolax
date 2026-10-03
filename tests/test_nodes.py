import pytest

from selectolax.lexbor import (
    LexborAttributes,
    LexborHTMLParser,
    LexborNode,
    SelectolaxError,
)

"""
We'are testing only our own code.
Many functionality are already tested in the Lexbor engine, so there is no reason to test every case.
"""

_PARSERS = (LexborHTMLParser,)

_PARSERS_PARAMETRIZER = (
    "parser",
    _PARSERS,
)

_NODE_ID_CASES = [
    ("<div id='my_node'></div>", "my_node", LexborHTMLParser),
    ("<div></div>", None, LexborHTMLParser),
]


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_selector(parser):
    html = "<span></span><div><p id='p3'>text</p></div><p></p>"
    selector = "p#p3"

    for node in parser(html).css(selector):
        assert node.text() == "text"
        assert node.tag == "p"
        assert node.parent.tag == "div"
        assert node.parent.next.tag == "p"
        assert node.parent.prev.tag == "span"
        assert node.parent.last_child.attributes["id"] == "p3"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_css_multiple_matches(parser):
    html = "<div></div><div></div><div></div>"
    assert len(parser(html).css("div")) == 3


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_css_matches(parser):
    html = "<div></div><div></div><div></div>"
    assert parser(html).css_matches("div")


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_any_css_matches(parser):
    html = "<div></div><span></span><div></div>"
    assert parser(html).any_css_matches(("h1", "span"))


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_css_one(parser):
    html = "<span></span><div><p class='p3'>text</p><p class='p3'>sd</p></div><p></p>"

    selector = ".s3"
    assert parser(html).css_first(selector) is None

    selector = "p.p3"
    assert parser(html).css_first(selector).text() == "text"

    with pytest.raises(ValueError):
        parser(html).css_first(selector, strict=True)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_text_when_html_is_empty(parser):
    html_parser = parser("")

    assert html_parser.text() == ""


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_css_first_default(parser):
    html = "<span></span><div><p class='p3'>text</p><p class='p3'>sd</p></div><p></p>"
    selector = ".s3"
    assert parser(html).css_first(selector, default="lorem ipsum") == "lorem ipsum"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_id_property(parser):
    html = "<p id='main_text'>text</p>"
    assert parser(html).css_first("p").id == "main_text"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_tag_property(parser):
    html = "<h1>text</h1>"
    assert parser(html).css_first("h1").tag == "h1"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attributes(parser):
    html = "<div><p id='p3'>text</p></div>"
    selector = "p#p3"
    for node in parser(html).css(selector):
        assert "id" in node.attributes
        assert node.attributes["id"] == "p3"

    html = "<div><p attr>text</p></div>"
    selector = "p#p3"
    for node in parser(html).css(selector):
        assert "attr" in node.attributes
        assert node.attributes["attr"] is None


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_decompose(parser):
    html = "<body><div><p id='p3'>text</p></div></body>"
    html_parser = parser(html)

    for node in html_parser.tags("p"):
        node.decompose()
    assert html_parser.body.child.html == "<div></div>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_html_property(parser):
    html = "<body>Hi there</body>"
    html_parser = parser(html)
    assert html_parser.body.child.html == "Hi there"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_root_property(parser):
    html = "<body>Hi there</body>"
    html_parser = parser(html)
    assert html_parser.root.html == "<html><head></head><body>Hi there</body></html>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_head_property(parser):
    html = """
    <html lang="en">
        <head><title>rushter.com</title></head>
        <body></body>
    </html>
    """
    html_parser = parser(html)
    assert html_parser.head.html == "<head><title>rushter.com</title></head>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_body_property(parser):
    html = "<body>Hi there</body>"
    html_parser = parser(html)
    assert html_parser.body.html == "<body>Hi there</body>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_strip_tags(parser):
    html = "<body><div></div><script></script></body>"
    html_parser = parser(html)
    html_parser.root.strip_tags(["div", "script"])
    assert html_parser.html == "<html><head></head><body></body></html>"

    with pytest.raises(TypeError):
        html_parser.strip_tags(1)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_malformed_attributes(parser):
    html = '<div> <meta name="description" content="ÐÐ°Ñ"Ð " /></div>'
    html_parser = parser(html)

    for tag in html_parser.tags("meta"):
        assert tag


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_iter_with_text(parser):
    html = """
    <div id="description">
        <h1>Title</h1>
        text
        <div>foo</div>
        <img scr="image.jpg">
    </div>
    """
    html_parser = parser(html)
    expected_tags = ["-text", "h1", "-text", "div", "-text", "img", "-text"]
    actual_tags = [
        node.tag
        for node in html_parser.css_first("#description").iter(include_text=True)
    ]
    assert expected_tags == actual_tags


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_text_deep_gh61(parser):
    html = """<div>this is a test <h1>Heading</h1></div>"""
    output = []
    tree = parser(html)
    for node in tree.root.traverse(include_text=True):
        if node.tag == "-text":
            text = node.text(deep=True)
            if text:
                output.append(text)
    assert output == ["this is a test ", "Heading"]


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_iter_no_text(parser):
    html = """
    <div id="description">
        <h1>Title</h1>
        text
        <div>foo</div>
        <img scr="image.jpg">
    </div>
    """
    html_parser = parser(html)
    expected_tags = ["h1", "div", "img"]
    actual_tags = [
        node.tag
        for node in html_parser.css_first("#description").iter(include_text=False)
    ]
    assert expected_tags == actual_tags


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
@pytest.mark.parametrize("remover", ["decompose", "remove", "unwrap"])
def test_iter_visits_every_child_when_removed_mid_iteration(parser, remover):
    """Removing the yielded node must not end the iteration early.

    ``lxb_dom_node_remove`` clears the ``next`` pointer of the node it unlinks,
    so reading ``node.next`` after resuming from the ``yield`` used to truncate
    the walk to the first child and silently skip the rest.
    """
    tree = parser("<div><p>1</p><p>2</p><p>3</p><p>4</p></div>")
    div = tree.css_first("div")

    seen = []
    for node in div.iter():
        seen.append(node.text())
        getattr(node, remover)()

    assert seen == ["1", "2", "3", "4"]
    assert tree.css("p") == []


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_iter_reports_all_children_when_some_are_removed_mid_iteration(parser):
    """Skipping nodes must not disturb the traversal of their siblings."""
    tree = parser("<div><p>1</p><p>2</p><p>3</p><p>4</p></div>")
    div = tree.css_first("div")

    seen = []
    for node in div.iter():
        seen.append(node.text())
        if node.text() in ("1", "3"):
            node.decompose()

    assert seen == ["1", "2", "3", "4"]
    assert [node.text() for node in tree.css("p")] == ["2", "4"]


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_navigation(parser):
    html = (
        '<div id="parent"><div id="prev"></div><div id="test_node"><h1 id="child">Title</h1>'
        '<div>foo</div><img scr="image.jpg"></div><div id="next"></div></div>'
    )
    html_parser = parser(html)
    main_node = html_parser.css_first("#test_node")
    assert main_node.prev.id == "prev"
    assert main_node.next.id == "next"
    assert main_node.parent.id == "parent"
    assert main_node.child.id == "child"


@pytest.mark.parametrize(
    "html,expected, parser",
    _NODE_ID_CASES,
)
def test_get_node_id(html, expected, parser):
    html_parser = parser(html)
    node = html_parser.css_first("div")
    assert node.id == expected


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_html_attribute_works_for_text(parser):
    html = "<div>foo bar</div>"
    html_parser = parser(html)
    node = html_parser.css_first("div").child
    assert node.html == "foo bar"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_text_node_returns_text(parser):
    html = "<div>foo bar</div>"
    html_parser = parser(html)
    node = html_parser.css_first("div").child
    assert node.text(deep=False) == "foo bar"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_text_node_returns_text_parent(parser):
    html = "<div>foo bar</div>"
    html_parser = parser(html)
    node = html_parser.css_first("div")
    assert node.text(deep=False) == "foo bar"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_unwrap(parser):
    html = '<a id="url" href="https://rushter.com/">I linked to <i>rushter.com</i></a>'
    html_parser = parser(html)
    node = html_parser.css_first("i")
    node.unwrap()
    assert (
        html_parser.body.child.html
        == '<a id="url" href="https://rushter.com/">I linked to rushter.com</a>'
    )


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_unwrap_detaches_node_from_its_children(parser):
    """An unwrapped node must stop referring to the children it just moved.

    ``lxb_dom_node_insert_before()`` re-parents without unlinking from the old
    parent, so without an explicit remove this node's ``first_child`` /
    ``last_child`` kept pointing at children that had already moved up to its
    own parent. Those nodes then belonged to two child lists at once, and
    reading or serializing the unwrapped node walked a cycle and segfaulted.
    """
    html_parser = parser("<html><body><p>1</p><p>2</p></body></html>")
    body = html_parser.body
    body.unwrap()

    assert body.parent is None
    assert body.first_child is None
    assert body.last_child is None
    assert list(body) == []
    assert body.inner_html == ""
    # The live tree is unaffected by the move: the children keep their order and
    # now sit directly under <html>.
    html_node = html_parser.css_first("html")
    assert html_node is not None
    assert [child.tag for child in html_node.iter()] == ["head", "p", "p"]


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_unwrap_preserves_child_order(parser):
    html_parser = parser("<div>a<b>1</b><i>2</i><u>3</u>z</div>")
    html_parser.css_first("div").unwrap()
    assert html_parser.body.inner_html == "a<b>1</b><i>2</i><u>3</u>z"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_unwrap_moved_children_are_not_duplicated(parser):
    html_parser = parser("<div><p><b>1</b></p><p><b>2</b></p></div>")
    html_parser.css_first("div").unwrap()

    assert html_parser.body.inner_html == "<p><b>1</b></p><p><b>2</b></p>"
    assert len(html_parser.css("b")) == 2
    # Every element's inner_html must still match its own children.
    for node in html_parser.css("*"):
        assert node.inner_html == "".join(
            child.html for child in node.iter(include_text=True)
        )


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_unwrap_empty_tag(parser):
    html = '<a id="url" href="https://rushter.com/">I linked to rushter.com<i></i></a>'
    html_parser = parser(html)
    node = html_parser.css_first("i")
    node.unwrap(delete_empty=True)
    assert (
        html_parser.body.child.html
        == '<a id="url" href="https://rushter.com/">I linked to rushter.com</a>'
    )


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_unwrap_tags(parser):
    html_parser = parser("<div><a href=>Hello</a> <i>world</i>!</div>")
    html_parser.body.unwrap_tags(["i", "a"])
    assert html_parser.body.html == "<body><div>Hello world!</div></body>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_unwrap_empty_tags(parser):
    html_parser = parser("<div><a href=>Hello</a> <i>world</i>!<i></i><a></a></div>")
    html_parser.body.unwrap_tags(["i", "a"], delete_empty=True)
    assert html_parser.body.html == "<body><div>Hello world!</div></body>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_unwraps_multiple_child_nodes(parser):
    html = """
    <div id="test">
        foo <span>bar <i>Lor<span>ems</span></i> I <span class='p3'>dummy <div>text</div></span></span>
    </div>
    """
    html_parser = parser(html)
    html_parser.body.unwrap_tags(["span", "i"])
    assert (
        html_parser.body.child.html
        == '<div id="test">\n        foo bar Lorems I dummy <div>text</div>\n    </div>'
    )


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_unwraps_multiple_child_nodes_with_empty(parser):
    html = """
    <div id="test">
        foo <span>bar <i>Lor<span>ems</span></i> I <span class='p3'>dummy<span><i></i></span> <div>text</div></span></span>
    </div>
    """
    html_parser = parser(html)
    html_parser.body.unwrap_tags(["span", "i"], delete_empty=True)
    assert (
        html_parser.body.child.html
        == '<div id="test">\n        foo bar Lorems I dummy <div>text</div>\n    </div>'
    )


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_replace_with(parser):
    html_parser = parser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first("img")
    img.replace_with(img.attributes.get("alt", ""))
    assert html_parser.body.child.html == "<div>Get Laptop</div>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_replace_with_multiple_nodes(parser):
    html_parser = parser(
        '<div>Get <span alt="Laptop"><img src="/jpg"> <div>/div></span></div>'
    )
    img = html_parser.css_first("span")
    img.replace_with(img.attributes.get("alt", ""))
    assert html_parser.body.child.html == "<div>Get Laptop</div>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_replace_with(parser):
    html_parser = parser(
        '<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>'
    )
    html_parser2 = parser("<div>Test</div>")
    img_node = html_parser.css_first("img")
    img_node.replace_with(html_parser2.body.child)
    assert (
        html_parser.body.child.html
        == '<div>Get <span alt="Laptop"><div>Test</div> <div></div></span></div>'
    )


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_replace_with_empty_string(parser):
    html_parser = parser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first("img")
    img.replace_with("")
    assert html_parser.body.child.html == "<div>Get </div>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_replace_with_invalid_value_passed_exception(parser):
    with pytest.raises(TypeError) as excinfo:
        html_parser = parser('<div>Get <img src="" alt="Laptop"></div>')
        img = html_parser.css_first("img")
        img.replace_with(None)
    assert "No matching signature found" in str(excinfo.value)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_insert_before(parser):
    html_parser = parser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first("img")
    img.insert_before(img.attributes.get("alt", ""))
    assert (
        html_parser.body.child.html == '<div>Get Laptop<img src="" alt="Laptop"></div>'
    )


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_insert_before(parser):
    html_parser = parser(
        '<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>'
    )
    html_parser2 = parser("<div>Test</div>")
    img_node = html_parser.css_first("img")
    img_node.insert_before(html_parser2.body.child)
    assert (
        html_parser.body.child.html
        == '<div>Get <span alt="Laptop"><div>Test</div><img src="/jpg"> <div></div></span></div>'
    )


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_insert_after(parser):
    html_parser = parser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first("img")
    img.insert_after(img.attributes.get("alt", ""))
    assert (
        html_parser.body.child.html == '<div>Get <img src="" alt="Laptop">Laptop</div>'
    )


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_insert_after(parser):
    html_parser = parser(
        '<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>'
    )
    html_parser2 = parser("<div>Test</div>")
    img_node = html_parser.css_first("img")
    img_node.insert_after(html_parser2.body.child)
    assert (
        html_parser.body.child.html
        == '<div>Get <span alt="Laptop"><img src="/jpg"><div>Test</div> <div></div></span></div>'
    )


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_insert_child(parser):
    html_parser = parser('<div>Get <img src=""></div>')
    div = html_parser.css_first("div")
    div.insert_child("Laptop")
    assert html_parser.body.child.html == '<div>Get <img src="">Laptop</div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_insert_child(parser):
    html_parser = parser('<div>Get <span alt="Laptop"> <div>Laptop</div> </span></div>')
    html_parser2 = parser("<div>Test</div>")
    span_node = html_parser.css_first("span")
    span_node.insert_child(html_parser2.body.child)
    assert (
        html_parser.body.child.html
        == '<div>Get <span alt="Laptop"> <div>Laptop</div> <div>Test</div></span></div>'
    )


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_adds_attribute(parser):
    html_parser = parser('<div id="id"></div>')
    node = html_parser.css_first("div")
    node.attrs["new_att"] = "new"
    assert node.attributes == {"id": "id", "new_att": "new"}


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_sets_attribute(parser):
    html_parser = parser('<div id="id"></div>')
    node = html_parser.css_first("div")
    node.attrs["id"] = "new_id"
    assert node.attributes == {"id": "new_id"}


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_removes_attribute(parser):
    html_parser = parser('<div id="id"></div>')
    node = html_parser.css_first("div")
    del node.attrs["id"]
    assert node.attributes == {}


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_test_dict_features(parser):
    html_parser = parser('<div id="id" v data-id="foo"></div>')
    node = html_parser.css_first("div")
    node.attrs["new_att"] = "new"
    assert list(node.attrs.keys()) == ["id", "v", "data-id", "new_att"]
    assert list(node.attrs.values()) == ["id", None, "foo", "new"]
    assert len(node.attrs) == 4
    assert node.attrs.get("unknown_field", "default_value") == "default_value"
    assert "id" in node.attrs
    assert "vid" not in node.attrs


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_keep_document_alive(parser):
    # LexborAttributes holds a borrowed pointer into the owning document, so it
    # has to keep the parser alive by itself. Here the parser is a temporary and
    # is freed by reference counting as soon as `.attrs` is evaluated.
    attrs = parser('<div id="id" data-x="1">text</div>').css_first("div").attrs

    assert list(attrs) == ["id", "data-x"]
    assert attrs["id"] == "id"
    assert attrs["data-x"] == "1"


# An element carrying both a plain and a namespace-prefixed variant of the same
# local name. Reporting local names collapsed them into one key, dropping a
# value, and iteration yielded the same key twice.
_SHARED_LOCAL_NAME = [
    ('<svg><use href="/plain" xlink:href="/xlinked"></use></svg>', "use"),
    ('<svg><use xlink:href="/xlinked" href="/plain"></use></svg>', "use"),
    ('<math><mi xlink:href="/xlinked" href="/plain"></mi></math>', "mi"),
    ('<div xlink:href="/xlinked" href="/plain"></div>', "div"),
]


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attributes_keeps_both_names_of_a_shared_local_name(parser):
    for html, selector in _SHARED_LOCAL_NAME:
        node = parser(html).css_first(selector)
        assert node.attributes == {"href": "/plain", "xlink:href": "/xlinked"}, html


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_iteration_yields_each_attribute_once(parser):
    for html, selector in _SHARED_LOCAL_NAME:
        node = parser(html).css_first(selector)
        assert sorted(node.attrs) == ["href", "xlink:href"], html
        assert len(node.attrs) == 2, html


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_keys_round_trip_through_lookup(parser):
    # Whatever iteration yields has to address the attribute it names, whichever
    # order the two attributes appear in. lxb_dom_element_attr_by_name() accepts
    # a match on either the local or the qualified name, so it could answer a
    # lookup of "href" with the value of "xlink:href".
    for html, selector in _SHARED_LOCAL_NAME:
        node = parser(html).css_first(selector)
        attributes = node.attributes

        for key in node.attrs:
            assert key in node.attrs, (html, key)
            assert node.attrs[key] == attributes[key], (html, key)

        assert dict(node.attrs.items()) == attributes, html


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_items_and_values_agree_with_lookup(parser):
    # items() and values() read each value off the attribute it belongs to instead
    # of resolving every name again, so they still have to answer as __getitem__
    # does: valueless is None, empty is an empty string.
    node = parser('<div id="a" bare empty=""></div>').css_first("div")

    assert list(node.attrs.items()) == [("id", "a"), ("bare", None), ("empty", "")]
    assert list(node.attrs.values()) == ["a", None, ""]
    assert dict(node.attrs.items()) == node.attributes


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_removes_the_attribute_it_looked_up(parser):
    # __delitem__ used to re-resolve the name through lexbor, which could drop
    # the attribute sharing a local name instead of the requested one.
    for html, selector in _SHARED_LOCAL_NAME:
        node = parser(html).css_first(selector)
        del node.attrs["href"]

        assert node.attributes == {"xlink:href": "/xlinked"}, html
        assert "href" not in node.attrs, html


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_prefixed_name_is_not_reachable_by_its_local_name(parser):
    # Only `xlink:href` is set, so there is no `href` attribute to find. As with
    # Element.getAttribute() in the DOM standard, a lookup matches the qualified
    # name and must not fall back to the local name.
    node = parser('<div xlink:href="/xlinked"></div>').css_first("div")

    assert node.attributes == {"xlink:href": "/xlinked"}
    assert node.attrs.get("xlink:href") == "/xlinked"
    assert node.attrs.get("href") is None
    assert "href" not in node.attrs
    with pytest.raises(KeyError):
        del node.attrs["href"]


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_lookup_stays_case_insensitive(parser):
    node = parser('<div DATA-X="1" data-y="2"></div>').css_first("div")

    assert node.attributes == {"data-x": "1", "data-y": "2"}
    assert node.attrs["DATA-X"] == "1"
    assert node.attrs["Data-X"] == "1"
    assert "DATA-X" in node.attrs


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_del_removes_missing_attribute(parser):
    node = parser('<div id="id"></div>').css_first("div")

    del node.attrs["id"]
    with pytest.raises(KeyError):
        del node.attrs["id"]
    with pytest.raises(KeyError):
        del node.attrs["unknown"]


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_del_of_id_and_class_updates_the_tree(parser):
    # lxb_dom_element_attr_remove() clears the element's cached id/class
    # pointers, so a removed id or class must stop matching selectors.
    html_parser = parser('<div id="id" class="cls"></div>')
    node = html_parser.css_first("div")

    del node.attrs["id"]
    assert html_parser.css("#id") == []
    assert len(html_parser.css(".cls")) == 1

    del node.attrs["class"]
    assert html_parser.css(".cls") == []
    assert html_parser.css_first("div").attributes == {}


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_traverse(parser):
    html = (
        '<div id="parent"><div id="prev"></div><div id="test_node"><h1 id="child">Title</h1>'
        '<div>foo</div><img scr="image.jpg"></div><div id="next"></div></div>'
    )
    html_parser = parser(html)
    actual = [node.tag for node in html_parser.root.traverse()]
    expected = ["html", "head", "body", "div", "div", "div", "h1", "div", "img", "div"]
    assert actual == expected


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_traverse_with_text(parser):
    html = (
        '<div id="parent"><div id="prev"></div><div id="test_node"><h1 id="child">Title</h1>'
        '<div>foo</div><img scr="image.jpg"></div><div id="next"></div></div>'
    )
    html_parser = parser(html)
    actual = [node.tag for node in html_parser.root.traverse(include_text=True)]
    expected = [
        "html",
        "head",
        "body",
        "div",
        "div",
        "div",
        "h1",
        "-text",
        "div",
        "-text",
        "img",
        "div",
    ]
    assert actual == expected


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_comparison(parser):
    html = """
        <div>H3ll0</div><div id='tt'><p id='stext'>Lorem ipsum dolor sit amet, ea quo modus meliore platonem.</p></div>
    """
    html_parser = parser(html)
    nodes = [node for node in html_parser.root.traverse(include_text=False)]
    same_node_path_one = nodes[-1].parent
    same_node_path_two = nodes[-2]
    same_node_path_three = html_parser.css_first("#tt")
    assert same_node_path_one == same_node_path_two == same_node_path_three


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_comprassion_with_strings(parser):
    html = """<div id="test"></div>"""
    html_parser = parser(html)
    node = html_parser.css_first("#test")
    assert node == '<div id="test"></div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_comparison_fails(parser):
    html = """<div id="test"></div>"""
    html_parser = parser(html)
    node = html_parser.css_first("#test")

    assert node is not None
    assert node != 123


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_adavanced_selector(parser):
    html_parser = parser("""
    <script>
     var super_value = 100;
    </script>
    """)
    selector = html_parser.select("script").text_contains("super_value")
    assert selector.any_matches


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_script_contain(parser):
    html_parser = parser("""
    <script>
     var super_value = 100;
    </script>
    """)
    assert html_parser.scripts_contain("super_value")


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_hash_nodes(parser):
    tree = parser("""<div><p><strong>J</strong>ohn</p><p>Doe</p></div>""")
    node = tree.css_first("div")
    assert node.mem_id == hash(node)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_srcs_contain(parser):
    html_parser = parser("""<script src="http://google.com/analytics.js"></script>""")
    assert html_parser.script_srcs_contain(("analytics.js",))


@pytest.mark.parametrize("parser", _PARSERS)
def test_content_method(parser):
    html = """
    <div>
        <div id="main">SuperTest</div>
    </div>
    """
    tree = parser(html)
    assert tree.css_first("#main").child.text_content == "SuperTest"
    assert tree.css_first("#main").text_content is None


@pytest.mark.parametrize("parser", _PARSERS)
def test_merge_text_nodes(parser):
    html = """<div><p><strong>J</strong>ohn</p><p>Doe</p></div>"""
    tree = parser(html)
    tree.unwrap_tags(["strong"])
    node = tree.css_first("div", strict=True)
    node.merge_text_nodes()
    assert node.html == "<div><p>John</p><p>Doe</p></div>"
    text = tree.text(deep=True, separator=" ", strip=True)
    assert text == "John Doe"


@pytest.mark.parametrize("parser", _PARSERS)
def test_merge_text_nodes_complex(parser):
    from textwrap import dedent

    html = dedent("""
        <article>
            <h1><em>H</em>ello <strong>W</strong>orld</h1>
            <div>
                <p>This <span>i</span>s <b>a</b> <i>t</i>est</p>
                <section>
                    <span>Nested</span> <span>text</span> nodes
                    <div>with <em>m</em>ore <strong>nesting</strong> here</div>
                </section>
            </div>
        </article>
    """).strip()
    tree = parser(html)
    tree.unwrap_tags(["em", "strong", "span", "b", "i"])
    root = tree.css_first("article", strict=True)
    root.merge_text_nodes()
    assert root.css_first("h1").text() == "Hello World"
    assert root.css_first("p").text() == "This is a test"
    assert "Nested text nodes" in root.css_first("section").text()
    assert root.css_first("section > div").text() == "with more nesting here"


@pytest.mark.parametrize("parser", _PARSERS)
def test_merge_text_nodes_three_plus(parser):
    html = """<div><em>O</em><strong>n</strong><b>e</b> <i>T</i><span>w</span><u>o</u> <small>T</small><big>h</big><mark>r</mark><sub>e</sub><sup>e</sup></div>"""
    tree = parser(html)
    tree.unwrap_tags(
        ["em", "strong", "b", "i", "span", "u", "small", "big", "mark", "sub", "sup"]
    )
    div = tree.css_first("div", strict=True)
    div.merge_text_nodes()
    assert div.text() == "One Two Three"


@pytest.mark.parametrize("parser", _PARSERS)
def test_merge_text_nodes_visits_every_sibling_subtree(parser):
    """Each element sibling must be descended into, not just the first one.

    Guards the iterative traversal: descending into the first child and then
    climbing out on ``next``/``parent`` has to pick up the remaining siblings,
    otherwise whole subtrees silently keep their unmerged text nodes.
    """
    html = (
        "<div>"
        + "".join(
            f"<section><b>x{i}</b>mid{i}<i>y{i}</i>tail{i}</section>"
            f"<article><b>p{i}</b>mid{i}<i>q{i}</i>tail{i}</article>"
            for i in range(50)
        )
        + "</div>"
    )
    tree = parser(html)
    tree.unwrap_tags(["b", "i"])
    root = tree.css_first("div", strict=True)
    root.merge_text_nodes()

    for node in root.css("section, article"):
        kids = list(node.iter(include_text=True))
        assert all(
            not (a.is_text_node and b.is_text_node) for a, b in zip(kids, kids[1:])
        ), f"{node.tag} still has adjacent text nodes: {node.html}"
    assert root.css_first("section").text() == "x0mid0y0tail0"
    assert root.css_first("article").text() == "p0mid0q0tail0"
    assert root.css("section")[-1].text() == "x49mid49y49tail49"
    assert root.css("article")[-1].text() == "p49mid49q49tail49"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_css_first_first(parser):
    html = '<h2 class="list-details__item__partial" id="js-partial">(1:1, 0:0, 0:0, 5:3)</h2>'
    selector = "h2.list-details__item__partial"
    find_first = parser(html).css_first(selector)
    assert find_first.css_first(selector) is not None


@pytest.mark.parametrize("parser", (LexborHTMLParser,))
def test_any_css_matches_fails(parser):
    html = """<h1>Test</h1>"""
    tree = parser(html)
    with pytest.raises(SelectolaxError):
        tree.any_css_matches(("##",))


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_text_separator_correctness(parser):
    inner = "".join(f"<span>word{i}</span>" for i in range(50))
    html = f"<div>{inner}</div>"
    tree = parser(html)
    node = tree.css_first("div")

    result = node.text(deep=True, separator=" ")
    parts = result.split(" ")

    assert parts[-1] != "", "Trailing separator found; join() not used correctly"
    assert len(parts) == 50
    for i, part in enumerate(parts):
        assert part == f"word{i}"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_text_strip_and_separator(parser):
    html = "<div><p>  hello  </p><p>  world  </p></div>"
    tree = parser(html)
    node = tree.css_first("div")

    result = node.text(deep=True, separator="|", strip=True)
    assert result == "hello|world"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_any_attribute_longer_than_missing_attribute(parser):
    html = """
    <div>
        <a href="http://very-long-url.example.com/path/to/page">with href</a>
        <a>no href at all</a>
        <a href="short">short href</a>
    </div>
    """
    tree = parser(html)
    # Must not raise TypeError despite the middle <a> having no href
    assert tree.root.select("a").any_attribute_longer_than("href", 10) is True
    assert tree.root.select("a").any_attribute_longer_than("href", 200) is False


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_any_attribute_longer_than_all_missing(parser):
    html = "<div><a>one</a><a>two</a></div>"
    tree = parser(html)
    assert tree.root.select("a").any_attribute_longer_than("href", 0) is False


def _descendants(node):
    """Every descendant of ``node`` in lexbor's walk order."""
    out = []
    stack = list(reversed(list(node.iter(include_text=True))))
    while stack:
        current = stack.pop()
        out.append(current)
        stack.extend(reversed(list(current.iter(include_text=True))))
    return out


def _reference_text(node, deep, separator, strip, skip_empty):
    """Recompute text() in pure Python, as ``separator.join(parts)``."""
    parts = []

    def add(candidate):
        content = candidate.text_content
        if content is None:
            return
        if skip_empty and candidate.is_empty_text_node:
            return
        parts.append(content.strip() if strip else content)

    if node.is_text_node:
        add(node)
    if deep:
        for descendant in _descendants(node):
            if descendant.is_text_node:
                add(descendant)
    else:
        for child in node.iter(include_text=True):
            if child.is_text_node:
                add(child)
    return separator.join(parts)


_TEXT_ASSEMBLY_CASES = [
    "<div>a<span>b</span>c</div>",
    "<div><span>  x  </span><span>\t y \n</span></div>",
]

# Tuple layout:
#   (html, selector, is_fragment, deep, separator, strip, skip_empty, expected)
# ``selector`` of None means the parser root.
_TEXT_EXPECTED_CASES = [
    # <div>a<span>b</span>c</div> has three text nodes, "a", "b" and "c", so the
    # deep walk concatenates them to "abc".
    ("<div>a<span>b</span>c</div>", "div", False, True, "", False, False, "abc"),
    ("<div>a<span>b</span>c</div>", "div", False, True, "|", False, False, "a|b|c"),
    ("<div>a<span>b</span>c</div>", "div", False, True, " ", False, False, "a b c"),
    ("<div>a<span>b</span>c</div>", "div", False, True, "-", True, False, "a-b-c"),
    ("<div>a<span>b</span>c</div>", "div", False, True, "", True, True, "abc"),
    # deep=False only sees the div's own text children, "a" and "c"; the text
    # inside the span is not a direct child.
    ("<div>a<span>b</span>c</div>", "div", False, False, "", False, False, "ac"),
    ("<div>a<span>b</span>c</div>", "div", False, False, "|", False, False, "a|c"),
    # Text inside <script> and <style> is text like any other.
    (
        "<div><script>var x=1;</script><style>a{}</style>ok</div>",
        "div",
        False,
        True,
        "",
        False,
        False,
        "var x=1;a{}ok",
    ),
    (
        "<div><script>var x=1;</script><style>a{}</style>ok</div>",
        "div",
        False,
        True,
        "|",
        False,
        False,
        "var x=1;|a{}|ok",
    ),
    # Whitespace around the fragments survives unless strip is set, and strip
    # is applied per fragment rather than to the joined result, so both the
    # leading and the trailing whitespace of each fragment disappear. The
    # single space inside "  x  " and inside "\t y \n" is interior and stays.
    (
        "<div><span>  x  </span><span>\t y \n</span></div>",
        "div",
        False,
        True,
        "",
        False,
        False,
        "  x  \t y \n",
    ),
    (
        "<div><span>  x  </span><span>\t y \n</span></div>",
        "div",
        False,
        True,
        "|",
        False,
        False,
        "  x  |\t y \n",
    ),
    (
        "<div><span>  x  </span><span>\t y \n</span></div>",
        "div",
        False,
        True,
        "|",
        True,
        False,
        "x|y",
    ),
    (
        "<div><span>  x  </span><span>\t y \n</span></div>",
        "div",
        False,
        True,
        "",
        True,
        False,
        "xy",
    ),
    (
        "<div><span>  x  </span><span>\t y \n</span></div>",
        "div",
        False,
        True,
        "",
        True,
        True,
        "xy",
    ),
    # Both text nodes here are whitespace only, so skip_empty drops both. It
    # used to be ignored entirely on the deep walk.
    (
        "<div>\n  \n<span>\t</span></div>",
        "div",
        False,
        True,
        "",
        False,
        False,
        "\n  \n\t",
    ),
    ("<div>\n  \n<span>\t</span></div>", "div", False, True, "", True, True, ""),
    (
        "<div>\n  \n<span>\t</span></div>",
        "div",
        False,
        True,
        "|",
        False,
        False,
        "\n  \n|\t",
    ),
    ("<div>\n  \n<span>\t</span></div>", "div", False, True, "|", True, True, ""),
    (
        "<div>\n  \n<span>\t</span></div>",
        "div",
        False,
        False,
        "",
        False,
        False,
        "\n  \n",
    ),
    ("<div>\n  \n<span>\t</span></div>", "div", False, False, "", True, True, ""),
    # skip_empty on the deep walk drops leading whitespace before a non-empty
    # fragment too.
    (
        "<div>\n  <span>\t</span><span>keep</span></div>",
        "div",
        False,
        True,
        "",
        False,
        False,
        "\n  \tkeep",
    ),
    (
        "<div>\n  <span>\t</span><span>keep</span></div>",
        "div",
        False,
        True,
        "|",
        True,
        True,
        "keep",
    ),
    # A plain space is ASCII whitespace, so it counts as empty.
    ("<div> </div>", "div", False, True, "", False, False, " "),
    ("<div> </div>", "div", False, True, "", True, False, ""),
    ("<div> </div>", "div", False, True, "", True, True, ""),
    # NBSP and the ideographic space are stripped by str.strip(), but they are
    # not ASCII whitespace, so skip_empty keeps them.
    ("<div>\u00a0</div>", "div", False, True, "", False, False, "\u00a0"),
    ("<div>\u00a0</div>", "div", False, True, "", True, False, ""),
    ("<div>\u00a0</div>", "div", False, True, "", False, True, "\u00a0"),
    ("<div>\u3000</div>", "div", False, True, "", False, False, "\u3000"),
    ("<div>\u3000</div>", "div", False, True, "", True, False, ""),
    # Empty and text-free elements yield an empty string, not None.
    ("<div></div>", "div", False, True, "", False, False, ""),
    ("<div></div>", "div", False, True, "|", False, False, ""),
    ("<div></div>", "div", False, False, "", False, False, ""),
    # Non-recursive text around an inline element.
    (
        "<p>lead<em>mid</em>trail</p>",
        "p",
        False,
        True,
        "",
        False,
        False,
        "leadmidtrail",
    ),
    ("<p>lead<em>mid</em>trail</p>", "p", False, False, "", False, False, "leadtrail"),
    # <br> contributes nothing, so deep and shallow agree.
    ("<div>a<br>b<br>c</div>", "div", False, True, "", False, False, "abc"),
    ("<div>a<br>b<br>c</div>", "div", False, False, "", False, False, "abc"),
    (
        "<table><tr><td>x</td><td>y</td></tr></table>",
        "td",
        False,
        True,
        "",
        False,
        False,
        "x",
    ),
    # Multibyte characters survive verbatim and are counted once.
    (
        "<div>\u00e9\u4e16\u754c\U0001f680</div>",
        "div",
        False,
        True,
        "",
        False,
        False,
        "\u00e9\u4e16\u754c\U0001f680",
    ),
    (
        "<div><span>\u00e9</span><span>\u4e16</span><span>\U0001f680</span></div>",
        "div",
        False,
        True,
        "|",
        False,
        False,
        "\u00e9|\u4e16|\U0001f680",
    ),
    # <div>a<b>a<b>a<b>z</b></b></b></div> has four text nodes, "a", "a",
    # "a", "z". Nesting adds elements, not text.
    (
        "<div>a<b>" * 3 + "z" + "</b>" * 3 + "</div>",
        "div",
        False,
        True,
        "",
        False,
        False,
        "aaaz",
    ),
    (
        "<div>a<b>" * 3 + "z" + "</b>" * 3 + "</div>",
        "div",
        False,
        True,
        "|",
        False,
        False,
        "a|a|a|z",
    ),
    # Repeated sibling elements: one separator between each, none trailing.
    (
        "<div><span>w0</span><span>w1</span><span>w2</span></div>",
        "div",
        False,
        True,
        "",
        False,
        False,
        "w0w1w2",
    ),
    (
        "<div><span>w0</span><span>w1</span><span>w2</span></div>",
        "div",
        False,
        True,
        "|",
        False,
        False,
        "w0|w1|w2",
    ),
    (
        "<div><span>w0</span><span>w1</span><span>w2</span></div>",
        "div",
        False,
        True,
        "|",
        True,
        False,
        "w0|w1|w2",
    ),
    # Fragments: the root is the first node of the fragment, and deep=True
    # reaches the siblings that follow it. A bare text root is covered by
    # test_text_does_not_duplicate_fragment_root_text_node in test_lexbor.py.
    ("<p>one</p><p>two</p>", None, True, True, "|", False, False, "one|two"),
    ("<p>one</p><p>two</p>", None, True, True, "", False, False, "onetwo"),
    # Not pinned here: deep=False on a fragment root walks the *parent's*
    # direct children, which are elements, so it returns "" while deep=True
    # returns "onetwo". That asymmetry is still unresolved, so no expected
    # value is asserted for it.
    # css_first() hands back an ordinary node rather than the fragment root,
    # so it only sees its own subtree.
    ("<p>one</p><p>two</p>", "p", True, True, "", False, False, "one"),
    ("<p>a<b>x</b>c</p>", "p", True, True, "", False, False, "axc"),
]


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
@pytest.mark.parametrize(
    "html,selector,is_fragment,deep,separator,strip,skip_empty,expected",
    _TEXT_EXPECTED_CASES,
)
def test_text_expected_value(
    parser, html, selector, is_fragment, deep, separator, strip, skip_empty, expected
):
    """Pin text() to literal expected strings."""
    node = parser(html, is_fragment=is_fragment).root
    assert node is not None
    if selector is not None:
        node = node.css_first(selector)
        assert node is not None, f"selector {selector!r} not found in {html!r}"
    assert (
        node.text(deep=deep, separator=separator, strip=strip, skip_empty=skip_empty)
        == expected
    )


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
@pytest.mark.parametrize("html", _TEXT_ASSEMBLY_CASES)
@pytest.mark.parametrize("is_fragment", [False, True])
@pytest.mark.parametrize("deep", [True, False])
@pytest.mark.parametrize("separator", ["", "|"])
@pytest.mark.parametrize("strip", [True, False])
@pytest.mark.parametrize("skip_empty", [True, False])
def test_text_matches_join_of_parts(
    parser, html, is_fragment, deep, separator, strip, skip_empty
):
    """Every combination of text() options must equal ``separator.join(parts)``."""
    tree = parser(html, is_fragment=is_fragment)
    node = tree.root
    if node is None:
        pytest.skip("empty fragment has no root")
    expected = _reference_text(node, deep, separator, strip, skip_empty)
    assert (
        node.text(deep=deep, separator=separator, strip=strip, skip_empty=skip_empty)
        == expected
    )


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_text_replaces_undecodable_bytes_instead_of_raising(parser):
    """text() substitutes U+FFFD rather than raising, on both paths."""
    node = parser(b"<div>\xff\xfe bad \x80bytes</div>").css_first("div")
    for kwargs in ({}, {"deep": False}, {"strip": True}, {"separator": "|"}):
        result = node.text(**kwargs)
        assert isinstance(result, str)
        assert "bad" in result
        assert "\ufffd" in result


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_text_content_exact_for_text_nodes(parser):
    """text_content returns this node's own characters verbatim."""
    tree = parser("<div>Super<b>Test</b></div>")
    child = tree.css_first("div").child
    assert child.is_text_node
    assert child.text_content == "Super"
    assert tree.css_first("b").text_content is None
    assert tree.css_first("div").text_content is None


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_text_and_text_lexbor_agree(parser):
    tree = parser("<div>a<span>b</span>c</div>")
    node = tree.css_first("div")
    assert node.text() == node.text_lexbor()
    assert tree.root.text() == tree.root.text_lexbor()


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_is_not_publicly_constructible(parser):
    with pytest.raises(TypeError, match="cannot be instantiated directly"):
        LexborNode()

    with pytest.raises(TypeError, match="cannot be instantiated directly"):
        LexborNode(1)

    node = parser("<div id='x'></div>").css_first("div")
    assert isinstance(node, LexborNode)
    assert node.id == "x"
    assert node.clone().id == "x"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attributes_is_not_publicly_constructible(parser):
    with pytest.raises(TypeError, match="cannot be instantiated directly"):
        LexborAttributes()

    node = parser("<div id='x' class='y'></div>").css_first("div")
    assert list(node.attrs) == ["id", "class"]


_SCRIPT_LOOKUP_HTML = (
    "<div id='a'><script>alpha</script><script src='alpha.js'></script></div>"
    "<div id='b'><script>beta</script><script src='beta.js'></script></div>"
)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_scripts_contain_is_scoped_to_the_node_it_is_called_on(parser):
    """Regression test: the cache lived on the parser but the search is per node.

    Both nodes live in one document and therefore shared one cache, so the
    second node answered with the first node's result.
    """
    tree = parser(_SCRIPT_LOOKUP_HTML)
    a, b = tree.css_first("#a"), tree.css_first("#b")

    assert a.scripts_contain("alpha") is True
    assert b.scripts_contain("alpha") is False
    assert b.scripts_contain("beta") is True
    assert a.scripts_contain("beta") is False


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_script_srcs_contain_is_scoped_to_the_node_it_is_called_on(parser):
    tree = parser(_SCRIPT_LOOKUP_HTML)
    a, b = tree.css_first("#a"), tree.css_first("#b")

    assert a.script_srcs_contain(("alpha.js",)) is True
    assert b.script_srcs_contain(("alpha.js",)) is False
    assert b.script_srcs_contain(("beta.js",)) is True
    assert a.script_srcs_contain(("beta.js",)) is False


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_script_lookup_does_not_depend_on_which_node_was_asked_first(parser):
    """The wrong answer must not depend on the order the scopes were queried."""
    tree = parser(_SCRIPT_LOOKUP_HTML)
    b, a = tree.css_first("#b"), tree.css_first("#a")

    assert b.scripts_contain("alpha") is False
    assert a.scripts_contain("alpha") is True
    assert b.script_srcs_contain(("alpha.js",)) is False
    assert a.script_srcs_contain(("alpha.js",)) is True


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_script_contain_sees_inserted_content(parser):
    """Regression test: the cache was never invalidated after a mutation."""
    tree = parser("<div><script>a()</script></div>")
    assert tree.scripts_contain("evil") is False

    tree.css_first("script").insert_child("evil")
    assert tree.scripts_contain("evil") is True


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_script_contain_stops_seeing_removed_content(parser):
    tree = parser("<div><script>evil()</script></div>")
    assert tree.scripts_contain("evil") is True

    tree.css_first("script").decompose()
    assert tree.scripts_contain("evil") is False

    tree = parser("<div><script>evil()</script></div>")
    assert tree.scripts_contain("evil") is True
    tree.css_first("script").unwrap()
    assert tree.scripts_contain("evil") is False

    tree = parser("<div><script>evil()</script></div>")
    assert tree.scripts_contain("evil") is True
    tree.css_first("script").replace_with("nothing to see")
    assert tree.scripts_contain("evil") is False

    tree = parser("<div><script>evil()</script></div>")
    assert tree.scripts_contain("evil") is True
    tree.strip_tags(["div"], recursive=True)
    assert tree.scripts_contain("evil") is False

    tree = parser("<div><script>evil()</script></div>")
    assert tree.scripts_contain("evil") is True
    tree.css_first("div").inner_html = "<span>clean</span>"
    assert tree.scripts_contain("evil") is False


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_script_srcs_contain_sees_attribute_changes(parser):
    """A changed ``src`` invalidates the lookup even though the node survives."""
    tree = parser("<script src='keep.js'></script>")
    assert tree.script_srcs_contain(("gone.js",)) is False

    tree.css_first("script").attrs["src"] = "gone.js"
    assert tree.script_srcs_contain(("gone.js",)) is True

    del tree.css_first("script").attrs["src"]
    assert tree.script_srcs_contain(("gone.js",)) is False

    tree = parser("<script src='gone.js'></script>")
    assert tree.script_srcs_contain(("gone.js",)) is True
    tree.css_first("script").attrs["src"] = None
    assert tree.script_srcs_contain(("gone.js",)) is False


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_script_contain_still_caches_for_the_whole_document(parser):
    """The cache is a performance feature, so it must survive repeated calls."""
    tree = parser(
        "<div id='a'><script>alpha</script></div>"
        "<div id='b'><script>beta</script></div>"
    )

    for _ in range(3):
        assert tree.scripts_contain("alpha") is True
        assert tree.scripts_contain("beta") is True
        assert tree.script_srcs_contain(("gone.js",)) is False
        assert tree.css_first("#a").scripts_contain("alpha") is True
        assert tree.css_first("#b").scripts_contain("alpha") is False


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_set_inner_html_leaves_replaced_nodes_readable(parser):
    """Nodes from the replaced subtree stay intact instead of reading freed memory."""
    tree = parser("<html><body><div id='a'><em>x</em></div></body></html>")
    old_div = tree.css_first("#a")
    old_em = tree.css_first("em")

    tree.body.inner_html = "<span>new</span>"

    # Detached, but still describing what they used to hold.
    assert old_div.html == '<div id="a"><em>x</em></div>'
    assert old_em.html == "<em>x</em>"
    assert old_div.text() == "x"
    assert [node.tag for node in old_div.css("*")] == ["div", "em"]
    # The replacement did not reach into them.
    assert tree.html == "<html><head></head><body><span>new</span></body></html>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_set_inner_html_recycled_addresses_do_not_alias(parser):
    """A retained node keeps its identity even after its address is handed out again."""
    tree = parser("<html><body><div id='a'><p>orig</p></div></body></html>")
    old_div = tree.css_first("#a")

    tree.body.inner_html = "<em>replacement</em>"
    for _ in range(500):
        tree.create_node("z")

    assert old_div.html == '<div id="a"><p>orig</p></div>'
    assert tree.body.inner_html == "<em>replacement</em>"


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_set_inner_html_on_a_detached_node_leaves_the_document_alone(parser):
    """Writing through a detached node must not corrupt the tree it came from."""
    tree = parser("<html><body><div id='a'><p>x</p></div></body></html>")
    old_div = tree.css_first("#a")
    tree.body.inner_html = "<em>y</em>"

    holder = tree.create_node("section")
    tree.body.insert_child(holder)
    for _ in range(200):
        holder.insert_child(tree.create_node("i"))
    expected = holder.html

    assert old_div.html == '<div id="a"><p>x</p></div>'
    old_div.insert_child("boom")
    # The write landed on the detached node, leaving the document untouched.
    assert old_div.inner_html == "<p>x</p>boom"
    assert holder.html == expected
    assert [node.tag for node in tree.root.traverse()] == [
        "html",
        "head",
        "body",
        "em",
        "section",
    ]
