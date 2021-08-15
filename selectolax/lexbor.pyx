from cpython cimport bool

_ENCODING = 'UTF-8'

include "lexbor/attrs.pxi"
include "lexbor/node.pxi"
include "lexbor/selection.pxi"
include "utils.pxi"

# We don't inherit from HTMLParser here, because it also includes all the C code from Modest.

cdef class LexborHTMLParser:
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
            raise RuntimeError("Failed to initialize object for HTML Document.")

        with nogil:
            status = lxb_html_document_parse(self.document, <lxb_char_t *> html, html_len)
        if status != 0x0000:
            raise RuntimeError("Can't parse HTML.")

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
        return LexborNode()._cinit(<lxb_dom_node_t *> body, self)    @property

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
            raise RuntimeError("Can't locate elements.")

        for i in range(lxb_dom_collection_length_noi(collection)):
            node = LexborNode()._cinit(
                <lxb_dom_node_t*> lxb_dom_collection_element_noi(collection, i),
                self
            )
            result.append(node)
        lxb_dom_collection_destroy(collection, <bint> True)
        return result

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
