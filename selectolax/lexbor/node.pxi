cimport cython
from cpython.bytearray cimport (
    PyByteArray_AS_STRING,
    PyByteArray_GET_SIZE,
    PyByteArray_Resize,
)
from cpython.exc cimport PyErr_SetNone
from cpython.list cimport PyList_Append
from cpython.unicode cimport PyUnicode_DecodeUTF8

import logging

logger = logging.getLogger("selectolax")

_TAG_TO_NAME = {
    LXB_TAG__EM_DOCTYPE: "-doctype",
    LXB_TAG__TEXT: "-text",
    LXB_TAG__EM_COMMENT: "-comment",
    LXB_TAG__DOCUMENT: "-document",
}
ctypedef fused str_or_LexborNode:
    str
    bytes
    LexborNode

ctypedef fused str_or_bytes:
    str
    bytes

cdef inline bytes to_bytes(str_or_LexborNode value):
    cdef bytes bytes_val
    if isinstance(value, unicode):
        bytes_val = <bytes> value.encode("utf-8")
    elif isinstance(value, bytes):
        bytes_val = <bytes> value
    return bytes_val


cdef inline void _replace_children(
    lxb_dom_node_t *parent, const lxb_char_t *html, size_t html_len
) except *:
    # The old children are unlinked, not destroyed, so LexborNode views the
    # caller already holds stay valid but detached, exactly as they do after
    # decompose(). lxb_html_element_inner_html_set() destroys them instead,
    # which frees the nodes and lets the next same-size allocation hand their
    # addresses out again, so a retained view would read unrelated memory.
    cdef lxb_dom_node_t *wrapper
    cdef lxb_dom_node_t *child

    wrapper = lxb_html_document_parse_fragment(
        <lxb_html_document_t *> parent.owner_document,
        lxb_dom_interface_element(parent),
        html,
        html_len,
    )
    if wrapper == NULL:
        raise SelectolaxError("Can't set inner HTML.")

    while parent.first_child != NULL:
        lxb_dom_node_remove(parent.first_child)

    while wrapper.first_child != NULL:
        child = wrapper.first_child
        lxb_dom_node_remove(child)
        lxb_dom_node_insert_child(parent, child)

    # The wrapper is built by the parse above and never handed to the caller.
    lxb_dom_node_destroy(wrapper)


