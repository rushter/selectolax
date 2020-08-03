#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from selectolax.parser import HTMLParser

"""
We'are testing only our own code.
Many functionality are already tested in the Modest engine, so there is no reason to test every case.
"""


def test_selector():
    html = "<span></span><div><p id='p3'>text</p></div><p></p>"
    selector = "p#p3"

    for node in HTMLParser(html).css(selector):
        assert node.text() == 'text'
        assert node.tag == 'p'
        assert node.parent.tag == 'div'
        assert node.parent.next.tag == 'p'
        assert node.parent.prev.tag == 'span'
        assert node.parent.last_child.attributes['id'] == 'p3'


def test_css_one():
    html = "<span></span><div><p class='p3'>text</p><p class='p3'>sd</p></div><p></p>"

    selector = ".s3"
    assert HTMLParser(html).css_first(selector) is None

    selector = "p.p3"
    assert HTMLParser(html).css_first(selector).text() == 'text'

    with pytest.raises(ValueError):
        HTMLParser(html).css_first(selector, strict=True)


def test_css_first_default():
    html = "<span></span><div><p class='p3'>text</p><p class='p3'>sd</p></div><p></p>"
    selector = ".s3"
    assert HTMLParser(html).css_first(selector, default='lorem ipsum') == 'lorem ipsum'


def test_attributes():
    html = "<div><p id='p3'>text</p></div>"
    selector = "p#p3"
    for node in HTMLParser(html).css(selector):
        assert 'id' in node.attributes
        assert node.attributes['id'] == 'p3'

    html = "<div><p attr>text</p></div>"
    selector = "p#p3"
    for node in HTMLParser(html).css(selector):
        assert 'attr' in node.attributes
        assert node.attributes['attr'] is None


def test_decompose():
    html = "<body><div><p id='p3'>text</p></div></body>"
    html_parser = HTMLParser(html)

    for node in html_parser.tags('p'):
        node.decompose()

    assert html_parser.body.child.html == '<div></div>'


def test_strip_tags():
    html = "<body><div></div><script></script></body>"
    html_parser = HTMLParser(html)
    html_parser.strip_tags(['div', 'script'])
    assert html_parser.html == '<html><head></head><body></body></html>'

    with pytest.raises(TypeError):
        html_parser.strip_tags(1)


def test_malformed_attributes():
    html = '<div> <meta name="description" content="ÐÐ°Ñ"Ð " /></div>'
    html_parser = HTMLParser(html)

    for tag in html_parser.tags('meta'):
        assert tag


def test_iter_with_text():
    html = """
    <div id="description">
        <h1>Title</h1>
        text
        <div>foo</div>
        <img scr="image.jpg">
    </div>
    """
    html_parser = HTMLParser(html)
    expected_tags = ['-text', 'h1', '-text', 'div', '-text', 'img', '-text']
    actual_tags = [node.tag for node in html_parser.css_first('#description').iter(include_text=True)]
    assert expected_tags == actual_tags


def test_iter_no_text():
    html = """
    <div id="description">
        <h1>Title</h1>
        text
        <div>foo</div>
        <img scr="image.jpg">
    </div>
    """
    html_parser = HTMLParser(html)
    expected_tags = ['h1', 'div','img']
    actual_tags = [node.tag for node in html_parser.css_first('#description').iter(include_text=False)]
    assert expected_tags == actual_tags


def test_node_navigation():
    html = (
        '<div id="parent"><div id="prev"></div><div id="test_node"><h1 id="child">Title</h1>'
        '<div>foo</div><img scr="image.jpg"></div><div id="next"></div></div>'
    )
    html_parser = HTMLParser(html)
    main_node = html_parser.css_first('#test_node')
    assert main_node.prev.id == 'prev'
    assert main_node.next.id == 'next'
    assert main_node.parent.id == 'parent'
    assert main_node.child.id == 'child'


