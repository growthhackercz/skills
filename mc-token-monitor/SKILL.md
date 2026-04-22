---
name: "Token & Budget Monitor"
description: "Track token spending, project budgets, and detect cost anomalies"
category: Control Center Integration
version: "1.0"
status: "ready"
---

# Token & Budget Monitor

Monitor token spending across agents and projects. Use this skill to check budgets, analyze cost trends, and identify anomalies.

## Available Endpoints

### 1. Cost Snapshots (Daily Aggregates)

**GET** `/api/tokens?range=7d` (or `30d`, `90d`)

Returns daily cost data aggregated by agent and model. Use this for trend analysis.

Response includes:
- `sessions[]` — per-agent token usage with computed costs
- `summary` — total input/output tokens, total cost

### 2. Project Budgets

**GET** `/api/projects`

Each project includes:
- `budget_limit` — maximum budget in USD
- `budget_spent` — current cumulative spending (auto-computed from task costs)
- `task_stats` — task counts by status

Check budget burn rate: `budget_spent / budget_limit * 100`

### 3. Model Pricing

**GET** `/api/settings` (admin only)

Budget monitor settings under `budget.*`:
- `budget.warning_threshold_percent` — default 80%
- `budget.critical_threshold_percent` — default 95%
- `budget.anomaly_multiplier` — default 2.0x (vs 7-day average)
- `budget.monitor_interval_minutes` — default 60

### 4. Scheduler Status

**GET** `/api/scheduler`

Check `budget_monitor` task status: last run, next run, last result.

## How to Use

### Check current spending
```
GET /api/tokens?range=7d
```
Look at `summary.totalCost` for the period total.

### Check project budget health
```
GET /api/projects
```
For each project, compute: `(budget_spent / budget_limit) * 100`
- Below 80%: healthy
- 80-95%: warning zone
- Above 95%: critical

### Analyze per-agent costs
From cost snapshots, group by `agent_name` to find top spenders.

### Trigger manual budget check
```
POST /api/scheduler/trigger
Body: { "taskId": "budget_monitor" }
```

## Automated Alerts

The budget monitor cron (hourly by default) automatically:
1. Refreshes `budget_spent` for all projects with budget limits
2. Sends `project.budget_warning` when spending crosses the warning threshold
3. Sends `project.budget_exceeded` when spending crosses the critical threshold
4. Sends `spending.anomaly` when daily spend exceeds the anomaly multiplier × 7-day average

Alerts go to admin webhooks and the Telegram system topic.
