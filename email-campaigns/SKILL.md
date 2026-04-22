---
category: Content & SEO
---

# Skill: Email Campaigns

Write emails that get opened, clicked, and acted on. Manage sequences, segment audiences, test everything, and build a swipe file of what works.

## Data Files

### Email Swipe File
Maintain in `memory/email-swipe-file.json`:

```json
{
  "highPerformers": [
    {
      "subject": "Your trial ends tomorrow (here's what you'll lose)",
      "type": "urgency/trial-expiry",
      "openRate": 62,
      "clickRate": 18,
      "sequence": "trial-nurture",
      "date": "2025-01-15",
      "whyItWorked": "Loss aversion + specificity. Listed 3 features they'd lose access to."
    }
  ],
  "subjectLineTests": [
    {
      "date": "2025-01-20",
      "variantA": "New feature: bulk invoicing",
      "variantB": "You asked, we built it",
      "winner": "B",
      "openRateA": 28,
      "openRateB": 41,
      "lesson": "Curiosity gap + 'you' language outperforms feature announcements"
    }
  ]
}
```

### Sequence Tracker
Track active sequences in `memory/email-sequences.json`:

```json
{
  "sequences": [
    {
      "name": "welcome",
      "emails": 5,
      "trigger": "signup",
      "status": "active",
      "metrics": {
        "overallOpenRate": 52,
        "overallClickRate": 12,
        "conversionToTrial": 8.5
      },
      "lastUpdated": "2025-01-15"
    }
  ]
}
```

## Writing Subject Lines

Every important email gets A/B tested subject lines. Generate at least 2 variants.

**Frameworks that work:**
- **Curiosity gap:** "The one metric that predicted our churn" (makes them need to know)
- **Specificity:** "How we increased signups by 34% in 2 weeks" (numbers build credibility)
- **Direct benefit:** "Save 3 hours on invoicing this week" (clear value, fast)
- **Personal/conversational:** "Quick question about your account" (feels 1:1)
- **Urgency (use sparingly):** "Your trial ends in 24 hours" (only when real)

**Rules for subject lines:**
- Under 50 characters performs best on mobile
- Don't use ALL CAPS or excessive punctuation!!!
- Personalization (first name) helps but isn't magic
- Preview text is your second subject line. Use it.
- Never mislead. Clickbait erodes trust and increases unsubscribes.

## Email Sequences

### Welcome Sequence (post-signup)
Goal: activate the user and show them the core value fast.

1. **Immediate** - Welcome + one clear first step ("Here's how to send your first invoice in 2 minutes")
2. **Day 1** - Social proof + quick win ("Sarah sent 14 invoices last week. Here's how to get started")
3. **Day 3** - Overcome the #1 objection or friction point
4. **Day 5** - Feature highlight that solves a specific pain
5. **Day 7** - Soft CTA to upgrade or complete setup

### Nurture Sequence (engaged but not paying)
Goal: build trust, demonstrate value, move toward conversion.

- Educational content related to their use case
- Case studies and customer stories
- Product tips they haven't discovered
- Gentle CTAs every 2-3 emails

### Launch Sequence (product or feature launch)
Goal: build anticipation, drive action on launch day, follow up.

1. **T-7 days** - Teaser ("Something new is coming...")
2. **T-3 days** - Reveal + early access offer
3. **T-1 day** - Reminder + social proof from beta testers
4. **Launch day** - The full announcement. Clear CTA.
5. **T+2 days** - Follow-up for non-openers (different subject line)
6. **T+5 days** - Results/social proof ("500 people already using it")

### Win-Back Sequence (churned or inactive users)
Goal: re-engage users who stopped using the product.

1. **Day 1** - "We noticed you've been away" (no guilt, just value)
2. **Day 4** - What's new since they left (features, improvements)
3. **Day 8** - "Is there something we could do better?" (feedback angle)
4. **Day 14** - Final offer or last chance (discount if appropriate)

### Re-Engagement Sequence (cold email list subscribers)
Goal: clean your list and re-engage the interested.

1. **Email 1** - "Still interested?" with clear yes/no CTA
2. **Email 2** - Best content or offer you have
3. **Email 3** - "Last email unless you click" (and mean it)
4. **No click after 3 emails** - Remove from active list. Clean lists = better deliverability.

## Audience Segmentation

Segment by behavior, not just demographics:

- **By engagement:** active openers, occasional readers, cold subscribers
- **By stage:** free user, trial user, paying customer, churned
- **By source:** how they found you (organic, paid, referral, product hunt)
- **By interest:** what content they clicked on, features they use
- **By value:** high LTV customers vs. low tier

**Segmentation rules:**
- The more targeted the email, the better it performs
- A 500-person targeted segment will outperform a 5,000-person blast
- Update segments monthly based on behavior changes
- Track conversion rates per segment to find your best audience

## Metrics & Benchmarks

Track for every send:
- **Open rate** - Industry average ~20-25%. Your own historical average is the better benchmark.
- **Click rate** - Average ~2-5%. Above 5% is excellent.
- **Unsubscribe rate** - Keep below 0.5% per send. Above 1% means something is wrong.
- **Bounce rate** - Keep below 2%. Hard bounces above 3% signal list quality issues.
- **Conversion rate** - Clicks that turned into the desired action. The number that actually matters.

**When to worry:**
- Open rates dropping over time (deliverability issue or list fatigue)
- Click rates dropping (content not matching audience interest)
- Unsubscribe spike (you sent something wrong or too often)
- Bounces spiking (bad list hygiene)

## Send Time Optimization

**Starting points:**
- B2B: Tuesday-Thursday, 9-11 AM recipient's timezone
- B2C: evenings and weekends can work well
- Newsletters: consistency matters more than timing. Pick a day and stick with it.

**Then test.** Your audience might be different. Run send-time tests over 4-6 weeks to find your sweet spot.

## Rules

- **Always get approval before sending.** Draft the email, show it, get the go-ahead.
- **Every send is a test.** A/B test subject lines on any list over 1,000. Test one variable at a time.
- **Log everything to the swipe file.** High performers and flops. Both teach you something.
- **Clean your list quarterly.** Remove hard bounces immediately. Re-engage or remove cold subscribers.
- **Respect the unsubscribe.** Make it easy, make it work, never send to someone who opted out.
- **Preview text matters.** Don't leave it as "View this email in your browser." Use it as a second subject line.
- **Mobile first.** 60%+ of emails are read on mobile. Short paragraphs. Big buttons. No tiny links.