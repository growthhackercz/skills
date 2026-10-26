---
name: Google Workspace Drive
description: Use Google Drive through the gog-safe wrapper for file search, upload, download, export, folder organization, and sharing. Requires the Google Workspace drive service to be authorized.
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-18"
---

# Skill: Google Workspace Drive

Use this skill for Google Drive file work through `gog-safe`.

## Required Authorization

- Control Center service: `drive`.
- Docs, Sheets, and Slides exports often use Drive too.
- If commands fail with insufficient scopes, ask the operator to reconnect
  Google Workspace with Drive enabled.

## Workflow

1. Check account state with `gog-safe status --json`.
2. Search with narrow queries and show candidate IDs before acting.
3. Download/export to an explicit task or document path.
4. Confirm before upload, replace, move, delete, or permission changes.

## Commands

```bash
gog-safe drive search "invoice filetype:pdf" --max 20 --json --no-input
gog-safe drive url <fileId> --json --no-input
gog-safe drive download <fileId> --out ./downloaded.bin --json --no-input
gog-safe drive download <fileId> --format pdf --out ./exported.pdf --json --no-input
```

Mutations after confirmation:

```bash
gog-safe drive upload ./report.pdf --parent <folderId> --json --no-input
gog-safe drive upload ./report.docx --convert --name "Report" --parent <folderId> --json --no-input
gog-safe drive mkdir "New Folder" --parent <parentFolderId> --json --no-input
gog-safe drive rename <fileId> "New Name" --json --no-input
gog-safe drive move <fileId> --parent <destinationFolderId> --json --no-input
gog-safe drive share <fileId> --to user --email user@example.com --role reader --json --no-input
```

## Guardrails

- Never share a file publicly or with a domain without explicit confirmation.
- Prefer trash over permanent delete; permanent delete needs extra confirmation.
- Do not upload secrets or OAuth credentials to Drive.
