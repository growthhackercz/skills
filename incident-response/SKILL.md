---
category: Support & Ops
---

# Skill: Incident Response

When production is on fire, follow this. No freelancing, no improvising. Work the process.

## Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|---------|
| **P0** | Service down, all users affected | Immediate | App won't load, database unreachable, payments broken |
| **P1** | Major feature broken, many users affected | Within 30 min | Auth broken, API returning 500s, data loss risk |
| **P2** | Feature degraded, some users affected | Within 2 hours | Slow queries, intermittent errors, one integration down |
| **P3** | Minor issue, workaround exists | Within 24 hours | UI glitch, non-critical feature broken, cosmetic issue |

## When to Trigger

- Monitoring alert fires (uptime check, error rate spike, etc.)
- User reports critical bug
- Deploy went wrong and rollback is needed
- You spot something wrong during a heartbeat check

## The Playbook

### Step 1: Assess (first 5 minutes)

1. **What's broken?** Get specific. "The app is down" vs "The /api/users endpoint is returning 503s."
2. **Who's affected?** All users? Some users? One customer? Internal only?
3. **When did it start?** Check monitoring. Correlate with recent deploys.
4. **Assign severity.** Use the table above. When in doubt, go one level higher.

Log immediately in `memory/YYYY-MM-DD.md`:
```
🚨 INCIDENT [P-level]: [brief description]
Started: [time]
Detected: [time]
Status: investigating
```

### Step 2: Communicate (next 2 minutes)

- Notify the dev: "🚨 P[X] incident: [what's broken]. Investigating now."
- If there's a status page, update it.
- If it affects customers, prepare a message (but don't send until you know more).

### Step 3: Triage (next 10-15 minutes)

**Check in this order:**

1. **Recent deploys** - Was anything deployed in the last few hours? If yes, that's suspect #1.
2. **Error logs** - What are the actual error messages? Stack traces?
3. **Infrastructure** - Is the server/database/CDN up? Check monitoring dashboards.
4. **External dependencies** - Is a third-party service down? (Stripe, AWS, etc.) Check their status pages.
5. **Traffic** - Traffic spike? DDoS? Unusual patterns?
6. **Database** - Connection pool exhausted? Long-running queries? Disk full?

### Step 4: Fix or Mitigate

**Decision tree:**

- **Caused by recent deploy?** Roll back. Fix forward later. Get production stable first.
- **Infrastructure issue?** Scale up, restart, or failover. Then investigate root cause.
- **External dependency?** Enable fallback if you have one. If not, communicate the dependency to users.
- **Database issue?** Kill long queries, check connections, verify disk space.
- **Unknown?** Enable extra logging, reproduce if possible, narrow down the blast radius.

**Rules during an incident:**
- Fix first, understand later. Restoration beats diagnosis.
- Don't make it worse. Test fixes on staging if time permits. No yolo pushes to prod.
- One change at a time. If you change three things and it's fixed, you don't know which one fixed it.
- Keep a timeline. Log every action you take with timestamps.

### Step 5: Verify Resolution

- [ ] The immediate issue is resolved
- [ ] Monitoring shows normal metrics (error rate, response time)
- [ ] Affected features tested manually
- [ ] No new errors appearing
- [ ] Status page updated (if applicable)
- [ ] Users/team notified that it's resolved

### Step 6: Post-Mortem

Within 24-48 hours of resolution, write a post-mortem. Draft it in `memory/postmortems/YYYY-MM-DD-[slug].md` if needed, then publish the durable summary to shared documents/wiki:

```markdown
# Post-Mortem: [Incident Title]

**Date:** [date]
**Severity:** P[X]
**Duration:** [how long from detection to resolution]
**Author:** [who]

## Summary
[1-2 sentences: what happened and what the impact was]

## Timeline
- [HH:MM] [Event or action taken]
- [HH:MM] [Event or action taken]

## Root Cause
[What actually caused the issue. Be specific. "The deploy had a bug" is not enough. "The migration dropped a NOT NULL constraint that the API relied on for the user query" is.]

## What Went Well
- [Things that helped: monitoring caught it fast, rollback was smooth, etc.]

## What Went Wrong
- [Things that hurt: no alerts, slow detection, unclear runbooks, etc.]

## Action Items
- [ ] [Specific fix to prevent recurrence] - owner: [who] - due: [when]
- [ ] [Process improvement] - owner: [who] - due: [when]
- [ ] [Monitoring/alerting improvement] - owner: [who] - due: [when]

## Lessons Learned
[What did we learn that applies beyond this specific incident?]
```

## Rules

- **No blame.** Post-mortems are about systems, not people. "The deploy process didn't catch X" not "Bob broke production."
- **Always write the post-mortem.** Even for small incidents. The pattern recognition across incidents is where the real value is.
- **Action items need owners and dates.** Otherwise they don't happen.
- **Publish the incident summary and architectural lessons to shared documents/wiki.** Update `MEMORY.md` only if this workspace keeps a curated local overlay.
- **If the same type of incident happens twice, the process failed.** The first one is a bug. The second one is a missing safeguard.
