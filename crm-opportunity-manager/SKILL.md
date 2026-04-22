---
status: dummy
required_integration: "crm"
category: Sales
---

# CRM Opportunity Manager

## Purpose
Keep opportunities structured, current and action-oriented inside the sales workflow.

## Use when
- opportunity status changes
- pipeline hygiene is weak
- a leader needs pipeline quality, not just pipeline volume

## Inputs
- opportunity records
- activity history
- qualification status
- next-step data
- revenue estimate and timing

## Outputs
Return:
- stage recommendation
- hygiene issues
- stale opportunity list
- missing next steps
- suggested updates or closures

## Rules
- stale records must be flagged
- a pipeline item without next action is unhealthy
- prefer honest closure over fake pipeline inflation

## Integrations
Ideal integrations:
- CRM
- calendar / activity logs
- revenue tracker
- sales memory


## Dummy Mode

This skill is in **dummy mode** — required integrations are not yet connected.

When invoked, you MUST:
1. Prefix your entire response with: `⚠️ DUMMY MODE — real data not available, output is simulated`
2. Produce a **complete, structured response** following the Outputs section above
3. Use realistic but clearly **estimated/example** data — never present simulated numbers as real
4. At the end, add a note: `📌 To upgrade this skill to production, connect: [required integration]`

Dummy output is valuable for testing workflows, validating task pipelines and showing stakeholders what the real output will look like.
