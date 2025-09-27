from typing import Iterator, Literal, TypeVar, overload

DefaultT = TypeVar("DefaultT")

class _Attributes:
    """A dict-like object that represents attributes."""

    @staticmethod
    def create(node: Node, decode_errors: str) -> _Attributes: ...
    def keys(self) -> Iterator[str]: ...
    def items(self) -> Iterator[tuple[str, str | None]]: ...
    def values(self) -> Iterator[str | None]: ...
    def __iter__(self) -> Iterator[str]: ...
    def __len__(self) -> int: ...
    def __getitem__(self, key: str) -> str | None: ...
    def __setitem__(self, key: str, value: str) -> None: ...
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
    def sget(self, key: str, default: str = "") -> str:
        """Same as get, but returns empty strings instead of None values for empty attributes."""
        ...

class Selector:
    """An advanced CSS selector that supports additional operations.

    Think of it as a toolkit that mimics some of the features of XPath.

    Please note, this is an experimental feature that can change in the future."""

    def __init__(self, node: Node, query: str): ...
    def css(self, query: str) -> Node:
        """Evaluate CSS selector against current scope."""
        ...
    @property
    def matches(self) -> list[Node]:
        """Returns all possible selector matches"""
        ...
    @property
    def any_matches(self) -> bool:
        """Returns True if there are any matches"""
        ...
    def text_contains(
        self, text: str, deep: bool = True, separator: str = "", strip: bool = False
    ) -> Selector:
        """Filter all current matches given text."""
        ...
    def any_text_contains(
        self, text: str, deep: bool = True, separator: str = "", strip: bool = False
    ) -> bool:
        """Returns True if any node in the current search scope contains specified text"""
        ...
    def attribute_longer_than(
        self, text: str, length: int, start: str | None = None
    ) -> Selector:
        """Filter all current matches by attribute length.

        Similar to string-length in XPath."""
        ...
    def any_attribute_longer_than(
        self, text: str, length: int, start: str | None = None
    ) -> bool:
        """Returns True any href attribute longer than a specified length.

        Similar to string-length in XPath."""
        ...

