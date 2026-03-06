"""Export review papers with annotations and markdown notes."""

import json
import shutil
from pathlib import Path

import fitz
import pandas as pd

from zotlib.covers import resolve_pdf_path, sanitize_filename
from zotlib.database import ZoteroDatabase
from zotlib.extractors import (
    extract_attachments,
    extract_collections,
    extract_creators,
    extract_items,
    extract_tags,
    _clean_items,
    _add_authors,
)


# Zotero annotation type integers to names
ANNOTATION_TYPES = {
    1: "highlight",
    2: "note",
    3: "image",
    4: "ink",
    5: "underline",
    6: "text",
}

# Zotero hex colors to readable labels (matches zotero-js/extract-annotations.js)
COLOR_LABELS = {
    "#ffd400": "yellow",
    "#ffff00": "yellow",
    "#ff6666": "red",
    "#ff0000": "red",
    "#5fb236": "green",
    "#00ff00": "green",
    "#2ea8e5": "blue",
    "#0000ff": "blue",
    "#a28ae5": "purple",
    "#800080": "purple",
    "#e56eee": "magenta",
    "#f19837": "orange",
}


def _str_or(value, default: str = "") -> str:
    """Coerce a value to string, returning default for NaN/None."""
    if pd.isna(value):
        return default
    return str(value) if value else default


def get_color_label(color: str) -> str:
    """Map a Zotero hex color to a readable label."""
    if not color:
        return ""
    return COLOR_LABELS.get(color.lower(), color)


def hex_to_rgb(color: str) -> tuple[float, float, float]:
    """Convert hex color string to RGB floats (0-1)."""
    color = color.lstrip("#")
    r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
    return (r / 255, g / 255, b / 255)


def convert_zotero_rect(
    rect: list[float], page_height: float
) -> fitz.Rect:
    """Convert a Zotero rect to a PyMuPDF rect.

    Zotero stores rects as [x0, y0, x1, y1] in PDF coordinates (bottom-left
    origin). PyMuPDF uses top-left origin, so Y coordinates are flipped.
    """
    x0, y0_bot, x1, y1_bot = rect
    y0_top = page_height - y1_bot
    y1_top = page_height - y0_bot
    return fitz.Rect(x0, y0_top, x1, y1_top)


def get_collection_items(
    db: ZoteroDatabase,
    collection_name: str,
) -> pd.DataFrame:
    """Get items in a collection with full metadata, authors, and tags.

    Args:
        db: ZoteroDatabase instance.
        collection_name: Name of the collection to filter by.

    Returns:
        DataFrame with item metadata including authors and tags.
    """
    items = extract_items(db)
    collections = extract_collections(db)
    creators = extract_creators(db)
    tags = extract_tags(db)

    # Filter to collection
    coll = collections.query(f"collectionName == '{collection_name}'")
    if coll.empty:
        raise ValueError(f"Collection not found: {collection_name}")

    coll_items = items.query("itemID in @coll['itemID']").copy()

    # Exclude attachment and note types (handled separately)
    coll_items = coll_items.query("typeName not in ['attachment', 'note']")

    # Add authors
    coll_items = _add_authors(coll_items, creators)

    # Add tags (comma-separated)
    item_tags = (
        tags.groupby("itemID")["name"]
        .apply(lambda x: ", ".join(sorted(x)))
        .rename("tags")
    )
    coll_items = coll_items.merge(item_tags, how="left", on="itemID")

    # Clean dates
    coll_items = _clean_items(coll_items)

    return coll_items


def get_standalone_attachments(
    db: ZoteroDatabase,
    collection_name: str,
) -> pd.DataFrame:
    """Get standalone PDF attachments in a collection.

    These are PDFs added directly to a collection without a parent item.

    Args:
        db: ZoteroDatabase instance.
        collection_name: Name of the collection to filter by.

    Returns:
        DataFrame with itemID, key, path, and title columns.
    """
    query = """
    SELECT i.itemID, i.key, ia.path, ia.contentType,
           COALESCE(idv.value, ia.path) AS title
    FROM collectionItems ci
    JOIN collections c ON ci.collectionID = c.collectionID
    JOIN items i ON ci.itemID = i.itemID
    JOIN itemAttachments ia ON i.itemID = ia.itemID
    LEFT JOIN itemData id ON i.itemID = id.itemID
        AND id.fieldID = (SELECT fieldID FROM fieldsCombined WHERE fieldName = 'title')
    LEFT JOIN itemDataValues idv ON id.valueID = idv.valueID
    WHERE c.collectionName = ?
      AND ia.parentItemID IS NULL
      AND ia.contentType = 'application/pdf'
      AND ia.path IS NOT NULL
    """
    with db.connection() as conn:
        return pd.read_sql_query(query, conn, params=[collection_name])


