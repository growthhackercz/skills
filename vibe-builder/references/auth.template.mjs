/**
 * Sdílená přihlašovací vrstva — `netlify/functions/_lib.mjs`
 *
 * 🛑 Tenhle soubor se KOPÍRUJE, nepřepisuje se po paměti. Je otestovaný
 * (`tests/test_auth.mjs`) a každá „drobná úprava" ty testy nejdřív musí projít.
 *
 * Použití: zkopíruj jako `netlify/functions/_lib.mjs` a nastav prostředí
 * SESSION_SECRET (min. 32 znaků) a SETUP_TOKEN.
 */
import { getStore } from "@netlify/blobs";
import { scryptSync, randomBytes, timingSafeEqual, createHash, createHmac } from "node:crypto";

const COOKIE = "relace";
const PLATNOST_S = 60 * 60 * 8;
const OKNO_S = 15 * 60;
const LIMIT = 5;
const POKUSU_O_ZAPIS = 5;
const POCET_STRID = 64;
const MAX_IDENTIT_NA_STRIDU = 128;
const TYPY_BRZDY = new Set(["email", "ip", "heslo"]);
const DUMMY_SCRYPT_SALT = "00000000000000000000000000000000";
const DUMMY_SCRYPT_KEY = "00".repeat(64);

/** Role jsou výčet, ne libovolný řetězec z těla požadavku. */
export const ROLE = ["majitel", "spravce", "uzivatel"];

export const uzivateleStore = () => getStore({ name: "uzivatele", consistency: "strong" });
const pokusyStore = () => getStore({ name: "pokusy", consistency: "strong" });
export const resetTokenyStore = () => getStore({ name: "reset-tokeny", consistency: "strong" });

function tajemstvi() {
  const s = process.env.SESSION_SECRET;
  if (!s || s.length < 32) throw new Error("SESSION_SECRET chybí nebo je krátký");
  return s;
}

/* ── hesla ────────────────────────────────────────────────────────────── */

export function hashHesla(heslo) {
  if (!jeHeslo(heslo)) throw new TypeError("heslo musí mít 10–200 znaků");
  const salt = randomBytes(16).toString("hex");
  return `scrypt$${salt}$${scryptSync(heslo, salt, 64).toString("hex")}`;
}

export function overHeslo(heslo, ulozene) {
  // Nepropouštěj objekty ani přerostlé řetězce do scryptSync. Endpoint pak
  // vrátí stejnou 401 jako pro neexistující účet, místo enumerovatelné 500.
  if (!jeHeslo(heslo)) return false;
  const [alg, salt, key] = String(ulozene || "").split("$");
  const formatPlati = alg === "scrypt"
    && /^[a-f0-9]{32}$/i.test(salt || "")
    && /^[a-f0-9]{128}$/i.test(key || "");
  // I neexistující, zakázaný nebo poškozený účet udělá pro platně tvarované
  // heslo stejnou drahou scrypt práci. Jinak jde existenci účtu měřit časem.
  const scryptSalt = formatPlati ? salt : DUMMY_SCRYPT_SALT;
  const scryptKey = formatPlati ? key : DUMMY_SCRYPT_KEY;
  try {
    const a = Buffer.from(scryptKey, "hex");
    const b = scryptSync(heslo, scryptSalt, 64);
    return formatPlati && a.length === b.length && timingSafeEqual(a, b);   // nikdy ===
  } catch { return false; }
}

/* ── sezení ───────────────────────────────────────────────────────────── */

/**
 * Token nese `verze`. Když se u účtu zvýší `tokenVerze`, všechna dosud vydaná
 * sezení okamžitě přestanou platit — to je jediná cesta, jak po změně hesla
 * nebo odebrání práv skutečně odhlásit už přihlášeného útočníka.
 */
export function vytvorToken(email, verze = 0) {
  const canonicalEmail = normalizujEmail(email);
  if (!canonicalEmail) throw new TypeError("neplatný e-mail účtu");
  const expiruje = Math.floor(Date.now() / 1000) + PLATNOST_S;
  const telo = Buffer.from(JSON.stringify({ email: canonicalEmail, expiruje, verze })).toString("base64url");
  const podpis = createHmac("sha256", tajemstvi()).update(telo).digest("base64url");
  return `${telo}.${podpis}`;
}

export function overToken(token) {
  if (!token || !token.includes(".")) return null;
  const [telo, podpis] = token.split(".");
  if (!telo || !podpis) return null;
  let ocekavany;
  try {
    ocekavany = createHmac("sha256", tajemstvi()).update(telo).digest("base64url");
  } catch { return null; }
  const a = Buffer.from(podpis), b = Buffer.from(ocekavany);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return null;
  let data;
  try { data = JSON.parse(Buffer.from(telo, "base64url").toString()); } catch { return null; }
  // Chybějící `expiruje` by prošlo navždy (`undefined < cokoli` je false).
  if (!data || typeof data.expiruje !== "number") return null;
  return data.expiruje < Math.floor(Date.now() / 1000) ? null : data;
}

