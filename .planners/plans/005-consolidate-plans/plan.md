---
id: 5
slug: consolidate-plans
status: done
branch: dev
created: 2026-03-06T00:00:00-07:00
concluded: 2026-03-06T17:39:39-08:00
pr: https://github.com/gitronald/zotlib/pull/6
---

# Consolidate plan and summary system

## Context

The `.claude/plans/` directory has grown organically across sessions with inconsistent numbering (three `000-*` files), no frontmatter, no lifecycle tracking, and a new `.claude/summaries/` directory that duplicates plan content. This cleanup consolidates everything into a single system with minimal ceremony.

## Changes

### 1. Update the global rule: `~/.claude/rules/plan-file-location.md`

Rewrite to include frontmatter spec, body template, and no-summaries policy:

```markdown
# Plan Files

Write plan files to the **project's** `.claude/plans/` directory.

## Naming

Format: `{NNN}-{feature-name}.md` with auto-incrementing prefix.
Next number = max(existing prefixes) + 1. Never reuse a number.

## Frontmatter

Every plan starts with YAML frontmatter:

    ---
    status: draft
    branch: dev/feature-name
    created: YYYY-MM-DD
    ---

Update `status` as work progresses: draft -> active -> done (or abandoned).
Omit `branch` for plans that don't involve a git branch.

## Body Sections

- **Plan** — implementation spec (required)
- **Log** — chronological notes, commits, decisions (optional, append during work)
- **Retrospective** — post-completion insights (optional, add when done)

## Commits

Commit changes in logical chunks during implementation, not one large commit at the end.

## No Separate Summaries

Do not create a `.claude/summaries/` directory. Session summaries belong in the plan's Log or Retrospective section.
```

### 2. Renumber misnumbered plans

| Current | New | Reason |
|---------|-----|--------|
| `000-library-conversion.md` | keep | oldest plan, `000` is correct |
| `001-pdf-covers-pipeline.md` | keep | already correct |
| `002-poetry-to-uv.md` | keep | already correct |
| `003-export-reviews.md` | keep | already correct |
| `000-backup-command.md` | `004-backup-command.md` | duplicate `000`, created 2026-03-02 |
| `000-organize-review-outputs.md` | `005-organize-review-outputs.md` | duplicate `000`, created 2026-03-06 |

Next new plan will be `007-*.md`.

### 3. Add YAML frontmatter to all plans

Three fields only — `status`, `branch` (optional), `created`:

| Plan | status | branch | created |
|------|--------|--------|---------|
| `000-library-conversion` | done | dev | 2025-01-19 |
| `001-pdf-covers-pipeline` | done | dev | 2025-01-31 |
| `002-poetry-to-uv` | done | dev | 2026-02-22 |
| `003-export-reviews` | done | feature/export-annotated-pdfs | 2026-03-02 |
| `004-backup-command` | done | dev | 2026-03-02 |
| `005-organize-review-outputs` | done | _(omit — shell only)_ | 2026-03-06 |

### 4. Merge summary into plan 003, delete summaries dir

Move the key insights from `summaries/000-export-annotated-pdfs.md` into a **Retrospective** section at the bottom of `003-export-reviews.md`. Then delete the summaries directory.

Retrospective content to merge:

```markdown
## Retrospective

- Multi-attachment bug: annotations keyed to specific attachments (annotation.parentItemID -> attachment.itemID), not parent items. Original code grabbed first PDF and baked all annotations onto it.
- Zotero JS async pitfall: async IIFEs return undefined in console. Use top-level code with `return output`.
- Subcollections: `getByLibrary()` only returns top-level. Use `Collections.get(id)` for subcollections.
- WSL <-> Zotero: debug endpoint binds to Windows localhost, not WSL's. Must paste scripts into console.
- Naming: generalizing early (export vs reviews) prevents rename churn later.
- Renamed reviews.py -> export.py, export_reviews -> export_collection, CLI reviews -> export.
```

## Files to modify

| File | Action |
|------|--------|
| `~/.claude/rules/plan-file-location.md` | Rewrite with updated spec |
| `.claude/plans/000-backup-command.md` | Rename to `004-`, add frontmatter |
| `.claude/plans/000-organize-review-outputs.md` | Rename to `005-`, add frontmatter |
| `.claude/plans/000-library-conversion.md` | Add frontmatter |
| `.claude/plans/001-pdf-covers-pipeline.md` | Add frontmatter |
| `.claude/plans/002-poetry-to-uv.md` | Add frontmatter |
| `.claude/plans/003-export-reviews.md` | Add frontmatter + retrospective section |
| `.claude/summaries/` | Delete directory |

## Verification

- All plans have valid YAML frontmatter with `status: done`
- No duplicate prefixes in filenames
- `ls .claude/plans/` shows `000` through `006` sequentially
- `.claude/summaries/` no longer exists
- Rule file updated and consistent with new plan format
