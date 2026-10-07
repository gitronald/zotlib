---
id: 9
slug: init-command
status: done
branch: dev
created: 2026-03-19T13:48:59-07:00
concluded: 2026-03-20T18:17:34-07:00
pr: https://github.com/gitronald/zotlib/pull/6
---

# Add `zotlib init` command
Add `zotlib init` command that discovers Zotero paths and saves them to `zotlib.toml`.

## Config file

`zotlib.toml` in project root:

```toml
[zotlib]
database = "/path/to/zotero.sqlite"
pdfs_dir = "/path/to/linked-pdfs"
```

## `zotlib init`

1. Auto-discover database path (existing `discover_zotero_database()`)
2. Auto-discover linked PDFs directory (existing `discover_pdfs_dir()`)
3. Print what was found
4. Write to `zotlib.toml`
5. If file already exists, show current values and confirm overwrite

## Config loading priority

Update `get_database_path()` and add `get_pdfs_dir()` with priority:

1. CLI flag (`--database`, `--pdfs-dir`)
2. Environment variable (`ZOTERO_DATABASE`)
3. `zotlib.toml`
4. Auto-discovery

## Changes

- Add `zotlib.toml` to `.gitignore`
- Add `init` command to `cli.py`
- Update `config.py` with `load_config()`, `get_pdfs_dir()`
- Update CLI commands to use `get_pdfs_dir()` instead of inline `discover_pdfs_dir()`

## Log

- Implemented all changes in a single commit on `dev`
- `config.py`: added `load_config()`, `get_pdfs_dir()`, `write_config()`, `CONFIG_FILE`
- `config.py`: updated `get_database_path()` to check `zotlib.toml` between env var and auto-discovery
- `cli.py`: added `init` command with overwrite confirmation
- `cli.py`: updated `export-annotations` and `export-covers` to use `get_pdfs_dir()` instead of `discover_pdfs_dir()`
- `.gitignore` already had `zotlib.toml`
- All 53 tests pass
