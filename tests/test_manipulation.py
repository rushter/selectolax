import pytest

from selectolax.lexbor import (
    LexborHTMLParser,
    SelectolaxError,
)
from tests.helpers import _top_level_nodes


def test_double_unwrap_does_not_segfault():
    html = """<div><div><div></div></div></div>"""
    outer_div = LexborHTMLParser(html, is_fragment=True).root
    some_set = set()

    inner_div = outer_div.child
    assert inner_div is not None
    inner_div.unwrap()
    inner_div.unwrap()
    some_set.add(outer_div.parent)
    some_set.add(outer_div.parent)


def test_merge_text_nodes_merges_top_level_runs_of_a_fragment():
    parser = LexborHTMLParser("<div>1</div><p><i>a</i></p>", is_fragment=True)

    # Unwrapping the <p> lifts its <i> to the top level, then two text nodes get
    # inserted in front of it, forming a run of adjacent text nodes that lives
    # beside the fragment root rather than inside it.
    parser.root.next.unwrap()
    node = parser.root.next
    node.insert_before("X")
    node.insert_before("Y")

    top_level = [(n.tag, n.text_content) for n in _top_level_nodes(parser)]
    assert top_level == [("div", None), ("-text", "X"), ("-text", "Y"), ("i", None)]

    parser.merge_text_nodes()
    assert [(n.tag, n.text_content) for n in _top_level_nodes(parser)] == [
        ("div", None),
        ("-text", "XY"),
        ("i", None),
    ]


def test_merge_text_nodes_on_a_non_root_node_stays_scoped():
    parser = LexborHTMLParser("<div>1</div><p><i>a</i></p>", is_fragment=True)
    parser.root.next.unwrap()
    node = parser.root.next
    node.insert_before("X")
    node.insert_before("Y")

    node.merge_text_nodes()

    assert [(n.tag, n.text_content) for n in _top_level_nodes(parser)] == [
        ("div", None),
        ("-text", "X"),
        ("-text", "Y"),
        ("i", None),
    ]


def test_merge_text_nodes_on_a_detached_fragment_root_is_a_safe_noop():
    parser = LexborHTMLParser("<div>a<span>s</span></div><p>b</p>", is_fragment=True)
    root = parser.root
    root.decompose()

    root.merge_text_nodes()

    assert root.text() == ""
    assert root.text_lexbor() == ""
    assert parser.html == "<p>b</p>"


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


def test_unwrap_tags_segfault_prevention():
    # This scenario used to cause a segmentation fault because the 'span' tag
    # matches the node itself, causing it to be detached. The subsequent
    # search for 'p' would then happen on a detached node.
    html = "<div><span id='repro'><span><p>Text</p></span></span></div>"
    tree = LexborHTMLParser(html)
    node = tree.css_first("#repro")
    assert node is not None

    # Should not segfault
    node.unwrap_tags(["span", "p"])

    assert "Text" in tree.html
    assert '<span id="repro">' not in tree.html


def test_strip_tags_then_text_basic():
    html = "<html><head></head><body><script>evil();</script><p>Hello</p></body></html>"
    parser = LexborHTMLParser(html)
    parser.strip_tags(["script"])
    result = parser.root.text(separator=" ", strip=True)
    assert "Hello" in result
    assert "evil" not in result


def test_strip_tags_then_text_multiple_tags():
    html = (
        "<html><head><style>body{}</style></head><body>"
        "<script>x=1;</script>"
        "<template><div>hidden</div></template>"
        "<p>Visible</p>"
        "</body></html>"
    )
    parser = LexborHTMLParser(html)
    parser.strip_tags(["style", "script", "template"])
    result = parser.root.text(separator=" ", strip=True)
    assert "Visible" in result
    assert "hidden" not in result
    assert "body{}" not in result


def test_strip_tags_then_text_nested_targets():
    html = (
        "<html><body>"
        "<template><script>inner();</script><p>tmpl</p></template>"
        "<script>outer();</script>"
        "<p>Keep this</p>"
        "</body></html>"
    )
    parser = LexborHTMLParser(html)
    parser.strip_tags(["template", "script"])
    result = parser.root.text(separator=" ", strip=True)
    assert "Keep this" in result
    assert "inner" not in result
    assert "outer" not in result


