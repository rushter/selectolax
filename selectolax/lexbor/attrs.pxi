cimport cython


cdef inline bint _ascii_ieq(const lxb_char_t *left, const lxb_char_t *right, size_t length) noexcept nogil:
    """Compare two ASCII byte strings, ignoring case.

    Parameters
    ----------
    left, right : const lxb_char_t *
        Buffers to compare. They must be at least ``length`` bytes long.
    length : size_t
        Number of bytes to compare.

    Returns
    -------
    bint
        ``True`` when both buffers spell the same case-insensitive word.
    """
    cdef size_t i
    cdef lxb_char_t lchar
    cdef lxb_char_t rchar

    for i in range(length):
        lchar = left[i]
        rchar = right[i]
        if lchar >= 'A' and lchar <= 'Z':
            lchar = lchar + 32
        if rchar >= 'A' and rchar <= 'Z':
            rchar = rchar + 32
        if lchar != rchar:
            return False
    return True


cdef inline lxb_dom_attr_t* _attr_by_qualified_name(
    lxb_dom_node_t *node,
    const lxb_char_t *name,
    size_t name_len,
) noexcept nogil:
    """Return the attribute of ``node`` whose qualified name is ``name``.

    ``lxb_dom_element_attr_by_name()`` accepts a match on *either* the local name
    or the qualified name, so on an element carrying both ``href`` and
    ``xlink:href`` a lookup of ``href`` returns whichever of the two happens to
    come first in the attribute list rather than the one that was asked for, and
    reports the wrong value. Comparing the qualified name outright is what makes
    a lookup address exactly the attribute that iteration reports.

    The comparison is ASCII case-insensitive because HTML matches attribute
    names that way, and ``lxb_dom_attr_qualified_name()`` already lowercases
    every unprefixed name.

    Parameters
    ----------
    node : lxb_dom_node_t *
        The element node whose attributes are scanned.
    name : const lxb_char_t *
        The qualified name to look for, not necessarily NUL terminated.
    name_len : size_t
        Length of ``name`` in bytes.

    Returns
    -------
    lxb_dom_attr_t *
        The matching attribute, or ``NULL`` when the element has no such
        attribute.
    """
    cdef lxb_dom_attr_t *attr = lxb_dom_element_first_attribute_noi(<lxb_dom_element_t *> node)
    cdef const lxb_char_t *qualified
    cdef size_t str_len = 0

    while attr != NULL:
        qualified = lxb_dom_attr_qualified_name(attr, &str_len)
        if qualified != NULL and str_len == name_len and _ascii_ieq(name, qualified, name_len):
            return attr
        attr = attr.next
    return NULL


cdef inline lxb_status_t _remove_attr(lxb_dom_node_t *node, lxb_dom_attr_t *attr) noexcept nogil:
    """Unlink and free an attribute already resolved to a pointer.

    Mirrors ``lxb_dom_element_remove_attribute()``, which re-derives the
    attribute from a name and so would drop a different one whenever the lookup
    above is what disambiguated two attributes sharing a local name.

    Returns
    -------
    lxb_status_t
        ``LXB_STATUS_OK`` once the attribute is gone from the element.
    """
    cdef lxb_status_t status

    status = lxb_dom_element_attr_remove(<lxb_dom_element_t *> node, attr)
    if status != LXB_STATUS_OK:
        return status

    lxb_dom_attr_interface_destroy(attr)
    return LXB_STATUS_OK


