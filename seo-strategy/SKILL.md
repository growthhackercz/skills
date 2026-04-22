---
category: Content & SEO
---

# Skill: SEO Strategy

Systematic SEO that compounds over time. Keywords, content, backlinks, and technical health. No black hat tricks, no keyword stuffing. Just solid fundamentals that build organic traffic month after month.

## Data Files

### Keyword Priority List
Maintain in `memory/seo-keywords.json`:

```json
{
  "keywords": [
    {
      "keyword": "best invoicing software for freelancers",
      "cluster": "invoicing",
      "volume": 1200,
      "difficulty": 35,
      "intent": "commercial",
      "currentRank": null,
      "targetRank": 5,
      "assignedPage": null,
      "status": "planned",
      "priority": "high",
      "notes": "Low competition, high buyer intent"
    }
  ],
  "clusters": [
    {
      "name": "invoicing",
      "pillarPage": "/blog/invoicing-guide",
      "keywords": ["invoicing software", "best invoicing tool", "freelance invoicing"],
      "status": "building"
    }
  ],
  "lastUpdated": null
}
```

### Rank Tracking
Track in `memory/seo-rankings.json`:

```json
{
  "snapshots": [
    {
      "date": "2025-01-15",
      "rankings": [
        {"keyword": "invoicing software freelancers", "position": 18, "page": "/blog/invoicing-guide", "change": -3}
      ]
    }
  ]
}
```

## Keyword Research & Clustering

When the user wants to explore new keywords or plan content:

1. **Seed keywords** - Start with what the product does and who it's for
2. **Expand** - Use web search to find related terms, questions, long-tail variations
3. **Cluster** - Group keywords by topic. Each cluster gets one pillar page and supporting content.
4. **Evaluate** - For each keyword: search volume (if available), competition, search intent
5. **Prioritize** - Score by: business relevance, difficulty, intent (buyer intent > informational), volume

**Search Intent Categories:**
- **Informational** - "how to write an invoice" (top of funnel, builds authority)
- **Commercial** - "best invoicing software" (mid-funnel, comparison shoppers)
- **Transactional** - "invoicing software pricing" (bottom of funnel, ready to buy)
- **Navigational** - "[brand name] login" (existing users)

**Prioritize commercial and transactional keywords first.** They're closer to revenue. Fill in informational content to build topical authority.

## Content Gap Analysis

Compare your content to competitors:

1. List competitor pages ranking for your target keywords
2. Identify keywords they rank for that you don't cover
3. Find topics where their content is thin or outdated
4. Prioritize gaps by: business relevance, keyword difficulty, search volume

**Output format:**
```
🔍 Content Gap Analysis

**Missing topics (high priority):**
- [keyword/topic]: competitor ranks #X, we have nothing. Est. volume: X/mo
- [keyword/topic]: ...

**Weak coverage (can improve):**
- [keyword/topic]: we rank #X, competitor ranks #Y. Their content is [better because...]

**Opportunities (low competition):**
- [keyword/topic]: no competitor covers this well. Volume: X/mo, difficulty: low
```

## Backlink Opportunities

Identify realistic link-building opportunities:

- **Resource pages** - Pages that list tools/resources in your niche
- **Broken links** - Competitor backlinks pointing to 404 pages you could replace
- **Guest posting** - Relevant blogs that accept contributions
- **Unlinked mentions** - Sites that mention your brand without linking
- **Data/research** - Original data, surveys, or benchmarks that people cite
- **Tool integrations** - Partners and integrations that could link to you

**Don't spam.** Focus on high-quality, relevant links. One good link from a respected site beats 50 from directories.

## Technical SEO Audit

Periodic checks (monthly or when issues are flagged):

**Crawlability:**
- [ ] Sitemap exists and is submitted to Search Console
- [ ] Robots.txt isn't blocking important pages
- [ ] No orphan pages (pages with no internal links)
- [ ] Canonical tags are correct

**Performance:**
- [ ] Core Web Vitals passing (LCP, FID, CLS)
- [ ] Pages load in under 3 seconds
- [ ] Images are optimized (WebP, lazy loading)
- [ ] No render-blocking resources

**On-Page:**
- [ ] Title tags are unique and include target keyword
- [ ] Meta descriptions are compelling (they affect CTR, not ranking directly)
- [ ] H1 tags are present and relevant
- [ ] Internal linking connects related content
- [ ] URLs are clean and descriptive

**Indexing:**
- [ ] Key pages are indexed (check with `site:yourdomain.com`)
- [ ] No duplicate content issues
- [ ] 301 redirects in place for changed URLs
- [ ] No soft 404s

Log audit results in `memory/seo-audit-YYYY-MM-DD.md`.

## Rank Tracking

During heartbeats (once daily):
1. If SEO tools are accessible, check rankings for priority keywords
2. Log changes in `memory/seo-rankings.json`
3. Flag significant moves (jumped or dropped 5+ positions)
4. Note new keywords appearing in top 50

**Report format:**
```
📈 SEO Ranking Update - [date]

**Movers:**
- "invoicing software" #18 → #12 (+6) 🟢
- "freelance tools" #8 → #11 (-3) 🔴

**New entries:**
- "send invoice online" appearing at #34

**No change:** [X keywords stable]
```

## Rules

- **Content quality first.** No keyword stuffing. Write for humans, optimize for search engines. In that order.
- **One primary keyword per page.** Supporting keywords are fine, but each page should have a clear target.
- **Update existing content before creating new.** A refreshed top-10 page is worth more than a new page starting from zero.
- **Internal linking is free SEO.** Every new piece of content should link to and from related pages.
- **Track what matters.** Rankings are a leading indicator. Traffic is a lagging indicator. Conversions from organic traffic is the number that actually matters.
- **Be patient.** SEO compounds. Month 1 results will be disappointing. Month 6 is where it starts paying off. Month 12 is where it gets exciting.
- **Update the keyword priority list monthly.** Priorities shift as you rank for things and discover new opportunities.