@cython.final
cdef class LexborNode:
    """A class that represents HTML node (element)."""

    def __init__(self, *args, **kwargs):
        raise TypeError(
            "LexborNode cannot be instantiated directly; it is a view onto a "
            "DOM node owned by a parser. Use LexborHTMLParser.create_node(), "
            "LexborHTMLParser(html, is_fragment=True).root or LexborNode.clone() instead."
        )

    cdef void set_as_fragment_root(self):
        self._is_fragment_root = 1

    @staticmethod
    cdef LexborNode new(lxb_dom_node_t *node, LexborHTMLParser parser):
        cdef LexborNode lxbnode = LexborNode.__new__(LexborNode)
        lxbnode.node = node
        lxbnode.parser = parser
        lxbnode._is_fragment_root = 0
        return lxbnode

    @property
    def mem_id(self):
        return <size_t> self.node

    @property
    def child(self):
        """Alias for the `first_child` property.

        **Deprecated**. Please use `first_child` instead.
        """
        return self.first_child

    @property
    def first_child(self):
        """Return the first child node."""
        cdef LexborNode node
        if self.node.first_child:
            node = LexborNode.new(<lxb_dom_node_t *> self.node.first_child, self.parser)
            return node
        return None

    @property
    def parent(self):
        """Return the parent node."""
        cdef LexborNode node
        if self.node.parent != NULL:
            node = LexborNode.new(<lxb_dom_node_t *> self.node.parent, self.parser)
            return node
        return None

    @property
    def next(self):
        """Return next node."""
        cdef LexborNode node
        if self.node.next != NULL:
            node = LexborNode.new(<lxb_dom_node_t *> self.node.next, self.parser)
            return node
        return None

    @property
    def prev(self):
        """Return previous node."""
        cdef LexborNode node
        if self.node.prev != NULL:
            node = LexborNode.new(<lxb_dom_node_t *> self.node.prev, self.parser)
            return node
        return None

    @property
    def last_child(self):
        """Return last child node."""
        cdef LexborNode node
        if self.node.last_child != NULL:
            node = LexborNode.new(<lxb_dom_node_t *> self.node.last_child, self.parser)
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
        cdef lxb_status_t status
        lxb_str = lexbor_str_create()
        if lxb_str == NULL:
            raise MemoryError("Can't allocate memory for the output string.")
        if self._is_fragment_root:
            status = serialize_fragment(self.node, lxb_str)
            # status = lxb_html_serialize_tree_str(self.node, lxb_str)
        else:
            status = lxb_html_serialize_tree_str(self.node, lxb_str)
        if status == 0:
            html = _decode_utf8(lxb_str.data, lexbor_str_length_noi(lxb_str)).replace('<-undef>', '')
            lexbor_str_destroy(lxb_str, self.node.owner_document.text, True)
            return html
        lexbor_str_destroy(lxb_str, self.node.owner_document.text, True)
        return None

    cdef inline str _serialize_html(self, lxb_html_serialize_opt_t options, size_t indent, bint pretty):
        cdef lexbor_str_t *lxb_str
        cdef lxb_status_t status

        lxb_str = lexbor_str_create()
        if lxb_str == NULL:
            raise MemoryError("Can't allocate memory for the output string.")
        if self._is_fragment_root:
            if pretty:
                status = serialize_fragment_pretty(self.node, lxb_str, options, indent)
            else:
                status = serialize_fragment(self.node, lxb_str)
        else:
            if pretty:
                status = lxb_html_serialize_pretty_tree_str(self.node, options, indent, lxb_str)
            else:
                status = lxb_html_serialize_tree_str(self.node, lxb_str)

        if status == 0:
            html = _decode_utf8(lxb_str.data, lexbor_str_length_noi(lxb_str)).replace('<-undef>', '')
            lexbor_str_destroy(lxb_str, self.node.owner_document.text, True)
            return html
        lexbor_str_destroy(lxb_str, self.node.owner_document.text, True)
        return None

    cdef inline str _serialize_inner_html(self, lxb_html_serialize_opt_t options, size_t indent, bint pretty):
        cdef lexbor_str_t *lxb_str
        cdef lxb_status_t status

        lxb_str = lexbor_str_create()
        if lxb_str == NULL:
            raise MemoryError("Can't allocate memory for the output string.")
        if pretty:
            status = lxb_html_serialize_pretty_deep_str(self.node, options, indent, lxb_str)
        else:
            status = lxb_html_serialize_deep_str(self.node, lxb_str)

        if status == 0 and lxb_str.data:
            html = _decode_utf8(lxb_str.data, lexbor_str_length_noi(lxb_str)).replace('<-undef>', '')
            lexbor_str_destroy(lxb_str, self.node.owner_document.text, True)
            return html
        lexbor_str_destroy(lxb_str, self.node.owner_document.text, True)
        return None

    def html_pretty(
        self,
        Py_ssize_t indent=0,
        bint skip_ws_nodes=False,
        bint skip_comment=False,
        bint raw=False,
        bint without_closing=False,
        bint tag_with_ns=False,
        bint without_text_indent=False,
        bint full_doctype=False,
        bint html5test=False,
    ):
        """Return pretty-printed HTML for the current node.

        Parameters
        ----------
        indent : int, optional
            Initial indentation level passed to Lexbor. Defaults to ``0``.
        skip_ws_nodes : bool, optional
            Skip text nodes that contain only whitespace.
        skip_comment : bool, optional
            Exclude HTML comment nodes from the serialized output.
        raw : bool, optional
            Serialize text and attribute values without HTML escaping.
        without_closing : bool, optional
            Omit closing tags for non-void elements.
        tag_with_ns : bool, optional
            Include namespace prefixes in serialized tag names when available.
        without_text_indent : bool, optional
            Disable extra indentation added around text and comment content.
        full_doctype : bool, optional
            Serialize the full document type declaration when a doctype node is present.
        html5test : bool, optional
            Serialize using Lexbor's HTML5 test formatting mode.
        """
        cdef lxb_html_serialize_opt_t options
        if indent < 0:
            raise ValueError("indent must be greater than or equal to 0")
        options = _html_pretty_options(
            skip_ws_nodes,
            skip_comment,
            raw,
            without_closing,
            tag_with_ns,
            without_text_indent,
            full_doctype,
            html5test,
        )
        return self._serialize_html(options, <size_t> indent, True)

    def inner_html_pretty(
        self,
        Py_ssize_t indent=0,
        bint skip_ws_nodes=False,
        bint skip_comment=False,
        bint raw=False,
        bint without_closing=False,
        bint tag_with_ns=False,
        bint without_text_indent=False,
        bint full_doctype=False,
        bint html5test=False,
    ):
        """Return pretty-printed HTML representation of the child nodes.

        Parameters
        ----------
        indent : int, optional
            Initial indentation level passed to Lexbor. Defaults to ``0``.
        skip_ws_nodes : bool, optional
            Skip text nodes that contain only whitespace.
        skip_comment : bool, optional
            Exclude HTML comment nodes from the serialized output.
        raw : bool, optional
            Serialize text and attribute values without HTML escaping.
        without_closing : bool, optional
            Omit closing tags for non-void elements.
        tag_with_ns : bool, optional
            Include namespace prefixes in serialized tag names when available.
        without_text_indent : bool, optional
            Disable extra indentation added around text and comment content.
        full_doctype : bool, optional
            Serialize the full document type declaration when a doctype node is present.
        html5test : bool, optional
            Serialize using Lexbor's HTML5 test formatting mode.
        """
        cdef lxb_html_serialize_opt_t options
        if indent < 0:
            raise ValueError("indent must be greater than or equal to 0")
        options = _html_pretty_options(
            skip_ws_nodes,
            skip_comment,
            raw,
            without_closing,
            tag_with_ns,
            without_text_indent,
            full_doctype,
            html5test,
        )
        return self._serialize_inner_html(options, <size_t> indent, True)

    def __hash__(self):
        return self.mem_id

    def text_lexbor(self):
        """Returns the text of the node including text of all its child nodes.

        Uses builtin method from lexbor.

        Covers the whole fragment when called on the root of an HTML fragment,
        like ``text()`` does.
        """

        cdef size_t str_len = 0
        cdef lxb_char_t * text
        cdef LexborNode start_node = self._get_node()
        text = lxb_dom_node_text_content(start_node.node, &str_len)
        if text == NULL:
            return ""

        try:
            if str_len == 0:
                return ""
            unicode_text = _decode_utf8(text, str_len)
        finally:
            # lxb_dom_node_text_content() copies the content into a buffer taken
            # from the document's text memory arena, which is only released
            # wholesale by lxb_html_document_destroy(). Give it back here.
            lxb_dom_document_destroy_text_noi(
                &self.parser.document.dom_document, text
            )
        return unicode_text

    def text(self, bool deep=True, str separator='', bool strip=False, bool skip_empty=False):
        """Return concatenated text from this node.

        Parameters
        ----------
        deep : bool, optional
            When ``True`` (default), include text from all descendant nodes; when
            ``False``, only include direct children.
        separator : str, optional
            String inserted between successive text fragments.
        strip : bool, optional
            If ``True``, apply ``str.strip()`` to each fragment before joining to
            remove surrounding whitespace. Defaults to ``False``.
        skip_empty : bool, optional
            Exclude text nodes whose content is only ASCII whitespace (space,
            tab, newline, form feed or carriage return) when ``True``.
            Defaults to ``False``.

        Returns
        -------
        text : str
            Combined textual content assembled according to the provided options.

        """
        cdef unsigned char * text
        cdef LexborNode start_node = self._get_node()
        cdef lxb_dom_node_t * node = <lxb_dom_node_t *> start_node.node.first_child
        cdef TextContainer container = TextContainer.create(separator, strip, skip_empty)

        # Both walks below start at the *children* of the node they are given,
        # never at that node itself, so a text node that is also the walk's root
        # has to contribute its data here. Widening a fragment root to its
        # parent means the walk covers it after all, and adding it as well would
        # duplicate it.
        if start_node.node == self.node and _is_node_type(self.node, LXB_DOM_NODE_TYPE_TEXT):
            if not skip_empty or not is_empty_text_node(<lxb_dom_node_t *> self.node):
                text = <unsigned char *> lexbor_str_data_noi(&(<lxb_dom_character_data_t *> self.node).data)
                if text != NULL:
                    container.add_bytes(
                        text, lexbor_str_length_noi(&(<lxb_dom_character_data_t *> self.node).data)
                    )

        if not deep:
            while node != NULL:
                if _is_node_type(node, LXB_DOM_NODE_TYPE_TEXT):
                    if not skip_empty or not is_empty_text_node(node):
                        text = <unsigned char *> lexbor_str_data_noi(&(<lxb_dom_character_data_t *> node).data)
                        if text != NULL:
                            container.add_bytes(
                                text, lexbor_str_length_noi(&(<lxb_dom_character_data_t *> node).data)
                            )
                node = node.next
            container.reraise()
            return container.text

        lxb_dom_node_simple_walk(
            <lxb_dom_node_t *> start_node.node,
            <lxb_dom_node_simple_walker_f> text_callback,
            <void *> container
        )
        container.reraise()
        return container.text

    cdef inline LexborNode _get_node(self):
        """Return the node that tree-walking operations should start from.

        A fragment's root is a single node, but its siblings are part of the
        fragment too, so operations that walk the tree start from the parent
        instead and thus cover every top-level node. This holds when the root is
        a text node as well, which happens whenever a fragment does not begin
        with an element.

        The parent is Lexbor's internal ``<html>`` wrapper rather than something
        the caller put in the document, so it is not a legitimate result of a
        search rooted here. The selector keeps it out of every match; see
        ``_wrapper_to_skip_for``.

        Returns ``self`` when this node is not a fragment root, and also when a
        fragment root has been detached from its wrapper, which is what
        ``unwrap()``, ``decompose()`` and ``replace_with()`` do to it. The
        detached node then stands in for the whole fragment, so its own subtree
        is walked -- the same treatment every other detached node already gets.

        Returns
        -------
        LexborNode
            The node to start from. Never ``None``: callers dereference
            ``.node`` on the result without checking, and a ``None`` here
            segfaults.
        """
        cdef LexborNode node
        if self._is_fragment_root:
            node = self.parent
            if node is not None:
                return node
        return self

    def css(self, str query):
        """Evaluate CSS selector against current node and its child nodes.

        Matches pattern `query` against HTML tree.
        `CSS selectors reference <https://www.w3schools.com/cssref/css_selectors.asp>`_.

        Special selectors:

         - parser.css('p:lexbor-contains("awesome" i)') -- case-insensitive contains
         - parser.css('p:lexbor-contains("awesome")') -- case-sensitive contains


        Parameters
        ----------
        query : str
            CSS selector (e.g. "div > :nth-child(2n+1):not(:has(a))").

        Returns
        -------
        selector : list of `Node` objects
        """
        return self.parser.selector.find(query, self._get_node())

    def css_first(self, str query, default=None, bool strict=False):
        """Same as `css` but returns only the first match.

        When `strict=False` stops at the first match. Works faster.

        Parameters
        ----------

        query : str
        default : Any, default None
            Default value to return if there is no match.
        strict: bool, default False
            Set to True if you want to check if there is strictly only one match in the document.


        Returns
        -------
        selector : `LexborNode` object
        """
        if strict:
            results = self.parser.selector.find(query, self._get_node())
        else:
            results = self.parser.selector.find_first(query, self._get_node())
        n_results = len(results)
        if n_results > 0:
            if strict and n_results > 1:
                raise ValueError("Expected 1 match, but found %s matches" % n_results)
            return results[0]
        return default

    def any_css_matches(self, tuple selectors):
        """Returns True if any of CSS selectors matches a node."""
        cdef LexborNode start_node = self._get_node()
        for selector in selectors:
            if self.parser.selector.any_matches(selector, start_node):
                return True
        return False

    def css_matches(self, str selector):
        """Returns True if CSS selector matches a node."""
        return bool(self.parser.selector.any_matches(selector, self._get_node()))

    def __repr__(self):
        return '<LexborNode %s>' % self.tag

    @property
    def tag_id(self):
        cdef lxb_tag_id_t tag_id = lxb_dom_node_tag_id_noi(self.node)
        return tag_id

    @property
    def tag(self):
        """Return the name of the current tag (e.g. div, p, img).

        For for non-tag nodes, returns the following names:

         * `-text` - text node
         * `-document` - document node
         * `-comment` - comment node
         * `-doctype` - doctype node

        Returns ``None`` for any other non-element node.

        Returns
        -------
        text : str or None
        """

        cdef const lxb_char_t *c_text
        cdef size_t str_len = 0
        cdef lxb_tag_id_t tag_id = lxb_dom_node_tag_id_noi(self.node)

        if tag_id in _TAG_TO_NAME:
            return _TAG_TO_NAME[tag_id]

        if not _is_node_type(self.node, LXB_DOM_NODE_TYPE_ELEMENT):
            return None

        c_text = lxb_dom_element_qualified_name(<lxb_dom_element_t *> self.node, &str_len)
        text = None
        if c_text:
            text = _decode_utf8(c_text, str_len)
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
        if self.node == <lxb_dom_node_t *> lxb_dom_document_root(&self.parser.document.dom_document):
            raise SelectolaxError("Decomposing the root node is not allowed.")

        if recursive:
            node_remove_deep(<lxb_dom_node_t *> self.node)
        else:
            lxb_dom_node_remove(<lxb_dom_node_t *> self.node)

        _maybe_refresh_head_body(self.parser.document, <lxb_dom_node_t *> self.node)
        self.parser._mark_mutated()

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
        cdef LexborNode element
        for tag in tags:
            for element in self.css(tag):
                element.decompose(recursive=recursive)

    @property
    def attributes(self):
        """Get all attributes that belong to the current node.

        The value of empty attributes is None.

        Keys are the attribute names as written in the markup, so a namespaced
        attribute keeps its prefix and stays addressable. This matters whenever
        an element carries both a plain and a prefixed variant of the same local
        name, where reporting local names alone would collapse the two into one
        key and silently drop one of the values:

        >>> tree = LexborHTMLParser("<svg><use href='/a' xlink:href='/b'></use></svg>")
        >>> tree.css_first("use").attributes
        {'href': '/a', 'xlink:href': '/b'}

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
        cdef lxb_dom_attr_t *attr
        cdef const lxb_char_t *name
        cdef size_t str_len = 0
        cdef size_t value_len = 0
        attributes = dict()

        if not _is_node_type(self.node, LXB_DOM_NODE_TYPE_ELEMENT):
            return attributes

        attr = lxb_dom_element_first_attribute_noi(<lxb_dom_element_t *> self.node)

        while attr != NULL:
            # N.B. `str_len` is read in the same expression that fills it in via
            # `&str_len`. C leaves the order in which call arguments are evaluated
            # unspecified, so GCC evaluates `str_len` first and every name came out
            # truncated to the previous attribute's length. Sequence the two.
            name = lxb_dom_attr_qualified_name(attr, &str_len)
            key = _decode_utf8(name, str_len)
            value = lxb_dom_attr_value_noi(attr, &value_len)

            if value:
                py_value = _decode_utf8(value, value_len)
            else:
                py_value = None
            attributes[key] = py_value

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
        if not _is_node_type(self.node, LXB_DOM_NODE_TYPE_ELEMENT):
            raise TypeError("attrs is only available for element nodes")
        cdef LexborAttributes attributes = LexborAttributes.create(<lxb_dom_node_t *> self.node, self.parser)
        return attributes

    @property
    def id(self):
        """Get the id attribute of the node.

        Returns None if id does not set, or if the node is not an element node.

        Returns
        -------
        text : str | None
        """
        cdef char * key = 'id'
        cdef size_t str_len
        cdef lxb_dom_attr_t * attr

        if not _is_node_type(self.node, LXB_DOM_NODE_TYPE_ELEMENT):
            return None

        attr = lxb_dom_element_attr_by_name(
            <lxb_dom_element_t *> self.node,
            <lxb_char_t *> key, 2
        )
        if attr != NULL:
            value = lxb_dom_attr_value_noi(attr, &str_len)
            return _decode_utf8(value, str_len) if value else None
        return None

    def iter(self, bool include_text = False, bool skip_empty = False):
        """Iterate over direct children of this node.

        Parameters
        ----------
        include_text : bool, optional
            When ``True``, yield text nodes in addition to element nodes. Defaults
            to ``False``.
        skip_empty : bool, optional
            When ``include_text`` is ``True``, ignore text nodes made up solely
            of ASCII whitespace (space, tab, newline, form feed or carriage
            return). Defaults to ``False``.

        Yields
        ------
        LexborNode
            Child nodes on the same tree level as this node, filtered according
            to the provided options.
        """

        cdef LexborNode start_node = self._get_node()
        cdef lxb_dom_node_t *node = start_node.node.first_child
        cdef lxb_dom_node_t *following
        cdef LexborNode next_node

        while node != NULL:
            if node.type == LXB_DOM_NODE_TYPE_TEXT and not include_text:
                node = node.next
                continue
            if node.type == LXB_DOM_NODE_TYPE_TEXT and include_text and skip_empty and is_empty_text_node(node):
                node = node.next
                continue

            following = node.next
            next_node = LexborNode.new(<lxb_dom_node_t *> node, self.parser)
            yield next_node
            node = following

    def __iter__(self):
        return self.iter()

    def __next__(self):
        return self.next

    def unwrap(self, bint delete_empty=False):
        """Replace node with whatever is inside this node.

        Does nothing if you perform unwrapping second time on the same node.

        Parameters
        ----------
        delete_empty : bool, default False
            If True, removes empty tags.

        Examples
        --------

        >>>  tree = LexborHTMLParser("<div>Hello <i>world</i>!</div>")
        >>>  tree.css_first('i').unwrap()
        >>>  tree.html
        '<html><head></head><body><div>Hello world!</div></body></html>'

        Note: by default, empty tags are ignored, use "delete_empty" to change this.
        """
        if self.node.parent == NULL:
            return

        if node_is_removed(<lxb_dom_node_t *> self.node) == 1:
            logger.error("Attempt to unwrap removed node. Does nothing.")
            return

        cdef lxb_dom_node_t * current_node = self.node.first_child
        cdef lxb_dom_node_t * next_node

        if current_node == NULL:
            if delete_empty:
                lxb_dom_node_remove(<lxb_dom_node_t *> self.node)
                _maybe_refresh_head_body(
                    self.parser.document, <lxb_dom_node_t *> self.node
                )
                self.parser._mark_mutated()
            return

        while current_node != NULL:
            next_node = current_node.next
            # A DOM move is a "pre-insert": unlink from the old parent first, then
            # insert. lxb_dom_node_insert_before() only re-parents and never unlinks,
            # so without the remove this node keeps pointing at children that have
            # already moved to its own parent, and they end up in two child lists at
            # once. The traversal then walks a cycle and dereferences freed memory.
            lxb_dom_node_remove(current_node)
            lxb_dom_node_insert_before(self.node, current_node)
            current_node = next_node

        lxb_dom_node_remove(<lxb_dom_node_t *> self.node)
        _maybe_refresh_head_body(self.parser.document, <lxb_dom_node_t *> self.node)
        self.parser._mark_mutated()

    def unwrap_tags(self, list tags, bint delete_empty = False):
        """Unwraps specified tags from the HTML tree.

        Works the same as the ``unwrap`` method, but applied to a list of tags.

        Parameters
        ----------
        tags : list
            List of tags to remove.
        delete_empty : bool, default False
            If True, removes empty tags.

        Examples
        --------

        >>> tree = LexborHTMLParser("<div><a href="">Hello</a> <i>world</i>!</div>")
        >>> tree.body.unwrap_tags(['i','a'])
        >>> tree.body.html
        '<body><div>Hello world!</div></body>'

        Note: by default, empty tags are ignored, use "delete_empty" to change this.
        """
        cdef LexborNode element
        for tag in tags:
            if self.node.parent == NULL and not _is_node_type(self.node, LXB_DOM_NODE_TYPE_DOCUMENT):
                break
            for element in self.css(tag):
                element.unwrap(delete_empty)

    def merge_text_nodes(self):
        """Iterates over all text nodes and merges all text nodes that are close to each other.

        This is useful for text extraction.
        Use it when you need to strip HTML tags and merge "dangling" text.

        Examples
        --------

        >>> tree = LexborHTMLParser("<div><p><strong>J</strong>ohn</p><p>Doe</p></div>")
        >>> node = tree.css_first('div')
        >>> tree.unwrap_tags(["strong"])
        >>> tree.text(deep=True, separator=" ", strip=True)
        "J ohn Doe" # Text extraction produces an extra space because the strong tag was removed.
        >>> node.merge_text_nodes()
        >>> tree.text(deep=True, separator=" ", strip=True)
        "John Doe"

        Merges runs of adjacent text nodes, so it covers the whole fragment when
        called on the root of an HTML fragment.
        """
        cdef LexborNode start_node = self._get_node()
        _merge_text_nodes(start_node.node)
        self.parser._mark_mutated()

    def traverse(self, bool include_text = False, bool skip_empty = False):
        """Depth-first traversal starting at the current node.

        Parameters
        ----------
        include_text : bool, optional
            When ``True``, include text nodes in the traversal sequence. Defaults
            to ``False``.
        skip_empty : bool, optional
            Skip text nodes that contain only ASCII whitespace (space, tab,
            newline, form feed or carriage return) when ``include_text`` is
            ``True``. Defaults to ``False``.

        Yields
        ------
        LexborNode
            Nodes encountered in depth-first order beginning with the current
            node, filtered according to the provided options.

        Notes
        -----
        Covers the whole fragment when called on the root of an HTML fragment,
        like ``iter()`` and ``text()`` do.
        """
        cdef LexborNode start_node = self._get_node()
        cdef lxb_dom_node_t * root
        cdef lxb_dom_node_t * node
        cdef lxb_dom_node_t * next_top_level
        cdef LexborNode lxb_node

        # A fragment root is searched through its wrapper, so the top-level nodes
        # are walked one after another rather than as a single subtree.
        cdef bint per_top_level = self._is_fragment_root and start_node is not self

        if per_top_level:
            root = start_node.node.first_child
            if root == NULL:
                return
        else:
            root = start_node.node

        node = root
        while True:
            if node == root:
                # Read before yielding, so unlinking this node does not end the walk.
                next_top_level = node.next

            if include_text or node.type != LXB_DOM_NODE_TYPE_TEXT:
                if not skip_empty or not is_empty_text_node(node):
                    lxb_node = LexborNode.new(<lxb_dom_node_t *> node, self.parser)
                    yield lxb_node

            if node.first_child != NULL:
                node = node.first_child
                continue

            while node != root and node.next == NULL:
                node = node.parent

            if node != root:
                node = node.next
                continue

            if not per_top_level:
                break

            root = next_top_level
            if root == NULL:
                break
            node = root

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
            lxb_dom_node_insert_before(self.node, new_node)
            lxb_dom_node_remove(<lxb_dom_node_t *> self.node)
            _maybe_refresh_head_body(
                self.parser.document, <lxb_dom_node_t *> self.node
            )
        elif isinstance(value, LexborNode):
            new_node = lxb_dom_document_import_node(
                &self.parser.document.dom_document,
                <lxb_dom_node_t *> value.node,
                <bint> True
            )
            if new_node == NULL:
                raise SelectolaxError("Can't create a new node")
            lxb_dom_node_insert_before(self.node, <lxb_dom_node_t *> new_node)
            lxb_dom_node_remove(<lxb_dom_node_t *> self.node)
            _maybe_refresh_head_body(
                self.parser.document, <lxb_dom_node_t *> self.node
            )
        else:
            raise SelectolaxError("Expected a string or LexborNode instance, but %s found" % type(value).__name__)

        self.parser._mark_mutated()

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
            lxb_dom_node_insert_before(self.node, new_node)
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

        self.parser._mark_mutated()

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
            lxb_dom_node_insert_after(self.node, new_node)
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

        self.parser._mark_mutated()

    def insert_child(self, str_or_LexborNode value):
        """
        Insert a node inside (at the end of) the current Node.

        Parameters
        ----------
        value : str, bytes or Node
            The text or Node instance to insert inside the Node.
            When a text string is passed, it's treated as text. All HTML tags will be escaped.
            Convert and pass the ``Node`` object when you want to work with HTML.
            Does not clone the ``Node`` object.
            All future changes to the passed ``Node`` object will also be taken into account.

        Examples
        --------

        >>> tree = LexborHTMLParser('<div>Get <img src=""></div>')
        >>> div = tree.css_first('div')
        >>> div.insert_child('Laptop')
        >>> tree.body.child.html
        '<div>Get <img src="">Laptop</div>'

        >>> html_parser = LexborHTMLParser('<div>Get <span alt="Laptop"> <div>Laptop</div> </span></div>')
        >>> html_parser2 = LexborHTMLParser('<div>Test</div>')
        >>> span_node = html_parser.css_first('span')
        >>> span_node.insert_child(html_parser2.body.child)
        <div>Get <span alt="Laptop"> <div>Laptop</div> <div>Test</div> </span></div>'
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
            lxb_dom_node_insert_child(self.node, new_node)
        elif isinstance(value, LexborNode):
            new_node = lxb_dom_document_import_node(
                &self.parser.document.dom_document,
                <lxb_dom_node_t *> value.node,
                <bint> True
            )
            if new_node == NULL:
                raise SelectolaxError("Can't create a new node")
            lxb_dom_node_insert_child(self.node, <lxb_dom_node_t *> new_node)
        else:
            raise SelectolaxError("Expected a string or LexborNode instance, but %s found" % type(value).__name__)

        self.parser._mark_mutated()

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
        raise NotImplementedError("This feature is not supported by the lexbor backend.")

    def scripts_contain(self, str query):
        """Returns True if any of the script tags contain specified text.

        The script texts are cached per document, keyed both by the node the
        search was rooted at and by the document's mutation counter, so
        repeating the call on the same subtree is cheap while a different
        subtree - or an edited tree - never reuses the previous answer.

        Parameters
        ----------
        query : str
            The query to check.

        """
        cdef LexborNode root = self._get_node()
        cdef list texts = _cached_script_values(
            self.parser.cached_script_texts,
            <size_t> root.node,
            self.parser._mutation_count,
        )
        if texts is None:
            texts = _collect_script_texts(root)
            self.parser.cached_script_texts = (
                <size_t> root.node,
                self.parser._mutation_count,
                texts,
            )

        for text in texts:
            if query in text:
                return True
        return False

    def script_srcs_contain(self, tuple queries):
        """Returns True if any of the script SRCs attributes contain on of the specified text.

        The ``src`` values are cached per document, keyed both by the node the
        search was rooted at and by the document's mutation counter, so
        repeating the call on the same subtree is cheap while a different
        subtree - or an edited tree, including one whose ``src`` was changed
        through ``attrs`` - never reuses the previous answer.

        Parameters
        ----------
        queries : tuple of str

        """
        cdef LexborNode root = self._get_node()
        cdef list srcs = _cached_script_values(
            self.parser.cached_script_srcs,
            <size_t> root.node,
            self.parser._mutation_count,
        )
        if srcs is None:
            srcs = _collect_script_srcs(root)
            self.parser.cached_script_srcs = (
                <size_t> root.node,
                self.parser._mutation_count,
                srcs,
            )

        for src in srcs:
            for query in queries:
                if query in src:
                    return True
        return False

    def remove(self, bool recursive=True):
        """An alias for the decompose method."""
        self.decompose(recursive)

    def select(self, query=None):
        """Select nodes given a CSS selector.

        Works similarly to the the ``css`` method, but supports chained filtering and extra features.

        Parameters
        ----------
        query : str or None
            The CSS selector to use when searching for nodes.

        Returns
        -------
        selector : The `Selector` class.
        """
        return LexborSelector(self._get_node(), query)

    def __eq__(self, other):
        """Compare by serialized HTML.

        Comparing against a ``str`` compares it to this node's ``html``.
        Comparing against another ``LexborNode`` compares the two serialized
        subtrees, which costs two HTML serializations.
        """
        if isinstance(other, str):
            return self.html == other
        if not isinstance(other, LexborNode):
            return False
        cdef LexborNode other_node = <LexborNode> other
        if self.node == other_node.node and self._is_fragment_root == other_node._is_fragment_root:
            return True
        return self.html == other_node.html

    @property
    def text_content(self):
        """Returns the text of the node if it is a text node.

        Returns None for other nodes.
        Unlike the ``text`` method, does not include child nodes.

        Returns
        -------
        text : str or None.
        """
        cdef unsigned char * text
        cdef lexbor_str_t * str_data
        if not _is_node_type(self.node, LXB_DOM_NODE_TYPE_TEXT):
            return None

        str_data = &(<lxb_dom_character_data_t *> self.node).data
        text = <unsigned char *> lexbor_str_data_noi(str_data)
        if text != NULL:
            return _decode_utf8(text, lexbor_str_length_noi(str_data))
        return None

    @property
    def comment_content(self) -> str | None:
        """Extract the textual content of an HTML comment node.

        Returns
        -------
        str or None
            Comment text with surrounding whitespace removed, or ``None`` if
            the current node is not a comment or the comment markup cannot be
            parsed.

        Examples
        --------
        >>> LexborHTMLParser("<!-- hello -->", is_fragment=True).root.comment_content
        'hello'
        >>> LexborHTMLParser("<div>not a comment</div>", is_fragment=True).root.comment_content is None
        True
        """
        if not self.is_comment_node:
            return None
        try:
            return extract_html_comment(self.html)
        except (ValueError, AttributeError, IndexError):
            return None

    @property
    def inner_html(self) -> str | None:
        """Return HTML representation of the child nodes.

        Works similar to innerHTML in JavaScript.
        Unlike the `.html` property, does not include the current node.
        Can be used to set HTML as well. See the setter docstring.

        Returns
        -------
        text : str | None
        """

        return self._serialize_inner_html(LXB_HTML_SERIALIZE_OPT_UNDEF, 0, False)

    @inner_html.setter
    def inner_html(self, str html) -> None:
        """Set inner HTML to the specified HTML.

        Replaces existing data inside the node.
        Works similar to innerHTML in JavaScript.

        Only available for element nodes.

        Nodes the caller obtained from the replaced subtree stay valid, but are
        detached from the document, as they are after ``decompose()``.

        Parameters
        ----------
        html : str | None

        Raises
        ------
        TypeError
            If the current node is not an element node.
        SelectolaxError
            If the HTML could not be parsed into the node.

        """
        cdef bytes bytes_val

        if not _is_node_type(self.node, LXB_DOM_NODE_TYPE_ELEMENT):
            raise TypeError("inner_html is only available for element nodes")

        bytes_val = <bytes> html.encode("utf-8")
        _replace_children(
            <lxb_dom_node_t *> self.node,
            <lxb_char_t *> bytes_val,
            len(bytes_val),
        )

        # Replacing the children of <html> detaches the old <head>/<body>
        # without going through the insertion modes that normally keep the
        # document's cached head/body pointers valid, so recompute them.
        if lxb_dom_node_tag_id_noi(self.node) == LXB_TAG_HTML:
            _refresh_head_body(self.parser.document)

        self.parser._mark_mutated()

    def clone(self) -> LexborNode:
        """Clone the current node.

        You can use to do temporary modifications without affecting the original HTML tree.

        It is tied to the current parser instance.
        Gets destroyed when parser instance is destroyed.
        """
        cdef lxb_dom_node_t * node
        node = lxb_dom_node_clone(<lxb_dom_node_t *> self.node, 1)
        if node == NULL:
            raise MemoryError("Can't clone the node")
        return LexborNode.new(node, self.parser)

    @property
    def is_element_node(self) -> bool:
        """Return True if the node represents an element node."""
        return _is_node_type(self.node, LXB_DOM_NODE_TYPE_ELEMENT)

    @property
    def is_text_node(self) -> bool:
        """Return True if the node represents a text node."""
        return _is_node_type(self.node, LXB_DOM_NODE_TYPE_TEXT)

    @property
    def is_comment_node(self) -> bool:
        """Return True if the node represents a comment node."""
        return _is_node_type(self.node, LXB_DOM_NODE_TYPE_COMMENT)

    @property
    def is_document_node(self) -> bool:
        """Return True if the node represents a document node."""
        return _is_node_type(self.node, LXB_DOM_NODE_TYPE_DOCUMENT)

    @property
    def is_empty_text_node(self) -> bool:
        """Check whether the current node is an empty text node.

        Returns
        -------
        bool
            ``True`` when the node is a text node whose character data consists
            only of ASCII whitespace characters (space, tab, newline, form feed
            or carriage return).
        """
        return is_empty_text_node(self.node)


