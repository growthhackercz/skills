import { spec } from "./spec";

/**
 * GHL v2 LeadConnector API client.
 *
 * Uses the global Node/undici `fetch` (NEVER python — Cloudflare blocks
 * python-urllib with error 1010). Credentials come from env so they are never
 * baked into the bundle.
 */
const GHL_BASE = "https://services.leadconnectorhq.com";
const GHL_VERSION = "2021-07-28";

function apiKey(): string {
  const key = process.env.GHL_API_KEY;
  if (!key) throw new Error("GHL_API_KEY is not set");
  return key;
}

export function locationId(): string {
  // Prefer env (synced on Netlify from CC); fall back to spec for local dev.
  return process.env.GHL_LOCATION_ID || spec.ghl_location_id;
}

function headers(): Record<string, string> {
  return {
    Authorization: `Bearer ${apiKey()}`,
    Version: GHL_VERSION,
    Accept: "application/json",
    "Content-Type": "application/json",
  };
}

export interface CustomField {
  id: string;
  value: string;
}

export interface UpsertContactInput {
  email: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
  customFields: CustomField[];
}

/**
 * POST /contacts/upsert — writes a contact and its custom fields.
 * Custom fields are ALWAYS addressed by `id`, never by name/slug/fieldKey.
 * Returns the contact id.
 */
export async function upsertContact(input: UpsertContactInput): Promise<string> {
  const body: Record<string, unknown> = {
    locationId: locationId(),
    email: input.email,
    customFields: input.customFields,
  };
  if (input.firstName) body.firstName = input.firstName;
  if (input.lastName) body.lastName = input.lastName;
  if (input.phone) body.phone = input.phone;

  const res = await fetch(`${GHL_BASE}/contacts/upsert`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`GHL upsert failed (${res.status}): ${text}`);
  }

  const json = (await res.json()) as { contact?: { id?: string } };
  const id = json?.contact?.id;
  if (!id) throw new Error("GHL upsert returned no contact id");
  return id;
}

export interface GhlContact {
  id: string;
  firstName?: string;
  lastName?: string;
  email?: string;
  tags?: string[];
  customFields?: CustomField[];
}

/**
 * GET /contacts/{id} — reads a contact.
 * `json.contact.customFields` is an array of { id, value }.
 */
export async function getContact(contactId: string): Promise<GhlContact | null> {
  const res = await fetch(`${GHL_BASE}/contacts/${encodeURIComponent(contactId)}`, {
    method: "GET",
    headers: headers(),
    cache: "no-store",
  });

  if (res.status === 404) return null;
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`GHL getContact failed (${res.status}): ${text}`);
  }

  const json = (await res.json()) as { contact?: GhlContact };
  return json?.contact ?? null;
}

/** Helper: pick a custom field value by its id. */
export function fieldValue(
  fields: CustomField[] | undefined,
  id: string
): string {
  if (!fields) return "";
  const found = fields.find((f) => f.id === id);
  return found?.value ?? "";
}

/**
 * POST /contacts/search — kontakty s daným tagem, stránkováno. Vrací tags
 * i customFields v payloadu, takže guard nepotřebuje per-kontakt GET (u
 * `converted` si ho ale kvůli eventually-consistent indexu radši ověří čerstvě).
 */
export async function searchContactsByTag(
  tag: string,
  maxPages = 100
): Promise<GhlContact[]> {
  const PAGE = 100;
  const all: GhlContact[] = [];
  for (let page = 1; page <= maxPages; page++) {
    const res = await fetch(`${GHL_BASE}/contacts/search`, {
      method: "POST",
      headers: headers(),
      cache: "no-store",
      body: JSON.stringify({
        locationId: locationId(),
        page,
        pageLimit: PAGE,
        filters: [{ field: "tags", operator: "contains", value: tag }],
      }),
    });
    if (!res.ok) {
      if (page === 1) throw new Error(`GHL search failed (${res.status})`);
      break;
    }
    const json = (await res.json()) as { contacts?: GhlContact[] };
    const contacts = Array.isArray(json.contacts) ? json.contacts : [];
    all.push(...contacts);
    if (contacts.length < PAGE) break;
  }
  return all;
}

/**
 * PUT /contacts/{id} — updates custom fields on an existing contact.
 * Custom fields are ALWAYS addressed by `id`.
 */
export async function updateContactFields(
  contactId: string,
  customFields: CustomField[]
): Promise<void> {
  if (customFields.length === 0) return;
  const res = await fetch(`${GHL_BASE}/contacts/${encodeURIComponent(contactId)}`, {
    method: "PUT",
    headers: headers(),
    body: JSON.stringify({ customFields }),
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`GHL updateContactFields failed (${res.status}): ${text}`);
  }
}

/** POST /contacts/{id}/tags — adds tags to a contact. */
export async function addTags(contactId: string, tags: string[]): Promise<void> {
  if (tags.length === 0) return;
  const res = await fetch(
    `${GHL_BASE}/contacts/${encodeURIComponent(contactId)}/tags`,
    {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ tags }),
      cache: "no-store",
    }
  );
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`GHL addTags failed (${res.status}): ${text}`);
  }
}

/** DELETE /contacts/{id}/tags — removes tags from a contact. */
export async function removeTags(contactId: string, tags: string[]): Promise<void> {
  if (tags.length === 0) return;
  const res = await fetch(
    `${GHL_BASE}/contacts/${encodeURIComponent(contactId)}/tags`,
    {
      method: "DELETE",
      headers: headers(),
      body: JSON.stringify({ tags }),
      cache: "no-store",
    }
  );
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`GHL removeTags failed (${res.status}): ${text}`);
  }
}

export interface SendEmailInput {
  contactId: string;
  subject: string;
  html: string;
  /** Unix timestamp in SECONDS (ms → GHL returns 422!). Omit = send now. */
  scheduledTimestamp?: number;
}

export interface SendEmailResult {
  emailMessageId: string;
  conversationId: string;
}

/**
 * POST /conversations/messages — sends (or schedules) an e-mail to a contact.
 * Immediate: no scheduledTimestamp. Scheduled: scheduledTimestamp in SECONDS.
 */
export async function sendEmail(input: SendEmailInput): Promise<SendEmailResult> {
  const body: Record<string, unknown> = {
    type: "Email",
    contactId: input.contactId,
    subject: input.subject,
    html: input.html,
  };
  if (input.scheduledTimestamp) {
    body.scheduledTimestamp = input.scheduledTimestamp;
  }

  const res = await fetch(`${GHL_BASE}/conversations/messages`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`GHL sendEmail failed (${res.status}): ${text}`);
  }

  const json = (await res.json()) as {
    emailMessageId?: string;
    messageId?: string;
    conversationId?: string;
  };
  return {
    emailMessageId: json.emailMessageId ?? json.messageId ?? "",
    conversationId: json.conversationId ?? "",
  };
}

/**
 * DELETE /conversations/messages/email/{emailMessageId}/schedule
 * Cancels a scheduled e-mail. A missing schedule is already in the desired
 * state and therefore counts as success.
 */
export async function cancelScheduledEmail(emailMessageId: string): Promise<boolean> {
  const res = await fetch(
    `${GHL_BASE}/conversations/messages/email/${encodeURIComponent(
      emailMessageId
    )}/schedule`,
    {
      method: "DELETE",
      headers: headers(),
      cache: "no-store",
    }
  );
  if (res.ok || res.status === 404) return true;
  console.error(
    `[ghl] zrušení naplánovaného e-mailu selhalo (${res.status})`
  );
  return false;
}
