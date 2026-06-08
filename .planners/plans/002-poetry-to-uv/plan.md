---
id: 2
slug: poetry-to-uv
status: done
branch: dev
created: 2026-02-22T00:00:00-08:00
completed: 2026-02-22T16:58:09-08:00
pr: https://github.com/gitronald/zotlib/pull/3
---

# Migrate from Poetry to uv

## Context

Migrate zotlib's dependency management from Poetry to uv for faster installs, simpler tooling, and PEP-compliant configuration.

## Files to modify

- `pyproject.toml` — rewrite build system, dependencies, dev groups
- `README.md` — line 25 ("Poetry configuration"), line 42 (`poetry install`)

## Files to create

- `.python-version` — pin to `3.12`
- `uv.lock` — generated via `uv lock`

## Files to delete

- `poetry.lock` — via `git rm`

## Steps

### 1. Rewrite `pyproject.toml`

**Build system**: Replace poetry-core with hatchling:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Dependencies**: Fix Poetry-style version syntax to PEP 508:
```toml
dependencies = [
    "pandas>=2.0.0",
    "typer>=0.12.0",
    "rich>=13.0.0",
    "pymupdf>=1.26.7,<2.0.0",
    "pillow>=12.1.0,<13.0.0",
]
```

**Dev dependencies**: Convert to PEP 735 `[dependency-groups]`:
```toml
[dependency-groups]
dev = ["pytest>=8.0.0", "ipykernel>=6.29.0"]
```

**Remove** all `[tool.poetry*]` sections.

### 2. Pin Python version

Create `.python-version` with `3.14` (installed at `~/.local/share/uv/python/`).

### 3. Swap lock files

```bash
git rm poetry.lock
uv lock
```

### 4. Update README

- Line 25: "Poetry configuration" → "Project configuration"
- Line 42: `poetry install` → `uv sync`

### 5. Recreate virtual environment

```bash
rm -rf .venv
uv sync --all-groups
```

### 6. Verify

```bash
uv run zotlib --help
uv run python -c "import pymupdf; print(pymupdf.__version__)"
```

## Commits

1. Migrate pyproject.toml, swap lock files, add .python-version
2. Update README
3. Recreate .venv (no commit needed)
