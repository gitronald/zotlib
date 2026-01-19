"""Data extraction functions for Zotero database."""

import pandas as pd

from zotlib.database import ZoteroDatabase


def extract_items(db: ZoteroDatabase) -> pd.DataFrame:
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
    details = entries.pivot(index="itemID", columns="fieldName", values="value")
    details = details.rename_axis(None, axis=1).reset_index()
    items = items.merge(details, how="left", on="itemID")

    # Merge item type names
    itemtypes = extract_itemtypes(db)
    items = items.merge(
        itemtypes[["itemTypeID", "typeName"]],
        how="left",
        on="itemTypeID",
        validate="m:1",
    )

    return items


def extract_itemtypes(db: ZoteroDatabase) -> pd.DataFrame:
    """Extract item type definitions."""
    return db.query("SELECT * FROM itemTypes")


def extract_creators(db: ZoteroDatabase) -> pd.DataFrame:
    """Extract item-creator relationships with creator details."""
    query = """
    SELECT itemCreators.itemID, itemCreators.creatorID, itemCreators.creatorTypeID,
           itemCreators.orderIndex, creators.firstName, creators.lastName,
           creators.fieldMode
    FROM itemCreators
    LEFT JOIN creators ON itemCreators.creatorID = creators.creatorID
    """
    return db.query(query)


def extract_collections(db: ZoteroDatabase) -> pd.DataFrame:
    """Extract collection memberships with collection metadata."""
    query = """
    SELECT collectionItems.collectionID, collectionItems.itemID,
           collectionItems.orderIndex, collections.collectionName,
           collections.parentCollectionID, collections.libraryID
    FROM collectionItems
    LEFT JOIN collections ON collectionItems.collectionID = collections.collectionID
    """
    return db.query(query)


def extract_libraries(db: ZoteroDatabase) -> pd.DataFrame:
    """Extract library metadata."""
    return db.query("SELECT * FROM libraries")


def _get_first_notnull(row: pd.Series) -> str | None:
    """Get first non-null value in a row."""
    valid_index = row.first_valid_index()
    return None if valid_index is None else row[valid_index]


def _clean_items(items: pd.DataFrame) -> pd.DataFrame:
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
        items["publication"] = items[existing_cols].apply(_get_first_notnull, axis=1)

    # Clean dates
    items["date_raw"] = items["date"].copy()
    items["datefmt"] = items["date_raw"].fillna("").str.split(" ", expand=True)[0]

    # Handle malformed dates like "2003-01-00"
    mask = items.datefmt.str.endswith("00")
    items.loc[mask, "datefmt"] = (
        items.loc[mask, "datefmt"].str.split("-", expand=True)[0]
    )

    items["date"] = pd.to_datetime(items["datefmt"], errors="coerce")
    items["year"] = items.date.dt.year
    items["month"] = items.date.dt.month

    # Clean encoded characters in pages
    if "pages" in items.columns:
        items["pages"] = items["pages"].fillna("").str.replace("–", "-")

    return items


def _add_authors(items: pd.DataFrame, creators: pd.DataFrame) -> pd.DataFrame:
    """Add concatenated authors string to items."""
    creators = creators.copy()
    creators["authors"] = creators["firstName"] + " " + creators["lastName"]
    item_creators = creators.groupby("itemID")["authors"].apply(
        lambda x: ", ".join(x)
    )
    return items.merge(item_creators, how="left", on="itemID")


def extract_cv_items(
    db: ZoteroDatabase,
    collection_name: str,
) -> pd.DataFrame:
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
    cv_collection = collections.query(f"collectionName == '{collection_name}'")
    cv_items = items.query("itemID in @cv_collection['itemID']").copy()

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
    ]
    existing_cols = [c for c in cols_main if c in cv_items.columns]

    return cv_items[existing_cols]
