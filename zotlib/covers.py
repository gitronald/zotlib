"""Generate cover images from first page of PDFs in a Zotero collection."""

import re
from pathlib import Path, PureWindowsPath

import fitz
import polars as pl

from zotlib.database import ZoteroDatabase
from zotlib.extractors import extract_attachments, extract_collections, extract_items


def resolve_pdf_path(
    storage_dir: Path,
    key: str,
    path_field: str,
    base_dir: Path | None = None,
) -> Path:
    """Resolve actual filesystem path from Zotero attachment record.

    Zotero uses three path formats:
    - 'storage:filename.pdf' -> {storage_dir}/{key}/{filename}
    - 'attachments:relative/path.pdf' -> {base_dir}/{relative/path}
    - Absolute Windows path -> converted to WSL /mnt/ path
    """
    if path_field.startswith("storage:"):
        filename = path_field.removeprefix("storage:")
        return storage_dir / key / filename

    if path_field.startswith("attachments:"):
        if base_dir is None:
            raise ValueError(
                "Linked attachment found but no --pdfs-dir provided. "
                "Set the directory for linked PDF attachments."
            )
        relative = path_field.removeprefix("attachments:")
        return base_dir / relative

    # Absolute Windows path (e.g., D:\Dropbox\lit\file.pdf)
    win_path = PureWindowsPath(path_field)
    drive = win_path.drive.rstrip(":").lower()
    return Path(f"/mnt/{drive}") / win_path.relative_to(win_path.anchor)


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = name.strip(". ")
    return name[:200] if name else "untitled"


def render_first_page(pdf_path: Path, output_path: Path, dpi: int = 300) -> None:
    """Render the first page of a PDF as a PNG image."""
    doc = fitz.open(pdf_path)
    page = doc[0]
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix)
    pixmap.save(str(output_path))
    doc.close()


def generate_thumbnails(
    input_dir: Path,
    output_dir: Path,
    width: int = 400,
) -> int:
    """Resize cover images to thumbnail size.

    Args:
        input_dir: Directory containing full-size cover PNGs.
        output_dir: Directory to write thumbnails.
        width: Target width in pixels (height scales proportionally).

    Returns:
        Number of thumbnails generated.
    """
    from PIL import Image

    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for png_path in sorted(input_dir.glob("*-cover.png")):
        img = Image.open(png_path)
        scale = width / img.width
        height = int(img.height * scale)
        thumb = img.resize((width, height), Image.Resampling.LANCZOS)

        thumb_name = png_path.stem.replace("-cover", "-thumb") + ".png"
        thumb.save(output_dir / thumb_name)
        count += 1

    return count


def generate_covers(
    db: ZoteroDatabase,
    collection_name: str,
    output_dir: Path,
    dpi: int = 300,
    base_dir: Path | None = None,
) -> tuple[dict[int, Path], list[str]]:
    """Generate first-page cover images for all PDFs in a collection.

    Returns:
        Tuple of (dict mapping parentItemID to cover image path,
                  list of skipped item descriptions).
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
    title_map = dict(zip(
        items_in_collection["itemID"].to_list(),
        items_in_collection["title"].to_list(),
    ))

    # Get PDF attachments
    attachments = extract_attachments(db)
    attachments = attachments.filter(pl.col("parentItemID").is_in(list(item_ids)))

    output_dir.mkdir(parents=True, exist_ok=True)

    cover_paths: dict[int, Path] = {}
    skipped = []

    for row in attachments.iter_rows(named=True):
        parent_id = row["parentItemID"]
        title = title_map.get(parent_id, f"item_{parent_id}")

        pdf_path = resolve_pdf_path(
            storage_dir, row["key"], row["path"], base_dir=base_dir
        )
        if not pdf_path.exists():
            skipped.append(f"{title} ({pdf_path})")
            continue

        bibkey = pdf_path.stem
        output_path = output_dir / f"{bibkey}-cover.png"
        render_first_page(pdf_path, output_path, dpi=dpi)
        cover_paths[parent_id] = output_path

    return cover_paths, skipped
