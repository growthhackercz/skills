---
status: dummy
required_integration: "ticketing"
category: Support & Ops
---

# SLA Queue Manager

## Purpose
Keep response queues healthy by prioritizing work according to urgency, SLA exposure and customer impact.

## Use when
- support or operations queues are growing
- response commitments are at risk
- work needs triage and routing

## Inputs
- queue items
- SLA rules
- customer/account context
- current capacity
- priority policy

## Outputs
Return:
- prioritized queue
- SLA risk list
- routing suggestion
- escalation candidates
- queue health summary

## Rules
- urgency, impact and commitment all matter
- do not let noisy low-value work bury critical items
- show why an item is prioritized

## Integrations
Ideal integrations:
- support inbox / ticket platform
- CRM/account context
- team capacity view


## Dummy Mode

This skill is in **dummy mode** — required integrations are not yet connected.

When invoked, you MUST:
1. Prefix your entire response with: `⚠️ DUMMY MODE — real data not available, output is simulated`
2. Produce a **complete, structured response** following the Outputs section above
3. Use realistic but clearly **estimated/example** data — never present simulated numbers as real
4. At the end, add a note: `📌 To upgrade this skill to production, connect: [required integration]`

Dummy output is valuable for testing workflows, validating task pipelines and showing stakeholders what the real output will look like.