@pytest.mark.parametrize("html,expected", [("<div id='my_node'></div>", 'my_node'), ("<div></div>", None)])
def test_get_node_id(html, expected):
    html_parser = HTMLParser(html)
    node = html_parser.css_first('div')
    assert node.id == expected


def test_html_attribute_works_for_text():
    html = '<div>foo bar</div>'
    html_parser = HTMLParser(html)
    node = html_parser.css_first('div').child
    assert node.html == 'foo bar'


def test_text_node_returns_text():
    html = '<div>foo bar</div>'
    html_parser = HTMLParser(html)
    node = html_parser.css_first('div').child
    assert node.text(deep=False) == 'foo bar'


def test_text_node_returns_text_when_deep():
    html = '<div>foo bar</div>'
    html_parser = HTMLParser(html)
    node = html_parser.css_first('div').child
    assert node.text(deep=True) == 'foo bar'


def test_unwrap():
    html = '<a id="url" href="https://rushter.com/">I linked to <i>rushter.com</i></a>'
    html_parser = HTMLParser(html)
    node = html_parser.css_first('i')
    node.unwrap()
    assert html_parser.body.child.html == '<a id="url" href="https://rushter.com/">I linked to rushter.com</a>'


def test_unwrap_tags():
    html_parser = HTMLParser("<div><a href="">Hello</a> <i>world</i>!</div>")
    html_parser.body.unwrap_tags(['i', 'a'])
    assert html_parser.body.html == '<body><div>Hello world!</div></body>'


def test_unwraps_multiple_child_nodes():
    html = """
    <div id="test">
        foo <span>bar <i>Lor<span>ems</span></i> I <span class='p3'>dummy <div>text</div></span></span>
    </div>
    """
    html_parser = HTMLParser(html)
    html_parser.body.unwrap_tags(['span', 'i'])
    assert html_parser.body.child.html == '<div id="test">\n        foo bar Lorems I dummy <div>text</div>\n    </div>'


def test_replace_with():
    html_parser = HTMLParser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first('img')
    img.replace_with(img.attributes.get('alt', ''))
    assert html_parser.body.child.html == '<div>Get Laptop</div>'


def test_replace_with_multiple_nodes():
    html_parser = HTMLParser('<div>Get <span alt="Laptop"><img src="/jpg"> <div>/div></span></div>')
    img = html_parser.css_first('span')
    img.replace_with(img.attributes.get('alt', ''))
    assert html_parser.body.child.html == '<div>Get Laptop</div>'


def test_node_replace_with():
    html_parser = HTMLParser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
    html_parser2 = HTMLParser('<div>Test</div>')
    img_node = html_parser.css_first('img')
    img_node.replace_with(html_parser2.body.child)
    assert html_parser.body.child.html == '<div>Get <span alt="Laptop"><div>Test</div> <div></div></span></div>'


def test_replace_with_empty_string():
    html_parser = HTMLParser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first('img')
    img.replace_with('')
    assert html_parser.body.child.html == '<div>Get </div>'


def test_replace_with_invalid_value_passed_exception():
    with pytest.raises(TypeError) as excinfo:
        html_parser = HTMLParser('<div>Get <img src="" alt="Laptop"></div>')
        img = html_parser.css_first('img')
        img.replace_with(None)
    assert 'No matching signature found' in str(excinfo.value)


def test_insert_before():
    html_parser = HTMLParser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first('img')
    img.insert_before(img.attributes.get('alt', ''))
    assert html_parser.body.child.html == '<div>Get Laptop<img src="" alt="Laptop"></div>'


def test_node_insert_before():
    html_parser = HTMLParser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
    html_parser2 = HTMLParser('<div>Test</div>')
    img_node = html_parser.css_first('img')
    img_node.insert_before(html_parser2.body.child)
    assert html_parser.body.child.html == '<div>Get <span alt="Laptop"><div>Test</div><img src="/jpg"> <div></div></span></div>'


