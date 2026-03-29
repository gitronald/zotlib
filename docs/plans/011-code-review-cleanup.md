---
status: done
branch: dev
created: 2026-03-21T12:49:31-07:00
completed: 2026-03-21T14:19:25-07:00
pr: https://github.com/gitronald/zotlib/pull/6
---

# Code review and cleanup

## Context

Code review scan identified several cleanup items across the codebase: naming inconsistencies, unsafe SQL patterns, dead code, silent error handling, and test gaps.

## Plan

### 1. Standardize `base_dir` / `pdfs_dir` naming

The linked-PDFs directory is called `base_dir` in covers.py, export.py, and CLI flags but `pdfs_dir` in config.py and zotlib.toml. Standardize on `pdfs_dir` everywhere.

- `zotlib/covers.py` — rename `base_dir` param to `pdfs_dir` in `resolve_pdf_path()` and `export_covers()`
- `zotlib/export.py` — rename `base_dir` param to `pdfs_dir` in `export_collection()`
- `zotlib/cli.py` — rename internal variable in `export_annotations()` and `export_covers()`

### 2. Parameterize SQL queries in export.py

Replace f-string interpolation with `?` placeholders:

- `get_item_annotations()` (line ~191) — use `WHERE parentItemID IN ({",".join("?" * len(item_ids))})` with tuple params
- `export_collection()` (line ~599) — use `WHERE parentItemID = ?` with param

### 3. Remove unused `db_path` param from `discover_pdfs_dir()`

- `zotlib/config.py:64` — remove `db_path` parameter from signature
- Update any callers (check cli.py, other config.py functions)

### 4. Log skipped files in backup.py

- `backup.py:28, 91` — add `print()` or `console.print()` warning when `OSError` is caught so users know files were skipped

### 5. Remove `export-covers` coupling to CSV directory

- `cli.py:347` — the `export-covers` command hardcodes `output/export-csv` to find CSV data. Evaluate whether this coupling is necessary or if the data can be sourced differently.

### 6. Clean up unused `unlist()` in utils.py

- Check if `unlist()` is used anywhere in main code. If only in tests, either remove it or document it as a public utility.

### 7. Add ruff linting

- Add ruff as a dev dependency: `uv add --dev ruff`
- Add `[tool.ruff]` config to `pyproject.toml` with sensible defaults
- Run `ruff check` and fix any issues
- Run `ruff format --check` to verify formatting

### 8. Update type hints for Python 3.14

Python 3.14 removes `Optional` from typing. Replace all `Optional[X]` with `X | None` and drop unused `Optional` imports. Also check for any other deprecated typing imports (`List`, `Dict`, `Tuple`, etc.) and replace with builtins.

### 9. Add GitHub Actions CI

Add `.github/workflows/test.yml`:

- Trigger on push/PR to dev and main
- Matrix: Python 3.11, 3.12, 3.13, 3.14
- Use `astral-sh/setup-uv@v5` for uv
- Run `uv run pytest -v --cov=zotlib --cov-report=term-missing`

### 10. Add tests for untested modules

- `config.py` — test `discover_zotero_database()`, `discover_pdfs_dir()`, `load_config()`
- `covers.py` — test `resolve_pdf_path()`, `sanitize_filename()`
- `database.py` — test `ZoteroDatabase` query methods

## Verification

- `uv run pytest` — all tests pass
- `grep -rn "f\".*{" zotlib/export.py` — no f-string SQL queries remain
- `grep -rn "base_dir" zotlib/` — no remaining `base_dir` references
- `grep -rn "db_path" zotlib/config.py` — param removed from `discover_pdfs_dir`
- `uv run ruff check` — no lint errors
- `uv run ruff format --check` — formatting clean

## Log

### Commits

- `cbef4af` add code review cleanup todo and plan
- `2af9bee` code review cleanup: naming, sql params, ruff, typing, ci
- `e65dc62` add .coverage to gitignore
- `bb11622` reorder cli params to avoid ellipsis type hack

### What was done

1. **`base_dir` → `pdfs_dir`** — renamed across covers.py, export.py, cli.py with `replace_all`
2. **SQL parameterization** — added `params` arg to `db.query()`, replaced 2 f-string queries in export.py
3. **Removed unused `db_path` param** from `discover_pdfs_dir()` — no callers used it
4. **Backup logging** — both `OSError` catches now print warnings
5. **Decoupled `export-covers`** — changed hardcoded `Path("output/export-csv")` to `output_dir.parent / "export-csv"`
6. **Removed `unlist()`** — deleted utils.py and test_utils.py (only used in tests, not main code)
7. **Added ruff** — dev dependency, pyproject config (`E, F, I, W, UP` rules, line-length 100), auto-fixed 25 issues, formatted 9 files
8. **Updated typing** — `Optional[X]` → `X | None` (ruff UP045), `typing.Iterator` → `collections.abc.Iterator` (ruff UP035), removed unused `Optional` import
9. **Added GitHub Actions CI** — `.github/workflows/test.yml` with Python 3.11-3.14 matrix, uv, pytest-cov
10. **Added pytest-cov** — dev dependency, coverage at 48%

