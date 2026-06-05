---
name: Google Workspace Docs
description: Use Google Docs through the gog-safe wrapper for reading, creating, updating, copying, replacing, find/replace, and exporting documents. Requires the Google Workspace docs service to be authorized.
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-18"
---

# Skill: Google Workspace Docs

Use this skill for Google Docs work through `gog-safe`.

## Required Authorization

- Control Center service: `docs`.
- Docs uses both Docs and Drive capabilities for some create/copy/export paths.
- If commands fail with insufficient scopes, ask the operator to reconnect
  Google Workspace with Docs enabled.

## Workflow

1. Check account state with `gog-safe status --json`.
2. Inspect document metadata or content before editing.
3. Prefer append/update for additive edits; use full write/replace only when the
   operator approves replacing existing content.
4. Export to task/document paths when producing deliverables.

## Commands

```bash
gog-safe docs info <docId> --json --no-input
gog-safe docs cat <docId> --max-bytes 20000 --json --no-input
gog-safe docs list-tabs <docId> --json --no-input
gog-safe docs export <docId> --format docx --out ./document.docx --json --no-input
gog-safe docs export <docId> --format pdf --out ./document.pdf --json --no-input
```

Mutations after confirmation:

```bash
gog-safe docs create "Document title" --file ./body.md --json --no-input
gog-safe docs update <docId> --file ./insert.txt --index 25 --json --no-input
gog-safe docs write <docId> --file ./body.md --append --pageless --json --no-input
gog-safe docs find-replace <docId> "old" "new" --json --no-input
gog-safe docs copy <docId> "Document Copy" --json --no-input
```

## Guardrails

- Never replace a whole document without confirming the exact doc ID and title.
- Keep generated source files in a task/document path so changes are auditable.
- Do not insert private or secret material into shared documents.
