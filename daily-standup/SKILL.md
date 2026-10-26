---
name: daily-standup
description: Vygeneruje krátký ranní standup shrnující včerejší progres, dnešní priority a blockers. Použij, když tým začíná pracovat nebo se někdo ptá "co je dnes na řadě?"
status: ready
version: "1.0"
publishedAt: "2026-04-25"
category: internal
---

# Skill: Daily Standup

Krátký ranní standup pro rychlé soustředění. Zabere 2 minuty. Drží poctivý
přehled o progresu.

## Kdy ho spustit

- Každé ráno, když tým začíná pracovat (manuálně nebo přes cron)
- Lze spustit i triggerem "standup" nebo "what's on today?"

## Workflow

### 1. Shromáždi kontext

Přečti tyto soubory:
- `memory/YYYY-MM-DD.md` (včerejšek), abys věděl, co se stalo
- `memory/YYYY-MM-DD.md` (dnešek), jestli už je tam něco zapsané
- `USER.md` pro aktuální cíle a targety

Zároveň zjisti:
- assigned tasks přes `mc-task-api`
- shared context přes wiki/documents/memory tools
- `MEMORY.md` jen pokud jde o persistent C-level workspace a soubor existuje

### 2. Vygeneruj standup

Formát:

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

### 3. Pravidla

- Drž to KRÁTKÉ. Je to standup, ne report. Max 15 řádků.
- Priority ber nejdřív z assigned tasks a instrukcí team leada, potom z aktuální shared documents/wiki context a teprve nakonec z `MEMORY.md`, pokud ten soubor existuje.
- Pokud je dostupné MRR data, vždy ho zahrň. Tým by měl své číslo vidět každý den.
- `Quick Note` má být upřímná. Může znít třeba: "Day 3 of the launch streak, keep it going." Nebo: "That bug from Monday is still open, worth a look?" Nebo: "You shipped 4 features this week. Solid."
- Pokud nejsou data za včerejšek, nevymýšlej si je. Prostě napiš "No log from yesterday."
- Po vygenerování standupu zaloguj dnešní priority do `memory/YYYY-MM-DD.md`.

### 4. Follow-Up

Na konci dne (nebo druhý den ráno) může standup odkázat na to, co se skutečně
udělalo vs. co bylo plánované. Tím se časem buduje accountability.

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
