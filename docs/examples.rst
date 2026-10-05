Examples
========

This page contains simple examples of how to use Selectolax for HTML parsing and manipulation.

.. note::
   All examples use the Lexbor backend (``from selectolax.lexbor import LexborHTMLParser``).

Basic HTML Parsing
------------------

There are 3 ways to create or parse objects in Selectolax:

1. Parse HTML as a full document using ``LexborHTMLParser()``
2. Parse HTML as a fragment using ``LexborHTMLParser(..., is_fragment=True)``
3. Create single node using ``LexborHTMLParser(...).create_node()``

- ``LexborHTMLParser()`` - Returns the HTML tree as parsed by Lexbor, unmodified. The HTML is assumed to be a full document. ``<html>``, ``<head>``, and ``<body>`` tags are added if missing.

- ``LexborHTMLParser(..., is_fragment=True)`` - Intended for HTML fragments/partials.
    Behaves the same way as `DocumentFragment` in browsers.
    Drops ``<html>``, ``<head>``, and ``<body>`` tags if present in the input HTML.
    Use it to parse snippets of HTML that are not complete documents.


.. code-block:: python

    from selectolax.lexbor import LexborHTMLParser

    html = """
    <body>
        <span id="vspan"></span>
        <h1>Welcome to selectolax tutorial</h1>
        <div id="text">
            <p class='p3' style='display:none;'>Excepteur <i>sint</i> occaecat cupidatat non proident</p>
            <p class='p3' vid>Lorem ipsum</p>
        </div>
        <div>
            <p id='stext'>Lorem ipsum dolor sit amet, ea quo modus meliore platonem.</p>
        </div>
    </body>
    """

    fragment = """
    <div>
        <p class="p3">
            Hello there!
        </p>
    </div>
    <script>
        document.querySelector(".p3").addEventListener("click", () => { ... });
    </script>
    """

    # Parse HTML as a full document
    parser = LexborHTMLParser(html)

    # Parse HTML as a fragment
    frag_parser = LexborHTMLParser(fragment, is_fragment=True)

    # Create a new node for  `parser`.
    node = parser.create_node("div")

    # A document has the wrappers the Standard requires...
    print(parser.head is not None, parser.body is not None)

    # ...a fragment has neither, yet searches still reach every top-level node.
    print(frag_parser.head, frag_parser.body)
    print([n.tag for n in frag_parser.css('p, script')])

**Output:**

.. code-block:: text

    True True
    None None
    ['p', 'script']

Serializing each parser shows the difference in what the wrappers do:

.. code-block:: text

    >>> parser.html
    '<html><head></head><body>...</body></html>'

    >>> frag_parser.html
    '<div>\n    <p class="p3">\n        Hello there!\n    </p>\n</div>\n<script>\n    ...\n</script>\n'

Because a fragment is not a document it has no ``<body>``, so read it through
``parser.html``, ``parser.text()`` or a search such as ``parser.css()`` rather
than through ``parser.body``.

Parsing Bytes
-------------

Pass ``encoding=True`` when your input is ``bytes`` that may not be UTF-8.
Without it, bytes are parsed as UTF-8 and any encoding declaration in the
document is ignored.

.. code-block:: python

    from selectolax.lexbor import LexborHTMLParser

    raw = '<meta charset="windows-1251"><p>Привет</p>'.encode("windows-1251")

    # Without encoding=True the declaration means nothing.
    print(LexborHTMLParser(raw).text())

    # With it, the declared encoding is detected and transcoded to UTF-8 first.
    print(LexborHTMLParser(raw, encoding=True).text())

**Output:**

.. code-block:: text


    Привет

Detection follows the HTML Standard. A byte-order mark wins over any
declaration, and both ``<meta charset>`` and
``<meta http-equiv="content-type" content="...charset=...">`` are honoured, but
only within the first 1024 bytes of the stream, which is where the Standard
stops looking. Bytes that are invalid in the detected encoding become U+FFFD.

