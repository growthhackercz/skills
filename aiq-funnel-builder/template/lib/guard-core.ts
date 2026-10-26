import { TAGS } from "./spec";
import { SCHEDULED_IDS_FIELD_ID, SEQUENCE_END_FIELD_ID } from "./fields";
import {
  searchContactsByTag,
  getContact,
  cancelScheduledEmail,
  addTags,
  removeTags,
  updateContactFields,
  fieldValue,
  GhlContact,
} from "./ghl";
import { parseScheduledField } from "./scheduled-state";

/**
 * Hlídač naplánovaných e-mailů — jádro. Volá ho hodinová Netlify scheduled
 * function `netlify/functions/cron-guard.mts`.
 *
 * 1) `[prefix] - converted` (přidá klient na svůj cíl) → zruš zbývající e-maily,
 *    sundej `[prefix] - active`, vyprázdni Scheduled IDs pole.
 * 2) `[prefix] - active` se Sequence End < teď → přirozený konec → sundej
 *    `active`, přidej `[prefix] - completed`.
 *
 * Vše namespacnuté per funnel (guard sáhne jen na svoje kontakty). Idempotentní:
 * vyprázdněné pole + sundaný `active` znamenají, že příští běh kontakt přeskočí.
 */

export interface GuardResult {
  convertedStopped: number;
  cancelledEmails: number;
  completedMarked: number;
  errors: number;
}

function scheduledIdsFrom(contact: GhlContact): string[] {
  const raw = fieldValue(contact.customFields, SCHEDULED_IDS_FIELD_ID);
  return parseScheduledField(raw).ids;
}

export async function cancelScheduledIds(
  ids: string[],
  cancel: (id: string) => Promise<boolean> = cancelScheduledEmail
): Promise<{ cancelled: number; failed: string[] }> {
  let cancelled = 0;
  const failed: string[] = [];
  for (const id of [...new Set(ids)]) {
    try {
      if (await cancel(id)) cancelled += 1;
      else failed.push(id);
    } catch {
      failed.push(id);
    }
  }
  return { cancelled, failed };
}

export async function runGuard(): Promise<GuardResult> {
  const out: GuardResult = {
    convertedStopped: 0,
    cancelledEmails: 0,
    completedMarked: 0,
    errors: 0,
  };
  const activeLc = TAGS.active.toLowerCase();
  const convertedLc = TAGS.converted.toLowerCase();
  const nowSec = Math.floor(Date.now() / 1000);

  // ── 1) Konvertovaní — stáhnout dřív. ──────────────────────────────────────
  let converted: GhlContact[] = [];
  try {
    converted = await searchContactsByTag(TAGS.converted);
  } catch (e) {
    console.error("[guard] search converted:", e instanceof Error ? e.message : e);
    out.errors += 1;
  }

  for (const cand of converted) {
    try {
      // Čerstvý detail: search index je eventually-consistent; `converted`
      // přidaný před chvílí i pole se čtou spolehlivě až z GET.
      const contact = await getContact(cand.id);
      if (!contact) continue;
      const tags = (contact.tags ?? []).map((t) => String(t).toLowerCase());
      if (!tags.includes(convertedLc)) continue; // stale kandidát
      const isActive = tags.includes(activeLc);
      const isProcessing = tags.includes(TAGS.processing);
      if (!isActive && !isProcessing) continue; // sekvence už zrušená → hotovo

      const cancellation = await cancelScheduledIds(scheduledIdsFrom(contact));
      out.cancelledEmails += cancellation.cancelled;
      if (cancellation.failed.length > 0) {
        // Zachovej jen nezrušené schedule ID. Active/processing tag zůstane,
        // takže další hodinový guard provede bezpečný retry.
        await updateContactFields(contact.id, [
          {
            id: SCHEDULED_IDS_FIELD_ID,
            value: JSON.stringify(cancellation.failed),
          },
        ]);
        console.error(
          `[guard] converted ${contact.id}: nezrušeno ${cancellation.failed.length} e-mailů`
        );
        out.errors += 1;
        continue;
      }
      // Vyprázdni pole + sundej active → idempotence.
      await updateContactFields(contact.id, [
        { id: SCHEDULED_IDS_FIELD_ID, value: "[]" },
      ]);
      await removeTags(
        contact.id,
        [TAGS.active, TAGS.processing].filter((tag) => tags.includes(tag))
      );
      out.convertedStopped += 1;
    } catch (e) {
      console.error(`[guard] converted ${cand.id}:`, e instanceof Error ? e.message : e);
      out.errors += 1;
    }
  }

  // ── 2) Přirozený konec — active + Sequence End < teď → completed. ─────────
  let active: GhlContact[] = [];
  try {
    active = await searchContactsByTag(TAGS.active);
  } catch (e) {
    console.error("[guard] search active:", e instanceof Error ? e.message : e);
    out.errors += 1;
  }

  for (const contact of active) {
    const tags = (contact.tags ?? []).map((t) => String(t).toLowerCase());
    if (tags.includes(convertedLc)) continue; // řešeno v kroku 1
    // Sequence End ze search payloadu (žádný per-kontakt GET pro běžící leady).
    const endRaw = SEQUENCE_END_FIELD_ID
      ? fieldValue(contact.customFields, SEQUENCE_END_FIELD_ID)
      : "";
    const end = Number(endRaw);
    if (!Number.isFinite(end) || end <= 0 || end > nowSec) continue; // sekvence běží
    try {
      await removeTags(contact.id, [TAGS.active]);
      await addTags(contact.id, [TAGS.completed]);
      out.completedMarked += 1;
    } catch (e) {
      console.error(`[guard] completed ${contact.id}:`, e instanceof Error ? e.message : e);
      out.errors += 1;
    }
  }

  console.log(
    `[guard] converted stopped ${out.convertedStopped} (emails ${out.cancelledEmails}), ` +
      `completed ${out.completedMarked}, errors ${out.errors}`
  );
  return out;
}
