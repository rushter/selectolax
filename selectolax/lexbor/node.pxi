from libc.stdlib cimport free

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
        cdef size_t str_len = 0
        cdef lxb_char_t * text

        # TODO: improve
        text = lxb_dom_node_text_content(self.node, &str_len)
        if <int>str_len == 0:
            raise RuntimeError("Can't extract text")

        unicode_text = text.decode(_ENCODING)
        lxb_dom_document_destroy_text_noi(self.node.owner_document, text)
        return unicode_text

    def css(self, str query):
        """Evaluate CSS selector against current node and its child nodes.

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
        return self.parser.selector.find(query, self)

    def css_first(self, str query, default=None, bool strict=False):
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
        results = self.css(query)
        n_results = len(results)
        if n_results > 0:
            if strict and n_results > 1:
                raise ValueError("Expected 1 match, but found %s matches" % n_results)
            return results[0]
        return default


    def __repr__(self):
        return '<LexborNode %s>' % self.tag

    @property
    def tag(self):
        """Return the name of the current tag (e.g. div, p, img).

        Returns
        -------
        text : str
        """

        cdef lxb_char_t *c_text
        cdef size_t str_len = 0

        c_text = lxb_dom_element_qualified_name(<lxb_dom_element_t *> self.node, &str_len)
        text = None
        if c_text:
            text = c_text.decode(_ENCODING)
        return text


    def decompose(self, bool recursive=True):
        """Remove the current node from the tree.

        Parameters
        ----------
        recursive : bool, default True
            Whenever to delete all its child nodes

        Examples
        --------

        >>> tree = LexborHTMLParser(html)
        >>> for tag in tree.css('script'):
        >>>     tag.decompose()

        """
        if recursive:
            lxb_dom_node_destroy(<lxb_dom_node_t *>self.node)
        else:
            lxb_dom_node_destroy_deep(<lxb_dom_node_t *>self.node)

    @property
    def attributes(self):
        """Get all attributes that belong to the current node.

        The value of empty attributes is None.

        Returns
        -------
        attributes : dictionary of all attributes.

        Examples
        --------

        >>> tree = LexborHTMLParser("<div data id='my_id'></div>")
        >>> node = tree.css_first('div')
        >>> node.attributes
        {'data': None, 'id': 'my_id'}
        """
        cdef lxb_dom_attr_t *attr = lxb_dom_element_first_attribute_noi(<lxb_dom_element_t *> self.node)
        cdef size_t str_len = 0
        attributes = dict()

        while attr != NULL:
            key = lxb_dom_attr_local_name_noi(attr, &str_len)
            value = lxb_dom_attr_value_noi(attr, &str_len)

            if value:
                py_value = value.decode(_ENCODING)
            else:
                py_value = None
            attributes[key.decode(_ENCODING)] = py_value

            attr = attr.next
        return attributes

    @property
    def attrs(self):
        """A dict-like object that is similar to the ``attributes`` property, but operates directly on the Node data.

        .. warning:: Use ``attributes`` instead, if you don't want to modify Node attributes.

        Returns
        -------
        attributes : Attributes mapping object.

        Examples
        --------

        >>> tree = HTMLParser("<div id='a'></div>")
        >>> node = tree.css_first('div')
        >>> node.attrs
        <div attributes, 1 items>
        >>> node.attrs['id']
        'a'
        >>> node.attrs['foo'] = 'bar'
        >>> del node.attrs['id']
        >>> node.attributes
        {'foo': 'bar'}
        >>> node.attrs['id'] = 'new_id'
        >>> node.html
        '<div foo="bar" id="new_id"></div>'
        """
        cdef LexborAttributes attributes = LexborAttributes.create(<lxb_dom_node_t *>self.node)
        return attributes


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


cdef lxb_status_t css_finder_callback(lxb_dom_node_t *node, lxb_css_selector_specificity_t *spec, void *ctx):
    cdef LexborNode lxb_node
    cdef object cls
    cls = <object> ctx
    lxb_node = LexborNode()
    lxb_node._cinit(<lxb_dom_node_t *> node, cls.current_node.parser)
    cls.results.append(lxb_node)

