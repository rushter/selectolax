
#todo: split into different extern blocks

cdef extern from "mycss/mycss.h" nogil:
    ctypedef unsigned int mystatus_t

    ctypedef struct mycss_entry_t
    ctypedef struct mycss_t
    ctypedef struct mycss_selectors_t

    ctypedef struct mycss_selectors_entries_list_t
    ctypedef struct mycss_declaration_entry_t

    ctypedef enum mycss_selectors_flags_t:
        MyCSS_SELECTORS_FLAGS_UNDEF         = 0x00
        MyCSS_SELECTORS_FLAGS_SELECTOR_BAD  = 0x01

    ctypedef struct mycss_selectors_list_t:
        mycss_selectors_entries_list_t* entries_list;
        size_t entries_list_length;

        mycss_declaration_entry_t* declaration_entry;

        mycss_selectors_flags_t flags;

        mycss_selectors_list_t* parent;
        mycss_selectors_list_t* next;
        mycss_selectors_list_t* prev;

    # CSS init routines
    mycss_t * mycss_create()
    mystatus_t mycss_init(mycss_t* mycss)
    mycss_entry_t * mycss_entry_create()
    mystatus_t mycss_entry_init(mycss_t* mycss, mycss_entry_t* entry)

    mycss_selectors_list_t * mycss_selectors_parse(mycss_selectors_t* selectors, myencoding_t encoding,
                                                   const char* data, size_t data_size, mystatus_t* out_status)
    mycss_selectors_t * mycss_entry_selectors(mycss_entry_t* entry)

