---
name: Google Workspace Presentations
description: Use Google Slides through the gog-safe wrapper for creating, copying, exporting, and updating presentations. Requires the Google Workspace slides service to be authorized.
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-18"
---

# Skill: Google Workspace Presentations

Use this skill for Google Slides work through `gog-safe`.

## Required Authorization

- Control Center service: `slides`.
- Slides uses Drive for copy/export and file-level operations.
- If commands fail with insufficient scopes, ask the operator to reconnect
  Google Workspace with Presentations enabled.

## Workflow

1. Check account state with `gog-safe status --json`.
2. Inspect presentation metadata and slide IDs before editing.
3. Prefer creating from Markdown or template when producing a new deck.
4. Confirm before replacing slides or changing speaker notes.

## Commands

```bash
gog-safe slides info <presentationId> --json --no-input
gog-safe slides list-slides <presentationId> --json --no-input
gog-safe slides export <presentationId> --format pptx --out ./deck.pptx --json --no-input
gog-safe slides export <presentationId> --format pdf --out ./deck.pdf --json --no-input
```

Mutations after confirmation:

```bash
gog-safe slides create "Deck title" --json --no-input
gog-safe slides create-from-markdown "Deck title" --content-file ./slides.md --json --no-input
gog-safe slides create-from-template <templateId> "Deck title" --replace "name=Client" --json --no-input
gog-safe slides add-slide <presentationId> ./slide.png --notes "Speaker notes" --json --no-input
gog-safe slides update-notes <presentationId> <slideId> --notes "Updated notes" --json --no-input
gog-safe slides replace-slide <presentationId> <slideId> ./new-slide.png --notes "New notes" --json --no-input
```

## Guardrails

- Keep slide source Markdown or images in task/document paths.
- Do not replace slides without confirming presentation ID, slide ID, and title.
- Export a deck after material changes so the user can review the output.
