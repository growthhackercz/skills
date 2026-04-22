---
status: dummy
required_integration: "publishing_apis"
category: Campaign & Strategy
---

# Multichannel Publisher

## Purpose
Package and publish approved assets across multiple channels while preserving channel fit and execution traceability.

## Use when
- the same campaign spans multiple channels
- asset packaging differs by format and platform

## Inputs
- approved assets
- channel rules
- schedule
- metadata and tracking requirements
- approval state

## Outputs
Return:
- channel-by-channel publishing plan
- packaged variants
- publication status
- issue log
- handoff metadata for analytics

## Rules
- do not publish without approval state
- preserve tracking metadata
- respect channel-specific constraints

## Integrations
Ideal integrations:
- channel APIs or scheduling tools
- asset storage
- analytics / UTM management


## Dummy Mode

This skill is in **dummy mode** — required integrations are not yet connected.

When invoked, you MUST:
1. Prefix your entire response with: `⚠️ DUMMY MODE — real data not available, output is simulated`
2. Produce a **complete, structured response** following the Outputs section above
3. Use realistic but clearly **estimated/example** data — never present simulated numbers as real
4. At the end, add a note: `📌 To upgrade this skill to production, connect: [required integration]`

Dummy output is valuable for testing workflows, validating task pipelines and showing stakeholders what the real output will look like.
