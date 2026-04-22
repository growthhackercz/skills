---
name: content-ideation
description: Generate scored content ideas based on trends, audience questions, and creator expertise. Use when the creator needs topic ideas, during weekly content planning, or when content gaps need filling.
status: ready
category: Content & SEO
---

# Skill: Content Ideation

Generate content ideas based on trends, past performance, audience questions, and the creator's expertise. Maintain a scored backlog. Think cross-platform from the start.

## Output Structure

### Data Files
```
memory/content-ideas.json       # Scored idea backlog
memory/content-log.json         # Published content tracker
```

### Deliverable Format
```
~/documents/{project-slug}/content/
├── ideation-{YYYY-MM-DD}.md    # Ideation session output
└── content-backlog.md           # Current prioritized backlog
```

## Idea Template

Each ideation session produces this exact output:

```markdown
# Content Ideas — {YYYY-MM-DD}

**Creator:** {Name}
**Niche:** {Primary niche}
**Ideas generated:** {N}
**Top picks:** {N with score 4.0+}

---

## Top Ideas (Score 4.0+)

### 1. {Title} — Score: {X.X}

**Hook:** "{First line that stops the scroll}"

**Why this works:** {One sentence — what makes this idea uniquely valuable}

**Scoring:**
| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Audience Demand | {1-5} | {Why this score} |
| Expertise | {1-5} | {Why this score} |
| Timeliness | {1-5} | {Why this score} |
| Repurpose Potential | {1-5} | {Why this score} |
| Unique Angle | {1-5} | {Why this score} |

**Cross-Platform Plan:**
| Platform | Format | Angle |
|----------|--------|-------|
| {Platform 1} | {Format} | {How it adapts} |
| {Platform 2} | {Format} | {How it adapts} |
| {Platform 3} | {Format} | {How it adapts} |

**Source:** {What triggered this idea — analytics, question, trend, conversation}

---

### 2. {Title} — Score: {X.X}
...

---

## Backlog Updates

**Added:** {N new ideas}
**Promoted:** {Ideas moved to "in progress"}
**Pruned:** {Ideas removed and why}
```

## When to Use

- Creator asks "what should I post about?" or "I need ideas"
- During weekly content planning sessions
- When a topic is trending in the creator's niche
- During heartbeats when flagging potential content angles
- When audience questions reveal content gaps

## Data File Structure

Maintain ideas in `memory/content-ideas.json`:

```json
{
  "ideas": [
    {
      "id": 1,
      "title": "Why most tutorial videos fail (and how to fix yours)",
      "hook": "I analyzed my 50 best and worst performing tutorials. The pattern is embarrassingly obvious.",
      "source": "analytics-review",
      "platforms": ["youtube", "twitter-thread", "blog"],
      "score": 4.2,
      "scoring": {
        "audienceDemand": 5,
        "expertise": 4,
        "timeliness": 3,
        "repurposePotential": 5,
        "uniqueAngle": 4
      },
      "status": "idea",
      "addedDate": "2025-01-15",
      "notes": "Based on real data. Could include screenshots."
    }
  ],
  "lastBrainstorm": null
}
```

## Scoring System

Rate each idea 1-5 on five dimensions. Average for final score.

| Dimension | 5 (Excellent) | 3 (Average) | 1 (Poor) |
|-----------|---------------|-------------|----------|
| **Audience Demand** | People actively searching/asking for this | General interest, not urgent | Nobody is looking for this |
| **Expertise** | Creator has unique data or deep experience | Creator knows the topic well | Creator would be guessing |
| **Timeliness** | Trending right now OR timeless evergreen | Relevant but not urgent | Moment has passed |
| **Repurpose Potential** | 5+ pieces across platforms easily | 2-3 pieces with effort | One-and-done content |
| **Unique Angle** | Nobody else has this take/data | Somewhat differentiated | Everyone is saying this |

