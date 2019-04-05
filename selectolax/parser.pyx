#cython: boundscheck=False, wraparound=False, nonecheck=False, language_level=3
from cpython cimport bool

include "selector.pxi"
include "node.pxi"

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
        self._encoding = MyENCODING_UTF_8
        self.decode_errors = decode_errors

        if isinstance(html, (str, unicode)):
            bytes_html = html.encode('UTF-8')
            detect_encoding = False
        elif isinstance(html, bytes):
            bytes_html = html
        else:
            raise TypeError("Expected a string, but %s found" % type(html).__name__)

        html_len = len(bytes_html)
        html_chars = <char*>bytes_html


        if detect_encoding:
            self._detect_encoding(html_chars, html_len)

        self._parse_html(html_chars, html_len)


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
        """Same as `css` but returns only first match.
        
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
        cdef const char* encoding
        encoding = myencoding_name_by_id(self._encoding, NULL)

        if encoding != NULL:
            return encoding.decode('utf-8')
        else:
            return 'unknown'

    @property
    def root(self):
        """Returns root node."""
        cdef myhtml_tree_node_t* root
        root = myhtml_tree_get_document(self.html_tree)

        if root != NULL:
            node = Node()
            node._init(root, self)
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
        return self.body.text(deep=deep, separator=separator, strip=False)

    def strip_tags(self, list tags):
        """Remove specified tags from the node.

        Parameters
        ----------
        tags : list,
            List of tags to remove.

        Examples
        --------

        >>> tree = HTMLParser(html)
        >>> tags = ['style', 'script', 'xmp', 'iframe', 'noembed', 'noframes']
        >>> tree.strip_tags(tags)

        """

        node = Node()
        node._init(self.html_tree.node_html, self)

        for tag in tags:
            for element in node.css(tag):
                element.decompose()
        return node

    @property
    def html(self):
        return self.root.html

    def __dealloc__(self):
        cdef myhtml_t* myhtml

        if self.html_tree != NULL:
            myhtml = self.html_tree.myhtml
            myhtml_tree_destroy(self.html_tree)
            if myhtml != NULL:
                myhtml_destroy(myhtml)

    def __repr__(self):
        return '<HTMLParser chars=%s>' % len(self.root.html)
