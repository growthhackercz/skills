---
name: Google Workspace Contacts
description: Use Google Contacts through the gog-safe wrapper for personal contact and other-contact lookup. Requires the Google Workspace contacts service to be authorized.
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-18"
---

# Skill: Google Workspace Contacts

Use this skill for contact lookup through `gog-safe`.

## Required Authorization

- Control Center service: `contacts`.
- If commands fail with insufficient scopes, ask the operator to reconnect
  Google Workspace with Contacts enabled.

## Workflow

1. Check account state with `gog-safe status --json`.
2. Search narrowly by name, email, or organization.
3. Return only the fields needed for the task.
4. Confirm before creating, updating, or deleting a contact.

## Commands

```bash
gog-safe contacts search "Ada" --max 10 --json --no-input
gog-safe contacts get user@example.com --json --no-input
gog-safe contacts other search "John" --max 10 --json --no-input
```

Mutations after confirmation:

```bash
gog-safe contacts create --given "Jane" --family "Doe" --email "jane@example.com" --json --no-input
gog-safe contacts update people/<resourceName> --email "new@example.com" --json --no-input
```

## Guardrails

- Do not scrape broad contact lists or Workspace directory data.
- Do not expose full contact records when only one field is needed.
- Do not modify contacts without showing the exact intended change first.
