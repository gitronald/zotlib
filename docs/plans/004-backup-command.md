---
id: 4
slug: backup-command
status: done
branch: dev
created: 2026-03-02T00:00:00-08:00
completed: 2026-03-02T12:30:28-08:00
pr: https://github.com/gitronald/zotlib/pull/4
---

# Backup Command

## Context

zotlib has no way to back up the Zotero data directory. Adding a `backup` command that archives the entire Zotero folder as `.tar.bz2`.

## Files to create/modify

| File | Action |
|------|--------|
| `zotlib/backup.py` | Create - backup logic |
| `zotlib/cli.py` | Modify - add `backup` command |
| `tests/test_backup.py` | Create - tests |

## Implementation

### 1. `zotlib/backup.py` (new)

Three functions:

- **`get_directory_stats(source_dir)`** - Walk directory, return `(file_count, total_bytes)`
- **`default_backup_path()`** - Return `Path(f"zotero-backup-{date.today().isoformat()}.tar.bz2")`
- **`create_backup(source_dir, output_path, console)`** - Main function:
  1. Validate source exists, output doesn't exist
  2. Scan directory for file count + total size, print summary
  3. Create `.tar.bz2` with `tarfile` using `os.walk` + non-recursive `tar.add` for per-file progress
  4. Archive root = directory name (e.g. `Zotero/`) via `arcname=rel_to_parent`
  5. Rich progress bar showing files archived (SpinnerColumn + BarColumn + MofNCompleteColumn)
  6. Print final archive size

### 2. `zotlib/cli.py` - add `backup` command

```python
@app.command()
def backup(
    database: ...  # --database/-d, Optional[Path], default None
    output: ...    # --output/-o, Optional[Path], default None
):
```

- Resolve database path via `get_database_path(database)`
- Zotero directory = `db_path.parent`
- Default output via `default_backup_path()`
- Call `create_backup(source_dir, output, console)`

### 3. `tests/test_backup.py` (new)

- `fake_zotero_dir` fixture - tmp_path with `Zotero/zotero.sqlite` + `storage/ABCD1234/paper.pdf`
- Test `get_directory_stats` returns correct count/bytes
- Test `create_backup` produces valid tar.bz2 with expected contents and `Zotero/` root
- Test `FileExistsError` when output already exists
- Test `FileNotFoundError` when source missing
- Test `default_backup_path` format

## No changes to

- `__init__.py` - backup is CLI-only (same as `covers.py` functions)
- `pyproject.toml` - only uses stdlib (`tarfile`, `os`) + Rich (already a dependency)

## Verification

```bash
uv run pytest tests/test_backup.py -v
uv run zotlib backup --help
uv run zotlib backup  # test against real Zotero directory
```