@cython.internal
@cython.final
cdef class TextContainer:
    """Accumulates the text of consecutive text nodes into a single ``str``."""

    cdef bytearray _buf
    cdef bytes _sep_bytes
    cdef list _parts
    cdef str separator
    cdef bint strip
    cdef bint skip_empty
    cdef Py_ssize_t _count
    # The walker callback cannot propagate an error out of lexbor's C code, so
    # it parks it here for the caller to re-raise rather than losing it.
    cdef object _error

    @staticmethod
    cdef TextContainer create(str separator, bint strip, bint skip_empty=False):
        cdef TextContainer cls = <TextContainer> TextContainer.__new__(TextContainer)
        cls._buf = bytearray()
        cls._sep_bytes = separator.encode(_ENCODING) if separator else b''
        cls._parts = [] if strip else None
        cls.separator = separator
        cls.strip = strip
        cls.skip_empty = skip_empty
        cls._count = 0
        cls._error = None
        return cls

    @staticmethod
    cdef TextContainer new_with_defaults():
        return TextContainer.create('', False)

    cdef inline int add_bytes(self, const unsigned char *data, Py_ssize_t length) except -1:
        """Append one raw fragment, inserting the separator before it.

        The separator is placed *between* fragments rather than after each one
        so the result matches ``separator.join(parts)`` exactly.
        """
        cdef Py_ssize_t size
        cdef Py_ssize_t sep_len

        if self.strip:
            py_str = PyUnicode_DecodeUTF8(<char *> data, length, "replace")
            PyList_Append(self._parts, py_str.strip())
            return 0

        sep_len = len(self._sep_bytes)
        if self._count > 0 and sep_len > 0:
            size = PyByteArray_GET_SIZE(self._buf)
            PyByteArray_Resize(self._buf, size + sep_len)
            memcpy(
                PyByteArray_AS_STRING(self._buf) + size,
                PyBytes_AS_STRING(self._sep_bytes),
                sep_len
            )

        size = PyByteArray_GET_SIZE(self._buf)
        PyByteArray_Resize(self._buf, size + length)
        if length > 0:
            memcpy(PyByteArray_AS_STRING(self._buf) + size, <char *> data, length)
        self._count += 1
        return 0

    cdef inline void fail(self, object error) noexcept:
        self._error = error

    cdef inline void reraise(self):
        if self._error is not None:
            error = self._error
            self._error = None
            raise error

    @property
    def text(self):
        if self.strip:
            return self.separator.join(self._parts)
        size = PyByteArray_GET_SIZE(self._buf)
        if size == 0:
            return ''
        return PyUnicode_DecodeUTF8(PyByteArray_AS_STRING(self._buf), size, "replace")


