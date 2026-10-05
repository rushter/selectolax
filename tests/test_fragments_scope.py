import pytest

from selectolax.lexbor import LexborHTMLParser
from tests.helpers import clean_doc


@pytest.mark.parametrize(
    "html",
    [
        "hello",
        "a<span>s</span>",
        "lead<span>x</span>tail",
        "<div>a</div><span>s</span>",
        "<div><i>x</i>y</div>",
        "a<b>c</b>d",
        "<!--k--><b>c</b>",
        "only text",
        "<div>one</div><div>two</div>",
    ],
)
def test_text_lexbor_covers_whole_fragment(html):
    """``text_lexbor()`` must widen like ``text()`` does on a fragment root."""
    parser = LexborHTMLParser(html, is_fragment=True)
    root = parser.root
    assert root.text_lexbor() == parser.text()
    assert root.text_lexbor() == root.text()


def test_text_does_not_duplicate_fragment_root_text_node():
    parser = LexborHTMLParser("hello", is_fragment=True)
    root = parser.root
    assert root is not None
    assert root.is_text_node
    assert root.text(deep=True) == "hello"


@pytest.mark.parametrize(
    "html, expected_text, expected_deep_false",
    [
        ("hello", "hello", "hello"),
        ("a<span>s</span>", "as", "a"),
        ("lead<span>x</span>tail", "leadxtail", "leadtail"),
        ("a<b>c</b>d", "acd", "ad"),
        ("a<!--k--><b>c</b>", "ac", "a"),
    ],
)
def test_fragment_root_text_node_covers_whole_fragment(
    html, expected_text, expected_deep_false
):
    """A fragment that starts with text must not lose its siblings.

    The root is widened to the wrapper so the walk covers every top-level node,
    which means the root's own data is reached by the walk. It must therefore
    not also be added on the side, or it would be duplicated.
    """
    parser = LexborHTMLParser(html, is_fragment=True)
    root = parser.root
    assert root.is_text_node

    assert root.text() == expected_text
    assert root.text(deep=True) == expected_text
    assert root.text(deep=False) == expected_deep_false
    assert parser.text() == expected_text


@pytest.mark.parametrize(
    "html, query, expected_count",
    [
        ("a<span>s</span><b>b</b>", "span", 1),
        ("a<span>s</span><b>b</b>", "b", 1),
        ("a<span>s</span><b>b</b>", "i", 0),
        ("lead<span>x</span>tail<b>c</b>", "b", 1),
    ],
)
def test_fragment_root_text_node_css_covers_whole_fragment(html, query, expected_count):
    """Tree walks from a text-node fragment root reach every top-level node."""
    parser = LexborHTMLParser(html, is_fragment=True)
    root = parser.root
    assert root.is_text_node

    assert len(root.css(query)) == expected_count
    assert len(root.select(query).matches) == expected_count
    assert root.css_matches(query) is (expected_count > 0)
    assert root.any_css_matches((query,)) is (expected_count > 0)
    assert (root.css_first(query) is not None) is (expected_count > 0)


def test_fragment_root_text_node_iter_covers_whole_fragment():
    parser = LexborHTMLParser("a<span>s</span><b>b</b>", is_fragment=True)
    root = parser.root
    assert root.is_text_node

    assert [node.tag for node in root.iter()] == ["span", "b"]
    assert [node.tag for node in root.iter(include_text=True)] == [
        "-text",
        "span",
        "b",
    ]


def test_fragment_root_html_serialization():
    html = "<div>Hello</div><span>World</span>"
    p = LexborHTMLParser(html, is_fragment=True)
    assert p.root.html == "<div>Hello</div><span>World</span>"
    p.root.insert_child("!")
    assert p.html == "<div>Hello!</div><span>World</span>"


def test_fragment_root_html_pretty_serialization():
    html = "<div><span>Hello</span></div>\n<span>World</span>"
    p = LexborHTMLParser(html, is_fragment=True)
    assert p.root.html_pretty(skip_ws_nodes=True) == clean_doc(
        """
        <div>
          <span>
            "Hello"
          </span>
        </div>
        <span>
          "World"
        </span>
        """
    )
    assert p.html_pretty(skip_ws_nodes=True) == clean_doc(
        """
        <div>
          <span>
            "Hello"
          </span>
        </div>
        <span>
          "World"
        </span>
        """
    )


