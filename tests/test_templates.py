from selectolax.lexbor import LexborHTMLParser


def test_template_content_is_not_part_of_the_document_tree():
    tree = LexborHTMLParser(
        "<div id='w'><template id='t'><b class='in'>x</b></template></div>"
    )
    template = tree.css_first("template")

    assert tree.css(".in") == []
    assert template.inner_html == ""
    assert template.first_child is None
    assert list(template.iter()) == []
    # Only the serializer descends into the fragment the content lives in.
    assert '<b class="in">x</b>' in tree.html


def test_template_fragments_returns_the_content():
    tree = LexborHTMLParser("<template id='t'><b class='in'>x</b></template>")
    fragment = tree.template_fragments()[0]

    assert fragment.html == '<b class="in">x</b>'
    assert fragment.css(".in") == [fragment.css_first(".in")]
    assert fragment.text() == "x"
    assert [node.tag for node in fragment.iter()] == ["b"]


def test_template_fragments_is_empty_without_templates():
    assert LexborHTMLParser("<div>x</div>").template_fragments() == []


def test_template_fragments_is_ordered_and_covers_every_template():
    tree = LexborHTMLParser(
        "<template id='a'>1</template><template id='b'>2</template><template id='c'>3</template>"
    )

    assert [f.parent.attributes["id"] for f in tree.template_fragments()] == [
        "a",
        "b",
        "c",
    ]


def test_template_fragments_covers_an_empty_template():
    tree = LexborHTMLParser("<template id='a'></template>")

    assert len(tree.template_fragments()) == 1
    assert tree.template_fragments()[0].html == ""


def test_template_fragments_is_scoped_to_the_node_it_is_called_on():
    tree = LexborHTMLParser(
        "<template id='a'><b class='first'>1</b></template>"
        "<template id='b'><i class='second'>2</i></template>"
    )
    fragment = tree.css_first("template").template_fragments()[0]

    assert fragment.css(".first")
    assert fragment.css(".second") == []


def test_template_fragments_on_a_node_without_templates():
    tree = LexborHTMLParser("<template><b>1</b></template><div id='d'>2</div>")

    assert tree.css_first("#d").template_fragments() == []


def test_template_content_parent_is_the_template():
    tree = LexborHTMLParser("<div><template id='t'><b>x</b></template></div>")
    template = tree.css_first("template")

    assert tree.template_fragments()[0].parent == template
    assert template.parent == tree.css_first("div")


def test_template_content_first_and_last_child():
    tree = LexborHTMLParser("<template><b>1</b><i>2</i></template>")
    fragment = tree.template_fragments()[0]

    assert fragment.first_child == fragment.css("b")[0]
    assert fragment.last_child == fragment.css("i")[0]


def test_template_content_iteration_covers_every_top_level_node():
    tree = LexborHTMLParser("<template><b>1</b>text<i>2</i></template>")
    fragment = tree.template_fragments()[0]

    assert [n.tag for n in fragment.iter()] == ["b", "i"]
    assert [n.tag for n in fragment.iter(include_text=True)] == ["b", "-text", "i"]
    assert [n.tag for n in fragment.traverse()] == ["b", "i"]
    # Depth-first, so the text inside <b> precedes the text between the tags.
    assert [n.tag for n in fragment.traverse(include_text=True)] == [
        "b",
        "-text",
        "-text",
        "i",
        "-text",
    ]


def test_template_content_reports_no_children_once_decomposed():
    tree = LexborHTMLParser("<template><b>1</b></template>")
    fragment = tree.template_fragments()[0]
    fragment.css_first("b").decompose()

    assert fragment.html == ""
    assert fragment.css("b") == []


def test_template_content_is_a_view_of_the_document():
    tree = LexborHTMLParser("<template id='t'><b class='in'>x</b></template>")
    fragment = tree.template_fragments()[0]
    fragment.css_first(".in").attrs["class"] = "changed"

    assert '<b class="changed">x</b>' in tree.html
    assert fragment.css(".changed")


def test_template_content_insert_is_visible_in_the_document():
    tree = LexborHTMLParser("<template id='t'></template>")
    fragment = tree.template_fragments()[0]
    holder = LexborHTMLParser("<b class='new'>x</b>")
    fragment.insert_child(holder.css_first("b"))

    assert '<template id="t"><b class="new">x</b></template>' in tree.html
    assert fragment.css(".new")


