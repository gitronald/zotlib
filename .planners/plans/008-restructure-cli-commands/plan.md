---
id: 8
slug: restructure-cli-commands
status: done
branch: feature/export-annotated-pdfs
created: 2026-03-19T12:22:59-07:00
concluded: 2026-03-19T14:04:51-07:00
pr: https://github.com/gitronald/zotlib/pull/4
---

# Restructure CLI commands with export-* naming
Restructure CLI commands with consistent `export-*` naming, split formatting into its own command, and organize output directories by command.

## Current commands

| Command | Function | Default output |
|---|---|---|
| `extract` | Export metadata to CSV and/or APA markdown | `output/` |
| `covers` | Render first-page PNGs from PDFs | `output/{collection}/` |
| `export` | Bake annotations into PDFs + markdown notes | `output/export/` |
| `thumbnails` | Resize cover images | `{input_dir}/thumbs/` |
| `backup` | Archive Zotero data directory | `data/backups/` |
| `schema` | Show database schema | stdout |
| `collections` | List collections | stdout |
| `tables` | List database tables | stdout |

## New commands

| Command | Function | Default output |
|---|---|---|
| `export-csv` | Export metadata to CSV | `output/export-csv/{collection}.csv` |
| `export-apa` | Format as APA references | `output/export-apa/{collection}.md` |
| `export-covers` | Render first-page PNGs + thumbnails | `output/export-covers/{collection}/` |
| `export-annotations` | Bake annotations into PDFs + markdown | `output/export-annotations/{collection}/` |
| `show-tables` | Show database schema, or all tables with `--all` | stdout |
| `show-collections` | List collections | stdout |
| `backup` | Archive Zotero data directory (unchanged) | `data/backups/` |

## Changes

### 1. Split `extract` into `export-csv` and `export-apa`

- `export-csv` — takes `-c` collection name, outputs CSV only. No `--format` flag.
  - With `-c`: exports collection items to `output/export-csv/{collection}.csv`
  - Without `-c`: dumps all tables to `output/export-csv/data/`
- `export-apa` — takes `-c` collection name, outputs APA markdown.
  - Can read from existing CSV (`-i input.csv`) or pull from database directly.
  - Outputs to `output/export-apa/{collection}.md`

### 2. Rename `covers` to `export-covers`

- Default output changes from `output/{collection}/` to `output/export-covers/{collection}/`
- Generates both fullsize (`fullsize/`) and thumbnails (`thumbnails/`) by default
- Add `--no-thumbnails` flag to skip thumbnail generation
- CSV generation: check for CSV in `output/export-csv/`, create if missing, update with cover paths
- Rename `--base-dir` / `-b` to `--pdfs-dir` / `-p` (already done)
- Drop `thumbnails` CLI command — `generate_thumbnails` function stays in `covers.py` for internal use

### 3. Rename `export` to `export-annotations`

- Default output changes from `output/export/` to `output/export-annotations/{collection}/`
- Add collection name as subdirectory automatically

### 4. Update output directory structure

```
output/
├── export-csv/
│   ├── publications.csv
│   └── data/              (all-tables dump)
├── export-apa/
│   └── publications.md
├── export-covers/
│   └── publications/
│       ├── fullsize/       (300 DPI PNGs)
│       └── thumbnails/     (400px wide)
└── export-annotations/
    └── mycollection/
        └── author-year-title/
            ├── paper.pdf
            └── annotations.md
```

### 5. Update README and help strings

- Update all examples and documentation to use new command names
- Each command gets examples in its docstring

## Implementation order

1. Rename `extract` to `export-csv`, remove `--format` flag
2. Create `export-apa` as standalone command
3. Rename `covers` to `export-covers`, update output paths and CSV location, integrate thumbnail generation
4. Remove `thumbnails` CLI command
5. Rename `export` to `export-annotations`, add collection subdirectory
6. Update README, help strings, tests

## Log

- Implemented all export-* renames (export-csv, export-apa, export-covers, export-annotations)
- Split `extract` into `export-csv` and `export-apa` (dropped `--format` flag, added `--group-by` to export-apa)
- `export-covers` now generates both fullsize and thumbnails by default, with `--no-thumbnails` flag
- Dropped `thumbnails` CLI command
- Renamed `schema` -> `show-tables`, `tables` -> merged into `show-tables --all`, `collections` -> `show-collections`
- Renamed `schema.py` -> `tables.py`, added `itemAttachments` table definition, added `SCHEMA_MAP`
- `show-tables --all` now shows description and columns for documented tables
- Auto-discovery of linked PDFs dir from Zotero `prefs.js` (`discover_pdfs_dir()` in config.py)
- Converted `covers.py` from pandas to polars (missed in initial conversion)
- Renamed `--base-dir` to `--pdfs-dir` (`-p`)
- Command display order: show-tables, show-collections, export-*, backup
- Updated README, tests, help strings
- Note: `export-apa -i input.csv` (read from CSV) not implemented — currently always reads from database
