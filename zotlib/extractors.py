"""Data extraction functions for Zotero database."""

import polars as pl

from zotlib.database import ZoteroDatabase


def extract_items(db: ZoteroDatabase) -> pl.DataFrame:
    """Extract all items with merged field values and types.

    Joins items with itemData, fieldsCombined, and itemDataValues
    to reconstruct full item metadata.
    """
    # Get base items
    items = db.query("SELECT * FROM items")

    # Get item details by joining itemData -> fieldsCombined -> itemDataValues
    details_query = """
    SELECT itemData.itemID, itemData.fieldID, itemData.valueID,
           fieldsCombined.fieldName, itemDataValues.value
    FROM itemData
    LEFT JOIN fieldsCombined ON itemData.fieldID = fieldsCombined.fieldID
    LEFT JOIN itemDataValues ON itemData.valueID = itemDataValues.valueID
    """
    entries = db.query(details_query)

    # Pivot field names to columns
    details = entries.pivot(
        on="fieldName", index="itemID", values="value", aggregate_function="first"
    )
    items = items.join(details, on="itemID", how="left")

    # Merge item type names
    itemtypes = extract_itemtypes(db)
    items = items.join(
        itemtypes.select("itemTypeID", "typeName"),
        on="itemTypeID",
        how="left",
    )

    return items


def extract_itemtypes(db: ZoteroDatabase) -> pl.DataFrame:
    """Extract item type definitions."""
    return db.query("SELECT * FROM itemTypes")


def extract_creators(db: ZoteroDatabase) -> pl.DataFrame:
    """Extract item-creator relationships with creator details."""
    query = """
    SELECT itemCreators.itemID, itemCreators.creatorID, itemCreators.creatorTypeID,
           itemCreators.orderIndex, creators.firstName, creators.lastName,
           creators.fieldMode
    FROM itemCreators
    LEFT JOIN creators ON itemCreators.creatorID = creators.creatorID
    """
    return db.query(query)


def extract_collections(db: ZoteroDatabase) -> pl.DataFrame:
    """Extract collection memberships with collection metadata."""
    query = """
    SELECT collectionItems.collectionID, collectionItems.itemID,
           collectionItems.orderIndex, collections.collectionName,
           collections.parentCollectionID, collections.libraryID
    FROM collectionItems
    LEFT JOIN collections ON collectionItems.collectionID = collections.collectionID
    """
    return db.query(query)


def extract_libraries(db: ZoteroDatabase) -> pl.DataFrame:
    """Extract library metadata."""
    return db.query("SELECT * FROM libraries")


def _get_first_notnull(row: dict, cols: list[str]) -> str | None:
    """Get first non-null value from specified columns in a row dict."""
    for col in cols:
        val = row.get(col)
        if val is not None:
            return val
    return None


def _clean_items(items: pl.DataFrame) -> pl.DataFrame:
    """Clean and transform items DataFrame."""
    # Condense publication title from multiple columns
    title_cols = [
        "publicationTitle",
        "blogTitle",
        "bookTitle",
        "encyclopediaTitle",
        "proceedingsTitle",
        "seriesTitle",
        "websiteTitle",
        "publisher",
    ]
    existing_cols = [c for c in title_cols if c in items.columns]
    if existing_cols:
        items = items.with_columns(
            pl.coalesce([pl.col(c) for c in existing_cols]).alias("publication")
        )

    # Clean dates
    items = items.rename({"date": "date_raw"})

    # Extract first part before space, handle malformed dates
    items = items.with_columns(
        pl.col("date_raw")
        .fill_null("")
        .str.split(" ")
        .list.first()
        .str.replace_all("-00", "-01", literal=True)
        .alias("datefmt")
    )

    items = items.with_columns(
        pl.col("datefmt").str.to_date("%Y-%m-%d", strict=False).alias("date")
    )
    items = items.with_columns(
        pl.col("date").dt.year().alias("year"),
        pl.col("date").dt.month().alias("month"),
    )

    # Clean encoded characters in pages
    if "pages" in items.columns:
        items = items.with_columns(
            pl.col("pages").fill_null("").str.replace_all("\u2013", "-", literal=True).alias("pages")
        )

    return items


def _add_authors(items: pl.DataFrame, creators: pl.DataFrame) -> pl.DataFrame:
    """Add concatenated authors string to items."""
    item_creators = (
        creators.with_columns(
            (pl.col("firstName") + " " + pl.col("lastName")).alias("authors")
        )
        .group_by("itemID")
        .agg(pl.col("authors").str.join(", "))
    )
    return items.join(item_creators, on="itemID", how="left")


def extract_attachments(db: ZoteroDatabase) -> pl.DataFrame:
    """Extract PDF attachment paths with parent item and storage key.

    Returns DataFrame with: parentItemID, key (storage directory), path (filename).
    """
    query = """
    SELECT items.itemID, items.key, itemAttachments.parentItemID,
           itemAttachments.contentType, itemAttachments.path
    FROM itemAttachments
    JOIN items ON itemAttachments.itemID = items.itemID
    WHERE itemAttachments.contentType = 'application/pdf'
    AND itemAttachments.path IS NOT NULL
    """
    return db.query(query)


def extract_annotations(db: ZoteroDatabase) -> pl.DataFrame:
    """Extract PDF annotations from itemAnnotations table.

    Returns DataFrame with: itemID, parentItemID, type, text, comment,
    color, pageLabel, sortIndex, position, isExternal.
    """
    return db.query("SELECT * FROM itemAnnotations")


def extract_tags(db: ZoteroDatabase) -> pl.DataFrame:
    """Extract item tags with tag names.

    Returns DataFrame with: itemID, tagID, type, name.
    """
    query = """
    SELECT itemTags.itemID, itemTags.tagID, itemTags.type, tags.name
    FROM itemTags
    JOIN tags ON itemTags.tagID = tags.tagID
    """
    return db.query(query)


def extract_cv_items(
    db: ZoteroDatabase,
    collection_name: str,
) -> pl.DataFrame:
    """Extract items from a specific collection for CV use.

    Args:
        db: ZoteroDatabase instance.
        collection_name: Name of collection to filter by.

    Returns:
        DataFrame with cleaned CV items including authors.
    """
    items = extract_items(db)
    collections = extract_collections(db)
    creators = extract_creators(db)

    # Filter by collection
    cv_item_ids = collections.filter(
        pl.col("collectionName") == collection_name
    )["itemID"]
    cv_items = items.filter(pl.col("itemID").is_in(cv_item_ids))

    # Add authors and clean data
    cv_items = _add_authors(cv_items, creators)
    cv_items = _clean_items(cv_items)

    # Select main columns
    cols_main = [
        "itemID",
        "typeName",
        "authors",
        "title",
        "date",
        "year",
        "publication",
        "volume",
        "issue",
        "pages",
        "DOI",
        "url",
        "repository",
    ]
    existing_cols = [c for c in cols_main if c in cv_items.columns]

    return cv_items.select(existing_cols)
