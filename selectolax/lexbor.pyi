from typing import Any, Iterator, Literal, NoReturn, Optional, TypeVar, overload

DefaultT = TypeVar("DefaultT")

class LexborAttributes:
    """A dict-like object that represents attributes."""

    @staticmethod
    def create(node: LexborAttributes) -> LexborAttributes: ...
    def keys(self) -> Iterator[str]: ...
    def items(self) -> Iterator[tuple[str, str | None]]: ...
    def values(self) -> Iterator[str | None]: ...
    def __iter__(self) -> Iterator[str]: ...
    def __len__(self) -> int: ...
    def __getitem__(self, key: str) -> str | None: ...
    def __setitem__(self, key: str, value: Optional[str]) -> None: ...
    def __delitem__(self, key: str) -> None: ...
    def __contains__(self, key: str) -> bool: ...
    def __repr__(self) -> str: ...
    @overload
    def get(self, key: str, default: DefaultT) -> DefaultT | str | None: ...
    @overload
    def get(self, key: str, default: None = ...) -> str | None: ...
    @overload
    def sget(self, key: str, default: str | DefaultT) -> str | DefaultT: ...
    @overload
    def sget(self, key: str, default: str = "") -> str: ...

class LexborSelector:
    """An advanced CSS selector that supports additional operations.

    Think of it as a toolkit that mimics some of the features of XPath.

    Please note, this is an experimental feature that can change in the future.
    """

    def __init__(self, node: LexborNode, query: str): ...
    def css(self, query: str) -> NoReturn: ...
    @property
    def matches(self) -> list[LexborNode]:
        """Returns all possible matches"""
        ...
    @property
    def any_matches(self) -> bool:
        """Returns True if there are any matches"""
        ...
    def text_contains(
        self, text: str, deep: bool = True, separator: str = "", strip: bool = False
    ) -> LexborSelector:
        """Filter all current matches given text."""
        ...
    def any_text_contains(
        self, text: str, deep: bool = True, separator: str = "", strip: bool = False
    ) -> bool:
        """Returns True if any node in the current search scope contains specified text"""
        ...
    def attribute_longer_than(
        self, attribute: str, length: int, start: str | None = None
    ) -> LexborSelector:
        """Filter all current matches by attribute length.

        Similar to string-length in XPath.
        """
        ...
    def any_attribute_longer_than(
        self, attribute: str, length: int, start: str | None = None
    ) -> bool:
        """Returns True any href attribute longer than a specified length.

        Similar to string-length in XPath.
        """
        ...

    @property
    def inner_html(self) -> str | None:
        """Return HTML representation of the child nodes.

        Works similar to innerHTML in JavaScript.
        Unlike the `.html` property, does not include the current node.
        Can be used to set HTML as well. See the setter docstring.

        Returns
        -------
        text : str or None
        """
        ...

    @inner_html.setter
    def inner_html(self, html: str):
        """Set inner HTML to the specified HTML.

        Replaces existing data inside the node.
        Works similar to innerHTML in JavaScript.

        Parameters
        ----------
        html : str

        """
        ...

class LexborCSSSelector:
    def __init__(self): ...
    def find(self, query: str, node: LexborNode) -> list[LexborNode]: ...
    def any_matches(self, query: str, node: LexborNode) -> bool: ...

