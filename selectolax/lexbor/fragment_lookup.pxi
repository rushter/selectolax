cdef inline lxb_tag_id_t _fragment_tag_id_from_string(
    lxb_html_document_t *document,
    str fragment_tag,
) except? 0:
    cdef bytes fragment_tag_bytes
    cdef lxb_tag_id_t tag_id

    if not fragment_tag:
        raise ValueError("fragment_tag cannot be empty")

    fragment_tag_bytes = fragment_tag.encode("UTF-8")
    tag_id = lxb_tag_id_by_name_noi(
        document.dom_document.tags,
        <const lxb_char_t *> fragment_tag_bytes,
        len(fragment_tag_bytes),
    )
    if tag_id == LXB_TAG__UNDEF:
        raise ValueError(f"Unknown fragment tag: {fragment_tag!r}")

    return tag_id


cdef inline lxb_ns_id_t _fragment_namespace_id_from_string(
    lxb_html_document_t *document,
    str fragment_namespace,
) except? 0:
    cdef bytes fragment_namespace_bytes
    cdef const lxb_ns_prefix_data_t *prefix_data
    cdef const lxb_ns_data_t *ns_data

    if not fragment_namespace:
        raise ValueError("fragment_namespace cannot be empty")

    fragment_namespace_bytes = fragment_namespace.encode("UTF-8")

    prefix_data = lxb_ns_prefix_data_by_name(
        document.dom_document.ns,
        <const lxb_char_t *> fragment_namespace_bytes,
        len(fragment_namespace_bytes),
    )
    if prefix_data != NULL:
        return <lxb_ns_id_t> prefix_data.prefix_id

    ns_data = lxb_ns_data_by_link(
        document.dom_document.ns,
        <const lxb_char_t *> fragment_namespace_bytes,
        len(fragment_namespace_bytes),
    )
    if ns_data != NULL:
        return ns_data.ns_id

    raise ValueError(f"Unknown fragment namespace: {fragment_namespace!r}")
