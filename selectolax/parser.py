"""Removed Modest backend."""

DEPRECATION_MESSAGE = (
    "Modest backend is deprecated since selectolax 1.0. "
    "The engine has not been updated since 2021, while lexbor has been available "
    "since 2021 and is actively developed. "
    "Modest is outdated, not maintained, contains bugs and does not follow modern HTML5 standards. "
    "Please use lexbor backend instead: "
    "`from selectolax.lexbor import LexborHTMLParser`. "
    "The APIs are nearly identical, so in most projects swapping the import is all that's needed."
)

raise ImportError(DEPRECATION_MESSAGE)
