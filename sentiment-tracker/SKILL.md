---
name: sentiment-tracker
description: Monitor customer sentiment across support interactions, flag churn risk, and track mood trends. Use when scoring ticket sentiment, generating weekly sentiment reports, or detecting early churn signals.
status: ready
category: Support & Ops
---

# Skill: Sentiment Tracker

Monitor customer mood across tickets and interactions. Spot frustration early. Detect churn signals. Celebrate happiness.

## How It Works

### Sentiment Scoring

For every customer interaction, assess sentiment on a 1-5 scale:

| Score | Label | Signals |
|-------|-------|---------|
| 1 | **Angry** | ALL CAPS, threats to cancel/go public, profanity, "this is unacceptable" |
| 2 | **Frustrated** | Multiple follow-ups, "still waiting," exasperation, "I've tried everything" |
| 3 | **Neutral** | Straightforward question, no emotional signals, just wants an answer |
| 4 | **Satisfied** | "Thanks," positive tone, quick resolution acknowledged |
| 5 | **Happy** | Praise, "love the product," recommending to others, unsolicited compliments |

### Tracking

Log sentiment data in `memory/sentiment-log.json`:

```json
{
  "entries": [
    {
      "date": "2025-01-15",
      "ticketId": "#1234",
      "customer": "jane@example.com",
      "sentiment": 2,
      "label": "frustrated",
      "signals": ["3rd follow-up", "mentioned switching to competitor"],
      "category": "bug",
      "resolved": false,
      "churnRisk": true
    }
  ],
  "dailySummary": [
    {
      "date": "2025-01-15",
      "avgSentiment": 3.2,
      "ticketCount": 18,
      "angry": 1,
      "frustrated": 3,
      "neutral": 8,
      "satisfied": 4,
      "happy": 2,
      "churnFlags": 2
    }
  ]
}
```

## Priority Flagging

### Immediate Attention (flag during heartbeat)

- **Sentiment 1 (Angry):** Always flag. Include the ticket ID, customer name, plan tier, and what they're angry about.
- **Repeat frustrated:** Customer with 2+ tickets at sentiment 2 or below in the past 7 days.
- **Sentiment drop:** Customer who was previously a 4-5 and is now a 1-2. Something went wrong.
- **Churn signals:** Any of these in the ticket text:
  - "Cancel" / "cancellation" / "close my account"
  - Mentions a competitor by name
  - "Not worth it" / "waste of money"
  - "Looking for alternatives"
  - "This keeps happening"

### Format

```
😤 Sentiment Alert

Customer: [Name] ([Plan])
Current sentiment: [1-2] ([label])
Previous sentiment: [X] (from [date])
Churn risk: [Yes/No]

Trigger: [What happened - e.g., "3rd ticket about export bug, mentioned switching to Competitor X"]
Ticket: #[ID]

Suggested action: [e.g., "Priority response + escalate the bug + offer credit"]
```

## Trend Analysis

### Weekly Sentiment Report

Generate during the weekly support review:

```
📊 Sentiment Report - Week of [date]

Average sentiment: X.X (last week: X.X) [↑/↓/→]

Distribution:
😡 Angry:      X (X%)
😤 Frustrated: X (X%)
😐 Neutral:    X (X%)
😊 Satisfied:  X (X%)
🎉 Happy:      X (X%)

Churn flags: X customers
Top frustration drivers: [list top 3 issues causing low sentiment]
Top happiness drivers: [list top 3 things generating positive sentiment]

Trend: [e.g., "Sentiment improving after last week's bug fix deploy" or "Slight decline, billing confusion driving frustration"]
```

### Monthly Patterns

Look for:
- Sentiment correlation with deployments (did a release break things?)
- Sentiment by customer segment (are enterprise customers happier than free tier?)
- Sentiment by support channel (are chat customers more satisfied than email?)
- Day-of-week patterns (Monday morning frustration is real)

## Churn Prevention

When a customer is flagged as churn risk:

1. **Prioritize their ticket.** Whatever their issue is, move it to the front.
2. **Check their history.** How long have they been a customer? What plan? Previous issues?
3. **Escalate if needed.** If their issue requires engineering, fast-track it.
4. **Personal touch.** A response from a real person (not a template) acknowledging their frustration.
5. **Follow up.** After resolution, check in within 48 hours.
6. **Log it.** Record the operational follow-up in the daily log only if this workspace keeps one. Store durable cross-agent learnings in shared documents or wiki notes. Update `MEMORY.md` only if this workspace maintains a curated persistent overlay.

## Positive Sentiment

Don't just track the bad. When customers are happy:

- Log the praise in shared documents/wiki first. Mirror it into a daily local note only if this workspace keeps one; use `MEMORY.md` only as optional curated overlay.
- Share with the team (engineers love hearing their work made someone happy).
- Ask if they'd be open to a testimonial or review (only if appropriate).
- Note what made them happy. Do more of that.

