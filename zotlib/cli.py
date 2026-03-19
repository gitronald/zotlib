"""Command-line interface for zotlib."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

import polars as pl

from zotlib.config import get_database_path
from zotlib.database import ZoteroDatabase
from zotlib.extractors import (
    extract_items,
    extract_creators,
    extract_collections,
    extract_libraries,
    extract_cv_items,
)
from zotlib.backup import create_backup, default_backup_path
from zotlib.covers import generate_covers, generate_thumbnails
from zotlib.formatters.apa import format_cv_as_apa
from zotlib.export import export_collection
from zotlib.schema import ALL_SCHEMAS

app = typer.Typer(
    name="zotlib",
    help="Extract and format bibliographic data from Zotero databases.",
)
console = Console()


@app.command("export-csv")
def export_csv(
    database: Annotated[
        Optional[Path],
        typer.Option("--database", "-d", help="Path to zotero.sqlite"),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory"),
    ] = Path("output/export-csv"),
    collection: Annotated[
        Optional[str],
        typer.Option("--collection", "-c", help="Filter to collection name"),
    ] = None,
):
    """Export bibliographic data from Zotero database as CSV.

    Examples:
        zotlib export-csv
        zotlib export-csv -c publications
        zotlib export-csv -d /path/to/zotero.sqlite -c rer
    """
    db_path = get_database_path(database)
    console.print(f"Using database: {db_path}")

    db = ZoteroDatabase(db_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    if collection:
        items = extract_cv_items(db, collection)
        csv_path = output_dir / f"{collection}.csv"
        items.write_csv(csv_path)
        console.print(f"Saved: {csv_path} ({len(items)} items)")
    else:
        items = extract_items(db)
        creators = extract_creators(db)
        collections = extract_collections(db)
        libraries = extract_libraries(db)

        for name, df in [
            ("items", items),
            ("creators", creators),
            ("collections", collections),
            ("libraries", libraries),
        ]:
            path = output_dir / f"{name}.csv"
            df.write_csv(path)
            console.print(f"Saved: {path} ({len(df)} rows)")


@app.command("export-apa")
def export_apa(
    database: Annotated[
        Optional[Path],
        typer.Option("--database", "-d", help="Path to zotero.sqlite"),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory"),
    ] = Path("output/export-apa"),
    collection: Annotated[
        str,
        typer.Option("--collection", "-c", help="Collection name"),
    ] = ...,
    group_by: Annotated[
        str,
        typer.Option("--group-by", "-g", help="Column to group references by"),
    ] = "typeName",
):
    """Format collection items as APA references.

    Examples:
        zotlib export-apa -c publications
        zotlib export-apa -c publications -g year
    """
    db_path = get_database_path(database)
    console.print(f"Using database: {db_path}")

    db = ZoteroDatabase(db_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    items = extract_cv_items(db, collection)
    apa_path = output_dir / f"{collection}.md"
    format_cv_as_apa(items, apa_path, group_by=group_by)
    console.print(f"Saved: {apa_path} ({len(items)} items)")


@app.command()
def collections(
    database: Annotated[
        Optional[Path],
        typer.Option("--database", "-d", help="Path to zotero.sqlite"),
    ] = None,
):
    """List all collections in the Zotero library."""
    db_path = get_database_path(database)
    db = ZoteroDatabase(db_path)

    colls = extract_collections(db)
    unique_collections = colls.select("collectionID", "collectionName").unique()
    counts = colls.group_by("collectionName").agg(pl.len().alias("items"))
    unique_collections = unique_collections.join(counts, on="collectionName")

    table = Table(title="Zotero Collections")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Items", justify="right")

    for row in unique_collections.iter_rows(named=True):
        table.add_row(
            str(row["collectionID"]),
            row["collectionName"],
            str(row["items"]),
        )

    console.print(table)


@app.command()
def tables(
    database: Annotated[
        Optional[Path],
        typer.Option("--database", "-d", help="Path to zotero.sqlite"),
    ] = None,
):
    """List all tables in the Zotero database (for debugging)."""
    db_path = get_database_path(database)
    db = ZoteroDatabase(db_path)

    table_names = db.get_table_names()
    console.print(f"[bold]Tables in {db_path.name}:[/bold]")
    for name in sorted(table_names):
        console.print(f"  - {name}")


@app.command()
def schema(
    table_name: Annotated[
        Optional[str],
        typer.Argument(help="Table name to show schema for (optional)"),
    ] = None,
):
    """Show Zotero database schema for tables used by zotlib.

    Examples:
        zotlib schema
        zotlib schema items
        zotlib schema itemAnnotations
    """
    wide = Console(width=200, force_terminal=True)
    if table_name:
        # Show specific table
        for s in ALL_SCHEMAS:
            if s.name == table_name:
                table = Table(show_header=True)
                table.add_column("Table", style="cyan bold")
                table.add_column("Column", style="green")
                table.add_column("Type")
                table.add_column("Description")
                for i, (col, col_def) in enumerate(s.columns.items()):
                    table.add_row(
                        s.name if i == 0 else "",
                        col, col_def.type, col_def.description,
                    )
                wide.print(table)
                return
        wide.print(f"[red]Unknown table: {table_name}[/red]")
        wide.print(f"Available: {', '.join(s.name for s in ALL_SCHEMAS)}")
    else:
        # Show all tables
        table = Table(title="Zotero Database Schema")
        table.add_column("Table", style="cyan", no_wrap=True)
        table.add_column("Description", no_wrap=True)
        table.add_column("Columns", no_wrap=True)
        for s in ALL_SCHEMAS:
            cols = ", ".join(s.columns.keys())
            table.add_row(s.name, s.description, cols)
        wide.print(table)


@app.command("export-covers")
def export_covers(
    database: Annotated[
        Optional[Path],
        typer.Option("--database", "-d", help="Path to zotero.sqlite"),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory"),
    ] = Path("output/export-covers"),
    collection: Annotated[
        str,
        typer.Option("--collection", "-c", help="Collection name"),
    ] = ...,
    base_dir: Annotated[
        Optional[Path],
        typer.Option("--pdfs-dir", "-p", help="Directory for linked PDF attachments"),
    ] = None,
    dpi: Annotated[
        int,
        typer.Option("--dpi", help="Image resolution in DPI"),
    ] = 300,
    thumbnail_width: Annotated[
        int,
        typer.Option("--thumb-width", "-w", help="Thumbnail width in pixels"),
    ] = 400,
    no_thumbnails: Annotated[
        bool,
        typer.Option("--no-thumbnails", help="Skip thumbnail generation"),
    ] = False,
):
    """Generate first-page cover images and thumbnails for PDFs in a collection.

    Examples:
        zotlib export-covers -c publications
        zotlib export-covers -c publications -p "/mnt/i/My Drive/zotero-pdfs/"
        zotlib export-covers -c publications --no-thumbnails
    """
    db_path = get_database_path(database)
    console.print(f"Using database: {db_path}")

    db = ZoteroDatabase(db_path)
    fullsize_dir = output_dir / collection / "fullsize"

    cover_paths, skipped = generate_covers(
        db, collection, fullsize_dir, dpi=dpi, base_dir=base_dir
    )
    console.print(f"Generated {len(cover_paths)} cover images in {fullsize_dir}")

    # Generate thumbnails
    if not no_thumbnails:
        thumbs_dir = output_dir / collection / "thumbnails"
        count = generate_thumbnails(fullsize_dir, thumbs_dir, width=thumbnail_width)
        console.print(f"Generated {count} thumbnails ({thumbnail_width}px wide) in {thumbs_dir}")

    # Add cover paths to collection CSV
    csv_dir = Path("output/export-csv")
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_path = csv_dir / f"{collection}.csv"
    if csv_path.exists():
        items_df = pl.read_csv(csv_path)
    else:
        items_df = extract_cv_items(db, collection)

    cover_map = {item_id: str(path) for item_id, path in cover_paths.items()}
    items_df = items_df.with_columns(
        pl.col("itemID").replace_strict(cover_map, default=None).alias("cover")
    )
    items_df.write_csv(csv_path)
    console.print(f"Saved: {csv_path}")

    if skipped:
        console.print(f"[yellow]Skipped {len(skipped)} missing PDFs:[/yellow]")
        for item in skipped:
            console.print(f"  - {item}")


@app.command()
def backup(
    database: Annotated[
        Optional[Path],
        typer.Option("--database", "-d", help="Path to zotero.sqlite"),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output archive path"),
    ] = None,
):
    """Back up the Zotero data directory as a .tar.bz2 archive.

    Examples:
        zotlib backup
        zotlib backup -o ~/backups/zotero-2026-03-02.tar.bz2
        zotlib backup -d /path/to/zotero.sqlite
    """
    db_path = get_database_path(database)
    source_dir = db_path.parent

    if output is None:
        output = default_backup_path()

    output.parent.mkdir(parents=True, exist_ok=True)
    create_backup(source_dir, output, console)


@app.command("export-annotations")
def export_annotations(
    database: Annotated[
        Optional[Path],
        typer.Option("--database", "-d", help="Path to zotero.sqlite"),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory"),
    ] = Path("output/export-annotations"),
    collection: Annotated[
        str,
        typer.Option("--collection", "-c", help="Collection name"),
    ] = ...,
    base_dir: Annotated[
        Optional[Path],
        typer.Option("--pdfs-dir", "-p", help="Directory for linked PDF attachments"),
    ] = None,
):
    """Export collection with baked annotations and markdown notes.

    For each item in the collection, exports a subdirectory containing
    the PDF (with annotations baked in) and a markdown file with YAML
    frontmatter and annotation text.

    Examples:
        zotlib export-annotations -c mycollection
        zotlib export-annotations -c mycollection -p "/mnt/i/My Drive/zotero-pdfs/"
        zotlib export-annotations -c mycollection -o custom/output/path
    """
    db_path = get_database_path(database)
    console.print(f"Using database: {db_path}")

    db = ZoteroDatabase(db_path)
    collection_dir = output_dir / collection

    exported, skipped, warnings = export_collection(
        db, collection, collection_dir, base_dir=base_dir, console=console
    )

    console.print(f"\nExported {exported} items to {collection_dir}")
    if skipped:
        console.print(f"[yellow]Skipped {skipped} items (no PDF or annotations)[/yellow]")
    if warnings:
        console.print(f"[yellow]Warnings:[/yellow]")
        for w in warnings:
            console.print(f"  - {w}")


if __name__ == "__main__":
    app()
