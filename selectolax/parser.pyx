#cython: boundscheck=False, wraparound=False, nonecheck=False, language_level=3

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

    """
    def __init__(self, html, detect_encoding=True, use_meta_tags=True):

        self.detect_encoding = detect_encoding
        self.use_meta_tags = use_meta_tags

        if isinstance(html, (str, unicode)):
            pybyte_html = html.encode('UTF-8')
            self.c_html = pybyte_html
            self._encoding = MyENCODING_UTF_8
        elif isinstance(html, bytes):
            self.c_html = <char *> html
            if detect_encoding:
                self._detect_encoding()
        else:
            raise TypeError("Expected a string, but %s found" % type(html).__name__)


        self._parse_html(self.c_html, len(self.c_html))

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
        cdef myhtml_collection_t *collection
        cdef Selector selector = Selector(query)
        result = list()
        collection = selector.find(self.html_tree)

        for i in range(collection.length):
            node = Node()
            node._init(collection.list[i], self)
            result.append(node)

        myhtml_collection_destroy(collection)

        return result

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
        results = self.css(query)
        n_results = len(results)

        if n_results > 0:

            if strict and n_results > 1:
                raise ValueError("Expected 1 match, but found %s matches" % n_results)

            return results[0]

        return default

    cpdef _detect_encoding(self):
        cdef myencoding_t encoding = MyENCODING_DEFAULT;

        if self.use_meta_tags:
                encoding = myencoding_prescan_stream_to_determine_encoding(self.c_html, len(self.c_html))
                if encoding != MyENCODING_DEFAULT and encoding != MyENCODING_NOT_DETERMINED:
                    self._encoding = encoding
                    return

        if not myencoding_detect_bom(self.c_html, len(self.c_html), &encoding):
            myencoding_detect(self.c_html, len(self.c_html), &encoding)

        self._encoding = encoding

    cdef _parse_html(self, const char *data, size_t data_size):
        cdef myhtml_t *myhtml = myhtml_create()
        cdef mystatus_t status = myhtml_init(myhtml, MyHTML_OPTIONS_DEFAULT, 1, 0)

        if status != 0:
            raise RuntimeError("Can't init MyHTML object.")

        self.html_tree = myhtml_tree_create()
        status = myhtml_tree_init(self.html_tree, myhtml)

        if status != 0:
            raise RuntimeError("Can't init MyHTML Tree object.")

        status = myhtml_parse(self.html_tree, self._encoding, data, data_size)

        if status != 0:
            raise RuntimeError("Can't parse HTML:\n%s" % data)

    @property
    def input_encoding(self):
        cdef const char* encoding
        encoding = myencoding_name_by_id(self._encoding, NULL)

        if encoding != NULL:
            return encoding.decode('utf-8')
        else:
            return 'unknown'

    def get_root(self):
        """Returns root node."""
        cdef myhtml_tree_node_t* root
        root = myhtml_tree_get_document(self.html_tree)

        if root != NULL:
            node = Node()
            node._init(root, self)
            return node

        return None

    def get_body(self):
        """Returns document body."""
        cdef myhtml_tree_node_t* body
        body = myhtml_tree_get_node_body(self.html_tree)

        if body != NULL:
            node = Node()
            node._init(body, self)
            return node

        return None

    def __dealloc__(self):
        cdef myhtml_t *myhtml

        if self.html_tree != NULL:
            myhtml = self.html_tree.myhtml
            myhtml_tree_destroy(self.html_tree)
            myhtml_destroy(myhtml)

    def __repr__(self):
        return '<HTMLParser chars=%s>' % len(self.c_html)