def get_item_annotations(
    db: ZoteroDatabase,
    item_ids: set[int],
) -> pd.DataFrame:
    """Get annotations for items, joined through the attachment chain.

    The join path: annotation.parentItemID -> attachment.itemID,
    attachment.parentItemID -> paper.itemID.

    Args:
        db: ZoteroDatabase instance.
        item_ids: Set of parent item IDs (the papers).

    Returns:
        DataFrame with annotations plus paperItemID column.
    """
    ids_str = ", ".join(str(i) for i in item_ids)
    query = f"""
    SELECT ia.*, iatt.parentItemID AS paperItemID
    FROM itemAnnotations ia
    JOIN itemAttachments iatt ON ia.parentItemID = iatt.itemID
    WHERE iatt.parentItemID IN ({ids_str})
    ORDER BY ia.sortIndex
    """
    return db.query(query)


def make_review_dirname(item_row: pd.Series) -> str:
    """Build a subdirectory name from item metadata.

    Format: {first-author-last}-{year}-{short-title}
    """
    authors = _str_or(item_row.get("authors"))
    first_author = authors.split(",")[0].strip().split()[-1] if authors else "unknown"

    year = item_row.get("year")
    year_str = str(int(year)) if pd.notna(year) else "nd"

    title = _strip_review_prefix(_str_or(item_row.get("title"), "untitled"))
    short_title = title[:60].strip()

    raw = f"{first_author}-{year_str}-{short_title}"
    return sanitize_filename(raw).lower().replace(" ", "-")


def bake_annotations(
    pdf_path: Path,
    annotations_df: pd.DataFrame,
    output_path: Path,
) -> list[str]:
    """Copy a PDF and bake Zotero annotations into it.

    Args:
        pdf_path: Path to the source PDF.
        annotations_df: DataFrame of annotations for this PDF's parent item.
        output_path: Path to write the annotated PDF.

    Returns:
        List of warnings for skipped annotations.
    """
    warnings = []
    doc = fitz.open(pdf_path)

    for _, ann in annotations_df.iterrows():
        ann_type = ANNOTATION_TYPES.get(ann["type"], "")
        position_raw = _str_or(ann.get("position"))
        comment = _str_or(ann.get("comment"))
        color = _str_or(ann.get("color"))

        # Parse position JSON
        try:
            position = json.loads(position_raw) if position_raw else {}
        except (json.JSONDecodeError, TypeError):
            warnings.append(f"Bad position JSON for annotation {ann['itemID']}")
            continue

        page_index = position.get("pageIndex", 0)
        rects = position.get("rects", [])

        if page_index >= len(doc):
            warnings.append(
                f"Page {page_index} out of range for annotation {ann['itemID']}"
            )
            continue

        page = doc[page_index]
        page_height = page.rect.height

        if ann_type in ("highlight", "underline"):
            if not rects:
                continue

            quads = []
            for r in rects:
                if len(r) != 4:
                    continue
                rect = convert_zotero_rect(r, page_height)
                quads.append(rect.quad)

            if not quads:
                continue

            if ann_type == "highlight":
                annot = page.add_highlight_annot(quads)
            else:
                annot = page.add_underline_annot(quads)

            if color:
                rgb = hex_to_rgb(color)
                annot.set_colors(stroke=rgb)

            if comment:
                annot.info["content"] = comment

            annot.update()

        elif ann_type == "note":
            # Place note icon at the position
            if rects:
                rect = convert_zotero_rect(rects[0], page_height)
                point = fitz.Point(rect.x0, rect.y0)
            else:
                point = fitz.Point(50, 50)

            text = comment or _str_or(ann.get("text"))
            if text:
                annot = page.add_text_annot(point, text)
                if color:
                    rgb = hex_to_rgb(color)
                    annot.set_colors(fill=rgb)
                annot.update()

        elif ann_type in ("image", "ink"):
            warnings.append(f"Skipped {ann_type} annotation on page {page_index + 1}")

    doc.save(str(output_path), garbage=4, deflate=True)
    doc.close()

    return warnings


