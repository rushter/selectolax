from selectolax.lexbor import LexborHTMLParser

_SCRIPT_LOOKUP_HTML = (
    "<div id='a'><script>alpha</script><script src='alpha.js'></script></div>"
    "<div id='b'><script>beta</script><script src='beta.js'></script></div>"
)


def test_script_contain():
    html_parser = LexborHTMLParser("""
    <script>
     var super_value = 100;
    </script>
    """)
    assert html_parser.scripts_contain("super_value")


def test_srcs_contain():
    html_parser = LexborHTMLParser(
        """<script src="http://google.com/analytics.js"></script>"""
    )
    assert html_parser.script_srcs_contain(("analytics.js",))


def test_scripts_contain_is_scoped_to_the_node_it_is_called_on():
    """Regression test: the cache lived on the parser but the search is per node.

    Both nodes live in one document and therefore shared one cache, so the
    second node answered with the first node's result.
    """
    tree = LexborHTMLParser(_SCRIPT_LOOKUP_HTML)
    a, b = tree.css_first("#a"), tree.css_first("#b")

    assert a.scripts_contain("alpha") is True
    assert b.scripts_contain("alpha") is False
    assert b.scripts_contain("beta") is True
    assert a.scripts_contain("beta") is False


def test_script_srcs_contain_is_scoped_to_the_node_it_is_called_on():
    tree = LexborHTMLParser(_SCRIPT_LOOKUP_HTML)
    a, b = tree.css_first("#a"), tree.css_first("#b")

    assert a.script_srcs_contain(("alpha.js",)) is True
    assert b.script_srcs_contain(("alpha.js",)) is False
    assert b.script_srcs_contain(("beta.js",)) is True
    assert a.script_srcs_contain(("beta.js",)) is False


def test_script_lookup_does_not_depend_on_which_node_was_asked_first():
    """The wrong answer must not depend on the order the scopes were queried."""
    tree = LexborHTMLParser(_SCRIPT_LOOKUP_HTML)
    b, a = tree.css_first("#b"), tree.css_first("#a")

    assert b.scripts_contain("alpha") is False
    assert a.scripts_contain("alpha") is True
    assert b.script_srcs_contain(("alpha.js",)) is False
    assert a.script_srcs_contain(("alpha.js",)) is True


def test_script_contain_sees_inserted_content():
    """Regression test: the cache was never invalidated after a mutation."""
    tree = LexborHTMLParser("<div><script>a()</script></div>")
    assert tree.scripts_contain("evil") is False

    tree.css_first("script").insert_child("evil")
    assert tree.scripts_contain("evil") is True


def test_script_contain_stops_seeing_removed_content():
    tree = LexborHTMLParser("<div><script>evil()</script></div>")
    assert tree.scripts_contain("evil") is True

    tree.css_first("script").decompose()
    assert tree.scripts_contain("evil") is False

    tree = LexborHTMLParser("<div><script>evil()</script></div>")
    assert tree.scripts_contain("evil") is True
    tree.css_first("script").unwrap()
    assert tree.scripts_contain("evil") is False

    tree = LexborHTMLParser("<div><script>evil()</script></div>")
    assert tree.scripts_contain("evil") is True
    tree.css_first("script").replace_with("nothing to see")
    assert tree.scripts_contain("evil") is False

    tree = LexborHTMLParser("<div><script>evil()</script></div>")
    assert tree.scripts_contain("evil") is True
    tree.strip_tags(["div"], recursive=True)
    assert tree.scripts_contain("evil") is False

    tree = LexborHTMLParser("<div><script>evil()</script></div>")
    assert tree.scripts_contain("evil") is True
    tree.css_first("div").inner_html = "<span>clean</span>"
    assert tree.scripts_contain("evil") is False


def test_script_srcs_contain_sees_attribute_changes():
    """A changed ``src`` invalidates the lookup even though the node survives."""
    tree = LexborHTMLParser("<script src='keep.js'></script>")
    assert tree.script_srcs_contain(("gone.js",)) is False

    tree.css_first("script").attrs["src"] = "gone.js"
    assert tree.script_srcs_contain(("gone.js",)) is True

    del tree.css_first("script").attrs["src"]
    assert tree.script_srcs_contain(("gone.js",)) is False

    tree = LexborHTMLParser("<script src='gone.js'></script>")
    assert tree.script_srcs_contain(("gone.js",)) is True
    tree.css_first("script").attrs["src"] = None
    assert tree.script_srcs_contain(("gone.js",)) is False


def test_script_contain_still_caches_for_the_whole_document():
    """The cache is a performance feature, so it must survive repeated calls."""
    tree = LexborHTMLParser(
        "<div id='a'><script>alpha</script></div>"
        "<div id='b'><script>beta</script></div>"
    )

    for _ in range(3):
        assert tree.scripts_contain("alpha") is True
        assert tree.scripts_contain("beta") is True
        assert tree.script_srcs_contain(("gone.js",)) is False
        assert tree.css_first("#a").scripts_contain("alpha") is True
        assert tree.css_first("#b").scripts_contain("alpha") is False
