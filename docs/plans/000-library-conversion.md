---
status: done
branch: dev
created: 2025-01-19T00:00:00-08:00
completed: 2026-01-19T01:08:54-08:00
pr: https://github.com/gitronald/zotlib/pull/1
---

# Zotlib Library Conversion

Convert the zotero scripts into a Poetry-managed Python library.

## Plan

### Target Structure

```
zotlib/
├── pyproject.toml
├── README.md
├── zotlib/
│   ├── __init__.py
│   ├── cli.py              # Typer CLI
│   ├── config.py           # Configuration (env vars, auto-discovery)
│   ├── database.py         # SQLite connection (read-only)
│   ├── extractors.py       # Data extraction functions
│   ├── utils.py            # Local utils (replace external dep)
│   └── formatters/
│       ├── __init__.py
│       └── apa.py          # APA citation formatter
├── tests/
│   └── conftest.py
└── notebooks/
    └── analysis.ipynb
```

### Key Changes

1. **Configuration system** - Replace hardcoded paths with `ZOTERO_DATABASE` env var, CLI `--database` flag, and auto-discovery (Linux, WSL, macOS). Make collection filter configurable via `--collection` flag.
2. **Database layer** - Read-only SQLite connection (`?mode=ro`), context manager, path validation.
3. **Remove external dependency** - Replace `utils @ git+...` with local `unlist()` and `print_line()`.
4. **CLI commands** - `zotlib extract`, `zotlib collections`, `zotlib extract -c rer -f apa`
5. **Dependencies** - pandas>=2.0.0, typer>=0.12.0, rich>=13.0.0

### Zotero 6 to 7 Compatibility

No mandatory schema changes. Core tables (`items`, `itemData`, `itemDataValues`, `fieldsCombined`, `itemTypes`, `creators`, `itemCreators`, `collections`, `collectionItems`) are the same. Zotero 7 adds `itemAnnotations` for PDF annotations.

### Files Migrated

| Current | New Location |
|---------|--------------|
| `zotero/zotero.py` | `zotlib/database.py` + `extractors.py` |
| `zotero/apa.py` | `zotlib/formatters/apa.py` |
| `zotero/analysis.py` | `notebooks/analysis.ipynb` |
| `zotero/requirements.txt` | `pyproject.toml` |

## Implementation

### Library setup

Created dev branch, .gitignore, and made atomic commits for each component:

```
2a651ef add gitignore for python artifacts
218040a add poetry project configuration
d432466 add zotlib library package
e61f3a5 add test suite
44079ed update readme with library documentation
```

Fixed duplicate column name bug in JOIN queries - changed `SELECT *` to explicit column lists in `extractors.py` and simplified `database.py` to use `pd.read_sql_query()`.

```
d0618a1 fix duplicate column names in join queries
f936141 update readme todo list
```

### Project reorganization

Archived old `zotero/` scripts to `.archive/`, flattened `src/zotlib/` to `zotlib/`, updated `pyproject.toml` package location, and organized JS files into `zotero-js/` directory.

```
c18b75e reorganize project structure
54566f6 update readme with new project structure
6cb1bf5 add todo items to readme
fb1aa9c organize javascript files into zotero-js directory
```

### Final structure

```
zotlib/
├── .archive/                    # Old scripts (ignored)
├── zotlib/                      # Python library
│   ├── cli.py
│   ├── config.py
│   ├── database.py
│   ├── extractors.py
│   ├── formatters/
│   └── utils.py
├── zotero-js/                   # Zotero JavaScript scripts
│   ├── extract-annotations.js
│   ├── extract-annotations-cli.js
│   ├── extract-annotations-debug.js
│   └── run-extract.sh
├── tests/
├── pyproject.toml
└── README.md
```
