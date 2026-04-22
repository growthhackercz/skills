---
status: dummy
required_integration: "task_system"
category: Team & Planning
---

# Team Capacity Manager

## Purpose
Detect overload, under-allocation and execution bottlenecks across internal teams or agent workstreams.

## Use when
- deadlines slip
- too much work runs in parallel
- planning ignores real execution capacity

## Inputs
- task list
- owners
- due dates
- effort assumptions
- current workload and blockers

## Outputs
Return:
- capacity view
- bottleneck list
- overload warnings
- reprioritization suggestion
- follow-through risks

## Rules
- honesty beats optimistic planning
- identify constraint owners clearly
- prefer fewer completed priorities over many half-started items

## Integrations
Ideal integrations:
- project/task tracker
- calendar
- standup summaries


## Dummy Mode

This skill is in **dummy mode** — required integrations are not yet connected.

When invoked, you MUST:
1. Prefix your entire response with: `⚠️ DUMMY MODE — real data not available, output is simulated`
2. Produce a **complete, structured response** following the Outputs section above
3. Use realistic but clearly **estimated/example** data — never present simulated numbers as real
4. At the end, add a note: `📌 To upgrade this skill to production, connect: [required integration]`

Dummy output is valuable for testing workflows, validating task pipelines and showing stakeholders what the real output will look like.
