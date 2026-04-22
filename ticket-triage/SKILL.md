---
name: ticket-triage
description: Categorize, prioritize, and route incoming support tickets within 60 seconds. Use when new tickets arrive, a batch triage of the queue is needed, or someone asks "what's new in support?"
status: ready
category: Support & Ops
---

# Skill: Ticket Triage

Categorize, prioritize, and route incoming support tickets. The first 60 seconds of a ticket's life determine how fast it gets resolved.

## When to Run

- New ticket arrives (via heartbeat check or manual trigger)
- Batch triage of unprocessed tickets
- "Triage the queue" or "what's new?"

## Workflow

### 1. Read the Ticket

For each new ticket, extract:
- **Customer:** Name, email, plan tier, account age, VIP status
- **Channel:** Where it came from (email, chat, social, in-app)
- **Content:** What they're reporting/asking
- **Tone:** Calm, frustrated, angry, confused, urgent
- **History:** Previous tickets from this customer (check helpdesk, shared knowledge, and optional `MEMORY.md` if maintained for this workspace)

### 2. Categorize

Assign one primary category:

| Category | Examples |
|----------|---------|
| **Bug** | Something broken, error messages, unexpected behavior |
| **How-to** | Setup questions, feature usage, configuration help |
| **Billing** | Charges, refunds, plan changes, invoices |
| **Feature request** | "Can you add...", "It would be great if..." |
| **Account** | Login issues, password resets, access problems |
| **Outage** | Service down, can't access product at all |
| **Feedback** | General opinions, praise, complaints |
| **Integration** | Third-party connections, API questions, webhooks |

Also tag the **product area** (e.g., "payments", "dashboard", "API", "mobile app", "onboarding").

### 3. Set Priority

| Priority | Criteria | Response Target |
|----------|---------|----------------|
| **P1 - Critical** | Service down, data loss, security issue, multiple customers affected | 15 min |
| **P2 - High** | Core feature broken for customer, billing error, VIP customer blocked | 1 hour |
| **P3 - Medium** | Non-blocking bug, how-to for paying customer, integration issue | 4 hours |
| **P4 - Low** | Feature request, general feedback, nice-to-fix cosmetic issue | 24 hours |

**Priority boosters** (bump up one level):
- VIP customer
- Customer on highest-tier plan
- Customer has mentioned canceling
- 3rd+ contact about the same issue
- Public complaint (Twitter, review site)

### 4. Detect Duplicates

Before routing, check:
- shared wiki/documents/memory: is this a known issue with a workaround?
- Recent `memory/YYYY-MM-DD.md` files: same issue reported today?
- `MEMORY.md` Known Issues only if this workspace actually keeps a maintained curated memory file
- If duplicate of known issue: apply the workaround, link to KB article if one exists, add customer to the affected list.

### 5. Route

Based on category and priority, route to the right person:
- Check `USER.md` escalation contacts for routing rules
- Default: assign to whoever handles that category
- P1: immediately escalate per the escalation playbook
- If unsure who should handle it, assign to team lead

### 6. Log the Triage

Add to today's `memory/YYYY-MM-DD.md`:
```
### Ticket Triage
- #[ID]: [Category] / P[X] - [One-line summary] → [Assigned to]
```

If it's a new instance of a recurring issue, update the daily log if this workspace keeps one and, when relevant for future cross-agent retrieval, capture the pattern in shared documents or wiki notes. Update `MEMORY.md` only if this workspace uses it as curated local overlay.

## Output Template

```
🎫 Ticket #[ID] - [Customer Name] ([Plan])

Category: [Bug / How-to / Billing / etc.]
Product Area: [area]
Priority: P[X] - [Critical/High/Medium/Low]
Sentiment: [calm/frustrated/angry/confused]
Duplicate: [Yes - matches known issue X / No]

Summary: [One sentence describing the issue]

Suggested action: [e.g., "Apply workaround from KB#42 and monitor", "Escalate to engineering - new bug", "Reply with billing FAQ link"]
Route to: [Person/team]
```

## Batch Triage Format

When triaging multiple tickets at once:

```
📋 Queue Triage - [X] new tickets

P1 (0): None 🟢
P2 (1): #1234 - API auth broken for enterprise customer → Engineering
P3 (3): #1235, #1236, #1238 - Various how-to and config questions → Support
P4 (2): #1237, #1239 - Feature requests → Logged

Known issue matches: #1236 matches "CSV export timeout" (KB#42 sent)
VIP alert: #1234 is from [Company] (Enterprise plan)
```

## Rules

- Speed matters. Triage should take under 30 seconds per ticket.
- When in doubt about priority, round up. It's easier to deprioritize than to miss something urgent.
- Always check VIP list in `USER.md`. VIP customers get priority treatment.
- A ticket with no response in 2x the SLA target should be re-triaged and flagged.
- Feature requests still get a response. Acknowledge, log, thank them. Don't just close silently.

## Decision Criteria

| Criterion | Threshold | Action |
|-----------|-----------|--------|
| Triage speed | Under 30 seconds per ticket | If triage is taking longer, simplify categorization — don't overthink |
| Priority accuracy | VIP, top-tier plan, cancellation mention, or 3rd+ contact = automatic priority bump | Always check VIP list in USER.md before assigning priority |
| Duplicate detection | Check shared knowledge first, then today's memory file, then optional `MEMORY.md` overlay before routing | If match found, apply workaround and link KB article — do not route as new |
| SLA compliance | No ticket should exceed 2x its priority response target without re-triage | Flag overdue tickets and escalate |
| Categorization | Single primary category + product area tag for every ticket | Ambiguous tickets get the higher-impact category |

## Anti-patterns

| Don't | Why | Instead |
|-------|-----|---------|
| Overthink categorization and spend >60 seconds per ticket | Speed is the point of triage; delays cascade through the entire queue | Categorize in <30 seconds; ambiguous tickets get the higher-impact category |
| Route a duplicate as a new ticket | Wastes agent time and fragments the conversation | Always check shared knowledge, today's memory file, and optional `MEMORY.md` overlay before routing |
| Silently close feature requests without acknowledgment | Customer feels ignored; damages relationship and future feedback willingness | Acknowledge, log, and thank them — even if the answer is "not now" |
| Assign P1 tickets through normal routing | Critical issues need immediate escalation, not queue-based assignment | P1 tickets go straight to escalation playbook — skip normal routing |
| Skip VIP check before setting priority | Missing a VIP customer's ticket causes disproportionate business damage | Always check VIP list in USER.md before finalizing priority |

## Integration

**Uses:**
- `knowledge-base` — KB articles referenced for duplicate detection and workaround delivery
- `customer-health-monitor` — account health and VIP status inform priority boosting
- Shared documents/wiki plus native memory tools — primary source for known issues and historical context for duplicate matching

**Used by:**
- `sla-queue-manager` — triaged tickets with priority and category feed into SLA queue
- `sentiment-tracker` — ticket tone assessment contributes to sentiment scoring
- `incident-response` — P1 tickets and clusters of related issues trigger incident detection
- `daily-standup` — triage summary included in daily support status

## Quality Checklist

- [ ] Customer info extracted (name, email, plan tier, VIP status)
- [ ] Primary category and product area assigned
- [ ] Priority set correctly (with boosters applied where applicable)
- [ ] Duplicate/known issue check completed against shared knowledge and recent daily memory
- [ ] Routed to correct person/team based on category and priority
- [ ] Triage logged to today's memory file (`memory/YYYY-MM-DD.md`)
- [ ] P1 tickets escalated immediately per escalation playbook
- [ ] Feature requests acknowledged and logged (not silently closed)