Input that declares nothing is decoded as UTF-8, not as the windows-1252 a
browser would fall back to, so turning this on cannot reinterpret a document
that already parsed correctly.

``str`` input is never affected: a ``str`` is already decoded, so there is
nothing to detect.

Document Options
----------------

By default the parser applies the mutation events that the HTML Standard
defines, so the tree it builds is the one a browser would build.
``LexborDocumentOptions.WO_EVENTS`` turns those side effects off and leaves the
tree as close to the source as possible, which is what you want when
round-tripping HTML or diffing markup between two documents.

.. code-block:: python

    from selectolax.lexbor import LexborHTMLParser, LexborDocumentOptions

    html = "<select><selectedcontent></selectedcontent><option>this gets cloned</option></select>"

    # The Standard has <selectedcontent> mirror the selected <option>'s content,
    # so the parser clones it into place.
    print(LexborHTMLParser(html).css_first("selectedcontent").html)

    # Without events, the element keeps whatever the source actually contained.
    options = LexborDocumentOptions.WO_EVENTS
    parser = LexborHTMLParser(html, options=options)
    print(parser.css_first("selectedcontent").html)

    # The options in effect are readable back from the parser.
    print(parser.options == options)

**Output:**

.. code-block:: text

    <selectedcontent>this gets cloned</selectedcontent>
    <selectedcontent></selectedcontent>
    True

Several flags can be combined with the bitwise OR operator, or by passing the
equivalent plain integer:

.. code-block:: python

    options = LexborDocumentOptions.WO_EVENTS | LexborDocumentOptions.UNDEF

CSS Selectors
-------------

Select All Elements with CSS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Find all paragraph elements with class 'p3' and examine their properties.

.. code-block:: python

    from selectolax.lexbor import LexborHTMLParser

    html = """
    <body>
        <div id="text">
            <p class='p3' style='display:none;'>Excepteur <i>sint</i> occaecat cupidatat non proident</p>
            <p class='p3' vid>Lorem ipsum</p>
        </div>
        <div>
            <p id='stext'>Lorem ipsum dolor sit amet, ea quo modus meliore platonem.</p>
        </div>
    </body>
    """

    parser = LexborHTMLParser(html)
    selector = "p.p3"

    for node in parser.css(selector):
        print('---------------------')
        print('Node: %s' % node.html)
        print('attributes: %s' % node.attributes)
        print('node text: %s' % node.text(deep=True, separator='', strip=False))
        print('tag: %s' % node.tag)
        print('parent tag: %s' % node.parent.tag)
        if node.last_child:
            print('last child inside current node: %s' % node.last_child.html)
        print('---------------------\n')

**Output:**

.. code-block:: text

    ---------------------
    Node: <p class='p3' style='display:none;'>Excepteur <i>sint</i> occaecat cupidatat non proident</p>
    attributes: {'class': 'p3', 'style': 'display:none;'}
    node text: Excepteur sint occaecat cupidatat non proident
    tag: p
    parent tag: div
    last child inside current node: Excepteur <i>sint</i> occaecat cupidatat non proident
    ---------------------

    ---------------------
    Node: <p class='p3' vid>Lorem ipsum</p>
    attributes: {'class': 'p3', 'vid': ''}
    node text: Lorem ipsum
    tag: p
    parent tag: div
    last child inside current node: Lorem ipsum
    ---------------------

Select First Match
~~~~~~~~~~~~~~~~~~

Get the first matching element using CSS selectors.

.. code-block:: python

    parser = LexborHTMLParser(html)

    # Get first h1 element
    print("H1: %s" % parser.css_first('h1').text())

**Output:**

.. code-block:: text

    H1: Welcome to selectolax tutorial

Default Return Values
~~~~~~~~~~~~~~~~~~~~~

Handle cases where no elements match your selector by providing a default value.

.. code-block:: python

    # Return default value if no matches found
    print("Title: %s" % parser.css_first('title', default='not-found'))

**Output:**

.. code-block:: text

    Title: not-found

