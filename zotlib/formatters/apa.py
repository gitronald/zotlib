"""APA citation formatter."""

from pathlib import Path

import polars as pl


def _check_key_value_exists(row: dict, key: str) -> bool:
    """Check if key exists in row and is not null."""
    return key in row and row[key] is not None


def format_apa_reference(row: dict) -> str:
    """Format a single item as an APA reference string.

    Args:
        row: A dict containing fields: authors, year, title, publication,
             volume, issue, pages, DOI, url, typeName.

    Returns:
        Formatted APA reference string with HTML links.
    """
    reference = f"{row['authors']} ({row['year']}) {row['title']}."
    publication_details = ""

    if _check_key_value_exists(row, "publication"):
        publication_details += f"{row['publication']}"

    if _check_key_value_exists(row, "volume"):
        publication_details += f", {row['volume']}"

    if row["typeName"] == "journalArticle" and publication_details:
        reference += f" _{publication_details}_"

    if _check_key_value_exists(row, "issue"):
        reference += f" ({row['issue']})."

    if _check_key_value_exists(row, "pages"):
        reference = reference[:-1] + f", {row['pages']}."

    # DOI or URL hyperlink
    if _check_key_value_exists(row, "DOI"):
        ahref = f'<a href="https://doi.org/{row["DOI"]}" target="_blank">'
        reference += f" {ahref}{row['DOI']}</a>."
    elif _check_key_value_exists(row, "url"):
        ahref = f'<a href="{row["url"]}" target="_blank">'
        reference += f" {ahref}{row['url']}</a>."

    return reference


def format_cv_as_apa(
    items: pl.DataFrame,
    output_path: Path | str | None = None,
    group_by: str = "typeName",
) -> str:
    """Format CV items as APA references, optionally grouped.

    Args:
        items: DataFrame with CV items.
        output_path: Optional path to write output markdown file.
        group_by: Column to group references by (default: typeName).

    Returns:
        Formatted markdown string with APA references.
    """
    items = items.sort("date", descending=True)

    # Build references
    references = [format_apa_reference(row) for row in items.iter_rows(named=True)]
    items = items.with_columns(pl.Series("reference", references))

    output_lines = []
    for group in items[group_by].unique().sort().to_list():
        gdf = items.filter(pl.col(group_by) == group)
        output_lines.append(f"## {group}\n")
        for ref in gdf["reference"].to_list():
            output_lines.append(f"{ref}\n")
        output_lines.append("")

    output = "\n".join(output_lines)

    if output_path:
        Path(output_path).write_text(output)

    return output
