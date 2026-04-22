---
name: knowledge-base
description: Maintain the knowledge base by detecting gaps, drafting articles, and tracking helpfulness. Use when a support ticket reveals a missing or outdated KB article, or during weekly KB gap reviews.
status: ready
category: Support & Ops
---

# Skill: Knowledge Base Management

Keep the knowledge base accurate, complete, and actually useful. Every ticket that didn't need to be a ticket is a KB failure.

## When to Run

- After resolving a ticket that required a non-obvious answer
- During heartbeat KB gap checks
- Weekly during support review
- When a customer says "I couldn't find this in your docs"

## Output Structure

### KB Management Files
```
memory/
├── kb-gaps.json              # Gap tracking log (topics, ticket counts, priority)
├── kb-metrics.json           # Article helpfulness tracking (views, votes, status)
└── kb-articles/
    └── {article-slug}.md     # Drafted or updated KB articles
```

## Workflow

### 1. Detect Gaps
- Review resolved tickets for topics that could have been self-served
- Check `memory/kb-gaps.json` for existing gap entries on the same topic
- Apply priority rules: 5+ tickets = High, 3-4 = Medium, 1-2 = Low

### 2. Draft or Update Article
- Follow the article structure template (title, steps, common issues)
- Write for the least technical customer; add "Advanced" section if needed
- Test the steps yourself before publishing

### 3. Track Helpfulness
- Log article in `memory/kb-metrics.json` with initial metrics
- Review monthly: healthy (>80% helpful), needs work (50-80%), rewrite (<50%)

### 4. Improve Self-Service
- Identify patterns: in-app tooltip opportunities, onboarding gaps, unclear error messages
- Log improvement suggestions in shared documents/wiki first. Add a daily local note only if this workspace keeps one. Use `MEMORY.md` only as optional curated overlay for persistent agents.

## Gap Detection

### From Tickets

Every resolved ticket, ask: "Could the customer have solved this themselves?"

If yes, check:
1. Does a KB article exist for this topic?
2. Is it findable (good title, proper tags, shows up in search)?
3. Is it accurate and up to date?
4. Is it clear enough for a non-technical user?

If any answer is "no," log it in shared documents/wiki under FAQ / KB updates needed. Add a daily local note only if this workspace keeps one. Use `MEMORY.md` only as optional curated overlay.

### Gap Tracking

Maintain a gap log in `memory/kb-gaps.json`:

```json
{
  "gaps": [
    {
      "topic": "How to set up SSO with Okta",
      "ticketCount": 7,
      "firstReported": "2025-01-10",
      "status": "needs-article",
      "priority": "high",
      "notes": "Customers keep trying the SAML tab instead of OIDC"
    }
  ]
}
```

**Priority rules:**
- 5+ tickets on same topic → High priority, draft article this week
- 3-4 tickets → Medium priority, queue for next batch
- 1-2 tickets → Low priority, note it and watch for more

## Drafting Articles

### Structure

Every KB article should follow this format:

```markdown
# [Clear, searchable title - match what customers would type]

[One sentence: what this article covers and who it's for]

## Before You Start
- [Prerequisites, if any]

## Steps
1. [Step with specific UI references: "Click **Settings** in the left sidebar"]
2. [Next step]
3. [Continue until done]

## Common Issues
- **[Problem]:** [Solution]
- **[Problem]:** [Solution]

## Still Need Help?
Contact us at [support email] and we'll sort it out.
```

### Writing Rules

- **Title = what the customer would search.** "How to connect Stripe" not "Payment gateway integration configuration."
- **Lead with the answer.** If someone just needs a URL or a toggle location, put it in the first line.
- **Use screenshots** for anything that involves navigating a UI. Text instructions for clicking through 5 menus are painful.
- **Test the steps yourself** (or ask someone to). If you can't follow your own article, neither can they.
- **Keep it short.** The best KB article is the one that gets the customer unstuck in 30 seconds.
- **One topic per article.** Don't combine "How to set up billing" with "How to change your plan." Split them.

## Updating Articles

### When to Update

- Product UI changed (new layout, renamed features, moved settings)
- Steps no longer work as described
- Customers are following the article but still contacting support
- A better workaround or method was found
- Feature was added/removed

### Update Process

1. Check the article against the current product
2. Update steps, screenshots, and links
3. Add any new "Common Issues" from recent tickets
4. Update the "last reviewed" date
5. If the article was fundamentally wrong, check if any customers were recently sent this link and follow up