def test_insert_after():
    html_parser = HTMLParser('<div>Get <img src="" alt="Laptop"></div>')
    img = html_parser.css_first('img')
    img.insert_after(img.attributes.get('alt', ''))
    assert html_parser.body.child.html == '<div>Get <img src="" alt="Laptop">Laptop</div>'


def test_node_insert_after():
    html_parser = HTMLParser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
    html_parser2 = HTMLParser('<div>Test</div>')
    img_node = html_parser.css_first('img')
    img_node.insert_after(html_parser2.body.child)
    assert html_parser.body.child.html == '<div>Get <span alt="Laptop"><img src="/jpg"><div>Test</div> <div></div></span></div>'


def test_attrs_adds_attribute():
    html_parser = HTMLParser('<div id="id"></div>')
    node = html_parser.css_first('div')
    node.attrs['new_att'] = 'new'
    assert node.attributes == {'id': 'id', 'new_att': 'new'}


def test_attrs_sets_attribute():
    html_parser = HTMLParser('<div id="id"></div>')
    node = html_parser.css_first('div')
    node.attrs['id'] = 'new_id'
    assert node.attributes == {'id': 'new_id'}


def test_attrs_removes_attribute():
    html_parser = HTMLParser('<div id="id"></div>')
    node = html_parser.css_first('div')
    del node.attrs['id']
    assert node.attributes == {}


def test_attrs_test_dict_features():
    html_parser = HTMLParser('<div id="id" v data-id="foo"></div>')
    node = html_parser.css_first('div')
    node.attrs['new_att'] = 'new'
    assert list(node.attrs.keys()) == ['id', 'v', 'data-id', 'new_att']
    assert list(node.attrs.values()) == ['id', None, 'foo', 'new']
    assert len(node.attrs) == 4
    assert node.attrs.get('unknown_field', 'default_value') == 'default_value'
    assert 'id' in node.attrs
    assert 'vid' not in node.attrs


def test_traverse():
    html = (
        '<div id="parent"><div id="prev"></div><div id="test_node"><h1 id="child">Title</h1>'
        '<div>foo</div><img scr="image.jpg"></div><div id="next"></div></div>'
    )
    html_parser = HTMLParser(html)
    actual = [node.tag for node in html_parser.root.traverse()]
    expected = ['-undef', 'html', 'head', 'body', 'div', 'div', 'div', 'h1', 'div', 'img', 'div']
    assert actual == expected


def test_traverse_with_text():
    html = (
        '<div id="parent"><div id="prev"></div><div id="test_node"><h1 id="child">Title</h1>'
        '<div>foo</div><img scr="image.jpg"></div><div id="next"></div></div>'
    )
    html_parser = HTMLParser(html)
    actual = [node.tag for node in html_parser.root.traverse(include_text=True)]
    expected = ['-undef', 'html', 'head', 'body', 'div', 'div', 'div', 'h1', '-text', 'div', '-text', 'img', 'div']
    assert actual == expected


def test_node_comparison():
    html = """
        <div>H3ll0</div><div id='tt'><p id='stext'>Lorem ipsum dolor sit amet, ea quo modus meliore platonem.</p></div>
    """
    html_parser = HTMLParser(html)
    nodes = [node for node in html_parser.root.traverse(include_text=False)]
    same_node_path_one = nodes[-1].parent
    same_node_path_two = nodes[-2]
    same_node_path_three = html_parser.css_first('#tt')
    assert same_node_path_one == same_node_path_two == same_node_path_three


def test_node_comprassion_with_strings():
    html = """<div id="test"></div>"""
    html_parser = HTMLParser(html)
    node = html_parser.css_first('#test')
    assert node == '<div id="test"></div>'


def test_node_comparison_fails():
    html = """<div id="test"></div>"""
    html_parser = HTMLParser(html)
    node = html_parser.css_first('#test')

    assert node != None
    assert node != 123
    assert node != object
