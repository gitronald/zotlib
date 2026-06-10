---
id: 1
slug: pdf-covers-pipeline
status: done
branch: dev-pdf-covers
created: 2025-01-31T00:00:00-08:00
concluded: 2026-02-02T08:39:45-08:00
pr: https://github.com/gitronald/zotlib/pull/2
---

# PDF Covers Pipeline

Generate PNG images of the first page of each PDF in a Zotero collection.

## New CLI Command

```bash
zotlib covers -c collection_name          # output to output/{collection}/
zotlib covers -c collection_name -o dir/  # custom output directory
```

## Implementation

### 1. Add `pymupdf` dependency

```bash
poetry add pymupdf
```

PyMuPDF renders PDFs without requiring system-level poppler. It provides high-quality rendering and is fast.

### 2. Add `extract_attachments()` to `zotlib/extractors.py`

Query the `itemAttachments` table to find PDF files for items in a collection:

```sql
SELECT items.itemID, items.key, itemAttachments.parentItemID,
       itemAttachments.contentType, itemAttachments.path
FROM itemAttachments
JOIN items ON itemAttachments.itemID = items.itemID
WHERE itemAttachments.contentType = 'application/pdf'
```

Join with collection items to filter by collection. Return DataFrame with: parentItemID, key, path.

Zotero stores PDFs at: `{zotero_dir}/storage/{key}/{filename}` where:
- `{zotero_dir}` = parent directory of `zotero.sqlite`
- `{key}` = the `items.key` for the attachment item
- `{filename}` = extracted from the `path` column (format: `storage:filename.pdf`)

### 3. Create `zotlib/covers.py`

New module with:

- `resolve_pdf_path(storage_dir, key, path_field)` - resolve the actual filesystem path from Zotero's `storage:filename.pdf` format
- `render_first_page(pdf_path, output_path, dpi=300)` - use PyMuPDF to render page 0 as PNG at 300 DPI
- `generate_covers(db, collection_name, output_dir, dpi=300)` - main pipeline function:
  1. Get items in the collection (reuse existing `extract_collections`)
  2. Get PDF attachments for those items
  3. Get item titles for naming output files
  4. For each PDF: resolve path, render first page, save as `{sanitized_title}.png`
  5. Print progress with Rich console
  6. Return count of generated images and any skipped/missing PDFs

### 4. Add `covers` command to `zotlib/cli.py`

```python
@app.command()
def covers(
    database: ... = None,
    output_dir: ... = Path("output"),
    collection: ... (required),
    dpi: ... = 300,
):
```

Follows the same CLI patterns as the existing `extract` command (same database/output options). Output goes to `output/{collection_name}/` by default.

## Files Modified

| File | Change |
|------|--------|
| `pyproject.toml` | Add `pymupdf` dependency |
| `zotlib/extractors.py` | Add `extract_attachments()` function |
| `zotlib/covers.py` | New module - PDF resolution + rendering |
| `zotlib/cli.py` | Add `covers` command |

## Verification

1. `poetry install` to install pymupdf
2. `zotlib covers -c <collection_name>` with a known collection
3. Check output directory for PNG files
4. Verify PNG quality and that they show the correct first page