## Article Helpfulness Tracking

Track how well articles perform in `memory/kb-metrics.json`:

```json
{
  "articles": [
    {
      "id": "setup-sso",
      "title": "How to Set Up SSO",
      "views": 340,
      "helpfulVotes": 280,
      "notHelpfulVotes": 45,
      "ticketsAfterViewing": 12,
      "lastUpdated": "2025-01-15",
      "status": "healthy"
    }
  ]
}
```

**Health signals:**
- **Healthy:** High helpful %, low ticket-after-viewing rate
- **Needs work:** Low helpful %, or customers still filing tickets after reading it
- **Outdated:** Not updated in 3+ months, or references old UI/features
- **Dead:** Near-zero views. Either the topic doesn't matter or nobody can find it (fix the title/tags)

## Self-Service Improvements

Beyond articles, look for ways to reduce ticket volume:

- **In-app tooltips:** If customers keep asking about a specific button or setting, suggest the product team add a tooltip.
- **Onboarding flow gaps:** If "getting started" is a top ticket category, the onboarding needs work.
- **Error messages:** If customers screenshot an error and ask "what does this mean?", the error message itself needs to be clearer.
- **Search improvements:** If customers can't find existing articles, the search or article titles need fixing.

Log these suggestions in shared documents/wiki first, add a daily local note only if needed, and include them in the weekly support review.

## Rules

- The best support ticket is the one that never gets filed. KB is how you get there.
- Write for the least technical customer who might read it. You can always add an "Advanced" section.
- Don't let articles rot. A wrong article is worse than no article.
- When in doubt about whether to write an article: if 3 customers asked, write it.
- Always link related articles to each other. Customers rarely have just one question.

## Decision Criteria

| Criterion | Threshold | Action |
|-----------|-----------|--------|
| Gap priority | 5+ tickets on same topic = High (draft this week); 3-4 = Medium (next batch); 1-2 = Low (watch) | Follow priority rules strictly — high-priority gaps block other KB work |
| Article health | Helpful rate above 80% = Healthy; 50-80% = Needs work; below 50% = Rewrite or split | Review unhealthy articles monthly; rewrite before creating new ones |
| Freshness | Articles not updated in 3+ months are flagged Outdated | Schedule review; if references old UI/features, update immediately |
| Self-service deflection | Article should resolve the issue without a follow-up ticket in >80% of cases | If ticket-after-viewing rate exceeds 20%, rewrite the article |
| Searchability | Title must match what customers would type — not internal jargon | Test by searching the title in the help center; if not top-3 result, rename |

## Anti-patterns

| Don't | Why | Instead |
|-------|-----|---------|
| Use internal jargon in article titles | Customers search in their own language; jargon titles are unfindable | Title = what the customer would type: "How to connect Stripe" not "Payment gateway integration configuration" |
| Combine multiple topics in one article | Customers abandon long articles and still file tickets | One topic per article; link related articles to each other |
| Leave articles unreviewed for 3+ months | Outdated steps erode trust and generate more tickets than no article at all | Schedule monthly reviews; flag anything referencing old UI/features |
| Write articles without testing the steps | Untested instructions often skip steps or reference wrong UI elements | Follow your own steps on the live product before publishing |
| Create new articles before fixing unhealthy ones | Low-quality articles actively mislead customers | Rewrite articles with <50% helpful rate before drafting new ones |

## Integration

**Uses:**
- Native memory/wiki tools plus shared documents — search existing articles for duplicates and related content
- Document upload + task outputs + wiki source pages — publish new and updated KB material
- `mc-task-api` — create tasks for article drafts, reviews, and updates
- `ticket-triage` — source gap detection from resolved support tickets

**Used by:**
- `sla-queue-manager` — links KB articles in ticket responses for self-service deflection
- `customer-health-monitor` — KB coverage gaps correlate with client satisfaction

## Quality Checklist

- [ ] Article title matches customer search language (not internal jargon)
- [ ] Lead with the answer — key info in the first line
- [ ] Steps are numbered, specific, and reference exact UI elements
- [ ] "Common Issues" section includes recent ticket learnings
- [ ] Related articles are cross-linked
- [ ] Tested the steps yourself (or had someone else test them)
- [ ] "Last reviewed" date is current
- [ ] Article logged in `memory/kb-metrics.json` for tracking
