// Pozn.: "server-only" guard odstraněn — modul sdílí i Netlify background funkce (mimo Next runtime by import crashnul). Importuje se výhradně server-side.
import { getContact, fieldValue, GhlContact, CustomField } from "./ghl";
import {
  SCORE_FIELD_ID,
  SEGMENT_FIELD_ID,
  spec,
  Temperature,
} from "./spec";
import {
  Answers,
  Vars,
  buildVars,
  band,
  ctaOffer,
  temperature as computeTemperature,
  categoryLabel,
} from "./funnel";
import {
  SCHEDULED_IDS_FIELD_ID,
  TEMPERATURE_FIELD_ID,
  personaFieldIds,
} from "./fields";
import { parseScheduledField } from "./scheduled-state";

function toAnswerArray(raw: unknown): string[] {
  if (raw == null || raw === "") return [];
  if (Array.isArray(raw)) return raw.map(String).filter(Boolean);
  const text = String(raw);
  return text.includes(", ") ? text.split(", ").filter(Boolean) : [text];
}

/* ---------------- v0.5: full contact bundle ---------------- */

export interface ContactBundle {
  contactId: string;
  firstName: string;
  email: string;
  tags: string[];
  /** All quiz answers rebuilt from custom fields (multi → array). */
  answers: Answers;
  vars: Vars;
  temperature: Temperature;
  /** Persona field values stored in GHL (may be empty strings). */
  persona: Record<string, string>;
  /** True only after the final append-only scheduling state is persisted. */
  personalizationReady: boolean;
  customFields: CustomField[];
}

/** Build a full bundle from an already-fetched GHL contact (no extra GET). */
export function bundleFromContact(contact: GhlContact): ContactBundle {
  const fields = contact.customFields;
  const firstName = contact.firstName || "";

  // Rebuild the full answers object from all question fields.
  const answers: Answers = {};
  for (const q of spec.questions) {
    const raw = fieldValue(fields, q.field_id) as unknown;
    if (raw == null || raw === "") continue;
    answers[q.id] = q.type === "multi" ? toAnswerArray(raw) : String(raw);
  }

  const derived = buildVars({ firstName, answers });

  // Stored score is authoritative (submit-time decision).
  const parsedScore = parseInt(fieldValue(fields, SCORE_FIELD_ID), 10);
  if (!Number.isNaN(parsedScore)) {
    derived.score = Math.min(Math.max(parsedScore, 0), 100);
    derived.category_key = band(derived.score);
    derived.score_category = categoryLabel(derived.category_key);
    derived.cta_offer = ctaOffer(derived.category_key, derived.recommended_variant);
  }

  // Stored segment is authoritative.
  const storedSegmentKey = fieldValue(fields, SEGMENT_FIELD_ID);
  if (storedSegmentKey) {
    const segment = spec.segments.find((s) => s.key === storedSegmentKey);
    if (segment) {
      derived.segment_headline = segment.headline;
      derived.segment_proof = segment.proof;
    }
  }

  // Teplota: uložená hodnota ze submitu je autoritativní (rozhodnuto ve chvíli,
  // kdy jsme měli všechny odpovědi); jinak se přepočítá dle spec.temperature_rules.
  const storedTemp = fieldValue(fields, TEMPERATURE_FIELD_ID)
    .trim()
    .toLowerCase();
  const temperature: Temperature =
    storedTemp === "hot" || storedTemp === "warm" || storedTemp === "cold"
      ? (storedTemp as Temperature)
      : computeTemperature(derived.score, answers);

  // Persona fields stored in GHL (empty string when missing / not generated).
  const persona: Record<string, string> = {};
  const ids = personaFieldIds();
  for (const name of spec.persona_fields) {
    const id = ids[name];
    persona[name] = id ? fieldValue(fields, id) : "";
  }
  const scheduled = parseScheduledField(
    fieldValue(fields, SCHEDULED_IDS_FIELD_ID)
  );

  return {
    contactId: contact.id,
    firstName,
    email: contact.email || "",
    tags: contact.tags ?? [],
    answers,
    vars: derived,
    temperature,
    persona,
    personalizationReady: !scheduled.processing && scheduled.ids.length > 0,
    customFields: fields ?? [],
  };
}

/** Fetch a contact from GHL and build its full bundle. */
export async function getContactBundle(
  contactId: string
): Promise<ContactBundle | null> {
  const contact = await getContact(contactId);
  if (!contact) return null;
  return bundleFromContact(contact);
}
