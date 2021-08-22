#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from selectolax.parser import HTMLParser
from selectolax.lexbor import LexborHTMLParser

"""
We'are testing only our own code.
Many functionality are already tested in the Modest engine, so there is no reason to test every case.
"""

_PARSERS_PARAMETRIZER = ("parser", (HTMLParser, LexborHTMLParser),)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_selector(parser):
    html = "<span></span><div><p id='p3'>text</p></div><p></p>"
    selector = "p#p3"

    for node in parser(html).css(selector):
        assert node.text() == 'text'
        assert node.tag == 'p'
        assert node.parent.tag == 'div'
        assert node.parent.next.tag == 'p'
        assert node.parent.prev.tag == 'span'
        assert node.parent.last_child.attributes['id'] == 'p3'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_css_multiple_matches(parser):
    html = "<div></div><div></div><div></div>"
    assert len(parser(html).css('div')) == 3


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_css_matches(parser):
    html = "<div></div><div></div><div></div>"
    assert parser(html).css_matches('div')


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_any_css_matches(parser):
    html = "<div></div><span></span><div></div>"
    assert parser(html).any_css_matches(('h1', 'span'))


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_css_one(parser):
    html = "<span></span><div><p class='p3'>text</p><p class='p3'>sd</p></div><p></p>"

    selector = ".s3"
    assert parser(html).css_first(selector) is None

    selector = "p.p3"
    assert parser(html).css_first(selector).text() == 'text'

    with pytest.raises(ValueError):
        parser(html).css_first(selector, strict=True)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_css_first_default(parser):
    html = "<span></span><div><p class='p3'>text</p><p class='p3'>sd</p></div><p></p>"
    selector = ".s3"
    assert parser(html).css_first(selector, default='lorem ipsum') == 'lorem ipsum'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_id_property(parser):
    html = "<p id='main_text'>text</p>"
    assert parser(html).css_first('p').id == 'main_text'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_tag_property(parser):
    html = "<h1>text</h1>"
    assert parser(html).css_first('h1').tag == 'h1'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attributes(parser):
    html = "<div><p id='p3'>text</p></div>"
    selector = "p#p3"
    for node in parser(html).css(selector):
        assert 'id' in node.attributes
        assert node.attributes['id'] == 'p3'

    html = "<div><p attr>text</p></div>"
    selector = "p#p3"
    for node in HTMLParser(html).css(selector):
        assert 'attr' in node.attributes
        assert node.attributes['attr'] is None


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_decompose(parser):
    html = "<body><div><p id='p3'>text</p></div></body>"
    html_parser = parser(html)

    for node in html_parser.tags('p'):
        node.decompose()
    assert html_parser.body.child.html == '<div></div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_html_property(parser):
    html = "<body>Hi there</body>"
    html_parser = parser(html)
    assert html_parser.body.child.html == 'Hi there'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_root_property(parser):
    html = "<body>Hi there</body>"
    html_parser = parser(html)
    assert html_parser.root.html == '<html><head></head><body>Hi there</body></html>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_head_property(parser):
    html = """
    <html lang="en">
        <head><title>rushter.com</title></head>
        <body></body>
    </html>
    """
    html_parser = parser(html)
    assert html_parser.head.html == '<head><title>rushter.com</title></head>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_body_property(parser):
    html = "<body>Hi there</body>"
    html_parser = parser(html)
    assert html_parser.body.html == '<body>Hi there</body>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_strip_tags(parser):
    html = "<body><div></div><script></script></body>"
    html_parser = parser(html)
    html_parser.root.strip_tags(['div', 'script'])
    assert html_parser.html == '<html><head></head><body></body></html>'

    with pytest.raises(TypeError):
        html_parser.strip_tags(1)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_malformed_attributes(parser):
    html = '<div> <meta name="description" content="ÐÐ°Ñ"Ð " /></div>'
    html_parser = parser(html)

    for tag in html_parser.tags('meta'):
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
    expected_tags = ['-text', 'h1', '-text', 'div', '-text', 'img', '-text']
    actual_tags = [node.tag for node in html_parser.css_first('#description').iter(include_text=True)]
    assert expected_tags == actual_tags


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
    expected_tags = ['h1', 'div', 'img']
    actual_tags = [node.tag for node in html_parser.css_first('#description').iter(include_text=False)]
    assert expected_tags == actual_tags


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_navigation(parser):
    html = (
        '<div id="parent"><div id="prev"></div><div id="test_node"><h1 id="child">Title</h1>'
        '<div>foo</div><img scr="image.jpg"></div><div id="next"></div></div>'
    )
    html_parser = parser(html)
    main_node = html_parser.css_first('#test_node')
    assert main_node.prev.id == 'prev'
    assert main_node.next.id == 'next'
    assert main_node.parent.id == 'parent'
    assert main_node.child.id == 'child'


