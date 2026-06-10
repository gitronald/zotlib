---
id: 6
slug: pandas-to-polars
status: done
branch: feature/pandas-to-polars
created: 2026-03-19T10:56:45-07:00
concluded: 2026-03-19T11:48:51-07:00
pr: https://github.com/gitronald/zotlib/pull/4
---

# Convert pandas to polars
Convert all pandas usage in zotlib to polars.

## Scope

5 files import pandas:

- `zotlib/database.py` - `pd.read_sql_query()`, returns `pd.DataFrame`
- `zotlib/extractors.py` - `pd.read_sql_query()` (via database), `pd.to_datetime()`, `pd.Series`, DataFrame operations (merge, pivot, groupby)
- `zotlib/export.py` - `pd.isna()`, `pd.notna()`, `pd.read_sql_query()`, `pd.Series`, `pd.DataFrame` type hints
- `zotlib/formatters/apa.py` - `pd.isna()`, `pd.Series`, `pd.DataFrame` type hints
- `zotlib/cli.py` - `pd.read_csv()`

## Key conversion patterns

| pandas | polars |
|---|---|
| `pd.read_sql_query(sql, conn)` | `pl.read_database(sql, conn)` |
| `pd.read_csv(path)` | `pl.read_csv(path)` |
| `pd.to_datetime(col, errors="coerce")` | `col.str.to_datetime(strict=False)` |
| `pd.isna(val)` / `pd.notna(val)` | `val is None` (scalar) or `.is_null()` (column) |
| `pd.Series` row access `row["col"]` | `row["col"]` on dict or named tuple |
| `df.merge(...)` | `df.join(...)` |
| `df.pivot(...)` | `df.pivot(...)` |
| `df.groupby(...).agg(...)` | `df.group_by(...).agg(...)` |
| `df.iterrows()` | `df.iter_rows(named=True)` |
| Type hints `pd.DataFrame` / `pd.Series` | `pl.DataFrame` / `dict` (for rows) |

## Implementation order

1. **`zotlib/database.py`** - Foundation layer. Change `pd.read_sql_query` to `pl.read_database`. Update return type hints. This affects all downstream consumers.
2. **`zotlib/extractors.py`** - Heaviest pandas usage (merge, pivot, groupby, to_datetime). Convert all DataFrame operations to polars equivalents.
3. **`zotlib/export.py`** - Replace `pd.isna`/`pd.notna` checks, update row iteration patterns, update type hints.
4. **`zotlib/formatters/apa.py`** - Replace `pd.isna` checks, update `pd.Series` row access to dict access, update type hints.
5. **`zotlib/cli.py`** - Replace `pd.read_csv` with `pl.read_csv`.
6. **Dependencies** - Remove pandas from project deps (`uv remove pandas`), add polars if not present (`uv add polars`).
7. **Tests** - Run existing tests, fix any breakage from the conversion.

## Notes

- Row iteration changes from `pd.Series` (with `.index` attribute and `pd.isna` checks) to plain dicts (with `is None` checks). This is the most pervasive change.
- `pl.read_database` requires a connection URI string or connectorx, not a sqlite3 connection object. May need to pass the DB path as a URI instead. Alternative: use `pl.read_database_uri()` with `sqlite:///path`.
- The `_get_first_notnull` helper in extractors.py operates on a `pd.Series` row - will need rework for dict-based rows.

## Log

- Converted all 5 source files and 3 test files from pandas to polars
- Used cursor-based SQL query in `database.py` instead of `pl.read_database` to avoid connectorx dependency
- Replaced `pd.Series` row types with plain `dict` throughout (via `iter_rows(named=True)`)
- Replaced `_get_first_notnull` row helper with `pl.coalesce` column expression
- Fixed pre-existing bug in `cli.py` schema command: was using dict access on dataclass objects
- Added 11 CLI smoke tests in `tests/test_cli.py`
- Removed pandas/numpy deps, added polars; 54 tests passing
