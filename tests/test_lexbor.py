"""Tests for functionality that is only supported by lexbor backend."""

from inspect import cleandoc


from selectolax.lexbor import LexborHTMLParser, parse_fragment, SelectolaxError


def clean_doc(text: str) -> str:
    return f"{cleandoc(text)}\n"


def test_reads_inner_html():
    html = """<div id="main"><div>Hi</div><div id="updated">2025-09-27</div></div>"""
    parser = LexborHTMLParser(html)
    actual = parser.css_first("#main").inner_html
    expected = """<div>Hi</div><div id="updated">2025-09-27</div>"""
    assert actual == expected


def test_sets_inner_html():
    html = """<div id="main"><div>Hi</div><div id="updated">2025-09-27</div></div>"""
    parser = LexborHTMLParser(html)
    expected = "<span>Test</span>"
    parser.css_first("#main").inner_html = "<span>Test</span>"
    actual = parser.css_first("#main").inner_html
    assert actual == expected


def test_checking_attributes_does_not_segfault():
    parser = LexborHTMLParser("")
    root_node = parser.root
    assert root_node is not None
    for node in root_node.traverse():
        parent = node.parent
        assert parent is not None
        parent = parent.attributes.get("anything")


def test_node_cloning():
    parser = LexborHTMLParser("<div id='main'>123</div>")
    new_node = parser.css_first("#main").clone()
    new_node.inner_html = "<div>new</div>"
    assert parser.css_first("#main").html != new_node.html
    assert new_node.html == '<div id="main"><div>new</div></div>'


def test_double_unwrap_does_not_segfault():
    html = """<div><div><div></div></div></div>"""
    outer_div = parse_fragment(html)[0]
    some_set = set()

    inner_div = outer_div.child
    assert inner_div is not None
    inner_div.unwrap()
    inner_div.unwrap()
    some_set.add(outer_div.parent)
    some_set.add(outer_div.parent)


def test_unicode_selector_works():
    html = '<span data-original-title="Pneu renforcé"></span>'
    tree = LexborHTMLParser(html)
    node = tree.css_first('span[data-original-title="Pneu renforcé"]')
    assert node.tag == "span"


def test_node_type_helpers():
    html = "<div id='main'>text<!--comment--></div>"
    parser = LexborHTMLParser(html)

    div_node = parser.css_first("#main")
    assert div_node.is_element_node
    assert not div_node.is_text_node

    text_node = div_node.first_child
    assert text_node is not None
    assert text_node.is_text_node
    assert not text_node.is_element_node

    comment_node = div_node.last_child
    assert comment_node is not None
    assert comment_node.is_comment_node
    assert not comment_node.is_text_node

    document_node = parser.root.parent
    assert document_node is not None
    assert document_node.is_document_node
    assert not document_node.is_element_node


def test_text_honors_skip_empty_flag():
    parser = LexborHTMLParser("<div><span>value</span><title>\n   \n</title></div>")
    span = parser.css_first("span")
    assert span is not None
    assert span.text(deep=False, skip_empty=False) == "value"
    assert span.text(deep=False, skip_empty=True) == "value"
    title = parser.css_first("title")
    assert title is not None
    assert title.text(deep=False, skip_empty=False) == "\n   \n"
    assert title.text(deep=False, skip_empty=True) == ""


def test_iter_includes_text_nodes_when_requested():
    parser = LexborHTMLParser("<div><span>value</span><title>\n   \n</title></div>")
    div = parser.css_first("div")
    children = [node for node in div.iter(include_text=True, skip_empty=True)]
    assert (
        ", ".join(
            node.tag for node in children[0].iter(include_text=True, skip_empty=True)
        )
        == "-text"
    )
    assert (
        ", ".join(
            node.tag for node in children[1].iter(include_text=True, skip_empty=True)
        )
        == ""
    )


def test_traverse_respects_skip_empty_on_text_nodes():
    parser = LexborHTMLParser("<div><span>value</span><title>\n   \n</title></div>")
    div = parser.css_first("div")
    children = [node.tag for node in div.traverse(include_text=True, skip_empty=True)]
    assert ", ".join(children) == "div, span, -text, title"