### Score Thresholds
- **4.0+** = Do this within 7 days. High-priority. Assign to calendar immediately.
- **3.0-3.9** = Solid idea. Schedule within 2-4 weeks.
- **2.0-2.9** = Needs a better angle, timing, or hook. Park it.
- **Below 2.0** = Kill it or save only if a specific trigger could revive it.

## Ideation Process

### 1. Gather Inputs

Before generating ideas, check:
- shared documents/wiki — top performing content patterns, audience insights
- `memory/content-log.json` — what's been published recently (avoid repeats within 60 days)
- `USER.md` — niche, topics, audience, brand voice
- Recent conversations — anything the creator mentioned that's interesting
- Trending topics in their niche (if accessible)
- `MEMORY.md` only if this is a persistent workspace that keeps a curated overlay

### 2. Generate Ideas

Aim for 10 raw ideas. Quality over cleverness. Each idea needs:
- A working title (specific, not vague)
- A hook (the first line that makes someone stop scrolling)
- Which platforms it fits
- Why it would work (the "so what")

**Idea sources that consistently produce winners:**
- Problems the creator recently solved (high expertise + unique angle)
- Questions the audience keeps asking (high demand)
- Contrarian takes on popular advice in the niche (high unique angle)
- Personal stories with a lesson (high repurpose potential)
- Data/results from real experience (inherently unique)
- "Things I wish I knew when I started X" (high demand + expertise)
- Reactions to trending news/discourse in the niche (high timeliness)
- Behind-the-scenes of the creator's process (high unique angle)
- Comparisons and "X vs Y" breakdowns (high demand)
- Mistakes and failures (high engagement — these always perform)

**Title formulas that work:**
- "Why [common approach] is wrong (and what to do instead)"
- "I [did X] for [time]. Here's what happened."
- "[Number] [things] I learned from [specific experience]"
- "The [adjective] guide to [topic] (that nobody talks about)"
- "How [specific person/company] [achieved result]"

### 3. Score and Rank

Score each idea using the 5 dimensions. Sort by score. Present the top 5 with hooks.

### 4. Cross-Platform Angles

For each top idea, sketch how it lives on each platform:

| Platform | Format | Angle | Effort |
|----------|--------|-------|--------|
| YouTube | 10-min video | Full tutorial with screen recording | High |
| Twitter/X | Thread (8 tweets) | Quick tips version with screenshots | Medium |
| Newsletter | Feature section | Personal story + the lesson | Medium |
| Blog | Long-form post | SEO-optimized deep dive | High |
| Instagram | Carousel (10 slides) | Visual summary of key points | Medium |
| LinkedIn | Text post | Professional angle, results-focused | Low |
| TikTok/Reels | 60s video | Hook + 3 quick takeaways | Medium |

### 5. Save and Track

- Add scored ideas to `memory/content-ideas.json`
- Update status as ideas move through the pipeline: `idea` → `planned` → `in-progress` → `published`
- When an idea is published, move it to `memory/content-log.json`
- During weekly reviews, resurface high-scoring ideas that haven't been used
- Prune ideas older than 90 days without action (review, refresh, or remove)

## Rules

- Never suggest ideas outside the creator's niche unless they ask for experiments.
- Hooks matter more than topics. A great hook on a boring topic beats a boring hook on a great topic.
- If the creator has data (analytics, personal results, experiments), always suggest data-driven content. It's inherently unique.
- Don't suggest what everyone else is posting. The value is in the unique angle.
- Evergreen content scores higher than reactive content unless the trend is massive.
- Keep the backlog pruned. Ideas older than 3 months without action should be reviewed and either refreshed or removed.
- When the creator mentions something interesting in passing ("I just figured out why my last video flopped"), immediately flag it as a content idea.
- Never present more than 5 ideas at once. Overwhelm kills action.
- Every idea must have a hook. No hook = not ready to present.

## Workflow