def test_strip_tags_then_text_recursive_flag():
    html = (
        "<html><body>"
        "<div class='rm'><span>child1</span><em>child2</em></div>"
        "<p>Survivor</p>"
        "</body></html>"
    )
    parser = LexborHTMLParser(html)
    parser.strip_tags(["div"], recursive=True)
    result = parser.root.text(separator=" ", strip=True)
    assert "Survivor" in result
    assert "child1" not in result


def test_strip_tags_then_text_many_iterations():
    template = (
        "<html><head><style>.a{{}}</style></head><body>"
        "<script>var x={i};</script>"
        "<p>Content {i}</p>"
        "</body></html>"
    )
    for i in range(50):
        parser = LexborHTMLParser(template.format(i=i))
        parser.strip_tags(["style", "script"])
        text = parser.root.text(separator=" ", strip=True)
        assert f"Content {i}" in text


def test_insert_node_fragment_parser():
    html = "<div></div>"
    p = LexborHTMLParser(html, is_fragment=True)
    p.root.insert_child("text")
    assert p.html == "<div>text</div>"


def test_insert_before_fragment_parser():
    html = "<div><span></span></div>"
    p = LexborHTMLParser(html, is_fragment=True)
    span = p.root.css_first("span")
    span.insert_before("text")
    assert p.html == "<div>text<span></span></div>"


def test_insert_after_fragment_parser():
    html = "<div><span></span></div>"
    p = LexborHTMLParser(html, is_fragment=True)
    span = p.root.css_first("span")
    span.insert_after("text")
    assert p.html == "<div><span></span>text</div>"


def test_fragment_node_operations_combined():
    html = "<div><span>Hello</span></div>"
    p = LexborHTMLParser(html, is_fragment=True)
    span = p.root.css_first("span")
    span.replace_with("Replaced")
    assert p.html == "<div>Replaced</div>"

    html2 = "<div><span></span></div>"
    p2 = LexborHTMLParser(html2, is_fragment=True)
    span2 = p2.root.css_first("span")
    span2.insert_before("Before")
    span2.insert_after("After")
    assert p2.html == "<div>Before<span></span>After</div>"


def test_fragment_replace_with_node():
    html = "<div><span>Hello</span></div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    replacement_html = "<em>Replaced</em>"
    replacement_parser = LexborHTMLParser(replacement_html, is_fragment=True)
    span = parser.root.css_first("span")
    span.replace_with(replacement_parser.root)
    assert parser.html == "<div><em>Replaced</em></div>"


def test_fragment_insert_before_node():
    base_html = "<div><span></span></div>"
    base_parser = LexborHTMLParser(base_html, is_fragment=True)
    before_html = "<strong>Before</strong>"
    before_parser = LexborHTMLParser(before_html, is_fragment=True)
    span = base_parser.root.css_first("span")
    span.insert_before(before_parser.root)
    assert base_parser.html == "<div><strong>Before</strong><span></span></div>"


def test_fragment_insert_after_node():
    base_html = "<div><span></span></div>"
    base_parser = LexborHTMLParser(base_html, is_fragment=True)
    after_html = "<em>After</em>"
    after_parser = LexborHTMLParser(after_html, is_fragment=True)
    span = base_parser.root.css_first("span")
    span.insert_after(after_parser.root)
    assert base_parser.html == "<div><span></span><em>After</em></div>"


def test_fragment_insert_child_node():
    base_html = "<div></div>"
    base_parser = LexborHTMLParser(base_html, is_fragment=True)
    child_html = "<p>Child</p>"
    child_parser = LexborHTMLParser(child_html, is_fragment=True)
    div = base_parser.root.css_first("div")
    div.insert_child(child_parser.root)
    assert base_parser.html == "<div><p>Child</p></div>"


def test_fragment_strip_tags():
    html = "<div><script>alert('test')</script><p>Hello</p><style>body { color: red; }</style></div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    parser.root.strip_tags(["script", "style"])
    assert parser.html == "<div><p>Hello</p></div>"


def test_fragment_decompose():
    html = "<div><script>alert('test')</script><p>Hello</p></div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    script = parser.root.css_first("script")
    script.decompose()
    assert parser.html == "<div><p>Hello</p></div>"


def test_fragment_unwrap():
    html = "<div><span>Hello</span> world</div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    span = parser.root.css_first("span")
    span.unwrap()
    assert parser.html == "<div>Hello world</div>"