def test_fragment_tags_covers_whole_fragment():
    # Lexbor never links a fragment's wrapper element into the document's child
    # list, so a lookup rooted at the document used to return nothing at all.
    html = "<div><p>a</p></div><div><p>b</p></div><span>c</span>"
    parser = LexborHTMLParser(html, is_fragment=True)

    assert [node.html for node in parser.tags("div")] == [
        "<div><p>a</p></div>",
        "<div><p>b</p></div>",
    ]
    assert [node.html for node in parser.tags("p")] == ["<p>a</p>", "<p>b</p>"]
    assert len(parser.tags("*")) == 5
    assert parser.tags("table") == []
    assert parser.tags("html") == []  # the wrapper is not part of the fragment


def test_fragment_tags_follows_mutations():
    parser = LexborHTMLParser("<div><b>a</b></div><u>b</u>", is_fragment=True)
    assert len(parser.tags("b")) == 1

    parser.root.unwrap()
    assert len(parser.tags("b")) == 1

    parser.css_first("b").decompose()
    assert parser.tags("b") == []


def test_parser_strip_tags_covers_whole_fragment():
    # Same root cause as tags(): the collection was rooted at the document, so
    # strip_tags() silently removed nothing from a fragment.
    parser = LexborHTMLParser(
        "<script>a</script><div><script>b</script><p>c</p></div>", is_fragment=True
    )
    parser.strip_tags(["script"], recursive=True)

    assert parser.html == "<div><p>c</p></div>"

    parser.strip_tags(["div"])
    assert parser.html == "" and parser.root is None


def test_attached_fragment_root_still_covers_every_top_level_node():
    """Tree walks from an attached fragment root must widen to its siblings."""
    parser = LexborHTMLParser("<div>a</div><p>b</p><i>c</i>", is_fragment=True)
    root = parser.root
    assert root.tag == "div"

    assert root.text() == "abc"
    assert len(root.css("p")) == 1
    assert root.css_matches("i") is True
    assert [node.tag for node in root.iter()] == ["div", "p", "i"]
    assert len(root.select("i").matches) == 1


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda node: node.unwrap(), id="unwrap"),
        pytest.param(lambda node: node.decompose(), id="decompose"),
        pytest.param(lambda node: node.remove(), id="remove"),
        pytest.param(lambda node: node.replace_with("X"), id="replace_with"),
        pytest.param(lambda node: node.strip_tags(["div"]), id="strip_tags"),
        pytest.param(
            lambda node: node.decompose(recursive=False), id="decompose_shallow"
        ),
    ],
)
def test_detached_fragment_root_does_not_crash(mutate):
    """Every tree walk from a detached fragment root must stay in bounds.

    Tree walks start at ``_get_node()``, which used to hand back ``None`` once
    the root lost its parent, and the callers dereferenced it unconditionally.
    """
    parser = LexborHTMLParser("<div>a<span>s</span></div><p>b</p>", is_fragment=True)
    root = parser.root
    mutate(root)

    # The detached node stands in for itself: only its own subtree is walked.
    assert root.text() in ("", "a" + "s")
    assert root.css("span") is not None
    assert root.css_first("span") is None or root.css_first("span").tag == "span"
    assert isinstance(root.css_matches("div"), bool)
    assert isinstance(root.any_css_matches(("div", "span")), bool)
    assert isinstance(list(root.iter()), list)
    assert isinstance(list(root.iter(include_text=True)), list)
    assert isinstance(root.select("span").matches, list)
    assert root.text_content is None or isinstance(root.text_content, str)


def test_detached_fragment_root_reports_its_own_subtree():
    parser = LexborHTMLParser("<div>a<span>s</span></div>", is_fragment=True)
    root = parser.root
    root.unwrap()

    # unwrap() lifts the children out of the root, leaving it empty and
    # detached; the fragment itself keeps them.
    assert root.text() == ""
    assert root.css("span") == []
    assert list(root.iter()) == []
    assert root.parent is None
    assert parser.html == "a<span>s</span>"


