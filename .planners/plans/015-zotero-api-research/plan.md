---
id: 15
slug: zotero-api-research
status: draft
branch:
created: 2026-06-15T11:35:10-07:00
concluded:
pr:
---

# Research Zotero integration options beyond the SQLite read approach

## Plan

zotlib currently reads the Zotero library by opening `zotero.sqlite` directly
(read-only). That works without Zotero running, but it is read-only, depends on
the internal schema, and can't trigger Zotero behavior (sync, attachment
resolution, item creation). This plan is **research only** — no implementation —
to map the alternative integration surfaces and what each unlocks.

### Questions to answer

1. **Other packages** — survey existing libraries for talking to Zotero across
   languages (e.g. Pyzotero, libzotero/zotero-cli, the JS `zotero-api-client`,
   any R/Go clients). For each: which API it targets (Web API vs local), read
   vs. write support, auth model, and maintenance status.
2. **The local HTTP API** — document how Zotero's built-in local server works:
   - The connector/local endpoint exposed by a running Zotero instance
     (`http://localhost:23119`, e.g. `/api/`, `/connector/`) — what it requires
     (Zotero running, which version, any setting to enable).
   - How it relates to the cloud **Web API** (`api.zotero.org`) — same schema?
     same client (Pyzotero `local=True`)? auth differences (none locally vs API
     key)?
   - What it returns and accepts: items, collections, full-text, attachments,
     writes/creates, saved searches.
3. **Comparison vs. the current SQLite read** — build a capability table:
   read vs. write, requires-Zotero-running, schema-stability/version-coupling,
   attachment/file resolution, sync awareness, performance, and cross-platform
   path issues (relevant given the WSL/Zotero path quirks).

### Method

- Web research: official Zotero docs (dev pages for the local server, Web API
  spec), the Pyzotero docs, and source/READMEs of the other clients.
- Capture findings in this plan's `## Log` (or a sidecar `findings.md` in this
  plan directory) with source links.

### Out of scope

- Standing up a local Zotero instance or running the local API here.
- Implementing a new backend in zotlib — that would be a follow-up plan if the
  research warrants it.

### Deliverable

A written summary (in this plan) covering the package landscape, how the local
API works, and the capability comparison — enough to decide whether a future
plan should add an HTTP-API backend alongside the SQLite reader.
