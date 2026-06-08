---
id: 10
slug: reorganize-zotero-js
status: done
branch: dev
created: 2026-03-21T12:01:53-07:00
completed: 2026-03-21T12:12:26-07:00
pr: https://github.com/gitronald/zotlib/pull/6
---

# Reorganize Zotero JS scripts

## Context

The `zotero-js/` directory contains 5 Zotero JavaScript/shell scripts that sit at the project root as a separate folder. The goal is to consolidate them into the existing `scripts/` directory (which currently has `generate_schema_docs.py`) so all utility scripts live in one place.

## Plan

### 1. Move files with git

Move all 5 files from `zotero-js/` to `scripts/`:

- `extract-annotations.js`
- `extract-annotations-cli.js`
- `extract-annotations-debug.js`
- `create-parents-for-standalone.js`
- `run-extract.sh`

```bash
git mv zotero-js/* scripts/
```

This removes `zotero-js/` automatically once empty.

### 2. Update references

**`README.md`** — 3 changes:
- Project structure tree (lines 19-24): replace `zotero-js/` section, merge JS files under `scripts/`
- Usage path (line 159): `./zotero-js/run-extract.sh` → `./scripts/run-extract.sh`
- Section title (line 142): optionally rename "Zotero JavaScript Scripts" or keep as-is

**`zotlib/export.py`** (line 33) — update comment:
- `zotero-js/extract-annotations.js` → `scripts/extract-annotations.js`

**`run-extract.sh`** (line 10) — no change needed, already uses `$SCRIPT_DIR` relative path.

### 3. Update TODO.md

Mark the item `[x]` and add plan link.

### 4. Commit

Single commit: `reorganize zotero-js into scripts directory`

## Verification

- `ls scripts/` shows all 6 files (5 moved + 1 existing)
- `ls zotero-js/` fails (directory removed)
- `grep -r "zotero-js" .` returns no hits (excluding `.claude/plans/`)
- `run-extract.sh` still resolves its sibling JS file correctly (inspect `$SCRIPT_DIR` logic)
