from libc.stdlib cimport free

_TAG_TO_NAME = {
    0x0005: "_doctype",
    0x0002: "_text",
    0x0004: "_comment",
}

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
    def tag_id(self):
        cdef lxb_tag_id_t tag_id = lxb_dom_node_tag_id_noi(self.node)
        return tag_id

    @property
    def tag(self):
        """Return the name of the current tag (e.g. div, p, img).

        Returns
        -------
        text : str
        """

        cdef lxb_char_t *c_text
        cdef size_t str_len = 0
        if self.tag_id in [LXB_TAG__EM_DOCTYPE, LXB_TAG__TEXT, LXB_TAG__EM_COMMENT]:
            return _TAG_TO_NAME[self.tag_id]
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

    @property
    def id(self):
        """Get the id attribute of the node.

        Returns None if id does not set.

        Returns
        -------
        text : str
        """
        cdef char * key = 'id'
        cdef size_t str_len
        cdef lxb_dom_attr_t * attr = lxb_dom_element_attr_by_name(
            <lxb_dom_element_t *> self.node,
            <lxb_char_t *> key, 2
        )
        if attr != NULL:
            value = lxb_dom_attr_value_noi(attr, &str_len)
            return value.decode(_ENCODING) if value else None
        return None

    def iter(self, include_text=False):
        """Iterate over nodes on the current level.

        Parameters
        ----------
        include_text : bool
            If True, includes text nodes as well.

        Yields
        -------
        node
        """

        cdef lxb_dom_node_t *node = self.node.first_child
        cdef LexborNode next_node

        while node != NULL:
            if node.type == LXB_DOM_NODE_TYPE_TEXT and not include_text:
                node = node.next
                continue

            next_node = LexborNode()
            next_node._cinit(<lxb_dom_node_t *> node, self.parser)
            yield next_node
            node = node.next

    def traverse(self, include_text=False):
        """Iterate over all child and next nodes starting from the current level.

        Parameters
        ----------
        include_text : bool
            If True, includes text nodes as well.

        Yields
        -------
        node
        """
        cdef lxb_dom_node_t * root = self.node
        cdef lxb_dom_node_t * node = root.first_child
        cdef LexborNode lxb_node

        while node != NULL:
            if not (not include_text and node.type == LXB_DOM_NODE_TYPE_TEXT):
                lxb_node = LexborNode()
                lxb_node._cinit(<lxb_dom_node_t *> node, self.parser)
                yield lxb_node

            if node.first_child != NULL:
                node = node.first_child
            else:
                while node != root and node.next == NULL:
                    node = node.parent
                if node == root:
                    break
                node = node.next



cdef lxb_status_t css_finder_callback(lxb_dom_node_t *node, lxb_css_selector_specificity_t *spec, void *ctx):
    cdef LexborNode lxb_node
    cdef object cls
    cls = <object> ctx
    lxb_node = LexborNode()
    lxb_node._cinit(<lxb_dom_node_t *> node, cls.current_node.parser)
    cls.results.append(lxb_node)

