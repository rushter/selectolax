include "../utils.pxi"

import re

def create_tag(tag: str):
    """
    Given an HTML tag name, e.g. `"div"`, create a single empty node for that tag,
    e.g. `"<div></div>"`.
    """
    return do_create_tag(tag, LexborHTMLParser)


def parse_fragment(html: str):
    """
    Given HTML, parse it into a list of Nodes, such that the nodes
    correspond to the given HTML.

    For contrast, HTMLParser adds `<html>`, `<head>`, and `<body>` tags
    if they are missing. This function does not add these tags.
    """
    return do_parse_fragment(html, LexborHTMLParser)

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