cdef lexbor_action_t text_callback(lxb_dom_node_t *node, void *ctx):
    cdef unsigned char *text
    cdef lexbor_str_t *str_data
    cdef TextContainer container = <TextContainer> ctx
    cdef lxb_tag_id_t tag_id = lxb_dom_node_tag_id_noi(node)

    if tag_id != LXB_TAG__TEXT:
        return LEXBOR_ACTION_OK

    if container.skip_empty and is_empty_text_node(node):
        return LEXBOR_ACTION_OK

    str_data = &(<lxb_dom_text_t *> node).char_data.data
    text = <unsigned char *> lexbor_str_data_noi(str_data)
    if text == NULL:
        return LEXBOR_ACTION_OK

    try:
        container.add_bytes(text, lexbor_str_length_noi(str_data))
    except BaseException as error:
        container.fail(error)
        return LEXBOR_ACTION_STOP

    return LEXBOR_ACTION_OK

cdef lxb_status_t serialize_fragment(lxb_dom_node_t *node, lexbor_str_t *lxb_str):
    cdef lxb_status_t status
    while node != NULL:
        status = lxb_html_serialize_tree_str(node, lxb_str)
        if status != LXB_STATUS_OK:
            return status
        node = node.next

    return LXB_STATUS_OK


cdef lxb_status_t serialize_fragment_pretty(
    lxb_dom_node_t *node,
    lexbor_str_t *lxb_str,
    lxb_html_serialize_opt_t options,
    size_t indent,
):
    cdef lxb_status_t status
    while node != NULL:
        status = lxb_html_serialize_pretty_tree_str(node, options, indent, lxb_str)
        if status != LXB_STATUS_OK:
            return status
        node = node.next

    return LXB_STATUS_OK


