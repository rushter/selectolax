
cdef class Selector:

    cdef char *c_selector
    cdef mycss_entry_t *css_entry
    cdef modest_finder_t *finder
    cdef mycss_selectors_list_t *selectors_list

    def __init__(self, str selector):

        selector_pybyte = selector.encode('UTF-8')
        self.c_selector = selector_pybyte

        # In order to propagate errors these methods should return no value
        self._create_css_parser()
        self._prepare_selector(self.css_entry, self.c_selector, len(self.c_selector))
        self.finder = modest_finder_create_simple()

    cdef myhtml_collection_t* find(self, myhtml_tree_node_t* scope):
        """Find all possible matches."""

        cdef myhtml_collection_t *collection

        collection = NULL
        modest_finder_by_selectors_list(self.finder, scope, self.selectors_list, &collection)

        return collection


    cdef _create_css_parser(self):
        cdef mystatus_t status

        cdef mycss_t *mycss = mycss_create()
        status = mycss_init(mycss)

        if status != 0:
            raise RuntimeError("Can't init MyCSS object.")
            # return

        self.css_entry = mycss_entry_create()
        status = mycss_entry_init(mycss, self.css_entry)

        if status != 0:
            raise RuntimeError("Can't init MyCSS Entry object.")



    cdef _prepare_selector(self, mycss_entry_t *css_entry,
                                                   const char *selector, size_t selector_size):
        cdef mystatus_t out_status;
        self.selectors_list = mycss_selectors_parse(mycss_entry_selectors(css_entry),
                                                         myencoding_t.MyENCODING_UTF_8,
                                                         selector, selector_size,
                                                         &out_status)

        if (self.selectors_list == NULL) or (self.selectors_list.flags and MyCSS_SELECTORS_FLAGS_SELECTOR_BAD):
            raise  ValueError("Bad CSS Selectors: %s" % self.c_selector.decode('utf-8'))

    def __dealloc__(self):
        mycss_selectors_list_destroy(mycss_entry_selectors(self.css_entry), self.selectors_list, 1)
        modest_finder_destroy(self.finder, 1)

        cdef mycss_t *mycss = self.css_entry.mycss
        mycss_entry_destroy(self.css_entry, 1)
        mycss_destroy(mycss, 1)


