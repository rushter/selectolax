import pytest

from selectolax.lexbor import LexborHTMLParser
from tests.helpers import clean_doc


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


def test_html_pretty_document():
    parser = LexborHTMLParser("<div><span>Hello</span><!-- note --></div>")
    assert parser.html_pretty() == clean_doc(
        """
        <html>
          <head>
          </head>
          <body>
            <div>
              <span>
                "Hello"
              </span>
              <!--  note  -->
            </div>
          </body>
        </html>
        """
    )


def test_html_pretty_node_with_options():
    parser = LexborHTMLParser("<div><span>Hello</span><!-- note --></div>")
    node = parser.css_first("div")
    assert node.html_pretty(skip_comment=True) == clean_doc(
        """
        <div>
          <span>
            "Hello"
          </span>
        </div>
        """
    )


def test_html_pretty_skip_ws_nodes_option():
    parser = LexborHTMLParser("<div>\n</div><span></span>", is_fragment=True)
    assert parser.html_pretty(skip_ws_nodes=True) == clean_doc(
        """
        <div>
        </div>
        <span>
        </span>
        """
    )


def test_inner_html_pretty_node_with_options():
    parser = LexborHTMLParser("<div><span>Hello</span><!-- note --></div>")
    node = parser.css_first("div")
    assert node.inner_html_pretty(skip_comment=True) == clean_doc(
        """
        <span>
          "Hello"
        </span>
        """
    )


def test_inner_html_pretty_parser():
    parser = LexborHTMLParser("<div><span>Hello</span></div>", is_fragment=True)
    assert parser.inner_html_pretty(skip_ws_nodes=True) == clean_doc(
        """
        <div>
          <span>
            "Hello"
          </span>
        </div>
        """
    )


def test_html_pretty_rejects_negative_indent():
    parser = LexborHTMLParser("<div>Hello</div>")
    with pytest.raises(ValueError):
        parser.html_pretty(indent=-1)


def test_inner_html_pretty_rejects_negative_indent():
    parser = LexborHTMLParser("<div>Hello</div>")
    with pytest.raises(ValueError):
        parser.inner_html_pretty(indent=-1)


def test_inner_html_setter_rejects_non_element_nodes():
    """Regression test: lexbor grafts children onto any node type.

    Assigning ``inner_html`` on a text or comment node used to attach element
    children to it, leaving the node with a type that no longer matches its
    contents. Every accessor then disagreed: ``.html`` included the injected
    markup, ``.text(deep=True)`` counted it as text, but ``.text_content``,
    ``.text(deep=False)`` and ``.text_lexbor()`` ignored it.
    """
    parser = LexborHTMLParser("<div>hello<p>world</p><!--note--></div>")
    div = parser.css_first("div")
    non_elements = [
        node for node in div.iter(include_text=True) if not node.is_element_node
    ]
    assert [node.tag for node in non_elements] == ["-text", "-comment"]

    before = parser.html
    for node in non_elements:
        with pytest.raises(TypeError, match="element nodes"):
            node.inner_html = "<b>injected</b>"

    assert parser.html == before


def test_inner_html_setter_rejects_document_node():
    parser = LexborHTMLParser("<div>hi</div>")
    document = parser.css_first("div").parent.parent.parent
    assert document is not None
    assert document.is_document_node

    before = parser.html
    with pytest.raises(TypeError, match="element nodes"):
        document.inner_html = "<b>injected</b>"

    assert parser.html == before


def test_sets_inner_html_on_html_keeps_head_and_body_in_sync():
    """Regression test: parser.head/parser.body used to dangle.

    ``lxb_html_element_inner_html_set`` replaces the children of ``<html>``
    directly, bypassing the insertion modes that normally populate the
    document's cached head/body pointers. Those pointers then referenced
    destroyed nodes while ``parser.html`` walked the live tree, so the two
    disagreed about the same document.
    """
    parser = LexborHTMLParser(
        "<html><head><title>Title</title></head><body><div>hi</div></body></html>"
    )
    parser.root.inner_html = "<main>new</main>"

    assert parser.html == "<html><head></head><body><main>new</main></body></html>"
    assert parser.head is not None
    assert parser.body is not None
    assert parser.head.tag == "head"
    assert parser.body.tag == "body"
    assert parser.head.html == "<head></head>"
    assert parser.body.html == "<body><main>new</main></body>"
    assert parser.body.text() == "new"


