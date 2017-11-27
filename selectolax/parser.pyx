#cython: boundscheck=False, wraparound=False, nonecheck=False, language_level=3


from libc.stdlib cimport free


class HtmlParser:
    def __init__(self, html, detect_encoding=True, use_meta_tags=True):
        """

        Parameters
        ----------
        html: str (unicode) or bytes
        detect_encoding: Bool, default True
            If `True` and html type is `bytes` then encoding will be detected automatically.
        use_meta_tags: Bool, default True
            Whether to use meta tags in encoding detection process.
        """
        self.html = html

    def css(self, selector):
        """Initialize CSS selector.

        Parameters
        ----------
        selector: str
            CSS selector (e.g. "div > :nth-child(2n+1):not(:has(a))").

        Returns
        -------
        selector : `Selector` object

        """
        return Selector(self.html, selector)


cdef class Node:
    cdef myhtml_tree_node_t *node
    cdef Selector selector

    cdef _init(self, myhtml_tree_node_t *node, Selector selector):
        self.node = node
        # Keep reference to the selector object, so myhtml structures will not be garbage collected prematurely
        self.selector = selector

    @property
    def attributes(self):
        """Get all attributes that belong to the current node.

        Returns
        -------
        attributes: dictionary of all attributes.
            Note that the value of empty attributes is None.

        """
        cdef myhtml_tree_attr_t *attr = myhtml_node_attribute_first(self.node)
        attributes = dict()

        while attr:
            key = attr.key.data.decode('UTF-8')
            if attr.value.data:
                value = attr.value.data.decode('UTF-8')
            else:
                value = None
            attributes[key] = value

            attr = attr.next

        return attributes

    @property
    def text(self):
        """Returns the text of the node including the text of child nodes.

        Returns
        -------
        text : str

        """
        text = None
        cdef const char*c_text
        cdef myhtml_tree_node_t*child = self.node.child

        while child != NULL:
            if child.tag_id == 1:
                c_text = myhtml_node_text(child, NULL)
                if c_text != NULL:
                    if text is None:
                        text = ""
                    text += c_text.decode('utf-8')

            child = child.child
        return text

    @property
    def tag(self):
        """Return the name of the current tag (e.g. div, p, img).

        Returns
        -------
        text : str
        """
        cdef const char *c_text
        c_text = myhtml_tag_name_by_id(self.node.tree, self.node.tag_id, NULL)
        text = None
        if c_text:
            text = c_text.decode("utf-8")
        return text

    @property
    def child(self):
        """Returns the child of current node."""
        cdef Node node
        if self.node.child:
            node = Node()
            node._init(self.node.child, self.selector)
            return node
        return None

    @property
    def parent(self):
        """Returns the parent of current node."""
        cdef Node node
        if self.node.parent:
            node = Node()
            node._init(self.node.parent, self.selector)
            return node
        return None

    @property
    def html(self):
        """Returns html representation of current node including all its child nodes.

        Returns
        -------
        text : str
        """
        cdef mycore_string_raw_t c_str
        c_str.data = NULL
        c_str.length = 0
        c_str.size = 0

        cdef mystatus_t status
        status = myhtml_serialization(self.node, &c_str)

        if status == 0 and c_str.data:
            return c_str.data.decode('utf-8')

        free(c_str.data)
        return None

    def css(self, str selector):
        return Selector(self.html, selector)


cdef class Selector:
    cdef char *c_html
    cdef char *c_selector
    cdef str error

    cdef myhtml_tree_t *html_tree
    cdef mycss_entry_t *css_entry
    cdef modest_finder_t *finder
    cdef mycss_selectors_list_t *selectors_list
    cdef myhtml_collection_t *collection
    cdef myhtml_tree_node_t *tree_node

    def __cinit__(self, str html, str selector):

        html_pybyte = html.encode('UTF-8')
        self.c_html = html_pybyte
        selector_pybyte = selector.encode('UTF-8')
        self.c_selector = selector_pybyte

        # In order to propagate errors all these methods should return no value
        self._parse_html(self.c_html, len(self.c_html))
        self._create_css_parser()
        self._prepare_selector(self.css_entry, self.c_selector, len(self.c_selector))

        self.finder = modest_finder_create_simple()
        self.collection = NULL
        self.tree_node = get_html_node(self.html_tree)

        modest_finder_by_selectors_list(self.finder, self.tree_node, self.selectors_list, &self.collection)

    cpdef find(self):
        """Find all possible matches.
        
        Returns
        -------
        result : list of `Node` objects 
        """
        cdef size_t i

        cdef Node node
        result = list()

        for i in range(self.collection.length):
            node = Node()
            node._init(self.collection.list[i], self)
            result.append(node)
        return result


    cpdef find_one(self):
        result = self.find()

        if len(result) != 1:
            raise ValueError("Expected one css match, found %s " % len(result))

        return result[0]

    cdef  _create_css_parser(self):
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


    cdef _parse_html(self,const char *data, size_t data_size):
        cdef myhtml_t *myhtml = myhtml_create()
        cdef mystatus_t status = myhtml_init(myhtml, MyHTML_OPTIONS_DEFAULT, 1, 0)

        if status != 0:
            raise RuntimeError("Can't init MyHTML object.")


        self.html_tree = myhtml_tree_create()
        status = myhtml_tree_init(self.html_tree, myhtml)

        if status != 0:
            raise RuntimeError("Can't init MyHTML Tree object.")


        status = myhtml_parse(self.html_tree, MyENCODING_UTF_8, data, data_size)

        if status != 0:
            raise RuntimeError("Can't parse HTML:\n%s" % data)


    cdef _prepare_selector(self, mycss_entry_t *css_entry,
                                                   const char *selector, size_t selector_size):
        cdef mystatus_t out_status;
        self.selectors_list = mycss_selectors_parse(mycss_entry_selectors(css_entry),
                                                         MyENCODING_UTF_8,
                                                         selector, selector_size,
                                                         &out_status)

        if (self.selectors_list == NULL) or (self.selectors_list.flags and MyCSS_SELECTORS_FLAGS_SELECTOR_BAD):
            raise  ValueError("Bad CSS Selectors: %s" % self.c_selector.decode('utf-8'))


    def __dealloc__(self):
        destroy_selector(self.finder, self.html_tree, self.css_entry, self.selectors_list, self.collection)
