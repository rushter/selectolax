#cython: boundscheck=False, wraparound=False, nonecheck=False, language_level=3

include "selector.pxi"
include "node.pxi"

cdef class HtmlParser:
    """The HTML parser.

    Use this class to parse raw HTML.

    Parameters
    ----------

    html: str (unicode) or bytes
    detect_encoding: bool, default True
        If `True` and html type is `bytes` then encoding will be detected automatically.
    use_meta_tags: bool, default True
        Whether to use meta tags in encoding detection process.

    """
    def __cinit__(self, html, detect_encoding=True, use_meta_tags=True):


        if isinstance(html, str):
            html = html.encode('UTF-8')
            self.c_html = html
            self._encoding = MyENCODING_UTF_8
        elif isinstance(html, bytes):
            self.c_html = <char *> html
            if detect_encoding:
                self._detect_encoding()

        self.detect_encoding = detect_encoding
        self.use_meta_tags = use_meta_tags
        self._parse_html(self.c_html, len(self.c_html))

    def css(self, str query):
        """A CSS selector.

        Matches pattern `query` against HTML tree.
        `CSS selectors reference <https://www.w3schools.com/cssref/css_selectors.asp>`_.

        Parameters
        ----------
        query: str
            CSS selector (e.g. "div > :nth-child(2n+1):not(:has(a))").

        Returns
        -------
        selector : list of `Node` objects
    
        """
        cdef myhtml_collection_t *collection
        cdef Selector selector =  Selector(query)
        result = list()
        collection = selector.find(self.html_tree)

        for i in range(collection.length):
            node = Node()
            node._init(collection.list[i], self)
            result.append(node)

        myhtml_collection_destroy(collection)

        return result

    cpdef _detect_encoding(self):
        cdef myencoding_t encoding = MyENCODING_DEFAULT;

        if not myencoding_detect_bom(self.c_html, len(self.c_html), &encoding):
            if not myencoding_detect(self.c_html, len(self.c_html), &encoding):

                if encoding == MyENCODING_DEFAULT and self.use_meta_tags:
                    encoding = myencoding_prescan_stream_to_determine_encoding(self.c_html, len(self.c_html))
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

    cpdef _get_input_encoding(self):
        cdef const char* encoding
        encoding = myencoding_name_by_id(self._encoding, NULL)

        if encoding != NULL:
            return encoding.decode('utf-8')
        else:
            return 'unknown'

    def __dealloc__(self):
        cdef myhtml_t *myhtml = self.html_tree.myhtml
        myhtml_tree_destroy(self.html_tree)
        myhtml_destroy(myhtml)

