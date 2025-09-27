Examples
========

This page contains simple examples of how to use Selectolax for HTML parsing and manipulation.

.. note::
   All examples use the Lexbor backend (``from selectolax.lexbor import LexborHTMLParser``)
   which provides better performance and features compared to the older Modest backend.

Basic HTML Parsing
------------------

There are 3 ways to create or parse objects in Selectolax:

1. Parse HTML as a full document using ``LexborHTMLParser()``
2. Parse HTML as a fragment using ``LexborHTMLParser().parse_fragment()``
3. Create single node using ``LexborHTMLParser().create_tag()``

- ``LexborHTMLParser()`` - Returns the HTML tree as parsed by Lexbor, unmodified. The HTML is assumed to be a full document. ``<html>``, ``<head>``, and ``<body>`` tags are added if missing.

- ``parse_fragment()`` - Intended for HTML fragments/partials. Returns a list of Nodes. Given HTML doesn't need to contain ``<html>``, ``<head>``, ``<body>``. HTML can have multiple root elements.

- ``create_tag()`` - Create a single empty node for given tag.

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
    html_tree = LexborHTMLParser(html)

    # Parse HTML as a fragment
    frag_tree = LexborHTMLParser().parse_fragment(fragment)

    # Create a single node
    node = LexborHTMLParser().create_tag("div")

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
    print(node.inner)

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
