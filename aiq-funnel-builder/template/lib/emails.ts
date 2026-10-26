import { spec, BRAND, token } from "./spec";

/**
 * E-mailové šablony a plánování.
 *
 * Obálka je pevná (kód), LLM generuje jen tělo. Patička s odhlášením se
 * neřeší tady — vkládá ji GHL sub-account automaticky. My přidáváme jen
 * identifikaci odesílatele (spec.brand.email_footer, např. „Firma · adresa").
 */

const FOOTER_TEXT = BRAND.email_footer || BRAND.name;

/* ---------- Plánování: D+day v 9:00 Europe/Prague, Unix SEKUNDY ---------- */

function tzOffsetMs(timeZone: string, date: Date): number {
  const dtf = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const parts: Record<string, string> = {};
  for (const p of dtf.formatToParts(date)) parts[p.type] = p.value;
  const asUTC = Date.UTC(
    Number(parts.year),
    Number(parts.month) - 1,
    Number(parts.day),
    Number(parts.hour) % 24,
    Number(parts.minute),
    Number(parts.second)
  );
  return asUTC - date.getTime();
}

/**
 * Unix timestamp (SEKUNDY) pro `daysFromNow` dní od dneška v 9:00
 * Europe/Prague (DST-safe).
 */
export function pragueNineAmTimestamp(daysFromNow: number): number {
  const now = new Date();
  const dayFmt = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Prague",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  const [y, m, d] = dayFmt.format(now).split("-").map(Number);
  // 9:00 pražského času vyjádřené nejdřív jako UTC "wall time"…
  const wallUtc = Date.UTC(y, m - 1, d + daysFromNow, 9, 0, 0);
  // …a pak posunuté o offset Prahy platný v ten okamžik.
  const offset = tzOffsetMs("Europe/Prague", new Date(wallUtc));
  return Math.floor((wallUtc - offset) / 1000);
}

/* ---------- Pilot mode ---------- */

/** Subject prefix pro E0 v pilot módu: [PILOT→skutečný@email] Předmět. */
export function pilotSubjectE0(subject: string, realEmail: string): string {
  if (!spec.pilot_mode?.enabled) return subject;
  return `[PILOT→${realEmail}] ${subject}`;
}

/** Subject prefix pro naplánované e-maily větve v pilot módu: [PILOT]. */
export function pilotSubjectBranch(subject: string): string {
  if (!spec.pilot_mode?.enabled) return subject;
  return `[PILOT] ${subject}`;
}

/* ---------- Obálka ---------- */

export interface WrapEmailInput {
  /** Vokativ („Petře") nebo null → „Dobrý den,". */
  vocativeName: string | null;
  /** Tělo e-mailu — jednoduché HTML odstavce (bez oslovení, bez odkazů). */
  bodyHtml: string;
  /** CTA odkaz (vkládá kód, nikdy LLM). Volitelné. */
  ctaUrl?: string;
  ctaLabel?: string;
}

/** Pevná obálka: oslovení (vokativ tabulka, ne LLM) + tělo + CTA + patička. */
export function wrapEmail({ vocativeName, bodyHtml, ctaUrl, ctaLabel }: WrapEmailInput): string {
  const greeting = vocativeName ? `Dobrý den, ${vocativeName},` : "Dobrý den,";
  // CTA barva z brand tokenů (accent) — e-mail nepodporuje CSS proměnné, hex
  // se proto vkládá napřímo z token(). Zbytek obálky drží neutrální e-mail-safe
  // barvy (E0 musí být bulletproof napříč klienty).
  const cta =
    ctaUrl && ctaLabel
      ? `<p style="margin:28px 0;">
           <a href="${ctaUrl}"
              style="display:inline-block;background:${token("accent")};color:#ffffff;
                     text-decoration:none;font-weight:700;border-radius:10px;
                     padding:14px 28px;font-family:Arial,Helvetica,sans-serif;">
             ${ctaLabel}
           </a>
         </p>`
      : "";

  return `<!doctype html>
<html lang="cs">
  <body style="margin:0;padding:0;background:#f5f5f5;">
    <div style="max-width:600px;margin:0 auto;padding:32px 24px;background:#ffffff;
                font-family:Arial,Helvetica,sans-serif;font-size:16px;line-height:1.6;
                color:#333333;">
      <p style="margin:0 0 16px;">${greeting}</p>
      ${bodyHtml}
      ${cta}
      <p style="margin:24px 0 0;">S pozdravem,<br />tým ${BRAND.name}</p>
      <hr style="border:none;border-top:1px solid #e3e6ea;margin:28px 0 16px;" />
      <p style="margin:0;font-size:13px;color:#666666;">${FOOTER_TEXT}</p>
    </div>
  </body>
</html>`;
}

/* ---------- E0: okamžité potvrzení (deterministické, žádné LLM) ---------- */

export function e0Email(vocativeName: string | null): { subject: string; html: string } {
  // Název magnetu do předmětu ZÁMĚRNĚ nevkládáme — otázkové názvy
  // („Test: Jak dobře…?") by uprostřed věty rozbily češtinu.
  const subject = "Potvrzení: vaše odpovědi jsme přijali";
  const bodyHtml = `
      <p style="margin:0 0 16px;">
        děkujeme za vyplnění dotazníku. Vaše odpovědi jsme v pořádku
        přijali.
      </p>
      <p style="margin:0 0 16px;">
        Právě pro vás připravujeme <strong>personalizovanou analýzu</strong> —
        vychází z kombinace vašich odpovědí, ne z obecných tabulek. Odkaz na
        kompletní analýzu vám přijde e-mailem.
      </p>
      <p style="margin:0 0 16px;">
        Mezitím nemusíte nic dělat. Pokud budete mít jakýkoli dotaz, stačí
        odpovědět na tento e-mail.
      </p>`;
  const html = wrapEmail({ vocativeName, bodyHtml });
  return { subject, html };
}