def format_annotations_markdown(
    item_row: pd.Series,
    annotations_df: pd.DataFrame,
) -> str:
    """Generate markdown with YAML frontmatter and page-grouped annotations.

    Args:
        item_row: Series with item metadata (title, authors, year, etc.).
        annotations_df: DataFrame of annotations sorted by sortIndex.

    Returns:
        Markdown string.
    """
    lines = []

    # YAML frontmatter
    title = _strip_review_prefix(_str_or(item_row.get("title"), "Untitled"))
    authors = _str_or(item_row.get("authors"))
    year = item_row.get("year")
    year_str = str(int(year)) if pd.notna(year) else ""
    publication = _str_or(item_row.get("publicationTitle"))
    doi = _str_or(item_row.get("DOI"))
    date_added = _str_or(item_row.get("dateAdded"))
    tags = _str_or(item_row.get("tags"))
    url = _str_or(item_row.get("url"))

    lines.append("---")
    lines.append(f'title: "{title}"')
    if authors:
        lines.append(f'authors: "{authors}"')
    if year_str:
        lines.append(f"year: {year_str}")
    if publication:
        lines.append(f'publication: "{publication}"')
    if doi:
        lines.append(f'doi: "{doi}"')
    if url:
        lines.append(f'url: "{url}"')
    if date_added:
        lines.append(f'date_added: "{date_added}"')
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        lines.append(f"tags: {tag_list}")
    lines.append(f"annotation_count: {len(annotations_df)}")
    lines.append("---")
    lines.append("")

    # Annotations grouped by page
    current_page = -1

    for _, ann in annotations_df.iterrows():
        ann_type = ANNOTATION_TYPES.get(ann["type"], str(ann["type"]))
        text = _str_or(ann.get("text"))
        comment = _str_or(ann.get("comment"))
        color = _str_or(ann.get("color"))

        # Determine page number
        position_raw = _str_or(ann.get("position"))
        try:
            position = json.loads(position_raw) if position_raw else {}
        except (json.JSONDecodeError, TypeError):
            position = {}

        page_label = _str_or(ann.get("pageLabel"))
        page_index = position.get("pageIndex", 0)
        page = int(page_label) if page_label else page_index + 1

        if page != current_page:
            current_page = page
            lines.append(f"## Page {page}")
            lines.append("")

        if ann_type == "highlight":
            color_label = get_color_label(color)
            prefix = f"[{color_label}] " if color_label else ""
            lines.append(f"{prefix}**Highlight:**")
            lines.append("> " + text.replace("\n", "\n> "))
            if comment:
                lines.append("")
                lines.append(f"**Note:** {comment}")
            lines.append("")

        elif ann_type == "note":
            lines.append("**Note:**")
            lines.append(comment or text)
            lines.append("")

        elif ann_type == "underline":
            lines.append("**Underline:**")
            lines.append("> " + text.replace("\n", "\n> "))
            if comment:
                lines.append("")
                lines.append(f"**Note:** {comment}")
            lines.append("")

        elif ann_type == "image":
            lines.append("**Image annotation:**")
            if comment:
                lines.append(comment)
            lines.append("*(Image not exported)*")
            lines.append("")

        else:
            lines.append(f"**{ann_type}:**")
            if text:
                lines.append("> " + text.replace("\n", "\n> "))
            if comment:
                lines.append(f"**Note:** {comment}")
            lines.append("")

    return "\n".join(lines)


def _strip_review_prefix(title: str) -> str:
    """Strip 'REVIEW: ' prefix from a title if present."""
    if title.upper().startswith("REVIEW: "):
        return title[8:]
    return title