def test_head_and_body_survive_allocations_after_inner_html():
    """Regression test: the stale pointers aliased recycled memory.

    Destroyed lexbor blocks go back onto a size-keyed free list
    (``lexbor_mraw_free``), so the next same-size allocation is handed the very
    same address. Before the fix, ``parser.body`` ended up pointing at an
    unrelated live ``<span>`` created after the assignment.
    """
    parser = LexborHTMLParser(
        "<html><head><title>Title</title></head><body><div>hi</div></body></html>"
    )
    parser.root.inner_html = "<main>new</main>"

    head, body = parser.head, parser.body
    assert head is not None
    assert body is not None

    for _ in range(50):
        allocated = parser.create_node("span")
        assert allocated.mem_id != head.mem_id
        assert allocated.mem_id != body.mem_id

    assert parser.head.tag == "head"
    assert parser.body.tag == "body"
    assert parser.body.text() == "new"


@pytest.mark.parametrize("target", ["head", "body"])
def test_sets_inner_html_on_head_or_body_keeps_pointers_valid(target: str):
    """Only ``<html>`` loses its head/body children, so only it needs a refresh."""
    parser = LexborHTMLParser(
        "<html><head><title>Title</title></head><body><div>hi</div></body></html>"
    )
    node = parser.css_first(target)
    assert node is not None
    node.inner_html = "<meta charset='utf-8'>"

    head, body = parser.head, parser.body
    assert head is not None
    assert body is not None
    assert head.tag == "head"
    assert body.tag == "body"

    if target == "head":
        assert head.html == '<head><meta charset="utf-8"></head>'
        assert body.html == "<body><div>hi</div></body>"
    else:
        assert head.html == "<head><title>Title</title></head>"
        assert body.html == '<body><meta charset="utf-8"></body>'


def test_sets_inner_html_on_nested_element_keeps_head_and_body():
    parser = LexborHTMLParser(
        "<html><head><title>Title</title></head><body><div>hi</div></body></html>"
    )
    parser.css_first("div").inner_html = "<span>new</span>"

    assert parser.head is not None
    assert parser.body is not None
    assert parser.head.html == "<head><title>Title</title></head>"
    assert parser.body.html == "<body><div><span>new</span></div></body>"


def test_sets_inner_html_on_fragment_root_leaves_head_and_body_absent():
    parser = LexborHTMLParser("<div>hi</div>", is_fragment=True)
    assert parser.head is None
    assert parser.body is None

    parser.root.inner_html = "<span>new</span>"

    assert parser.head is None
    assert parser.body is None


def test_fragment_inner_html():
    html = "<div><span>Hello</span><p>World</p></div>"
    p = LexborHTMLParser(html, is_fragment=True)
    div = p.root.css_first("div")
    assert div.inner_html == "<span>Hello</span><p>World</p>"
    div.inner_html = "<em>New</em> content"
    assert div.html == "<div><em>New</em> content</div>"


def test_document_inner_html_is_unaffected_by_fragment_semantics():
    tree = LexborHTMLParser("<!DOCTYPE html><div>a</div><p>b</p>")
    assert tree.inner_html == "<head></head><body><div>a</div><p>b</p></body>"
    tree.inner_html = "<span>c</span>"
    assert tree.html == (
        "<!DOCTYPE html><html><head></head><body><span>c</span></body></html>"
    )


def test_html_property():
    html = "<body>Hi there</body>"
    html_parser = LexborHTMLParser(html)
    assert html_parser.body.child.html == "Hi there"


def test_html_attribute_works_for_text():
    html = "<div>foo bar</div>"
    html_parser = LexborHTMLParser(html)
    node = html_parser.css_first("div").child
    assert node.html == "foo bar"


def test_set_inner_html_leaves_replaced_nodes_readable():
    """Nodes from the replaced subtree stay intact instead of reading freed memory."""
    tree = LexborHTMLParser("<html><body><div id='a'><em>x</em></div></body></html>")
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


def test_set_inner_html_recycled_addresses_do_not_alias():
    """A retained node keeps its identity even after its address is handed out again."""
    tree = LexborHTMLParser("<html><body><div id='a'><p>orig</p></div></body></html>")
    old_div = tree.css_first("#a")

    tree.body.inner_html = "<em>replacement</em>"
    for _ in range(500):
        tree.create_node("z")

    assert old_div.html == '<div id="a"><p>orig</p></div>'
    assert tree.body.inner_html == "<em>replacement</em>"


def test_set_inner_html_on_a_detached_node_leaves_the_document_alone():
    """Writing through a detached node must not corrupt the tree it came from."""
    tree = LexborHTMLParser("<html><body><div id='a'><p>x</p></div></body></html>")
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
    # 5 structural nodes (html/head/body/em/section) + 200 <i> children.
    assert len(list(tree.root.traverse())) == 205