Strict Mode
~~~~~~~~~~~

Ensure exactly one match exists, otherwise raise an error.

.. code-block:: python

    # This will raise an error if multiple matches are found
    try:
        result = parser.css_first("p.p3", default='not-found', strict=True)
    except Exception as e:
        print(f"Error: {e}")

**Output:**

.. code-block:: text

    ValueError: Expected 1 match, but found 2 matches

HTML manipulation
-----------------

Getting HTML data back
~~~~~~~~~~~~~~~~~~~~~~

You can get HTML data back using `.html` or `.inner_html` properties.
They can be called on any node.

.. code-block:: python

    from selectolax.lexbor import LexborHTMLParser
    html = """
    <div id="main">
      <div>Hi there</div>
      <div id="updated">2021-08-15</div>
     </div>
    """
    parser = LexborHTMLParser(html)
    node = parser.css_first("#main")
    print("Inner html:\n")
    print(node.inner_html)
    print("\nOuter html:\n")
    print(node.html)

**Output:**

.. code-block:: text

    Inner html:

      <div>Hi there</div>
      <div id="updated">2021-08-15</div>

    Outer html:

    <div id="main">
      <div>Hi there</div>
      <div id="updated">2021-08-15</div>
     </div>


Changing HTML
~~~~~~~~~~~~~~

You can also change HTML by setting the `.inner_html` property.

.. code-block:: python

    from selectolax.lexbor import LexborHTMLParser
    html = """
    <div id="main">
      <div>Hi there</div>
     </div>
    """
    parser = LexborHTMLParser(html)
    node = parser.css_first("#main")
    print("Old html:\n")
    print(node.html)

    node.inner_html = "<span>Test</span>"
    print("\nNew html:\n")
    print(node.inner_html)

**Output:**

    Old html:

    <div id="main">
    <div>Hi there</div>
    </div>

    New html:

    <div id="main"><span>Test</span></div>


DOM Navigation
--------------

Parent Elements
~~~~~~~~~~~~~~~

Get parent element in the DOM tree.

.. code-block:: python

    # Print parent of p#stext
    print(parser.css_first('p#stext').parent.html)

**Output:**

.. code-block:: text

    <div>
            <p id='stext'>Lorem ipsum dolor sit amet, ea quo modus meliore platonem.</p>
        </div>

Nested Selectors
~~~~~~~~~~~~~~~~

Chain CSS selectors to find nested elements.

.. code-block:: python

    # Chain CSS selectors
    result = parser.css_first('div#text').css_first('p:nth-child(2)').html
    print(result)

**Output:**

.. code-block:: text

    <p class='p3' vid>Lorem ipsum</p>

Iterating Over Child Nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Walk all child nodes of an element.

.. code-block:: python

    for node in parser.css("div#text"):
        for cnode in node.iter():
            print(cnode.tag, cnode.html)

**Output:**

.. code-block:: text

    p <p class="p3" style="display:none;">Excepteur <i>sint</i> occaecat cupidatat non proident</p>
    p <p class="p3" vid>Lorem ipsum</p>

Node Basics
-----------

Creating Nodes
~~~~~~~~~~~~~~

``create_tag()`` returns a standalone node, while
``LexborHTMLParser.create_node()`` returns one tied to a specific parser.
Neither can be inserted into an arbitrary tree, so use ``create_node()``
whenever the node is destined for that parser's document.

.. code-block:: python

    from selectolax.lexbor import LexborHTMLParser, create_tag

    node = create_tag("div")
    node.attrs["class"] = "card"
    print(node.html)

    parser = LexborHTMLParser("<div id='main'></div>")
    tied = parser.create_node("span")
    print(tied.tag)

**Output:**

.. code-block:: text

    <div class="card"></div>
    span

Identifying Nodes
~~~~~~~~~~~~~~~~~

``id`` is the ``id`` attribute ready-made, and ``tag_id`` is lexbor's numeric
tag identifier, which is cheaper to compare than repeatedly comparing tag name
strings. Both return ``None`` on a node that has no such value, such as a text
or comment node.

