"""Zotero SQLite database schema definitions.

Documents the tables and columns used by zotlib for extracting bibliographic data.
Based on Zotero 7 database structure.
"""

from dataclasses import dataclass


@dataclass
class Column:
    """Column definition with type and description."""

    type: str
    description: str


@dataclass
class Table:
    """Table schema definition."""

    name: str
    description: str
    columns: dict[str, Column]


# Core item tables
ITEMS = Table(
    name="items",
    description="Base table for all Zotero items (papers, books, etc.)",
    columns={
        "itemID": Column("INTEGER", "Primary key"),
        "itemTypeID": Column("INTEGER", "Foreign key to itemTypes"),
        "dateAdded": Column("TIMESTAMP", "Timestamp when item was added"),
        "dateModified": Column("TIMESTAMP", "Timestamp of last modification"),
        "clientDateModified": Column("TIMESTAMP", "Client-side modification timestamp"),
        "libraryID": Column("INTEGER", "Foreign key to libraries"),
        "key": Column("TEXT", "Unique sync key"),
        "version": Column("INTEGER", "Sync version number"),
        "synced": Column("INTEGER", "Sync status flag (0 or 1)"),
    },
)

ITEM_DATA = Table(
    name="itemData",
    description="Links items to their field values (title, date, DOI, etc.)",
    columns={
        "itemID": Column("INTEGER", "Foreign key to items"),
        "fieldID": Column("INTEGER", "Foreign key to fieldsCombined"),
        "valueID": Column("INTEGER", "Foreign key to itemDataValues"),
    },
)

ITEM_DATA_VALUES = Table(
    name="itemDataValues",
    description="Stores actual field values (deduplicated)",
    columns={
        "valueID": Column("INTEGER", "Primary key"),
        "value": Column("TEXT", "The actual field value text"),
    },
)

FIELDS_COMBINED = Table(
    name="fieldsCombined",
    description="Field definitions (title, date, DOI, volume, etc.)",
    columns={
        "fieldID": Column("INTEGER", "Primary key"),
        "fieldName": Column("TEXT", "Internal field name (e.g., 'title', 'DOI')"),
        "label": Column("TEXT", "Display label"),
        "fieldFormatID": Column("INTEGER", "Format specification"),
        "custom": Column("INTEGER", "Whether this is a custom field (0 or 1)"),
    },
)

ITEM_TYPES = Table(
    name="itemTypes",
    description="Item type definitions (journalArticle, book, etc.)",
    columns={
        "itemTypeID": Column("INTEGER", "Primary key"),
        "typeName": Column("TEXT", "Internal type name"),
        "templateItemTypeID": Column("INTEGER", "Template reference"),
        "display": Column("INTEGER", "Display order"),
    },
)

# Creator tables
ITEM_CREATORS = Table(
    name="itemCreators",
    description="Links items to their creators (authors, editors, etc.)",
    columns={
        "itemID": Column("INTEGER", "Foreign key to items"),
        "creatorID": Column("INTEGER", "Foreign key to creators"),
        "creatorTypeID": Column("INTEGER", "Type of creator (author, editor, etc.)"),
        "orderIndex": Column("INTEGER", "Position in author list"),
    },
)

CREATORS = Table(
    name="creators",
    description="Creator (person) records",
    columns={
        "creatorID": Column("INTEGER", "Primary key"),
        "firstName": Column("TEXT", "First name"),
        "lastName": Column("TEXT", "Last name"),
        "fieldMode": Column("INTEGER", "Name format mode (0=two-field, 1=single-field)"),
    },
)

# Collection tables
COLLECTION_ITEMS = Table(
    name="collectionItems",
    description="Links items to collections",
    columns={
        "collectionID": Column("INTEGER", "Foreign key to collections"),
        "itemID": Column("INTEGER", "Foreign key to items"),
        "orderIndex": Column("INTEGER", "Position in collection"),
    },
)

COLLECTIONS = Table(
    name="collections",
    description="Collection (folder) definitions",
    columns={
        "collectionID": Column("INTEGER", "Primary key"),
        "collectionName": Column("TEXT", "Display name"),
        "parentCollectionID": Column("INTEGER", "Parent collection (for nesting)"),
        "clientDateModified": Column("TIMESTAMP", "Client-side modification timestamp"),
        "libraryID": Column("INTEGER", "Foreign key to libraries"),
        "key": Column("TEXT", "Unique sync key"),
        "version": Column("INTEGER", "Sync version number"),
        "synced": Column("INTEGER", "Sync status flag (0 or 1)"),
    },
)

# Library tables
LIBRARIES = Table(
    name="libraries",
    description="Library definitions (personal, group libraries)",
    columns={
        "libraryID": Column("INTEGER", "Primary key"),
        "type": Column("TEXT", "Library type (user, group)"),
        "editable": Column("INTEGER", "Whether library is editable (0 or 1)"),
        "filesEditable": Column("INTEGER", "Whether files can be modified (0 or 1)"),
        "version": Column("INTEGER", "Sync version"),
        "storageVersion": Column("INTEGER", "Storage version"),
        "lastSync": Column("TIMESTAMP", "Last sync timestamp"),
        "archived": Column("INTEGER", "Archive status (0 or 1)"),
    },
)

# Annotation tables
ITEM_ANNOTATIONS = Table(
    name="itemAnnotations",
    description="PDF annotations created in Zotero's built-in reader",
    columns={
        "itemID": Column("INTEGER", "Primary key (the annotation item)"),
        "parentItemID": Column("INTEGER", "Foreign key to the PDF attachment item"),
        "type": Column("INTEGER", "Annotation type (1=highlight, 2=note, 3=image, 5=underline)"),
        "authorName": Column("TEXT", "Name of annotation author"),
        "text": Column("TEXT", "Highlighted or selected text"),
        "comment": Column("TEXT", "User comment on the annotation"),
        "color": Column("TEXT", "Hex color string (e.g., #ffd400)"),
        "pageLabel": Column("TEXT", "Page number label"),
        "sortIndex": Column("TEXT", "Lexicographic sort index for ordering"),
        "position": Column("TEXT", "JSON with pageIndex and rects/paths coordinates"),
        "isExternal": Column("INTEGER", "Whether annotation is external (0 or 1)"),
    },
)

# Tag tables
ITEM_TAGS = Table(
    name="itemTags",
    description="Links items to tags",
    columns={
        "itemID": Column("INTEGER", "Foreign key to items"),
        "tagID": Column("INTEGER", "Foreign key to tags"),
        "type": Column("INTEGER", "Tag type (0=manual, 1=automatic)"),
    },
)

TAGS = Table(
    name="tags",
    description="Tag definitions",
    columns={
        "tagID": Column("INTEGER", "Primary key"),
        "name": Column("TEXT", "Tag display name"),
    },
)

# All schemas for iteration
ALL_SCHEMAS = [
    ITEMS,
    ITEM_DATA,
    ITEM_DATA_VALUES,
    FIELDS_COMBINED,
    ITEM_TYPES,
    ITEM_CREATORS,
    CREATORS,
    COLLECTION_ITEMS,
    COLLECTIONS,
    LIBRARIES,
    ITEM_ANNOTATIONS,
    ITEM_TAGS,
    TAGS,
]


def get_table_names() -> list[str]:
    """Get list of table names used by zotlib."""
    return [s.name for s in ALL_SCHEMAS]


def get_schema(table_name: str) -> Table | None:
    """Get schema definition for a table."""
    for schema in ALL_SCHEMAS:
        if schema.name == table_name:
            return schema
    return None
