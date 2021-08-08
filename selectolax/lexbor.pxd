from libc.stdint cimport uint32_t, uint8_t, uintptr_t


cdef extern from "lexbor/core/core.h" nogil:
    ctypedef uint32_t lxb_codepoint_t
    ctypedef unsigned char lxb_char_t
    ctypedef unsigned int lxb_status_t
    lexbor_str_t* lexbor_str_destroy(lexbor_str_t *str, lexbor_mraw_t *mraw, bint destroy_obj)
    lexbor_str_t* lexbor_str_create()


cdef extern from "lexbor/html/html.h" nogil:
    ctypedef unsigned int lxb_html_document_opt_t

    ctypedef struct lxb_html_tokenizer_t
    ctypedef struct lxb_html_form_element_t
    ctypedef struct lxb_html_head_element_t
    ctypedef struct lxb_html_body_element_t
    ctypedef struct lxb_dom_element_t
    ctypedef struct lexbor_mraw_t
    ctypedef struct lexbor_hash_t
    ctypedef struct lxb_dom_document_type_t
    ctypedef void lxb_dom_interface_t
    ctypedef uintptr_t lxb_tag_id_t
    ctypedef uintptr_t lxb_ns_id_t
    ctypedef lxb_dom_interface_t *(*lxb_dom_interface_destroy_f)(lxb_dom_interface_t *intrfc)
    ctypedef lxb_dom_interface_t *(*lxb_dom_interface_create_f)(lxb_dom_document_t *document, lxb_tag_id_t tag_id,
                                                                lxb_ns_id_t ns)

    ctypedef struct lxb_dom_event_target_t:
        void *events

    ctypedef struct lexbor_str_t:
        lxb_char_t *data;
        size_t     length;


    ctypedef struct lxb_dom_node_t:
        lxb_dom_event_target_t event_target
    
    
        uintptr_t              local_name
        uintptr_t              prefix
        uintptr_t              ns
    
        lxb_dom_document_t     *owner_document
    
        lxb_dom_node_t         *next
        lxb_dom_node_t         *prev
        lxb_dom_node_t         *parent
        lxb_dom_node_t         *first_child
        lxb_dom_node_t         *last_child
        void                   *user
    
        lxb_dom_node_type_t    type


    ctypedef struct lxb_dom_document_t:
        lxb_dom_node_t              node

        lxb_dom_document_cmode_t    compat_mode
        lxb_dom_document_dtype_t    type

        lxb_dom_document_type_t *doctype
        lxb_dom_element_t *element

        lxb_dom_interface_create_f  create_interface
        lxb_dom_interface_destroy_f destroy_interface

        lexbor_mraw_t *mraw
        lexbor_mraw_t *text
        lexbor_hash_t *tags
        lexbor_hash_t *attrs
        lexbor_hash_t *prefix
        lexbor_hash_t *ns
        void *parser
        void *user

        bint                        tags_inherited
        bint                        ns_inherited

        bint                        scripting


    ctypedef  struct lxb_html_document_t:
        lxb_dom_document_t dom_document

        void *iframe_srcdoc

        lxb_html_head_element_t *head
        lxb_html_body_element_t *body
        lxb_html_document_ready_state_t ready_state
        lxb_html_document_opt_t         opt

    ctypedef  enum lxb_html_document_ready_state_t:
        LXB_HTML_DOCUMENT_READY_STATE_UNDEF       = 0x00
        LXB_HTML_DOCUMENT_READY_STATE_LOADING     = 0x01
        LXB_HTML_DOCUMENT_READY_STATE_INTERACTIVE = 0x02
        LXB_HTML_DOCUMENT_READY_STATE_COMPLETE    = 0x03

    ctypedef enum lxb_html_parser_state_t:
        LXB_HTML_PARSER_STATE_BEGIN            = 0x00
        LXB_HTML_PARSER_STATE_PROCESS          = 0x01
        LXB_HTML_PARSER_STATE_END              = 0x02
        LXB_HTML_PARSER_STATE_FRAGMENT_PROCESS = 0x03
        LXB_HTML_PARSER_STATE_ERROR            = 0x04


    ctypedef enum lxb_dom_node_type_t:
        LXB_DOM_NODE_TYPE_ELEMENT                = 0x01
        LXB_DOM_NODE_TYPE_ATTRIBUTE              = 0x02
        LXB_DOM_NODE_TYPE_TEXT                   = 0x03
        LXB_DOM_NODE_TYPE_CDATA_SECTION          = 0x04
        LXB_DOM_NODE_TYPE_ENTITY_REFERENCE       = 0x05
        LXB_DOM_NODE_TYPE_ENTITY                 = 0x06
        LXB_DOM_NODE_TYPE_PROCESSING_INSTRUCTION = 0x07
        LXB_DOM_NODE_TYPE_COMMENT                = 0x08
        LXB_DOM_NODE_TYPE_DOCUMENT               = 0x09
        LXB_DOM_NODE_TYPE_DOCUMENT_TYPE          = 0x0A
        LXB_DOM_NODE_TYPE_DOCUMENT_FRAGMENT      = 0x0B
        LXB_DOM_NODE_TYPE_NOTATION               = 0x0C
        LXB_DOM_NODE_TYPE_LAST_ENTRY             = 0x0D

    ctypedef enum lxb_dom_document_cmode_t:
        LXB_DOM_DOCUMENT_CMODE_NO_QUIRKS = 0x00
        LXB_DOM_DOCUMENT_CMODE_QUIRKS = 0x01
        LXB_DOM_DOCUMENT_CMODE_LIMITED_QUIRKS = 0x02

    ctypedef enum lxb_dom_document_dtype_t:
        LXB_DOM_DOCUMENT_DTYPE_UNDEF = 0x00,
        LXB_DOM_DOCUMENT_DTYPE_HTML = 0x01,
        LXB_DOM_DOCUMENT_DTYPE_XML = 0x02

    ctypedef enum lxb_html_serialize_opt_t:
        LXB_HTML_SERIALIZE_OPT_UNDEF = 0x00
        LXB_HTML_SERIALIZE_OPT_SKIP_WS_NODES = 0x01
        LXB_HTML_SERIALIZE_OPT_SKIP_COMMENT = 0x02
        LXB_HTML_SERIALIZE_OPT_RAW = 0x04
        LXB_HTML_SERIALIZE_OPT_WITHOUT_CLOSING = 0x08
        LXB_HTML_SERIALIZE_OPT_TAG_WITH_NS = 0x10
        LXB_HTML_SERIALIZE_OPT_WITHOUT_TEXT_INDENT = 0x20
        LXB_HTML_SERIALIZE_OPT_FULL_DOCTYPE = 0x40

    ctypedef struct lexbor_array_t:
        void **list
        size_t size
        size_t length

    ctypedef struct lexbor_array_obj_t:
        uint8_t *list
        size_t  size
        size_t  length
        size_t  struct_size


    ctypedef struct lxb_html_tree_pending_table_t
    ctypedef bint lxb_html_tree_insertion_mode_f;
    ctypedef lxb_status_t lxb_html_tree_append_attr_f;

    ctypedef struct lxb_html_tree_t:

        lxb_html_tokenizer_t *tkz_ref

        lxb_html_document_t *document
        lxb_dom_node_t *fragment

        lxb_html_form_element_t *form

        lexbor_array_t *open_elements;
        lexbor_array_t *active_formatting;
        lexbor_array_obj_t *template_insertion_modes;

        lxb_html_tree_pending_table_t *pending_table;

        lexbor_array_obj_t *parse_errors;

        bint foster_parenting
        bint frameset_ok
        bint scripting

        lxb_html_tree_insertion_mode_f mode
        lxb_html_tree_insertion_mode_f original_mode
        lxb_html_tree_append_attr_f    before_append_attr

        lxb_status_t status

        size_t ref_count

    ctypedef struct lxb_html_parser_t:
        lxb_html_tokenizer_t *tkz
        lxb_html_tree_t *tree
        lxb_html_tree_t *original_tree

        lxb_dom_node_t *root
        lxb_dom_node_t *form

        lxb_html_parser_state_t state
        lxb_status_t status

        size_t  ref_count

    # Functions
    lxb_html_document_t * lxb_html_document_create()
    lxb_status_t lxb_html_document_parse(lxb_html_document_t *document,  const lxb_char_t *html, size_t size)
    lxb_html_body_element_t * lxb_html_document_body_element_noi(lxb_html_document_t *document)
    lxb_dom_element_t * lxb_dom_document_element(lxb_dom_document_t *document)

    lxb_status_t lxb_html_serialize_tree_str(lxb_dom_node_t *node, lexbor_str_t *str)

