# MeetingInsight Contract

`MeetingInsight` je společný formát mezi `fireflies-meeting-intelligence` a
downstream skilly jako `cliqsales-crm-sync` nebo follow-up orchestrátor.

## Schema

```json
{
  "schema": "openclaw.meeting_insight.v1",
  "source": {
    "provider": "fireflies",
    "meeting_id": "string",
    "client_reference_id": "string|null",
    "transcript_url": "string|null",
    "audio_url": "string|null",
    "video_url": "string|null"
  },
  "meeting": {
    "title": "string",
    "date": "ISO-8601|string|null",
    "duration_seconds": 0,
    "language": "string|null",
    "organizer_email": "string|null",
    "participants": [
      {
        "name": "string|null",
        "email": "string|null",
        "phone": "string|null",
        "source_name": "string|null"
      }
    ]
  },
  "identity_resolution": {
    "matched_company_id": "string|null",
    "matched_contact_ids": ["string"],
    "matched_deal_id": "string|null",
    "matched_thread_id": "string|null",
    "confidence": 0.0,
    "requires_confirmation": false,
    "possible_matches": [],
    "match_reasons": []
  },
  "conversation_continuity": {
    "is_first_known_meeting": true,
    "possible_previous_threads": [],
    "confidence": 0.0,
    "continuity_reasons": []
  },
  "sales_insight": {
    "short_summary": "string",
    "meeting_type": "discovery|demo|follow_up|negotiation|support|onboarding|unknown",
    "stage_signal": "new_lead|discovery|qualified|proposal|negotiation|won_signal|lost_risk|unknown",
    "intent_level": "low|medium|high|unknown",
    "pain_points": [],
    "objections": [],
    "buying_signals": [],
    "decision_makers": [],
    "competitors": [],
    "budget_mentions": [],
    "timeline_mentions": [],
    "risks": [],
    "next_steps": [],
    "tasks": [
      {
        "title": "string",
        "description": "string",
        "owner_hint": "string|null",
        "due_date": "ISO-8601|string|null",
        "source_quote": "string|null",
        "confidence": 0.0
      }
    ],
    "recommended_follow_up": {
      "type": "email|call|proposal|internal_review|none",
      "summary": "string",
      "draft_prompt": "string|null"
    }
  },
  "crm_recommendations": {
    "safe_to_write_automatically": [],
    "requires_approval": [],
    "do_not_write": [],
    "suggested_tags": [],
    "suggested_custom_fields": {},
    "suggested_stage_change": {
      "from": "string|null",
      "to": "string|null",
      "reason": "string|null",
      "requires_approval": true
    },
    "suggested_score": {
      "value": 0,
      "reason": "string|null",
      "requires_approval": true
    }
  },
  "quality": {
    "confidence": 0.0,
    "missing_data": [],
    "warnings": []
  },
  "wiki_handoff": {
    "source_kind": "fireflies",
    "source_ref": "fireflies:{meeting_id}",
    "preferred_input": "meeting_insight",
    "meeting_insight_path": "string|null",
    "summary_path": "string|null",
    "raw_payload_path": "string|null"
  }
}
```

## Rule of Thumb

- `sales_insight` říká, co se stalo.
- `identity_resolution` říká, komu to pravděpodobně patří.
- `crm_recommendations` říká, co se smí poslat dál do CRM.
- `quality` říká, čemu agent nevěří.
- `wiki_handoff` je volitelný ukazatel pro Control Center wiki ingest; nesmí
  nahrazovat CRM-safe filtrování ani vytvářet duplicitní webhook/job.