@pytest.mark.parametrize("html,expected, parser", [
    ("<div id='my_node'></div>", 'my_node', HTMLParser),
    ("<div></div>", None, HTMLParser),
    ("<div id='my_node'></div>", 'my_node', LexborHTMLParser),
    ("<div></div>", None, LexborHTMLParser),
])
def test_get_node_id(html, expected, parser):
    html_parser = parser(html)
    node = html_parser.css_first('div')
    assert node.id == expected


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_html_attribute_works_for_text(parser):
    html = '<div>foo bar</div>'
    html_parser = parser(html)
    node = html_parser.css_first('div').child
    assert node.html == 'foo bar'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_text_node_returns_text(parser):
    html = '<div>foo bar</div>'
    html_parser = parser(html)
    node = html_parser.css_first('div').child
    assert node.text(deep=False) == 'foo bar'


def test_text_node_returns_text_when_deep():
    html = '<div>foo bar</div>'
    html_parser = HTMLParser(html)
    node = html_parser.css_first('div').child
    assert node.text(deep=True) == 'foo bar'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_unwrap(parser):
    html = '<a id="url" href="https://rushter.com/">I linked to <i>rushter.com</i></a>'
    html_parser = parser(html)
    node = html_parser.css_first('i')
    node.unwrap()
    assert html_parser.body.child.html == '<a id="url" href="https://rushter.com/">I linked to rushter.com</a>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_unwrap_tags(parser):
    html_parser = parser("<div><a href="">Hello</a> <i>world</i>!</div>")
    html_parser.body.unwrap_tags(['i', 'a'])
    assert html_parser.body.html == '<body><div>Hello world!</div></body>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_unwraps_multiple_child_nodes(parser):
    html = """
    <div id="test">
        foo <span>bar <i>Lor<span>ems</span></i> I <span class='p3'>dummy <div>text</div></span></span>
    </div>
    """
    html_parser = parser(html)
    html_parser.body.unwrap_tags(['span', 'i'])
    assert html_parser.body.child.html == '<div id="test">\n        foo bar Lorems I dummy <div>text</div>\n    </div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_replace_with(parser):
    html_parser = parser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first('img')
    img.replace_with(img.attributes.get('alt', ''))
    assert html_parser.body.child.html == '<div>Get Laptop</div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_replace_with_multiple_nodes(parser):
    html_parser = parser('<div>Get <span alt="Laptop"><img src="/jpg"> <div>/div></span></div>')
    img = html_parser.css_first('span')
    img.replace_with(img.attributes.get('alt', ''))
    assert html_parser.body.child.html == '<div>Get Laptop</div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_replace_with(parser):
    html_parser = parser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
    html_parser2 = parser('<div>Test</div>')
    img_node = html_parser.css_first('img')
    img_node.replace_with(html_parser2.body.child)
    assert html_parser.body.child.html == '<div>Get <span alt="Laptop"><div>Test</div> <div></div></span></div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_replace_with_empty_string(parser):
    html_parser = parser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first('img')
    img.replace_with('')
    assert html_parser.body.child.html == '<div>Get </div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_replace_with_invalid_value_passed_exception(parser):
    with pytest.raises(TypeError) as excinfo:
        html_parser = parser('<div>Get <img src="" alt="Laptop"></div>')
        img = html_parser.css_first('img')
        img.replace_with(None)
    assert 'No matching signature found' in str(excinfo.value)


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_insert_before(parser):
    html_parser = parser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first('img')
    img.insert_before(img.attributes.get('alt', ''))
    assert html_parser.body.child.html == '<div>Get Laptop<img src="" alt="Laptop"></div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_insert_before(parser):
    html_parser = parser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
    html_parser2 = parser('<div>Test</div>')
    img_node = html_parser.css_first('img')
    img_node.insert_before(html_parser2.body.child)
    assert html_parser.body.child.html == '<div>Get <span alt="Laptop"><div>Test</div><img src="/jpg"> <div></div></span></div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_insert_after(parser):
    html_parser = parser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first('img')
    img.insert_after(img.attributes.get('alt', ''))
    assert html_parser.body.child.html == '<div>Get <img src="" alt="Laptop">Laptop</div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_insert_after(parser):
    html_parser = parser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
    html_parser2 = parser('<div>Test</div>')
    img_node = html_parser.css_first('img')
    img_node.insert_after(html_parser2.body.child)
    assert html_parser.body.child.html == '<div>Get <span alt="Laptop"><img src="/jpg"><div>Test</div> <div></div></span></div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_adds_attribute(parser):
    html_parser = parser('<div id="id"></div>')
    node = html_parser.css_first('div')
    node.attrs['new_att'] = 'new'
    assert node.attributes == {'id': 'id', 'new_att': 'new'}


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_sets_attribute(parser):
    html_parser = parser('<div id="id"></div>')
    node = html_parser.css_first('div')
    node.attrs['id'] = 'new_id'
    assert node.attributes == {'id': 'new_id'}


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_removes_attribute(parser):
    html_parser = parser('<div id="id"></div>')
    node = html_parser.css_first('div')
    del node.attrs['id']
    assert node.attributes == {}


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_attrs_test_dict_features(parser):
    html_parser = parser('<div id="id" v data-id="foo"></div>')
    node = html_parser.css_first('div')
    node.attrs['new_att'] = 'new'
    assert list(node.attrs.keys()) == ['id', 'v', 'data-id', 'new_att']
    assert list(node.attrs.values()) == ['id', None, 'foo', 'new']
    assert len(node.attrs) == 4
    assert node.attrs.get('unknown_field', 'default_value') == 'default_value'
    assert 'id' in node.attrs
    assert 'vid' not in node.attrs


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_traverse(parser):
    html = (
        '<div id="parent"><div id="prev"></div><div id="test_node"><h1 id="child">Title</h1>'
        '<div>foo</div><img scr="image.jpg"></div><div id="next"></div></div>'
    )
    html_parser = parser(html)
    actual = [node.tag for node in html_parser.root.traverse()]
    expected = ['html', 'head', 'body', 'div', 'div', 'div', 'h1', 'div', 'img', 'div']
    assert actual == expected


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_traverse_with_text(parser):
    html = (
        '<div id="parent"><div id="prev"></div><div id="test_node"><h1 id="child">Title</h1>'
        '<div>foo</div><img scr="image.jpg"></div><div id="next"></div></div>'
    )
    html_parser = parser(html)
    actual = [node.tag for node in html_parser.root.traverse(include_text=True)]
    expected = ['html', 'head', 'body', 'div', 'div', 'div', 'h1', '-text', 'div', '-text', 'img', 'div']
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
    same_node_path_three = html_parser.css_first('#tt')
    assert same_node_path_one == same_node_path_two == same_node_path_three


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_comprassion_with_strings(parser):
    html = """<div id="test"></div>"""
    html_parser = parser(html)
    node = html_parser.css_first('#test')
    assert node == '<div id="test"></div>'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_node_comparison_fails(parser):
    html = """<div id="test"></div>"""
    html_parser = parser(html)
    node = html_parser.css_first('#test')

    assert node != None
    assert node != 123
    assert node != object