cdef class LexborHTMLParser:
    cdef lxb_html_document_t *document
    cdef public bytes raw_html
    cdef _parse_html(self, char* html, size_t html_len)


cdef extern from "lexbor/dom/dom.h" nogil:
    lxb_dom_collection_t * lxb_dom_collection_make(lxb_dom_document_t *document, size_t start_list_size)
    lxb_char_t * lxb_dom_node_text_content(lxb_dom_node_t *node, size_t *len)
    void * lxb_dom_document_destroy_text_noi(lxb_dom_document_t *document, lxb_char_t *text)

    ctypedef struct lxb_dom_collection_t:
        lexbor_array_t     array
        lxb_dom_document_t *document


cdef extern from "lexbor/dom/interfaces/element.h" nogil:
    lxb_status_t lxb_dom_elements_by_tag_name(lxb_dom_element_t *root, lxb_dom_collection_t *collection,
                                              const lxb_char_t *qualified_name, size_t len)


cdef extern from "lexbor/dom/interfaces/document.h" nogil:
    lxb_html_document_t * lxb_html_document_destroy(lxb_html_document_t *document)


cdef extern from "lexbor/dom/collection.h" nogil:
    size_t lxb_dom_collection_length_noi(lxb_dom_collection_t *col)

    lxb_dom_element_t * lxb_dom_collection_element_noi(lxb_dom_collection_t *col, size_t idx)
    lxb_dom_collection_t * lxb_dom_collection_destroy(lxb_dom_collection_t *col, bint self_destroy)