def test_traverse_with_skip_empty_on_a_full_html_document():
    html = clean_doc(
        """
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title>Title!</title>
            <!-- My crazy comment -->
          </head>
          <body>
            <p>Hello <strong>World</strong>!</p>
            <div hidden draggable="true" translate="no" contenteditable="true" tabindex="3">
              Div
            </div>
          </body>
        </html>
        """
    )
    parser = LexborHTMLParser(html)
    children = [
        (node.tag, node.text_content)
        for node in parser.root.traverse(include_text=True, skip_empty=False)
    ]
    assert children == [
        ("html", None),
        ("head", None),
        ("-text", "\n    "),
        ("meta", None),
        ("-text", "\n    "),
        ("meta", None),
        ("-text", "\n    "),
        ("title", None),
        ("-text", "Title!"),
        ("-text", "\n    "),
        ("-comment", None),
        ("-text", "\n  "),
        ("-text", "\n  "),
        ("body", None),
        ("-text", "\n    "),
        ("p", None),
        ("-text", "Hello "),
        ("strong", None),
        ("-text", "World"),
        ("-text", "!"),
        ("-text", "\n    "),
        ("div", None),
        ("-text", "\n      Div\n    "),
        ("-text", "\n  \n\n"),
    ]
    children = [
        (node.tag, node.text_content)
        for node in parser.root.traverse(include_text=True, skip_empty=True)
    ]
    assert children == [
        ("html", None),
        ("head", None),
        ("meta", None),
        ("meta", None),
        ("title", None),
        ("-text", "Title!"),
        ("-comment", None),
        ("body", None),
        ("p", None),
        ("-text", "Hello "),
        ("strong", None),
        ("-text", "World"),
        ("-text", "!"),
        ("div", None),
        ("-text", "\n      Div\n    "),
    ]


def test_is_empty_text_node_property():
    parser = LexborHTMLParser("<div><span>\n \n</span><title>X</title></div>")
    text_node = parser.css_first("span").first_child
    assert text_node.text_content == "\n \n"
    assert text_node.is_empty_text_node
    text_node = parser.css_first("title").first_child
    assert text_node.text_content == "X"
    assert not text_node.is_empty_text_node


def test_comment_content_property() -> None:
    parser = LexborHTMLParser("<div><span><!-- hello --></span><title>X</title></div>")
    text_node = parser.css_first("span").first_child
    assert text_node is not None
    assert text_node.is_comment_node
    assert text_node.comment_content == "hello"


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


def test_node_insert_operations_with_different_types():
    html = '<div><span id="target">target</span></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    target = root.css_first("#target")
    assert target is not None

    # Test insert_before with string
    target.insert_before("before_text")
    assert "before_text<span" in root.html

    # Test insert_after with bytes
    target.insert_after(b"after_bytes")
    assert "after_bytes</div>" in root.html


def test_node_replace_with_different_types():
    html = '<div><span id="target">old</span></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    target = root.css_first("#target")
    assert target is not None

    # Test replace_with string
    target.replace_with("replaced")
    assert root.html == "<html><head></head><body><div>replaced</div></body></html>"

    # Test replace_with bytes
    html = '<div><span id="target">old</span></div>'
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    target = root.css_first("#target")
    assert target is not None

    target.replace_with(b"bytes_replaced")
    assert "bytes_replaced" in root.html


def test_node_insert_with_lexbor_node():
    html1 = "<div>content1</div>"
    html2 = "<span>content2</span>"
    parser1 = LexborHTMLParser(html1)
    parser2 = LexborHTMLParser(html2)

    root1 = parser1.root
    root2 = parser2.root
    assert root1 is not None and root2 is not None

    div1 = root1.css_first("div")
    span2 = root2.css_first("span")
    assert div1 is not None and span2 is not None

    # Insert node from another parser
    div1.insert_child(span2)
    assert "<span>content2</span>" in root1.html


def test_node_manipulation_with_fragments():
    html = "<div>First</div><span>Second</span>"
    parser = LexborHTMLParser(html, is_fragment=True)
    root = parser.root
    assert root is not None

    span = root.next
    assert span is not None

    span.insert_before("Before")
    assert parser.html == "<div>First</div>Before<span>Second</span>"

    span.insert_after("After")
    assert parser.html == "<div>First</div>Before<span>Second</span>After"

    span.insert_child("Child")
    assert parser.html == "<div>First</div>Before<span>SecondChild</span>After"


def test_merge_text_nodes_edge_cases():
    html = "<div><p><strong>J</strong>ohn<strong>D</strong>oe</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None

    # Before unwrapping - text nodes are separated by strong tags
    text_before = div.text(deep=True, separator="")
    assert "JohnDoe" in text_before

    # Unwrap strong tags - this creates adjacent text nodes
    div.unwrap_tags(["strong"])

    # After unwrapping but before merging - text nodes are adjacent
    text_after_unwrap = div.text(deep=True, separator="")
    assert "JohnDoe" in text_after_unwrap

    # After merging - should be the same since they were already adjacent
    div.merge_text_nodes()
    text_after_merge = div.text(deep=True, separator="")
    assert "JohnDoe" in text_after_merge


