import importlib.util
from typing import Any

import pytest

HAS_MODEST = importlib.util.find_spec("selectolax.parser") is not None

requires_modest = pytest.mark.skipif(
    not HAS_MODEST,
    reason="modest engine is not built",
)

HTMLParser: Any
Node: Any
create_tag: Any
parse_fragment: Any

if HAS_MODEST:
    from selectolax import parser as _modest

    HTMLParser = _modest.HTMLParser
    Node = _modest.Node
    create_tag = _modest.create_tag
    parse_fragment = _modest.parse_fragment
else:
    HTMLParser = None
    Node = None
    create_tag = None
    parse_fragment = None
