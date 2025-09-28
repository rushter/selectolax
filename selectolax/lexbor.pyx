from cpython.bool cimport bool
from cpython.exc cimport PyErr_SetObject


_ENCODING = 'UTF-8'

include "base.pxi"
include "utils.pxi"
include "lexbor/attrs.pxi"
include "lexbor/node.pxi"
include "lexbor/selection.pxi"
include "lexbor/util.pxi"
include "lexbor/node_remove.pxi"

# We don't inherit from HTMLParser here, because it also includes all the C code from Modest.

cdef class LexborHTMLParser:
    """The lexbor HTML parser.

    Use this class to parse raw HTML.

    This parser mimics most of the stuff from ``HTMLParser`` but not inherits it directly.

    Parameters
    ----------

    html : str (unicode) or bytes
    """
    def __init__(self, html):
        cdef size_t html_len
        cdef object bytes_html
        bytes_html, html_len = preprocess_input(html)
        self._parse_html(bytes_html, html_len)
        self.raw_html = bytes_html
        self._selector = None

    @property
    def selector(self):
        if self._selector is None:
            self._selector = LexborCSSSelector()
        return self._selector

    cdef int _parse_html(self, char *html, size_t html_len) except -1:
        cdef lxb_status_t status

        with nogil:
            self.document = lxb_html_document_create()

        if self.document == NULL:
            PyErr_SetObject(SelectolaxError, "Failed to initialize object for HTML Document.")
            return -1

        with nogil:
            status = lxb_html_document_parse(self.document, <lxb_char_t *> html, html_len)

        if status != 0x0000:
            PyErr_SetObject(SelectolaxError, "Can't parse HTML.")
            return -1

        if self.document == NULL:
            PyErr_SetObject(RuntimeError, "document is NULL even after html was parsed correctly")
            return -1
        return 0

    def __dealloc__(self):
        if self.document != NULL:
            lxb_html_document_destroy(self.document)

    def __repr__(self):
        return '<LexborHTMLParser chars=%s>' % len(self.root.html)

    @property
    def root(self):
        """Returns root node."""
        if self.document == NULL:
            return None
        return LexborNode.new(<lxb_dom_node_t *> lxb_dom_document_root(&self.document.dom_document), self)

    @property
    def body(self):
        """Returns document body."""
        cdef lxb_html_body_element_t* body
        body = lxb_html_document_body_element_noi(self.document)
        if body == NULL:
            return None
        return LexborNode.new(<lxb_dom_node_t *> body, self)

    @property
    def head(self):
        """Returns document head."""
        cdef lxb_html_head_element_t* head
        head = lxb_html_document_head_element_noi(self.document)
        if head == NULL:
            return None
        return LexborNode.new(<lxb_dom_node_t *> head, self)

    def tags(self, str name):
        """Returns a list of tags that match specified name.

        Parameters
        ----------
        name : str (e.g. div)

        """

        if not name:
            raise ValueError("Tag name cannot be empty")
        if len(name) > 100:
            raise ValueError("Tag name is too long")

        cdef lxb_dom_collection_t* collection = NULL
        cdef lxb_status_t status
        pybyte_name = name.encode('UTF-8')

        result = list()
        collection = lxb_dom_collection_make(&self.document.dom_document, 128)

        if collection == NULL:
            return result
        status = lxb_dom_elements_by_tag_name(
            <lxb_dom_element_t *> self.document,
            collection,
            <lxb_char_t *> pybyte_name,
            len(pybyte_name)
        )
        if status != 0x0000:
            lxb_dom_collection_destroy(collection, <bint> True)
            raise SelectolaxError("Can't locate elements.")

        for i in range(lxb_dom_collection_length_noi(collection)):
            node = LexborNode.new(
                <lxb_dom_node_t*> lxb_dom_collection_element_noi(collection, i),
                self
            )
            result.append(node)
        lxb_dom_collection_destroy(collection, <bint> True)
        return result

    def text(self, bool deep=True, str separator='', bool strip=False):
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
        if self.body is None:
            return ""
        return self.body.text(deep=deep, separator=separator, strip=strip)

    @property
    def html(self):
        """Return HTML representation of the page."""
        if self.document == NULL:
            return None
        node = LexborNode.new(<lxb_dom_node_t *> &self.document.dom_document, self)
        return node.html

    def css(self, str query):
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
        return self.root.css(query)

    def css_first(self, str query, default=None, strict=False):
        """Same as `css` but returns only the first match.

        Parameters
        ----------

        query : str
        default : Any, default None
            Default value to return if there is no match.
        strict: bool, default False
            Set to True if you want to check if there is strictly only one match in the document.


        Returns
        -------
        selector : `LexborNode` object
        """
        return self.root.css_first(query, default, strict)

    def strip_tags(self, list tags, bool recursive = False):
        """Remove specified tags from the node.

        Parameters
        ----------
        tags : list of str
            List of tags to remove.
        recursive : bool, default False
            Whenever to delete all its child nodes

        Examples
        --------

        >>> tree = LexborHTMLParser('<html><head></head><body><script></script><div>Hello world!</div></body></html>')
        >>> tags = ['head', 'style', 'script', 'xmp', 'iframe', 'noembed', 'noframes']
        >>> tree.strip_tags(tags)
        >>> tree.html
        '<html><body><div>Hello world!</div></body></html>'

        """
        cdef lxb_dom_collection_t* collection = NULL
        cdef lxb_status_t status

        for tag in tags:
            pybyte_name = tag.encode('UTF-8')

            collection = lxb_dom_collection_make(&self.document.dom_document, 128)

            if collection == NULL:
                raise SelectolaxError("Can't initialize DOM collection.")

            status = lxb_dom_elements_by_tag_name(
                <lxb_dom_element_t *> self.document,
                collection,
                <lxb_char_t *> pybyte_name,
                len(pybyte_name)
            )
            if status != 0x0000:
                lxb_dom_collection_destroy(collection, <bint> True)
                raise SelectolaxError("Can't locate elements.")

            for i in range(lxb_dom_collection_length_noi(collection)):
                if recursive:
                    lxb_dom_node_destroy_deep(<lxb_dom_node_t*> lxb_dom_collection_element_noi(collection, i))
                else:
                    lxb_dom_node_destroy(<lxb_dom_node_t *> lxb_dom_collection_element_noi(collection, i))
            lxb_dom_collection_destroy(collection, <bint> True)

    def select(self, query=None):
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
        cdef LexborNode node
        node = self.root
        if node:
            return LexborSelector(node, query)

    def any_css_matches(self, tuple selectors):
        """Returns True if any of the specified CSS selectors matches a node."""
        return self.root.any_css_matches(selectors)

    def scripts_contain(self, str query):
        """Returns True if any of the script tags contain specified text.

        Caches script tags on the first call to improve performance.

        Parameters
        ----------
        query : str
            The query to check.

        """
        return self.root.scripts_contain(query)

    def script_srcs_contain(self, tuple queries):
        """Returns True if any of the script SRCs attributes contain on of the specified text.

        Caches values on the first call to improve performance.

        Parameters
        ----------
        queries : tuple of str

        """
        return self.root.script_srcs_contain(queries)

    def css_matches(self, str selector):
        return self.root.css_matches(selector)

    def merge_text_nodes(self):
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
        return self.root.merge_text_nodes()

    @staticmethod
    cdef LexborHTMLParser from_document(lxb_html_document_t *document, bytes raw_html):
        obj = <LexborHTMLParser> LexborHTMLParser.__new__(LexborHTMLParser)
        obj.document = document
        obj.raw_html = raw_html
        obj.cached_script_texts = None
        obj.cached_script_srcs = None
        obj._selector = None
        return obj

    def clone(self):
        """Clone the current node.

        You can use to do temporary modifications without affecting the original HTML tree.

        It is tied to the current parser instance.
        Gets destroyed when parser instance is destroyed.
        """
        cdef lxb_html_document_t* cloned_document
        cdef lxb_dom_node_t* cloned_node
        cdef LexborHTMLParser cls

        with nogil:
            cloned_document = lxb_html_document_create()

        if cloned_document == NULL:
            raise SelectolaxError("Can't create a new document")

        cloned_document.ready_state = LXB_HTML_DOCUMENT_READY_STATE_COMPLETE

        with nogil:
            cloned_node = lxb_dom_document_import_node(
                &cloned_document.dom_document,
                <lxb_dom_node_t *> lxb_dom_document_root(&self.document.dom_document),
                <bint> True
            )

        if cloned_node == NULL:
            raise SelectolaxError("Can't create a new document")

        with nogil:
            lxb_dom_node_insert_child(<lxb_dom_node_t * > cloned_document, cloned_node)

        cls = LexborHTMLParser.from_document(cloned_document, self.raw_html)
        return cls

    def unwrap_tags(self, list tags, delete_empty = False):
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
        # faster to check if the document is empty which should determine if we have a root
        if self.document != NULL:
            self.root.unwrap_tags(tags, delete_empty=delete_empty)

    @property
    def inner_html(self) -> str:
        """Return HTML representation of the child nodes.

        Works similar to innerHTML in JavaScript.
        Unlike the `.html` property, does not include the current node.
        Can be used to set HTML as well. See the setter docstring.

        Returns
        -------
        text : str | None
        """
        return self.root.inner_html

    @inner_html.setter
    def inner_html(self, str html):
        """Set inner HTML to the specified HTML.

        Replaces existing data inside the node.
        Works similar to innerHTML in JavaScript.

        Parameters
        ----------
        html : str

        """
        self.root.inner_html = html
