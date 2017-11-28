from .parser cimport myhtml_tree_node_t, myencoding_t, myhtml_collection_t, myhtml_tree_t

cdef extern from "mycss/mycss.h" nogil:
    ctypedef unsigned int mystatus_t

    ctypedef struct mycss_entry_t:
        # not completed struct
        mycss_t* mycss

    ctypedef struct mycss_t

    ctypedef struct mycss_selectors_t

    ctypedef struct mycss_selectors_entries_list_t
    ctypedef struct mycss_declaration_entry_t

    ctypedef enum mycss_selectors_flags_t:
        MyCSS_SELECTORS_FLAGS_UNDEF         = 0x00
        MyCSS_SELECTORS_FLAGS_SELECTOR_BAD  = 0x01

    ctypedef struct mycss_selectors_list_t:
        mycss_selectors_entries_list_t* entries_list;
        size_t entries_list_length;

        mycss_declaration_entry_t* declaration_entry;

        mycss_selectors_flags_t flags;

        mycss_selectors_list_t* parent;
        mycss_selectors_list_t* next;
        mycss_selectors_list_t* prev;

    # CSS init routines
    mycss_t * mycss_create()
    mystatus_t mycss_init(mycss_t* mycss)
    mycss_entry_t * mycss_entry_create()
    mystatus_t mycss_entry_init(mycss_t* mycss, mycss_entry_t* entry)

    mycss_selectors_list_t * mycss_selectors_parse(mycss_selectors_t* selectors, myencoding_t encoding,
                                                   const char* data, size_t data_size, mystatus_t* out_status)
    mycss_selectors_t * mycss_entry_selectors(mycss_entry_t* entry)

    mycss_selectors_list_t * mycss_selectors_list_destroy(mycss_selectors_t* selectors,
                                                          mycss_selectors_list_t* selectors_list, bint self_destroy)
    mycss_entry_t * mycss_entry_destroy(mycss_entry_t* entry, bint self_destroy)
    mycss_t * mycss_destroy(mycss_t* mycss, bint self_destroy)



cdef extern from "modest/finder/finder.h" nogil:
    ctypedef struct modest_finder_t
    modest_finder_t* modest_finder_create_simple()
    mystatus_t modest_finder_by_selectors_list(modest_finder_t* finder, myhtml_tree_node_t* scope_node,
                                                mycss_selectors_list_t* selector_list, myhtml_collection_t** collection)
    modest_finder_t * modest_finder_destroy(modest_finder_t* finder, bint self_destroy)

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

    cdef myhtml_collection_t* find(self, myhtml_tree_t *html_tree):
        """Find all possible matches."""

        cdef myhtml_collection_t *collection

        collection = NULL
        modest_finder_by_selectors_list(self.finder, html_tree.node_html, self.selectors_list, &collection)

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