def test_detached_fragment_root_can_be_decomposed_repeatedly():
    parser = LexborHTMLParser("<div>a</div>", is_fragment=True)
    root = parser.root

    root.decompose()
    root.decompose()
    root.unwrap()

    assert root.text() == ""
    # Match-root is on, so a walk from a detached node still matches the node
    # itself -- just nothing below it.
    assert [node.tag for node in root.css("div")] == ["div"]
    assert root.css("span") == []


def test_detached_non_fragment_node_tree_walks_are_unaffected():
    parser = LexborHTMLParser("<div><p>a</p></div><div>b</div>")
    div = parser.css_first("div")
    div.decompose()

    assert div.text() == ""
    assert div.css("p") == []
    assert div.parent is None


def test_fragment_text_extraction_multiple_nodes():
    html = "<p>1</p><p>2</p>"
    p = LexborHTMLParser(html, is_fragment=True)
    assert p.text(deep=False) == ""
    assert p.text(deep=True, separator=" ", strip=True) == "1 2"


def test_fragment_iter_multiple_nodes():
    html = "<p>1</p><p>2</p>"
    p = LexborHTMLParser(html, is_fragment=True)
    assert len(list(p.root.iter())) == 2


@pytest.mark.parametrize(
    "html",
    [
        "<div><b>x</b></div><p>z</p>",
        "<div><b>x</b></div>",
        "text<span>s</span>",
        "<!--c--><p>z</p>",
        "<style>a{}</style><p>z</p>",
    ],
)
def test_fragment_inner_html_covers_every_top_level_node(html):
    tree = LexborHTMLParser(html, is_fragment=True)
    assert tree.inner_html == tree.html


def test_fragment_inner_html_setter_replaces_every_top_level_node():
    tree = LexborHTMLParser("<div><b>x</b></div><p>z</p>", is_fragment=True)
    tree.inner_html = "<i>new</i>"
    assert tree.html == "<i>new</i>"
    assert tree.css("b") == []
    assert tree.css("p") == []


@pytest.mark.parametrize("html", ["text<span>s</span>", "<!--c--><p>z</p>"])
def test_fragment_inner_html_setter_accepts_non_element_first_node(html):
    tree = LexborHTMLParser(html, is_fragment=True)
    tree.inner_html = "<p>new</p>"
    assert tree.html == "<p>new</p>"


def test_fragment_inner_html_setter_uses_the_fragment_context():
    tree = LexborHTMLParser("<style>a{}</style><p>z</p>", is_fragment=True)
    tree.inner_html = "<td>cell</td>"
    assert tree.html == "cell"
    assert tree.css("style") == []

    table = LexborHTMLParser(
        "<td>a</td><td>b</td>", is_fragment=True, fragment_tag="td"
    )
    table.inner_html = "<td>new</td>"
    assert (
        table.html
        == LexborHTMLParser("<td>new</td>", is_fragment=True, fragment_tag="td").html
    )


def test_fragment_inner_html_setter_is_idempotent():
    tree = LexborHTMLParser("<div><b>x</b></div><p>z</p>", is_fragment=True)
    tree.inner_html = "<td>cell</td>"
    once = tree.html
    tree.inner_html = "<td>cell</td>"
    assert tree.html == once


def test_fragment_inner_html_setter_leaves_replaced_nodes_readable():
    tree = LexborHTMLParser("<div><b>old</b></div><p>z</p>", is_fragment=True)
    old = tree.css_first("b")
    tree.inner_html = "<p>new</p>"
    assert old.html == "<b>old</b>"
    assert tree.html == "<p>new</p>"


def test_fragment_inner_html_setter_invalidates_derived_caches():
    tree = LexborHTMLParser(
        '<div><script src="a.js">old</script></div>', is_fragment=True
    )
    assert tree.script_srcs_contain(("a.js",)) is True
    tree.inner_html = '<div><script src="b.js">new</script></div>'
    assert tree.script_srcs_contain(("a.js",)) is False
    assert tree.script_srcs_contain(("b.js",)) is True
    assert tree.scripts_contain("new") is True
    assert tree.scripts_contain("old") is False


