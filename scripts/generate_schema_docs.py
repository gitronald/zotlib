#!/usr/bin/env python3
"""Generate docs/schema.md from schema.py definitions."""

from pathlib import Path

from zotlib.tables import ALL_SCHEMAS


def generate_schema_markdown() -> str:
    """Generate markdown documentation for all schema tables."""
    lines = [
        "# Zotero Database Schema",
        "",
        "Schema definitions for Zotero SQLite database tables used by zotlib.",
        "",
    ]

    for table in ALL_SCHEMAS:
        # Table header
        lines.append(f"## {table.name}")
        lines.append("")
        lines.append(table.description)
        lines.append("")

        # Column table
        lines.append("| Name | Type | Description |")
        lines.append("|------|------|-------------|")
        for col_name, col in table.columns.items():
            lines.append(f"| {col_name} | {col.type} | {col.description} |")
        lines.append("")

    return "\n".join(lines)


def main():
    """Generate and write schema documentation."""
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    output_path = docs_dir / "schema.md"
    content = generate_schema_markdown()
    output_path.write_text(content)

    print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
