# CRM Sync Contract

Tento kontrakt popisuje, co smí `cliqsales-crm-sync` převzít z
`MeetingInsight` a jak s tím naložit.

## Auto-write položky

Automaticky zapisuj jen pokud je contact/deal match jasný:

```json
{
  "note": true,
  "tasks": true,
  "existing_safe_tags": true,
  "transcript_link": true,
  "participants_summary": true
}
```
## Approval položky

Tyto položky jen navrhni:

```json
{
  "stage_change": true,
  "deal_value_change": true,
  "owner_change": true,
  "won_lost_status": true,
  "new_contact_on_uncertain_match": true,
  "new_custom_field_schema": true,
  "client_message_send": true
}
```

## Recommended CRM Field Mapping

Pokud jsou custom fields připravené v CliqSales, doporučené mapování:

```text
Fireflies Last Meeting Date        <- meeting.date
Fireflies Last Transcript URL      <- source.transcript_url
Fireflies Last Meeting Summary     <- sales_insight.short_summary
Fireflies Intent Level             <- sales_insight.intent_level
Fireflies Stage Signal             <- sales_insight.stage_signal
Fireflies Open Objections          <- sales_insight.objections
Fireflies Buying Signals           <- sales_insight.buying_signals
Fireflies Next Best Action         <- sales_insight.recommended_follow_up.summary
Fireflies Meeting Confidence       <- quality.confidence
```

## Result Schema

```json
{
  "schema": "openclaw.crm_sync_result.v1",
  "source_meeting_id": "string",
  "mode": "dry_run|write",
  "crm_target": {
    "contact_ids": ["string"],
    "opportunity_id": "string|null",
    "company_or_business_id": "string|null"
  },
  "written": {
    "notes": [{"id": "string", "type": "meeting_summary"}],
    "tasks": [{"id": "string", "title": "string"}],
    "tags": [{"name": "string"}],
    "custom_fields": [{"field": "string", "status": "updated"}]
  },
  "requires_approval": [
    {
      "type": "stage_change|score_change|owner_change|send_message|create_contact",
      "reason": "string",
      "payload": {}
    }
  ],
  "skipped": [
    {
      "type": "string",
      "reason": "string"
    }
  ],
  "errors": []
}
```
