from inspect import cleandoc

import pytest

from selectolax.lexbor import LEXBOR_VERSION_MAJOR, LEXBOR_VERSION_MINOR

LEXBOR_VERSION = (LEXBOR_VERSION_MAJOR, LEXBOR_VERSION_MINOR)


def requires_lexbor_gt(*version):
    """Skip unless the bundled lexbor is strictly newer than ``version``.

    Accepts either ``requires_lexbor_gt(3, 1)`` or ``requires_lexbor_gt((3, 1))``.
    """
    if len(version) == 1 and isinstance(version[0], (tuple, list)):
        version = tuple(version[0])
    reason = "requires lexbor > " + ".".join(map(str, version))
    return pytest.mark.skipif(LEXBOR_VERSION <= version, reason=reason)


def clean_doc(text: str) -> str:
    return f"{cleandoc(text)}\n"


def _top_level_nodes(parser):
    """The fragment's top-level nodes, reached the way the library reaches them."""
    node = parser.root
    while node is not None:
        yield node
        node = node.next
