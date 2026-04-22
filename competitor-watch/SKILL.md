---
category: Control Center Integration
---

# Skill: Competitor Watch

Monitor competitors without obsessing over them. Track changes, spot opportunities, move on.

## Data File

Store observations in `memory/competitors.json`:

```json
{
  "competitors": [
    {
      "name": "CompetitorX",
      "url": "https://competitorx.com",
      "pricingUrl": "https://competitorx.com/pricing",
      "changelogUrl": "https://competitorx.com/changelog",
      "twitter": "@competitorx",
      "notes": "Main competitor. Targets enterprise more than us.",
      "observations": [
        {
          "date": "2025-01-15",
          "type": "pricing",
          "detail": "Raised prices from $19 to $29/mo. Free tier removed."
        },
        {
          "date": "2025-01-20",
          "type": "feature",
          "detail": "Launched API v2. Added webhooks support."
        }
      ]
    }
  ],
  "lastFullScan": null
}
```

## Commands

### Add Competitor

When the user says "track [competitor]" or "watch [competitor]":

1. Ask for (or find): name, URL, pricing page, changelog, Twitter handle
2. Add to `memory/competitors.json`
3. Do an initial scan of their pricing page and recent activity
4. Log first observations

### Scan Competitors

During heartbeats (once daily) or when asked:

1. Read `memory/competitors.json`
2. For each competitor, fetch their pricing page using `web_fetch`
3. Compare to last known state (previous observations)
4. If anything changed, log a new observation
5. Check their Twitter for notable announcements (if accessible)

**What to look for:**
- Pricing changes (new plans, price increases/decreases, free tier changes)
- New features announced
- Funding announcements
- Public metrics they share (user count, revenue)
- Hiring activity (indicates where they're investing)
- Negative signals (layoffs, downtime, user complaints)

### Competitor Report

When asked for a report or during weekly review:

```
🔍 Competitor Update - [date]

**[Competitor Name]**
- [Recent observations]
- Pricing: [current pricing summary]
- Last notable change: [what and when]
- What it means for us: [brief analysis]

**[Next Competitor]**
- ...

No changes: [list competitors with no recent activity]
```

### Quick Compare

When the user asks "how do we compare to X?":

Pull from stored observations and provide:
- Feature comparison (what we have that they don't, and vice versa)
- Pricing comparison
- Positioning difference
- Where we win, where they win

## Rules

- **Check weekly, not daily.** Competitors are a distraction if you let them be. One thorough check per week is enough.
- **Always tie back to action.** "They raised prices" is an observation. "They raised prices, which means our $19/mo plan is now the cheapest option, worth mentioning on our pricing page" is useful.
- **Don't copy.** Track competitors to find opportunities, not to clone features.
- **Log everything.** Even small changes add up to a pattern over time.
- **Pricing changes are gold.** When a competitor changes pricing, it's almost always worth a response (even if the response is "do nothing but mention we're cheaper").
- **Watch for weakness.** Customer complaints about competitors on Twitter are potential leads.

## Observation Types

Use these types in the JSON for consistency:
- `pricing` - any pricing or plan change
- `feature` - new feature or product update
- `funding` - investment, revenue, or financial news
- `hiring` - job postings or team changes
- `incident` - downtime, bugs, customer complaints
- `marketing` - campaigns, content, positioning changes
- `other` - anything else notable
