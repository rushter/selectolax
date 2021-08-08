from libc.stdlib cimport free

_ENCODING = 'UTF-8'

cdef class LexborNode:
    """A class that represents HTML node (element)."""
    cdef lxb_dom_node_t *node
    cdef LexborHTMLParser parser

    cdef _cinit(self, lxb_dom_node_t *node, LexborHTMLParser parser):
        self.parser = parser
        self.node = node
        return self

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
