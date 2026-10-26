---
name: Google Workspace Calendar
description: Use Google Calendar through the gog-safe wrapper for schedule lookup, free/busy checks, event creation, updates, and deletion. Requires the Google Workspace calendar service to be authorized.
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-18"
---

# Skill: Google Workspace Calendar

Use this skill for Google Calendar work through `gog-safe`.

## Required Authorization

- Control Center service: `calendar`.
- If commands fail with insufficient scopes, ask the operator to reconnect
  Google Workspace with Calendar enabled.

## Workflow

1. Check account state with `gog-safe status --json`.
2. Resolve the target calendar before creating or changing events.
3. Use explicit ISO dates with timezone offsets for event writes.
4. Confirm attendee list, time, timezone, title, and notification behavior
   before creating, updating, or deleting events.

## Commands

```bash
gog-safe calendar calendars --json --no-input
gog-safe calendar events primary --today --json --no-input
gog-safe calendar events primary --from 2026-04-28T00:00:00Z --to 2026-04-29T00:00:00Z --json --no-input
gog-safe calendar search "meeting" --days 30 --max 20 --json --no-input
gog-safe calendar get primary <eventId> --json --no-input
```

Create or update after confirmation:

```bash
gog-safe calendar create primary \
  --summary "Meeting title" \
  --from 2026-04-28T10:00:00+02:00 \
  --to 2026-04-28T10:30:00+02:00 \
  --attendees "alice@example.com,bob@example.com" \
  --send-updates all \
  --json --no-input

gog-safe calendar update primary <eventId> \
  --summary "Updated title" \
  --from 2026-04-28T11:00:00+02:00 \
  --to 2026-04-28T11:30:00+02:00 \
  --send-updates all \
  --json --no-input
```

## Guardrails

- Default to read-only calendar work until the operator confirms a mutation.
- Do not send attendee notifications unless the operator confirms it.
- Do not delete events without confirming the exact event ID and title.