.. code-block:: python

    parser = LexborHTMLParser("<div id='main'>Hi</div>")
    main = parser.css_first("div")

    print(main.id)
    print(main.tag)
    print(main.tag_id)

**Output:**

.. code-block:: text

    main
    div
    52

Reading Attributes Safely
~~~~~~~~~~~~~~~~~~~~~~~~~

An attribute that is present but valueless, such as ``<input disabled>``, has
``None`` as its value, and a missing attribute raises ``KeyError`` on lookup.
``attrs.sget()`` returns a string in both cases, so it is the convenient
option when you only care about the value.

.. code-block:: python

    parser = LexborHTMLParser("<div id='main' data-tag></div>")
    main = parser.css_first("div")

    print(main.attributes)
    print(main.attrs.get("data-tag"))
    print(main.attrs.get("data-missing"))

    # sget() never returns None: it falls back to the given default.
    print(main.attrs.sget("data-missing", "none"))
    print(main.attrs.sget("id"))

**Output:**

.. code-block:: text

    {'id': 'main', 'data-tag': None}
    None
    None
    none
    main

DOM Modification
----------------

Tag Removal
~~~~~~~~~~~

Completely remove elements from the DOM tree.

.. code-block:: python

    parser = LexborHTMLParser(html)

    # Remove all p tags
    for node in parser.tags('p'):
        node.decompose()

    print(parser.body.html)

**Output:**

.. code-block:: text

    <body>
        <span id="vspan"></span>
        <h1>Welcome to selectolax tutorial</h1>
        <div id="text">


        </div>
        <div>

        </div>
    </body>

Tag Unwrapping
~~~~~~~~~~~~~~

Remove tags but preserve their content.

.. code-block:: python

    parser = LexborHTMLParser(html)

    # Remove p and i tags but keep their content
    parser.unwrap_tags(['p', 'i'])
    print(parser.body.html)

**Output:**

.. code-block:: text

    <body>
        <span id="vspan"></span>
        <h1>Welcome to selectolax tutorial</h1>
        <div id="text">
            Excepteur sint occaecat cupidatat non proident
            Lorem ipsum
        </div>
        <div>
            Lorem ipsum dolor sit amet, ea quo modus meliore platonem.
        </div>
    </body>

Attribute Manipulation
~~~~~~~~~~~~~~~~~~~~~~

Add, modify, and remove element attributes.

.. code-block:: python

    parser = LexborHTMLParser(html)
    node = parser.css_first('div#text')

    # Set attributes
    node.attrs['data'] = 'secret data'
    node.attrs['id'] = 'new_id'
    print(node.attributes)

    # Remove attributes
    del node.attrs['id']
    print(node.attributes)
    print(node.html)

**Output:**

.. code-block:: text

    {'id': 'new_id', 'data': 'secret data'}
    {'data': 'secret data'}
    <div data="secret data">
            <p class="p3" style="display:none;">Excepteur <i>sint</i> occaecat cupidatat non proident</p>
            <p class="p3" vid>Lorem ipsum</p>
        </div>

Inserting Nodes
~~~~~~~~~~~~~~~

Insert new content into the DOM at specific positions.

.. code-block:: python

    html = """
    <div id="container">
        <span class="red"></span>
        <span class="green"></span>
        <span class="red"></span>
        <span class="green"></span>
    </div>
    """

    parser = LexborHTMLParser(html)

    # Insert text before an element. A str is inserted as text, so any HTML
    # in it is escaped rather than parsed.
    red_node = parser.css_first('.red')
    red_node.insert_before("Hello")

    # Insert a node taken from another parser. The insert methods want a
    # LexborNode, so reach into the parser you borrowed it from.
    green_node = parser.css_first('.green')
    donor = LexborHTMLParser("<div>Hi</div>")
    green_node.insert_before(donor.body.first_child)

    # Insert before, after, or as a child. These methods move the node they
    # are given, so clone() first when you want more than one copy.
    car_div = parser.create_node("div")
    car_div.inner_html = "Car"
    green_node.insert_before(car_div)
    green_node.insert_after(car_div.clone())
    green_node.insert_child(car_div.clone())

    print(parser.body.html)

