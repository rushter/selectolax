"""Removed Modest backend."""

DEPRECATION_MESSAGE = (
    "Modest backend is deprecated since selectolax 1.0. "
    "It's outdated, not maintained, contains bugs and does not follow modern HTML5 standards. "
    "Please use lexbor backend instead: "
    "`from selectolax.lexbor import LexborHTMLParser`."
)

raise ImportError(DEPRECATION_MESSAGE)
