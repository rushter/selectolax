import pytest

from selectolax.lexbor import LexborHTMLParser

_TEXT_ASSEMBLY_CASES = [
    "<div>a<span>b</span>c</div>",
    "<div><span>  x  </span><span>\t y \n</span></div>",
]

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
    # test_text_does_not_duplicate_fragment_root_text_node in test_fragments_scope.py.
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


def test_text_lexbor_on_empty_strings():
    parser = LexborHTMLParser("<div></div>")
    div = parser.css_first("div")
    assert div is not None
    assert div.text_lexbor() == ""

    parser = LexborHTMLParser("<div><p></p><p>foo</p></div>")
    div = parser.css_first("div")
    assert div is not None
    assert div.text_lexbor() == "foo"

    parser = LexborHTMLParser("")
    assert parser.root.text_lexbor() == ""


def test_text_lexbor_on_a_text_node_reports_only_itself():
    """Widening must not make a text node report its siblings too."""
    parser = LexborHTMLParser("<div>hi</div><p>yo</p>")
    for tag, expected in (("div", "hi"), ("p", "yo")):
        text_node = parser.css_first(tag).first_child
        assert text_node.is_text_node
        assert text_node.text_lexbor() == expected


def test_text_node_fragment_root_text_node_owns_its_own_data():
    """A text node that is not a fragment root only reports itself."""
    parser = LexborHTMLParser("<div>hi</div><p>yo</p>")
    for tag in ("div", "p"):
        text_node = parser.css_first(tag).first_child
        assert text_node.is_text_node
        assert text_node.text() == text_node.text_content
        assert text_node.text(deep=True) == text_node.text_content
        assert text_node.text(deep=False) == text_node.text_content
    assert parser.css_first("div").first_child.text_content == "hi"
    assert parser.css_first("p").first_child.text_content == "yo"


def test_is_empty_text_node_property():
    parser = LexborHTMLParser("<div><span>\n \n</span><title>X</title></div>")
    text_node = parser.css_first("span").first_child
    assert text_node.text_content == "\n \n"
    assert text_node.is_empty_text_node
    text_node = parser.css_first("title").first_child
    assert text_node.text_content == "X"
    assert not text_node.is_empty_text_node


def test_fragment_text_extraction():
    html = "<div>Hello <strong>World</strong>!</div>"
    p = LexborHTMLParser(html, is_fragment=True)
    div = p.root.css_first("div")
    assert div.text() == "Hello World!"
    assert div.text(deep=True, separator=" ", strip=True) == "Hello World !"


def test_fragment_text_content():
    html = "<div>Hello</div>"
    parser = LexborHTMLParser(html, is_fragment=True)
    text_node = parser.root.first_child
    assert text_node.text_content == "Hello"
    assert parser.root.text_content is None


def test_text_when_html_is_empty():
    html_parser = LexborHTMLParser("")

    assert html_parser.text() == ""


def test_text_deep_gh61():
    html = """<div>this is a test <h1>Heading</h1></div>"""
    output = []
    tree = LexborHTMLParser(html)
    for node in tree.root.traverse(include_text=True):
        if node.tag == "-text":
            text = node.text(deep=True)
            if text:
                output.append(text)
    assert output == ["this is a test ", "Heading"]


def test_text_node_returns_text():
    html = "<div>foo bar</div>"
    html_parser = LexborHTMLParser(html)
    node = html_parser.css_first("div").child
    assert node.text(deep=False) == "foo bar"


def test_text_node_returns_text_parent():
    html = "<div>foo bar</div>"
    html_parser = LexborHTMLParser(html)
    node = html_parser.css_first("div")
    assert node.text(deep=False) == "foo bar"


def test_content_method():
    html = """
    <div>
        <div id="main">SuperTest</div>
    </div>
    """
    tree = LexborHTMLParser(html)
    assert tree.css_first("#main").child.text_content == "SuperTest"
    assert tree.css_first("#main").text_content is None


def test_text_separator_correctness():
    inner = "".join(f"<span>word{i}</span>" for i in range(50))
    html = f"<div>{inner}</div>"
    tree = LexborHTMLParser(html)
    node = tree.css_first("div")

    result = node.text(deep=True, separator=" ")
    parts = result.split(" ")

    assert parts[-1] != "", "Trailing separator found; join() not used correctly"
    assert len(parts) == 50
    for i, part in enumerate(parts):
        assert part == f"word{i}"


def test_text_strip_and_separator():
    html = "<div><p>  hello  </p><p>  world  </p></div>"
    tree = LexborHTMLParser(html)
    node = tree.css_first("div")

    result = node.text(deep=True, separator="|", strip=True)
    assert result == "hello|world"


@pytest.mark.parametrize(
    "html,selector,is_fragment,deep,separator,strip,skip_empty,expected",
    _TEXT_EXPECTED_CASES,
)
def test_text_expected_value(
    html, selector, is_fragment, deep, separator, strip, skip_empty, expected
):
    """Pin text() to literal expected strings."""
    node = LexborHTMLParser(html, is_fragment=is_fragment).root
    assert node is not None
    if selector is not None:
        node = node.css_first(selector)
        assert node is not None, f"selector {selector!r} not found in {html!r}"
    assert (
        node.text(deep=deep, separator=separator, strip=strip, skip_empty=skip_empty)
        == expected
    )


@pytest.mark.parametrize("html", _TEXT_ASSEMBLY_CASES)
@pytest.mark.parametrize("is_fragment", [False, True])
@pytest.mark.parametrize("deep", [True, False])
@pytest.mark.parametrize("separator", ["", "|"])
@pytest.mark.parametrize("strip", [True, False])
@pytest.mark.parametrize("skip_empty", [True, False])
def test_text_matches_join_of_parts(
    html, is_fragment, deep, separator, strip, skip_empty
):
    """Every combination of text() options must equal ``separator.join(parts)``."""
    tree = LexborHTMLParser(html, is_fragment=is_fragment)
    node = tree.root
    if node is None:
        pytest.skip("empty fragment has no root")
    expected = _reference_text(node, deep, separator, strip, skip_empty)
    assert (
        node.text(deep=deep, separator=separator, strip=strip, skip_empty=skip_empty)
        == expected
    )


def test_text_replaces_undecodable_bytes_instead_of_raising():
    """text() substitutes U+FFFD rather than raising, on both paths."""
    node = LexborHTMLParser(b"<div>\xff\xfe bad \x80bytes</div>").css_first("div")
    for kwargs in ({}, {"deep": False}, {"strip": True}, {"separator": "|"}):
        result = node.text(**kwargs)
        assert isinstance(result, str)
        assert "bad" in result
        assert "\ufffd" in result


def test_text_content_exact_for_text_nodes():
    """text_content returns this node's own characters verbatim."""
    tree = LexborHTMLParser("<div>Super<b>Test</b></div>")
    child = tree.css_first("div").child
    assert child.is_text_node
    assert child.text_content == "Super"
    assert tree.css_first("b").text_content is None
    assert tree.css_first("div").text_content is None


def test_text_and_text_lexbor_agree():
    tree = LexborHTMLParser("<div>a<span>b</span>c</div>")
    node = tree.css_first("div")
    assert node.text() == node.text_lexbor()
    assert tree.root.text() == tree.root.text_lexbor()
