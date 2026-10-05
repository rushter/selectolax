from inspect import cleandoc


def clean_doc(text: str) -> str:
    return f"{cleandoc(text)}\n"


def _top_level_nodes(parser):
    """The fragment's top-level nodes, reached the way the library reaches them."""
    node = parser.root
    while node is not None:
        yield node
        node = node.next
