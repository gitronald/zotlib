# Zotero Database Schema

Schema definitions for Zotero SQLite database tables used by zotlib.

## items

Base table for all Zotero items (papers, books, etc.)

| Name | Type | Description |
|------|------|-------------|
| itemID | INTEGER | Primary key |
| itemTypeID | INTEGER | Foreign key to itemTypes |
| dateAdded | TIMESTAMP | Timestamp when item was added |
| dateModified | TIMESTAMP | Timestamp of last modification |
| clientDateModified | TIMESTAMP | Client-side modification timestamp |
| libraryID | INTEGER | Foreign key to libraries |
| key | TEXT | Unique sync key |
| version | INTEGER | Sync version number |
| synced | INTEGER | Sync status flag (0 or 1) |

## itemData

Links items to their field values (title, date, DOI, etc.)

| Name | Type | Description |
|------|------|-------------|
| itemID | INTEGER | Foreign key to items |
| fieldID | INTEGER | Foreign key to fieldsCombined |
| valueID | INTEGER | Foreign key to itemDataValues |

## itemDataValues

Stores actual field values (deduplicated)

| Name | Type | Description |
|------|------|-------------|
| valueID | INTEGER | Primary key |
| value | TEXT | The actual field value text |

## fieldsCombined

Field definitions (title, date, DOI, volume, etc.)

| Name | Type | Description |
|------|------|-------------|
| fieldID | INTEGER | Primary key |
| fieldName | TEXT | Internal field name (e.g., 'title', 'DOI') |
| label | TEXT | Display label |
| fieldFormatID | INTEGER | Format specification |
| custom | INTEGER | Whether this is a custom field (0 or 1) |

## itemTypes

Item type definitions (journalArticle, book, etc.)

| Name | Type | Description |
|------|------|-------------|
| itemTypeID | INTEGER | Primary key |
| typeName | TEXT | Internal type name |
| templateItemTypeID | INTEGER | Template reference |
| display | INTEGER | Display order |

## itemCreators

Links items to their creators (authors, editors, etc.)

| Name | Type | Description |
|------|------|-------------|
| itemID | INTEGER | Foreign key to items |
| creatorID | INTEGER | Foreign key to creators |
| creatorTypeID | INTEGER | Type of creator (author, editor, etc.) |
| orderIndex | INTEGER | Position in author list |

## creators

Creator (person) records

| Name | Type | Description |
|------|------|-------------|
| creatorID | INTEGER | Primary key |
| firstName | TEXT | First name |
| lastName | TEXT | Last name |
| fieldMode | INTEGER | Name format mode (0=two-field, 1=single-field) |

## collectionItems

Links items to collections

| Name | Type | Description |
|------|------|-------------|
| collectionID | INTEGER | Foreign key to collections |
| itemID | INTEGER | Foreign key to items |
| orderIndex | INTEGER | Position in collection |

## collections

Collection (folder) definitions

| Name | Type | Description |
|------|------|-------------|
| collectionID | INTEGER | Primary key |
| collectionName | TEXT | Display name |
| parentCollectionID | INTEGER | Parent collection (for nesting) |
| clientDateModified | TIMESTAMP | Client-side modification timestamp |
| libraryID | INTEGER | Foreign key to libraries |
| key | TEXT | Unique sync key |
| version | INTEGER | Sync version number |
| synced | INTEGER | Sync status flag (0 or 1) |

## libraries

Library definitions (personal, group libraries)

| Name | Type | Description |
|------|------|-------------|
| libraryID | INTEGER | Primary key |
| type | TEXT | Library type (user, group) |
| editable | INTEGER | Whether library is editable (0 or 1) |
| filesEditable | INTEGER | Whether files can be modified (0 or 1) |
| version | INTEGER | Sync version |
| storageVersion | INTEGER | Storage version |
| lastSync | TIMESTAMP | Last sync timestamp |
| archived | INTEGER | Archive status (0 or 1) |

## itemAttachments

PDF and file attachments linked to items

| Name | Type | Description |
|------|------|-------------|
| itemID | INTEGER | Primary key (the attachment item) |
| parentItemID | INTEGER | Foreign key to the parent item |
| linkMode | INTEGER | How the file is stored (0=imported, 1=linked, 2=web) |
| contentType | TEXT | MIME type (e.g., application/pdf) |
| charsetID | INTEGER | Character set for text attachments |
| path | TEXT | File path (storage:, attachments:, or absolute) |
| syncState | INTEGER | File sync status |
| storageModTime | INTEGER | Storage modification timestamp |
| storageHash | TEXT | File content hash |
| lastProcessedModificationTime | INTEGER | Last processing timestamp |

## itemAnnotations

PDF annotations created in Zotero's built-in reader

| Name | Type | Description |
|------|------|-------------|
| itemID | INTEGER | Primary key (the annotation item) |
| parentItemID | INTEGER | Foreign key to the PDF attachment item |
| type | INTEGER | Annotation type (1=highlight, 2=note, 3=image, 5=underline) |
| authorName | TEXT | Name of annotation author |
| text | TEXT | Highlighted or selected text |
| comment | TEXT | User comment on the annotation |
| color | TEXT | Hex color string (e.g., #ffd400) |
| pageLabel | TEXT | Page number label |
| sortIndex | TEXT | Lexicographic sort index for ordering |
| position | TEXT | JSON with pageIndex and rects/paths coordinates |
| isExternal | INTEGER | Whether annotation is external (0 or 1) |

## itemTags

Links items to tags

| Name | Type | Description |
|------|------|-------------|
| itemID | INTEGER | Foreign key to items |
| tagID | INTEGER | Foreign key to tags |
| type | INTEGER | Tag type (0=manual, 1=automatic) |

## tags

Tag definitions

| Name | Type | Description |
|------|------|-------------|
| tagID | INTEGER | Primary key |
| name | TEXT | Tag display name |