def test_non_empty_fragment_queries_still_work():
    """The root guard must not shadow normal results."""
    tree = LexborHTMLParser(
        "<div><p>a</p><script src='x.js'>y</script></div>", is_fragment=True
    )
    assert tree.root is not None
    assert len(tree.css("div")) == 1
    assert tree.css_first("p").text() == "a"
    assert tree.css_matches("p") is True
    assert tree.css_matches("table") is False
    assert tree.any_css_matches(("table", "p")) is True
    assert tree.scripts_contain("y") is True
    assert tree.script_srcs_contain(("x.js",)) is True
    assert tree.inner_html == tree.html


def test_full_document_queries_still_work():
    """A full document always has a root, so behaviour must be unchanged."""
    tree = LexborHTMLParser("<div><p>hi</p></div>")
    assert tree.root is not None
    assert len(tree.css("p")) == 1
    assert tree.css_first("p").text() == "hi"
    assert tree.css_first("table") is None
    assert tree.css_first("table", default="d") == "d"
    assert tree.css_matches("p") is True
    assert tree.any_css_matches(("p",)) is True
    assert tree.scripts_contain("nope") is False
    assert tree.merge_text_nodes() is None
    assert tree.inner_html == "<head></head><body><div><p>hi</p></div></body>"


def test_fragment_root_match_helpers_use_the_same_scope_as_css():
    """Regression test: the match helpers searched the wrong subtree.

    ``css`` evaluates a fragment root against the whole fragment, via the
    fragment wrapper, but ``css_matches``/``any_css_matches`` were handed the
    root element itself. They therefore missed matches that ``css`` returned
    whenever the match sat outside the first top-level node.
    """
    tree = LexborHTMLParser("<div>x</div><p>sibling</p>", is_fragment=True)
    root = tree.root

    assert [node.html for node in root.css("p")] == ["<p>sibling</p>"]
    assert root.css_matches("p") is True
    assert root.any_css_matches(("p",)) is True
    assert root.any_css_matches(("table", "p")) is True

    # Also reachable through the parser, which delegates to the root node.
    assert [node.html for node in tree.css("p")] == ["<p>sibling</p>"]
    assert tree.css_matches("p") is True
    assert tree.any_css_matches(("table", "p")) is True


def test_fragment_root_match_helpers_still_reject_absent_selectors():
    """Widening the scope must not turn non-matches into matches."""
    tree = LexborHTMLParser("<div>x</div><p>sibling</p>", is_fragment=True)
    root = tree.root

    assert root.css_matches("table") is False
    assert root.any_css_matches(("table",)) is False
    assert root.any_css_matches(("table", "section")) is False
    # `p` is not a child of `div`, it is a sibling of it
    assert root.css_matches("div > p") is False
    # the root node itself and its own subtree are still reachable
    assert root.css_matches("div") is True


@pytest.mark.parametrize(
    "method, args", [("css_matches", ("p",)), ("any_css_matches", (("p",),))]
)
def test_match_helpers_agree_for_non_fragment_nodes(method, args):
    """Only fragment roots change scope; ordinary nodes keep matching their subtree."""
    tree = LexborHTMLParser('<div id="a"><p>x</p><span>s</span></div>')
    div = tree.css_first("div")

    assert getattr(div, method)(*args) is True
    assert (
        getattr(div, method)(
            *(("table",) if method == "css_matches" else (("table",),))
        )
        is False
    )

    assert getattr(tree.root, method)(*args) is True
    assert getattr(tree.body, method)(*args) is True


