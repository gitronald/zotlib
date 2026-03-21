"""Command-line interface for zotlib."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

import polars as pl

from zotlib.config import (
    get_database_path,
    get_pdfs_dir,
    discover_zotero_database,
    discover_pdfs_dir,
    write_config,
    load_config,
    CONFIG_FILE,
)
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
from zotlib.tables import ALL_SCHEMAS, SCHEMA_MAP

app = typer.Typer(
    name="zotlib",
    help="Extract and format bibliographic data from Zotero databases.",
)
console = Console()


# --- Init ---


@app.command()
def init():
    """Discover Zotero paths and save to zotlib.toml.

    Auto-discovers the Zotero database and linked PDFs directory,
    then writes them to a config file for future use.

    Examples:
        zotlib init
    """
    # Check for existing config
    existing = load_config()
    if existing:
        console.print(f"[yellow]Existing {CONFIG_FILE}:[/yellow]")
        for key, value in existing.items():
            console.print(f"  {key} = {value}")
        overwrite = typer.confirm("Overwrite?", default=False)
        if not overwrite:
            raise typer.Abort()

    # Discover database
    db_path = discover_zotero_database()
    if db_path:
        console.print(f"[green]database:[/green] {db_path}")
    else:
        console.print("[red]Could not find Zotero database[/red]")
        raise typer.Exit(1)

    # Discover PDFs directory
    pdfs_dir = discover_pdfs_dir(check_exists=False)
    if pdfs_dir:
        console.print(f"[green]pdfs_dir:[/green] {pdfs_dir}")
        if not pdfs_dir.exists():
            console.print("[yellow]  Path not currently accessible[/yellow]")
    else:
        console.print("[yellow]Could not find linked PDFs directory[/yellow]")

    # Write config
    config_path = write_config(db_path, pdfs_dir)
    console.print(f"\nSaved to {config_path}")


# --- Explore ---


@app.command("show-tables")
def show_tables(
    table_name: Annotated[
        Optional[str],
        typer.Argument(help="Table name to show schema for (optional)"),
    ] = None,
    database: Annotated[
        Optional[Path],
        typer.Option("--database", "-d", help="Path to zotero.sqlite"),
    ] = None,
    all: Annotated[
        bool,
        typer.Option("--all", "-a", help="List all tables in the database"),
    ] = False,
):
    """Show Zotero database schema for tables used by zotlib.

    Examples:
        zotlib show-tables
        zotlib show-tables items
        zotlib show-tables itemAnnotations
        zotlib show-tables --all
    """
    wide = Console(width=250, force_terminal=True)
    if all:
        db_path = get_database_path(database)
        db = ZoteroDatabase(db_path)
        table_names = db.get_table_names()
        table = Table(title=f"All Tables in {db_path.name}")
        table.add_column("Table", style="cyan", no_wrap=True)
        table.add_column("Description", no_wrap=True)
        table.add_column("Columns", no_wrap=True)
        for name in sorted(table_names):
            schema = SCHEMA_MAP.get(name)
            desc = schema.description if schema else ""
            cols = ", ".join(schema.columns.keys()) if schema else ""
            table.add_row(name, desc, cols)
        wide.print(table)
    elif table_name:
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



@app.command("show-collections")
def show_collections(
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


# --- Export ---


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
    if base_dir is None:
        base_dir = get_pdfs_dir()
        if base_dir:
            console.print(f"Using linked PDFs directory: {base_dir}")
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
    if base_dir is None:
        base_dir = get_pdfs_dir()
        if base_dir:
            console.print(f"Using linked PDFs directory: {base_dir}")
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


# --- Manage ---


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


if __name__ == "__main__":
    app()
