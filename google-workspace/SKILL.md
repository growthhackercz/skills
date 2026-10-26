---
name: Google Workspace
description: Shared operating rules for using Google Workspace through the gog-safe wrapper. Use this when a task spans several Google services or when checking account, auth, and safety prerequisites.
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-18"
---

# Skill: Google Workspace

Use Google Workspace through the `gog-safe` wrapper when a task spans several Google
services or when you need to check account/auth status before using a more
specific Google Workspace skill.

Prefer the narrower skill when the task is clearly about one service:

- `google-workspace-mail` for Gmail.
- `google-workspace-calendar` for Calendar.
- `google-workspace-drive` for Drive files and permissions.
- `google-workspace-sheets` for spreadsheets.
- `google-workspace-docs` for Google Docs.
- `google-workspace-slides` for presentations.
- `google-workspace-contacts` for contacts lookup.

## Before You Act

- Confirm that Google Workspace is connected in Control Center.
- If `gog-safe status --json` reports no connected account, ask the operator to
  connect Google Workspace in Control Center.
- Check that the connected account has the required service authorized. Ask the
  operator to reconnect with the missing service enabled if `gog-safe` returns a 403
  insufficient scope error.
- Prefer `--json` and `--no-input` for commands used in scripts.
- Confirm with the operator before sending email, creating calendar events,
  changing shared files, or modifying Docs/Sheets/Slides.

## Account

Use the connected default account managed by Control Center:

```bash
gog-safe status --json
```

## Service Mapping

Control Center can authorize these service buckets:

| Service | Use when the task needs |
| --- | --- |
| `gmail` | Gmail search/read/draft/send. |
| `calendar` | Calendar reads, free/busy, event create/update/delete. |
| `drive` | File search, upload/download/export, folders, sharing. |
| `sheets` | Spreadsheet read/write/format/export. |
| `docs` | Google Docs read/write/export. |
| `slides` | Google Slides create/export/update. |
| `contacts` | Personal contacts lookup. |

Docs, Sheets, and Slides operations may also require Drive access because Google
native files are stored and exported through Drive.

## Common Commands

Use these to inspect the setup before a task:

```bash
gog-safe status --json
```

## Guardrails

- Do not change Gmail settings, forwarding, filters, aliases, or delegation.
- Do not scrape a Google Workspace directory.
- Do not send bulk email without a confirmed recipient list and final message
  body.
- Do not share, delete, overwrite, or move user files without explicit
  confirmation.
- Do not expose OAuth tokens, keyring files, or client secrets.
