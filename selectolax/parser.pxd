# cython: boundscheck=False, wraparound=False, nonecheck=False, language_level=3, embedsignature=True

cdef extern from "myhtml/myhtml.h" nogil:
    ctypedef unsigned int mystatus_t
    ctypedef struct myhtml_t
    ctypedef size_t myhtml_tag_id_t

    ctypedef struct myhtml_tree_t:
        # not completed struct
        myhtml_t* myhtml
        myhtml_tree_node_t*   document
        myhtml_tree_node_t*   node_html

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


    ctypedef enum myhtml_tags:
        MyHTML_TAG__UNDEF              = 0x000
        MyHTML_TAG__TEXT               = 0x001
        MyHTML_TAG__COMMENT            = 0x002
        MyHTML_TAG__DOCTYPE            = 0x003
        MyHTML_TAG_A                   = 0x004
        MyHTML_TAG_ABBR                = 0x005
        MyHTML_TAG_ACRONYM             = 0x006
        MyHTML_TAG_ADDRESS             = 0x007
        MyHTML_TAG_ANNOTATION_XML      = 0x008
        MyHTML_TAG_APPLET              = 0x009
        MyHTML_TAG_AREA                = 0x00a
        MyHTML_TAG_ARTICLE             = 0x00b
        MyHTML_TAG_ASIDE               = 0x00c
        MyHTML_TAG_AUDIO               = 0x00d
        MyHTML_TAG_B                   = 0x00e
        MyHTML_TAG_BASE                = 0x00f
        MyHTML_TAG_BASEFONT            = 0x010
        MyHTML_TAG_BDI                 = 0x011
        MyHTML_TAG_BDO                 = 0x012
        MyHTML_TAG_BGSOUND             = 0x013
        MyHTML_TAG_BIG                 = 0x014
        MyHTML_TAG_BLINK               = 0x015
        MyHTML_TAG_BLOCKQUOTE          = 0x016
        MyHTML_TAG_BODY                = 0x017
        MyHTML_TAG_BR                  = 0x018
        MyHTML_TAG_BUTTON              = 0x019
        MyHTML_TAG_CANVAS              = 0x01a
        MyHTML_TAG_CAPTION             = 0x01b
        MyHTML_TAG_CENTER              = 0x01c
        MyHTML_TAG_CITE                = 0x01d
        MyHTML_TAG_CODE                = 0x01e
        MyHTML_TAG_COL                 = 0x01f
        MyHTML_TAG_COLGROUP            = 0x020
        MyHTML_TAG_COMMAND             = 0x021
        MyHTML_TAG_COMMENT             = 0x022
        MyHTML_TAG_DATALIST            = 0x023
        MyHTML_TAG_DD                  = 0x024
        MyHTML_TAG_DEL                 = 0x025
        MyHTML_TAG_DETAILS             = 0x026
        MyHTML_TAG_DFN                 = 0x027
        MyHTML_TAG_DIALOG              = 0x028
        MyHTML_TAG_DIR                 = 0x029
        MyHTML_TAG_DIV                 = 0x02a
        MyHTML_TAG_DL                  = 0x02b
        MyHTML_TAG_DT                  = 0x02c
        MyHTML_TAG_EM                  = 0x02d
        MyHTML_TAG_EMBED               = 0x02e
        MyHTML_TAG_FIELDSET            = 0x02f
        MyHTML_TAG_FIGCAPTION          = 0x030
        MyHTML_TAG_FIGURE              = 0x031
        MyHTML_TAG_FONT                = 0x032
        MyHTML_TAG_FOOTER              = 0x033
        MyHTML_TAG_FORM                = 0x034
        MyHTML_TAG_FRAME               = 0x035
        MyHTML_TAG_FRAMESET            = 0x036
        MyHTML_TAG_H1                  = 0x037
        MyHTML_TAG_H2                  = 0x038
        MyHTML_TAG_H3                  = 0x039
        MyHTML_TAG_H4                  = 0x03a
        MyHTML_TAG_H5                  = 0x03b
        MyHTML_TAG_H6                  = 0x03c
        MyHTML_TAG_HEAD                = 0x03d
        MyHTML_TAG_HEADER              = 0x03e
        MyHTML_TAG_HGROUP              = 0x03f
        MyHTML_TAG_HR                  = 0x040
        MyHTML_TAG_HTML                = 0x041
        MyHTML_TAG_I                   = 0x042
        MyHTML_TAG_IFRAME              = 0x043
        MyHTML_TAG_IMAGE               = 0x044
        MyHTML_TAG_IMG                 = 0x045
        MyHTML_TAG_INPUT               = 0x046
        MyHTML_TAG_INS                 = 0x047
        MyHTML_TAG_ISINDEX             = 0x048
        MyHTML_TAG_KBD                 = 0x049
        MyHTML_TAG_KEYGEN              = 0x04a
        MyHTML_TAG_LABEL               = 0x04b
        MyHTML_TAG_LEGEND              = 0x04c
        MyHTML_TAG_LI                  = 0x04d
        MyHTML_TAG_LINK                = 0x04e
        MyHTML_TAG_LISTING             = 0x04f
        MyHTML_TAG_MAIN                = 0x050
        MyHTML_TAG_MAP                 = 0x051
        MyHTML_TAG_MARK                = 0x052
        MyHTML_TAG_MARQUEE             = 0x053
        MyHTML_TAG_MENU                = 0x054
        MyHTML_TAG_MENUITEM            = 0x055
        MyHTML_TAG_META                = 0x056
        MyHTML_TAG_METER               = 0x057
        MyHTML_TAG_MTEXT               = 0x058
        MyHTML_TAG_NAV                 = 0x059
        MyHTML_TAG_NOBR                = 0x05a
        MyHTML_TAG_NOEMBED             = 0x05b
        MyHTML_TAG_NOFRAMES            = 0x05c
        MyHTML_TAG_NOSCRIPT            = 0x05d
        MyHTML_TAG_OBJECT              = 0x05e
        MyHTML_TAG_OL                  = 0x05f
        MyHTML_TAG_OPTGROUP            = 0x060
        MyHTML_TAG_OPTION              = 0x061
        MyHTML_TAG_OUTPUT              = 0x062
        MyHTML_TAG_P                   = 0x063
        MyHTML_TAG_PARAM               = 0x064
        MyHTML_TAG_PLAINTEXT           = 0x065
        MyHTML_TAG_PRE                 = 0x066
        MyHTML_TAG_PROGRESS            = 0x067
        MyHTML_TAG_Q                   = 0x068
        MyHTML_TAG_RB                  = 0x069
        MyHTML_TAG_RP                  = 0x06a
        MyHTML_TAG_RT                  = 0x06b
        MyHTML_TAG_RTC                 = 0x06c
        MyHTML_TAG_RUBY                = 0x06d
        MyHTML_TAG_S                   = 0x06e
        MyHTML_TAG_SAMP                = 0x06f
        MyHTML_TAG_SCRIPT              = 0x070
        MyHTML_TAG_SECTION             = 0x071
        MyHTML_TAG_SELECT              = 0x072
        MyHTML_TAG_SMALL               = 0x073
        MyHTML_TAG_SOURCE              = 0x074
        MyHTML_TAG_SPAN                = 0x075
        MyHTML_TAG_STRIKE              = 0x076
        MyHTML_TAG_STRONG              = 0x077
        MyHTML_TAG_STYLE               = 0x078
        MyHTML_TAG_SUB                 = 0x079
        MyHTML_TAG_SUMMARY             = 0x07a
        MyHTML_TAG_SUP                 = 0x07b
        MyHTML_TAG_SVG                 = 0x07c
        MyHTML_TAG_TABLE               = 0x07d
        MyHTML_TAG_TBODY               = 0x07e
        MyHTML_TAG_TD                  = 0x07f
        MyHTML_TAG_TEMPLATE            = 0x080
        MyHTML_TAG_TEXTAREA            = 0x081
        MyHTML_TAG_TFOOT               = 0x082
        MyHTML_TAG_TH                  = 0x083
        MyHTML_TAG_THEAD               = 0x084
        MyHTML_TAG_TIME                = 0x085
        MyHTML_TAG_TITLE               = 0x086
        MyHTML_TAG_TR                  = 0x087
        MyHTML_TAG_TRACK               = 0x088
        MyHTML_TAG_TT                  = 0x089
        MyHTML_TAG_U                   = 0x08a
        MyHTML_TAG_UL                  = 0x08b
        MyHTML_TAG_VAR                 = 0x08c
        MyHTML_TAG_VIDEO               = 0x08d
        MyHTML_TAG_WBR                 = 0x08e
        MyHTML_TAG_XMP                 = 0x08f
        MyHTML_TAG_ALTGLYPH            = 0x090
        MyHTML_TAG_ALTGLYPHDEF         = 0x091
        MyHTML_TAG_ALTGLYPHITEM        = 0x092
        MyHTML_TAG_ANIMATE             = 0x093
        MyHTML_TAG_ANIMATECOLOR        = 0x094
        MyHTML_TAG_ANIMATEMOTION       = 0x095
        MyHTML_TAG_ANIMATETRANSFORM    = 0x096
        MyHTML_TAG_CIRCLE              = 0x097
        MyHTML_TAG_CLIPPATH            = 0x098
        MyHTML_TAG_COLOR_PROFILE       = 0x099
        MyHTML_TAG_CURSOR              = 0x09a
        MyHTML_TAG_DEFS                = 0x09b
        MyHTML_TAG_DESC                = 0x09c
        MyHTML_TAG_ELLIPSE             = 0x09d
        MyHTML_TAG_FEBLEND             = 0x09e
        MyHTML_TAG_FECOLORMATRIX       = 0x09f
        MyHTML_TAG_FECOMPONENTTRANSFER = 0x0a0
        MyHTML_TAG_FECOMPOSITE         = 0x0a1
        MyHTML_TAG_FECONVOLVEMATRIX    = 0x0a2
        MyHTML_TAG_FEDIFFUSELIGHTING   = 0x0a3
        MyHTML_TAG_FEDISPLACEMENTMAP   = 0x0a4
        MyHTML_TAG_FEDISTANTLIGHT      = 0x0a5
        MyHTML_TAG_FEDROPSHADOW        = 0x0a6
        MyHTML_TAG_FEFLOOD             = 0x0a7
        MyHTML_TAG_FEFUNCA             = 0x0a8
        MyHTML_TAG_FEFUNCB             = 0x0a9
        MyHTML_TAG_FEFUNCG             = 0x0aa
        MyHTML_TAG_FEFUNCR             = 0x0ab
        MyHTML_TAG_FEGAUSSIANBLUR      = 0x0ac
        MyHTML_TAG_FEIMAGE             = 0x0ad
        MyHTML_TAG_FEMERGE             = 0x0ae
        MyHTML_TAG_FEMERGENODE         = 0x0af
        MyHTML_TAG_FEMORPHOLOGY        = 0x0b0
        MyHTML_TAG_FEOFFSET            = 0x0b1
        MyHTML_TAG_FEPOINTLIGHT        = 0x0b2
        MyHTML_TAG_FESPECULARLIGHTING  = 0x0b3
        MyHTML_TAG_FESPOTLIGHT         = 0x0b4
        MyHTML_TAG_FETILE              = 0x0b5
        MyHTML_TAG_FETURBULENCE        = 0x0b6
        MyHTML_TAG_FILTER              = 0x0b7
        MyHTML_TAG_FONT_FACE           = 0x0b8
        MyHTML_TAG_FONT_FACE_FORMAT    = 0x0b9
        MyHTML_TAG_FONT_FACE_NAME      = 0x0ba
        MyHTML_TAG_FONT_FACE_SRC       = 0x0bb
        MyHTML_TAG_FONT_FACE_URI       = 0x0bc
        MyHTML_TAG_FOREIGNOBJECT       = 0x0bd
        MyHTML_TAG_G                   = 0x0be
        MyHTML_TAG_GLYPH               = 0x0bf
        MyHTML_TAG_GLYPHREF            = 0x0c0
        MyHTML_TAG_HKERN               = 0x0c1
        MyHTML_TAG_LINE                = 0x0c2
        MyHTML_TAG_LINEARGRADIENT      = 0x0c3
        MyHTML_TAG_MARKER              = 0x0c4
        MyHTML_TAG_MASK                = 0x0c5
        MyHTML_TAG_METADATA            = 0x0c6
        MyHTML_TAG_MISSING_GLYPH       = 0x0c7
        MyHTML_TAG_MPATH               = 0x0c8
        MyHTML_TAG_PATH                = 0x0c9
        MyHTML_TAG_PATTERN             = 0x0ca
        MyHTML_TAG_POLYGON             = 0x0cb
        MyHTML_TAG_POLYLINE            = 0x0cc
        MyHTML_TAG_RADIALGRADIENT      = 0x0cd
        MyHTML_TAG_RECT                = 0x0ce
        MyHTML_TAG_SET                 = 0x0cf
        MyHTML_TAG_STOP                = 0x0d0
        MyHTML_TAG_SWITCH              = 0x0d1
        MyHTML_TAG_SYMBOL              = 0x0d2
        MyHTML_TAG_TEXT                = 0x0d3
        MyHTML_TAG_TEXTPATH            = 0x0d4
        MyHTML_TAG_TREF                = 0x0d5
        MyHTML_TAG_TSPAN               = 0x0d6
        MyHTML_TAG_USE                 = 0x0d7
        MyHTML_TAG_VIEW                = 0x0d8
        MyHTML_TAG_VKERN               = 0x0d9
        MyHTML_TAG_MATH                = 0x0da
        MyHTML_TAG_MACTION             = 0x0db
        MyHTML_TAG_MALIGNGROUP         = 0x0dc
        MyHTML_TAG_MALIGNMARK          = 0x0dd
        MyHTML_TAG_MENCLOSE            = 0x0de
        MyHTML_TAG_MERROR              = 0x0df
        MyHTML_TAG_MFENCED             = 0x0e0
        MyHTML_TAG_MFRAC               = 0x0e1
        MyHTML_TAG_MGLYPH              = 0x0e2
        MyHTML_TAG_MI                  = 0x0e3
        MyHTML_TAG_MLABELEDTR          = 0x0e4
        MyHTML_TAG_MLONGDIV            = 0x0e5
        MyHTML_TAG_MMULTISCRIPTS       = 0x0e6
        MyHTML_TAG_MN                  = 0x0e7
        MyHTML_TAG_MO                  = 0x0e8
        MyHTML_TAG_MOVER               = 0x0e9
        MyHTML_TAG_MPADDED             = 0x0ea
        MyHTML_TAG_MPHANTOM            = 0x0eb
        MyHTML_TAG_MROOT               = 0x0ec
        MyHTML_TAG_MROW                = 0x0ed
        MyHTML_TAG_MS                  = 0x0ee
        MyHTML_TAG_MSCARRIES           = 0x0ef
        MyHTML_TAG_MSCARRY             = 0x0f0
        MyHTML_TAG_MSGROUP             = 0x0f1
        MyHTML_TAG_MSLINE              = 0x0f2
        MyHTML_TAG_MSPACE              = 0x0f3
        MyHTML_TAG_MSQRT               = 0x0f4
        MyHTML_TAG_MSROW               = 0x0f5
        MyHTML_TAG_MSTACK              = 0x0f6
        MyHTML_TAG_MSTYLE              = 0x0f7
        MyHTML_TAG_MSUB                = 0x0f8
        MyHTML_TAG_MSUP                = 0x0f9
        MyHTML_TAG_MSUBSUP             = 0x0fa
        MyHTML_TAG__END_OF_FILE        = 0x0fb
        MyHTML_TAG_FIRST_ENTRY         = MyHTML_TAG__TEXT
        MyHTML_TAG_LAST_ENTRY          = 0x0fc

    ctypedef enum myhtml_tree_parse_flags_t:
        MyHTML_TREE_PARSE_FLAGS_CLEAN = 0x000
        MyHTML_TREE_PARSE_FLAGS_WITHOUT_BUILD_TREE = 0x001
        MyHTML_TREE_PARSE_FLAGS_WITHOUT_PROCESS_TOKEN = 0x003
        MyHTML_TREE_PARSE_FLAGS_SKIP_WHITESPACE_TOKEN = 0x004
        MyHTML_TREE_PARSE_FLAGS_WITHOUT_DOCTYPE_IN_TREE = 0x008

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



    myhtml_t * myhtml_create()
    mystatus_t myhtml_init(myhtml_t* myhtml, myhtml_options opt, size_t thread_count, size_t queue_size)
    myhtml_tree_t * myhtml_tree_create()
    mystatus_t myhtml_tree_init(myhtml_tree_t* tree, myhtml_t* myhtml)
    mystatus_t myhtml_parse(myhtml_tree_t* tree, myencoding_t encoding, const char* html, size_t html_size)

    myhtml_tree_attr_t* myhtml_node_attribute_first(myhtml_tree_node_t* node)
    myhtml_tree_attr_t* myhtml_attribute_by_key(myhtml_tree_node_t *node, const char *key, size_t key_len)
    const char* myhtml_node_text(myhtml_tree_node_t *node, size_t *length)
    mycore_string_t * myhtml_node_string(myhtml_tree_node_t *node)
    const char * myhtml_tag_name_by_id(myhtml_tree_t* tree, myhtml_tag_id_t tag_id, size_t *length)

    myhtml_collection_t * myhtml_collection_destroy(myhtml_collection_t *collection)
    myhtml_tree_t * myhtml_tree_destroy(myhtml_tree_t* tree)
    myhtml_t* myhtml_destroy(myhtml_t* myhtml)

    myhtml_tree_node_t* myhtml_tree_get_document(myhtml_tree_t* tree)
    myhtml_tree_node_t* myhtml_tree_get_node_body(myhtml_tree_t* tree)
    myhtml_tree_node_t* myhtml_tree_get_node_head(myhtml_tree_t* tree)

    myhtml_collection_t* myhtml_get_nodes_by_name(myhtml_tree_t* tree, myhtml_collection_t *collection,
                         const char* name, size_t length, mystatus_t *status)

    void myhtml_node_delete(myhtml_tree_node_t *node)
    void myhtml_node_delete_recursive(myhtml_tree_node_t *node)
    void myhtml_tree_parse_flags_set(myhtml_tree_t* tree, myhtml_tree_parse_flags_t parse_flags)
    myhtml_tree_node_t * myhtml_node_insert_before(myhtml_tree_node_t *target, myhtml_tree_node_t *node)
    myhtml_tree_node_t * myhtml_node_insert_after(myhtml_tree_node_t *target, myhtml_tree_node_t *node)
    myhtml_tree_node_t * myhtml_node_create(myhtml_tree_t* tree, myhtml_tag_id_t tag_id, myhtml_namespace ns)
    myhtml_tree_node_t * myhtml_node_clone_deep(myhtml_tree_t* dest_tree, myhtml_tree_node_t* src)
    myhtml_tree_node_t * myhtml_node_append_child(myhtml_tree_node_t* target, myhtml_tree_node_t* node)

    mycore_string_t * myhtml_node_text_set(myhtml_tree_node_t *node, const char* text, size_t length,
                                          myencoding_t encoding)
    myhtml_tree_attr_t * myhtml_attribute_by_key(myhtml_tree_node_t *node, const char *key, size_t key_len)
    myhtml_tree_attr_t * myhtml_attribute_remove_by_key(myhtml_tree_node_t *node, const char *key, size_t key_len)
    myhtml_tree_attr_t * myhtml_attribute_add(myhtml_tree_node_t *node, const char *key, size_t key_len,
                                              const char *value, size_t value_len, myencoding_t encoding)

    myhtml_tree_node_t * myhtml_node_insert_to_appropriate_place(myhtml_tree_node_t *target, myhtml_tree_node_t *node)