class LexborNode:
    """A class that represents HTML node (element)."""

    parser: LexborHTMLParser
    @property
    def mem_id(self) -> int: ...
    @property
    def child(self) -> LexborNode | None:
        """Alias for the `first_child` property.

        **Deprecated**. Please use `first_child` instead.
        """
        ...
    @property
    def first_child(self) -> LexborNode | None:
        """Return the first child node."""
        ...
    @property
    def parent(self) -> LexborNode | None:
        """Return the parent node."""
        ...
    @property
    def next(self) -> LexborNode | None:
        """Return next node."""
        ...
    @property
    def prev(self) -> LexborNode | None:
        """Return previous node."""
        ...
    @property
    def last_child(self) -> LexborNode | None:
        """Return last child node."""
        ...
    @property
    def html(self) -> str | None:
        """Return HTML representation of the current node including all its child nodes.

        Returns
        -------
        text : str
        """
        ...
    def __hash__(self) -> int: ...
    def text_lexbor(self) -> str:
        """Returns the text of the node including text of all its child nodes.

        Uses builtin method from lexbor.
        """
        ...
    def text(self, deep: bool = True, separator: str = "", strip: bool = False) -> str:
        """Returns the text of the node including text of all its child nodes.

        Parameters
        ----------
        strip : bool, default False
            If true, calls ``str.strip()`` on each text part to remove extra white spaces.
        separator : str, default ''
            The separator to use when joining text from different nodes.
        deep : bool, default True
            If True, includes text from all child nodes.

        Returns
        -------
        text : str
        """
        ...
    def css(self, query: str) -> list[LexborNode]:
        """Evaluate CSS selector against current node and its child nodes.

        Matches pattern `query` against HTML tree.
        `CSS selectors reference <https://www.w3schools.com/cssref/css_selectors.asp>`_.

        Special selectors:

         - parser.css('p:lexbor-contains("awesome" i)') -- case-insensitive contains
         - parser.css('p:lexbor-contains("awesome")') -- case-sensitive contains


        Parameters
        ----------
        query : str
            CSS selector (e.g. "div > :nth-child(2n+1):not(:has(a))").

        Returns
        -------
        selector : list of `Node` objects
        """
        ...
    @overload
    def css_first(
        self, query: str, default: Any = ..., strict: Literal[True] = ...
    ) -> LexborNode:
        """Same as `css` but returns only the first match.

        Parameters
        ----------

        query : str
        default : bool, default None
            Default value to return if there is no match.
        strict: bool, default False
            Set to True if you want to check if there is strictly only one match in the document.


        Returns
        -------
        selector : `LexborNode` object
        """
        ...
    @overload
    def css_first(
        self, query: str, default: DefaultT, strict: bool = False
    ) -> LexborNode | DefaultT:
        """Same as `css` but returns only the first match.

        Parameters
        ----------

        query : str
        default : bool, default None
            Default value to return if there is no match.
        strict: bool, default False
            Set to True if you want to check if there is strictly only one match in the document.


        Returns
        -------
        selector : `LexborNode` object
        """
        ...
    @overload
    def css_first(
        self, query: str, default: None = ..., strict: bool = False
    ) -> LexborNode | None:
        """Same as `css` but returns only the first match.

        Parameters
        ----------

        query : str
        default : bool, default None
            Default value to return if there is no match.
        strict: bool, default False
            Set to True if you want to check if there is strictly only one match in the document.


        Returns
        -------
        selector : `LexborNode` object
        """
        ...
    def any_css_matches(self, selectors: tuple[str]) -> bool:
        """Returns True if any of CSS selectors matches a node"""
        ...
    def css_matches(self, selector: str) -> bool:
        """Returns True if CSS selector matches a node."""
        ...
    @property
    def tag_id(self) -> int: ...
    @property
    def tag(self) -> str | None:
        """Return the name of the current tag (e.g. div, p, img).

        For for non-tag nodes, returns the following names:

         * `-text` - text node
         * `-document` - document node
         * `-comment` - comment node

        Returns
        -------
        text : str
        """
        ...
    def decompose(self, recursive: bool = True) -> None:
        """Remove the current node from the tree.

        Parameters
        ----------
        recursive : bool, default True
            Whenever to delete all its child nodes

        Examples
        --------

        >>> tree = LexborHTMLParser(html)
        >>> for tag in tree.css('script'):
        >>>     tag.decompose()
        """
        ...
    def strip_tags(self, tags: list[str], recursive: bool = False) -> None:
        """Remove specified tags from the HTML tree.

        Parameters
        ----------
        tags : list
            List of tags to remove.
        recursive : bool, default True
            Whenever to delete all its child nodes

        Examples
        --------

        >>> tree = LexborHTMLParser('<html><head></head><body><script></script><div>Hello world!</div></body></html>')
        >>> tags = ['head', 'style', 'script', 'xmp', 'iframe', 'noembed', 'noframes']
        >>> tree.strip_tags(tags)
        >>> tree.html
        '<html><body><div>Hello world!</div></body></html>'
        """
        ...
    @property
    def attributes(self) -> dict[str, str | None]:
        """Get all attributes that belong to the current node.

        The value of empty attributes is None.

        Returns
        -------
        attributes : dictionary of all attributes.

        Examples
        --------

        >>> tree = LexborHTMLParser("<div data id='my_id'></div>")
        >>> node = tree.css_first('div')
        >>> node.attributes
        {'data': None, 'id': 'my_id'}
        """
        ...
    @property
    def attrs(self) -> LexborAttributes:
        """A dict-like object that is similar to the ``attributes`` property, but operates directly on the Node data.

        .. warning:: Use ``attributes`` instead, if you don't want to modify Node attributes.

        Returns
        -------
        attributes : Attributes mapping object.

        Examples
        --------

        >>> tree = LexborHTMLParser("<div id='a'></div>")
        >>> node = tree.css_first('div')
        >>> node.attrs
        <div attributes, 1 items>
        >>> node.attrs['id']
        'a'
        >>> node.attrs['foo'] = 'bar'
        >>> del node.attrs['id']
        >>> node.attributes
        {'foo': 'bar'}
        >>> node.attrs['id'] = 'new_id'
        >>> node.html
        '<div foo="bar" id="new_id"></div>'
        """
        ...
    @property
    def id(self) -> str | None:
        """Get the id attribute of the node.

        Returns None if id does not set.

        Returns
        -------
        text : str
        """
        ...
    def iter(self, include_text: bool = False) -> Iterator[LexborNode]:
        """Iterate over nodes on the current level.

        Parameters
        ----------
        include_text : bool
            If True, includes text nodes as well.

        Yields
        -------
        node
        """
        ...
    def unwrap(self, delete_empty: bool = False) -> None:
        """Replace node with whatever is inside this node.

        Does nothing if you perform unwrapping second time on the same node.

        Parameters
        ----------
        delete_empty : bool, default False
            If True, removes empty tags.

        Examples
        --------

        >>>  tree = LexborHTMLParser("<div>Hello <i>world</i>!</div>")
        >>>  tree.css_first('i').unwrap()
        >>>  tree.html
        '<html><head></head><body><div>Hello world!</div></body></html>'

        Note: by default, empty tags are ignored, use "delete_empty" to change this.
        """
        ...
    def unwrap_tags(self, tags: list[str], delete_empty: bool = False) -> None:
        """Unwraps specified tags from the HTML tree.

        Works the same as the ``unwrap`` method, but applied to a list of tags.

        Parameters
        ----------
        tags : list
            List of tags to remove.
        delete_empty : bool, default False
            If True, removes empty tags.

        Examples
        --------

        >>> tree = LexborHTMLParser("<div><a href="">Hello</a> <i>world</i>!</div>")
        >>> tree.body.unwrap_tags(['i','a'])
        >>> tree.body.html
        '<body><div>Hello world!</div></body>'

        Note: by default, empty tags are ignored, use "delete_empty" to change this.
        """
        ...
    def merge_text_nodes(self) -> None:
        """Iterates over all text nodes and merges all text nodes that are close to each other.

        This is useful for text extraction.
        Use it when you need to strip HTML tags and merge "dangling" text.

        Examples
        --------

        >>> tree = LexborHTMLParser("<div><p><strong>J</strong>ohn</p><p>Doe</p></div>")
        >>> node = tree.css_first('div')
        >>> tree.unwrap_tags(["strong"])
        >>> tree.text(deep=True, separator=" ", strip=True)
        "J ohn Doe" # Text extraction produces an extra space because the strong tag was removed.
        >>> node.merge_text_nodes()
        >>> tree.text(deep=True, separator=" ", strip=True)
        "John Doe"
        """
        ...
    def traverse(self, include_text: bool = False) -> Iterator[LexborNode]:
        """Iterate over all child and next nodes starting from the current level.

        Parameters
        ----------
        include_text : bool
            If True, includes text nodes as well.

        Yields
        -------
        node
        """
        ...
    def replace_with(self, value: bytes | str | LexborNode) -> None:
        """Replace current Node with specified value.

        Parameters
        ----------
        value : str, bytes or Node
            The text or Node instance to replace the Node with.
            When a text string is passed, it's treated as text. All HTML tags will be escaped.
            Convert and pass the ``Node`` object when you want to work with HTML.
            Does not clone the ``Node`` object.
            All future changes to the passed ``Node`` object will also be taken into account.

        Examples
        --------

        >>> tree = LexborHTMLParser('<div>Get <img src="" alt="Laptop"></div>')
        >>> img = tree.css_first('img')
        >>> img.replace_with(img.attributes.get('alt', ''))
        >>> tree.body.child.html
        '<div>Get Laptop</div>'

        >>> html_parser = LexborHTMLParser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
        >>> html_parser2 = LexborHTMLParser('<div>Test</div>')
        >>> img_node = html_parser.css_first('img')
        >>> img_node.replace_with(html_parser2.body.child)
        '<div>Get <span alt="Laptop"><div>Test</div> <div></div></span></div>'
        """
        ...
    def insert_before(self, value: bytes | str | LexborNode) -> None:
        """Insert a node before the current Node.

        Parameters
        ----------
        value : str, bytes or Node
            The text or Node instance to insert before the Node.
            When a text string is passed, it's treated as text. All HTML tags will be escaped.
            Convert and pass the ``Node`` object when you want to work with HTML.
            Does not clone the ``Node`` object.
            All future changes to the passed ``Node`` object will also be taken into account.

        Examples
        --------

        >>> tree = LexborHTMLParser('<div>Get <img src="" alt="Laptop"></div>')
        >>> img = tree.css_first('img')
        >>> img.insert_before(img.attributes.get('alt', ''))
        >>> tree.body.child.html
        '<div>Get Laptop<img src="" alt="Laptop"></div>'

        >>> html_parser = LexborHTMLParser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
        >>> html_parser2 = LexborHTMLParser('<div>Test</div>')
        >>> img_node = html_parser.css_first('img')
        >>> img_node.insert_before(html_parser2.body.child)
        <div>Get <span alt="Laptop"><div>Test</div><img src="/jpg"> <div></div></span></div>'
        """
        ...
    def insert_after(self, value: bytes | str | LexborNode) -> None:
        """Insert a node after the current Node.

        Parameters
        ----------
        value : str, bytes or Node
            The text or Node instance to insert after the Node.
            When a text string is passed, it's treated as text. All HTML tags will be escaped.
            Convert and pass the ``Node`` object when you want to work with HTML.
            Does not clone the ``Node`` object.
            All future changes to the passed ``Node`` object will also be taken into account.

        Examples
        --------

        >>> tree = LexborHTMLParser('<div>Get <img src="" alt="Laptop"></div>')
        >>> img = tree.css_first('img')
        >>> img.insert_after(img.attributes.get('alt', ''))
        >>> tree.body.child.html
        '<div>Get <img src="" alt="Laptop">Laptop</div>'

        >>> html_parser = LexborHTMLParser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
        >>> html_parser2 = LexborHTMLParser('<div>Test</div>')
        >>> img_node = html_parser.css_first('img')
        >>> img_node.insert_after(html_parser2.body.child)
        <div>Get <span alt="Laptop"><img src="/jpg"><div>Test</div> <div></div></span></div>'
        """
        ...
    def insert_child(self, value: bytes | str | LexborNode) -> None:
        """Insert a node inside (at the end of) the current Node.

        Parameters
        ----------
        value : str, bytes or Node
            The text or Node instance to insert inside the Node.
            When a text string is passed, it's treated as text. All HTML tags will be escaped.
            Convert and pass the ``Node`` object when you want to work with HTML.
            Does not clone the ``Node`` object.
            All future changes to the passed ``Node`` object will also be taken into account.

        Examples
        --------

        >>> tree = LexborHTMLParser('<div>Get <img src=""></div>')
        >>> div = tree.css_first('div')
        >>> div.insert_child('Laptop')
        >>> tree.body.child.html
        '<div>Get <img src="">Laptop</div>'

        >>> html_parser = LexborHTMLParser('<div>Get <span alt="Laptop"> <div>Laptop</div> </span></div>')
        >>> html_parser2 = LexborHTMLParser('<div>Test</div>')
        >>> span_node = html_parser.css_first('span')
        >>> span_node.insert_child(html_parser2.body.child)
        <div>Get <span alt="Laptop"> <div>Laptop</div> <div>Test</div> </span></div>'
        """
        ...
    @property
    def raw_value(self) -> NoReturn:
        """Return the raw (unparsed, original) value of a node.

        Currently, works on text nodes only.

        Returns
        -------

        raw_value : bytes

        Examples
        --------

        >>> html_parser = LexborHTMLParser('<div>&#x3C;test&#x3E;</div>')
        >>> selector = html_parser.css_first('div')
        >>> selector.child.html
        '&lt;test&gt;'
        >>> selector.child.raw_value
        b'&#x3C;test&#x3E;'
        """
        ...
    def scripts_contain(self, query: str) -> bool:
        """Returns True if any of the script tags contain specified text.

        Caches script tags on the first call to improve performance.

        Parameters
        ----------
        query : str
            The query to check.
        """
        ...
    def script_srcs_contain(self, queries: tuple[str]) -> bool:
        """Returns True if any of the script SRCs attributes contain on of the specified text.

        Caches values on the first call to improve performance.

        Parameters
        ----------
        queries : tuple of str
        """
        ...
    def remove(self, recursive: bool = True) -> None:
        """An alias for the decompose method."""
        ...
    def select(self, query: str | None = None) -> LexborSelector:
        """Select nodes given a CSS selector.

        Works similarly to the the ``css`` method, but supports chained filtering and extra features.

        Parameters
        ----------
        query : str or None
            The CSS selector to use when searching for nodes.

        Returns
        -------
        selector : The `Selector` class.
        """
        ...
    @property
    def text_content(self) -> str | None:
        """Returns the text of the node if it is a text node.

        Returns None for other nodes.
        Unlike the ``text`` method, does not include child nodes.

        Returns
        -------
        text : str or None.
        """
        ...

    @property
    def inner_html(self) -> str | None:
        """Return HTML representation of the child nodes.

        Works similar to innerHTML in JavaScript.
        Unlike the `.html` property, does not include the current node.
        Can be used to set HTML as well. See the setter docstring.

        Returns
        -------
        text : str or None
        """
        ...

    @inner_html.setter
    def inner_html(self, html: str):
        """Set inner HTML to the specified HTML.

        Replaces existing data inside the node.
        Works similar to innerHTML in JavaScript.

        Parameters
        ----------
        html : str

        """
        ...

    def clone(self) -> LexborNode:
        """Clone the current node.

        You can use to do temporary modifications without affecting the original HTML tree.

        It is tied to the current parser instance.
        Gets destroyed when parser instance is destroyed.
        """
        ...

