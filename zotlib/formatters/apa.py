"""APA citation formatter."""

from pathlib import Path

import pandas as pd


def _check_key_value_exists(row: pd.Series, key: str) -> bool:
    """Check if key exists in row and is not null."""
    return key in row.index and not pd.isna(row[key])


def format_apa_reference(row: pd.Series) -> str:
    """Format a single item as an APA reference string.

    Args:
        row: A row containing fields: authors, year, title, publication,
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
    items: pd.DataFrame,
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
    items = items.sort_values("date", ascending=False)
    items["reference"] = items.apply(format_apa_reference, axis=1)

    output_lines = []
    for group, gdf in items.groupby(group_by):
        output_lines.append(f"## {group}\n")
        for ref in gdf["reference"]:
            output_lines.append(f"{ref}\n")
        output_lines.append("")

    output = "\n".join(output_lines)

    if output_path:
        Path(output_path).write_text(output)

    return output
