import { NextResponse } from "next/server";
import { createHmac } from "crypto";
import {
  spec,
  TAGS,
  SCORE_FIELD_ID,
  SEGMENT_FIELD_ID,
} from "../../../lib/spec";
import {
  Answers,
  buildVars,
  computeScore,
  band,
  pickSegment,
  temperature as computeTemperature,
} from "../../../lib/funnel";
import {
  upsertContact,
  addTags,
  sendEmail,
  CustomField,
} from "../../../lib/ghl";
import { vocative } from "../../../lib/vocative";
import { e0Email, pilotSubjectE0 } from "../../../lib/emails";
import { TEMPERATURE_FIELD_ID } from "../../../lib/fields";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface ContactInput {
  firstName?: string;
  lastName?: string;
  email?: string;
  phone?: string;
  consent?: boolean;
  consentProcessing?: boolean;
}

interface SubmitBody {
  answers?: Answers;
  contact?: ContactInput;
  /** Honeypot — legitimní kvíz posílá prázdné, bot často vyplní. */
  website?: string;
}

/** Convert an answer value to the string we store in GHL (multi -> CSV). */
function toGhlValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  if (value == null) return "";
  return String(value);
}

/** Max délka volné textové odpovědi (limit vstupu do GHL i LLM promptu). */
const MAX_TEXT_ANSWER_LENGTH = 1000;
const MAX_NAME_LENGTH = 100;
const MAX_EMAIL_LENGTH = 254;
const MAX_PHONE_LENGTH = 50;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Serverová validace odpovědí (veřejný endpoint — vstupu nevěříme):
 * uzavřené otázky přijímají jen hodnoty z `options`, volný text se ořezává
 * na MAX_TEXT_ANSWER_LENGTH. Neznámé otázky se zahazují.
 */
function sanitizeAnswers(raw: Answers): Answers {
  const clean: Answers = {};
  for (const q of spec.questions) {
    const value = raw[q.id];
    if (value == null) continue;
    if (q.type === "textarea") {
      const text = (Array.isArray(value) ? value.join(", ") : String(value))
        .slice(0, MAX_TEXT_ANSWER_LENGTH)
        .trim();
      if (text) clean[q.id] = text;
    } else {
      const allowed = new Set(q.options ?? []);
      const values = (Array.isArray(value) ? value : [value])
        .map((v) => String(v))
        .filter((v) => allowed.has(v));
      if (values.length === 0) continue;
      clean[q.id] = q.type === "multi" ? values : values[0];
    }
  }
  return clean;
}

/** Fire-and-forget webhook kick (optional, signed). Failures are ignored. */
async function kickWebhook(contactId: string): Promise<void> {
  const url = process.env.AIQ_WEBHOOK_URL;
  if (!url) return;
  try {
    const body = JSON.stringify({ contactId, funnel_slug: spec.funnel_slug });
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    const secret = process.env.AIQ_WEBHOOK_SECRET;
    if (secret) {
      headers["X-AIQ-Signature"] = createHmac("sha256", secret)
        .update(body)
        .digest("hex");
    }
    await fetch(url, { method: "POST", headers, body, cache: "no-store" });
  } catch (e) {
    // Webhook selhání nikdy neblokuje submit.
    console.warn(
      "[submit] webhook kick failed (ignored):",
      e instanceof Error ? e.message : e
    );
  }
}

