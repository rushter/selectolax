include "lexbor_node.pxi"
include "utils.pxi"

cdef class LexborHTMLParser:
    def __init__(self, html):

        cdef size_t html_len
        cdef char* html_chars

        bytes_html, html_len = preprocess_input(html)
        self._parse_html(bytes_html, html_len)
        self.raw_html = bytes_html

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
        return LexborNode()._cinit(<lxb_dom_node_t *> self.document, self)

    @property
    def body(self):
        """Returns document body."""
        cdef lxb_html_body_element_t* body
        body = lxb_html_document_body_element_noi(self.document)
        if body == NULL:
            print('no body')
            return None
        return LexborNode()._cinit(<lxb_dom_node_t *> body, self)

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
