---
name: Control Center API
description: Create and manage tasks, deliverables, documents, and structured notes via the Control Center REST API
category: Control Center Integration
version: "1.1"
---

# Control Center API Skill

You have access to Control Center (CC), the orchestration dashboard. Use these
API endpoints to coordinate work, publish outputs, and inspect shared context.

## Authentication

All requests require the `x-api-key` header:

```text
x-api-key: {{CC_API_KEY}}
```

Base URL: `{{CC_URL}}`

Use the runtime placeholders, not hardcoded secrets:

- `{{CC_URL}}` = current Control Center base URL
- `{{CC_API_KEY}}` = current operator API key from runtime/env

## Task Management

### Create Task

```bash
curl -s -X POST {{CC_URL}}/api/tasks \
  -H "Content-Type: application/json" \
  -H "x-api-key: {{CC_API_KEY}}" \
  -d '{
    "title": "Task title",
    "description": "Detailed description",
    "assigned_to": "agent_name",
    "priority": "medium",
    "status": "assigned",
    "tags": ["tag1", "tag2"]
  }'
```

**Fields:**

- `title` (required, max 500 chars): Clear, actionable title.
- `description` (optional, max 5000 chars): Detailed context, requirements, and references.
- `assigned_to` (optional, max 100 chars): Agent name or session key such as `ceo`, `cmo`, `cso`, `coo`, `cto`.
- `priority`: `low` | `medium` (default) | `high` | `critical`
- `status`: `inbox` (default) | `assigned` | `in_progress`
- `tags`: Array of strings, e.g. `["marketing", "urgent"]`
- `due_date` (optional): Unix timestamp (seconds).
- `estimated_hours` (optional): Number >= 0.
- `parent_task_id` (optional): Integer parent task ID for child tasks.
- `depends_on` (optional, max 500 chars): Free-text dependency description.
- `project_id` (optional): Integer project ID. Defaults to `1`.
- `metadata` (optional): Arbitrary JSON object for extra data.

**Current runtime behavior:** when `assigned_to` is provided, Control Center
wakes the assignee immediately and the returned task will usually already be in
`in_progress`.

**Response (201):**

```json
{ "task": { "id": 42, "title": "...", "status": "in_progress", ... } }
```

### Update Task

```bash
curl -s -X PUT {{CC_URL}}/api/tasks/{task_id} \
  -H "Content-Type: application/json" \
  -H "x-api-key: {{CC_API_KEY}}" \
  -d '{"status": "review"}'
```

All fields from creation are updatable. Only include fields you want to change.
Additional updatable field:

- `actual_hours` (number >= 0): Track time spent.

**Valid statuses:** `inbox` | `assigned` | `in_progress` | `review` |
`quality_review` | `done` | `blocked` | `failed` | `cancelled`

**Status flow:**

```text
inbox -> assigned -> in_progress -> review
review -> done                 [after required quality approval]
review -> in_progress          [after rejection]
any -> blocked | failed | cancelled
```

**Important:** moving a task to `done` without the required quality approval
returns `403`.

### List Tasks

```bash
curl -s "{{CC_URL}}/api/tasks" \
  -H "x-api-key: {{CC_API_KEY}}"
```

**Optional query parameters:**

- `status` -- filter by one or more statuses, e.g. `?status=in_progress,review`
- `assigned_to` -- filter by agent name, e.g. `?assigned_to=cmo`
- `priority` -- filter by priority, e.g. `?priority=high`
- `project_id` -- filter by project
- `limit` -- max results, default 50, max 200
- `offset` -- pagination offset

**Response:**

```json
{ "tasks": [...], "total": 15, "page": 1, "limit": 50 }
```

### Get Single Task

```bash
curl -s "{{CC_URL}}/api/tasks/{task_id}" \
  -H "x-api-key: {{CC_API_KEY}}"
```

### Get Standup Report

```bash
curl -s -X POST {{CC_URL}}/api/standup \
  -H "Content-Type: application/json" \
  -H "x-api-key: {{CC_API_KEY}}" \
  -d '{}'
```

**Optional body fields:**

- `date`: Target date in `YYYY-MM-DD` format (defaults to today).
- `agents`: Array of agent names to filter, e.g. `["cmo", "cto"]`.

**Response wrapper:** `{ "standup": { ... } }`

The nested standup object includes `summary`, `agentReports`,
`teamAccomplishments`, `teamBlockers`, and `overdueTasks`.

## Deliverables

Deliverables are the outputs of completed work. Every task should produce at
least one deliverable before moving to review.

### Create Deliverable

```bash
curl -s -X POST {{CC_URL}}/api/deliverables \
  -H "Content-Type: application/json" \
  -H "x-api-key: {{CC_API_KEY}}" \
  -d '{
    "task_id": 42,
    "title": "Instagram Posts - Ethiopia Sidamo",
    "type": "text",
    "content": "FULL output here - the complete deliverable text, not a summary.",
    "created_by": "cmo"
  }'
```

**Fields:**

- `task_id` (required for task outputs): The task this deliverable belongs to.
- `title` (required): Descriptive title.
- `type` (required): `text` | `report` | `file` | `link`
- `content` (required for text/report): The full deliverable content.
- `file_path` (optional): Path to a generated file, e.g. `~/documents/output/report.pdf`.
- `created_by` (optional): Agent name. Defaults to authenticated user.