export async function POST(req: Request) {
  let body: SubmitBody;
  try {
    body = (await req.json()) as SubmitBody;
  } catch {
    return NextResponse.json({ error: "Neplatný požadavek." }, { status: 400 });
  }

  const answers: Answers = sanitizeAnswers(body.answers ?? {});
  const contact = body.contact ?? {};

  const email = (contact.email ?? "").trim();
  const firstName = (contact.firstName ?? "").trim();
  const lastName = (contact.lastName ?? "").trim();
  const phone = (contact.phone ?? "").trim();

  if (
    !firstName ||
    firstName.length > MAX_NAME_LENGTH ||
    lastName.length > MAX_NAME_LENGTH ||
    !EMAIL_RE.test(email) ||
    email.length > MAX_EMAIL_LENGTH ||
    phone.length > MAX_PHONE_LENGTH
  ) {
    return NextResponse.json(
      { error: "Zkontrolujte prosím kontaktní údaje." },
      { status: 400 }
    );
  }

  // Consent je povinný — bez něj nelze analýzu připravit ani odeslat.
  // Obě pole musí být VÝSLOVNĚ true (=== true), ne „jen ne false" — jinak by
  // API klient bez pole souhlas obešel, přestože ho UI vynucuje.
  if (contact.consent !== true || contact.consentProcessing !== true) {
    return NextResponse.json(
      { error: "Bez souhlasu nemůžeme analýzu připravit a odeslat." },
      { status: 400 }
    );
  }

  // Honeypot: skryté pole, které legitimní kvíz posílá prázdné. Vyplněný
  // požadavek odmítneme ještě před GHL zápisem a placenou personalizací.
  const suspectedBot =
    typeof body.website === "string" && body.website.trim() !== "";
  if (suspectedBot) {
    console.warn("[submit] honeypot vyplněn — požadavek odmítnut.");
    return NextResponse.json({ error: "Neplatný požadavek." }, { status: 400 });
  }

  const missingRequiredAnswer = spec.questions.some((question) => {
    if (question.type === "textarea") return false;
    const value = answers[question.id];
    return value == null || value === "" || (Array.isArray(value) && value.length === 0);
  });
  if (missingRequiredAnswer) {
    return NextResponse.json(
      { error: "Vyplňte prosím všechny povinné otázky." },
      { status: 400 }
    );
  }

  // 1–5) Score, kategorie, segment, teplota, vars. Výpočet obalený: rozbitý
  // spec (chybějící temperature_rules apod.) nesmí shodit ZÁPIS kontaktu —
  // sběr leada je priorita, teplotu radši degradujeme na bezpečné defaulty.
  let score = 0;
  let category = "";
  let segment: ReturnType<typeof pickSegment> = null;
  let temperature: ReturnType<typeof computeTemperature> = "cold";
  let vars: ReturnType<typeof buildVars>;
  try {
    score = computeScore(answers);
    category = band(score);
    segment = pickSegment(answers);
    temperature = computeTemperature(score, answers);
    vars = buildVars({ firstName, answers });
  } catch (e) {
    console.error(
      "[submit] výpočet skóre/teploty selhal (pokračuji se zápisem kontaktu):",
      e instanceof Error ? e.message : e
    );
    // Bezpečný literál — NEvolat znovu buildVars/band/pickSegment (mohou spadnout
    // ze stejného důvodu). Cíl: zapsat kontakt i při rozbitém specu, sběr leada
    // je priorita. Persona/segment se dopočítá později na /online/ z uložených polí.
    vars = {
      first_name: firstName,
      score: 0,
      score_category: "",
      category_key: "",
      top_pain: "",
      recommended_variant: "",
      segment_headline: "",
      segment_proof: "",
      cta_offer: "",
    };
  }

  // 6) Build custom fields: one per answered question, by field_id.
  const customFields: CustomField[] = [];
  for (const q of spec.questions) {
    const raw = answers[q.id];
    if (raw == null || (Array.isArray(raw) && raw.length === 0) || raw === "") {
      continue;
    }
    customFields.push({ id: q.field_id, value: toGhlValue(raw) });
  }

  // Consent.
  customFields.push({
    id: spec.consent_field_id,
    value: "Ano",
  });

  // Derived: score + segment — jen když builder doplnil derived_field_ids.
  if (SCORE_FIELD_ID) {
    customFields.push({ id: SCORE_FIELD_ID, value: String(score) });
  }
  if (SEGMENT_FIELD_ID) {
    customFields.push({
      id: SEGMENT_FIELD_ID,
      value: segment ? segment.key : "",
    });
  }

  // Temperature — jen když je fields-map vygenerovaná.
  if (TEMPERATURE_FIELD_ID) {
    customFields.push({ id: TEMPERATURE_FIELD_ID, value: temperature });
  } else {
    // Bez uloženého pole si /online/ a /magnet/ teplotu PŘEPOČÍTAJÍ z GHL — a ta
    // rekonstrukce se může lišit (tag `[prefix] - hot lead` visí z těchhle odpovědí,
    // ale e-mailová větev pak pojede z přepočtu). Ať to není tiché.
    console.warn(
      "[submit] TEMPERATURE_FIELD_ID chybí — teplota se neuloží a bude se " +
        "přepočítávat. Ověř, že ensure-fields proběhl (deploy checklist)."
    );
  }

  try {
    const contactId = await upsertContact({
      email,
      firstName: firstName || undefined,
      lastName: lastName || undefined,
      phone: phone || undefined,
      customFields,
    });

    // Odkazy jsou čisté (bez tokenu) — contactId je náhodné GHL id (capability URL).

    // Tagy: base = `[prefix]` (origin, permanentní — podle něj se segmentuje
    // „kdo přišel z tohoto magnetu"). Hot lead → `[prefix] - hot lead`. `[prefix] - active`
    // přidá až personalizace po naplánování e-mailů. Vše namespacnuté per funnel,
    // GHL je lowercasuje (`aiq - [quiz] - …`).
    try {
      const tags = [TAGS.base];
      if (temperature === "hot") tags.push(TAGS.hot);
      await addTags(contactId, tags);
    } catch (e) {
      console.error(
        "[submit] addTags failed:",
        e instanceof Error ? e.message : e
      );
    }

    // E0 — okamžitý deterministický potvrzovací e-mail (bez LLM).
    try {
      const { subject, html } = e0Email(vocative(firstName));
      await sendEmail({
        contactId,
        subject: pilotSubjectE0(subject, email),
        html,
      });
    } catch (e) {
      console.error(
        "[submit] E0 e-mail failed:",
        e instanceof Error ? e.message : e
      );
    }

    // Volitelný webhook kick (podepsaný, failure ignorujeme).
    await kickWebhook(contactId);

    return NextResponse.json({
      contactId,
      score,
      category,
      temperature,
      vars,
    });
  } catch (e) {
    const message =
      e instanceof Error ? e.message : "Zápis do CRM se nezdařil.";
    // Avoid leaking secrets; log server-side only.
    console.error("[submit] GHL upsert error:", message);
    return NextResponse.json(
      { error: "Zápis do CRM se nezdařil." },
      { status: 502 }
    );
  }
}
