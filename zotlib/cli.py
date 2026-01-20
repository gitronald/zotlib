"""Command-line interface for zotlib."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from zotlib.config import get_database_path
from zotlib.database import ZoteroDatabase
from zotlib.extractors import (
    extract_items,
    extract_creators,
    extract_collections,
    extract_libraries,
    extract_cv_items,
)
from zotlib.formatters.apa import format_cv_as_apa
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
            csv_path = output_dir / "cv.csv"
            items.to_csv(csv_path, index=False)
            console.print(f"Saved: {csv_path}")

        if format in ("apa", "both"):
            apa_path = output_dir / "apa.md"
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
            df.to_csv(path, index=False)
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
    unique_collections = colls[["collectionID", "collectionName"]].drop_duplicates()
    counts = colls.groupby("collectionName").size().reset_index(name="items")
    unique_collections = unique_collections.merge(counts, on="collectionName")

    table = Table(title="Zotero Collections")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Items", justify="right")

    for _, row in unique_collections.iterrows():
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
    """Show Zotero database schema for tables used by zotlib."""
    if table_name:
        # Show specific table
        for s in ALL_SCHEMAS:
            if s["table"] == table_name:
                console.print(f"[bold]{s['table']}[/bold]: {s['description']}\n")
                table = Table(show_header=True)
                table.add_column("Column", style="cyan")
                table.add_column("Description")
                for col, desc in s["columns"].items():
                    table.add_row(col, desc)
                console.print(table)
                return
        console.print(f"[red]Unknown table: {table_name}[/red]")
        console.print(f"Available: {', '.join(s['table'] for s in ALL_SCHEMAS)}")
    else:
        # Show all tables
        console.print("[bold]Zotero Database Schema (tables used by zotlib)[/bold]\n")
        for s in ALL_SCHEMAS:
            cols = ", ".join(s["columns"].keys())
            console.print(f"[cyan]{s['table']}[/cyan]: {s['description']}")
            console.print(f"  Columns: {cols}\n")


if __name__ == "__main__":
    app()
