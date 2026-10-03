from cpython.bool cimport bool
from cpython.bytes cimport PyBytes_AS_STRING, PyBytes_FromStringAndSize
from cpython.exc cimport PyErr_SetObject
from cpython.mem cimport (
    PyMem_RawCalloc,
    PyMem_RawFree,
    PyMem_RawMalloc,
    PyMem_RawRealloc
)
from enum import IntFlag
from libc.string cimport memcpy

_ENCODING = 'UTF-8'

include "base.pxi"
include "utils.pxi"
include "lexbor/attrs.pxi"
include "lexbor/node.pxi"
include "lexbor/selection.pxi"
include "lexbor/util.pxi"
include "lexbor/node_remove.pxi"
include "lexbor/fragment_lookup.pxi"


class LexborDocumentOptions(IntFlag):
    """Parser options for the Lexbor document.

    These mirror the ``lxb_dom_document_opt`` flags from Lexbor.

    Multiple options can be combined with the bitwise OR operator, or by
    combining their integer values. Both of the following are equivalent:

    >>> LexborDocumentOptions.WO_EVENTS | LexborDocumentOptions.UNDEF
    <LexborDocumentOptions.WO_EVENTS: 1>
    >>> LexborDocumentOptions.WO_EVENTS.value | LexborDocumentOptions.UNDEF.value
    1

    The combined value can be passed directly to the parser::

        LexborHTMLParser(html, options=LexborDocumentOptions.WO_EVENTS)
    """

    """Original Lexbor name: ``LXB_DOM_DOCUMENT_OPT_UNDEF``.

    Default value. No options are set.
    """
    UNDEF = 0x00

    """Original Lexbor name: ``LXB_DOM_DOCUMENT_OPT_WO_EVENTS``.

    Disables mutation events ("without events"). When set, Lexbor skips the
    document mutation callbacks (``inserted``, ``removed``, ``moved``,
    ``children_changed``, ``connected``, and the attribute callbacks) while
    building or modifying the tree. This can speed up parsing, but it also
    disables behaviors implemented through those callbacks.

    For example, ``<selectedcontent>`` no longer receives a copy of the
    selected ``<option>``::

        html = (
            "<select><button><selectedcontent></selectedcontent></button>"
            "<option>a</option><option selected>b</option></select>"
        )

        LexborHTMLParser(html).css_first("selectedcontent").html
        # '<selectedcontent>b</selectedcontent>'

        LexborHTMLParser(
            html, options=LexborDocumentOptions.WO_EVENTS
        ).css_first("selectedcontent").html
        # '<selectedcontent></selectedcontent>'
    """
    WO_EVENTS = 1 << 0


cdef lxb_dom_node_t* _clone_node_into_document(
    lxb_html_document_t* document, lxb_dom_node_t* node
) except NULL:
    """Deep-copy ``node`` into ``document`` and append it as its child."""
    cdef lxb_dom_node_t* cloned

    with nogil:
        cloned = lxb_dom_document_import_node(
            &document.dom_document, node, <bint> True
        )

    if cloned == NULL:
        raise SelectolaxError("Can't create a new document")

    with nogil:
        lxb_dom_node_insert_child(<lxb_dom_node_t * > document, cloned)

    return cloned


cdef inline void _refresh_head_body(lxb_html_document_t* document):
    """Recompute the cached ``head``/``body`` pointers of a document.

    Lexbor caches ``document->head`` and ``document->body`` while building the
    tree, from its insertion modes. Code that destroys and recreates children
    directly, such as ``lxb_html_element_inner_html_set`` on the ``<html>``
    element, bypasses those insertion modes and leaves the cached pointers
    dangling. Since freed lexbor blocks go back onto a size-keyed free list,
    the very next same-size allocation can hand the same address out again, so
    a stale pointer is not merely wrong but can alias an unrelated live node.

    Both pointers are reset to ``NULL`` before the tree is scanned, so a document
    that no longer has a ``<head>``/``<body>`` reports them as absent.

    Returns
    -------
    None
    """
    cdef lxb_dom_node_t* html_node
    cdef lxb_dom_node_t* child

    if document == NULL:
        return

    document.head = NULL
    document.body = NULL

    html_node = document.dom_document.node.first_child
    while html_node != NULL:
        if lxb_dom_node_tag_id_noi(html_node) == LXB_TAG_HTML:
            break
        html_node = html_node.next

    if html_node == NULL:
        return

    child = html_node.first_child
    while child != NULL:
        if lxb_dom_node_tag_id_noi(child) == LXB_TAG_HEAD:
            document.head = <lxb_html_head_element_t *> child
        elif lxb_dom_node_tag_id_noi(child) == LXB_TAG_BODY:
            document.body = <lxb_html_body_element_t *> child
        child = child.next


