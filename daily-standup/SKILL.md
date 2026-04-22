---
name: daily-standup
description: Generate a quick morning standup summarizing yesterday's progress, today's priorities, and blockers. Use when the team starts working or someone asks "what's on today?"
status: ready
category: Team & Planning
---

# Skill: Daily Standup

A quick morning standup to get focused. Takes 2 minutes. Keeps you honest about progress.

## When to Run

- Every morning when the team starts working (trigger manually or via cron)
- Can also be triggered with "standup" or "what's on today?"

## Workflow

### 1. Gather Context

Read these files:
- `memory/YYYY-MM-DD.md` (yesterday) for what happened
- `memory/YYYY-MM-DD.md` (today) for anything already logged
- `USER.md` for current goals and targets

Also gather:
- assigned tasks via `mc-task-api`
- shared context via wiki/documents/memory tools
- `MEMORY.md` only if this is a persistent C-level workspace and the file exists

### 2. Generate the Standup

Format:

```
☀️ **Standup - [Day, Month Date]**

**Yesterday:**
- [What got done, pulled from yesterday's memory file]
- [Or "No log from yesterday" if nothing exists]

**Today's Priorities:**
1. [Most important thing based on active project focus]
2. [Second priority]
3. [Third if applicable]

**Blockers:**
- [Anything stuck or waiting on something external]
- [Or "None" if clear]

**Metrics Pulse:**
- MRR: $X ([+/-] from last check)
- [Any other notable metric changes]

**Quick Note:** [One sentence of encouragement, observation, or gentle nudge]
```

### 3. Rules

- Keep it SHORT. This is a standup, not a report. Max 15 lines.
- Priorities come first from assigned tasks and team lead instructions, then from current shared documents/wiki context, and only lastly from `MEMORY.md` when that file exists.
- If MRR data is available, always include it. The team should see their number every day.
- The "Quick Note" should be genuine. Could be: "Day 3 of the launch streak, keep it going." Or: "That bug from Monday is still open, worth a look?" Or: "You shipped 4 features this week. Solid."
- If there's no yesterday data, don't fake it. Just say "No log from yesterday."
- After generating the standup, log today's priorities to `memory/YYYY-MM-DD.md`.

### 4. Follow-Up

At the end of the day (or next morning), the standup can reference what actually got done vs. what was planned. This builds accountability over time.

## Output Template

```
☀️ **Standup - Tuesday, March 4**

**Yesterday:**
- Shipped pricing page redesign
- Fixed Stripe webhook retry bug
- Replied to 3 support emails

**Today's Priorities:**
1. Write launch announcement blog post
2. Set up Product Hunt listing (draft)
3. Review churn data from last week

**Blockers:**
- Waiting on DNS propagation for new domain (should resolve by noon)

**Metrics Pulse:**
- MRR: $3,240 (+$80 this week)
- 2 new trials yesterday

**Quick Note:** Launch is Thursday. Blog post and PH listing today means tomorrow is just final checks. Good position.
```

## Decision Criteria

| Criterion | Threshold | Action |
|-----------|-----------|--------|
| Length | Maximum 15 lines | Cut lower-priority items; keep only top 3 priorities |
| Data freshness | Yesterday's data from `memory/YYYY-MM-DD.md`; if missing, explicitly state "No log from yesterday" | Never fabricate data |
| MRR inclusion | Always include if data is available; omit section only if no MRR data exists anywhere | Check `memory/revenue-log.json`, recent daily files, and shared knowledge; use `MEMORY.md` only as optional overlay |
| Priorities sourced | Must come from assigned tasks, team lead instructions, shared knowledge, or optional `MEMORY.md` — not invented | If no clear priorities found, flag it and ask |
| Follow-up logging | Today's priorities logged to `memory/YYYY-MM-DD.md` after generation | Fail if standup generated but not logged |

## Anti-patterns

| Don't | Why | Instead |
|-------|-----|---------|
| Invent priorities that aren't in tasks, shared knowledge, optional `MEMORY.md`, or team lead instructions | Fabricated priorities create confusion — the team works on things nobody assigned | Source all priorities from actual data; if nothing is found, flag it and ask rather than guess |
| Generate a standup without logging today's priorities to the daily file | Unlogged standups break the continuity chain — tomorrow's standup has no "yesterday" to reference | Always write priorities to `memory/YYYY-MM-DD.md` after generating the standup |
| List 10+ priorities for the day | Too many priorities means nothing is actually prioritized — everything is equally urgent | Cap at 3-5 priorities; if more exist, explicitly rank and defer the rest |
| Report blockers without suggesting a resolution path | "Blocked on API access" with no next step just acknowledges the problem without moving it forward | Every blocker needs an action: who to contact, what to escalate, or what workaround to try |
| Skip the standup on quiet days ("nothing to report") | Silent days break the rhythm and hide the fact that no progress was made — that itself is a signal | Always generate the standup; "no progress on X" is valuable information, not an excuse to skip |

## Integration

**Uses:**
- `mc-task-api` — pull task status and priorities from Control Center
- Native memory/wiki tools plus shared documents — retrieve active project context, recent decisions, and shared metrics context
- `revenue-tracker` — fetch latest MRR figures for metrics pulse

**Used by:**
- `mc-standup` — Control Center-level standup aggregates data from daily standups
- `executive-briefing` — standup highlights feed into leadership reports

## Quality Checklist

- [ ] Yesterday section reflects actual data (or honestly states "no log")
- [ ] Today's priorities are concrete and actionable (not vague)
- [ ] Blockers section is accurate (not padded or omitted)
- [ ] MRR data included when available
- [ ] Quick Note is genuine and context-aware
- [ ] Total output is under 15 lines
- [ ] Today's priorities logged to memory file after generation
