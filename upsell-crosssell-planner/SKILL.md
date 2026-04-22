---
status: dummy
required_integration: "crm"
category: Sales
---

# Upsell Crosssell Planner

## Purpose
Recommend credible expansion opportunities based on customer context, timing and demonstrated need.

## Use when
- a customer is healthy and expansion is possible
- renewal or follow-up creates a natural expansion moment

## Inputs
- account history
- usage / behavior signals
- offer catalog
- satisfaction / risk signals
- commercial rules

## Outputs
Return:
- expansion hypothesis
- why now / why not now
- recommended offer
- trigger conditions
- suggested conversation angle

## Rules
- relevance beats revenue greed
- avoid expansion attempts when health is weak or trust is low
- tie recommendation to observed customer context

## Integrations
Ideal integrations:
- CRM/account history
- product usage
- support / sentiment history
- revenue / billing history


## Dummy Mode

This skill is in **dummy mode** — required integrations are not yet connected.

When invoked, you MUST:
1. Prefix your entire response with: `⚠️ DUMMY MODE — real data not available, output is simulated`
2. Produce a **complete, structured response** following the Outputs section above
3. Use realistic but clearly **estimated/example** data — never present simulated numbers as real
4. At the end, add a note: `📌 To upgrade this skill to production, connect: [required integration]`

Dummy output is valuable for testing workflows, validating task pipelines and showing stakeholders what the real output will look like.