class Node:
    """A class that represents HTML node (element)."""

    parser: HTMLParser
    @property
    def attributes(self) -> dict[str, str | None]:
        """Get all attributes that belong to the current node.

        The value of empty attributes is None.

        Returns
        -------
        attributes : dictionary of all attributes.

        Examples
        --------

        >>> tree = HTMLParser("<div data id='my_id'></div>")
        >>> node = tree.css_first('div')
        >>> node.attributes
        {'data': None, 'id': 'my_id'}
        """
        ...
    @property
    def attrs(self) -> _Attributes:
        """A dict-like object that is similar to the ``attributes`` property, but operates directly on the Node data.

        .. warning:: Use ``attributes`` instead, if you don't want to modify Node attributes.

        Returns
        -------
        attributes : Attributes mapping object.

        Examples
        --------

        >>> tree = HTMLParser("<div id='a'></div>")
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

    def mem_id(self) -> int:
        """Get the mem_id attribute of the node.

        Returns
        -------
        text : int
        """
        ...

    def __hash__(self) -> int:
        """Get the hash of this node
        :return: int
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
    def iter(self, include_text: bool = False) -> Iterator[Node]:
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
    def traverse(self, include_text: bool = False) -> Iterator[Node]:
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
    @property
    def tag(self) -> str:
        """Return the name of the current tag (e.g. div, p, img).

        Returns
        -------
        text : str
        """
        ...
    @property
    def child(self) -> Node | None:
        """Alias for the `first_child` property.

        **Deprecated**. Please use `first_child` instead.
        """
        ...
    @property
    def parent(self) -> Node | None:
        """Return the parent node."""
        ...
    @property
    def next(self) -> Node | None:
        """Return next node."""
        ...
    @property
    def prev(self) -> Node | None:
        """Return previous node."""
        ...
    @property
    def last_child(self) -> Node | None:
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
    def css(self, query: str) -> list[Node]:
        """Evaluate CSS selector against current node and its child nodes."""
        ...
    def any_css_matches(self, selectors: tuple[str]) -> bool:
        """Returns True if any of CSS selectors matches a node"""
        ...
    def css_matches(self, selector: str) -> bool:
        """Returns True if CSS selector matches a node."""
        ...
    @overload
    def css_first(
        self, query: str, default: DefaultT, strict: bool = False
    ) -> Node | DefaultT: ...
    @overload
    def css_first(
        self, query: str, default: None = None, strict: bool = False
    ) -> Node | None | DefaultT:
        """Evaluate CSS selector against current node and its child nodes."""
        ...
    def decompose(self, recursive: bool = True) -> None:
        """Remove a Node from the tree.

        Parameters
        ----------
        recursive : bool, default True
            Whenever to delete all its child nodes

        Examples
        --------

        >>> tree = HTMLParser(html)
        >>> for tag in tree.css('script'):
        >>>     tag.decompose()
        """
        ...
    def remove(self, recursive: bool = True) -> None:
        """An alias for the decompose method."""
        ...
    def unwrap(self, delete_empty: bool = False) -> None:
        """Replace node with whatever is inside this node.

        Parameters
        ----------
        delete_empty : bool, default False
            Whenever to delete empty tags.

        Examples
        --------

        >>>  tree = HTMLParser("<div>Hello <i>world</i>!</div>")
        >>>  tree.css_first('i').unwrap()
        >>>  tree.html
        '<html><head></head><body><div>Hello world!</div></body></html>'

        Note: by default, empty tags are ignored, set "delete_empty" to "True" to change this.
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

        >>> tree = HTMLParser('<html><head></head><body><script></script><div>Hello world!</div></body></html>')
        >>> tags = ['head', 'style', 'script', 'xmp', 'iframe', 'noembed', 'noframes']
        >>> tree.strip_tags(tags)
        >>> tree.html
        '<html><body><div>Hello world!</div></body></html>'
        """
        ...
    def unwrap_tags(self, tags: list[str], delete_empty: bool = False) -> None:
        """Unwraps specified tags from the HTML tree.

        Works the same as the unwrap method, but applied to a list of tags.

        Parameters
        ----------
        tags : list
            List of tags to remove.
        delete_empty : bool, default False
            Whenever to delete empty tags.

        Examples
        --------

        >>> tree = HTMLParser("<div><a href="">Hello</a> <i>world</i>!</div>")
        >>> tree.body.unwrap_tags(['i','a'])
        >>> tree.body.html
        '<body><div>Hello world!</div></body>'

        Note: by default, empty tags are ignored, set "delete_empty" to "True" to change this.
        """
        ...
    def replace_with(self, value: str | bytes | None) -> None:
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

        >>> tree = HTMLParser('<div>Get <img src="" alt="Laptop"></div>')
        >>> img = tree.css_first('img')
        >>> img.replace_with(img.attributes.get('alt', ''))
        >>> tree.body.child.html
        '<div>Get Laptop</div>'

        >>> html_parser = HTMLParser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
        >>> html_parser2 = HTMLParser('<div>Test</div>')
        >>> img_node = html_parser.css_first('img')
        >>> img_node.replace_with(html_parser2.body.child)
        '<div>Get <span alt="Laptop"><div>Test</div> <div></div></span></div>'
        """
        ...
    def insert_before(self, value: str | bytes | None) -> None:
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

        >>> tree = HTMLParser('<div>Get <img src="" alt="Laptop"></div>')
        >>> img = tree.css_first('img')
        >>> img.insert_before(img.attributes.get('alt', ''))
        >>> tree.body.child.html
        '<div>Get Laptop<img src="" alt="Laptop"></div>'

        >>> html_parser = HTMLParser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
        >>> html_parser2 = HTMLParser('<div>Test</div>')
        >>> img_node = html_parser.css_first('img')
        >>> img_node.insert_before(html_parser2.body.child)
        <div>Get <span alt="Laptop"><div>Test</div><img src="/jpg"> <div></div></span></div>'
        """
        ...
    def insert_after(self, value: str | bytes | None) -> None:
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

        >>> tree = HTMLParser('<div>Get <img src="" alt="Laptop"></div>')
        >>> img = tree.css_first('img')
        >>> img.insert_after(img.attributes.get('alt', ''))
        >>> tree.body.child.html
        '<div>Get <img src="" alt="Laptop">Laptop</div>'

        >>> html_parser = HTMLParser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
        >>> html_parser2 = HTMLParser('<div>Test</div>')
        >>> img_node = html_parser.css_first('img')
        >>> img_node.insert_after(html_parser2.body.child)
        <div>Get <span alt="Laptop"><img src="/jpg"><div>Test</div> <div></div></span></div>'
        """
        ...
    def insert_child(self, value: str | bytes | None) -> None:
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

        >>> tree = HTMLParser('<div>Get <img src=""></div>')
        >>> div = tree.css_first('div')
        >>> div.insert_child('Laptop')
        >>> tree.body.child.html
        '<div>Get <img src="">Laptop</div>'

        >>> html_parser = HTMLParser('<div>Get <span alt="Laptop"> <div>Laptop</div> </span></div>')
        >>> html_parser2 = HTMLParser('<div>Test</div>')
        >>> span_node = html_parser.css_first('span')
        >>> span_node.insert_child(html_parser2.body.child)
        <div>Get <span alt="Laptop"> <div>Laptop</div> <div>Test</div> </span></div>'
        """
        ...
    @property
    def raw_value(self) -> bytes:
        """Return the raw (unparsed, original) value of a node.

        Currently, works on text nodes only.

        Returns
        -------

        raw_value : bytes

        Examples
        --------

        >>> html_parser = HTMLParser('<div>&#x3C;test&#x3E;</div>')
        >>> selector = html_parser.css_first('div')
        >>> selector.child.html
        '&lt;test&gt;'
        >>> selector.child.raw_value
        b'&#x3C;test&#x3E;'
        """
        ...
    def select(self, query: str | None = None) -> Selector:
        """Select nodes given a CSS selector.

        Works similarly to the css method, but supports chained filtering and extra features.

        Parameters
        ----------
        query : str or None
            The CSS selector to use when searching for nodes.

        Returns
        -------
        selector : The `Selector` class.
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
    def merge_text_nodes(self):
        """Iterates over all text nodes and merges all text nodes that are close to each other.

        This is useful for text extraction.
        Use it when you need to strip HTML tags and merge "dangling" text.

        Examples
        --------

        >>> tree = HTMLParser("<div><p><strong>J</strong>ohn</p><p>Doe</p></div>")
        >>> node = tree.css_first('div')
        >>> tree.unwrap_tags(["strong"])
        >>> tree.text(deep=True, separator=" ", strip=True)
        "J ohn Doe" # Text extraction produces an extra space because the strong tag was removed.
        >>> node.merge_text_nodes()
        >>> tree.text(deep=True, separator=" ", strip=True)
        "John Doe"
        """
        ...

class HTMLParser:
    """The HTML parser.

    Use this class to parse raw HTML.

    Parameters
    ----------

    html : str (unicode) or bytes
    detect_encoding : bool, default True
        If `True` and html type is `bytes` then encoding will be detected automatically.
    use_meta_tags : bool, default True
        Whether to use meta tags in encoding detection process.
    decode_errors : str, default 'ignore'
        Same as in builtin's str.decode, i.e 'strict', 'ignore' or 'replace'.
    """

    def __init__(
        self,
        html: bytes | str,
        detect_encoding: bool = True,
        use_meta_tags: bool = True,
        decode_errors: Literal["strict", "ignore", "replace"] = "ignore",
    ): ...
    def css(self, query: str) -> list[Node]:
        """A CSS selector.

        Matches pattern `query` against HTML tree.
        `CSS selectors reference <https://www.w3schools.com/cssref/css_selectors.asp>`_.

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
        self, query: str, default: DefaultT, strict: bool = False
    ) -> Node | DefaultT: ...
    @overload
    def css_first(
        self, query: str, default: None = None, strict: bool = False
    ) -> Node | None | DefaultT:
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
        selector : `Node` object
        """
        ...
    @property
    def input_encoding(self) -> str:
        """Return encoding of the HTML document.

        Returns `unknown` in case the encoding is not determined.
        """
        ...
    @property
    def root(self) -> Node | None:
        """Returns root node."""
        ...
    @property
    def head(self) -> Node | None:
        """Returns head node."""
        ...
    @property
    def body(self) -> Node | None:
        """Returns document body."""
        ...
    def tags(self, name: str) -> list[Node]:
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

        >>> tree = HTMLParser('<html><head></head><body><script></script><div>Hello world!</div></body></html>')
        >>> tags = ['head', 'style', 'script', 'xmp', 'iframe', 'noembed', 'noframes']
        >>> tree.strip_tags(tags)
        >>> tree.html
        '<html><body><div>Hello world!</div></body></html>'
        """
        ...
    def unwrap_tags(self, tags: list[str], delete_empty: bool = False) -> None:
        """Unwraps specified tags from the HTML tree.

        Works the same as th unwrap method, but applied to a list of tags.

        Parameters
        ----------
        tags : list
            List of tags to remove.
        delete_empty : bool, default False
            If True, removes empty tags.

        Examples
        --------

        >>> tree = HTMLParser("<div><a href="">Hello</a> <i>world</i>!</div>")
        >>> tree.head.unwrap_tags(['i','a'])
        >>> tree.head.html
        '<body><div>Hello world!</div></body>'
        """
        ...
    @property
    def html(self) -> str | None:
        """Return HTML representation of the page."""
        ...
    def select(self, query: str | None = None) -> Selector | None:
        """Select nodes given a CSS selector.

        Works similarly to  the ``css`` method, but supports chained filtering and extra features.

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
    def scripts_srcs_contain(self, queries: tuple[str]) -> bool:
        """Returns True if any of the script SRCs attributes contain on of the specified text.

        Caches values on the first call to improve performance.

        Parameters
        ----------
        queries : tuple of str
        """
        ...
    def css_matches(self, selector: str) -> bool: ...
    def clone(self) -> HTMLParser:
        """Clone the current tree."""
        ...
    def merge_text_nodes(self):
        """Iterates over all text nodes and merges all text nodes that are close to each other.

        This is useful for text extraction.
        Use it when you need to strip HTML tags and merge "dangling" text.

        Examples
        --------

        >>> tree = HTMLParser("<div><p><strong>J</strong>ohn</p><p>Doe</p></div>")
        >>> node = tree.css_first('div')
        >>> tree.unwrap_tags(["strong"])
        >>> tree.text(deep=True, separator=" ", strip=True)
        "J ohn Doe" # Text extraction produces an extra space because the strong tag was removed.
        >>> node.merge_text_nodes()
        >>> tree.text(deep=True, separator=" ", strip=True)
        "John Doe"
        """
        ...

def create_tag(tag: str) -> Node:
    """
    Given an HTML tag name, e.g. `"div"`, create a single empty node for that tag,
    e.g. `"<div></div>"`.
    """
    ...

def parse_fragment(html: str) -> list[Node]:
    """
    Given HTML, parse it into a list of Nodes, such that the nodes
    correspond to the given HTML.

    For contrast, HTMLParser adds `<html>`, `<head>`, and `<body>` tags
    if they are missing. This function does not add these tags.
    """
    ...