cdef inline lxb_html_serialize_opt_t _html_pretty_options(
    bint skip_ws_nodes,
    bint skip_comment,
    bint raw,
    bint without_closing,
    bint tag_with_ns,
    bint without_text_indent,
    bint full_doctype,
    bint html5test,
):
    cdef lxb_html_serialize_opt_t options = LXB_HTML_SERIALIZE_OPT_UNDEF

    if skip_ws_nodes:
        options = <lxb_html_serialize_opt_t> (options | LXB_HTML_SERIALIZE_OPT_SKIP_WS_NODES)
    if skip_comment:
        options = <lxb_html_serialize_opt_t> (options | LXB_HTML_SERIALIZE_OPT_SKIP_COMMENT)
    if raw:
        options = <lxb_html_serialize_opt_t> (options | LXB_HTML_SERIALIZE_OPT_RAW)
    if without_closing:
        options = <lxb_html_serialize_opt_t> (options | LXB_HTML_SERIALIZE_OPT_WITHOUT_CLOSING)
    if tag_with_ns:
        options = <lxb_html_serialize_opt_t> (options | LXB_HTML_SERIALIZE_OPT_TAG_WITH_NS)
    if without_text_indent:
        options = <lxb_html_serialize_opt_t> (options | LXB_HTML_SERIALIZE_OPT_WITHOUT_TEXT_INDENT)
    if full_doctype:
        options = <lxb_html_serialize_opt_t> (options | LXB_HTML_SERIALIZE_OPT_FULL_DOCTYPE)
    if html5test:
        options = <lxb_html_serialize_opt_t> (options | 0x80)

    return options