**Output:**

.. code-block:: text

    <body><div id="container">
        Hello<span class="red"></span>
        <div>Hi</div><div>Car</div><span class="green"><div>Car</div></span><div>Car</div>
        <span class="red"></span>
        <span class="green"></span>
    </div>
    </body>

Cloning Trees and Nodes
-----------------------

``clone()`` makes an independent deep copy. The copy is tied to the parser it came from
and is freed when that parser is, so keep a reference to the parser rather than
to the clone.

.. code-block:: python

    from selectolax.lexbor import LexborHTMLParser

    parser = LexborHTMLParser('<div id="main"><p>Hello</p></div>')

    # A cloned parser is a whole separate document.
    draft = parser.clone()
    draft.css_first('div').attrs['id'] = 'draft'
    print(parser.css_first('div').id, draft.css_first('div').id)

    # A cloned node is independent, so editing it leaves the original alone.
    div = parser.css_first('div')
    copy = div.clone()
    copy.attrs['id'] = 'copy'
    copy.insert_child(' world')
    print(div.html)
    print(copy.html)

**Output:**

.. code-block:: text

    main draft
    <div id="main"><p>Hello</p></div>
    <div id="copy"><p>Hello</p> world</div>

Cloning is also how you reuse a node. Insertion methods move the node they are
given rather than copying it, so inserting the same node twice leaves it in the
last position only. ``clone()`` before each insert when you want copies.

Tree Traversal
--------------

Walk  every node in the DOM tree and extract text content.

.. code-block:: python

    parser = LexborHTMLParser(html)

    # Traverse the entire tree
    for node in parser.root.traverse(include_text=True):
        if node.tag == '-text':
            text = node.text(deep=True).strip()
            if text:
                print(text)
        else:
            print(node.tag)

**Output:**

.. code-block:: text

    html
    head
    body
    div
    p
    Excepteur
    i
    sint
    occaecat cupidatat non proident
    p
    Lorem ipsum
    div
    p
    Lorem ipsum dolor sit amet, ea quo modus meliore platonem.


Text and Comment Nodes
----------------------

A tree holds more than elements. ``traverse()`` and ``iter()`` only yield text
nodes when you ask for them with ``include_text=True``, and the type predicates
tell the node kinds apart, which is cleaner than comparing ``node.tag``
against the ``-text`` and ``-comment`` placeholders.

Two properties read those nodes' content. ``text_content`` returns a text
node's own data without descending into children, and ``comment_content``
returns an HTML comment's body with the surrounding whitespace removed. On a
node of the wrong kind both return ``None`` instead of raising.

.. code-block:: python

    from selectolax.lexbor import LexborHTMLParser

    html = """
    <div id="main">
        <!-- updated 2026-10-06 -->
        <p>Price: <b>10</b> EUR</p>
    </div>
    """

    parser = LexborHTMLParser(html)
    p = parser.css_first('p')

    # text_content reads one text node; text() concatenates descendants.
    print(repr(p.first_child.text_content))
    print(repr(p.first_child.text()))
    print(repr(p.text()))

    # comment_content needs the comment node, which a tree walk finds.
    comment = next(n for n in parser.css_first('#main').traverse() if n.is_comment_node)
    print(repr(comment.comment_content))
    print(comment.html)

    # Neither property raises on the wrong node type.
    print(p.comment_content)
    print(comment.text_content)

**Output:**

.. code-block:: text

    'Price: '
    'Price: '
    'Price: 10 EUR'
    'updated 2026-10-06'
    <!-- updated 2026-10-06 -->
    None
    None

``is_empty_text_node`` reports whether a text node holds nothing but
whitespace, which is what ``skip_empty=True`` filters out in ``text()``,
``iter()`` and ``traverse()``.