**Critical rules:**

1. **Deliverable first, then review.** Create the deliverable before moving the task to `review`.
2. **Full content required.** Do not store only a summary when the real output is text.
3. **One deliverable per coherent output.** Bundle related text items together when they belong to one outcome.
4. **Prefer `type: "file"` for binaries.** The API normalizes legacy `image` and `document` values to `file`, but use `file` in new calls.

### List Deliverables

```bash
curl -s "{{CC_URL}}/api/deliverables?task_id=42" \
  -H "x-api-key: {{CC_API_KEY}}"
```

**Query parameters:**

- `task_id` -- filter by task
- `created_by` -- filter by agent
- `limit` -- max results (default 50)

## Quality Review

Use this when a parent C-level agent reviews a child task already in `review`.

### Submit Quality Review

```bash
curl -s -X POST {{CC_URL}}/api/quality-review \
  -H "Content-Type: application/json" \
  -H "x-api-key: {{CC_API_KEY}}" \
  -d '{
    "taskId": 42,
    "reviewer": "cmo",
    "status": "approved",
    "notes": "Output is acceptable. Proceeding to the next phase."
  }'
```

**Rules:**

- Use `/api/quality-review` to approve or reject a child task already in `review` or `quality_review`.
- Do **not** force approval by sending `status: "done"` directly to `/api/tasks/{id}`.
- `approved` by the required reviewer moves the task to `done`.
- `rejected` moves the task back to `in_progress` and wakes the assigned agent.

## Documents And Wiki Context

Shared evidence lives under `DOCUMENTS_PATH`. In default local runtimes this is
usually `~/documents/`.

### List Documents

```bash
curl -s "{{CC_URL}}/api/knowledge?search=brand&limit=20" \
  -H "x-api-key: {{CC_API_KEY}}"
```

**Useful query parameters:**

- `agent` -- filter documents by agent name
- `path_prefix` -- limit to one subtree
- `source_type` -- limit to one source type
- `search` -- search `original_name`, `description`, and extracted text
- `latest=0` -- include older revisions
- `limit` -- max results, capped at 500

**Response:**

```json
{
  "documents": [
    {
      "id": 1,
      "original_name": "brand-guide.pdf",
      "path": "brands/client-a/brand-guide.pdf",
      "file_type": "pdf",
      "agent_name": "cmo"
    }
  ]
}
```

### Read Document

Use your native `read` tool to access the file contents directly:

```text
read ~/documents/{path}
```

The `path` field from the API response is relative to the shared documents root.

### How Shared Knowledge Works Now

Primary shared context now comes from:

- task-linked documents and deliverables
- the document registry (`/api/knowledge`)
- wiki source and synthesis pages under `DOCUMENTS_PATH/wiki/main`
- native memory/wiki tools when they are available in runtime

Tasks completed, text/report deliverables, document uploads, and email bodies
are turned into wiki source pages automatically. You do not need a manual
knowledge-graph ingest step.

## Optional Structured Shared Notes

Control Center still exposes `/api/team-memory` for small structured keys. Use
it for lightweight coordination or fast lookup values. Durable shared knowledge
belongs in documents and wiki pages.

### Read Structured Notes

```bash
curl -s "{{CC_URL}}/api/team-memory?team_id=default&scope=brand:*" \
  -H "x-api-key: {{CC_API_KEY}}"
```

**Query parameters:**

- `team_id` -- namespace, default `default`
- `key` -- fetch a single entry by key
- `scope` -- prefix match, e.g. `brand:*` or `ops:*`

**Response (all entries):**

```json
{
  "entries": [
    {
      "id": 1,
      "team_id": "default",
      "key": "brand:voice",
      "content": "...",
      "tags": "[\"brand\"]"
    }
  ]
}
```

### Write Structured Notes (Upsert)

```bash
curl -s -X POST {{CC_URL}}/api/team-memory \
  -H "Content-Type: application/json" \
  -H "x-api-key: {{CC_API_KEY}}" \
  -d '{
    "team_id": "default",
    "key": "brand:voice",
    "content": "Professional but approachable.",
    "tags": ["brand", "guidelines"]
  }'
```

### Delete Structured Notes

```bash
curl -s -X DELETE "{{CC_URL}}/api/team-memory?id={entry_id}" \
  -H "x-api-key: {{CC_API_KEY}}"
```

## Workflow Rules

### For CEO (coordinator)

1. **Delegate, do not execute specialist work yourself.** Pick the right owner and create a task for them.
2. **Check shared context first.** Review documents, deliverables, and wiki context before writing the task brief.
3. **Check existing work before creating new work.** List relevant tasks first so you do not create parallel duplicates.
4. **Review quality carefully.** When a task reaches review, read the deliverable content before approving or rejecting it.

### For all agents

5. **Deliverable first, then review.** Never move a task to `review` without a deliverable.
6. **Put the real output in the deliverable.** The reviewer and operator judge what is actually stored there.
7. **Store findings through outputs, documents, and wiki-backed source material.** Make important knowledge reusable.
8. **Use structured notes sparingly.** Reserve `/api/team-memory` for compact shared keys, flags, or lookups - not as the primary knowledge store.
9. **Report status from the current runtime.** Use the standup endpoint or task lists instead of guessing.
