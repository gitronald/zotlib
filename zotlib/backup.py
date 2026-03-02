"""Backup Zotero data directory as a compressed archive."""

import os
import tarfile
from datetime import date
from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)


def get_directory_stats(source_dir: Path) -> tuple[int, int]:
    """Walk a directory and return (file_count, total_bytes)."""
    file_count = 0
    total_bytes = 0
    for dirpath, _dirnames, filenames in os.walk(source_dir):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            try:
                total_bytes += filepath.stat().st_size
                file_count += 1
            except OSError:
                continue
    return file_count, total_bytes


def default_backup_path() -> Path:
    """Generate default backup path in data/backups/."""
    today = date.today().isoformat()
    return Path("data") / "backups" / f"zotero-{today}.tar.bz2"


def create_backup(
    source_dir: Path,
    output_path: Path,
    console: Console,
) -> Path:
    """Archive a Zotero data directory as .tar.bz2.

    Args:
        source_dir: The Zotero data directory to archive.
        output_path: Path for the output .tar.bz2 file.
        console: Rich console for progress output.

    Returns:
        Path to the created archive.

    Raises:
        FileNotFoundError: If source_dir does not exist.
        FileExistsError: If output_path already exists.
    """
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Zotero directory not found: {source_dir}")

    if output_path.exists():
        raise FileExistsError(f"Output file already exists: {output_path}")

    file_count, total_bytes = get_directory_stats(source_dir)
    size_mb = total_bytes / (1024 * 1024)
    console.print(f"Source: {source_dir}")
    console.print(f"Files: {file_count:,} ({size_mb:,.1f} MB)")

    archived = 0
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Archiving", total=file_count)

        with tarfile.open(output_path, "w:bz2") as tar:
            for dirpath, _dirnames, filenames in os.walk(source_dir):
                rel_dir = Path(dirpath).relative_to(source_dir.parent)
                tar.add(dirpath, arcname=str(rel_dir), recursive=False)

                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    arcname = str(rel_dir / filename)
                    try:
                        tar.add(filepath, arcname=arcname)
                        archived += 1
                        progress.update(task, completed=archived)
                    except OSError:
                        continue

    archive_mb = output_path.stat().st_size / (1024 * 1024)
    console.print(f"Saved: {output_path} ({archive_mb:,.1f} MB)")
    return output_path