cdef inline bint _is_node_type(lxb_dom_node_t *node, lxb_dom_node_type_t expected_type):
    return node != NULL and node.type == expected_type

cdef inline void _collapse_text_runs(lxb_dom_node_t *node, lexbor_mraw_t *text_mraw):
    """Collapse each run of adjacent text children into the run's first node."""
    cdef lxb_dom_node_t *child
    cdef lxb_dom_node_t *next_node
    cdef lexbor_str_t *left_str
    cdef lexbor_str_t *right_str

    child = node.first_child
    while child != NULL:
        if child.type == LXB_DOM_NODE_TYPE_TEXT:
            left_str = &(<lxb_dom_text_t *> child).char_data.data
            # Merge the whole run into `child`, which stays put so that every
            # following sibling gets folded in as well.
            while child.next != NULL and child.next.type == LXB_DOM_NODE_TYPE_TEXT:
                next_node = child.next
                right_str = &(<lxb_dom_text_t *> next_node).char_data.data
                if lexbor_str_append(left_str, text_mraw, right_str.data, right_str.length) == NULL:
                    break
                lxb_dom_node_remove(next_node)
        child = child.next


cdef void _merge_text_nodes(lxb_dom_node_t *root):
    if root == NULL or node_is_removed(root):
        return

    cdef lxb_dom_node_t *node
    cdef lexbor_mraw_t *text_mraw

    # Text nodes own their character data inline, so a run of adjacent text
    # nodes can be collapsed straight into the first one. Appending in place
    # keeps this linear and, unlike lxb_dom_node_text_content(), needs no
    # scratch buffer taken from the document's text arena.
    text_mraw = root.owner_document.text

    # Iterative on purpose: recursing once per nesting level overflowed the C
    # stack on deeply nested HTML. Climbing back out on parent/next needs no
    # side stack and keeps each node's children visited exactly once.
    node = root
    _collapse_text_runs(node, text_mraw)

    while True:
        if node.first_child != NULL:
            node = node.first_child
        else:
            while node != NULL and node != root and node.next == NULL:
                node = node.parent
            if node == NULL or node == root:
                break
            node = node.next
        _collapse_text_runs(node, text_mraw)
