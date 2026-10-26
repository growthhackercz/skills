// Netlify BACKGROUND function (suffix -background => 202 okamžitě, limit 15 min).
// Interní endpoint — chráněný sdíleným tajemstvím v hlavičce (x-aiq-internal =
// AIQ_LINK_SECRET), ne tokenem v URL. Kick z /api/personalize hlavičku posílá.
import { timingSafeEqual } from "node:crypto";
import { runPersonalization } from "../../lib/run-personalization";

const handler = async (req: Request) => {
  if (req.method !== "POST") {
    return new Response("method not allowed", {
      status: 405,
      headers: { allow: "POST" },
    });
  }

  // Interní auth je fail-closed: chybějící konfigurace nesmí otevřít placený běh.
  const secret = (process.env.AIQ_LINK_SECRET ?? "").trim();
  if (!secret) {
    console.error("[personalize-background] AIQ_LINK_SECRET is not configured.");
    return new Response("not configured", { status: 500 });
  }

  const provided = req.headers.get("x-aiq-internal") ?? "";
  const expectedBuffer = Buffer.from(secret);
  const providedBuffer = Buffer.from(provided);
  const authorized =
    expectedBuffer.length === providedBuffer.length &&
    timingSafeEqual(expectedBuffer, providedBuffer);
  if (!authorized) {
    return new Response("forbidden", { status: 403 });
  }

  let body: { contactId?: string } = {};
  try {
    body = (await req.json()) as typeof body;
  } catch {
    return new Response("bad request", { status: 400 });
  }

  const contactId = (body.contactId ?? "").trim();
  if (!contactId) {
    return new Response("bad request", { status: 400 });
  }

  const result = await runPersonalization(contactId);
  console.log(
    `[personalize-background] contact=${contactId} status=${result.status}` +
      (result.scheduled != null ? ` scheduled=${result.scheduled}` : "") +
      (result.usedFallback ? " usedFallback=true" : "")
  );
  return new Response(JSON.stringify(result), { status: 200 });
};

export default handler;