def test_fragment_wrapper_is_never_reported_by_css():
    """Regression test: Lexbor's internal fragment wrapper escaped every query.

    A fragment's top-level nodes are reached through the ``<html>`` wrapper that
    Lexbor builds to hold them, and ``MATCH_ROOT`` makes the search root a
    candidate for every query. The wrapper therefore showed up in results --
    ``css('html')`` answered with it and ``css('*')`` listed it as if it were
    part of the fragment.
    """
    tree = LexborHTMLParser("<div>a</div><p>b</p>", is_fragment=True)

    assert tree.css("html") == []
    assert tree.css_first("html") is None
    assert tree.css_first("html", default="fallback") == "fallback"
    assert tree.css("html, body, head") == []
    assert [node.tag for node in tree.css("*")] == ["div", "p"]
    assert [node.html for node in tree.css("*")] == [
        "<div>a</div>",
        "<p>b</p>",
    ]
    # The same must hold for a query rooted at the node rather than the parser.
    assert tree.root.css("html") == []
    assert [node.tag for node in tree.root.css("*")] == ["div", "p"]
    # ...and through the selector wrapper, which roots the search itself.
    assert tree.select("html").matches == []


def test_fragment_wrapper_does_not_count_as_a_match():
    """The wrapper must not make a selector report a match on the fragment."""
    tree = LexborHTMLParser("<div>a</div>", is_fragment=True)

    assert tree.css_matches("html") is False
    assert tree.css_matches("body") is False
    assert tree.any_css_matches(("html",)) is False
    assert tree.any_css_matches(("table", "html")) is False
    # A real node in the same query still matches.
    assert tree.any_css_matches(("html", "div")) is True
    assert tree.root.css_matches("html") is False
    assert tree.root.any_css_matches(("html",)) is False


def test_fragment_wrapper_cannot_be_reached_and_destroyed():
    """Regression test: acting on the leaked wrapper discarded the fragment.

    The wrapper owns the whole fragment, so it was returned first by ``css('*')``
    and decomposing the first match removed nodes the caller had never selected.
    Selecting one node must now affect only that node's subtree.
    """
    tree = LexborHTMLParser("<div><b>gone</b></div><p>kept</p>", is_fragment=True)

    first = tree.css_first("*")
    assert first is not None and first.html == "<div><b>gone</b></div>"

    first.decompose()

    assert tree.root is not None
    assert tree.root.html == "<p>kept</p>"
    assert tree.html == "<p>kept</p>"


def test_fragment_wrapper_is_not_reported_by_parent():
    """A fragment's internal wrapper is not a parent a caller can act on."""
    tree = LexborHTMLParser("<div><span>a</span></div><p>b</p>", is_fragment=True)

    assert tree.root.parent is None
    assert tree.css_first("p").parent is None
    assert tree.css_first("span").parent.tag == "div"
    assert tree.css_first("span").parent.parent is None

    text_root = LexborHTMLParser("a<span>s</span>", is_fragment=True).root
    assert text_root.is_text_node
    assert text_root.parent is None

    assert tree.html == "<div><span>a</span></div><p>b</p>"


def test_unqueried_select_answers_with_the_node_itself():
    """An unqueried selector answers with the node, not the fragment wrapper."""
    tree = LexborHTMLParser("<div>a</div><p>b</p>", is_fragment=True)

    assert [node.tag for node in tree.root.select().matches] == ["div"]
    assert [node.tag for node in tree.css_first("p").select().matches] == ["p"]
    assert [node.tag for node in tree.select().matches] == ["div"]
    assert [node.tag for node in tree.root.select("*").matches] == ["div", "p"]


def test_full_document_still_reports_its_html_element():
    """Only a fragment's wrapper is internal; a real ``<html>`` still matches."""
    tree = LexborHTMLParser("<div>x</div>")

    assert [node.html for node in tree.css("html")] == [
        "<html><head></head><body><div>x</div></body></html>"
    ]
    assert [node.tag for node in tree.css("*")] == ["html", "head", "body", "div"]
    assert tree.css_matches("html") is True
    assert tree.any_css_matches(("html",)) is True
    assert [node.tag for node in tree.select("html").matches] == ["html"]


