---
id: 7
slug: cli-polish
status: done
branch: feature/export-annotated-pdfs
created: 2026-03-19T12:07:12-07:00
concluded: 2026-03-19T12:07:12-07:00
pr: https://github.com/gitronald/zotlib/pull/4
---

# Polish CLI schema command and output directories
Polish CLI commands found during review of the feature/export-annotated-pdfs branch.

## Changes

1. Fix `zotlib schema` crash — was using dict access (`s["table"]`) on dataclass `Table` objects instead of attribute access (`s.name`)
2. Standardize default output directory — `export` command used `outputs/export`, everything else used `output/`; changed to `output/export`
3. Add examples to `schema` command help string
4. Improve `schema` table display:
   - All tables view: Rich table with Table/Description/Columns columns, wide console (200 chars) to prevent wrapping
   - Single table view: added Table name column (first row only), added Type column for SQL types
   - Color scheme: table names cyan bold, column names green
   - Used `Console(width=200, force_terminal=True)` to work around Rich defaulting to 80 cols in WSL/IDE terminals
5. Add CLI smoke tests — 11 tests covering `--help` for every command plus `schema` execution

## Retrospective

- The schema dataclass bug existed before the polars conversion but was never caught because there were no CLI tests. The new smoke tests would have caught it.
- Rich `Console()` auto-detection is unreliable in WSL — hardcoding width with a dedicated console instance is a clean workaround for static content like schema tables.
- `force_terminal=True` is needed on the wide console to enable ANSI color output, since a non-default console doesn't inherit the terminal detection of the default one.
