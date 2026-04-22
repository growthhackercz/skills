---
name: revenue-tracker
description: Track MRR, customer count, and churn in a structured JSON log and generate trend reports. Use when logging revenue updates, generating revenue reports, or monitoring growth milestones and alert thresholds.
status: ready
category: Team & Planning
---

# Revenue Tracker

Track MRR, customers, and churn in a simple JSON log. Report trends on demand. Celebrate wins, flag concerns.

## Data File

Store revenue data in `memory/revenue-log.json`:

```json
{
  "entries": [
    {
      "date": "2025-01-15",
      "mrr": 2450,
      "customers": 48,
      "newCustomers": 3,
      "churned": 1,
      "notes": "Lost 1 customer (downgraded to free), gained 3 from PH launch"
    }
  ],
  "currency": "USD",
  "products": [
    {
      "name": "Pro Plan",
      "price": 29,
      "billing": "monthly"
    },
    {
      "name": "Team Plan",
      "price": 79,
      "billing": "monthly"
    }
  ]
}
```

## Output Structure

### Revenue Files
```
~/documents/{client-slug}/revenue/
├── revenue-report-{YYYY-MM-DD}.md
└── memory/revenue-log.json
```

### Revenue Report Template

```markdown
# Revenue Report — {Date}

**Current MRR:** ${X,XXX}
**Total Customers:** {N}
**Churn Rate:** {X.X}%
**Avg Revenue/Customer:** ${XX}

---

## Trends

| Period | MRR Change | % Change | Net Customers | Churn |
|--------|-----------|----------|--------------|-------|
| 7-day | {+/-}${XX} | {+/-}X% | {+/-}N | N |
| 30-day | {+/-}${XX} | {+/-}X% | {+/-}N | N |
| 90-day | {+/-}${XX} | {+/-}X% | {+/-}N | N |

---

## Growth Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Monthly growth rate | {X.X}% | {Accelerating / Stable / Decelerating / Declining} |
| Revenue per customer | ${XX} | {Rising / Stable / Falling} |
| Net revenue retention | {X}% | {Above 100% = expansion / Below 100% = contraction} |
| Months to next milestone | ~{N} | {At current growth rate} |

---

## Product Breakdown

| Product | Customers | MRR | % of Total |
|---------|-----------|-----|-----------|
| {Pro Plan} | {N} | ${X,XXX} | {X}% |
| {Team Plan} | {N} | ${X,XXX} | {X}% |

---

## Observations

{2-3 specific observations about what's happening and why}

---

## Alerts

{Any threshold breaches — churn > 5%, flat MRR 3+ weeks, milestone approaching}
```

## Workflow

### 1. Log Revenue Update

When the user provides new numbers:

