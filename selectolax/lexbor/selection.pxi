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
        self.results = []
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
