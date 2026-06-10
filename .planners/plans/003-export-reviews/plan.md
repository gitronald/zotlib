---
id: 3
slug: export-reviews
status: done
branch: feature/export-annotated-pdfs
created: 2026-03-02T00:00:00-08:00
concluded: 2026-03-06T17:39:39-08:00
pr: https://github.com/gitronald/zotlib/pull/4
---

# Export Reviews Command

## Context

Review papers in the Zotero "writing/reviews" collection need to be exported to `./outputs/reviews/` with annotated PDFs and markdown annotation files. Zotero 7 stores PDF annotations in its SQLite database (not embedded in the PDF), so exporting requires baking annotations into PDF copies and generating structured markdown.

## Approach: SQLite + PyMuPDF

Read annotations from the `itemAnnotations` table and use PyMuPDF to bake them into PDF copies. This doesn't require Zotero to be running and follows the same patterns as existing commands (covers, extract).

The existing `zotero-js/` scripts serve as the **reference format** for markdown output — color labels, page grouping, annotation type formatting — but the implementation is pure Python via SQLite queries.

## Output Structure

```
outputs/reviews/
├── smith-2024-title-of-paper/
│   ├── paper.pdf            # PDF with annotations baked in
│   └── annotations.md       # YAML frontmatter + annotations
```

## Files to Create

### `zotlib/reviews.py` — core logic

Functions:
- `get_collection_items(db, collection_name)` — items in a collection with metadata, authors, tags
- `get_item_annotations(db, item_ids)` — annotations joined through attachment→paper chain
- `bake_annotations(pdf_path, annotations_df, output_path)` — copy PDF with annotations rendered via PyMuPDF
- `format_annotations_markdown(item_row, annotations_df)` — YAML frontmatter + page-grouped annotations
- `export_reviews(db, collection_name, output_dir, base_dir)` — main orchestrator

Reuses from existing code:
- `covers.py`: `resolve_pdf_path()`, `sanitize_filename()`
- `extractors.py`: `extract_items()`, `extract_collections()`, `extract_creators()`, `extract_attachments()`
- `config.py`: `get_database_path()`

### `tests/test_reviews.py` — unit tests

Test coordinate conversion, markdown formatting, YAML structure, annotation type handling.

## Files to Modify

### `zotlib/extractors.py`

Add two new extractors:

```python
def extract_annotations(db: ZoteroDatabase) -> pd.DataFrame:
    """Extract PDF annotations from itemAnnotations table."""
    return db.query("SELECT * FROM itemAnnotations")

def extract_tags(db: ZoteroDatabase) -> pd.DataFrame:
    """Extract item tags with tag names."""
    query = """
    SELECT itemTags.itemID, itemTags.tagID, itemTags.type, tags.name
    FROM itemTags
    JOIN tags ON itemTags.tagID = tags.tagID
    """
    return db.query(query)
```

### `zotlib/cli.py`

Add `reviews` command:

```python
@app.command()
def reviews(
    database: ... = None,
    output_dir: ... = Path("outputs/reviews"),
    collection: ... = "reviews",
    base_dir: ... = None,
):
    """Export review papers with annotations and markdown notes."""
```

### `zotlib/schema.py`

Add `ITEM_ANNOTATIONS`, `ITEM_TAGS`, `TAGS` table definitions to `ALL_SCHEMAS`.

## Key Implementation Details

### Annotation baking (PyMuPDF)

Zotero stores annotation positions as JSON with `pageIndex` and `rects` arrays. PyMuPDF uses top-left origin vs PDF's bottom-left origin, so Y coordinates need flipping:

```python
def convert_zotero_rect(rect, page_height):
    x0, y0_bot, x1, y1_bot = rect
    return fitz.Rect(x0, page_height - y1_bot, x1, page_height - y0_bot)
```

Annotation types:
- **highlight** → `page.add_highlight_annot(quads)` with color
- **underline** → `page.add_underline_annot(quads)`
- **note** → `page.add_text_annot(point, comment)`
- **image/ink** → skip with warning

### Markdown format (matching zotero-js reference)

```yaml
---
title: "Paper Title"
authors: "First Author, Second Author"
year: 2024
publication: "Journal Name"
doi: "10.xxxx/xxxxx"
date_added: "2024-01-15"
tags: [tag1, tag2]
annotation_count: 15
---
```

Body grouped by page with color-labeled highlights, blockquoted text, and notes — same format as `extract-annotations.js`.

### Collection resolution

Query the `collections` table for `collectionName == 'reviews'`. The parent "writing" collection is context for the user; the query just needs the leaf name.

### Subdirectory naming

`{first_author_last}-{year}-{short_title}` via `sanitize_filename()`.

### Error handling

- Missing PDF → skip PDF, still export annotations.md, warn
- No annotations → copy PDF as-is, skip annotations.md
- Neither → skip entirely, warn
- Bad position JSON → skip that annotation, warn

## Commit Plan

1. Add `extract_annotations()`, `extract_tags()` to extractors + schema updates
2. Create `zotlib/reviews.py` with core logic
3. Add `reviews` command to CLI
4. Add tests

## Verification

```bash
zotlib reviews -c reviews
ls outputs/reviews/
# Check a subdirectory has paper.pdf and annotations.md
# Open paper.pdf to verify annotations are visible
# Check annotations.md has correct YAML frontmatter and content
```

## Retrospective

- Multi-attachment bug: annotations keyed to specific attachments (annotation.parentItemID -> attachment.itemID), not parent items. Original code grabbed first PDF and baked all annotations onto it.
- Zotero JS async pitfall: async IIFEs return undefined in console. Use top-level code with `return output`.
- Subcollections: `getByLibrary()` only returns top-level. Use `Collections.get(id)` for subcollections.
- WSL <-> Zotero: debug endpoint binds to Windows localhost, not WSL's. Must paste scripts into console.
- Naming: generalizing early (export vs reviews) prevents rename churn later.
- Renamed reviews.py -> export.py, export_reviews -> export_collection, CLI reviews -> export.