cdef extern from "myhtml/tree.h" nogil:
    myhtml_tree_node_t * myhtml_tree_node_clone(myhtml_tree_node_t* node)
    myhtml_tree_node_t * myhtml_tree_node_insert_root(myhtml_tree_t* tree, myhtml_token_node_t* token,
                                                      myhtml_namespace ns)

cdef extern from "myhtml/serialization.h" nogil:
    mystatus_t myhtml_serialization(myhtml_tree_node_t* scope_node, mycore_string_raw_t* str)


cdef extern from "myencoding/encoding.h" nogil:
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

    bint myencoding_detect_bom(const char *text, size_t length, myencoding_t *encoding)
    bint myencoding_detect(const char *text, size_t length, myencoding_t *encoding)
    myencoding_t myencoding_prescan_stream_to_determine_encoding(const char *data, size_t data_size)
    const char* myencoding_name_by_id(myencoding_t encoding, size_t *length)


cdef extern from "mycss/mycss.h" nogil:
    ctypedef struct mycss_entry_t:
        # not completed struct
        mycss_t* mycss

    ctypedef struct mycss_t

    ctypedef struct mycss_selectors_t

    ctypedef struct mycss_selectors_entries_list_t
    ctypedef struct mycss_declaration_entry_t

    ctypedef enum mycss_selectors_flags:
        MyCSS_SELECTORS_FLAGS_UNDEF         = 0x00
        MyCSS_SELECTORS_FLAGS_SELECTOR_BAD  = 0x01
    ctypedef mycss_selectors_flags mycss_selectors_flags_t

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

    mycss_selectors_list_t * mycss_selectors_list_destroy(mycss_selectors_t* selectors,
                                                          mycss_selectors_list_t* selectors_list, bint self_destroy)
    mycss_entry_t * mycss_entry_destroy(mycss_entry_t* entry, bint self_destroy)
    mycss_t * mycss_destroy(mycss_t* mycss, bint self_destroy)



