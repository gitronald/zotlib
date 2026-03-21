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

# Attachment tables
ITEM_ATTACHMENTS = Table(
    name="itemAttachments",
    description="PDF and file attachments linked to items",
    columns={
        "itemID": Column("INTEGER", "Primary key (the attachment item)"),
        "parentItemID": Column("INTEGER", "Foreign key to the parent item"),
        "linkMode": Column("INTEGER", "How the file is stored (0=imported, 1=linked, 2=web)"),
        "contentType": Column("TEXT", "MIME type (e.g., application/pdf)"),
        "charsetID": Column("INTEGER", "Character set for text attachments"),
        "path": Column("TEXT", "File path (storage:, attachments:, or absolute)"),
        "syncState": Column("INTEGER", "File sync status"),
        "storageModTime": Column("INTEGER", "Storage modification timestamp"),
        "storageHash": Column("TEXT", "File content hash"),
        "lastProcessedModificationTime": Column("INTEGER", "Last processing timestamp"),
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

# Note tables
ITEM_NOTES = Table(
    name="itemNotes",
    description="Rich-text notes attached to items",
    columns={
        "itemID": Column("INTEGER", "Primary key (the note item)"),
        "parentItemID": Column("INTEGER", "Foreign key to the parent item"),
        "note": Column("TEXT", "HTML note content"),
        "title": Column("TEXT", "Note title (first line of note)"),
    },
)

# Relation tables
ITEM_RELATIONS = Table(
    name="itemRelations",
    description="Relations between items (e.g., related-to, replaces)",
    columns={
        "itemID": Column("INTEGER", "Foreign key to items"),
        "predicateID": Column("INTEGER", "Foreign key to relationPredicates"),
        "object": Column("TEXT", "Target item URI"),
    },
)

COLLECTION_RELATIONS = Table(
    name="collectionRelations",
    description="Relations between collections",
    columns={
        "collectionID": Column("INTEGER", "Foreign key to collections"),
        "predicateID": Column("INTEGER", "Foreign key to relationPredicates"),
        "object": Column("TEXT", "Target collection URI"),
    },
)

RELATION_PREDICATES = Table(
    name="relationPredicates",
    description="Predicate types for relations (dc:relation, owl:sameAs, etc.)",
    columns={
        "predicateID": Column("INTEGER", "Primary key"),
        "predicate": Column("TEXT", "Predicate URI"),
    },
)

# Field definition tables
FIELDS = Table(
    name="fields",
    description="Built-in field definitions",
    columns={
        "fieldID": Column("INTEGER", "Primary key"),
        "fieldName": Column("TEXT", "Internal field name"),
        "fieldFormatID": Column("INTEGER", "Format specification"),
    },
)

FIELD_FORMATS = Table(
    name="fieldFormats",
    description="Validation formats for field values",
    columns={
        "fieldFormatID": Column("INTEGER", "Primary key"),
        "regex": Column("TEXT", "Validation regex pattern"),
        "isInteger": Column("INTEGER", "Whether field is integer (0 or 1)"),
    },
)

BASE_FIELD_MAPPINGS = Table(
    name="baseFieldMappings",
    description="Maps item-type-specific fields to base fields (built-in)",
    columns={
        "itemTypeID": Column("INTEGER", "Foreign key to itemTypes"),
        "baseFieldID": Column("INTEGER", "Base field ID"),
        "fieldID": Column("INTEGER", "Item-type-specific field ID"),
    },
)

BASE_FIELD_MAPPINGS_COMBINED = Table(
    name="baseFieldMappingsCombined",
    description="Maps item-type-specific fields to base fields (built-in + custom)",
    columns={
        "itemTypeID": Column("INTEGER", "Foreign key to itemTypes"),
        "baseFieldID": Column("INTEGER", "Base field ID"),
        "fieldID": Column("INTEGER", "Item-type-specific field ID"),
    },
)

# Item type field tables
ITEM_TYPE_FIELDS = Table(
    name="itemTypeFields",
    description="Fields available for each item type (built-in)",
    columns={
        "itemTypeID": Column("INTEGER", "Foreign key to itemTypes"),
        "fieldID": Column("INTEGER", "Foreign key to fields"),
        "hide": Column("INTEGER", "Whether field is hidden (0 or 1)"),
        "orderIndex": Column("INTEGER", "Display order"),
    },
)

ITEM_TYPE_FIELDS_COMBINED = Table(
    name="itemTypeFieldsCombined",
    description="Fields available for each item type (built-in + custom)",
    columns={
        "itemTypeID": Column("INTEGER", "Foreign key to itemTypes"),
        "fieldID": Column("INTEGER", "Foreign key to fields"),
        "hide": Column("INTEGER", "Whether field is hidden (0 or 1)"),
        "orderIndex": Column("INTEGER", "Display order"),
    },
)

ITEM_TYPES_COMBINED = Table(
    name="itemTypesCombined",
    description="Item type definitions (built-in + custom)",
    columns={
        "itemTypeID": Column("INTEGER", "Primary key"),
        "typeName": Column("TEXT", "Internal type name"),
        "display": Column("INTEGER", "Display order"),
        "custom": Column("INTEGER", "Whether this is a custom type (0 or 1)"),
    },
)

# Creator type tables
CREATOR_TYPES = Table(
    name="creatorTypes",
    description="Creator role definitions (author, editor, translator, etc.)",
    columns={
        "creatorTypeID": Column("INTEGER", "Primary key"),
        "creatorType": Column("TEXT", "Role name"),
    },
)

ITEM_TYPE_CREATOR_TYPES = Table(
    name="itemTypeCreatorTypes",
    description="Creator roles available for each item type",
    columns={
        "itemTypeID": Column("INTEGER", "Foreign key to itemTypes"),
        "creatorTypeID": Column("INTEGER", "Foreign key to creatorTypes"),
        "primaryField": Column("INTEGER", "Whether this is the primary creator type (0 or 1)"),
    },
)

# Custom schema tables
CUSTOM_ITEM_TYPES = Table(
    name="customItemTypes",
    description="User-defined item types",
    columns={
        "customItemTypeID": Column("INTEGER", "Primary key"),
        "typeName": Column("TEXT", "Internal type name"),
        "label": Column("TEXT", "Display label"),
        "display": Column("INTEGER", "Display order"),
        "icon": Column("TEXT", "Icon identifier"),
    },
)

CUSTOM_FIELDS = Table(
    name="customFields",
    description="User-defined fields",
    columns={
        "customFieldID": Column("INTEGER", "Primary key"),
        "fieldName": Column("TEXT", "Internal field name"),
        "label": Column("TEXT", "Display label"),
    },
)

CUSTOM_ITEM_TYPE_FIELDS = Table(
    name="customItemTypeFields",
    description="Fields available for custom item types",
    columns={
        "customItemTypeID": Column("INTEGER", "Foreign key to customItemTypes"),
        "fieldID": Column("INTEGER", "Foreign key to fields"),
        "customFieldID": Column("INTEGER", "Foreign key to customFields"),
        "hide": Column("INTEGER", "Whether field is hidden (0 or 1)"),
        "orderIndex": Column("INTEGER", "Display order"),
    },
)

CUSTOM_BASE_FIELD_MAPPINGS = Table(
    name="customBaseFieldMappings",
    description="Maps custom fields to base fields",
    columns={
        "customItemTypeID": Column("INTEGER", "Foreign key to customItemTypes"),
        "baseFieldID": Column("INTEGER", "Base field ID"),
        "customFieldID": Column("INTEGER", "Foreign key to customFields"),
    },
)

# Group tables
GROUPS = Table(
    name="groups",
    description="Group library definitions",
    columns={
        "groupID": Column("INTEGER", "Primary key"),
        "libraryID": Column("INTEGER", "Foreign key to libraries"),
        "name": Column("TEXT", "Group name"),
        "description": Column("TEXT", "Group description"),
        "version": Column("INTEGER", "Sync version"),
    },
)

GROUP_ITEMS = Table(
    name="groupItems",
    description="Tracks which users created/modified items in group libraries",
    columns={
        "itemID": Column("INTEGER", "Foreign key to items"),
        "createdByUserID": Column("INTEGER", "Foreign key to users"),
        "lastModifiedByUserID": Column("INTEGER", "Foreign key to users"),
    },
)

USERS = Table(
    name="users",
    description="Zotero user accounts",
    columns={
        "userID": Column("INTEGER", "Primary key"),
        "name": Column("TEXT", "Display name"),
    },
)

# Feed tables
FEEDS = Table(
    name="feeds",
    description="RSS/Atom feed subscriptions",
    columns={
        "libraryID": Column("INTEGER", "Foreign key to libraries"),
        "name": Column("TEXT", "Feed name"),
        "url": Column("TEXT", "Feed URL"),
        "lastUpdate": Column("TIMESTAMP", "Last successful update"),
        "lastCheck": Column("TIMESTAMP", "Last check attempt"),
        "lastCheckError": Column("TEXT", "Error from last check"),
        "cleanupReadAfter": Column("INTEGER", "Days before read items are removed"),
        "cleanupUnreadAfter": Column("INTEGER", "Days before unread items are removed"),
        "refreshInterval": Column("INTEGER", "Refresh interval in minutes"),
    },
)

FEED_ITEMS = Table(
    name="feedItems",
    description="Items from RSS/Atom feeds",
    columns={
        "itemID": Column("INTEGER", "Foreign key to items"),
        "guid": Column("TEXT", "Feed item GUID"),
        "readTime": Column("TIMESTAMP", "When item was read"),
        "translatedTime": Column("TIMESTAMP", "When item was translated to Zotero item"),
    },
)

# Full-text indexing tables
FULLTEXT_ITEMS = Table(
    name="fulltextItems",
    description="Full-text indexing status for attachments",
    columns={
        "itemID": Column("INTEGER", "Foreign key to items"),
        "indexedPages": Column("INTEGER", "Number of pages indexed"),
        "totalPages": Column("INTEGER", "Total pages in document"),
        "indexedChars": Column("INTEGER", "Number of characters indexed"),
        "totalChars": Column("INTEGER", "Total characters"),
        "version": Column("INTEGER", "Index version"),
        "synced": Column("INTEGER", "Sync status (0 or 1)"),
    },
)

FULLTEXT_WORDS = Table(
    name="fulltextWords",
    description="Word dictionary for full-text search",
    columns={
        "wordID": Column("INTEGER", "Primary key"),
        "word": Column("TEXT", "Indexed word"),
    },
)

FULLTEXT_ITEM_WORDS = Table(
    name="fulltextItemWords",
    description="Links items to their indexed words",
    columns={
        "wordID": Column("INTEGER", "Foreign key to fulltextWords"),
        "itemID": Column("INTEGER", "Foreign key to items"),
    },
)

# Saved search tables
SAVED_SEARCHES = Table(
    name="savedSearches",
    description="Saved search definitions",
    columns={
        "savedSearchID": Column("INTEGER", "Primary key"),
        "savedSearchName": Column("TEXT", "Search name"),
        "clientDateModified": Column("TIMESTAMP", "Client-side modification timestamp"),
        "libraryID": Column("INTEGER", "Foreign key to libraries"),
        "key": Column("TEXT", "Unique sync key"),
        "version": Column("INTEGER", "Sync version"),
        "synced": Column("INTEGER", "Sync status (0 or 1)"),
    },
)

SAVED_SEARCH_CONDITIONS = Table(
    name="savedSearchConditions",
    description="Conditions for saved searches",
    columns={
        "savedSearchID": Column("INTEGER", "Foreign key to savedSearches"),
        "searchConditionID": Column("INTEGER", "Condition index"),
        "condition": Column("TEXT", "Field or condition type"),
        "operator": Column("TEXT", "Comparison operator"),
        "value": Column("TEXT", "Value to match"),
        "required": Column("INTEGER", "Whether condition is required (0 or 1)"),
    },
)

# Charset and file type tables
CHARSETS = Table(
    name="charsets",
    description="Character set definitions for text attachments",
    columns={
        "charsetID": Column("INTEGER", "Primary key"),
        "charset": Column("TEXT", "Character set name (e.g., utf-8)"),
    },
)

FILE_TYPES = Table(
    name="fileTypes",
    description="File type categories",
    columns={
        "fileTypeID": Column("INTEGER", "Primary key"),
        "fileType": Column("TEXT", "File type name"),
    },
)

FILE_TYPE_MIME_TYPES = Table(
    name="fileTypeMimeTypes",
    description="Maps file types to MIME types",
    columns={
        "fileTypeID": Column("INTEGER", "Foreign key to fileTypes"),
        "mimeType": Column("TEXT", "MIME type string"),
    },
)

# Proxy tables
PROXIES = Table(
    name="proxies",
    description="Proxy configurations for accessing paywalled content",
    columns={
        "proxyID": Column("INTEGER", "Primary key"),
        "multiHost": Column("INTEGER", "Whether proxy handles multiple hosts (0 or 1)"),
        "autoAssociate": Column("INTEGER", "Whether to auto-detect proxy (0 or 1)"),
        "scheme": Column("TEXT", "Proxy URL scheme/template"),
    },
)

PROXY_HOSTS = Table(
    name="proxyHosts",
    description="Hostnames associated with proxies",
    columns={
        "hostID": Column("INTEGER", "Primary key"),
        "proxyID": Column("INTEGER", "Foreign key to proxies"),
        "hostname": Column("TEXT", "Hostname"),
    },
)

# Deletion tracking tables
DELETED_ITEMS = Table(
    name="deletedItems",
    description="Tracks deleted items for sync",
    columns={
        "itemID": Column("INTEGER", "Deleted item ID"),
        "dateDeleted": Column("TIMESTAMP", "Deletion timestamp"),
    },
)

DELETED_COLLECTIONS = Table(
    name="deletedCollections",
    description="Tracks deleted collections for sync",
    columns={
        "collectionID": Column("INTEGER", "Deleted collection ID"),
        "dateDeleted": Column("TIMESTAMP", "Deletion timestamp"),
    },
)

DELETED_SEARCHES = Table(
    name="deletedSearches",
    description="Tracks deleted saved searches for sync",
    columns={
        "savedSearchID": Column("INTEGER", "Deleted search ID"),
        "dateDeleted": Column("TIMESTAMP", "Deletion timestamp"),
    },
)

RETRACTED_ITEMS = Table(
    name="retractedItems",
    description="Items flagged as retracted publications",
    columns={
        "itemID": Column("INTEGER", "Foreign key to items"),
        "data": Column("TEXT", "Retraction data (JSON)"),
        "flag": Column("INTEGER", "Retraction flag"),
    },
)

PUBLICATIONS_ITEMS = Table(
    name="publicationsItems",
    description="Items shared to My Publications feed",
    columns={
        "itemID": Column("INTEGER", "Foreign key to items"),
    },
)

# Sync tables
SYNC_OBJECT_TYPES = Table(
    name="syncObjectTypes",
    description="Object type definitions for sync (item, collection, search, etc.)",
    columns={
        "syncObjectTypeID": Column("INTEGER", "Primary key"),
        "name": Column("TEXT", "Object type name"),
    },
)

SYNC_CACHE = Table(
    name="syncCache",
    description="Cached sync data from server",
    columns={
        "libraryID": Column("INTEGER", "Foreign key to libraries"),
        "key": Column("TEXT", "Object sync key"),
        "syncObjectTypeID": Column("INTEGER", "Foreign key to syncObjectTypes"),
        "version": Column("INTEGER", "Object version"),
        "data": Column("TEXT", "Cached JSON data"),
    },
)

SYNC_DELETE_LOG = Table(
    name="syncDeleteLog",
    description="Log of remotely deleted objects pending local deletion",
    columns={
        "syncObjectTypeID": Column("INTEGER", "Foreign key to syncObjectTypes"),
        "libraryID": Column("INTEGER", "Foreign key to libraries"),
        "key": Column("TEXT", "Object sync key"),
        "dateDeleted": Column("TIMESTAMP", "Deletion timestamp"),
    },
)

SYNC_QUEUE = Table(
    name="syncQueue",
    description="Queue of objects pending sync upload",
    columns={
        "libraryID": Column("INTEGER", "Foreign key to libraries"),
        "key": Column("TEXT", "Object sync key"),
        "syncObjectTypeID": Column("INTEGER", "Foreign key to syncObjectTypes"),
        "lastCheck": Column("TIMESTAMP", "Last sync attempt"),
        "tries": Column("INTEGER", "Number of sync attempts"),
    },
)

SYNCED_SETTINGS = Table(
    name="syncedSettings",
    description="Settings synced across devices",
    columns={
        "setting": Column("TEXT", "Setting name"),
        "libraryID": Column("INTEGER", "Foreign key to libraries"),
        "value": Column("TEXT", "Setting value"),
        "version": Column("INTEGER", "Setting version"),
        "synced": Column("INTEGER", "Sync status (0 or 1)"),
    },
)

STORAGE_DELETE_LOG = Table(
    name="storageDeleteLog",
    description="Log of file attachments pending remote deletion",
    columns={
        "libraryID": Column("INTEGER", "Foreign key to libraries"),
        "key": Column("TEXT", "Object sync key"),
        "dateDeleted": Column("TIMESTAMP", "Deletion timestamp"),
    },
)

# Settings and metadata tables
SETTINGS = Table(
    name="settings",
    description="Local Zotero settings (key-value pairs)",
    columns={
        "setting": Column("TEXT", "Setting category"),
        "key": Column("TEXT", "Setting key"),
        "value": Column("TEXT", "Setting value"),
    },
)

TRANSLATOR_CACHE = Table(
    name="translatorCache",
    description="Cached metadata for Zotero translators (import/export plugins)",
    columns={
        "fileName": Column("TEXT", "Translator filename"),
        "metadataJSON": Column("TEXT", "Translator metadata (JSON)"),
        "lastModifiedTime": Column("INTEGER", "File modification timestamp"),
    },
)

VERSION = Table(
    name="version",
    description="Database schema version tracking",
    columns={
        "schema": Column("TEXT", "Schema name"),
        "version": Column("INTEGER", "Schema version number"),
    },
)

DB_DEBUG1 = Table(
    name="dbDebug1",
    description="Debug table (internal use)",
    columns={
        "a": Column("INTEGER", "Debug value"),
    },
)

# All schemas for iteration
ALL_SCHEMAS = [
    # Core item tables
    ITEMS,
    ITEM_DATA,
    ITEM_DATA_VALUES,
    FIELDS_COMBINED,
    ITEM_TYPES,
    ITEM_TYPES_COMBINED,
    # Creator tables
    ITEM_CREATORS,
    CREATORS,
    CREATOR_TYPES,
    ITEM_TYPE_CREATOR_TYPES,
    # Collection tables
    COLLECTION_ITEMS,
    COLLECTIONS,
    # Library tables
    LIBRARIES,
    # Attachment and annotation tables
    ITEM_ATTACHMENTS,
    ITEM_ANNOTATIONS,
    ITEM_NOTES,
    # Tag tables
    ITEM_TAGS,
    TAGS,
    # Relation tables
    ITEM_RELATIONS,
    COLLECTION_RELATIONS,
    RELATION_PREDICATES,
    # Field definition tables
    FIELDS,
    FIELD_FORMATS,
    BASE_FIELD_MAPPINGS,
    BASE_FIELD_MAPPINGS_COMBINED,
    ITEM_TYPE_FIELDS,
    ITEM_TYPE_FIELDS_COMBINED,
    # Custom schema tables
    CUSTOM_ITEM_TYPES,
    CUSTOM_FIELDS,
    CUSTOM_ITEM_TYPE_FIELDS,
    CUSTOM_BASE_FIELD_MAPPINGS,
    # Group tables
    GROUPS,
    GROUP_ITEMS,
    USERS,
    # Feed tables
    FEEDS,
    FEED_ITEMS,
    # Full-text indexing tables
    FULLTEXT_ITEMS,
    FULLTEXT_WORDS,
    FULLTEXT_ITEM_WORDS,
    # Saved search tables
    SAVED_SEARCHES,
    SAVED_SEARCH_CONDITIONS,
    # Charset and file type tables
    CHARSETS,
    FILE_TYPES,
    FILE_TYPE_MIME_TYPES,
    # Proxy tables
    PROXIES,
    PROXY_HOSTS,
    # Deletion tracking tables
    DELETED_ITEMS,
    DELETED_COLLECTIONS,
    DELETED_SEARCHES,
    RETRACTED_ITEMS,
    PUBLICATIONS_ITEMS,
    # Sync tables
    SYNC_OBJECT_TYPES,
    SYNC_CACHE,
    SYNC_DELETE_LOG,
    SYNC_QUEUE,
    SYNCED_SETTINGS,
    STORAGE_DELETE_LOG,
    # Settings and metadata tables
    SETTINGS,
    TRANSLATOR_CACHE,
    VERSION,
    DB_DEBUG1,
]


# Lookup by table name
SCHEMA_MAP = {s.name: s for s in ALL_SCHEMAS}


def get_table_names() -> list[str]:
    """Get list of table names used by zotlib."""
    return [s.name for s in ALL_SCHEMAS]


def get_schema(table_name: str) -> Table | None:
    """Get schema definition for a table."""
    for schema in ALL_SCHEMAS:
        if schema.name == table_name:
            return schema
    return None
