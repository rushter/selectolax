from libc.stdlib cimport free

_ENCODING = 'UTF-8'

cdef class LexborNode:
    """A class that represents HTML node (element)."""

    cdef _cinit(self, lxb_dom_node_t *node, LexborHTMLParser parser):
        self.parser = parser
        self.node = node
        return self

    @property
    def first_child(self):
        """Return the first child node."""
        cdef LexborNode node
        if self.node.first_child:
            node = LexborNode()
            node._cinit(<lxb_dom_node_t *> self.node.first_child, self.parser)
            return node
        return None

    @property
    def parent(self):
        """Return the parent node."""
        cdef LexborNode node
        if self.node.parent:
            node = LexborNode()
            node._cinit(<lxb_dom_node_t *> self.node.parent, self.parser)
            return node
        return None

    @property
    def next(self):
        """Return next node."""
        cdef LexborNode node
        if self.node.next:
            node = LexborNode()
            node._cinit(<lxb_dom_node_t *> self.node.next, self.parser)
            return node
        return None

    @property
    def prev(self):
        """Return previous node."""
        cdef LexborNode node
        if self.node.prev:
            node = LexborNode()
            node._cinit(<lxb_dom_node_t *> self.node.prev, self.parser)
            return node
        return None

    @property
    def last_child(self):
        """Return last child node."""
        cdef LexborNode node
        if self.node.last_child:
            node = LexborNode()
            node._cinit(<lxb_dom_node_t *> self.node.last_child, self.parser)
            return node
        return None

    @property
    def html(self):
        """Return HTML representation of the current node including all its child nodes.

        Returns
        -------
        text : str
        """
        cdef lexbor_str_t *lxb_str
        cdef lxb_status_t lxb_status_t

        lxb_str = lexbor_str_create()
        status = lxb_html_serialize_tree_str(self.node, lxb_str)
        if status == 0 and lxb_str.data:
            html = lxb_str.data.decode(_ENCODING).replace('<-undef>', '')
            lexbor_str_destroy(lxb_str,  self.node.owner_document.text, True)
            return html
        return None

    def text(self):
        cdef size_t * str_len
        cdef lxb_char_t * text

        # TODO: improve
        text = lxb_dom_node_text_content(self.node, str_len)
        if <int>str_len == 0:
            raise RuntimeError("Can't extract text")

        unicode_text = text.decode(_ENCODING)
        lxb_dom_document_destroy_text_noi(self.node.owner_document, text)
        return unicode_text

    def css(self, str query):
        """Evaluate CSS selector against current node and its child nodes."""
        return self.parser.selector.find(query, self)

    def __repr__(self):
        return '<LexborNode %s>' % self.tag

    @property
    def tag(self):
        cdef lxb_char_t *c_text
        cdef size_t * str_len

        c_text = lxb_dom_element_qualified_name(<lxb_dom_element_t *> self.node, str_len)
        text = None
        if c_text:
            text = c_text.decode(_ENCODING)
        return text


cdef class LexborCSSSelector:

    def __init__(self):
        self._create_css_parser()
        self.results = []
        self.current_node = None

    cdef _create_css_parser(self):
        cdef lxb_status_t status


        self.parser = lxb_css_parser_create()
        status = lxb_css_parser_init(self.parser, NULL, NULL)

        if status != 0x0000:
            raise RuntimeError("Can't initialize CSS parser.")

        self.css_selectors = lxb_css_selectors_create()
        status = lxb_css_selectors_init(self.css_selectors, 32)

        if status != 0x0000:
            raise RuntimeError("Can't initialize CSS selector.")

        lxb_css_parser_selectors_set(self.parser, self.css_selectors)

        self.selectors = lxb_selectors_create()
        status = lxb_selectors_init(self.selectors)

        if status != 0x0000:
            raise RuntimeError("Can't initialize CSS selector.")


    cpdef find(self, str query, LexborNode node):
        cdef lxb_css_selector_list_t* selectors
        cdef lxb_char_t* c_selector
        cdef lxb_css_selector_list_t * selectors_list

        bytes_query = query.encode(_ENCODING)
        selectors_list = lxb_css_selectors_parse(self.parser, <lxb_char_t *> bytes_query, <size_t>len(query))

        if selectors_list == NULL:
            raise ValueError("Can't parse CSS selector.")

        self.current_node = node
        status = lxb_selectors_find(self.selectors, node.node, selectors_list,
                                    <lxb_selectors_cb_f>css_finder_callback, <void*>self)
        results = list(self.results)
        self.results = []
        self.current_node = None
        return results

    def __dealloc__(self):
        lxb_selectors_destroy(self.selectors, True)
        lxb_css_parser_destroy(self.parser, True)
        lxb_css_selectors_destroy(self.css_selectors, True, True)


cdef lxb_status_t css_finder_callback(lxb_dom_node_t *node, lxb_css_selector_specificity_t *spec, void *ctx):
    cdef LexborNode lxb_node
    cdef object cls
    cls = <object> ctx
    lxb_node = LexborNode()
    lxb_node._cinit(<lxb_dom_node_t *> node, cls.current_node.parser)
    cls.results.append(lxb_node)