def test_fragment_script_lookups_cover_every_top_level_node():
    """Regression test: scripts outside the first top-level node were missed.

    The lookup is rooted at the fragment's scope, so a script nested in a later
    top-level node has to be found too.
    """
    tree = LexborHTMLParser(
        "<script>first</script><div><script>second</script></div>", is_fragment=True
    )

    assert tree.scripts_contain("first") is True
    assert tree.scripts_contain("second") is True
    assert tree.scripts_contain("third") is False

    sources = LexborHTMLParser(
        '<script src="/a.js"></script><div><script src="/b.js"></script></div>',
        is_fragment=True,
    )

    assert sources.script_srcs_contain(("/b.js",)) is True
    assert sources.script_srcs_contain(("/a.js",)) is True
    assert sources.script_srcs_contain(("/c.js",)) is False


def test_fragment_script_lookups_stay_scoped_to_the_node_they_are_called_on():
    tree = LexborHTMLParser(
        "<div><script>inside</script></div><script>outside</script>",
        is_fragment=True,
    )
    div = tree.css_first("div")

    assert div.scripts_contain("inside") is True
    assert div.scripts_contain("outside") is False
    assert tree.scripts_contain("outside") is True


def test_fragment_select_searches_the_same_scope_as_css():
    """Regression test: ``select()`` only looked at the first top-level node."""
    tree = LexborHTMLParser(
        '<div>a</div><p class="t">b</p><span class="t">c</span>', is_fragment=True
    )

    assert [node.tag for node in tree.select(".t").matches] == ["p", "span"]
    assert [node.tag for node in tree.select(".t").matches] == [
        node.tag for node in tree.css(".t")
    ]
    # An unqueried selector is still rooted at the fragment root itself.
    assert [node.tag for node in tree.select().matches] == ["div"]


def test_fragment_traverse_covers_every_top_level_node():
    """Regression test: ``traverse()`` stopped after the first top-level node."""
    tree = LexborHTMLParser("<div>a</div><p>b</p><span>c</span>", is_fragment=True)

    assert [node.tag for node in tree.root.traverse()] == ["div", "p", "span"]
    assert [node.tag for node in tree.root.traverse()] == [
        node.tag for node in tree.root.iter()
    ]
    assert [
        (node.tag, node.text_content) for node in tree.root.traverse(include_text=True)
    ] == [
        ("div", None),
        ("-text", "a"),
        ("p", None),
        ("-text", "b"),
        ("span", None),
        ("-text", "c"),
    ]


def test_fragment_traverse_covers_a_fragment_starting_with_text():
    """Regression test: such a fragment yielded nothing at all."""
    tree = LexborHTMLParser("one<div>two</div>three", is_fragment=True)

    assert [node.tag for node in tree.root.traverse(include_text=True)] == [
        "-text",
        "div",
        "-text",
        "-text",
    ]
    assert [node.tag for node in tree.root.traverse()] == ["div"]


def test_traverse_of_a_detached_fragment_root_is_unchanged():
    """A detached root stands for itself again, so it covers only its subtree."""
    tree = LexborHTMLParser("<div><span>a</span></div><p>b</p>", is_fragment=True)
    root = tree.root
    root.unwrap()

    # The span was moved out of the div, which is what unwrapping does.
    assert tree.html == "<span>a</span><p>b</p>"
    assert [node.tag for node in root.traverse()] == ["div"]
    assert [node.tag for node in tree.root.traverse()] == ["span", "p"]


def test_script_lookups_on_a_detached_fragment_root_are_scoped_to_it():
    """A detached root stands for itself again, so it no longer covers the fragment."""
    tree = LexborHTMLParser(
        "<div><script>inside</script></div><script>outside</script>", is_fragment=True
    )
    root = tree.root
    root.unwrap()

    assert root.scripts_contain("inside") is False
    assert root.scripts_contain("outside") is False
    assert tree.scripts_contain("inside") is True
    assert tree.scripts_contain("outside") is True


def test_fragment_traverse_survives_nodes_being_removed_during_iteration():
    """A removed node must not end the walk, like it does not in ``iter()``."""
    tree = LexborHTMLParser(
        "<div>a</div><p>b</p><span>c</span><b>d</b>", is_fragment=True
    )

    seen = []
    for node in tree.root.traverse():
        seen.append(node.tag)
        node.decompose()

    assert seen == ["div", "p", "span", "b"]
    assert tree.html == ""