def test_template_content_serialization():
    tree = LexborHTMLParser("<template><!--c--><b>1</b><i>2</i></template>")
    fragment = tree.template_fragments()[0]
    pretty = fragment.html_pretty()

    assert fragment.html == "<!--c--><b>1</b><i>2</i>"
    assert fragment.inner_html == "<!--c--><b>1</b><i>2</i>"
    assert pretty == '<!-- c -->\n<b>\n  "1"\n</b>\n<i>\n  "2"\n</i>\n'
    assert fragment.text() == "12"


def test_template_content_serializes_to_the_content_the_template_holds():
    tree = LexborHTMLParser("<template id='t'><b>1</b></template>")
    fragment = tree.template_fragments()[0]

    assert fragment.html == "<b>1</b>"
    assert fragment.html in tree.html


def test_nested_template_content_is_reachable_from_the_outer_fragment():
    tree = LexborHTMLParser(
        "<template id='outer'><p>x<template id='inner'><b>y</b></template></p></template>"
    )
    outer = tree.template_fragments()[0]

    assert len(tree.template_fragments()) == 1
    assert outer.template_fragments()[0].html == "<b>y</b>"
    assert outer.template_fragments()[0].parent.attributes["id"] == "inner"


def test_svg_template_is_an_ordinary_element_and_is_not_reported():
    tree = LexborHTMLParser("<svg><template><circle/></template></svg>")
    template = tree.css_first("template")

    assert tree.template_fragments() == []
    assert template.css("circle")
    assert template.inner_html == "<circle></circle>"


def test_template_content_from_a_fragment_parser():
    tree = LexborHTMLParser(
        "<template><b class='in'>x</b></template><p>y</p>", is_fragment=True
    )

    assert tree.css(".in") == []
    assert tree.template_fragments()[0].css(".in")


def test_template_content_in_a_deeply_nested_template():
    depth = 200
    tree = LexborHTMLParser(
        f"<template>{'<div>' * depth}x{'</div>' * depth}</template>"
    )

    assert len(tree.template_fragments()[0].css("div")) == depth


def test_template_content_holds_scripts():
    tree = LexborHTMLParser("<template><script>var x = 'y';</script></template>")
    fragment = tree.template_fragments()[0]

    assert fragment.scripts_contain("var x")
    # The script is outside the document tree, so a document-wide lookup misses
    # it, exactly as it misses the markup around it.
    assert not tree.scripts_contain("var x")
    assert not tree.css_first("template").scripts_contain("var x")


def test_template_element_itself_is_unchanged():
    tree = LexborHTMLParser("<template id='t' class='c'><b>1</b></template>")
    template = tree.css_first("template")

    assert template.attributes == {"id": "t", "class": "c"}
    assert template.tag == "template"
    assert template.text() == ""
    assert tree.html == (
        '<html><head><template id="t" class="c"><b>1</b></template></head><body></body></html>'
    )


def test_template_content_view_outlives_the_template_element():
    tree = LexborHTMLParser("<div id='w'><template><b>x</b></template></div>")
    fragment = tree.template_fragments()[0]
    tree.css_first("template").decompose()

    assert tree.css_first("#w").inner_html == ""
    assert fragment.html == "<b>x</b>"


def test_template_content_search_does_not_affect_later_document_searches():
    tree = LexborHTMLParser(
        "<template><b class='in'>1</b></template><div class='out'>2</div>"
    )
    fragment = tree.template_fragments()[0]

    for _ in range(3):
        assert [n.attributes.get("class") for n in fragment.css("*")] == ["in"]
        assert [n.attributes.get("class") for n in tree.css("*")] == [
            None,
            None,
            None,
            None,
            "out",
        ]
        assert fragment.css_matches("b")
        assert tree.css_matches("div")


def test_template_content_matching_is_scoped_to_the_fragment():
    tree = LexborHTMLParser("<template><b class='in'>1</b></template>")
    fragment = tree.template_fragments()[0]

    assert fragment.css_matches(".in")
    assert not tree.css_matches(".in")


def test_repeated_template_fragments_are_the_same_node():
    tree = LexborHTMLParser("<template><b>x</b></template>")
    first = tree.template_fragments()[0]
    second = tree.template_fragments()[0]

    assert first == second
    assert hash(first) == hash(second)
    assert first.css_first("b") == second.css_first("b")


def test_template_content_unwrap():
    tree = LexborHTMLParser("<template><div><span>keep</span></div></template>")
    tree.template_fragments()[0].css_first("div").unwrap()

    assert tree.html == (
        "<html><head><template><span>keep</span></template></head><body></body></html>"
    )
