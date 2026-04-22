---
status: dummy
required_integration: "crm"
category: Support & Ops
---

# Customer Health Monitor

## Purpose
Track customer risk, satisfaction and expansion readiness from multiple signals.

## Use when
- support load changes
- sentiment worsens
- renewal or upsell decisions are approaching

## Inputs
- ticket history
- response speed / SLA adherence
- sentiment signals
- payment context
- usage or engagement signals
- account history

## Outputs
Return:
- health classification
- risk factors
- positive signals
- next best action
- escalation recommendation

## Rules
- separate annoyance from actual churn risk
- explain the classification
- prioritize prevention over rescue

## Integrations
Ideal integrations:
- support platform
- CRM/account data
- billing/payment data
- sentiment tracker


## Dummy Mode

This skill is in **dummy mode** — required integrations are not yet connected.

When invoked, you MUST:
1. Prefix your entire response with: `⚠️ DUMMY MODE — real data not available, output is simulated`
2. Produce a **complete, structured response** following the Outputs section above
3. Use realistic but clearly **estimated/example** data — never present simulated numbers as real
4. At the end, add a note: `📌 To upgrade this skill to production, connect: [required integration]`

Dummy output is valuable for testing workflows, validating task pipelines and showing stakeholders what the real output will look like.
