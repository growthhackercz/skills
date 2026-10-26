import fieldsMapJson from "../fields-map.json";

/**
 * Mapa persona polí → GHL custom field id.
 *
 * Soubor `fields-map.json` generuje `scripts/ensure-fields.mjs` (idempotentní,
 * creds z env). Před vygenerováním obsahuje placeholder — kód se pak chová
 * defenzivně (zápisy do neexistujících polí se přeskočí).
 */

interface FieldsMap {
  _generated?: boolean;
  persona?: Record<string, string>;
  temperature_field_id?: string | null;
  scheduled_ids_field_id?: string | null;
  sequence_end_field_id?: string | null;
}

const fm = fieldsMapJson as unknown as FieldsMap;

/** GHL field id pole „AIQ - Temperature" ("" když mapa není vygenerovaná). */
export const TEMPERATURE_FIELD_ID: string = fm.temperature_field_id ?? "";

/** GHL field id pole „AIQ [name] - Scheduled IDs" ("" když mapa není vygenerovaná). */
export const SCHEDULED_IDS_FIELD_ID: string = fm.scheduled_ids_field_id ?? "";

/** GHL field id pole „AIQ [name] - Sequence End" (Unix ts posledního e-mailu; guard
 *  z něj pozná přirozený konec sekvence → `completed`). "" když chybí. */
export const SEQUENCE_END_FIELD_ID: string = fm.sequence_end_field_id ?? "";

/** GHL field id pro persona pole (např. "main_headline"), "" když chybí. */
export function personaFieldId(name: string): string {
  return fm.persona?.[name] ?? "";
}

/** Celá persona mapa (field_name → id). */
export function personaFieldIds(): Record<string, string> {
  return fm.persona ?? {};
}

/** True když je fields-map vygenerovaná a použitelná pro zápis. */
export function fieldsReady(): boolean {
  return Boolean(
    fm._generated &&
      TEMPERATURE_FIELD_ID &&
      SCHEDULED_IDS_FIELD_ID &&
      fm.persona &&
      Object.keys(fm.persona).length > 0
  );
}
