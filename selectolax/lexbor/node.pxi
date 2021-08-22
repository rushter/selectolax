from libc.stdlib cimport free

_TAG_TO_NAME = {
    0x0005: "- doctype",
    0x0002: "-text",
    0x0004: "-comment",
}
ctypedef fused str_or_LexborNode:
    basestring
    bytes
    LexborNode

cdef inline bytes to_bytes(str_or_LexborNode value):
    cdef bytes bytes_val
    if isinstance(value, (str, unicode)):
        bytes_val = value.encode(_ENCODING)
    elif isinstance(value, bytes):
        bytes_val =  <char*> value
    return bytes_val


cdef class LexborNode:
    """A class that represents HTML node (element)."""

    cdef _cinit(self, lxb_dom_node_t *node, LexborHTMLParser parser):
        self.parser = parser
        self.node = node
        return self

    @property
    def child(self):
        """Alias for the `first_child` property."""
        return self.first_child

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

    def text_lexbor(self):
        """Returns the text of the node including text of all its child nodes.

        Uses builtin method from lexbor.
        """

        cdef size_t str_len = 0
        cdef lxb_char_t * text

        text = lxb_dom_node_text_content(self.node, &str_len)
        if <int>str_len == 0:
            raise RuntimeError("Can't extract text")

        unicode_text = text.decode(_ENCODING)
        lxb_dom_document_destroy_text_noi(self.node.owner_document, text)
        return unicode_text

    def text(self, bool deep=True, str separator='', bool strip=False):
        """Returns the text of the node including text of all its child nodes.

        Parameters
        ----------
        strip : bool, default False
            If true, calls ``str.strip()`` on each text part to remove extra white spaces.
        separator : str, default ''
            The separator to use when joining text from different nodes.
        deep : bool, default True
            If True, includes text from all child nodes.

        Returns
        -------
        text : str

        """
        cdef unsigned char * text
        cdef lxb_dom_node_t* node = <lxb_dom_node_t*> self.node.first_child

        if not deep:
            container = TextContainer(separator, strip)
            if self.node.type == LXB_DOM_NODE_TYPE_TEXT:
                text = <unsigned char *> lexbor_str_data_noi(&(<lxb_dom_character_data_t *> self.node).data)
                if text != NULL:
                    py_text = text.decode(_ENCODING)
                    container.append(py_text)

            while node != NULL:
                if node.type == LXB_DOM_NODE_TYPE_TEXT:
                    text = <unsigned char *> lexbor_str_data_noi(&(<lxb_dom_character_data_t *> self.node).data)
                    if text != NULL:
                        py_text = text.decode(_ENCODING)
                        container.append(py_text)
                node = node.next
            return container.text
        else:
            container = TextContainer(separator, strip)
            if self.node.type == LXB_DOM_NODE_TYPE_TEXT:
                text = <unsigned char *> lexbor_str_data_noi(&(<lxb_dom_character_data_t *> self.node).data)
                if text != NULL:
                    container.append(text.decode(_ENCODING))

            lxb_dom_node_simple_walk(
                <lxb_dom_node_t *> self.node,
                <lxb_dom_node_simple_walker_f>text_callback,
                <void *>container
            )
            return container.text

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
        # TODO: This can be improved.
        results = self.css(query)
        n_results = len(results)
        if n_results > 0:
            if strict and n_results > 1:
                raise ValueError("Expected 1 match, but found %s matches" % n_results)
            return results[0]
        return default

    def any_css_matches(self, tuple selectors):
        """Returns True if any of CSS selectors matches a node"""
        for selector in selectors:
            if self.parser.selector.any_matches(selector,  self):
                return True
        return False

    def css_matches(self, str selector):
        """Returns True if CSS selector matches a node."""
        return self.parser.selector.any_matches(selector, self)

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

    def strip_tags(self, list tags, bool recursive = False):
        """Remove specified tags from the HTML tree.

        Parameters
        ----------
        tags : list
            List of tags to remove.
        recursive : bool, default True
            Whenever to delete all its child nodes

        Examples
        --------

        >>> tree = LexborHTMLParser('<html><head></head><body><script></script><div>Hello world!</div></body></html>')
        >>> tags = ['head', 'style', 'script', 'xmp', 'iframe', 'noembed', 'noframes']
        >>> tree.strip_tags(tags)
        >>> tree.html
        '<html><body><div>Hello world!</div></body></html>'

        """
        for tag in tags:
            for element in self.css(tag):
                element.decompose(recursive=recursive)


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

        >>> tree = LexborHTMLParser("<div id='a'></div>")
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


    def unwrap(self):
        """Replace node with whatever is inside this node.

        Examples
        --------

        >>>  tree = LexborHTMLParser("<div>Hello <i>world</i>!</div>")
        >>>  tree.css_first('i').unwrap()
        >>>  tree.html
        '<html><head></head><body><div>Hello world!</div></body></html>'

        """
        if self.node.first_child == NULL:
            return
        cdef lxb_dom_node_t* next_node;
        cdef lxb_dom_node_t* current_node;

        if self.node.first_child.next != NULL:
            current_node = self.node.first_child
            next_node = current_node.next

            while next_node != NULL:
                next_node = current_node.next
                lxb_dom_node_insert_before(self.node, current_node)
                current_node = next_node
        else:
            lxb_dom_node_insert_before(self.node, self.node.first_child)
        lxb_dom_node_destroy(<lxb_dom_node_t *> self.node)

    def unwrap_tags(self, list tags):
        """Unwraps specified tags from the HTML tree.

        Works the same as the ``unwrap`` method, but applied to a list of tags.

        Parameters
        ----------
        tags : list
            List of tags to remove.

        Examples
        --------

        >>> tree = LexborHTMLParser("<div><a href="">Hello</a> <i>world</i>!</div>")
        >>> tree.body.unwrap_tags(['i','a'])
        >>> tree.body.html
        '<body><div>Hello world!</div></body>'
        """

        for tag in tags:
            for element in self.css(tag):
                element.unwrap()


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
        cdef lxb_dom_node_t * node = root
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

    def replace_with(self, str_or_LexborNode value):
        """Replace current Node with specified value.

        Parameters
        ----------
        value : str, bytes or Node
            The text or Node instance to replace the Node with.
            When a text string is passed, it's treated as text. All HTML tags will be escaped.
            Convert and pass the ``Node`` object when you want to work with HTML.
            Does not clone the ``Node`` object.
            All future changes to the passed ``Node`` object will also be taken into account.

        Examples
        --------

        >>> tree = LexborHTMLParser('<div>Get <img src="" alt="Laptop"></div>')
        >>> img = tree.css_first('img')
        >>> img.replace_with(img.attributes.get('alt', ''))
        >>> tree.body.child.html
        '<div>Get Laptop</div>'

        >>> html_parser = LexborHTMLParser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
        >>> html_parser2 = LexborHTMLParser('<div>Test</div>')
        >>> img_node = html_parser.css_first('img')
        >>> img_node.replace_with(html_parser2.body.child)
        '<div>Get <span alt="Laptop"><div>Test</div> <div></div></span></div>'
        """
        cdef lxb_dom_node_t * new_node

        if isinstance(value, (str, bytes, unicode)):
            bytes_val = to_bytes(value)
            new_node = <lxb_dom_node_t *> lxb_dom_document_create_text_node(
                    &self.parser.document.dom_document,
                    <lxb_char_t *> bytes_val, len(bytes_val)
            )
            if new_node == NULL:
                raise SelectolaxError("Can't create a new node")
            lxb_dom_node_insert_before(self.node,  new_node)
            lxb_dom_node_destroy(<lxb_dom_node_t *> self.node)
        elif isinstance(value, LexborNode):
            new_node = lxb_dom_document_import_node(
                &self.parser.document.dom_document,
                <lxb_dom_node_t *> value.node,
                <bint> True
            )
            if new_node == NULL:
                raise SelectolaxError("Can't create a new node")
            lxb_dom_node_insert_before(self.node, <lxb_dom_node_t *> new_node)
            lxb_dom_node_destroy(<lxb_dom_node_t *> self.node)
        else:
            raise SelectolaxError("Expected a string or LexborNode instance, but %s found" % type(value).__name__)


    def insert_before(self, str_or_LexborNode value):
        """
        Insert a node before the current Node.

        Parameters
        ----------
        value : str, bytes or Node
            The text or Node instance to insert before the Node.
            When a text string is passed, it's treated as text. All HTML tags will be escaped.
            Convert and pass the ``Node`` object when you want to work with HTML.
            Does not clone the ``Node`` object.
            All future changes to the passed ``Node`` object will also be taken into account.

        Examples
        --------

        >>> tree = LexborHTMLParser('<div>Get <img src="" alt="Laptop"></div>')
        >>> img = tree.css_first('img')
        >>> img.insert_before(img.attributes.get('alt', ''))
        >>> tree.body.child.html
        '<div>Get Laptop<img src="" alt="Laptop"></div>'

        >>> html_parser = LexborHTMLParser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
        >>> html_parser2 = LexborHTMLParser('<div>Test</div>')
        >>> img_node = html_parser.css_first('img')
        >>> img_node.insert_before(html_parser2.body.child)
        <div>Get <span alt="Laptop"><div>Test</div><img src="/jpg"> <div></div></span></div>'
        """
        cdef lxb_dom_node_t * new_node

        if isinstance(value, (str, bytes, unicode)):
            bytes_val = to_bytes(value)
            new_node = <lxb_dom_node_t *> lxb_dom_document_create_text_node(
                    &self.parser.document.dom_document,
                    <lxb_char_t *> bytes_val, len(bytes_val)
            )
            if new_node == NULL:
                raise SelectolaxError("Can't create a new node")
            lxb_dom_node_insert_before(self.node,  new_node)
        elif isinstance(value, LexborNode):
            new_node = lxb_dom_document_import_node(
                &self.parser.document.dom_document,
                <lxb_dom_node_t *> value.node,
                <bint> True
            )
            if new_node == NULL:
                raise SelectolaxError("Can't create a new node")
            lxb_dom_node_insert_before(self.node, <lxb_dom_node_t *> new_node)
        else:
            raise SelectolaxError("Expected a string or LexborNode instance, but %s found" % type(value).__name__)

    def insert_after(self, str_or_LexborNode value):
        """
        Insert a node after the current Node.

        Parameters
        ----------
        value : str, bytes or Node
            The text or Node instance to insert after the Node.
            When a text string is passed, it's treated as text. All HTML tags will be escaped.
            Convert and pass the ``Node`` object when you want to work with HTML.
            Does not clone the ``Node`` object.
            All future changes to the passed ``Node`` object will also be taken into account.

        Examples
        --------

        >>> tree = LexborHTMLParser('<div>Get <img src="" alt="Laptop"></div>')
        >>> img = tree.css_first('img')
        >>> img.insert_after(img.attributes.get('alt', ''))
        >>> tree.body.child.html
        '<div>Get <img src="" alt="Laptop">Laptop</div>'

        >>> html_parser = LexborHTMLParser('<div>Get <span alt="Laptop"><img src="/jpg"> <div></div></span></div>')
        >>> html_parser2 = LexborHTMLParser('<div>Test</div>')
        >>> img_node = html_parser.css_first('img')
        >>> img_node.insert_after(html_parser2.body.child)
        <div>Get <span alt="Laptop"><img src="/jpg"><div>Test</div> <div></div></span></div>'
        """
        cdef lxb_dom_node_t * new_node

        if isinstance(value, (str, bytes, unicode)):
            bytes_val = to_bytes(value)
            new_node = <lxb_dom_node_t *> lxb_dom_document_create_text_node(
                    &self.parser.document.dom_document,
                    <lxb_char_t *> bytes_val, len(bytes_val)
            )
            if new_node == NULL:
                raise SelectolaxError("Can't create a new node")
            lxb_dom_node_insert_after(self.node,  new_node)
        elif isinstance(value, LexborNode):
            new_node = lxb_dom_document_import_node(
                &self.parser.document.dom_document,
                <lxb_dom_node_t *> value.node,
                <bint> True
            )
            if new_node == NULL:
                raise SelectolaxError("Can't create a new node")
            lxb_dom_node_insert_after(self.node, <lxb_dom_node_t *> new_node)
        else:
            raise SelectolaxError("Expected a string or LexborNode instance, but %s found" % type(value).__name__)

    @property
    def raw_value(self):
        """Return the raw (unparsed, original) value of a node.

        Currently, works on text nodes only.

        Returns
        -------

        raw_value : bytes

        Examples
        --------

        >>> html_parser = LexborHTMLParser('<div>&#x3C;test&#x3E;</div>')
        >>> selector = html_parser.css_first('div')
        >>> selector.child.html
        '&lt;test&gt;'
        >>> selector.child.raw_value
        b'&#x3C;test&#x3E;'
        """
        raise SelectolaxError("This features is not supported by the lexbor backend. Please use Modest backend.")

    def scripts_contain(self, str query):
        """Returns True if any of the script tags contain specified text.

        Caches script tags on the first call to improve performance.

        Parameters
        ----------
        query : str
            The query to check.

        """
        if self.parser.cached_script_texts is None:
            nodes = self.parser.selector.find('script', self)
            text_nodes = []
            for node in nodes:
                node_text = node.text(deep=True)
                if node_text:
                    text_nodes.append(node_text)
            self.parser.cached_script_texts = text_nodes

        for text in self.parser.cached_script_texts:
            if query in text:
                return True
        return False

    def script_srcs_contain(self, tuple queries):
        """Returns True if any of the script SRCs attributes contain on of the specified text.

        Caches values on the first call to improve performance.

        Parameters
        ----------
        queries : tuple of str

        """
        if self.parser.cached_script_srcs is None:
            nodes = self.parser.selector.find('script', self)
            src_nodes = []
            for node in nodes:
                node_src = node.attrs.get('src')
                if node_src:
                    src_nodes.append(node_src)
            self.parser.cached_script_srcs = src_nodes

        for text in self.parser.cached_script_srcs:
            for query in queries:
                if query in text:
                    return True
        return False

    def remove(self, bool recursive=True):
        """An alias for the decompose method."""
        self.decompose(recursive)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.html == other
        if not isinstance(other, LexborNode):
            return False
        return self.html == other.html

cdef class TextContainer:
    cdef public str text
    cdef public str separator
    cdef public bool strip

    def __init__(self, str separator = '', bool strip = False):
        self.text = ""
        self.separator = separator
        self.strip = strip

    def append(self, node_text):
        if self.strip:
            self.text += node_text.strip() + self.separator
        else:
            self.text += node_text + self.separator


cdef lexbor_action_t text_callback(lxb_dom_node_t *node, void *ctx):
    cdef unsigned char *text;
    cdef lxb_tag_id_t tag_id = lxb_dom_node_tag_id_noi(node)
    if tag_id != LXB_TAG__TEXT:
        return LEXBOR_ACTION_OK

    text = <unsigned char*> lexbor_str_data_noi(&(<lxb_dom_text_t *> node).char_data.data)
    if not text:
        return LEXBOR_ACTION_OK
    py_str = text.decode(_ENCODING)
    cdef object cls
    cls = <object> ctx
    cls.append(py_str)
    return LEXBOR_ACTION_OK
