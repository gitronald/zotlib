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


@app.command()
def extract(
    database: Annotated[
        Optional[Path],
        typer.Option("--database", "-d", help="Path to zotero.sqlite"),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory"),
    ] = Path("output"),
    collection: Annotated[
        Optional[str],
        typer.Option("--collection", "-c", help="Filter to collection name"),
    ] = None,
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: csv, apa, both"),
    ] = "both",
):
    """Extract bibliographic data from Zotero database.

    Examples:
        zotlib extract
        zotlib extract -d /path/to/zotero.sqlite -c rer
        zotlib extract --format apa --collection mypapers
    """
    db_path = get_database_path(database)
    console.print(f"Using database: {db_path}")

    db = ZoteroDatabase(db_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    if collection:
        # Extract CV items from specific collection
        items = extract_cv_items(db, collection)
        console.print(f"Extracted {len(items)} items from '{collection}' collection")

        if format in ("csv", "both"):
            csv_path = output_dir / f"{collection}.csv"
            items.write_csv(csv_path)
            console.print(f"Saved: {csv_path}")

        if format in ("apa", "both"):
            apa_path = output_dir / f"{collection}-apa.md"
            format_cv_as_apa(items, apa_path)
            console.print(f"Saved: {apa_path}")
    else:
        # Extract all tables
        items = extract_items(db)
        creators = extract_creators(db)
        collections = extract_collections(db)
        libraries = extract_libraries(db)

        data_dir = output_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        for name, df in [
            ("items", items),
            ("creators", creators),
            ("collections", collections),
            ("libraries", libraries),
        ]:
            path = data_dir / f"{name}.csv"
            df.write_csv(path)
            console.print(f"Saved: {path} ({len(df)} rows)")


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
    if table_name:
        # Show specific table
        for s in ALL_SCHEMAS:
            if s.name == table_name:
                console.print(f"[bold]{s.name}[/bold]: {s.description}\n")
                table = Table(show_header=True)
                table.add_column("Column", style="cyan")
                table.add_column("Description")
                for col, col_def in s.columns.items():
                    table.add_row(col, col_def.description)
                console.print(table)
                return
        console.print(f"[red]Unknown table: {table_name}[/red]")
        console.print(f"Available: {', '.join(s.name for s in ALL_SCHEMAS)}")
    else:
        # Show all tables
        console.print("[bold]Zotero Database Schema (tables used by zotlib)[/bold]\n")
        for s in ALL_SCHEMAS:
            cols = ", ".join(s.columns.keys())
            console.print(f"[cyan]{s.name}[/cyan]: {s.description}")
            console.print(f"  Columns: {cols}\n")


@app.command()
def covers(
    database: Annotated[
        Optional[Path],
        typer.Option("--database", "-d", help="Path to zotero.sqlite"),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory"),
    ] = Path("output"),
    collection: Annotated[
        str,
        typer.Option("--collection", "-c", help="Collection name"),
    ] = ...,
    base_dir: Annotated[
        Optional[Path],
        typer.Option("--base-dir", "-b", help="Base directory for linked attachments"),
    ] = None,
    dpi: Annotated[
        int,
        typer.Option("--dpi", help="Image resolution in DPI"),
    ] = 300,
):
    """Generate first-page cover images for PDFs in a collection.

    Examples:
        zotlib covers -c publications -b "/mnt/i/My Drive/zotero-pdfs/"
        zotlib covers -c mypapers -o covers/ --dpi 150
    """
    db_path = get_database_path(database)
    console.print(f"Using database: {db_path}")

    db = ZoteroDatabase(db_path)
    covers_dir = output_dir / collection

    cover_paths, skipped = generate_covers(
        db, collection, covers_dir, dpi=dpi, base_dir=base_dir
    )
    console.print(f"Generated {len(cover_paths)} cover images in {covers_dir}")

    # Add cover paths to collection CSV
    csv_path = output_dir / f"{collection}.csv"
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
def thumbnails(
    input_dir: Annotated[
        Path,
        typer.Argument(help="Directory containing cover images"),
    ],
    output_dir: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output directory (default: {input_dir}/thumbs)"),
    ] = None,
    width: Annotated[
        int,
        typer.Option("--width", "-w", help="Target width in pixels"),
    ] = 400,
):
    """Resize cover images to thumbnails.

    Examples:
        zotlib thumbnails output/publications
        zotlib thumbnails output/publications -w 200
        zotlib thumbnails output/publications -o output/thumbs
    """
    if output_dir is None:
        output_dir = input_dir / "thumbs"

    count = generate_thumbnails(input_dir, output_dir, width=width)
    console.print(f"Generated {count} thumbnails ({width}px wide) in {output_dir}")


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


@app.command()
def export(
    database: Annotated[
        Optional[Path],
        typer.Option("--database", "-d", help="Path to zotero.sqlite"),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory"),
    ] = Path("output/export"),
    collection: Annotated[
        str,
        typer.Option("--collection", "-c", help="Collection name"),
    ] = ...,
    base_dir: Annotated[
        Optional[Path],
        typer.Option("--base-dir", "-b", help="Base directory for linked attachments"),
    ] = None,
):
    """Export collection with baked annotations and markdown notes.

    For each item in the collection, exports a subdirectory containing
    the PDF (with annotations baked in) and a markdown file with YAML
    frontmatter and annotation text.

    Examples:
        zotlib export -c mycollection
        zotlib export -c mycollection -b "/mnt/i/My Drive/zotero-pdfs/"
        zotlib export -c mycollection -o custom/output/path
    """
    db_path = get_database_path(database)
    console.print(f"Using database: {db_path}")

    db = ZoteroDatabase(db_path)

    exported, skipped, warnings = export_collection(
        db, collection, output_dir, base_dir=base_dir, console=console
    )

    console.print(f"\nExported {exported} items to {output_dir}")
    if skipped:
        console.print(f"[yellow]Skipped {skipped} items (no PDF or annotations)[/yellow]")
    if warnings:
        console.print(f"[yellow]Warnings:[/yellow]")
        for w in warnings:
            console.print(f"  - {w}")


if __name__ == "__main__":
    app()