def _export_item(
    item_row: pd.Series,
    item_anns: pd.DataFrame,
    pdf_path: Path | None,
    output_dir: Path,
    warnings: list[str],
    console=None,
) -> bool:
    """Export a single item (PDF + markdown). Returns True if exported."""
    title = _str_or(item_row.get("title"), "untitled")
    has_annotations = len(item_anns) > 0
    has_pdf = pdf_path is not None

    if not has_pdf and not has_annotations:
        warnings.append(f"No PDF or annotations: {title}")
        return False

    dirname = make_review_dirname(item_row)
    item_dir = output_dir / dirname
    item_dir.mkdir(parents=True, exist_ok=True)

    if has_pdf:
        output_pdf = item_dir / "paper.pdf"
        if has_annotations:
            ann_warnings = bake_annotations(pdf_path, item_anns, output_pdf)
            warnings.extend(ann_warnings)
        else:
            shutil.copy2(pdf_path, output_pdf)

    if has_annotations:
        md_content = format_annotations_markdown(item_row, item_anns)
        (item_dir / "annotations.md").write_text(md_content, encoding="utf-8")

    if console:
        console.print(f"  Exported: {dirname}")

    return True


def _resolve_item_pdf(
    attachments: pd.DataFrame,
    item_id: int,
    storage_dir: Path,
    base_dir: Path | None,
    warnings: list[str],
    title: str,
) -> Path | None:
    """Resolve the PDF path for a regular item via its attachments."""
    item_atts = attachments[attachments["parentItemID"] == item_id]
    if item_atts.empty:
        return None

    att = item_atts.iloc[0]
    try:
        pdf_path = resolve_pdf_path(
            storage_dir, att["key"], att["path"], base_dir=base_dir
        )
        if pdf_path.exists():
            return pdf_path
    except ValueError as e:
        warnings.append(f"{title}: {e}")
    return None


def export_reviews(
    db: ZoteroDatabase,
    collection_name: str,
    output_dir: Path,
    base_dir: Path | None = None,
    console=None,
) -> tuple[int, int, list[str]]:
    """Export review items with annotated PDFs and markdown.

    Handles both regular items (with child attachments) and standalone
    attachment items (PDFs added directly to the collection).

    Args:
        db: ZoteroDatabase instance.
        collection_name: Name of the Zotero collection.
        output_dir: Root output directory.
        base_dir: Base directory for linked attachments.
        console: Rich console for output (optional).

    Returns:
        Tuple of (exported_count, skipped_count, warnings).
    """
    storage_dir = db.database_path.parent / "storage"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get regular items in collection
    items = get_collection_items(db, collection_name)
    item_ids = set(items["itemID"])

    # Get standalone attachments in collection
    standalone = get_standalone_attachments(db, collection_name)

    if console:
        console.print(
            f"Found {len(items)} items and {len(standalone)} standalone PDFs "
            f"in '{collection_name}' collection"
        )

    # Get attachments and annotations for regular items
    attachments = extract_attachments(db)
    attachments = attachments[attachments["parentItemID"].isin(item_ids)]
    annotations = get_item_annotations(db, item_ids)

    exported = 0
    skipped = 0
    warnings = []

    # Export regular items
    for _, item in items.iterrows():
        item_id = item["itemID"]
        title = _str_or(item.get("title"), "untitled")
        item_anns = annotations[annotations["paperItemID"] == item_id]

        pdf_path = _resolve_item_pdf(
            attachments, item_id, storage_dir, base_dir, warnings, title
        )

        if _export_item(item, item_anns, pdf_path, output_dir, warnings, console):
            exported += 1
        else:
            skipped += 1

    # Export standalone attachments
    for _, att in standalone.iterrows():
        att_id = att["itemID"]
        title = _strip_review_prefix(
            Path(att["title"]).stem if att["title"] else "untitled"
        )

        # Resolve PDF path
        pdf_path = None
        try:
            pdf_path = resolve_pdf_path(
                storage_dir, att["key"], att["path"], base_dir=base_dir
            )
            if not pdf_path.exists():
                pdf_path = None
        except ValueError as e:
            warnings.append(f"{title}: {e}")

        # Get annotations directly on this attachment
        att_anns_query = f"""
        SELECT * FROM itemAnnotations
        WHERE parentItemID = {att_id}
        ORDER BY sortIndex
        """
        att_anns = db.query(att_anns_query)

        # Build a minimal item-like Series for directory naming and markdown
        item_row = pd.Series({
            "itemID": att_id,
            "title": title,
            "authors": "",
            "year": float("nan"),
        })

        if _export_item(item_row, att_anns, pdf_path, output_dir, warnings, console):
            exported += 1
        else:
            skipped += 1

    return exported, skipped, warnings
