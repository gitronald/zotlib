"""Generate cover images from first page of PDFs in a Zotero collection."""

from collections.abc import Callable
from pathlib import Path

import fitz
import polars as pl

from zotlib.database import ZoteroDatabase
from zotlib.extractors import extract_attachments, extract_collections, extract_items
from zotlib.paths import resolve_pdf_path


def write_atomic(output_path: Path, write: Callable[[Path], None]) -> None:
    """Write output_path through a sibling partial file renamed into place.

    An interrupted write leaves no truncated file at output_path, which
    is_current would otherwise take as up to date on every later run.
    """
    partial = output_path.with_name(f"{output_path.stem}.partial{output_path.suffix}")
    try:
        write(partial)
        partial.replace(output_path)
    finally:
        partial.unlink(missing_ok=True)


def render_first_page(pdf_path: Path, output_path: Path, dpi: int = 300) -> None:
    """Render the first page of a PDF as a PNG image."""
    doc = fitz.open(pdf_path)
    try:
        page = doc[0]
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix)
        write_atomic(output_path, lambda path: pixmap.save(str(path)))
    finally:
        doc.close()


def is_current(output_path: Path, source_path: Path) -> bool:
    """Whether output_path exists and is at least as new as source_path."""
    return output_path.exists() and output_path.stat().st_mtime >= source_path.stat().st_mtime


def generate_thumbnails(
    input_dir: Path,
    output_dir: Path,
    width: int = 400,
    force: bool = False,
) -> int:
    """Resize cover images to thumbnail size.

    A thumbnail at least as new as its cover is kept, unless force is set.

    Args:
        input_dir: Directory containing full-size cover PNGs.
        output_dir: Directory to write thumbnails.
        width: Target width in pixels (height scales proportionally).
        force: Regenerate every thumbnail.

    Returns:
        Number of thumbnails written.
    """
    from PIL import Image

    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for png_path in sorted(input_dir.glob("*-cover.png")):
        thumb_path = output_dir / (png_path.stem.replace("-cover", "-thumb") + ".png")
        if not force and is_current(thumb_path, png_path):
            continue

        img = Image.open(png_path)
        scale = width / img.width
        height = int(img.height * scale)
        thumb = img.resize((width, height), Image.Resampling.LANCZOS)

        write_atomic(thumb_path, lambda path: thumb.save(path, format="PNG"))
        count += 1

    return count


def generate_covers(
    db: ZoteroDatabase,
    collection_name: str,
    output_dir: Path,
    dpi: int = 300,
    pdfs_dir: Path | None = None,
    force: bool = False,
) -> tuple[dict[int, Path], list[str], int]:
    """Generate first-page cover images for all PDFs in a collection.

    A cover at least as new as its PDF is kept, unless force is set, so a
    rerun writes only the covers whose PDF changed.

    Returns:
        Tuple of (dict mapping parentItemID to cover image path,
                  list of skipped item descriptions,
                  number of covers rendered).
    """
    storage_dir = db.database_path.parent / "storage"

    # Get items in the collection
    collections = extract_collections(db)
    collection_items = collections.filter(pl.col("collectionName") == collection_name)
    if len(collection_items) == 0:
        raise ValueError(f"Collection not found: {collection_name}")

    item_ids = set(collection_items["itemID"].to_list())

    # Get all items for titles
    items = extract_items(db)
    items_in_collection = items.filter(pl.col("itemID").is_in(list(item_ids)))
    title_map = dict(
        zip(
            items_in_collection["itemID"].to_list(),
            items_in_collection["title"].to_list(),
        )
    )

    # Get PDF attachments
    attachments = extract_attachments(db)
    attachments = attachments.filter(pl.col("parentItemID").is_in(list(item_ids)))

    output_dir.mkdir(parents=True, exist_ok=True)

    cover_paths: dict[int, Path] = {}
    skipped = []
    rendered = 0

    for row in attachments.iter_rows(named=True):
        parent_id = row["parentItemID"]
        title = title_map.get(parent_id, f"item_{parent_id}")

        pdf_path = resolve_pdf_path(storage_dir, row["key"], row["path"], pdfs_dir=pdfs_dir)
        if not pdf_path.exists():
            skipped.append(f"{title} ({pdf_path})")
            continue

        bibkey = pdf_path.stem
        output_path = output_dir / f"{bibkey}-cover.png"
        if force or not is_current(output_path, pdf_path):
            render_first_page(pdf_path, output_path, dpi=dpi)
            rendered += 1
        cover_paths[parent_id] = output_path

    return cover_paths, skipped, rendered
