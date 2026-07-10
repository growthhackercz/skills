---
name: objection-handler
description: Diagnose the real concern behind a sales objection and return structured response options, proof angles, and reframing. Use when a prospect raises concerns about price/timing/fit/trust, or the team wants a framework before replying live. Requires CRM integration.
required_integration: "crm"
---

# Objection Handler

## Purpose
Help the sales team respond to objections in a structured, context-aware way that moves the conversation forward.

## Use when
- a prospect raises concern about price, timing, fit, trust or risk
- a team wants a response framework before replying live

## Inputs
- objection text or summary
- deal context
- lead profile
- offer rules and commercial limits
- prior objections and responses

## Outputs
Return:
- likely real concern behind the objection
- response options
- proof or reframing suggestions
- recommended next question
- escalation recommendation when needed

## Rules
- diagnose before answering
- avoid manipulative tricks
- stay within approved offer and discount rules

## Integrations
Ideal integrations:
- CRM / call notes
- proposal context
- proof / testimonial library
- sales memory


## Dummy Mode

This skill is in **dummy mode** — required integrations are not yet connected.

When invoked, you MUST:
1. Prefix your entire response with: `⚠️ DUMMY MODE — real data not available, output is simulated`
2. Produce a **complete, structured response** following the Outputs section above
3. Use realistic but clearly **estimated/example** data — never present simulated numbers as real
4. At the end, add a note: `📌 To upgrade this skill to production, connect: [required integration]`

Dummy output is valuable for testing workflows, validating task pipelines and showing stakeholders what the real output will look like.