cdef inline void _maybe_refresh_head_body(
    lxb_html_document_t* document, lxb_dom_node_t* removed
):
    """Re-point a document's cached ``head``/``body`` if ``removed`` was one.

    ``document->head`` and ``document->body`` are written only by the parser's
    insertion modes and are never cleared afterwards, so unlinking or freeing
    either element leaves the cache pointing at a node that is no longer part
    of the document. ``lxb_html_document_head_element_noi`` returns that cache
    verbatim, which is what makes ``parser.head`` / ``parser.body`` hand out a
    detached node after e.g. ``parser.body.unwrap()``.

    Comparing pointer values is safe even when the cached node has already been
    freed; the pointers are only ever assigned by ``_refresh_head_body``,
    which rescans the tree instead of reading the stale value.

    Any mutation that detaches a node must call this, so that the removal
    sources of truth stay in sync. It is deliberately not fired when the
    removed node merely *contains* the head/body (``<html>``): unwrapping
    ``<html>`` leaves both elements alive and attached to the document, which
    is a legitimate state that ``parser.head`` / ``parser.body`` keep reporting.

    Parameters
    ----------
    document : lxb_html_document_t *
        Document whose caches may need updating. ``NULL`` is ignored.
    removed : lxb_dom_node_t *
        The node that has just been unlinked from the tree. ``NULL`` is ignored.

    Returns
    -------
    None
    """
    if document == NULL or removed == NULL:
        return

    if removed == <lxb_dom_node_t *> document.head:
        _refresh_head_body(document)
    elif removed == <lxb_dom_node_t *> document.body:
        _refresh_head_body(document)


cdef inline list _cached_script_values(
    object cached, size_t scope, unsigned long epoch
):
    """Return a cached script lookup result, or ``None`` when it is not usable.

    A cache entry is the ``(scope, epoch, values)`` triple written by
    ``scripts_contain`` / ``script_srcs_contain``. Both components have to line
    up before the entry may be reused:

    ``scope``
        The address of the node the lookup was rooted at. Storing it is what
        stops a node-scoped lookup from answering with the results of a
        different node - or of the whole document - since ``LexborNode`` is a
        view onto a shared tree and both kinds of call land in the same cache.
    ``epoch``
        The value of the document's ``_mutation_count`` when the entry was
        built. Editing the tree bumps that counter, so an entry built before an
        edit can never be read afterwards.

    A stale entry is never distinguishable from a valid one, so anything that
    is not an exact match is reported as missing and simply recomputed. Only
    extra work can result from that, never a wrong answer.

    Parameters
    ----------
    cached : object
        Cache entry, or ``None`` when nothing has been cached yet.
    scope : size_t
        Address of the node the current lookup is rooted at.
    epoch : unsigned long
        The document's current ``_mutation_count``.

    Returns
    -------
    list or None
        The cached values, or ``None`` when the entry is absent or stale.
    """
    if cached is None:
        return None

    if (<size_t> cached[0]) != scope or (<unsigned long> cached[1]) != epoch:
        return None

    return <list> cached[2]


cdef inline list _collect_script_texts(LexborNode root):
    """Collect the text of every ``<script>`` in the subtree of ``root``.

    ``root`` is the node the search is actually rooted at, so callers pass
    ``node._get_node()``: a fragment's root is a single node whose siblings
    belong to the fragment too, and searching from the node alone would skip
    every script outside the first top-level node.
    """
    cdef LexborNode node

    texts = []
    for node in root.parser.selector.find('script', root):
        node_text = node.text(deep=True)
        if node_text:
            texts.append(node_text)

    return texts


cdef inline list _collect_script_srcs(LexborNode root):
    """Collect the ``src`` of every ``<script>`` in the subtree of ``root``.

    Rooted at ``node._get_node()`` for the same reason as
    ``_collect_script_texts``.
    """
    cdef LexborNode node

    srcs = []
    for node in root.parser.selector.find('script', root):
        node_src = node.attrs.get('src')
        if node_src:
            srcs.append(node_src)

    return srcs


