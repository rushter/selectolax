from typing import Iterator, TypeVar, Literal

DefaultT = TypeVar("DefaultT")

class _Attributes:
    @staticmethod
    def create(node: "Node", decode_errors: str) -> "_Attributes": ...
    def keys(self) -> Iterator[str]: ...
    def items(self) -> Iterator[tuple[str, str]]: ...
    def values(self) -> Iterator[str]: ...
    def get(self, key, default: DefaultT | None = None) -> str | DefaultT: ...
    def sget(self, key, default: str = "") -> str | DefaultT: ...

class Selector:
    """An advanced CSS selector that supports additional operations.

    Think of it as a toolkit that mimics some of the features of XPath.

    Please note, this is an experimental feature that can change in the future."""

    def __init__(self, node: "Node", query: str): ...
    def css(self, query: str) -> "Node":
        """Evaluate CSS selector against current scope."""
        ...
    @property
    def matches(self) -> list["Node"]:
        """Returns all possible selector matches"""
        ...
    @property
    def any_matches(self) -> bool:
        """Returns True if there are any matches"""
        ...
    def text_contains(
        self, text: str, deep: bool = True, separator: str = "", strip: bool = False
    ) -> "Selector":
        """Filter all current matches given text."""
        ...
    def any_text_contains(
        self, text: str, deep: bool = True, separator: str = "", strip: bool = False
    ) -> bool:
        """Returns True if any node in the current search scope contains specified text"""
        ...
    def attribute_long_than(
        self, text: str, length: int, start: str | None = None
    ) -> "Selector":
        """Filter all current matches by attribute length.

        Similar to string-length in XPath."""
        ...
    def any_attribute_long_than(
        self, text: str, length: int, start: str | None = None
    ) -> bool:
        """Returns True any href attribute longer than a specified length.

        Similar to string-length in XPath."""
        ...

class Node:
    @property
    def attributes(self) -> dict[str, None | str]:
        """Get all attributes that belong to the current node.

        The value of empty attributes is None."""
        ...
    @property
    def attrs(self) -> "_Attributes":
        """A dict-like object that is similar to the attributes property, but operates directly on the Node data."""
        ...
    @property
    def id(self) -> str | None:
        """Get the id attribute of the node.

        Returns None if id does not set."""
        ...

    def mem_id(self) -> int:
        """Get the mem_id of the node.

        Returns 0 if mem_id does not set."""
        ...

    def __hash__(self) -> int:
        """ Get the hash of this node
        :return: int
        """
        ...
    def text(self, deep: bool = True, separator: str = "", strip: bool = False) -> str:
        """Returns the text of the node including text of all its child nodes."""
        ...
    def iter(self, include_text: bool = False) -> Iterator["Node"]:
        """Iterate over nodes on the current level."""
        ...
    def traverse(self, include_text: bool = False) -> Iterator["Node"]:
        """Iterate over all child and next nodes starting from the current level."""
        ...
    @property
    def tag(self) -> str:
        """Return the name of the current tag (e.g. div, p, img)."""
        ...
    @property
    def child(self) -> None | "Node":
        """Return the child node."""
        ...
    @property
    def parent(self) -> None | "Node":
        """Return the parent node."""
        ...
    @property
    def next(self) -> None | "Node":
        """Return next node."""
        ...
    @property
    def prev(self) -> None | "Node":
        """Return previous node."""
        ...
    @property
    def last_child(self) -> None | "Node":
        """Return last child node."""
        ...
    @property
    def html(self) -> None | str:
        """Return HTML representation of the current node including all its child nodes."""
        ...
    def css(self, query: str) -> list["Node"]:
        """Evaluate CSS selector against current node and its child nodes."""
        ...
    def any_css_matches(self, selectors: tuple[str]) -> bool:
        """Returns True if any of CSS selectors matches a node"""
        ...
    def css_matches(self, selector: str) -> bool:
        """Returns True if CSS selector matches a node."""
        ...
    def css_first(
        self, query: str, default: DefaultT | None = None, strict: bool = False
    ) -> "Node" | DefaultT:
        """Evaluate CSS selector against current node and its child nodes."""
        ...
    def decompose(self, recursive: bool = True) -> None:
        """Remove a Node from the tree."""
        ...
    def remove(self, recursive: bool = True) -> None:
        """An alias for the decompose method."""
        ...
    def unwrap(self) -> None:
        """Replace node with whatever is inside this node."""
        ...
    def strip_tags(self, tags: list[str], recursive: bool = False) -> None:
        """Remove specified tags from the HTML tree."""
        ...
    def unwrap_tags(self, tags: list[str]) -> None:
        """Unwraps specified tags from the HTML tree.

        Works the same as the unwrap method, but applied to a list of tags."""
        ...
    def replace_with(self, value: str | bytes | None) -> None:
        """Replace current Node with specified value."""
        ...
    def insert_before(self, value: str | bytes | None) -> None:
        """Insert a node before the current Node."""
        ...
    def insert_after(self, value: str | bytes | None) -> None:
        """Insert a node after the current Node."""
        ...
    @property
    def raw_value(self) -> bytes:
        """Return the raw (unparsed, original) value of a node.

        Currently, works on text nodes only."""
        ...
    def select(self, query: str | None = None) -> "Selector":
        """Select nodes given a CSS selector.

        Works similarly to the css method, but supports chained filtering and extra features.
        """
        ...
    def scripts_contain(self, query: str) -> bool:
        """Returns True if any of the script tags contain specified text.

        Caches script tags on the first call to improve performance."""
        ...
    def script_srcs_contain(self, queries: tuple[str]) -> bool:
        """Returns True if any of the script SRCs attributes contain on of the specified text.

        Caches values on the first call to improve performance."""
        ...
    @property
    def text_content(self) -> str | None:
        """Returns the text of the node if it is a text node.

        Returns None for other nodes. Unlike the text method, does not include child nodes.
        """
        ...
    def merge_text_nodes(self):
        """Iterates over all text nodes and merges all text nodes that are close to each other.

        This is useful for text extraction."""
        ...