def test_unwrap_tags_with_nested_elements():
    html = "<div><p><span><em>Text</em></span></p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    div = root.css_first("div")
    assert div is not None

    div.unwrap_tags(["span", "em"])
    html = root.html
    assert html is not None
    assert "<span>" not in html and "<em>" not in html
    assert "Text" in html


def test_unwrap_tags_delete_empty():
    html = "<div><p><span></span><em>Keep</em><i></i></p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    p = root.css_first("p")
    assert p is not None

    p.unwrap_tags(["span", "i"], delete_empty=True)
    html = root.html
    assert html is not None
    assert "<span>" not in html and "<i>" not in html
    assert "<em>Keep</em>" in html


def test_parser_clone_method():
    html = "<div id='original'><p>Original content</p></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None

    # Clone the parser
    cloned_parser = parser.clone()
    assert cloned_parser is not parser
    assert cloned_parser.html == parser.html

    # Modify the clone
    cloned_root = cloned_parser.root
    assert cloned_root is not None
    cloned_div = cloned_root.css_first("div")
    assert cloned_div is not None
    cloned_div.attrs["id"] = "modified"

    # Original should be unchanged
    original_div = root.css_first("div")
    assert original_div is not None
    assert original_div.attrs["id"] == "original"

    # Clone should be modified
    assert cloned_div.attrs["id"] == "modified"


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

    try:
        root.css("[invalid")
    except Exception:
        pass


def test_selector_attribute_longer_than_edge_cases():
    html = "<div><a href='short'>Link1</a><a>Link2</a><a href=''>Link3</a></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None

    selector = root.select("a")
    result = selector.attribute_longer_than("href", 0)
    assert len(result.matches) == 1


def test_node_replace_with_empty():
    html = "<div><span>target</span></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    span = root.css_first("span")
    assert span is not None

    span.replace_with("")
    html_result = root.html
    assert html_result is not None
    assert "<span>" not in html_result
    assert parser.html == "<html><head></head><body><div></div></body></html>"


def test_double_unwrap_prevention():
    html = "<div><span>test</span></div>"
    parser = LexborHTMLParser(html)
    root = parser.root
    assert root is not None
    span = root.css_first("span")
    assert span is not None

    # First unwrap should work
    span.unwrap()

    # Second unwrap should not cause issues (already removed)
    span.unwrap()

    html_result = root.html
    assert html_result is not None
    assert "test" in html_result


def test_clone_complex_modifications():
    html = "<div><p>Original</p><span>Content</span></div>"
    parser = LexborHTMLParser(html)

    p_tag = parser.root.css_first("p")
    assert p_tag is not None
    p_tag.inner_html = "Modified"

    cloned = parser.clone()

    cloned_p = cloned.root.css_first("p")
    assert cloned_p is not None
    cloned_p.decompose()

    original_text = parser.root.text()
    assert "Modified" in original_text

    cloned_text = cloned.root.text()
    assert "Modified" not in cloned_text


def test_create_node_basic():
    parser = LexborHTMLParser("<div></div>")
    new_node = parser.create_node("span")
    assert new_node.tag == "span"
    assert new_node.parent is None

    parser.css_first("div").insert_child(new_node)
    expected_html = "<html><head></head><body><div><span></span></div></body></html>"
    assert parser.html == expected_html


def test_create_node_different_tags():
    parser = LexborHTMLParser("<div></div>")
    root = parser.root
    assert root is not None

    tags_to_test = ["p", "span", "div", "h1", "custom-tag"]
    for tag in tags_to_test:
        new_node = parser.create_node(tag)
        assert new_node.tag == tag
        root.insert_child(new_node)

    html = parser.html
    assert html is not None
    for tag in tags_to_test:
        assert f"<{tag}></{tag}>" in html


def test_create_node_with_attributes():
    parser = LexborHTMLParser("<div></div>")
    new_node = parser.create_node("a")
    new_node.attrs["href"] = "https://example.com"
    new_node.attrs["class"] = "link"

    parser.root.insert_child(new_node)
    html = parser.html
    assert html is not None
    assert 'href="https://example.com"' in html
    assert 'class="link"' in html


def test_create_node_empty_tag_name():
    parser = LexborHTMLParser("<div></div>")
    try:
        parser.create_node("")
        assert False, "Should have raised an exception"
    except SelectolaxError:
        pass
