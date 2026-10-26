import { spec, BASE_URL, TAGS } from "./spec";
import {
  getContact,
  fieldValue,
  addTags,
  removeTags,
  sendEmail,
  updateContactFields,
  CustomField,
} from "./ghl";
import { vocative } from "./vocative";
import {
  wrapEmail,
  pilotSubjectBranch,
  pragueNineAmTimestamp,
} from "./emails";
import {
  SCHEDULED_IDS_FIELD_ID,
  SEQUENCE_END_FIELD_ID,
  personaFieldId,
  fieldsReady,
} from "./fields";
import { bundleFromContact } from "./server";
import { generatePersona } from "./personalize";
import {
  parseScheduledField,
  ScheduledEmailCheckpoint,
} from "./scheduled-state";

const PROCESSING_FRESH_SECONDS = 5 * 60;

export interface RunResult {
  status: "ready" | "pending" | "error" | "not_found" | "not_configured";
  usedFallback?: boolean;
  scheduled?: number;
}

/**
 * Celá personalizační práce (LLM + zápisy + naplánování e-mailů).
 * Idempotentní: ready → vrátí ready; čerstvé processing → pending.
 * Volá se z Netlify BACKGROUND funkce (15min limit) — v synchronní API routě
 * by to narazilo na 30s wall-clock limit (ověřeno 504 při F2b testu).
 */