cdef extern from "modest/finder/finder.h" nogil:
    ctypedef struct modest_finder_t
    modest_finder_t* modest_finder_create_simple()
    mystatus_t modest_finder_by_selectors_list(modest_finder_t* finder, myhtml_tree_node_t* scope_node,
                                                mycss_selectors_list_t* selector_list, myhtml_collection_t** collection)
    modest_finder_t * modest_finder_destroy(modest_finder_t* finder, bint self_destroy)


cdef class HTMLParser:
    cdef myhtml_tree_t *html_tree
    cdef public bint detect_encoding
    cdef public bint use_meta_tags
    cdef myencoding_t _encoding
    cdef public unicode decode_errors
    cdef public bytes raw_html
    cdef object cached_script_texts
    cdef object cached_script_srcs

    cdef void _detect_encoding(self, char* html, size_t html_len) nogil
    cdef _parse_html(self, char* html, size_t html_len)
    @staticmethod
    cdef HTMLParser from_tree(
        myhtml_tree_t * tree, bytes raw_html, bint detect_encoding, bint use_meta_tags, str decode_errors,
        myencoding_t encoding
    )


cdef class Stack:
    cdef size_t capacity
    cdef size_t top
    cdef myhtml_tree_node_t ** _stack

    cdef bint is_empty(self)
    cdef push(self, myhtml_tree_node_t* res)
    cdef myhtml_tree_node_t * pop(self)
    cdef resize(self)
