---
name: Google Workspace Mail
description: Use Gmail through the gog-safe wrapper for searching, reading, drafting, replying, forwarding, and sending email. Requires the Google Workspace gmail service to be authorized.
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-18"
---

# Skill: Google Workspace Mail

Use this skill for Gmail work through `gog-safe`.

## Required Authorization

- Control Center service: `gmail`.
- If commands fail with insufficient scopes, ask the operator to reconnect
  Google Workspace with Mail enabled.
- The Control Center wrapper intentionally avoids Gmail settings/delegation
  scopes. Do not try to manage forwarding, filters, send-as aliases, vacation
  responders, or delegation.

## Workflow

1. Check account state with `gog-safe status --json`.
2. Search narrowly before reading full messages.
3. Summarize findings with message/thread IDs and relevant dates.
4. Create drafts freely when requested.
5. Send, forward, archive, label, or mark mail only after explicit confirmation.

## Commands

```bash
gog-safe gmail search 'in:inbox newer_than:7d' --max 20 --json --no-input
gog-safe gmail thread get <threadId> --json --no-input
gog-safe gmail get <messageId> --json --no-input
gog-safe gmail attachment <messageId> <attachmentId> --out ./attachment.bin --no-input
```

Draft and send:

```bash
gog-safe gmail drafts create --to user@example.com --subject "Subject" --body-file ./message.txt --json --no-input
gog-safe gmail send --to user@example.com --subject "Subject" --body-file ./message.txt --json --no-input
gog-safe gmail send --reply-to-message-id <messageId> --quote --to user@example.com --subject "Re: Subject" --body-file ./reply.txt --json --no-input
gog-safe gmail forward <messageId> --to user@example.com --note "FYI" --json --no-input
```

Safe label operations after confirmation:

```bash
gog-safe gmail labels list --json --no-input
gog-safe gmail labels modify <threadId> --add STARRED --remove INBOX --json --no-input
```

## Guardrails

- Never send a final email without showing recipient, subject, and body first.
- Treat attachments as potentially sensitive. Save them only to task/document
  paths, not random working directories.
- Do not perform broad mailbox exports unless the operator explicitly asks.
