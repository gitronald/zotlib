---
id: 12
slug: pyproject-urls
status: draft
branch:
created: 2026-06-08T11:57:41-07:00
completed:
pr:
---

# Add a project.urls section to pyproject.toml for the pip homepage

## Plan

`pyproject.toml` has no `[project.urls]` table, so the PyPI/pip project page shows no
homepage or source link. Add a `[project.urls]` section pointing at the repository (and
optionally homepage/issues) so the package page links back to the source.

Carried over from `TODO.md` during the `.planners/` migration (was a `(no plan)` item).