def test_raw_value():
    html_parser = HTMLParser('<div>&#x3C;test&#x3E;</div>')
    selector = html_parser.css_first('div')
    assert selector.child.raw_value == b'&#x3C;test&#x3E;'
    assert selector.child.html == '&lt;test&gt;'


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_adavanced_selector(parser):
    html_parser = parser("""
    <script>
     var super_value = 100;
    </script>
    
    """)
    selector = html_parser.select('script').text_contains("super_value")
    assert selector.any_matches


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_script_contain(parser):
    html_parser = parser("""
    <script>
     var super_value = 100;
    </script>
    
    """)
    assert html_parser.scripts_contain('super_value')


@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
def test_srcs_contain(parser):
    html_parser = parser("""<script src="http://google.com/analytics.js"></script>""")
    assert html_parser.script_srcs_contain(('analytics.js', ))


@pytest.mark.parametrize("parser", (HTMLParser, ))
def test_css_chaining(parser):
    html = """
    <span class="red"></span>
    <div id="container">
        <span class="red"></span>
        <span class="green"></span>
        <span class="red"></span>
        <span class="green"></span>
    </div>
    <span class="red"></span>
    """
    tree = parser(html)
    assert len(tree.select('div').css("span").css(".red").matches) == 2


@pytest.mark.parametrize("parser", (HTMLParser, ))
def test_css_chaining_two(parser):
    html = """
    <script  integrity="sha512-DHpNaMnQ8GaECHElNcJkpGhIThksyXA==" type="application/javascript" class="weird_script">
        var counter = 10;
    </script>
    """
    tree = parser(html)
    query = (
        tree.select('script').text_contains('var counter = ').css(".weird_script")
        .attribute_longer_than("integrity", 25)
    )
    assert query