/** Ověří podpis I platnost verze proti účtu. Používej tam, kde jde o data. */
export async function prihlasenyUzivatel(req) {
  const data = prihlaseny(req);
  if (!data) return null;
  const email = normalizujEmail(data.email);
  if (!email) return null;
  const ucet = await uzivateleStore().get(email, { type: "json" });
  if (!ucet || ucet.zakazan) return null;
  if ((ucet.tokenVerze ?? 0) !== (data.verze ?? 0)) return null;   // sezení odvoláno
  return { ...data, email, role: ucet.role };
}

export function cookieHlavicka(token) {
  const z = `${COOKIE}=${token}; HttpOnly; Secure; SameSite=Strict; Path=/`;
  return token
    ? `${z}; Max-Age=${PLATNOST_S}`
    : `${COOKIE}=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0`;
}

export function prihlaseny(req) {
  const par = (req.headers.get("cookie") || "").split(";")
    .map((c) => c.trim()).find((c) => c.startsWith(`${COOKIE}=`));
  return par ? overToken(par.slice(COOKIE.length + 1)) : null;
}

/**
 * Stabilní, slash-safe namespace pro tenantova Blob data. Raw e-mail není
 * bezpečný prefix: účet `a@b.cz/evil` by jinak spadal i pod prefix `a@b.cz/`.
 * SHA-256 zde není ochrana tajemství, jen bezpečné deterministické ID. Záměrně
 * se NEODVOZUJE ze SESSION_SECRET: jeho rotace nesmí odpojit uložená data.
 */
export function tenantKlic(email) {
  const canonicalEmail = normalizujEmail(email);
  if (!canonicalEmail) return null;
  return createHash("sha256").update(`tenant\0${canonicalEmail}`).digest("hex");
}

/** Odvolá všechna sezení účtu — po změně hesla, zákazu účtu i změně role. */
export async function odvolejSezeni(email) {
  email = normalizujEmail(email);
  if (!email) return false;
  const store = uzivateleStore();
  const u = await store.get(email, { type: "json" });
  if (!u) return false;
  await store.setJSON(email, { ...u, tokenVerze: (u.tokenVerze ?? 0) + 1 });
  return true;
}

/* ── jednorázové tokeny ───────────────────────────────────────────────── */

/** V úložišti je jen HMAC digest; samotný bearer token existuje jen ve výstupu setupu. */
export function digestResetTokenu(token) {
  if (typeof token !== "string" || token.length < 24 || token.length > 128) return null;
  return createHmac("sha256", tajemstvi()).update(`reset\0${token}`).digest("hex");
}

/**
 * Atomicky označí reset token jako použitý. Jen jeden souběžný požadavek získá
 * `stav: "ok"`; konflikt CAS, opakované použití i neplatný token skončí null.
 */
export async function spotrebujResetToken(token) {
  const digest = digestResetTokenu(token);
  if (!digest) return null;
  const store = resetTokenyStore();
  const klic = `v1/${digest}`;
  const nacteno = await store.getWithMetadata(klic, { type: "json" });
  const z = nacteno?.data;
  if (!z || z.pouzit || typeof z.email !== "string" || typeof z.tokenDo !== "number") return null;

  const ted = Math.floor(Date.now() / 1000);
  const vysledek = await store.setJSON(klic, { ...z, pouzit: ted }, { onlyIfMatch: nacteno.etag });
  if (!vysledek?.modified) return null;
  return z.tokenDo < ted
    ? { stav: "vyprsel", klic }
    : { stav: "ok", klic, email: z.email, resetVerze: z.resetVerze };
}

/* ── brzda ────────────────────────────────────────────────────────────── */

/**
 * Libovolné identity nikdy nepoužívej jako názvy Blobů. HMAC je rozděluje do
 * pevného počtu stříd; každá střída má pevný strop a při každém dotyku smaže
 * prošlé položky. Úložiště tak má nejvýš 3 × 64 Blobů a 3 × 64 × 128 aktivních
 * identit. Plná střída selže zavřeně, aby vytlačování nešlo použít k obejití.
 */
