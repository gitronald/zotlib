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
│   ├── exporters.py             # Collection export (annotations + PDFs)
│   ├── backup.py                # Zotero directory backup
│   ├── tables.py                # Zotero database table definitions
│   ├── covers.py                # PDF cover generation
│   ├── paths.py                 # Path resolution and filename utilities
│   └── formatters/apa.py        # APA citation formatter
├── scripts/                     # Utility scripts
│   ├── extract-annotations.js   # Annotation extractor (interactive + headless)
│   ├── create-parents-for-standalone.js
│   ├── run-extract.sh           # Shell wrapper for headless extraction
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

Run `zotlib init` to auto-discover Zotero paths and save them to `zotlib.toml`:

```bash
zotlib init
```

```
database: /mnt/c/Users/rer/Zotero/zotero.sqlite
pdfs_dir: /mnt/i/My Drive/zotero-pdfs

Saved to zotlib.toml
```

The config file stores the database and linked PDFs directory:

```toml
[zotlib]
database = "/path/to/zotero.sqlite"
pdfs_dir = "/path/to/linked-pdfs"
```

Path resolution priority (for both database and PDFs dir):

1. **CLI flag**: `--database`, `--pdfs-dir`
2. **Environment variable**: `ZOTERO_DATABASE`
3. **Config file**: `zotlib.toml`
4. **Auto-discovery**: Checks common locations (Linux, WSL, macOS)

## CLI Commands

### Export data

```bash
# Export all tables as CSV
zotlib export-csv

# Export a collection as CSV
zotlib export-csv -c publications

# Format a collection as APA references
zotlib export-apa -c publications

# Generate cover images and thumbnails
zotlib export-covers -c publications
zotlib export-covers -c publications -p "/path/to/linked-pdfs/"

# Export annotated PDFs and markdown notes
zotlib export-annotations -c mycollection
zotlib export-annotations -c mycollection -p "/path/to/linked-pdfs/"
```

### Explore and manage

```bash
# List available collections
zotlib show-collections

# Show database tables
zotlib show-tables
zotlib show-tables items

# Back up the Zotero data directory
zotlib backup
```

### Output structure

```
output/
├── export-csv/                     # Bibliographic metadata
│   └── publications.csv
├── export-apa/                     # APA-formatted references
│   └── publications.md
├── export-covers/                  # PDF cover images
│   └── publications/
│       ├── fullsize/
│       └── thumbnails/
└── export-annotations/             # Annotated PDFs + notes
    └── mycollection/
        └── author-year-title/
            ├── paper.pdf
            └── annotations.md
```

### Export annotations features

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

**WIP** — Utilities for Zotero's JavaScript console (Tools > Developer > Run JavaScript). The Zotero SQLite database should never be modified directly via Python — use these JS scripts (which run through Zotero's API) for any write operations.

### create-parents-for-standalone.js

Creates parent document items for standalone PDF attachments in a collection. Useful when PDFs were added directly without metadata — creates a parent item using the filename as the title and re-parents the attachment.

### extract-annotations.js

Extracts annotations from the selected item's PDFs as markdown. Auto-detects its context:

- **Interactive** (Tools > Developer > Run JavaScript): shows a file save dialog
- **Headless** (via HTTP debug API): writes to `~/Desktop/zotero-annotations/`

To run headlessly:

```bash
./scripts/run-extract.sh
```

Requires: Settings > Advanced > "Allow other applications to communicate with Zotero"

The shell script should work on macOS where Zotero and the terminal share the same `localhost`. On WSL, the script calls Zotero's debug HTTP endpoint on `127.0.0.1:23119`, but `localhost` does not bridge to the Windows host by default. You may need to use the Windows host IP or run the curl command from PowerShell instead.

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