Common Patterns
---------------

Extract Text Content
~~~~~~~~~~~~~~~~~~~~

Extract text content from HTML elements with various formatting options.

.. code-block:: python

    parser = LexborHTMLParser('<div><p>Hello <b>world</b>!</p></div>')

    # Get text content with different options
    node = parser.css_first('p')

    # Get all text content
    print(node.text())  # "Hello world!"

    # Get text with custom separator
    print(node.text(separator=' | '))  # "Hello | world | !"

    # Get text without stripping whitespace
    print(node.text(strip=False))

**Output:**

.. code-block:: text

    Hello world!
    Hello  | world | !
    Hello world!

Clean HTML
~~~~~~~~~~

Remove potentially dangerous or unwanted HTML elements.

.. code-block:: python

    dirty_html = '''
    <div>
        <p>Good content</p>
        <script>alert('xss')</script>
        <style>body { color: red; }</style>
        <p>More content</p>
    </div>
    '''

    parser = LexborHTMLParser(dirty_html)

    # Remove unwanted tags
    for tag in parser.css('script, style'):
        tag.decompose()

    print(parser.body.html)

**Output:**

.. code-block:: text

    <body><div>
        <p>Good content</p>


        <p>More content</p>
    </div>
    </body>

Extract Links and Images
~~~~~~~~~~~~~~~~~~~~~~~~

Extract all links and images from HTML content.

.. code-block:: python

    html = '''
    <div>
        <a href="https://example.com">Link 1</a>
        <a href="/page2">Link 2</a>
        <img src="image1.jpg" alt="Image 1">
        <img src="image2.png" alt="Image 2">
    </div>
    '''

    parser = LexborHTMLParser(html)

    # Extract all links
    for link in parser.css('a[href]'):
        print(f"Link: {link.text()} -> {link.attrs['href']}")

    # Extract all images
    for img in parser.css('img[src]'):
        print(f"Image: {img.attrs.get('alt', 'No alt')} -> {img.attrs['src']}")

**Output:**

.. code-block:: text

    Link: Link 1 -> https://example.com
    Link: Link 2 -> /page2
    Image: Image 1 -> image1.jpg
    Image: Image 2 -> image2.png


Advanced selectors
------------------

Text Content Filtering
~~~~~~~~~~~~~~~~~~~~~~

Use advanced selectors to filter elements based on their text content.

.. code-block:: python

    html = """
    <script>
     var super_variable = 100;
    </script>
    <script>
     console.log('debug');
    </script>
    """

    parser = LexborHTMLParser(html)

    # Filter script tags containing specific text
    scripts_with_super = parser.select('script').text_contains("super").matches
    print([node.text() for node in scripts_with_super])

**Output:**

.. code-block:: text

    ['\n var super_variable = 100;\n']

CSS Attribute and Pseudo-class Selectors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    html = """
    <div>
        <article class="post published" data-id="1">
            <h2>First Post</h2>
            <p>Content of first post</p>
            <div class="meta">
                <span class="author">John</span>
                <span class="date">2023-01-01</span>
            </div>
        </article>
        <article class="post draft" data-id="2">
            <h2>Second Post</h2>
            <p>Content of second post</p>
            <div class="meta">
                <span class="author">Jane</span>
                <span class="date">2023-01-02</span>
            </div>
        </article>
        <aside class="sidebar">
            <div class="widget">
                <h3>Popular Posts</h3>
                <ul>
                    <li><a href="#1">First Post</a></li>
                    <li><a href="#2">Second Post</a></li>
                </ul>
            </div>
        </aside>
    </div>
    """

    parser = LexborHTMLParser(html)

    # Attribute selectors
    published_posts = parser.css('article.post.published')
    print(f"Published posts: {len(published_posts)}")

    # Descendant selectors
    authors = parser.css('article .meta .author')
    for author in authors:
        print(f"Author: {author.text()}")

    # Pseudo-class selectors
    first_article = parser.css('article:first-child')
    if first_article:
        print(f"First article title: {first_article[0].css_first('h2').text()}")

    # Attribute value selectors
    specific_post = parser.css_first('article[data-id="1"]')
    if specific_post:
        print(f"Post ID 1 title: {specific_post.css_first('h2').text()}")