def test_fragment_unwrap_tags():
    html = "<div><i>Hello</i> <b>world</b></div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    parser.root.unwrap_tags(["i", "b"])
    assert parser.html == "<div>Hello world</div>"


def test_fragment_create_node_basic():
    parser = LexborHTMLParser("<div></div>", is_fragment=True)
    assert parser.root is not None
    new_node = parser.create_node("span")
    assert new_node.tag == "span"
    assert new_node.parent is None

    parser.root.insert_child(new_node)
    expected_html = "<div><span></span></div>"
    assert parser.html == expected_html


def test_fragment_create_node_different_tags():
    parser = LexborHTMLParser("<div></div>", is_fragment=True)
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


def test_fragment_create_node_with_attributes():
    parser = LexborHTMLParser("<div></div>", is_fragment=True)
    assert parser.root is not None
    new_node = parser.create_node("a")
    new_node.attrs["href"] = "https://example.com"
    new_node.attrs["class"] = "link"

    parser.root.insert_child(new_node)
    html = parser.html
    assert html is not None
    assert 'href="https://example.com"' in html
    assert 'class="link"' in html


def test_decompose():
    html = "<body><div><p id='p3'>text</p></div></body>"
    html_parser = LexborHTMLParser(html)

    for node in html_parser.tags("p"):
        node.decompose()
    assert html_parser.body.child.html == "<div></div>"


def test_strip_tags():
    html = "<body><div></div><script></script></body>"
    html_parser = LexborHTMLParser(html)
    html_parser.root.strip_tags(["div", "script"])
    assert html_parser.html == "<html><head></head><body></body></html>"

    with pytest.raises(TypeError):
        html_parser.strip_tags(1)


def test_unwrap():
    html = '<a id="url" href="https://rushter.com/">I linked to <i>rushter.com</i></a>'
    html_parser = LexborHTMLParser(html)
    node = html_parser.css_first("i")
    node.unwrap()
    assert (
        html_parser.body.child.html
        == '<a id="url" href="https://rushter.com/">I linked to rushter.com</a>'
    )


def test_unwrap_detaches_node_from_its_children():
    """An unwrapped node must stop referring to the children it just moved.

    ``lxb_dom_node_insert_before()`` re-parents without unlinking from the old
    parent, so without an explicit remove this node's ``first_child`` /
    ``last_child`` kept pointing at children that had already moved up to its
    own parent. Those nodes then belonged to two child lists at once, and
    reading or serializing the unwrapped node walked a cycle and segfaulted.
    """
    html_parser = LexborHTMLParser("<html><body><p>1</p><p>2</p></body></html>")
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


def test_unwrap_preserves_child_order():
    html_parser = LexborHTMLParser("<div>a<b>1</b><i>2</i><u>3</u>z</div>")
    html_parser.css_first("div").unwrap()
    assert html_parser.body.inner_html == "a<b>1</b><i>2</i><u>3</u>z"


def test_unwrap_moved_children_are_not_duplicated():
    html_parser = LexborHTMLParser("<div><p><b>1</b></p><p><b>2</b></p></div>")
    html_parser.css_first("div").unwrap()

    assert html_parser.body.inner_html == "<p><b>1</b></p><p><b>2</b></p>"
    assert len(html_parser.css("b")) == 2
    # Every element's inner_html must still match its own children.
    for node in html_parser.css("*"):
        assert node.inner_html == "".join(
            child.html for child in node.iter(include_text=True)
        )


def test_unwrap_empty_tag():
    html = '<a id="url" href="https://rushter.com/">I linked to rushter.com<i></i></a>'
    html_parser = LexborHTMLParser(html)
    node = html_parser.css_first("i")
    node.unwrap(delete_empty=True)
    assert (
        html_parser.body.child.html
        == '<a id="url" href="https://rushter.com/">I linked to rushter.com</a>'
    )


def test_unwrap_tags():
    html_parser = LexborHTMLParser("<div><a href=>Hello</a> <i>world</i>!</div>")
    html_parser.body.unwrap_tags(["i", "a"])
    assert html_parser.body.html == "<body><div>Hello world!</div></body>"


def test_unwrap_empty_tags():
    html_parser = LexborHTMLParser(
        "<div><a href=>Hello</a> <i>world</i>!<i></i><a></a></div>"
    )
    html_parser.body.unwrap_tags(["i", "a"], delete_empty=True)
    assert html_parser.body.html == "<body><div>Hello world!</div></body>"