cdef class LexborHTMLParser:
    """The lexbor HTML parser.

    Use this class to parse raw HTML.

    ``raw_html`` holds the bytes that were parsed. That is the UTF-8 form of the
    input, so for non-UTF-8 input read with ``encoding=True`` it is the
    transcoded document rather than the bytes that were passed in.

    Notes
    -----
    Not thread-safe: use one parser per thread, or lock the parser. The shared
    per-parser ``LexborCSSSelector`` races on a free-threaded build, so even
    read-only ``css()`` calls can interfere.
    """
    def __init__(
        self,
        html: str | bytes,
        is_fragment: bool = False,
        fragment_tag: str = "div",
        fragment_namespace: str = "html",
        options: int = 0,
        encoding: bool = False,
    ):
        """Create a parser and load HTML.

        Parameters
        ----------
        html : str or bytes
            HTML content to parse.
            Bytes are parsed as UTF-8; see ``encoding`` to have the encoding
            detected instead.
        is_fragment : bool, optional
            When ``False`` (default), the input is parsed as a full HTML document.
            If the input is only a fragment, the parser still accepts it and inserts any missing required elements,
            (such as `<html>`, `<head>`, and `<body>`) into the tree,
            according to the HTML parsing rules in the HTML Standard.
            This matches how browsers construct the DOM when they load an HTML page.

            When ``True``, the input is parsed as an HTML fragment.
            The parser does not insert any missing required HTML elements.
            Behaves the same way as `DocumentFragment` in browsers.
            When `<html>`, `<head>` or `<body>` are present, ignores them entirely.
            As per the HTML Standard.
        fragment_tag : str, optional
            Context element tag used for fragment parsing. Defaults to ``"div"``.
            Only used when ``is_fragment`` is ``True``.
        fragment_namespace : str, optional
            Context element namespace used for fragment parsing. Defaults to ``"html"``.
            Accepts Lexbor namespace names such as ``"html"``, ``"svg"``, and ``"math"``,
            or a namespace URI recognized by Lexbor. Only used when ``is_fragment`` is ``True``.
        options : int, optional
            Lexbor document options, a combination of :class:`LexborDocumentOptions` flags.
            Defaults to ``0``, which enables DOM mutation events.
            Pass ``options`` only when you need a non-default behaviour.

            Mutation events are the side effects Lexbor applies to the tree after parsing.
            For example, the HTML Standard has `<selectedcontent>` mirror the selected
            `<option>`'s content, so by default the parser clones it into place::

                >>> html = (
                ...     "<select><selectedcontent></selectedcontent>"
                ...     "<option>this gets cloned</option></select>"
                ... )
                >>> LexborHTMLParser(html).css_first("selectedcontent").html
                '<selectedcontent>this gets cloned</selectedcontent>'

            ``WO_EVENTS`` ("without events") turns that off, so the element keeps
            whatever the source actually contained::

                >>> LexborHTMLParser(
                ...     html, options=LexborDocumentOptions.WO_EVENTS
                ... ).css_first("selectedcontent").html
                '<selectedcontent></selectedcontent>'

            Reach for it when you want the raw source rather than the browser-normalised
            tree, for example to round-trip HTML or diff markup between two documents.
            Leave it at ``0`` when you want a tree that matches what a browser would build.

            Several flags can be combined with the bitwise OR operator::

                LexborDocumentOptions.WO_EVENTS | LexborDocumentOptions.UNDEF

            or by passing the equivalent plain integer::

                LexborDocumentOptions.WO_EVENTS.value | LexborDocumentOptions.UNDEF.value

        encoding : bool, optional
            Detect the encoding of ``bytes`` input and transcode it to UTF-8
            before parsing. Defaults to ``False``, which parses bytes as UTF-8.

            Text input is never affected: a ``str`` is already decoded, so there
            is nothing to detect.

            Detection follows the HTML Standard. A byte-order mark wins over any
            declaration, and a ``<meta charset>`` or
            ``<meta http-equiv="content-type" content="...charset=...">``
            declaration is honoured within the first 1024 bytes, which is where
            the Standard stops looking. Bytes that are invalid in the detected
            encoding become U+FFFD rather than being kept as they are::

                >>> raw = '<meta charset="windows-1251"><p>Привет</p>'.encode('windows-1251')
                >>> LexborHTMLParser(raw).text()
                '������'
                >>> LexborHTMLParser(raw, encoding=True).text()
                'Привет'

            Input that declares nothing is decoded as UTF-8, not as the
            windows-1252 a browser would fall back to, so that turning this on
            cannot reinterpret a document that already parsed correctly. A
            declaration naming something that cannot read text is ignored the
            same way - an unknown label, or one of the codec module's binary
            and text-transform pseudo-encodings such as ``base64`` or ``rot13`` -
            so no page can fail its own parse by choosing one.

            The encoding is resolved before parsing, so this costs one extra pass
            over non-UTF-8 input and nothing at all for UTF-8.

        """
        cdef size_t html_len
        cdef object bytes_html

        self._is_fragment = is_fragment
        self._fragment_wrapper = NULL
        self._fragment_tag_id = LXB_TAG_DIV
        self._fragment_namespace_id = LXB_NS_HTML
        self._selector = None
        self._new_html_document()
        lxb_html_document_dom_opt_set(self.document, <lxb_dom_document_opt_t> int(options))

        if self._is_fragment:
            self._fragment_tag_id = _fragment_tag_id_from_string(self.document, fragment_tag)
            self._fragment_namespace_id = _fragment_namespace_id_from_string(self.document, fragment_namespace)
        bytes_html, html_len = preprocess_input(html, encoding=encoding)
        self._parse_html(bytes_html, html_len)
        self.raw_html = bytes_html

    cdef inline void _new_html_document(self):
        """Initialize a fresh Lexbor HTML document.

        Returns
        -------
        None

        Raises
        ------
        SelectolaxError
            If the underlying Lexbor document cannot be created.
        """
        with nogil:
            self.document = lxb_html_document_create()

        if self.document == NULL:
            PyErr_SetObject(SelectolaxError, "Failed to initialize object for HTML Document.")

    cdef int _parse_html(self, char *html, size_t html_len) except -1:
        """Parse HTML content into the internal document.

        Parameters
        ----------
        html : char *
            Pointer to UTF-8 encoded HTML bytes.
        html_len : size_t
            Length of the HTML buffer.

        Returns
        -------
        int
            ``0`` on success; ``-1`` when parsing fails.

        Raises
        ------
        SelectolaxError
            If Lexbor returns a non-OK status.
        RuntimeError
            If the internal document is ``NULL`` after a successful parse.
        """
        cdef lxb_status_t status

        if self.document == NULL:
            return -1

        with nogil:
            if self._is_fragment:
                status = self._parse_html_fragment(html, html_len)
            else:
                status = self._parse_html_document(html, html_len)

        if status != LXB_STATUS_OK:
            PyErr_SetObject(SelectolaxError, "Can't parse HTML.")
            return -1

        if self.document == NULL:
            PyErr_SetObject(RuntimeError, "document is NULL even after html was parsed correctly")
            return -1
        return 0

    cdef inline lxb_status_t _parse_html_document(self, char *html, size_t html_len) noexcept nogil:
        """Parse HTML as a full HTML document.
        If the input is only a fragment, the parser still accepts it and inserts any missing required elements,
        (such as `<html>`, `<head>`, and `<body>`) into the tree,
        according to the HTML parsing rules in the HTML Standard.
        This matches how browsers construct the DOM when they load an HTML page.

        Parameters
        ----------
        html : char *
            Pointer to UTF-8 encoded HTML bytes.
        html_len : size_t
            Length of the HTML buffer.

        Returns
        -------
        lxb_status_t
            Lexbor status code produced by ``lxb_html_document_parse``.
        """
        return lxb_html_document_parse(self.document, <lxb_char_t *> html, html_len)

    cdef inline lxb_status_t _parse_html_fragment(self, char *html, size_t html_len) noexcept nogil:
        """Parse HTML as an HTML fragment.
        The parser does not insert any missing required HTML elements.

        Parameters
        ----------
        html : char *
            Pointer to UTF-8 encoded HTML bytes.
        html_len : size_t
            Length of the HTML buffer.

        Returns
        -------
        lxb_status_t
            Lexbor status code; ``LXB_STATUS_OK`` when parsing the fragment succeeded.
        """
        cdef lxb_html_parser_t *parser = NULL
        cdef lxb_dom_node_t *fragment_html_node = NULL
        cdef lxb_status_t status = LXB_STATUS_OK

        parser = lxb_html_parser_create()
        if parser == NULL:
            return LXB_STATUS_ERROR_MEMORY_ALLOCATION

        status = lxb_html_parser_init(parser)
        if status != LXB_STATUS_OK:
            lxb_html_parser_destroy(parser)
            return status

        fragment_html_node = lxb_html_parse_fragment_by_tag_id(
            parser,
            self.document,
            self._fragment_tag_id,
            self._fragment_namespace_id,
            <lxb_char_t *> html,
            html_len
        )
        if fragment_html_node == NULL:
            status = parser.status
            lxb_html_parser_destroy(parser)
            if status == LXB_STATUS_OK:
                return LXB_STATUS_ERROR
            return status

        self._fragment_wrapper = fragment_html_node
        lxb_html_parser_destroy(parser)
        return LXB_STATUS_OK

    cdef inline lxb_dom_node_t* _fragment_root_node(self):
        """Return the fragment's current top-level root node.

        A fragment's root is simply the first child of the wrapper ``<html>``
        element that Lexbor builds while parsing, so it is read from the wrapper
        on every access instead of being cached once at parse time. Caching it
        went stale as soon as the tree was mutated: ``unwrap()``,
        ``decompose()``, ``replace_with()`` and ``strip_tags()`` can all unlink
        that first child, and ``insert_before()`` can push a new node in front
        of it. A stale pointer is worse than merely wrong here, because freed
        lexbor blocks go back onto a size-keyed free list, so the very next
        same-size allocation can hand the same address out again and a stale
        value can alias an unrelated live node.

        The wrapper itself is a stable anchor for the parser's lifetime: Lexbor
        allocates it from the document's ``mraw``, and removing a node only
        unlinks it, never frees it.

        Returns
        -------
        lxb_dom_node_t* or NULL
            The first top-level child of the fragment, or ``NULL`` when the
            fragment is empty. Also ``NULL`` for non-fragment parsers.
        """
        if self._fragment_wrapper == NULL:
            return NULL

        return self._fragment_wrapper.first_child

    cdef inline lxb_dom_node_t* _tag_search_root(self):
        """Return the node that tag lookups start from.

        A tag lookup walks the descendants of the node it is given, so a document
        is rooted at the document node, whose child is ``<html>``. A fragment
        cannot be: Lexbor re-attaches its wrapper ``<html>`` element by writing
        only the wrapper's ``parent`` pointer, never linking it into the
        document's child list, so a walk from the document node misses the whole
        fragment. Rooting at the wrapper covers it, and since the walk starts at
        ``first_child`` the wrapper never matches itself.
        """
        if self._fragment_wrapper != NULL:
            return self._fragment_wrapper

        return <lxb_dom_node_t *> self.document

    cdef inline void _mark_mutated(self) noexcept:
        """Record that the document was edited, invalidating derived caches.

        ``LexborNode`` is a view onto a mutable tree, so a value read out of
        that tree - the script text and ``src`` lookups behind
        ``scripts_contain`` / ``script_srcs_contain`` - only stays true as long
        as the document has not been edited since. Bumping this counter is the
        single invalidation mechanism for them: the cached entries record the
        counter they were built at and are discarded once it moves, so there is
        no cache to reset and therefore none that a missed call can leave
        stale.

        Every operation that changes the tree or an attribute must call this:
        ``decompose``/``remove``, ``unwrap``, ``merge_text_nodes``,
        ``replace_with``, ``insert_before``/``insert_after``/
        ``insert_child``, the ``inner_html`` setter, ``strip_tags`` and the
        ``attrs`` mutators. It is deliberately cheap and unconditional:
        marking a document that did not really change only costs a recompute,
        whereas failing to mark one that did silently answers with the previous
        answer.

        Over-marking does lose the cache when a mutation is applied and then
        rolled back - ``node.attrs['src'] = node.attrs['src']`` - but the tree
        is unchanged in that case, so the next lookup just repopulates it.

        Returns
        -------
        None
        """
        self._mutation_count += 1

    def __dealloc__(self):
        """Release the underlying Lexbor HTML document.

        Returns
        -------
        None

        Notes
        -----
        Safe to call multiple times; does nothing if the document is already
        freed.
        """
        if self.document != NULL:
            lxb_html_document_destroy(self.document)

    def __repr__(self):
        """Return a concise representation of the parsed document.

        Returns
        -------
        str
            A string showing the number of characters in the parsed HTML.
        """
        html_len = len(self.root.html if self.root is not None else "")
        return f"<LexborHTMLParser chars='{html_len}'>"

    @property
    def selector(self):
        """Return a lazily created CSS selector helper.

        Returns
        -------
        LexborCSSSelector
            Selector instance bound to this parser.
        """
        if self._selector is None:
            self._selector = LexborCSSSelector()
        return self._selector

    @property
    def options(self):
        """Return the Lexbor document options for this parser.

        Returns
        -------
        LexborDocumentOptions
            The options currently set on the underlying Lexbor document.
        """
        return LexborDocumentOptions(lxb_html_document_dom_opt(self.document))

    @property
    def root(self):
        """Return the document root node.

        For a fragment, this is the fragment's current top-level root, which
        tracks the tree as it is mutated: once the previous first child is
        unwrapped, decomposed or replaced, the next one takes its place, and an
        emptied fragment reports ``None``.

        Returns
        -------
        LexborNode or None
            Root of the parsed document, or ``None`` if unavailable.
        """
        if self.document == NULL:
            return None
        cdef LexborNode  node
        cdef lxb_dom_node_t* dom_root
        if self._is_fragment:
            dom_root = self._fragment_root_node()
        else:
            dom_root = lxb_dom_document_root(&self.document.dom_document)
        if dom_root == NULL:
            return None
        node =  LexborNode.new(dom_root, self)
        if self._is_fragment:
            node.set_as_fragment_root()
        return node

    @property
    def body(self):
        """Return document body.

        Reflects the current tree: returns ``None`` once the ``<body>`` has been
        removed from the document, for example by ``unwrap()``,
        ``unwrap_tags()``, ``strip_tags()``, ``decompose()`` or
        ``replace_with()``.

        Returns
        -------
        LexborNode or None
            ``<body>`` element when present, otherwise ``None``.
        """
        cdef lxb_html_body_element_t* body
        if self.document == NULL:
            return None
        body = lxb_html_document_body_element_noi(self.document)
        if body == NULL:
            return None
        return LexborNode.new(<lxb_dom_node_t *> body, self)

    @property
    def head(self):
        """Return document head.

        Reflects the current tree: returns ``None`` once the ``<head>`` has
        been removed from the document, for example by ``unwrap()``,
        ``unwrap_tags()``, ``strip_tags()``, ``decompose()`` or
        ``replace_with()``.

        Returns
        -------
        LexborNode or None
            ``<head>`` element when present, otherwise ``None``.
        """
        cdef lxb_html_head_element_t* head
        if self.document == NULL:
            return None
        head = lxb_html_document_head_element_noi(self.document)
        if head == NULL:
            return None
        return LexborNode.new(<lxb_dom_node_t *> head, self)

    def tags(self, str name):
        """Return all tags that match the provided name.

        Parameters
        ----------
        name : str
            Tag name to search for (e.g., ``"div"``).

        Returns
        -------
        list of LexborNode
            Matching elements in document order.

        Raises
        ------
        ValueError
            If ``name`` is empty or longer than 100 characters.
        SelectolaxError
            If Lexbor cannot locate the elements.
        """

        if not name:
            raise ValueError("Tag name cannot be empty")
        if len(name) > 100:
            raise ValueError("Tag name is too long")

        cdef lxb_dom_collection_t* collection = NULL
        cdef lxb_status_t status
        pybyte_name = name.encode('UTF-8')

        result = list()
        collection = lxb_dom_collection_make(&self.document.dom_document, 128)

        if collection == NULL:
            return result
        status = lxb_dom_elements_by_tag_name(
            <lxb_dom_element_t *> self._tag_search_root(),
            collection,
            <lxb_char_t *> pybyte_name,
            len(pybyte_name)
        )
        if status != 0x0000:
            lxb_dom_collection_destroy(collection, <bint> True)
            raise SelectolaxError("Can't locate elements.")

        for i in range(lxb_dom_collection_length_noi(collection)):
            node = LexborNode.new(
                <lxb_dom_node_t*> lxb_dom_collection_element_noi(collection, i),
                self
            )
            result.append(node)
        lxb_dom_collection_destroy(collection, <bint> True)
        return result

    def text(
        self,
        deep: bool = True,
        separator: str = "",
        strip: bool = False,
        skip_empty: bool = False,
    ) -> str:
        """Returns the text of the node including text of all its child nodes.

        Parameters
        ----------
        strip : bool, default False
            If true, calls ``str.strip()`` on each text part to remove extra white spaces.
        separator : str, default ''
            The separator to use when joining text from different nodes.
        deep : bool, default True
            If True, includes text from all child nodes.
        skip_empty : bool, optional
            Exclude text nodes whose content is only ASCII whitespace (space,
            tab, newline, form feed or carriage return) when ``True``.
            Defaults to ``False``.

        Returns
        -------
        text : str
            Combined textual content assembled according to the provided options.
        """
        if self.root is None:
            return ""
        return self.root.text(deep=deep, separator=separator, strip=strip, skip_empty=skip_empty)

    @property
    def html(self):
        """Return HTML representation of the page.

        Returns
        -------
        str or None
            Serialized HTML of the current document.
        """
        if self.document == NULL:
            return None
        if self._is_fragment:
            if self.root is None:
                return ""
            return self.root.html
        node = LexborNode.new(<lxb_dom_node_t *> &self.document.dom_document, self)
        return node.html

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
        """Return pretty-printed HTML representation of the page.

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
        if self.document == NULL:
            return None
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
        if self._is_fragment:
            if self.root is None:
                return None
            return self.root.html_pretty(
                indent=indent,
                skip_ws_nodes=skip_ws_nodes,
                skip_comment=skip_comment,
                raw=raw,
                without_closing=without_closing,
                tag_with_ns=tag_with_ns,
                without_text_indent=without_text_indent,
                full_doctype=full_doctype,
                html5test=html5test,
            )
        node = LexborNode.new(<lxb_dom_node_t *> &self.document.dom_document, self)
        return node._serialize_html(options, <size_t> indent, True)

    def css(self, str query):
        """A CSS selector.

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
        cdef LexborNode node = self.root
        if node is None:
            return []
        return node.css(query)

    def css_first(self, str query, default=None, strict=False):
        """Same as `css` but returns only the first match.

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
        cdef LexborNode node = self.root
        if node is None:
            return default
        return node.css_first(query, default, strict)

    def strip_tags(self, list tags, bool recursive = False):
        """Remove specified tags from the node.

        Parameters
        ----------
        tags : list of str
            List of tags to remove.
        recursive : bool, default False
            Whenever to delete all its child nodes

        Examples
        --------

        >>> tree = LexborHTMLParser('<html><head></head><body><script></script><div>Hello world!</div></body></html>')
        >>> tags = ['head', 'style', 'script', 'xmp', 'iframe', 'noembed', 'noframes']
        >>> tree.strip_tags(tags)
        >>> tree.html
        '<html><body><div>Hello world!</div></body></html>'

        Returns
        -------
        None
        """
        cdef lxb_dom_collection_t* collection = NULL
        cdef lxb_dom_element_t* element
        cdef lxb_status_t status

        for tag in tags:
            pybyte_name = tag.encode('UTF-8')

            collection = lxb_dom_collection_make(&self.document.dom_document, 128)

            if collection == NULL:
                raise SelectolaxError("Can't initialize DOM collection.")

            status = lxb_dom_elements_by_tag_name(
                <lxb_dom_element_t *> self._tag_search_root(),
                collection,
                <lxb_char_t *> pybyte_name,
                len(pybyte_name)
            )
            if status != 0x0000:
                lxb_dom_collection_destroy(collection, <bint> True)
                raise SelectolaxError("Can't locate elements.")

            for i in range(lxb_dom_collection_length_noi(collection)):
                element = lxb_dom_collection_element_noi(collection, i)
                if recursive:
                    node_remove_deep(<lxb_dom_node_t *> element)
                else:
                    lxb_dom_node_remove(<lxb_dom_node_t *> element)
                _maybe_refresh_head_body(self.document, <lxb_dom_node_t *> element)
            lxb_dom_collection_destroy(collection, <bint> True)

        self._mark_mutated()

    def select(self, query=None):
        """Select nodes given a CSS selector.

        Works similarly to the ``css`` method, but supports chained filtering and extra features.

        Parameters
        ----------
        query : str or None
            The CSS selector to use when searching for nodes.

        Returns
        -------
        LexborSelector or None
            Selector bound to the root node, or ``None`` if the document is empty.
        """
        cdef LexborNode node
        node = self.root
        if node:
            return LexborSelector(node, query)
        return None

    def any_css_matches(self, tuple selectors):
        """Return ``True`` if any of the specified CSS selectors match.

        Parameters
        ----------
        selectors : tuple[str]
            CSS selectors to evaluate.

        Returns
        -------
        bool
            ``True`` when at least one selector matches.
        """
        cdef LexborNode node = self.root
        if node is None:
            return False
        return node.any_css_matches(selectors)

    def scripts_contain(self, str query):
        """Return ``True`` if any script tag contains the given text.

        The script texts are cached per document, so repeating the call is
        cheap. The cache is keyed by the node the search was rooted at and by
        the document's mutation counter, so it is dropped as soon as the tree
        is edited and a node-scoped lookup never reuses the document-wide
        result, or vice versa.

        Parameters
        ----------
        query : str
            Text to search for within script contents.

        Returns
        -------
        bool
            ``True`` when a matching script tag is found.
        """
        cdef LexborNode node = self.root
        if node is None:
            return False
        return node.scripts_contain(query)

    def script_srcs_contain(self, tuple queries):
        """Return ``True`` if any script ``src`` contains one of the strings.

        The ``src`` values are cached per document, so repeating the call is
        cheap. The cache is keyed by the node the search was rooted at and by
        the document's mutation counter, so it is dropped as soon as the tree
        is edited - including when a ``src`` is changed through ``attrs`` - and
        a node-scoped lookup never reuses the document-wide result, or vice
        versa.

        Parameters
        ----------
        queries : tuple of str
            Strings to look for inside ``src`` attributes.

        Returns
        -------
        bool
            ``True`` when a matching source value is found.
        """
        cdef LexborNode node = self.root
        if node is None:
            return False
        return node.script_srcs_contain(queries)

    def css_matches(self, str selector):
        """Return ``True`` if the document matches the selector at least once.

        Parameters
        ----------
        selector : str
            CSS selector to test.

        Returns
        -------
        bool
            ``True`` when a match exists.
        """
        cdef LexborNode node = self.root
        if node is None:
            return False
        return node.css_matches(selector)

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

        Returns
        -------
        None
        """
        cdef LexborNode node = self.root
        if node is None:
            return
        return node.merge_text_nodes()

    @staticmethod
    cdef LexborHTMLParser from_document(lxb_html_document_t *document, bytes raw_html):
        """Construct a parser from an existing Lexbor document.

        Parameters
        ----------
        document : lxb_html_document_t *
            Borrowed pointer to an initialized Lexbor HTML document.
        raw_html : bytes
            Original HTML bytes backing the document.

        Returns
        -------
        LexborHTMLParser
            Parser instance wrapping the provided document.
        """
        obj = <LexborHTMLParser> LexborHTMLParser.__new__(LexborHTMLParser)
        obj.document = document
        obj.raw_html = raw_html
        obj.cached_script_texts = None
        obj.cached_script_srcs = None
        obj._is_fragment = False
        obj._fragment_wrapper = NULL
        obj._fragment_tag_id = LXB_TAG_DIV
        obj._fragment_namespace_id = LXB_NS_HTML
        obj._selector = None
        return obj

    def clone(self):
        """Clone the current document tree.

        You can use to do temporary modifications without affecting the original HTML tree.
        It is tied to the current parser instance.
        Gets destroyed when the parser instance is destroyed.
        Document options are preserved in the cloned parser.
        The document ``head`` and ``body`` are preserved when available.

        Returns
        -------
        LexborHTMLParser
            A parser instance backed by a deep-copied document.
        """
        cdef lxb_html_document_t* cloned_document
        cdef lxb_dom_node_t* cloned_node
        cdef lxb_dom_node_t* source_child
        cdef lxb_dom_node_t* next_child
        cdef LexborHTMLParser cls

        with nogil:
            cloned_document = lxb_html_document_create()

        if cloned_document == NULL:
            raise SelectolaxError("Can't create a new document")

        try:
            lxb_html_document_dom_opt_set(
                cloned_document, lxb_html_document_dom_opt(self.document)
            )

            cloned_document.ready_state = LXB_HTML_DOCUMENT_READY_STATE_COMPLETE

            cloned_node = NULL

            if self._is_fragment:
                if self._fragment_root_node() != NULL:
                    cloned_node = _clone_node_into_document(
                        cloned_document, self._fragment_wrapper
                    )
            else:
                source_child = self.document.dom_document.node.first_child
                while source_child != NULL:
                    next_child = source_child.next
                    cloned_node = _clone_node_into_document(cloned_document, source_child)
                    source_child = next_child

                _refresh_head_body(cloned_document)

            cls = LexborHTMLParser.from_document(cloned_document, self.raw_html)
        except BaseException:
            # Ownership of the document only moves to cls once it exists.
            lxb_html_document_destroy(cloned_document)
            raise

        if self._is_fragment:
            cls._is_fragment = True
            cls._fragment_tag_id = self._fragment_tag_id
            cls._fragment_namespace_id = self._fragment_namespace_id
            cls._fragment_wrapper = cloned_node
        return cls

    def unwrap_tags(self, list tags, delete_empty = False):
        """Unwraps specified tags from the HTML tree.

        Works the same as the ``unwrap`` method, but applied to a list of tags.

        Parameters
        ----------
        tags : list
            List of tags to remove.
        delete_empty : bool
            Whenever to delete empty tags.

        Examples
        --------

        >>> tree = LexborHTMLParser("<div><a href="">Hello</a> <i>world</i>!</div>")
        >>> tree.body.unwrap_tags(['i','a'])
        >>> tree.body.html
        '<body><div>Hello world!</div></body>'

        Returns
        -------
        None
        """
        # faster to check if the document is empty which should determine if we have a root
        cdef LexborNode node
        if self.document != NULL:
            node = self.root
            if node is not None:
                node.unwrap_tags(tags, delete_empty=delete_empty)

    @property
    def inner_html(self) -> str:
        """Return HTML representation of the child nodes.

        Works similar to innerHTML in JavaScript.
        Unlike the `.html` property, does not include the current node.
        Can be used to set HTML as well. See the setter docstring.

        Returns
        -------
        text : str | None
        """
        cdef LexborNode node = self.root
        if node is None:
            return ""
        return node.inner_html

    @inner_html.setter
    def inner_html(self, str html):
        """Set inner HTML to the specified HTML.

        Replaces existing data inside the node.
        Works similar to innerHTML in JavaScript.

        Parameters
        ----------
        html : str

        Returns
        -------
        None
        """
        cdef LexborNode node = self.root
        if node is None:
            return
        node.inner_html = html

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
        if self.root is None:
            return None
        return self.root.inner_html_pretty(
            indent=indent,
            skip_ws_nodes=skip_ws_nodes,
            skip_comment=skip_comment,
            raw=raw,
            without_closing=without_closing,
            tag_with_ns=tag_with_ns,
            without_text_indent=without_text_indent,
            full_doctype=full_doctype,
            html5test=html5test,
        )

    def create_node(self, str tag):
        """Given an HTML tag name, e.g. `"div"`, create a single empty node for that tag,
        e.g. `"<div></div>"`.

        Parameters
        ----------
        tag : str
            Name of the tag to create.

        Returns
        -------
        LexborNode
            Newly created element node.

        Raises
        ------
        SelectolaxError
            If the element cannot be created.

        Examples
        --------
        >>> parser = LexborHTMLParser("<div></div>")
        >>> new_node = parser.create_node("span")
        >>> new_node.tag_name
        'span'
        >>> parser.css_first("div").append_child(new_node)
        >>> parser.html
        '<html><head></head><body><div><span></span></div></body></html>'
        """
        cdef lxb_html_element_t* element
        cdef lxb_dom_node_t* dom_node
        if not tag:
            raise SelectolaxError("Tag name cannot be empty")
        pybyte_name = tag.encode('UTF-8')

        element = lxb_html_document_create_element(
            self.document,
            <const lxb_char_t *> pybyte_name,
            len(pybyte_name),
            NULL
        )

        if element == NULL:
            raise SelectolaxError(f"Can't create element for tag '{tag}'")

        dom_node = <lxb_dom_node_t *> element

        return LexborNode.new(dom_node, self)

# Putting lexbor on python's heap is better than putting it
# onto C's Heap, because python's Garbage collector can collect
# this memory after use and has the bonus of gaining access to
# mimalloc which python uses under the hood...
if lexbor_memory_setup(
    PyMem_RawMalloc,
    PyMem_RawRealloc,
    PyMem_RawCalloc,
    PyMem_RawFree
) != LXB_STATUS_OK:
    # This will almost never happen due to the code in both the windows and posix versions
    # but if something were to happen this excecption on import should be triggered...
    raise SelectolaxError("Can't initalize allocators from lexbor_memory_setup(...)")
