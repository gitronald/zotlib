# Zotlib Library Conversion Plan

Convert the zotero scripts into a Poetry-managed Python library.

## Target Structure

```
zotlib/
├── pyproject.toml
├── README.md
├── src/
│   └── zotlib/
│       ├── __init__.py
│       ├── cli.py              # Typer CLI
│       ├── config.py           # Configuration (env vars, auto-discovery)
│       ├── database.py         # SQLite connection (read-only)
│       ├── extractors.py       # Data extraction functions
│       ├── utils.py            # Local utils (replace external dep)
│       └── formatters/
│           ├── __init__.py
│           └── apa.py          # APA citation formatter
├── tests/
│   └── conftest.py
└── notebooks/
    └── analysis.ipynb
```

## Key Changes

### 1. Configuration System
- Replace hardcoded `/mnt/c/Users/rer/Zotero/zotero.sqlite` with:
  - `ZOTERO_DATABASE` env var
  - CLI `--database` flag
  - Auto-discovery of common locations (Linux, WSL, macOS)
- Make collection filter (`'rer'`) configurable via `--collection` flag

### 2. Database Layer
- Use read-only SQLite connection (`?mode=ro`) per Zotero docs
- Context manager for safe connection handling
- Validate path exists before connecting

### 3. Remove External Dependency
- Replace `utils @ git+https://github.com/gitronald/utils` with local implementations
- Only uses `unlist()` (flatten list) and `print_line()` (separator) - trivial to implement

### 4. CLI Commands
```bash
zotlib extract                    # Extract all data
zotlib extract -c rer -f apa      # CV items as APA
zotlib collections                # List collections
```

### 5. Dependencies (pyproject.toml)
- pandas>=2.0.0
- typer>=0.12.0
- rich>=13.0.0

## Zotero 6 to 7 Compatibility

**Good news**: No mandatory schema changes. Core tables are the same:
- `items`, `itemData`, `itemDataValues`, `fieldsCombined`, `itemTypes`
- `creators`, `itemCreators`
- `collections`, `collectionItems`

**Optional enhancement**: Zotero 7 adds `itemAnnotations` table for PDF annotations. Could add extraction later if needed.

## Files to Migrate

| Current | New Location |
|---------|--------------|
| `zotero/zotero.py` | `src/zotlib/database.py` + `extractors.py` |
| `zotero/apa.py` | `src/zotlib/formatters/apa.py` |
| `zotero/analysis.py` | `notebooks/analysis.ipynb` |
| `zotero/requirements.txt` | `pyproject.toml` |

## Implementation Order

1. Create `pyproject.toml` with Poetry config
2. Create `src/zotlib/` package structure
3. Implement `utils.py` (replace external dep)
4. Refactor `zotero.py` into `database.py` + `extractors.py`
5. Refactor `apa.py` into `formatters/apa.py`
6. Implement `config.py` with env var support
7. Implement `cli.py` with Typer
8. Update README with new usage
9. Add basic tests

## Verification

```bash
# Install and test
poetry install
poetry run zotlib --help
poetry run zotlib collections
poetry run zotlib extract -c rer -f apa
poetry run pytest
```
