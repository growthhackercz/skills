import { NextResponse } from "next/server";
import { TAGS } from "../../../../lib/spec";
import { getContact, fieldValue } from "../../../../lib/ghl";
import { SCHEDULED_IDS_FIELD_ID } from "../../../../lib/fields";
import { parseScheduledField } from "../../../../lib/scheduled-state";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/personalize/status?c={contactId}
 * → { status: "ready" | "pending" | "idle" } dle stavových tagů.
 */
export async function GET(req: Request) {
  const url = new URL(req.url);
  const contactId = (url.searchParams.get("c") ?? "").trim();

  if (!contactId) {
    return NextResponse.json({ error: "Neplatný odkaz." }, { status: 400 });
  }

  try {
    const contact = await getContact(contactId);
    if (!contact) {
      return NextResponse.json({ error: "Kontakt nenalezen." }, { status: 404 });
    }

    const tags = contact.tags ?? [];
    const scheduledRaw = fieldValue(contact.customFields, SCHEDULED_IDS_FIELD_ID);

    // Hotovo = finální pole má naplánované e-maily. Průběžný marker může
    // obsahovat už naplánované kroky, ale dokud má startedAt, je stále pending.
    let status: "ready" | "pending" | "idle" = "idle";
    const scheduled = parseScheduledField(scheduledRaw);
    if (!scheduled.processing && scheduled.ids.length > 0) {
      status = "ready";
    } else if (
      scheduled.processing ||
      tags.some((t) => t.toLowerCase() === TAGS.processing)
    ) {
      status = "pending";
    }

    return NextResponse.json({ status });
  } catch (e) {
    console.error(
      "[personalize/status] failed:",
      e instanceof Error ? e.message : e
    );
    return NextResponse.json({ status: "idle" }, { status: 200 });
  }
}