1. **Gather inputs** — Load `content-log.json`, `USER.md`, recent conversations, relevant shared documents, and wiki/memory results to understand the creator's niche, audience, and past performance. Use `MEMORY.md` only as an optional curated overlay in persistent C-level workspaces.
2. **Generate raw ideas** — Brainstorm 10+ ideas from proven sources: problems solved, audience questions, contrarian takes, personal stories, data/results, and trending topics.
3. **Score and rank** — Rate each idea on 5 dimensions (Audience Demand, Expertise, Timeliness, Repurpose Potential, Unique Angle) using 1-5 scale; calculate average score.
4. **Select top ideas** — Pick the top 5 ideas (score 4.0+) and write a compelling hook for each.
5. **Plan cross-platform angles** — For each top idea, map how it adapts to YouTube, Twitter/X, Newsletter, Blog, Instagram, LinkedIn, and TikTok/Reels.
6. **Save and present** — Add scored ideas to `memory/content-ideas.json`, generate the ideation session output, and present top 5 with hooks to the creator.
7. **Maintain backlog** — Update idea statuses (idea/planned/in-progress/published), prune ideas older than 90 days, and resurface high-scoring unused ideas during weekly reviews.

## Decision Criteria

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Idea score | 4.0+ average across 5 dimensions | Schedule within 7 days; assign to calendar immediately |
| Idea score | Below 2.0 | Kill the idea or save only if a specific trigger could revive it |
| Backlog staleness | Idea older than 90 days without action | Review, refresh, or remove during weekly review |
| Duplicate check | Same topic published within last 60 days | Reject; find a fresh angle or defer |
| Presentation limit | Max 5 ideas per session | Cut lower-scoring ideas to avoid overwhelm |

## Anti-patterns

| Don't | Why | Instead |
|-------|-----|---------|
| Suggest generic trending topics unrelated to the creator's niche | Generic ideas dilute brand authority and confuse the audience — followers came for a specific expertise | Every idea must connect to the creator's documented niche, expertise, or audience questions |
| Present ideas without hooks | A topic without a hook is just a category — it gives the creator nothing to start with and won't stop the scroll | Every idea must include a specific, written-out first line/hook before presenting |
| Score all dimensions equally high to make ideas look good | Inflated scores destroy the ranking system — everything looks like a 4.5 and real winners get buried | Score honestly with rationale per dimension; a 2 on Timeliness is fine if other dimensions are strong |
| Suggest 15+ ideas in a single session | Overwhelm kills action — the creator picks nothing when given too many options | Present max 5 scored ideas; keep extras in the backlog for future sessions |
| Recycle a topic published within the last 60 days | Audiences notice repetition quickly and engagement drops on repeated angles | Check content-log.json before presenting; if similar topic exists within 60 days, find a fresh angle or defer |

## Integration

**Uses:**
- `seo-strategy` — keyword demand data informs audience demand scoring dimension
- Native memory/wiki tools plus shared documents — retrieve past performance data, audience insights, and creator context
- `content-calendar-manager` — check existing calendar to avoid scheduling conflicts

**Used by:**
- `content-calendar-manager` — top-scored ideas feed directly into the publishing calendar
- `email-campaigns` — newsletter content drawn from the scored idea backlog
- `multichannel-publisher` — cross-platform plan from ideation guides publishing strategy
- `creative-director` — campaign content ideas inform creative asset briefs

## Quality Checklist

Before presenting any ideation session:

- [ ] At least 10 raw ideas generated before scoring
- [ ] Each presented idea has a specific hook (not just a topic)
- [ ] Scores include per-dimension rationale (not just numbers)
- [ ] No duplicate topics from last 60 days of published content
- [ ] Cross-platform plan included for all 4.0+ ideas
- [ ] Ideas are specific to the creator's niche and voice
- [ ] At least 1 data-driven idea if the creator has analytics/results
- [ ] Backlog updated in `memory/content-ideas.json`
- [ ] Stale ideas (90+ days) flagged for review or pruning
