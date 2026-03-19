# zotlib

Tools for extracting and formatting bibliographic data from Zotero databases.

## Project Structure

```
zotlib/
├── zotlib/                      # Python library
│   ├── cli.py                   # CLI commands
│   ├── config.py                # Database path discovery
│   ├── database.py              # SQLite interface
│   ├── extractors.py            # Data extraction functions
│   ├── export.py                # Collection export (annotations + PDFs)
│   ├── backup.py                # Zotero directory backup
│   ├── schema.py                # Zotero database schema definitions
│   ├── covers.py                # PDF cover generation
│   └── formatters/apa.py        # APA citation formatter
├── zotero-js/                   # Zotero JavaScript scripts
│   ├── extract-annotations.js   # Interactive annotation extractor
│   ├── extract-annotations-cli.js
│   ├── extract-annotations-debug.js
│   ├── create-parents-for-standalone.js
│   └── run-extract.sh           # Shell wrapper
├── scripts/                     # Utility scripts
│   └── generate_schema_docs.py  # Generate docs/schema.md
├── docs/                        # Documentation
│   └── schema.md                # Database schema reference
├── tests/                       # Test suite
└── pyproject.toml               # Project configuration
```

## Installation

```bash
uv sync
```

## Configuration

The database path can be configured via:

1. **CLI flag**: `--database /path/to/zotero.sqlite`
2. **Environment variable**: `ZOTERO_DATABASE=/path/to/zotero.sqlite`
3. **Auto-discovery**: Checks common locations (Linux, WSL, macOS)

## CLI Commands

### Extract and format

```bash
# Extract all data with auto-discovered database
zotlib extract

# Extract CV items from a specific collection as APA
zotlib extract -c rer -f apa

# List available collections
zotlib collections

# List database tables
zotlib tables

# Show schema for tables used by zotlib
zotlib schema
zotlib schema itemAnnotations

# Generate cover images from first page of PDFs
zotlib covers -c publications -b "/path/to/linked-pdfs/"

# Resize cover images to thumbnails
zotlib thumbnails output/publications
zotlib thumbnails output/publications -w 200

# Back up the Zotero data directory
zotlib backup
```

### Export annotated PDFs

```bash
# Export a collection with annotated PDFs and markdown notes
zotlib export -c mycollection

# Export with linked attachment resolution
zotlib export -c mycollection -b "/path/to/linked-pdfs/"

# Custom output directory
zotlib export -c mycollection -o custom/output/path
```

Each item in the collection is exported as a subdirectory containing:
- `paper.pdf` — PDF with annotations baked in via PyMuPDF
- `paper-2.pdf`, etc. — additional PDFs (e.g., supplementary materials)
- `annotations.md` — markdown with YAML frontmatter and page-grouped annotations

Features:
- Multi-attachment support: each PDF gets only its own annotations
- Standalone attachment support: PDFs added directly to a collection
- Linked attachment resolution via `--pdfs-dir`
- "REVIEW: " prefix stripping from titles

### Python API

```python
from zotlib import ZoteroDatabase, extract_cv_items, format_cv_as_apa

db = ZoteroDatabase("/path/to/zotero.sqlite")
items = extract_cv_items(db, collection_name="mypapers")
apa_output = format_cv_as_apa(items, output_path="output/apa.md")
```

## Zotero JavaScript Scripts

Utilities for Zotero's JavaScript console (Tools > Developer > Run JavaScript).

### create-parents-for-standalone.js

Creates parent document items for standalone PDF attachments in a collection. Useful when PDFs were added directly without metadata — creates a parent item using the filename as the title and re-parents the attachment.

### extract-annotations.js

Interactive annotation extractor with file save dialog. Select an item, run the script, and save annotations as markdown.

### extract-annotations-cli.js

Headless version that writes to `~/Desktop/zotero-annotations/`. Can be invoked via Zotero's HTTP debug API:

```bash
./zotero-js/run-extract.sh
```

Requires: Settings > Advanced > "Allow other applications to communicate with Zotero"

## Annotation Format

### Types

| Type | Extracted Data |
|------|----------------|
| Highlight | Text + comment + color |
| Note | Comment text |
| Underline | Text + comment |
| Image | Comment only (image not exported) |

### Color Labels

| Hex Code | Label |
|----------|-------|
| `#ffd400` | yellow |
| `#ff6666` | red |
| `#5fb236` | green |
| `#2ea8e5` | blue |
| `#a28ae5` | purple |
| `#e56eee` | magenta |
| `#f19837` | orange |