function identitaBrzdy(klic) {
  if (typeof klic !== "string" || klic.length > 320) return null;
  const lomitko = klic.indexOf("/");
  const typ = klic.slice(0, lomitko);
  const hodnota = klic.slice(lomitko + 1);
  if (lomitko < 1 || !TYPY_BRZDY.has(typ) || !hodnota) return null;
  const digest = createHmac("sha256", tajemstvi()).update(`brzda\0${typ}\0${hodnota}`).digest("hex");
  const strida = Number.parseInt(digest.slice(0, 8), 16) % POCET_STRID;
  return { digest, uloznyKlic: `v1/${typ}/${strida}` };
}

/**
 * 🛑 Zápis MUSÍ být podmíněný a jeho výsledek se MUSÍ číst.
 *
 * `setJSON` při konfliktu **nevyhazuje výjimku** — vrací `{ modified: false }`.
 * Kdo výsledek ignoruje (nebo spoléhá na try/catch), má brzdu, která nebrzdí:
 * pět souběžných pokusů přečte stejné `n` a limit se překročí.
 */
export async function brzda(klic) {
  const identita = identitaBrzdy(klic);
  if (!identita) return { blok: true, za: OKNO_S };
  const store = pokusyStore();
  const ted = Math.floor(Date.now() / 1000);

  for (let i = 0; i < POKUSU_O_ZAPIS; i++) {
    const nacteno = await store.getWithMetadata(identita.uloznyKlic, { type: "json" });
    const existuje = nacteno?.data != null;
    const polozky = { ...(existuje && nacteno.data?.polozky || {}) };
    for (const [digest, z] of Object.entries(polozky)) {
      if (!z || typeof z.do !== "number" || z.do <= ted) delete polozky[digest];
    }
    const stary = polozky[identita.digest];
    if (stary?.n >= LIMIT) return { blok: true, za: Math.max(1, stary.do - ted) };
    if (!stary && Object.keys(polozky).length >= MAX_IDENTIT_NA_STRIDU)
      return { blok: true, za: OKNO_S };
    polozky[identita.digest] = { n: (stary?.n ?? 0) + 1, do: stary?.do ?? ted + OKNO_S };
    const z = { verze: 1, polozky };

    // Nový záznam potřebuje onlyIfNew; existující onlyIfMatch na etag.
    const podminka = existuje ? { onlyIfMatch: nacteno.etag } : { onlyIfNew: true };
    let vysledek;
    try {
      vysledek = await store.setJSON(identita.uloznyKlic, z, podminka);
    } catch {
      continue;   // síťová chyba → další kolo
    }
    if (vysledek?.modified) return { blok: false };
    // modified:false = někdo nás předběhl → přečti znovu
  }
  // Nepodařilo se bezpečně započítat pokus → blokuj. Brzda, která se při
  // chybě otevře, nechrání nic.
  return { blok: true, za: OKNO_S };
}

export async function vynuluj(klic) {
  const identita = identitaBrzdy(klic);
  if (!identita) return false;
  const store = pokusyStore();
  for (let i = 0; i < POKUSU_O_ZAPIS; i++) {
    const nacteno = await store.getWithMetadata(identita.uloznyKlic, { type: "json" });
    if (!nacteno?.data) return true;
    const polozky = { ...(nacteno.data.polozky || {}) };
    const ted = Math.floor(Date.now() / 1000);
    for (const [digest, z] of Object.entries(polozky)) {
      if (!z || typeof z.do !== "number" || z.do <= ted) delete polozky[digest];
    }
    delete polozky[identita.digest];
    let vysledek;
    try {
      vysledek = await store.setJSON(
        identita.uloznyKlic, { verze: 1, polozky }, { onlyIfMatch: nacteno.etag });
    } catch { continue; }
    if (vysledek?.modified) return true;
  }
  return false;
}

/* ── vstup ────────────────────────────────────────────────────────────── */

/** Poškozené tělo je chyba volajícího (400), ne pád funkce (500). */
export async function ctiTelo(req, maxZnaku = 10_000) {
  let text;
  try { text = await req.text(); } catch { return null; }
  if (text.length > maxZnaku) return null;
  try { const d = JSON.parse(text); return d && typeof d === "object" ? d : null; }
  catch { return null; }
}

export const jeEmail = (v) =>
  typeof v === "string" && v.length <= 254 && /^[^@\s]+@[^@\s.]+\.[^@\s]+$/.test(v);

/** Jediná identita účtu: trim + lowercase před lookupem, tokenem i zápisem. */
export function normalizujEmail(v) {
  if (typeof v !== "string") return null;
  const email = v.trim().toLowerCase();
  return jeEmail(email) ? email : null;
}

export const jeHeslo = (v) => typeof v === "string" && v.length >= 10 && v.length <= 200;

export const json = (data, status = 200, hlavicky = {}) =>
  new Response(JSON.stringify(data), {
    status, headers: { "content-type": "application/json; charset=utf-8", ...hlavicky },
  });