export async function runPersonalization(
  contactId: string
): Promise<RunResult> {
  if (!fieldsReady()) {
    console.error(
      "[personalize] fields-map.json není vygenerovaná — spusťte scripts/ensure-fields.mjs"
    );
    return { status: "not_configured" };
  }

  const contact = await getContact(contactId);
  if (!contact) return { status: "not_found" };

  const scheduledRaw = fieldValue(contact.customFields, SCHEDULED_IDS_FIELD_ID);
  const {
    processing,
    processingStartedAt,
    ids: doneIds,
    entries: previousEntries,
  } = parseScheduledField(scheduledRaw);

  // Hotovo = Scheduled IDs pole obsahuje naplánované e-maily (ne processing
  // marker). Stav sekvence žije v poli — nahrazuje starý `ready` tag.
  if (!processing && doneIds.length > 0) {
    return { status: "ready" };
  }

  // Lease proti souběžnému běhu. Marker je autoritní i tehdy, když se zápis tagu
  // opozdí; starší než 5 minut považujeme za zaseknutý a bezpečně navážeme.
  const nowSec = Math.floor(Date.now() / 1000);
  if (
    processing &&
    processingStartedAt != null &&
    nowSec - processingStartedAt < PROCESSING_FRESH_SECONDS
  ) {
    return { status: "pending" };
  }

  const startedAt = nowSec;
  const entries = [...previousEntries];
  const entryIds = new Set(entries.map((entry) => entry.emailMessageId));
  const legacyIds = doneIds.filter((id) => !entryIds.has(id));

  async function persistProcessingState(): Promise<void> {
    await updateContactFields(contactId, [
      {
        id: SCHEDULED_IDS_FIELD_ID,
        value: JSON.stringify({
          state: "processing",
          startedAt,
          ids: legacyIds,
          entries,
        }),
      },
    ]);
  }

  // Označ zpracování a zachovej checkpointy z případného předchozího pokusu.
  await addTags(contactId, [TAGS.processing]);
  await persistProcessingState();

  try {
    const bundle = bundleFromContact(contact);

    // Dvě souběžné generace (persona pole + e-maily) se společným request capem.
    const persona = await generatePersona(bundle);

    // Zápis persona polí do GHL přes fields-map.
    const personaFields: CustomField[] = [];
    for (const name of spec.persona_fields) {
      const id = personaFieldId(name);
      if (!id) continue;
      personaFields.push({ id, value: persona.fields[name] ?? "" });
    }
    await updateContactFields(contactId, personaFields);

    // Naplánování e-mailů větve (D+day 9:00 Europe/Prague, Unix SEKUNDY).
    const branch = spec.email_branches[bundle.temperature];
    if (!Array.isArray(branch) || branch.length === 0) {
      throw new Error(`E-mailová větev ${bundle.temperature} je prázdná`);
    }
    if (new Set(branch.map((step) => step.id)).size !== branch.length) {
      throw new Error(`E-mailová větev ${bundle.temperature} obsahuje duplicitní step id`);
    }
    const voc = vocative(contact.firstName || "");
    const ctaUrl = `${BASE_URL}/online/${encodeURIComponent(contactId)}`;

    const completedStepIds = new Set(entries.map((entry) => entry.stepId));
    for (const step of branch) {
      if (completedStepIds.has(step.id)) continue;
      const gen = persona.emails.find((e) => e.id === step.id);
      if (!gen) {
        throw new Error(`Personalizace nevrátila e-mail pro krok ${step.id}`);
      }
      const html = wrapEmail({
        vocativeName: voc,
        bodyHtml: gen.body_html,
        ctaUrl,
        ctaLabel: "Zobrazit moje doporučení",
      });
      const ts = pragueNineAmTimestamp(step.day);
      const result = await sendEmail({
        contactId,
        subject: pilotSubjectBranch(gen.subject),
        html,
        scheduledTimestamp: ts,
      });
      if (!result.emailMessageId) {
        throw new Error(`GHL nevrátilo ID naplánovaného e-mailu pro krok ${step.id}`);
      }
      entries.push({
        stepId: step.id,
        emailMessageId: result.emailMessageId,
        scheduledTimestamp: ts,
      });
      completedStepIds.add(step.id);
      // Append-only checkpoint po KAŽDÉM externím zápisu. Pád dalšího kroku
      // nesmí při retry znovu naplánovat už vytvořené e-maily.
      await persistProcessingState();
    }

    const emailIds = [
      ...new Set([...legacyIds, ...entries.map((entry) => entry.emailMessageId)]),
    ];
    const scheduledTimestamps = entries.map((entry) => entry.scheduledTimestamp);
    if (branch.some((step) => !completedStepIds.has(step.id))) {
      throw new Error("E-mailová větev nebyla naplánována kompletně");
    }

    // Datum konce sekvence = poslední naplánovaný e-mail → guard z něj pozná
    // přirozený konec (`completed`). Bez e-mailů = teď.
    const sequenceEnd = scheduledTimestamps.length
      ? Math.max(...scheduledTimestamps)
      : Math.floor(Date.now() / 1000);

    // Stav do polí: Scheduled IDs (array = hotovo) + Sequence End.
    const stateFields: CustomField[] = [
      { id: SCHEDULED_IDS_FIELD_ID, value: JSON.stringify(emailIds) },
    ];
    if (SEQUENCE_END_FIELD_ID) {
      stateFields.push({ id: SEQUENCE_END_FIELD_ID, value: String(sequenceEnd) });
    }
    // Nejdřív přidej `active`, pak teprve zapiš finální stav. Kdyby tag selhal,
    // processing checkpoint zůstane obnovitelný a další pokus opravu dokončí.
    await addTags(contactId, [TAGS.active]);
    await updateContactFields(contactId, stateFields);

    // Finální pole je zapsané, přechodný lease může pryč. Jeho úklid už nesmí
    // změnit úspěšně naplánovanou sekvenci na chybu.
    try {
      await removeTags(contactId, [TAGS.processing]);
    } catch (e) {
      console.warn(
        "[personalize] processing tag cleanup failed:",
        e instanceof Error ? e.message : e
      );
    }

    return {
      status: "ready",
      usedFallback: persona.usedFallback,
      scheduled: emailIds.length,
    };
  } catch (e) {
    console.error("[personalize] failed:", e instanceof Error ? e.message : e);
    // Processing marker i tag ponecháme. Po vypršení lease další pokus naváže
    // z append-only checkpointů a již naplánované e-maily nepřidá podruhé.
    return { status: "error" };
  }
}