def test_unwraps_multiple_child_nodes():
    html = """
    <div id="test">
        foo <span>bar <i>Lor<span>ems</span></i> I <span class='p3'>dummy <div>text</div></span></span>
    </div>
    """
    html_parser = LexborHTMLParser(html)
    html_parser.body.unwrap_tags(["span", "i"])
    assert (
        html_parser.body.child.html
        == '<div id="test">\n        foo bar Lorems I dummy <div>text</div>\n    </div>'
    )


def test_unwraps_multiple_child_nodes_with_empty():
    html = """
    <div id="test">
        foo <span>bar <i>Lor<span>ems</span></i> I <span class='p3'>dummy<span><i></i></span> <div>text</div></span></span>
    </div>
    """
    html_parser = LexborHTMLParser(html)
    html_parser.body.unwrap_tags(["span", "i"], delete_empty=True)
    assert (
        html_parser.body.child.html
        == '<div id="test">\n        foo bar Lorems I dummy <div>text</div>\n    </div>'
    )


def test_replace_with():
    html_parser = LexborHTMLParser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first("img")
    img.replace_with(img.attributes.get("alt", ""))
    assert html_parser.body.child.html == "<div>Get Laptop</div>"


def test_replace_with_multiple_nodes():
    html_parser = LexborHTMLParser(
        '<div>Get <span alt="Laptop"><img src="/jpg"> <div>/div></span></div>'
    )
    img = html_parser.css_first("span")
    img.replace_with(img.attributes.get("alt", ""))
    assert html_parser.body.child.html == "<div>Get Laptop</div>"


def test_node_replace_with():
    html_parser = LexborHTMLParser(
        '<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>'
    )
    html_parser2 = LexborHTMLParser("<div>Test</div>")
    img_node = html_parser.css_first("img")
    img_node.replace_with(html_parser2.body.child)
    assert (
        html_parser.body.child.html
        == '<div>Get <span alt="Laptop"><div>Test</div> <div></div></span></div>'
    )


def test_replace_with_empty_string():
    html_parser = LexborHTMLParser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first("img")
    img.replace_with("")
    assert html_parser.body.child.html == "<div>Get </div>"


def test_replace_with_invalid_value_passed_exception():
    with pytest.raises(TypeError) as excinfo:
        html_parser = LexborHTMLParser('<div>Get <img src="" alt="Laptop"></div>')
        img = html_parser.css_first("img")
        img.replace_with(None)
    assert "No matching signature found" in str(excinfo.value)


def test_insert_before():
    html_parser = LexborHTMLParser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first("img")
    img.insert_before(img.attributes.get("alt", ""))
    assert (
        html_parser.body.child.html == '<div>Get Laptop<img src="" alt="Laptop"></div>'
    )


def test_node_insert_before():
    html_parser = LexborHTMLParser(
        '<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>'
    )
    html_parser2 = LexborHTMLParser("<div>Test</div>")
    img_node = html_parser.css_first("img")
    img_node.insert_before(html_parser2.body.child)
    assert (
        html_parser.body.child.html
        == '<div>Get <span alt="Laptop"><div>Test</div><img src="/jpg"> <div></div></span></div>'
    )


def test_insert_after():
    html_parser = LexborHTMLParser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first("img")
    img.insert_after(img.attributes.get("alt", ""))
    assert (
        html_parser.body.child.html == '<div>Get <img src="" alt="Laptop">Laptop</div>'
    )


def test_node_insert_after():
    html_parser = LexborHTMLParser(
        '<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>'
    )
    html_parser2 = LexborHTMLParser("<div>Test</div>")
    img_node = html_parser.css_first("img")
    img_node.insert_after(html_parser2.body.child)
    assert (
        html_parser.body.child.html
        == '<div>Get <span alt="Laptop"><img src="/jpg"><div>Test</div> <div></div></span></div>'
    )


def test_insert_child():
    html_parser = LexborHTMLParser('<div>Get <img src=""></div>')
    div = html_parser.css_first("div")
    div.insert_child("Laptop")
    assert html_parser.body.child.html == '<div>Get <img src="">Laptop</div>'


