---
status: dummy
required_integration: "team_reports"
category: Team & Planning
---

# Executive Briefing

## Purpose
Create a compact, decision-ready executive summary from multiple team inputs. The output should help the leadership team understand what matters now without reading raw agent logs.

## Use when
- the day starts and leadership needs an operating picture
- multiple teams have updates and a concise summary is needed
- a major shift, incident or opportunity requires executive awareness

## Inputs
- updates from CMO, CSO and COO
- current KPIs, incidents, risks and blockers
- previous unresolved decisions
- optional human priorities for the day or week

## Outputs
Return:
1. top priorities
2. risks / exceptions
3. opportunities
4. decisions needed
5. recommended next actions
6. open questions / missing data

## Rules
- summarize, do not restate everything
- separate fact, inference and recommendation
- highlight only material issues
- include owner and urgency where possible
- if data is missing, say exactly what is missing

## Integrations
Ideal integrations:
- CRM / pipeline summary
- marketing performance summary
- ticket / queue status
- revenue and payment status
- shared memory / decision log


## Dummy Mode

This skill is in **dummy mode** — required integrations are not yet connected.

When invoked, you MUST:
1. Prefix your entire response with: `⚠️ DUMMY MODE — real data not available, output is simulated`
2. Produce a **complete, structured response** following the Outputs section above
3. Use realistic but clearly **estimated/example** data — never present simulated numbers as real
4. At the end, add a note: `📌 To upgrade this skill to production, connect: [required integration]`

Dummy output is valuable for testing workflows, validating task pipelines and showing stakeholders what the real output will look like.
