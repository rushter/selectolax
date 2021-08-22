from cpython cimport bool

_ENCODING = 'UTF-8'

include "base.pxi"
include "utils.pxi"
include "lexbor/attrs.pxi"
include "lexbor/node.pxi"
include "lexbor/selection.pxi"

# We don't inherit from HTMLParser here, because it also includes all the C code from Modest.

cdef class LexborHTMLParser:
    """The lexbor HTML parser.

    Use this class to parse raw HTML.

    This parser mimics most of the stuff from ``HTMLParser`` but not inherits in directly.

    Parameters
    ----------

    html : str (unicode) or bytes
    """
    def __init__(self, html):

        cdef size_t html_len
        cdef char* html_chars

        bytes_html, html_len = preprocess_input(html)
        self._parse_html(bytes_html, html_len)
        self.raw_html = bytes_html
        self._selector = None

    @property
    def selector(self):
        if self._selector is None:
            self._selector = LexborCSSSelector()
        return self._selector


    cdef _parse_html(self, char *html, size_t html_len):
        cdef lxb_status_t status

        with nogil:
            self.document = lxb_html_document_create()

        if self.document == NULL:
            raise SelectolaxError("Failed to initialize object for HTML Document.")

        with nogil:
            status = lxb_html_document_parse(self.document, <lxb_char_t *> html, html_len)
        if status != 0x0000:
            raise SelectolaxError("Can't parse HTML.")

        assert self.document != NULL

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
        return LexborNode()._cinit(<lxb_dom_node_t *> lxb_dom_document_root(&self.document.dom_document), self)

    @property
    def body(self):
        """Returns document body."""
        cdef lxb_html_body_element_t* body
        body = lxb_html_document_body_element_noi(self.document)
        if body == NULL:
            return None
        return LexborNode()._cinit(<lxb_dom_node_t *> body, self)

    @property
    def head(self):
        """Returns document head."""
        cdef lxb_html_head_element_t* head
        head = lxb_html_document_head_element_noi(self.document)
        if head == NULL:
            return None
        return LexborNode()._cinit(<lxb_dom_node_t *> head, self)

    def tags(self, str name):
        """Returns a list of tags that match specified name.

        Parameters
        ----------
        name : str (e.g. div)

        """
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
            raise SelectolaxError("Can't locate elements.")

        for i in range(lxb_dom_collection_length_noi(collection)):
            node = LexborNode()._cinit(
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
        return self.body.text(deep=deep, separator=separator, strip=strip)

    @property
    def html(self):
        """Return HTML representation of the page."""
        return self.root.html

    def css(self, str query):
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
        return self.root.css(query)

    def css_first(self, str query, default=None, strict=False):
        """Same as `css` but returns only the first match.

        Parameters
        ----------

        query : str
        default : bool, default None
            Default value to return if there is no match.
        strict: bool, default True
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
                raise SelectolaxError("Can't locate elements.")

            for i in range(lxb_dom_collection_length_noi(collection)):
                if recursive:
                    lxb_dom_node_destroy( <lxb_dom_node_t*> lxb_dom_collection_element_noi(collection, i))
                else:
                    lxb_dom_node_destroy_deep( <lxb_dom_node_t*> lxb_dom_collection_element_noi(collection, i))
            lxb_dom_collection_destroy(collection, <bint> True)

    def select(self, query=None):
        """Select nodes give a CSS selector.

        Works similarly to the the ``css`` method, but supports chained filtering and extra features.

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
        """Clone the current tree."""
        cdef lxb_html_document_t* cloned_document
        cdef lxb_dom_node_t* cloned_node

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
