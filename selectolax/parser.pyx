# cython: boundscheck=False, wraparound=False, nonecheck=False, language_level=3, embedsignature=False

from cpython cimport bool

include "modest/selection.pxi"
include "modest/node.pxi"
include "utils.pxi"

MAX_HTML_INPUT_SIZE = 8e+7

cdef class HTMLParser:
    """The HTML parser.

    Use this class to parse raw HTML.

    Parameters
    ----------

    html : str (unicode) or bytes
    detect_encoding : bool, default True
        If `True` and html type is `bytes` then encoding will be detected automatically.
    use_meta_tags : bool, default True
        Whether to use meta tags in encoding detection process.
    decode_errors : str, default 'ignore'
        Same as in builtin's str.decode, i.e 'strict', 'ignore' or 'replace'.
    """
    def __init__(self, html, detect_encoding=True, use_meta_tags=True, decode_errors = 'ignore'):

        cdef size_t html_len
        cdef char* html_chars

        self.detect_encoding = detect_encoding
        self.use_meta_tags = use_meta_tags
        self.decode_errors = decode_errors
        self._encoding = MyENCODING_UTF_8

        bytes_html, html_len = preprocess_input(html, decode_errors)
        html_chars = <char*> bytes_html

        if detect_encoding:
            self._detect_encoding(html_chars, html_len)

        self._parse_html(html_chars, html_len)

        self.raw_html = bytes_html
        self.cached_script_texts = None
        self.cached_script_srcs = None

    def css(self, str query):
        """A CSS selector.

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

        node = Node()
        node._init(self.html_tree.node_html, self)
        return node.css(query)

    def css_first(self, str query, default=None, strict=False):
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
        selector : `Node` object

        """

        node = Node()
        node._init(self.html_tree.node_html, self)
        return node.css_first(query, default, strict)

    cdef void _detect_encoding(self, char* html, size_t html_len) nogil:
        cdef myencoding_t encoding = MyENCODING_DEFAULT;

        if self.use_meta_tags:
            encoding = myencoding_prescan_stream_to_determine_encoding(html, html_len)
            if encoding != MyENCODING_DEFAULT and encoding != MyENCODING_NOT_DETERMINED:
                self._encoding = encoding
                return

        if not myencoding_detect_bom(html, html_len, &encoding):
            myencoding_detect(html, html_len, &encoding)

        self._encoding = encoding

    cdef _parse_html(self, char* html, size_t html_len):
        cdef myhtml_t* myhtml
        cdef mystatus_t status

        with nogil:
            myhtml = myhtml_create()
            status = myhtml_init(myhtml, MyHTML_OPTIONS_DEFAULT, 1, 0)

        if status != 0:
            raise RuntimeError("Can't init MyHTML object.")

        with nogil:
            self.html_tree = myhtml_tree_create()
            status = myhtml_tree_init(self.html_tree, myhtml)

        if status != 0:
            raise RuntimeError("Can't init MyHTML Tree object.")

        with nogil:
            status = myhtml_parse(self.html_tree, self._encoding, html, html_len)

        if status != 0:
            raise RuntimeError("Can't parse HTML:\n%s" % str(html))

        assert self.html_tree.node_html != NULL


    @property
    def input_encoding(self):
        """Return encoding of the HTML document."""
        cdef const char* encoding
        encoding = myencoding_name_by_id(self._encoding, NULL)

        if encoding != NULL:
            return encoding.decode('utf-8')
        else:
            return 'unknown'

    @property
    def root(self):
        """Returns root node."""
        if self.html_tree and self.html_tree.node_html:
            node = Node()
            node._init(self.html_tree.node_html, self)
            return node
        return None

    @property
    def head(self):
        """Returns head node."""
        cdef myhtml_tree_node_t* head
        head = myhtml_tree_get_node_head(self.html_tree)

        if head != NULL:
            node = Node()
            node._init(head, self)
            return node
        return None

    @property
    def body(self):
        """Returns document body."""
        cdef myhtml_tree_node_t* body
        body = myhtml_tree_get_node_body(self.html_tree)

        if body != NULL:
            node = Node()
            node._init(body, self)
            return node

        return None

    def tags(self, str name):
        """Returns a list of tags that match specified name.

        Parameters
        ----------
        name : str (e.g. div)

        """
        cdef myhtml_collection_t* collection = NULL
        pybyte_name = name.encode('UTF-8')
        cdef mystatus_t status = 0;

        result = list()
        collection = myhtml_get_nodes_by_name(self.html_tree, NULL, pybyte_name, len(pybyte_name), &status)

        if collection == NULL:
            return result

        if status == 0:
            for i in range(collection.length):
                node = Node()
                node._init(collection.list[i], self)
                result.append(node)

        myhtml_collection_destroy(collection)

        return result

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
        return self.body.text(deep=deep, separator=separator, strip=strip)

    def strip_tags(self, list tags, bool recursive = False):
        """Remove specified tags from the node.

        Parameters
        ----------
        tags : list of str
            List of tags to remove.
        recursive : bool, default True
            Whenever to delete all its child nodes

        Examples
        --------

        >>> tree = HTMLParser('<html><head></head><body><script></script><div>Hello world!</div></body></html>')
        >>> tags = ['head', 'style', 'script', 'xmp', 'iframe', 'noembed', 'noframes']
        >>> tree.strip_tags(tags)
        >>> tree.html
        '<html><body><div>Hello world!</div></body></html>'

        """
        cdef myhtml_collection_t* collection = NULL

        cdef mystatus_t status = 0;

        for tag in tags:
            pybyte_name = tag.encode('UTF-8')
            collection = myhtml_get_nodes_by_name(self.html_tree, NULL, pybyte_name, len(pybyte_name), &status)

            if collection == NULL:
                continue

            if status != 0:
                continue

            for i in range(collection.length):
                if recursive:
                    myhtml_node_delete_recursive(collection.list[i])
                else:
                    myhtml_node_delete(collection.list[i])

            myhtml_collection_destroy(collection)


    def unwrap_tags(self, list tags):
        """Unwraps specified tags from the HTML tree.

        Works the same as th `unwrap` method, but applied to a list of tags.

        Parameters
        ----------
        tags : list
            List of tags to remove.

        Examples
        --------

        >>> tree = HTMLParser("<div><a href="">Hello</a> <i>world</i>!</div>")
        >>> tree.head.unwrap_tags(['i','a'])
        >>> tree.head.html
        '<body><div>Hello world!</div></body>'
        """
        self.root.unwrap_tags(tags)

    @property
    def html(self):
        """Return HTML representation of the page."""
        return self.root.html

    def select(self, query=None):
        """Select nodes give a CSS selector.

        Works similarly to the the ``css`` method, but supports chained filtering and extra features.

        Parameters
        ----------
        query : str or None
            The CSS selector to use when searching for nodes.

        Returns
        -------
        selector : The `Selector` class.
        """
        cdef Node node
        node = self.root
        if node:
            return Selector(node, query)

    def any_css_matches(self, tuple selectors):
        """Returns True if any of the specified CSS selectors matches a node."""
        return self.root.any_css_matches(selectors)

    def scripts_contain(self, str query):
        """Returns True if any of the script tags contain specified text.

        Caches script tags on the first call to improve performance.

        Parameters
        ----------
        query : str
            The query to check.

        """
        return self.root.scripts_contain(query)

    def script_srcs_contain(self, tuple queries):
        """Returns True if any of the script SRCs attributes contain on of the specified text.

        Caches values on the first call to improve performance.

        Parameters
        ----------
        queries : tuple of str

        """
        return self.root.script_srcs_contain(queries)

    def css_matches(self, str selector):
        return self.root.css_matches(selector)

    @staticmethod
    cdef HTMLParser from_tree(
            myhtml_tree_t * tree, bytes raw_html, bint detect_encoding, bint use_meta_tags, str decode_errors,
            myencoding_t encoding
    ):
        obj = <HTMLParser> HTMLParser.__new__(HTMLParser)
        obj.html_tree = tree
        obj.raw_html = raw_html
        obj.detect_encoding = detect_encoding
        obj.use_meta_tags = use_meta_tags
        obj.decode_errors = decode_errors
        obj._encoding = encoding
        obj.cached_script_texts = None
        obj.cached_script_srcs = None
        return obj


    def clone(self):
        """Clone the current tree."""
        cdef myhtml_t* myhtml
        cdef mystatus_t status
        cdef myhtml_tree_t* html_tree
        cdef myhtml_tree_node_t* node

        with nogil:
            myhtml = myhtml_create()
            status = myhtml_init(myhtml, MyHTML_OPTIONS_DEFAULT, 1, 0)

        if status != 0:
            raise RuntimeError("Can't init MyHTML object.")

        with nogil:
            html_tree = myhtml_tree_create()
            status = myhtml_tree_init(html_tree, myhtml)

        if status != 0:
            raise RuntimeError("Can't init MyHTML Tree object.")

        node = myhtml_node_clone_deep(html_tree, self.html_tree.node_html)
        myhtml_tree_node_insert_root(html_tree, NULL, MyHTML_NAMESPACE_HTML)
        html_tree.node_html = node

        cls = HTMLParser.from_tree(
            html_tree,
            self.raw_html,
            self.detect_encoding,
            self.use_meta_tags,
            self.decode_errors,
            self._encoding
        )
        return cls

    def __dealloc__(self):
        cdef myhtml_t* myhtml

        if self.html_tree != NULL:
            myhtml = self.html_tree.myhtml
            myhtml_tree_destroy(self.html_tree)
            if myhtml != NULL:
                myhtml_destroy(myhtml)

    def __repr__(self):
        return '<HTMLParser chars=%s>' % len(self.root.html)
