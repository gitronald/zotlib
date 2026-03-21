"""Path resolution and filename utilities for Zotero attachments."""

import re
from pathlib import Path, PureWindowsPath


def resolve_pdf_path(
    storage_dir: Path,
    key: str,
    path_field: str,
    pdfs_dir: Path | None = None,
) -> Path:
    """Resolve actual filesystem path from Zotero attachment record.

    Zotero uses three path formats:
    - 'storage:filename.pdf' -> {storage_dir}/{key}/{filename}
    - 'attachments:relative/path.pdf' -> {pdfs_dir}/{relative/path}
    - Absolute Windows path -> converted to WSL /mnt/ path
    """
    if path_field.startswith("storage:"):
        filename = path_field.removeprefix("storage:")
        return storage_dir / key / filename

    if path_field.startswith("attachments:"):
        if pdfs_dir is None:
            raise ValueError(
                "Linked attachment found but no --pdfs-dir provided. "
                "Set the directory for linked PDF attachments."
            )
        relative = path_field.removeprefix("attachments:")
        return pdfs_dir / relative

    # Absolute Windows path (e.g., D:\Dropbox\lit\file.pdf)
    win_path = PureWindowsPath(path_field)
    drive = win_path.drive.rstrip(":").lower()
    return Path(f"/mnt/{drive}") / win_path.relative_to(win_path.anchor)


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = name.strip(". ")
    return name[:200] if name else "untitled"