class LexborHTMLParser:
    """The lexbor HTML parser.

    Use this class to parse raw HTML.

    This parser mimics most of the stuff from ``HTMLParser`` but not inherits it directly.

    Parameters
    ----------

    html : str (unicode) or bytes
    """

    def __init__(self, html: str | bytes): ...
    @property
    def selector(self) -> "LexborCSSSelector": ...
    @property
    def root(self) -> LexborNode | None:
        """Returns root node."""
        ...
    @property
    def body(self) -> LexborNode | None:
        """Returns document body."""
        ...
    @property
    def head(self) -> LexborNode | None:
        """Returns document head."""
        ...
    def tags(self, name: str) -> list[LexborNode]:
        """Returns a list of tags that match specified name.

        Parameters
        ----------
        name : str (e.g. div)
        """
        ...
    def text(self, deep: bool = True, separator: str = "", strip: bool = False) -> str:
        """Returns the text of the node including text of all its child nodes.

        Parameters
        ----------
        strip : bool, default False
            If true, calls ``str.strip()`` on each text part to remove extra white spaces.
        separator : str, default ''
            The separator to use when joining text from different nodes.
        deep : bool, default True
            If True, includes text from all child nodes.

        Returns
        -------
        text : str
        """
        ...
    @property
    def html(self) -> str | None:
        """Return HTML representation of the page."""
        ...
    def css(self, query: str) -> list[LexborNode]:
        """A CSS selector.

        Matches pattern `query` against HTML tree.
        `CSS selectors reference <https://www.w3schools.com/cssref/css_selectors.asp>`_.

        Special selectors:

         - parser.css('p:lexbor-contains("awesome" i)') -- case-insensitive contains
         - parser.css('p:lexbor-contains("awesome")') -- case-sensitive contains


        Parameters
        ----------
        query : str
            CSS selector (e.g. "div > :nth-child(2n+1):not(:has(a))").

        Returns
        -------
        selector : list of `Node` objects
        """
        ...
    @overload
    def css_first(
        self, query: str, default: Any = ..., strict: Literal[True] = ...
    ) -> LexborNode:
        """Same as `css` but returns only the first match.

        Parameters
        ----------

        query : str
        default : bool, default None
            Default value to return if there is no match.
        strict: bool, default False
            Set to True if you want to check if there is strictly only one match in the document.


        Returns
        -------
        selector : `LexborNode` object
        """
        ...
    @overload
    def css_first(
        self, query: str, default: DefaultT, strict: bool = False
    ) -> LexborNode | DefaultT:
        """Same as `css` but returns only the first match.

        Parameters
        ----------

        query : str
        default : bool, default None
            Default value to return if there is no match.
        strict: bool, default False
            Set to True if you want to check if there is strictly only one match in the document.


        Returns
        -------
        selector : `LexborNode` object
        """
        ...
    @overload
    def css_first(
        self, query: str, default: None = ..., strict: bool = False
    ) -> LexborNode | None:
        """Same as `css` but returns only the first match.

        Parameters
        ----------

        query : str
        default : bool, default None
            Default value to return if there is no match.
        strict: bool, default False
            Set to True if you want to check if there is strictly only one match in the document.


        Returns
        -------
        selector : `LexborNode` object
        """
        ...
    def strip_tags(self, tags: list[str], recursive: bool = False) -> None:
        """Remove specified tags from the node.

        Parameters
        ----------
        tags : list of str
            List of tags to remove.
        recursive : bool, default True
            Whenever to delete all its child nodes

        Examples
        --------

        >>> tree = LexborHTMLParser('<html><head></head><body><script></script><div>Hello world!</div></body></html>')
        >>> tags = ['head', 'style', 'script', 'xmp', 'iframe', 'noembed', 'noframes']
        >>> tree.strip_tags(tags)
        >>> tree.html
        '<html><body><div>Hello world!</div></body></html>'
        """
        ...
    def select(self, query: str | None = None) -> LexborSelector | None:
        """Select nodes give a CSS selector.

        Works similarly to the ``css`` method, but supports chained filtering and extra features.

        Parameters
        ----------
        query : str or None
            The CSS selector to use when searching for nodes.

        Returns
        -------
        selector : The `Selector` class.
        """
        ...
    def any_css_matches(self, selectors: tuple[str]) -> bool:
        """Returns True if any of the specified CSS selectors matches a node."""
        ...
    def scripts_contain(self, query: str) -> bool:
        """Returns True if any of the script tags contain specified text.

        Caches script tags on the first call to improve performance.

        Parameters
        ----------
        query : str
            The query to check.
        """
        ...
    def script_srcs_contain(self, queries: tuple[str]) -> bool:
        """Returns True if any of the script SRCs attributes contain on of the specified text.

        Caches values on the first call to improve performance.

        Parameters
        ----------
        queries : tuple of str
        """
        ...
    def css_matches(self, selector: str) -> bool: ...
    def merge_text_nodes(self) -> None:
        """Iterates over all text nodes and merges all text nodes that are close to each other.

        This is useful for text extraction.
        Use it when you need to strip HTML tags and merge "dangling" text.

        Examples
        --------

        >>> tree = LexborHTMLParser("<div><p><strong>J</strong>ohn</p><p>Doe</p></div>")
        >>> node = tree.css_first('div')
        >>> tree.unwrap_tags(["strong"])
        >>> tree.text(deep=True, separator=" ", strip=True)
        "J ohn Doe" # Text extraction produces an extra space because the strong tag was removed.
        >>> node.merge_text_nodes()
        >>> tree.text(deep=True, separator=" ", strip=True)
        "John Doe"
        """
        ...
    def clone(self) -> LexborHTMLParser:
        """Clone the current tree."""
        ...
    def unwrap_tags(self, tags: list[str], delete_empty: bool = False) -> None:
        """Unwraps specified tags from the HTML tree.

        Works the same as the ``unwrap`` method, but applied to a list of tags.

        Parameters
        ----------
        tags : list
            List of tags to remove.
        delete_empty : bool
            Whenever to delete empty tags.

        Examples
        --------

        >>> tree = LexborHTMLParser("<div><a href="">Hello</a> <i>world</i>!</div>")
        >>> tree.body.unwrap_tags(['i','a'])
        >>> tree.body.html
        '<body><div>Hello world!</div></body>'
        """
        ...

def create_tag(tag: str) -> LexborNode:
    """
    Given an HTML tag name, e.g. `"div"`, create a single empty node for that tag,
    e.g. `"<div></div>"`.
    """
    ...

def parse_fragment(html: str) -> list[LexborNode]:
    """
    Given HTML, parse it into a list of Nodes, such that the nodes
    correspond to the given HTML.

    For contrast, HTMLParser adds `<html>`, `<head>`, and `<body>` tags
    if they are missing. This function does not add these tags.
    """
    ...

class SelectolaxError(Exception):
    """An exception that indicates error."""

    pass
