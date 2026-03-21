"""Export collection items with annotations and markdown notes."""

import json
import shutil
from pathlib import Path

import fitz
import polars as pl

from zotlib.covers import resolve_pdf_path, sanitize_filename
from zotlib.database import ZoteroDatabase
from zotlib.extractors import (
    _add_authors,
    _clean_items,
    extract_attachments,
    extract_collections,
    extract_creators,
    extract_items,
    extract_tags,
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

# Zotero hex colors to readable labels (matches scripts/extract-annotations.js)
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
    if value is None:
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


def convert_zotero_rect(rect: list[float], page_height: float) -> fitz.Rect:
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
) -> pl.DataFrame:
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
    coll = collections.filter(pl.col("collectionName") == collection_name)
    if len(coll) == 0:
        raise ValueError(f"Collection not found: {collection_name}")

    coll_item_ids = coll["itemID"]
    coll_items = items.filter(pl.col("itemID").is_in(coll_item_ids))

    # Exclude attachment and note types (handled separately)
    coll_items = coll_items.filter(~pl.col("typeName").is_in(["attachment", "note"]))

    # Add authors
    coll_items = _add_authors(coll_items, creators)

    # Add tags (comma-separated)
    item_tags = tags.group_by("itemID").agg(pl.col("name").sort().str.join(", ").alias("tags"))
    coll_items = coll_items.join(item_tags, on="itemID", how="left")

    # Clean dates
    coll_items = _clean_items(coll_items)

    return coll_items


def get_standalone_attachments(
    db: ZoteroDatabase,
    collection_name: str,
) -> pl.DataFrame:
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
        cursor = conn.cursor()
        cursor.execute(query, [collection_name])
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return pl.DataFrame({col: [row[i] for row in rows] for i, col in enumerate(columns)})


def get_item_annotations(
    db: ZoteroDatabase,
    item_ids: set[int],
) -> pl.DataFrame:
    """Get annotations for items, joined through the attachment chain.

    The join path: annotation.parentItemID -> attachment.itemID,
    attachment.parentItemID -> paper.itemID.

    Args:
        db: ZoteroDatabase instance.
        item_ids: Set of parent item IDs (the papers).

    Returns:
        DataFrame with annotations plus paperItemID column.
    """
    placeholders = ",".join("?" * len(item_ids))
    query = f"""
    SELECT ia.*, iatt.parentItemID AS paperItemID
    FROM itemAnnotations ia
    JOIN itemAttachments iatt ON ia.parentItemID = iatt.itemID
    WHERE iatt.parentItemID IN ({placeholders})
    ORDER BY ia.sortIndex
    """
    return db.query(query, list(item_ids))


def make_item_dirname(item_row: dict) -> str:
    """Build a subdirectory name from item metadata.

    Format: {first-author-last}-{year}-{short-title}
    """
    authors = _str_or(item_row.get("authors"))
    first_author = authors.split(",")[0].strip().split()[-1] if authors else "unknown"

    year = item_row.get("year")
    year_str = str(int(year)) if year is not None else "nd"

    title = _strip_review_prefix(_str_or(item_row.get("title"), "untitled"))
    short_title = title[:60].strip()

    raw = f"{first_author}-{year_str}-{short_title}"
    return sanitize_filename(raw).lower().replace(" ", "-")


def bake_annotations(
    pdf_path: Path,
    annotations_df: pl.DataFrame,
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

    for ann in annotations_df.iter_rows(named=True):
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
            warnings.append(f"Page {page_index} out of range for annotation {ann['itemID']}")
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
    item_row: dict,
    annotations_df: pl.DataFrame,
) -> str:
    """Generate markdown with YAML frontmatter and page-grouped annotations.

    Args:
        item_row: Dict with item metadata (title, authors, year, etc.).
        annotations_df: DataFrame of annotations sorted by sortIndex.

    Returns:
        Markdown string.
    """
    lines = []

    # YAML frontmatter
    title = _strip_review_prefix(_str_or(item_row.get("title"), "Untitled"))
    authors = _str_or(item_row.get("authors"))
    year = item_row.get("year")
    year_str = str(int(year)) if year is not None else ""
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

    for ann in annotations_df.iter_rows(named=True):
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


def _resolve_attachment_pdfs(
    attachments: pl.DataFrame,
    item_id: int,
    storage_dir: Path,
    pdfs_dir: Path | None,
    warnings: list[str],
    title: str,
) -> list[tuple[int, Path]]:
    """Resolve PDF paths for all attachments of an item.

    Returns list of (attachment_itemID, resolved_path) tuples.
    """
    item_atts = attachments.filter(pl.col("parentItemID") == item_id)
    resolved = []
    for att in item_atts.iter_rows(named=True):
        try:
            pdf_path = resolve_pdf_path(storage_dir, att["key"], att["path"], pdfs_dir=pdfs_dir)
            if pdf_path.exists():
                resolved.append((att["itemID"], pdf_path))
        except ValueError as e:
            warnings.append(f"{title}: {e}")
    return resolved