@cython.final
cdef class LexborAttributes:
    """A dict-like object that represents attributes."""
    cdef lxb_dom_node_t *node
    # Keeps the owning document alive. ``node`` is a borrowed pointer into
    # ``parser.document``; without this reference the whole document is freed
    # as soon as the LexborNode that produced these attrs is collected, leaving
    # every method here reading freed memory.
    cdef LexborHTMLParser parser
    cdef unicode decode_errors

    def __init__(self, *args, **kwargs):
        raise TypeError(
            "LexborAttributes cannot be instantiated directly; use LexborNode.attrs "
            "on an existing element node instead."
        )

    @staticmethod
    cdef LexborAttributes create(lxb_dom_node_t *node, LexborHTMLParser parser):
        if not _is_node_type(node, LXB_DOM_NODE_TYPE_ELEMENT):
            raise TypeError("attrs is only available for element nodes")
        obj = <LexborAttributes> LexborAttributes.__new__(LexborAttributes)
        obj.node = node
        obj.parser = parser
        return obj

    cdef inline lxb_dom_attr_t* _first_attr(self) noexcept:
        return lxb_dom_element_first_attribute_noi(<lxb_dom_element_t *> self.node)

    def __iter__(self):
        cdef lxb_dom_attr_t *attr = self._first_attr()
        cdef size_t str_len = 0
        cdef const lxb_char_t *key

        while attr != NULL:
            # The qualified name, not the local name: __getitem__/__contains__/
            # __delitem__ address attributes through lxb_dom_element_attr_by_name(),
            # which expects this spelling. Yielding local names instead made the two
            # disagree -- an element with both `href` and `xlink:href` iterated as
            # ["href", "href"], and `del attrs["href"]` raised KeyError.
            key = lxb_dom_attr_qualified_name(attr, &str_len)
            if key is not NULL:
                yield key.decode(_ENCODING)
            attr = attr.next

    def _iter_pairs(self):
        """Yield ``(name, value)`` for every attribute in a single pass.

        Values are read off the attribute node the name came from rather than
        through ``__getitem__``, whose lookup is a linear scan and made this
        quadratic in the number of attributes.
        """
        cdef lxb_dom_attr_t *attr = self._first_attr()
        cdef size_t str_len = 0
        cdef const lxb_char_t *key
        cdef const lxb_char_t *value

        while attr != NULL:
            key = lxb_dom_attr_qualified_name(attr, &str_len)
            if key != NULL:
                value = lxb_dom_attr_value_noi(attr, &str_len)
                yield (
                    key.decode(_ENCODING),
                    value.decode(_ENCODING) if value != NULL else None,
                )
            attr = attr.next

    def __setitem__(self, str key, object value):
        bytes_key = key.encode(_ENCODING)
        cdef bytes bytes_value
        cdef lxb_dom_attr_t *attr
        cdef lxb_dom_document_t *doc

        if value is None:
            # N.B. This is suboptimal, but there is not API to set empty attributes
            attr = lxb_dom_element_set_attribute(
                <lxb_dom_element_t *> self.node,
                <lxb_char_t *> bytes_key, len(bytes_key),
                NULL, 0
            )
            if attr == NULL:
                raise MemoryError("Failed to set attribute")
            doc = (<lxb_dom_node_t*>attr).owner_document
            if attr.value != NULL:
                # The header comes from doc.mraw and its data from doc.text, so each must go
                # back to its own pool. lexbor_str_destroy() would release the
                # header with a plain free(), which corrupts the mraw.
                if attr.value.data != NULL:
                    lexbor_mraw_free(doc.text, attr.value.data)
                lexbor_mraw_free(doc.mraw, attr.value)
                attr.value = NULL

        elif isinstance(value, str) or isinstance(value, unicode) :
            bytes_value = value.encode(_ENCODING)
            attr = lxb_dom_element_set_attribute(
                <lxb_dom_element_t *> self.node,
                <lxb_char_t *> bytes_key, len(bytes_key),
                <lxb_char_t *> bytes_value, len(bytes_value),
            )
            if attr == NULL:
                raise MemoryError("Failed to set attribute")
        else:
            raise TypeError("Expected str or unicode, got %s" % type(value).__name__)

        self.parser._mark_mutated()

    def __delitem__(self, key):
        bytes_key = key.encode(_ENCODING)
        cdef lxb_dom_attr_t *attr = _attr_by_qualified_name(
            <lxb_dom_node_t *> self.node,
            <const lxb_char_t *> bytes_key, len(bytes_key)
        )
        if attr == NULL:
            raise KeyError(key)
        if _remove_attr(<lxb_dom_node_t *> self.node, attr) != LXB_STATUS_OK:
            raise SelectolaxError("Can't remove attribute %r" % key)
        self.parser._mark_mutated()

    def __getitem__(self, str key):
        bytes_key = key.encode(_ENCODING)
        cdef lxb_dom_attr_t * attr = _attr_by_qualified_name(
            <lxb_dom_node_t *> self.node,
            <const lxb_char_t *> bytes_key, len(bytes_key)
        )
        cdef size_t str_len = 0
        if attr != NULL:
            value = lxb_dom_attr_value_noi(attr, &str_len)
            return value.decode(_ENCODING) if value else None
        raise KeyError(key)

    def __len__(self):
        return len(list(self.__iter__()))

    def keys(self):
        return self.__iter__()

    def items(self):
        return self._iter_pairs()

    def values(self):
        for _, value in self._iter_pairs():
            yield value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def sget(self, key, default=""):
        """Same as get, but returns empty strings instead of None values for empty attributes."""
        try:
            val = self[key]
            if val is None:
                val = ""
            return val
        except KeyError:
            return default

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def __repr__(self):
        cdef const lxb_char_t *c_text
        cdef size_t str_len = 0
        c_text = lxb_dom_element_qualified_name(<lxb_dom_element_t *> self.node, &str_len)
        tag_name = c_text.decode(_ENCODING, 'ignore') if c_text != NULL else 'unknown'
        return "<%s attributes, %s items>" % (tag_name, len(self))