## Rules

- Sentiment scoring is subjective. Be consistent rather than precise. The trend matters more than any individual score.
- Don't wait for a customer to say "I'm angry." Read between the lines. Short, clipped responses after a long thread are a signal.
- Never tell a customer "our sentiment analysis flagged you." That's creepy. Just respond faster and better.
- A single angry customer is a ticket. A cluster of angry customers is an incident. Know the difference.
- Happy customers are your best marketing channel. Treat positive sentiment as an asset, not just a nice stat.

## Output Structure

```
memory/sentiment-log.json              # Per-interaction sentiment scores + signals
memory/sentiment-reports/
└── YYYY-MM-DD-sentiment-weekly.md     # Weekly sentiment distribution + trends
```

Alerts are sent directly via chat when escalation triggers fire.

## Workflow

1. **Score interaction** — For every customer interaction, assess sentiment on the 1-5 scale based on tone, language signals, and context (angry/frustrated/neutral/satisfied/happy).
2. **Log entry** — Record the sentiment score, signals, category, churn risk flag, and resolution status to `memory/sentiment-log.json`.
3. **Check escalation triggers** — If sentiment is 1 (Angry), sentiment dropped from 4-5 to 1-2, or churn signal keywords detected, generate a Sentiment Alert immediately.
4. **Flag repeat frustration** — If the same customer has 2+ tickets at sentiment 2 or below within 7 days, escalate as high churn risk.
5. **Generate weekly report** — Compile sentiment distribution, average score with week-over-week trend, top frustration drivers, and top happiness drivers.
6. **Activate churn prevention** — For flagged customers: prioritize their ticket, check history, escalate if needed, send personal response, follow up within 48 hours, and log the intervention.
7. **Capture positive signals** — Log praise to shared documents/wiki, share with team, and consider requesting testimonials from sentiment-5 customers. Mirror to `MEMORY.md` only if the local workspace uses it as curated persistent overlay.

## Decision Criteria

| Criterion | Threshold | Action |
|-----------|-----------|--------|
| Immediate escalation | Sentiment 1 (Angry) OR sentiment drop from 4-5 to 1-2 | Flag immediately with ticket ID, customer name, plan tier, and suggested action |
| Churn risk detection | Any churn signal keyword detected (cancel, competitor mention, "not worth it", "looking for alternatives") | Mark `churnRisk: true`; prioritize ticket; follow churn prevention protocol |
| Repeat frustration | 2+ tickets at sentiment 2 or below from same customer within 7 days | Escalate — this customer is at high risk of leaving |
| Weekly trend threshold | Average sentiment drops >0.3 points week-over-week | Investigate root cause — likely a product issue or deployment regression |
| Positive sentiment action | Sentiment 5 (Happy) with specific praise | Log in shared documents/wiki; consider requesting testimonial; share with team |

## Anti-patterns

| Don't | Why | Instead |
|-------|-----|---------|
| Tell a customer "our sentiment analysis flagged you" | Creepy and erodes trust — customers don't want to feel monitored | Just respond faster and with more care; never reveal the scoring |
| Treat a cluster of angry customers as individual tickets | A cluster is an incident, not coincidence — the root cause is systemic | Escalate to incident-response when 3+ customers report the same issue |
| Score sentiment without reading the full thread | Short latest reply may seem neutral but the thread shows mounting frustration | Always assess sentiment in context of the full interaction history |
| Ignore positive sentiment as "just a nice stat" | Happy customers are your best marketing channel and churn buffer | Log praise, share with team, and consider requesting testimonials |
| Apply the same churn prevention for all tiers | Enterprise churn costs 10-50x more than starter churn | Weight response urgency and intervention depth by customer tier |

## Integration

**Uses:**
- `ticket-triage` — ticket data provides raw interaction content for sentiment scoring
- `customer-health-monitor` — health scores add context to sentiment trends
- Native memory/wiki tools plus shared documents — retrieve account context for sentiment analysis

**Used by:**
- `incident-response` — sentiment clusters trigger incident detection
- `sla-queue-manager` — sentiment scores influence queue prioritization
- `executive-briefing` — weekly sentiment trends included in executive summaries
- `daily-standup` — sentiment alerts surface in daily standup reports

## Quality Checklist

- [ ] Every interaction scored on 1-5 scale with consistent criteria
- [ ] Sentiment entry logged to `memory/sentiment-log.json` with all required fields
- [ ] Churn risk flags set correctly based on signal keywords
- [ ] Angry/frustrated customers flagged via Sentiment Alert format
- [ ] Weekly sentiment report generated with distribution and trend analysis
- [ ] Top frustration drivers identified and linked to specific product areas
- [ ] Positive feedback logged and shared with relevant team members
