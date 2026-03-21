"""Zotlib - Extract and format bibliographic data from Zotero databases."""

__version__ = "0.4.2"

from zotlib.database import ZoteroDatabase
from zotlib.extractors import (
    extract_collections,
    extract_creators,
    extract_cv_items,
    extract_items,
    extract_libraries,
)
from zotlib.formatters.apa import format_apa_reference, format_cv_as_apa

__all__ = [
    "ZoteroDatabase",
    "extract_items",
    "extract_creators",
    "extract_collections",
    "extract_libraries",
    "extract_cv_items",
    "format_apa_reference",
    "format_cv_as_apa",
]