### Round 2

- `ced2a06` mark code review cleanup as done
- `f48a11b` add tests for covers, config, database, and extractors (48% → 59% coverage, 49 → 86 tests)

Fixes during test writing:
- `mock_db` fixture needed `conn.commit()` — read-only mode meant uncommitted inserts weren't visible
- `test_not_found_raises` needed `monkeypatch.setattr` on `discover_zotero_database` — real Zotero DB on dev machine caused auto-discovery to succeed

### Deferred

- **Step 10 (new tests)** — done. Added test_covers.py, test_config.py, test_database.py, test_extractors.py.

### Issues encountered

- **Typer `= ...` hack** — Pylance flagged `EllipsisType` on required options using `= ...`. Removing `= ...` caused Python syntax errors (required param after default). Fix: reorder params so required `collection` comes first, no default needed.
- **ruff `replace_all` interaction** — `base_dir` rename via `replace_all` in export.py also correctly hit docstrings and comments, which was the desired behavior.
- **ruff format** — auto-fix handled import sorting and `Optional` removal, but format needed a separate pass to reformat 9 files.

## Plan — Round 3: Module organization

### 11. Move shared utilities out of covers.py

`resolve_pdf_path()` and `sanitize_filename()` live in covers.py but are shared by both covers.py and export.py. They're general-purpose path utilities, not cover-specific.

- Create `zotlib/paths.py` with `resolve_pdf_path()` and `sanitize_filename()`
- Update imports in `covers.py`, `export.py`, and `__init__.py` (if exported)
- Move tests in `test_covers.py` to `test_paths.py`

### 12. Rename export.py → exporters.py

Consistent with `extractors.py` and `formatters/`. Updated imports in cli.py and tests.

### 13. Rename create-parents-for-standalone.js → create-parent-item.js

Shorter, clearer name. Added description comment in README project structure.

### Round 3 commits

- `9849752` extract shared path utilities into paths.py
- `66e8214` rename export to exporters for consistency with extractors/formatters
- `27d3513` rename create-parents-for-standalone to create-parent-item

## Retrospective

Started as a code review cleanup (naming, SQL, dead code) and grew into a broader modernization pass. Three rounds:

1. **Code quality** — standardized naming, parameterized SQL, added ruff + CI, updated typing
2. **Test coverage** — added 37 tests across 4 new test files, coverage 48% → 59%
3. **Module organization** — extracted `paths.py` from `covers.py`, renamed `export.py` → `exporters.py` to match `extractors.py`/`formatters/`

Final state: 86 tests, 59% coverage, ruff clean, CI on Python 3.11-3.14.

Follow-ups:
- Added `.ruff_cache` and `.coverage` to `.gitignore` — easy to forget when adding new tooling.
- Removed `docs/schema.md` and `scripts/generate_schema_docs.py` — redundant with `show-tables` CLI command which renders the same `ALL_SCHEMAS` data interactively.
- README polish: reorganized CLI sections (Explore/Export/Backup), added descriptions per section, noted `show-tables` documents Zotero's undocumented SQLite schema, added backup default path and flags, removed redundant `-p` examples (covered by `init`), added install-from-source and install-as-dependency instructions.
- Added `publish.yml` GitHub Actions workflow — triggers on PR merge to main, uses PyPI trusted publishing (OIDC) via `pypa/gh-action-pypi-publish`. Package name `zotlib` confirmed available on PyPI.
- Updated GitHub repo description to mention Zotero 8. Added Zotero 8 requirement note to README with incompatibility warning for older versions.
- Expanded install instructions: pip/uv from PyPI, clone from source, branch-specific via `uv add git+...@dev`.
- Added repo topics: zotero, bibliography, citation, pdfs, sqlite, python.
- Bumped `actions/checkout` to v6 and `astral-sh/setup-uv` to v7 to fix Node.js 20 deprecation warnings.
- Reduced CI noise from stanza releases: changed test workflow to push on dev only + PR to main (was push on dev+main + PR on dev+main). Cuts runs per release from 5 to 4.
- Published to PyPI as `zotlib==0.4.5` via trusted publishing. Required making repo public and setting up PyPI pending publisher with OIDC environment.

Future considerations:
- Add branch protection rule on main requiring test status checks to pass before merging. Currently `publish.yml` and `test.yml` are independent — tests could fail but a merge would still trigger a publish.
- Evaluate `ty` (Astral's Rust type checker) once it reaches stable release for CI type checking.