**Output:**

.. code-block:: text

    Published posts: 1
    Author: John
    Author: Jane
    First article title: First Post
    Post ID 1 title: First Post

Text Content Pseudo-class Selectors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use lexbor-specific pseudo-classes for case-sensitive and case-insensitive text matching.

.. code-block:: python

    html = '<div><p>hello </p><p id="main">lexbor is AwesOme</p></div>'
    parser = LexborHTMLParser(html)

    # Case-insensitive search
    results_ci = parser.css('p:lexbor-contains("awesome" i)')
    print(f"Case-insensitive results: {len(results_ci)}")

    # Case-sensitive search
    results_cs = parser.css('p:lexbor-contains("AwesOme")')
    print(f"Case-sensitive results: {len(results_cs)}")
    print(f"Matching text: {results_cs[0].text()}")

**Output:**

.. code-block:: text

    Case-insensitive results: 1
    Case-sensitive results: 1
    Matching text: lexbor is AwesOme

Template Content
----------------

Reach the content of ``<template>`` elements, which ``css()`` never finds.

The HTML Standard does not make ``<template>`` a container: markup written inside
it is parsed into a separate document fragment the element owns, so it is not
part of the document tree and ordinary searches skip it. Use
``template_fragments()`` to get that content as fragments.

.. code-block:: python

    from selectolax.lexbor import LexborHTMLParser

    html = """
    <div id="app">
        <template id="row-template">
            <tr class="row">
                <td class="name"></td>
                <td class="age"></td>
            </tr>
        </template>
        <template id="header-template">
            <tr><th>Name</th><th>Age</th></tr>
        </template>
    </div>
    """

    parser = LexborHTMLParser(html)

    # css() skips template content entirely.
    print(len(parser.css('.row')))

    # One fragment per <template>, in document order. fragment.parent is the
    # <template> the content came from, so its attributes stay reachable.
    for fragment in parser.template_fragments():
        cells = [cell.tag for cell in fragment.css('td, th')]
        print(f"{fragment.parent.attrs['id']}: {cells}")

    # Fragments are views onto the tree, not copies, so edits are not lost.
    row = parser.css_first('#row-template').template_fragments()[0]
    row.css_first('.name').attrs['data-role'] = 'name'
    print('data-role="name"' in parser.html)

**Output:**

.. code-block:: text

    0
    row-template: ['td', 'td']
    header-template: ['th', 'th']
    True

A ``<template>`` in the SVG or MathML namespace is an ordinary element, so its
content is already part of the tree and is not reported here. A template nested
inside another template's content is not in the document tree either; call
``template_fragments()`` on the outer fragment to reach it.


Sibling Navigation
------------------

Navigate between sibling elements in the DOM.

.. code-block:: python

    html = """
    <nav>
        <a href="/">Home</a>
        <a href="/about">About</a>
        <a href="/contact" class="active">Contact</a>
        <a href="/blog">Blog</a>
    </nav>
    """

    parser = LexborHTMLParser(html)
    active_link = parser.css_first("a.active")

    if active_link:
        print(f"Active link: {active_link.text()}")
        # We need to call it twice, because there are text nodes (spaces and new lines) between <a> elements
        if active_link.prev:
            print(f"Previous link: {active_link.prev.prev.text()}")

        if active_link.next:
            print(f"Next link: {active_link.next.next.text()}")

**Output:**

.. code-block:: text

    Active link: Contact
    Previous link: About
    Next link: Blog


Table Parsing
-------------

Parse HTML tables and extract structured data.

