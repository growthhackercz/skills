import { NextResponse } from "next/server";
import { BASE_URL, TAGS } from "../../../lib/spec";
import { getContact, fieldValue } from "../../../lib/ghl";
import { SCHEDULED_IDS_FIELD_ID, fieldsReady } from "../../../lib/fields";
import { parseScheduledField } from "../../../lib/scheduled-state";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface PersonalizeBody {
  contactId?: string;
}

/**
 * Kick endpoint — personalizační práce běží v Netlify BACKGROUND funkci
 * (/.netlify/functions/personalize-background, 15min limit). Synchronní
 * route narazila na 30s wall-clock limit (504 při F2b testu). Tady jen:
 * validace contactId → rychlá idempotence → kick → pending. Stav sleduje
 * /api/personalize/status.
 */
export async function POST(req: Request) {
  let body: PersonalizeBody;
  try {
    body = (await req.json()) as PersonalizeBody;
  } catch {
    return NextResponse.json({ error: "Neplatný požadavek." }, { status: 400 });
  }

  const contactId = (body.contactId ?? "").trim();

  if (!contactId) {
    return NextResponse.json({ error: "Neplatný odkaz." }, { status: 400 });
  }

  if (!fieldsReady()) {
    console.error(
      "[personalize] fields-map.json není vygenerovaná — spusťte scripts/ensure-fields.mjs"
    );
    return NextResponse.json(
      { status: "error", error: "Personalizace není nakonfigurovaná." },
      { status: 500 }
    );
  }

  const internalSecret = (process.env.AIQ_LINK_SECRET ?? "").trim();
  if (!internalSecret) {
    console.error("[personalize] AIQ_LINK_SECRET není nastavené.");
    return NextResponse.json(
      { status: "error", error: "Personalizace není nakonfigurovaná." },
      { status: 500 }
    );
  }

  // Rychlá idempotence: hotovo → ready hned, bez kicku.
  const contact = await getContact(contactId);
  if (!contact) {
    return NextResponse.json({ error: "Kontakt nenalezen." }, { status: 404 });
  }
  const tags = (contact.tags ?? []).map((tag) => String(tag).toLowerCase());
  if (!tags.includes(TAGS.base.toLowerCase())) {
    return NextResponse.json({ error: "Kontakt nenalezen." }, { status: 404 });
  }
  // Hotovo = Scheduled IDs pole má naplánované e-maily (stav žije v poli, ne v tagu).
  const scheduledRaw = fieldValue(contact.customFields, SCHEDULED_IDS_FIELD_ID);
  const scheduled = parseScheduledField(scheduledRaw);
  if (!scheduled.processing && scheduled.ids.length > 0) {
    return NextResponse.json({ status: "ready" });
  }

  // Kick background funkce. Vrací 202 okamžitě; duplicitní kicky řeší
  // idempotence uvnitř runPersonalization (processing marker < 5 min).
  try {
    const res = await fetch(
      `${BASE_URL}/.netlify/functions/personalize-background`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // Interní sdílené tajemství (ne v URL) — chrání background endpoint.
          "x-aiq-internal": internalSecret,
        },
        body: JSON.stringify({ contactId }),
      }
    );
    if (res.status >= 400) {
      console.error("[personalize] background kick failed:", res.status);
      return NextResponse.json({ status: "error" }, { status: 502 });
    }
  } catch (e) {
    console.error(
      "[personalize] background kick error:",
      e instanceof Error ? e.message : e
    );
    return NextResponse.json({ status: "error" }, { status: 502 });
  }

  return NextResponse.json({ status: "pending" });
}
