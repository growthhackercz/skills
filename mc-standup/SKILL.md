---
name: Daily Standup
description: Generate and deliver daily standup reports summarizing team progress, blockers, and priorities
category: Team & Planning
version: "1.0"
---

# Daily Standup Skill

You can generate daily standup reports summarizing the team's work. Use this when asked for a status update, daily report, or standup.

## How to Generate a Standup

Call the Control Center standup API:

```bash
curl -s -X POST {{CC_URL}}/api/standup \
  -H "Content-Type: application/json" \
  -H "x-api-key: {{CC_API_KEY}}" \
  -d '{}'
```

### Optional Parameters

```json
{
  "date": "2026-03-08",
  "agents": ["cmo", "cto"]
}
```

- `date` — target date in YYYY-MM-DD format (defaults to today)
- `agents` — filter to specific agents (defaults to all)

### Response Structure

The API response is wrapped as `{ "standup": { ... } }`. The nested report includes:
- **summary** — totals: completed, in_progress, assigned, review, blocked, overdue
- **agentReports** — per-agent breakdown with tasks in each status
- **teamAccomplishments** — recently completed tasks (top 10)
- **teamBlockers** — tasks with blockers or urgent priority
- **overdueTasks** — tasks past due date

## How to Format the Report

When presenting the standup, format it as a clear, concise summary:

### Template

```
📊 Daily Standup — {date}

**Summary**
✅ {completed} completed | 🔄 {inProgress} in progress | 📋 {assigned} assigned | 🔍 {review} in review | ⚠️ {blocked} blocked

**Per Agent**
For each agent with activity:
- **{agent_name}** ({role}): {completed} done, {inProgress} active
  - Completed: {task titles}
  - Working on: {task titles}
  - Blocked: {task titles if any}

**Accomplishments**
- {completed task titles with agent names}

**Blockers** (if any)
- {blocked task titles with agent names and reasons}

**Overdue** (if any)
- {overdue task titles with due dates}
```

## When This Skill Activates

- User asks: "standup", "daily report", "status update", "what's happening", "team progress"
- Scheduled via cron: daily automated standup generation

## After Generating

1. Present the formatted report to the user
2. If there are blockers or overdue tasks, highlight them prominently
3. Suggest priorities for today based on assigned + in_progress tasks
4. Save important insights to shared documents/wiki, or to structured notes only when a small keyed entry is enough