.. code-block:: python

    table_html = """
    <table class="data-table">
        <thead>
            <tr>
                <th>Name</th>
                <th>Age</th>
                <th>City</th>
                <th>Occupation</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Alice Johnson</td>
                <td>28</td>
                <td>New York</td>
                <td>Software Engineer</td>
            </tr>
            <tr>
                <td>Bob Smith</td>
                <td>35</td>
                <td>Los Angeles</td>
                <td>Designer</td>
            </tr>
            <tr>
                <td>Carol Brown</td>
                <td>42</td>
                <td>Chicago</td>
                <td>Manager</td>
            </tr>
        </tbody>
    </table>
    """

    parser = LexborHTMLParser(table_html)

    # Extract headers
    headers = [th.text() for th in parser.css('thead th')]
    print("Headers:", headers)

    # Extract data rows
    rows = []
    for tr in parser.css('tbody tr'):
        row_data = [td.text() for td in tr.css('td')]
        rows.append(row_data)

    # Display as structured data
    for i, row in enumerate(rows):
        print(f"\nRow {i+1}:")
        for header, value in zip(headers, row):
            print(f"  {header}: {value}")

**Output:**

.. code-block:: text

    Headers: ['Name', 'Age', 'City', 'Occupation']

    Row 1:
      Name: Alice Johnson
      Age: 28
      City: New York
      Occupation: Software Engineer

    Row 2:
      Name: Bob Smith
      Age: 35
      City: Los Angeles
      Occupation: Designer

    Row 3:
      Name: Carol Brown
      Age: 42
      City: Chicago
      Occupation: Manager

Form Data Extraction
--------------------

Parse HTML forms and extract input data.

.. code-block:: python

    form_html = """
    <form id="contact-form" method="post" action="/submit">
        <div class="form-group">
            <label for="name">Name:</label>
            <input type="text" id="name" name="name" value="John Doe" required>
        </div>
        <div class="form-group">
            <label for="email">Email:</label>
            <input type="email" id="email" name="email" placeholder="john@example.com">
        </div>
        <div class="form-group">
            <label for="country">Country:</label>
            <select id="country" name="country">
                <option value="us">United States</option>
                <option value="ca" selected>Canada</option>
                <option value="uk">United Kingdom</option>
            </select>
        </div>
        <div class="form-group">
            <label>
                <input type="checkbox" name="newsletter" checked> Subscribe to newsletter
            </label>
        </div>
        <div class="form-group">
            <label for="message">Message:</label>
            <textarea id="message" name="message" rows="4">Hello there!</textarea>
        </div>
        <button type="submit">Submit</button>
    </form>
    """

    parser = LexborHTMLParser(form_html)

    # Extract form metadata
    form = parser.css_first('form')
    print(f"Form ID: {form.attrs.get('id')}")
    print(f"Form method: {form.attrs.get('method')}")
    print(f"Form action: {form.attrs.get('action')}")

    # Extract input fields
    print("\nInput fields:")
    for input_field in parser.css('input'):
        field_type = input_field.attrs.get('type', 'text')
        name = input_field.attrs.get('name')
        value = input_field.attrs.get('value', '')
        checked = 'checked' in input_field.attrs

        print(f"  {name} ({field_type}): {value} {'[checked]' if checked else ''}")

    # Extract select options
    print("\nSelect fields:")
    for select in parser.css('select'):
        name = select.attrs.get('name')
        print(f"  {name}:")
        for option in select.css('option'):
            value = option.attrs.get('value')
            text = option.text()
            selected = 'selected' in option.attrs
            print(f"    {value}: {text} {'[selected]' if selected else ''}")

    # Extract textarea
    print("\nTextarea fields:")
    for textarea in parser.css('textarea'):
        name = textarea.attrs.get('name')
        content = textarea.text()
        print(f"  {name}: {content}")

**Output:**

.. code-block:: text

    Form ID: contact-form
    Form method: post
    Form action: /submit

    Input fields:
      name (text): John Doe
      email (email):
      newsletter (checkbox):  [checked]

    Select fields:
      country:
        us: United States
        ca: Canada [selected]
        uk: United Kingdom

    Textarea fields:
      message: Hello there!