1. Read `memory/revenue-log.json` (create if it doesn't exist)
2. Add a new entry with today's date
3. Save the file
4. If this is a persistent C-level workspace and the change affects active planning, update `MEMORY.md` only as a short local overlay
5. If the update changes shared business understanding, capture the result in shared documents, wiki pages, source pages, or optional structured notes
6. Report the change compared to last entry

**Quick update format:**
```
Revenue Update — {date}
MRR: ${X,XXX} ({+/-}${XX} from last entry)
Customers: {XX} ({+/-}N)
Churn: {N} this period
{Notes if any}
```

### 2. Generate Revenue Report

When asked for a report or during weekly review:

1. Read all entries from `memory/revenue-log.json`
2. Calculate all metrics (see calculation rules below)
3. Apply alert thresholds
4. Check milestones
5. Write observations

### 3. Quick MRR Check

For standups and quick updates:
```
MRR: ${X,XXX} ({+/-}${XX} this week)
```

## Calculation Rules

| Metric | Formula |
|--------|---------|
| MRR change | Current MRR - Previous MRR |
| Growth rate | (Current MRR - Previous MRR) / Previous MRR * 100 |
| Churn rate | Churned customers / Total customers at start of period * 100 |
| Revenue per customer | MRR / Total customers |
| Net revenue retention | (MRR end - new customer MRR) / MRR start * 100 |
| Months to milestone | (Milestone MRR - Current MRR) / Avg monthly MRR growth |

## Alert Thresholds

| Condition | Severity | Action |
|-----------|----------|--------|
| Churn rate > 5% monthly | WARNING | Flag every time it's reported |
| Churn rate > 10% monthly | CRITICAL | Recommend immediate churn analysis |
| MRR flat for 3+ weeks | WARNING | "Flat is the new down" — investigate |
| MRR declining 2+ consecutive periods | CRITICAL | Root cause analysis needed |
| Growth rate decelerating 3+ months | WARNING | Review acquisition channels |
| Revenue per customer declining | WARNING | Check for plan downgrades |

## Milestones to Celebrate

| Milestone | Significance |
|-----------|-------------|
| First paying customer | The hardest one |
| $100 MRR | Proof of concept |
| $500 MRR | Real traction |
| $1,000 MRR | Ramen profitable for some |
| $2,500 MRR | Consistent value delivery |
| $5,000 MRR | Meaningful business |
| $10,000 MRR | Real business territory |
| Every $5k after that | Compounding growth |

When a milestone is hit, make a big deal. Suggest a celebratory tweet. The team chose the hard path — acknowledge the wins.

## Data Rules

- Store amounts as simple dollar numbers (not cents)
- One entry per day max. If multiple updates same day, update existing entry
- Notes field is optional but valuable — capture WHY numbers changed
- Never delete entries — append only (preserves history)
- If data is missing for a period, note the gap, don't interpolate

## Decision Criteria

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Monthly churn rate | >5% | WARNING: flag every time it is reported |
| Monthly churn rate | >10% | CRITICAL: recommend immediate churn analysis |
| MRR trend | Flat for 3+ consecutive weeks | WARNING: investigate acquisition and retention |
| MRR trend | Declining 2+ consecutive periods | CRITICAL: root cause analysis needed |
| Milestone reached | MRR crosses $100, $500, $1K, $2.5K, $5K, $10K, or any $5K increment | Celebrate; suggest a celebratory post |

## Anti-patterns

| Don't | Why | Instead |
|-------|-----|---------|
| Interpolate missing data points | Fabricated numbers destroy trust in financial reports | Note the gap explicitly and report only actual data |
| Report MRR without verifying customer count math | Revenue per customer will be wrong, undermining all derived metrics | Always cross-check MRR = sum of (customers x plan prices) |
| Celebrate milestones during a churn spike | Tone-deaf — team morale suffers if you ignore the bad news | Acknowledge the milestone AND the churn concern together |
| Use vanity metrics (total revenue, gross numbers) | Hides churn and contraction; paints a misleading picture | Always report net metrics (net MRR change, net revenue retention) |
| Delete or overwrite historical entries | Destroys trend analysis and makes auditing impossible | Append only — never modify past entries |

## Integration

**Uses:**
- `crm-opportunity-manager` — pipeline value data feeds revenue forecasts
- `customer-health-monitor` — churn signals and account health scores
- `lead-qualifier` — new customer source tracking for acquisition analysis
- Shared documents/wiki plus optional structured notes — store milestone, risk, or trend changes that other agents may need

**Used by:**
- `upsell-crosssell-planner` — expansion revenue tracked and reported here
- `executive-briefing` — MRR and growth figures included in executive summaries
- `daily-standup` — quick MRR check referenced during standups
- `finance-ops` — financial reporting draws from revenue data

## Quality Checklist

Before delivering any revenue report:

- [ ] All calculations verified (growth rate, churn rate, averages)
- [ ] Trends cover 7-day, 30-day, and 90-day periods
- [ ] Alert thresholds checked and flagged if breached
- [ ] Milestones checked and celebrated if reached
- [ ] Observations are specific (not generic "growth is good")
- [ ] Product breakdown included if multiple products exist
- [ ] Data gaps acknowledged (not hidden)
- [ ] Revenue log file updated and saved
- [ ] MRR figure matches sum of customer calculations
