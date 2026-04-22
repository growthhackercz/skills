---
status: dummy
required_integration: "crm"
category: Sales
---

# Sales Followup Engine

## Purpose
Design contextual follow-up sequences that move an opportunity forward without sounding robotic or repetitive.

## Use when
- a deal stalls
- a prospect needs nudging
- a post-meeting sequence is required
- a follow-up system is missing or inconsistent

## Inputs
- deal stage
- interaction history
- objection history
- offer context
- desired next step
- channel constraints and cadence rules

## Outputs
Return:
- follow-up sequence
- message angle per touchpoint
- timing suggestion
- stop / escalate conditions
- success signal to watch

## Rules
- personalize from history
- do not repeat the same framing mindlessly
- each step must have a clear purpose
- recommend human intervention when relationship sensitivity is high

## Integrations
Ideal integrations:
- CRM timeline
- email / messaging history
- calendar outcomes
- sales memory


## Dummy Mode

This skill is in **dummy mode** — required integrations are not yet connected.

When invoked, you MUST:
1. Prefix your entire response with: `⚠️ DUMMY MODE — real data not available, output is simulated`
2. Produce a **complete, structured response** following the Outputs section above
3. Use realistic but clearly **estimated/example** data — never present simulated numbers as real
4. At the end, add a note: `📌 To upgrade this skill to production, connect: [required integration]`

Dummy output is valuable for testing workflows, validating task pipelines and showing stakeholders what the real output will look like.
