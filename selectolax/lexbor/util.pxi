include "../utils.pxi"

from cpython.unicode cimport PyUnicode_DecodeUTF8

import re


cdef inline str _decode_utf8(const lxb_char_t *data, size_t length):
    # Lexbor passes bytes it cannot decode through verbatim, so every read of a
    # name, attribute or text has to substitute U+FFFD instead of raising. This is
    # the single place that policy is defined; do not decode strictly elsewhere.
    return PyUnicode_DecodeUTF8(<char *> data, length, "replace")


def create_tag(tag: str):
    """
    Given an HTML tag name, e.g. `"div"`, create a single empty node for that tag,
    e.g. `"<div></div>"`.

    Use `LexborHTMLParser().create_node(..)` if you need to create a node tied to a specific parser instance.
    """
    return LexborHTMLParser(f"<{tag}></{tag}>", is_fragment=True).root


def parse_fragment(html: str):
    """
    Removed. Use ``LexborHTMLParser(html, is_fragment=True)`` instead.

    Parameters
    ----------
    html : str

    Raises
    ------
    SelectolaxError
        Always.

    Notes
    -----
    This function guessed whether ``html`` was a whole document or a fragment by
    scanning it for ``<html>``, ``<head>`` and ``<body>``, then stripped the tags
    it considered synthetic. The guess was wrong for uppercase tags, for tags
    inside text or comments, and for content that only *looks* like a fragment.
    ``is_fragment=True`` has the parser decide, per the HTML Standard.

    Examples
    --------
    Instead of::

        for node in parse_fragment(html):
            ...

    use::

        parser = LexborHTMLParser(html, is_fragment=True)
        for node in parser.root.iter(include_text=True):
            ...
    """
    msg = (
        "parse_fragment() has been removed. "
        "Use LexborHTMLParser(html, is_fragment=True) instead: "
        "`parser.root` is the fragment root and `parser.root.iter(include_text=True)` "
        "yields its top-level nodes."
    )
    raise SelectolaxError(msg)


def extract_html_comment(text: str) -> str:
    """Extract the inner content of an HTML comment string.

    Args:
        text: Raw HTML comment, including the ``<!--`` and ``-->`` markers.

    Returns:
        The comment body with surrounding whitespace stripped.

    Raises:
        ValueError: If the input is not a well-formed HTML comment.

    Examples:
        >>> extract_html_comment("<!-- hello -->")
        'hello'
    """
    if match := re.fullmatch(r"\s*<!--\s*(.*?)\s*-->\s*", text, flags=re.DOTALL):
        return match.group(1).strip()
    msg = "Input is not a valid HTML comment"
    raise ValueError(msg)


cdef inline bint is_empty_text_node(lxb_dom_node_t *text_node) noexcept:
    """
    Check whether a node is a text node made up solely of HTML ASCII whitespace.

    Parameters
    ----------
    text_node : lxb_dom_node_t *
        Pointer to the node that should be inspected.

    Returns
    -------
    bint
        ``True`` if ``text_node`` is a text node whose character data contains
        only space, tab, newline, form feed, or carriage return characters;
        otherwise ``False``.
    """
    if text_node == NULL or text_node.type != LXB_DOM_NODE_TYPE_TEXT:
        return False

    cdef lxb_dom_character_data_t *text_character_data = <lxb_dom_character_data_t *> text_node
    cdef lexbor_str_t *text_buffer = &text_character_data.data
    cdef size_t text_length = text_buffer.length
    cdef lxb_char_t *text_bytes = text_buffer.data

    return _is_whitespace_only(text_bytes, text_length)


cdef inline bint _is_whitespace_only(const lxb_char_t *buffer, size_t buffer_length) noexcept nogil:
    """
    Determine whether a byte buffer consists only of HTML ASCII whitespace.

    Parameters
    ----------
    buffer : const lxb_char_t *
        Pointer to the buffer to inspect.
    buffer_length : size_t
        Number of bytes available in ``buffer``.

    Returns
    -------
    bint
        ``True`` if ``buffer`` is ``NULL``, empty, or contains only space
        (0x20), tab (0x09), line feed (0x0A), form feed (0x0C), or carriage
        return (0x0D) bytes; otherwise ``False``.

    Notes
    -----
    Mirrors Lexbor's ``lexbor_utils_whitespace`` macro and stays inline to
    keep the GIL released in hot loops.
    """
    cdef const lxb_char_t *cursor = buffer
    cdef const lxb_char_t *end = buffer + buffer_length
    cdef lxb_char_t current_char

    if buffer == NULL or buffer_length == 0:
        return True

    # Inline whitespace check mirroring lexbor_utils_whitespace(chr, !=, &&)
    while cursor < end:
        current_char = cursor[0]
        if (current_char != ' ' and current_char != '\t' and current_char != '\n'
                and current_char != '\f' and current_char != '\r'):
            return False
        cursor += 1

    return True