def test_node_insert_child():
    html_parser = LexborHTMLParser(
        '<div>Get <span alt="Laptop"> <div>Laptop</div> </span></div>'
    )
    html_parser2 = LexborHTMLParser("<div>Test</div>")
    span_node = html_parser.css_first("span")
    span_node.insert_child(html_parser2.body.child)
    assert (
        html_parser.body.child.html
        == '<div>Get <span alt="Laptop"> <div>Laptop</div> <div>Test</div></span></div>'
    )


def test_same_document_insert_child_moves_node():
    parser = LexborHTMLParser("<div></div><span>hello</span>")
    div = parser.css_first("div")
    span = parser.css_first("span")
    div.insert_child(span)
    assert parser.body.html == "<body><div><span>hello</span></div></body>"


def test_same_document_insert_before_moves_node():
    parser = LexborHTMLParser("<p>first</p><p>second</p>")
    p2 = parser.css("p")[1]
    p1 = parser.css_first("p")
    p2.insert_before(p1)
    assert parser.body.html == "<body><p>first</p><p>second</p></body>"


def test_same_document_insert_after_moves_node():
    parser = LexborHTMLParser("<span>A</span><div>B</div><em>C</em>")
    span = parser.css_first("span")
    em = parser.css_first("em")
    span.insert_after(em)
    assert parser.body.html == "<body><span>A</span><em>C</em><div>B</div></body>"


def test_same_document_replace_with_moves_node():
    parser = LexborHTMLParser("<div><a>link</a><b>bold</b></div>")
    a = parser.css_first("a")
    b = parser.css_first("b")
    a.replace_with(b)
    assert parser.css_first("div").html == "<div><b>bold</b></div>"


def test_cross_document_insert_child_moves_node():
    html_parser = LexborHTMLParser("<div></div>")
    html_parser2 = LexborHTMLParser("<span>foreign</span>")
    html_parser.css_first("div").insert_child(html_parser2.css_first("span"))
    assert "<span>foreign</span>" in html_parser.body.html
    assert html_parser2.css_first("span") is None


def test_cross_document_replace_with_moves_node():
    html_parser = LexborHTMLParser("<div><a>link</a></div>")
    html_parser2 = LexborHTMLParser("<b>bold</b>")
    html_parser.css_first("a").replace_with(html_parser2.css_first("b"))
    assert "<b>bold</b>" in html_parser.css_first("div").html
    assert html_parser2.css_first("b") is None


def test_merge_text_nodes():
    html = """<div><p><strong>J</strong>ohn</p><p>Doe</p></div>"""
    tree = LexborHTMLParser(html)
    tree.unwrap_tags(["strong"])
    node = tree.css_first("div", strict=True)
    node.merge_text_nodes()
    assert node.html == "<div><p>John</p><p>Doe</p></div>"
    text = tree.text(deep=True, separator=" ", strip=True)
    assert text == "John Doe"


def test_merge_text_nodes_complex():
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
    tree = LexborHTMLParser(html)
    tree.unwrap_tags(["em", "strong", "span", "b", "i"])
    root = tree.css_first("article", strict=True)
    root.merge_text_nodes()
    assert root.css_first("h1").text() == "Hello World"
    assert root.css_first("p").text() == "This is a test"
    assert "Nested text nodes" in root.css_first("section").text()
    assert root.css_first("section > div").text() == "with more nesting here"


def test_merge_text_nodes_three_plus():
    html = """<div><em>O</em><strong>n</strong><b>e</b> <i>T</i><span>w</span><u>o</u> <small>T</small><big>h</big><mark>r</mark><sub>e</sub><sup>e</sup></div>"""
    tree = LexborHTMLParser(html)
    tree.unwrap_tags(
        ["em", "strong", "b", "i", "span", "u", "small", "big", "mark", "sub", "sup"]
    )
    div = tree.css_first("div", strict=True)
    div.merge_text_nodes()
    assert div.text() == "One Two Three"


def test_merge_text_nodes_visits_every_sibling_subtree():
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
    tree = LexborHTMLParser(html)
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


def test_strip_tags_from_root():
    html = "<body><div></div><script></script></body>"
    html_parser = LexborHTMLParser(html)
    html_parser.root.strip_tags(["div", "script"])
    assert html_parser.html == "<html><head></head><body></body></html>"

    with pytest.raises(TypeError):
        html_parser.strip_tags(1)


def test_decompose_root_node():
    html_parser = LexborHTMLParser("<div><p>test</p></div>")
    with pytest.raises(SelectolaxError):
        html_parser.root.decompose()