cdef extern from "myhtml/myhtml.h" nogil:

    ctypedef struct myhtml_t
    ctypedef size_t myhtml_tag_id_t
    ctypedef struct myhtml_tree_t
    ctypedef struct mchar_async_t

    ctypedef struct mycore_string_t:
        char*  data
        size_t size
        size_t length

        mchar_async_t *mchar
        size_t node_idx

    ctypedef struct mycore_string_raw_t:
        char*  data
        size_t size
        size_t length

        myhtml_namespace ns

    ctypedef enum myhtml_options:
        MyHTML_OPTIONS_DEFAULT                 = 0x00
        MyHTML_OPTIONS_PARSE_MODE_SINGLE       = 0x01
        MyHTML_OPTIONS_PARSE_MODE_ALL_IN_ONE   = 0x02
        MyHTML_OPTIONS_PARSE_MODE_SEPARATELY   = 0x04

    ctypedef struct myhtml_collection_t:
        myhtml_tree_node_t **list;
        size_t size;
        size_t length;

    ctypedef  struct myhtml_tree_node_t:
        myhtml_tree_node_flags flags

        myhtml_tag_id_t tag_id
        myhtml_namespace ns

        myhtml_tree_node_t* prev
        myhtml_tree_node_t* next
        myhtml_tree_node_t* child
        myhtml_tree_node_t* parent

        myhtml_tree_node_t* last_child

        myhtml_token_node_t* token
        void* data

        myhtml_tree_t* tree

    ctypedef enum myhtml_namespace:
        MyHTML_NAMESPACE_UNDEF      = 0x00
        MyHTML_NAMESPACE_HTML       = 0x01
        MyHTML_NAMESPACE_MATHML     = 0x02
        MyHTML_NAMESPACE_SVG        = 0x03
        MyHTML_NAMESPACE_XLINK      = 0x04
        MyHTML_NAMESPACE_XML        = 0x05
        MyHTML_NAMESPACE_XMLNS      = 0x06
        MyHTML_NAMESPACE_ANY        = 0x07
        MyHTML_NAMESPACE_LAST_ENTRY = 0x07

    ctypedef enum myhtml_tree_node_flags:
        MyHTML_TREE_NODE_UNDEF           = 0
        MyHTML_TREE_NODE_PARSER_INSERTED = 1
        MyHTML_TREE_NODE_BLOCKING        = 2

    ctypedef enum myhtml_token_type:
        MyHTML_TOKEN_TYPE_OPEN             = 0x000
        MyHTML_TOKEN_TYPE_CLOSE            = 0x001
        MyHTML_TOKEN_TYPE_CLOSE_SELF       = 0x002
        MyHTML_TOKEN_TYPE_DONE             = 0x004
        MyHTML_TOKEN_TYPE_WHITESPACE       = 0x008
        MyHTML_TOKEN_TYPE_RCDATA           = 0x010
        MyHTML_TOKEN_TYPE_RAWTEXT          = 0x020
        MyHTML_TOKEN_TYPE_SCRIPT           = 0x040
        MyHTML_TOKEN_TYPE_PLAINTEXT        = 0x080
        MyHTML_TOKEN_TYPE_CDATA            = 0x100
        MyHTML_TOKEN_TYPE_DATA             = 0x200
        MyHTML_TOKEN_TYPE_COMMENT          = 0x400
        MyHTML_TOKEN_TYPE_NULL             = 0x800

    ctypedef enum mycss_selectors_flags:
        MyCSS_SELECTORS_FLAGS_UNDEF         = 0x00
        MyCSS_SELECTORS_FLAGS_SELECTOR_BAD  = 0x01

    ctypedef  struct myhtml_token_node_t:
        myhtml_tag_id_t tag_id

        mycore_string_t str

        size_t raw_begin
        size_t raw_length

        size_t element_begin
        size_t element_length

        myhtml_token_attr_t* attr_first
        myhtml_token_attr_t* attr_last

        myhtml_token_type type

    ctypedef struct myhtml_token_attr_t:
        myhtml_token_attr_t* next
        myhtml_token_attr_t* prev

        mycore_string_t key
        mycore_string_t value

        size_t raw_key_begin
        size_t raw_key_length
        size_t raw_value_begin
        size_t raw_value_length

        myhtml_namespace ns

    ctypedef struct myhtml_tree_attr_t:
        myhtml_tree_attr_t* next
        myhtml_tree_attr_t* prev

        mycore_string_t key
        mycore_string_t value

        size_t raw_key_begin
        size_t raw_key_length
        size_t raw_value_begin
        size_t raw_value_length

    ctypedef enum myencoding_t:
        MyENCODING_DEFAULT        = 0x00
        # MyENCODING_AUTO           = 0x01  // future
        MyENCODING_NOT_DETERMINED = 0x02
        MyENCODING_UTF_8          = 0x00  # default encoding
        MyENCODING_UTF_16LE       = 0x04
        MyENCODING_UTF_16BE       = 0x05
        MyENCODING_X_USER_DEFINED = 0x06
        MyENCODING_BIG5           = 0x07
        MyENCODING_EUC_JP         = 0x08
        MyENCODING_EUC_KR         = 0x09
        MyENCODING_GB18030        = 0x0a
        MyENCODING_GBK            = 0x0b
        MyENCODING_IBM866         = 0x0c
        MyENCODING_ISO_2022_JP    = 0x0d
        MyENCODING_ISO_8859_10    = 0x0e
        MyENCODING_ISO_8859_13    = 0x0f
        MyENCODING_ISO_8859_14    = 0x10
        MyENCODING_ISO_8859_15    = 0x11
        MyENCODING_ISO_8859_16    = 0x12
        MyENCODING_ISO_8859_2     = 0x13
        MyENCODING_ISO_8859_3     = 0x14
        MyENCODING_ISO_8859_4     = 0x15
        MyENCODING_ISO_8859_5     = 0x16
        MyENCODING_ISO_8859_6     = 0x17
        MyENCODING_ISO_8859_7     = 0x18
        MyENCODING_ISO_8859_8     = 0x19
        MyENCODING_ISO_8859_8_I   = 0x1a
        MyENCODING_KOI8_R         = 0x1b
        MyENCODING_KOI8_U         = 0x1c
        MyENCODING_MACINTOSH      = 0x1d
        MyENCODING_SHIFT_JIS      = 0x1e
        MyENCODING_WINDOWS_1250   = 0x1f
        MyENCODING_WINDOWS_1251   = 0x20
        MyENCODING_WINDOWS_1252   = 0x21
        MyENCODING_WINDOWS_1253   = 0x22
        MyENCODING_WINDOWS_1254   = 0x23
        MyENCODING_WINDOWS_1255   = 0x24
        MyENCODING_WINDOWS_1256   = 0x25
        MyENCODING_WINDOWS_1257   = 0x26
        MyENCODING_WINDOWS_1258   = 0x27
        MyENCODING_WINDOWS_874    = 0x28
        MyENCODING_X_MAC_CYRILLIC = 0x29
        MyENCODING_LAST_ENTRY     = 0x2a

    myhtml_t * myhtml_create()
    mystatus_t myhtml_init(myhtml_t* myhtml, myhtml_options opt, size_t thread_count, size_t queue_size)


    myhtml_tree_t * myhtml_tree_create()
    mystatus_t myhtml_tree_init(myhtml_tree_t* tree, myhtml_t* myhtml)

    mystatus_t myhtml_parse(myhtml_tree_t* tree, myencoding_t encoding, const char* html, size_t html_size)


cdef extern from "helper.h" nogil:

    ctypedef struct modest_finder_t



    modest_finder_t* modest_finder_create_simple()
    myhtml_tree_node_t* get_html_node(myhtml_tree_t* html_tree)
    mystatus_t modest_finder_by_selectors_list(modest_finder_t* finder, myhtml_tree_node_t* scope_node,
                                                mycss_selectors_list_t* selector_list, myhtml_collection_t** collection)



    myhtml_collection_t* myhtml_collection_destroy(myhtml_collection_t* collection)
    void destroy_selector(modest_finder_t* finder, myhtml_tree_t* html_tree, mycss_entry_t* css_entry,
                          mycss_selectors_list_t* selectors_list, myhtml_collection_t* collection)

    myhtml_tree_attr_t* myhtml_node_attribute_first(myhtml_tree_node_t* node)
    const char* myhtml_node_text(myhtml_tree_node_t *node, size_t *length)
    mycore_string_t * myhtml_node_string(myhtml_tree_node_t *node)
    const char * myhtml_tag_name_by_id(myhtml_tree_t* tree, myhtml_tag_id_t tag_id, size_t *length)
    const char* get_tag(myhtml_tree_node_t* node)
    mystatus_t myhtml_serialization(myhtml_tree_node_t* scope_node, mycore_string_raw_t* str)