def _export_item(
    item_row: dict,
    all_anns: pl.DataFrame,
    att_pdfs: list[tuple[int, Path]],
    output_dir: Path,
    warnings: list[str],
    console=None,
) -> bool:
    """Export a single item with per-attachment annotation baking.

    Args:
        item_row: Dict with item metadata.
        all_anns: DataFrame of annotations with parentItemID column
            pointing to specific attachments.
        att_pdfs: List of (attachment_itemID, pdf_path) tuples.
        output_dir: Root output directory.
        warnings: List to append warnings to.
        console: Rich console for output.

    Returns True if exported.
    """
    title = _str_or(item_row.get("title"), "untitled")
    has_annotations = len(all_anns) > 0
    has_pdfs = len(att_pdfs) > 0

    if not has_pdfs and not has_annotations:
        warnings.append(f"No PDF or annotations: {title}")
        return False

    dirname = make_item_dirname(item_row)
    item_dir = output_dir / dirname
    item_dir.mkdir(parents=True, exist_ok=True)

    if has_pdfs:
        # First PDF with annotations is "paper.pdf", rest are numbered
        pdf_names = iter(["paper.pdf"] + [f"paper-{i}.pdf" for i in range(2, 20)])
        for att_id, pdf_path in att_pdfs:
            output_name = next(pdf_names)
            output_pdf = item_dir / output_name

            # Get annotations for this specific attachment
            att_anns = all_anns.filter(pl.col("parentItemID") == att_id)

            if len(att_anns) > 0:
                ann_warnings = bake_annotations(pdf_path, att_anns, output_pdf)
                warnings.extend(ann_warnings)
            else:
                shutil.copy2(pdf_path, output_pdf)

    if has_annotations:
        md_content = format_annotations_markdown(item_row, all_anns)
        (item_dir / "annotations.md").write_text(md_content, encoding="utf-8")

    if console:
        console.print(f"  Exported: {dirname}")

    return True


def export_collection(
    db: ZoteroDatabase,
    collection_name: str,
    output_dir: Path,
    pdfs_dir: Path | None = None,
    console=None,
) -> tuple[int, int, list[str]]:
    """Export collection items with annotated PDFs and markdown.

    Handles both regular items (with child attachments) and standalone
    attachment items (PDFs added directly to the collection).

    Args:
        db: ZoteroDatabase instance.
        collection_name: Name of the Zotero collection.
        output_dir: Root output directory.
        pdfs_dir: Base directory for linked attachments.
        console: Rich console for output (optional).

    Returns:
        Tuple of (exported_count, skipped_count, warnings).
    """
    storage_dir = db.database_path.parent / "storage"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get regular items in collection
    items = get_collection_items(db, collection_name)
    item_ids = set(items["itemID"].to_list())

    # Get standalone attachments in collection
    standalone = get_standalone_attachments(db, collection_name)

    if console:
        console.print(
            f"Found {len(items)} items and {len(standalone)} standalone PDFs "
            f"in '{collection_name}' collection"
        )

    # Get attachments and annotations for regular items
    attachments = extract_attachments(db)
    attachments = attachments.filter(pl.col("parentItemID").is_in(list(item_ids)))
    annotations = get_item_annotations(db, item_ids)

    exported = 0
    skipped = 0
    warnings = []

    # Export regular items
    for item in items.iter_rows(named=True):
        item_id = item["itemID"]
        title = _str_or(item.get("title"), "untitled")
        item_anns = annotations.filter(pl.col("paperItemID") == item_id)

        att_pdfs = _resolve_attachment_pdfs(
            attachments, item_id, storage_dir, pdfs_dir, warnings, title
        )

        if _export_item(item, item_anns, att_pdfs, output_dir, warnings, console):
            exported += 1
        else:
            skipped += 1

    # Export standalone attachments
    for att in standalone.iter_rows(named=True):
        att_id = att["itemID"]
        title = _strip_review_prefix(Path(att["title"]).stem if att["title"] else "untitled")

        # Resolve PDF path
        att_pdfs = []
        try:
            pdf_path = resolve_pdf_path(storage_dir, att["key"], att["path"], pdfs_dir=pdfs_dir)
            if pdf_path.exists():
                att_pdfs = [(att_id, pdf_path)]
        except ValueError as e:
            warnings.append(f"{title}: {e}")

        # Get annotations directly on this attachment
        att_anns_query = """
        SELECT * FROM itemAnnotations
        WHERE parentItemID = ?
        ORDER BY sortIndex
        """
        att_anns = db.query(att_anns_query, [att_id])

        # Build a minimal item-like dict for directory naming and markdown
        item_row = {
            "itemID": att_id,
            "title": title,
            "authors": "",
            "year": None,
        }

        if _export_item(item_row, att_anns, att_pdfs, output_dir, warnings, console):
            exported += 1
        else:
            skipped += 1

    return exported, skipped, warnings