class HTMLParser:
    def __init__(
        self,
        html: bytes | str,
        detect_encoding: bool = True,
        use_meta_tags: bool = True,
        decode_errors: Literal["strict", "ignore", "replace"] = "ignore",
    ): ...
    def css(self, query: str) -> list["Node"]:
        """A CSS selector.

        Matches pattern query against HTML tree."""
        ...
    def css_first(
        self, query: str, default: DefaultT | None = None, strict: bool = False
    ) -> DefaultT | "Node":
        """Same as css but returns only the first match."""
        ...
    @property
    def input_encoding(self) -> str:
        """Return encoding of the HTML document.

        Returns unknown in case the encoding is not determined."""
        ...
    @property
    def root(self) -> "Node" | None:
        """Returns root node."""
        ...
    @property
    def head(self) -> "Node" | None:
        """Returns head node."""
        ...
    @property
    def body(self) -> "Node" | None:
        """Returns document body."""
        ...
    def tags(self, name: str) -> list["Node"]:
        """Returns a list of tags that match specified name."""
        ...
    def text(self, deep: bool = True, separator: str = "", strip: bool = False) -> str:
        """Returns the text of the node including text of all its child nodes."""
        ...
    def strip_tags(self, tags: list[str], recursive: bool = False) -> None: ...
    def unwrap_tags(self, tags: list[str]) -> None:
        """Unwraps specified tags from the HTML tree.

        Works the same as th unwrap method, but applied to a list of tags."""
        ...
    @property
    def html(self) -> None | str:
        """Return HTML representation of the page."""
        ...
    def select(self, query: str | None = None) -> "Selector" | None:
        """Select nodes given a CSS selector.

        Works similarly to the css method, but supports chained filtering and extra features.
        """
        ...
    def any_css_matches(self, selectors: tuple[str]) -> bool:
        """Returns True if any of the specified CSS selectors matches a node."""
        ...
    def scripts_contain(self, query: str) -> bool:
        """Returns True if any of the script tags contain specified text.

        Caches script tags on the first call to improve performance."""
        ...
    def scripts_srcs_contain(self, queries: tuple[str]) -> bool:
        """Returns True if any of the script SRCs attributes contain on of the specified text.

        Caches values on the first call to improve performance."""
        ...
    def css_matches(self, selector: str) -> bool: ...
    def clone(self) -> "HTMLParser":
        """Clone the current tree."""
        ...
    def merge_text_nodes(self):
        """Iterates over all text nodes and merges all text nodes that are close to each other.

        This is useful for text extraction."""
        ...
