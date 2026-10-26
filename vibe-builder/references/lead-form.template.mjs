// netlify/functions/lead.mjs — příjem kontaktu z landingu magnetu do GoHighLevel.
//
// Vystaví se jako POST /api/lead (viz netlify.toml níže v komentáři). Stránka
// je statická, proto NIKDY nevolá CRM přímo z prohlížeče: klíč patří sem, do
// prostředí funkce, ne do HTML.
//
//   Klíč NIKDY nepředávej argumentem příkazu (zůstal by v historii procesů).
//   Klient ho vloží do Control Centra, publisher ho propíše do prostředí webu:
//   Příkazy ber z načteného netlify-publisher skillu a volej je přes
//   python3 <publisherBaseDir>/scripts/netlify_publish.py env-set …
//   Povinné klíče: GHL_API_KEY, GHL_LOCATION_ID, LEAD_GUARD_SECRET.
//   Volitelné: MAGNET_TAG, MAGNET_SOURCE, SOUHLAS_FIELD_ID, GHL_TIMEOUT_MS — viz
//   `15-lead-magnet-pages.md` (tabulka obsahuje význam i default každé proměnné).
//
// V netlify.toml:
//   [functions]
//     directory = "netlify/functions"
//   [[redirects]]
//     from = "/api/lead"
//     to = "/.netlify/functions/lead"
//     status = 200
//
// Ověřeno naživo 7. 8. 2026 proti GHL v2.0.

import { getStore } from "@netlify/blobs";
import { createHmac, randomUUID } from "node:crypto";

const GHL = "https://services.leadconnectorhq.com";
const OKNO_S = 10 * 60;
const LIMIT_NA_IP = 10;
const IDEMPOTENCE_S = 10 * 60;
const LEASE_S = 60;
const NEURCITY_VYSLEDEK_S = 24 * 60 * 60;
const POCET_STRID = 32;
const MAX_IDENTIT_NA_STRIDU = 64;
const POKUSU_O_ZAPIS = 5;

const ochranaStore = () => getStore({ name: "lead-ochrana", consistency: "strong" });

function konfigurace() {
  const chybi = ["GHL_API_KEY", "GHL_LOCATION_ID", "LEAD_GUARD_SECRET"]
    .filter((k) => !process.env[k]);
  if (chybi.length || process.env.LEAD_GUARD_SECRET.length < 32)
    throw new Error("neúplná konfigurace lead endpointu");
}

function timeoutMs() {
  const zadano = Number.parseInt(process.env.GHL_TIMEOUT_MS ?? "8000", 10);
  return Number.isFinite(zadano) ? Math.min(15_000, Math.max(250, zadano)) : 8_000;
}

// Bez plného prohlížečového User-Agenta vrací Cloudflare 403 „Error 1010".
// Vypadá to jako špatný klíč, ale není — nezkracovat.
const USER_AGENT =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });

async function ghl(cesta, telo) {
  const odpoved = await fetch(GHL + cesta, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.GHL_API_KEY}`,
      Version: "2021-07-28",
      "Content-Type": "application/json",
      Accept: "application/json",
      "User-Agent": USER_AGENT,
    },
    body: JSON.stringify(telo),
    signal: AbortSignal.timeout(timeoutMs()),
  });
  const data = await odpoved.json().catch(() => ({}));
  if (!odpoved.ok) {
    // Do odpovědi klientovi ani do logu nejde tělo chyby — nese e-maily,
    // telefony i kusy klíče. Logujeme jen stav a cestu.
    console.error("[lead] GHL selhalo", cesta, odpoved.status);
    throw new Error(`GHL ${odpoved.status}`);
  }
  return data;
}

/** Vyhledá kontakt podle e-mailu. Vrací objekt kontaktu, nebo null.
 *  Čtení, ne zápis — proto GET a ne `upsert`. */
async function najdiKontakt(email) {
  const url = new URL(GHL + "/contacts/search/duplicate");
  url.searchParams.set("locationId", process.env.GHL_LOCATION_ID ?? "");
  url.searchParams.set("email", email);
  const odpoved = await fetch(url, {
    headers: {
      Authorization: `Bearer ${process.env.GHL_API_KEY}`,
      Version: "2021-07-28",
      Accept: "application/json",
      "User-Agent": USER_AGENT,
    },
    signal: AbortSignal.timeout(timeoutMs()),
  });
  if (odpoved.status === 404) return null;
  if (!odpoved.ok) {
    console.error("[lead] GHL hledání selhalo", odpoved.status);
    throw new Error(`GHL ${odpoved.status}`);
  }
  const data = await odpoved.json().catch(() => ({}));
  return data?.contact ?? null;
}

/* ── bounded anti-abuse + idempotence v existujících Netlify Blobs ───── */

function identita(typ, hodnota) {
  const digest = createHmac("sha256", process.env.LEAD_GUARD_SECRET)
    .update(`lead\0${typ}\0${hodnota}`).digest("hex");
  const strida = Number.parseInt(digest.slice(0, 8), 16) % POCET_STRID;
  return { digest, klic: `v1/${typ}/${strida}` };
}

async function zmenStridu(id, zmena) {
  const store = ochranaStore();
  for (let i = 0; i < POKUSU_O_ZAPIS; i++) {
    const ted = Math.floor(Date.now() / 1000);
    const nacteno = await store.getWithMetadata(id.klic, { type: "json" });
    const existuje = nacteno?.data != null;
    const polozky = { ...(existuje && nacteno.data?.polozky || {}) };
    for (const [digest, z] of Object.entries(polozky)) {
      if (!z || typeof z.do !== "number" || z.do <= ted) delete polozky[digest];
    }
    const rozhodnuti = zmena(polozky, ted);
    if (!rozhodnuti.zapsat) return rozhodnuti.vysledek;
    const podminka = existuje ? { onlyIfMatch: nacteno.etag } : { onlyIfNew: true };
    let vysledek;
    try {
      vysledek = await store.setJSON(id.klic, { verze: 1, polozky }, podminka);
    } catch { continue; }
    if (vysledek?.modified) return rozhodnuti.vysledek;
  }
  return { stav: "blok" }; // konflikt nebo výpadek guardu nesmí ochranu otevřít
}

async function povolIp(ip) {
  const id = identita("ip", ip);
  return zmenStridu(id, (polozky, ted) => {
    const z = polozky[id.digest];
    if (z?.n >= LIMIT_NA_IP) return { zapsat: false, vysledek: { stav: "blok", za: z.do - ted } };
    if (!z && Object.keys(polozky).length >= MAX_IDENTIT_NA_STRIDU)
      return { zapsat: false, vysledek: { stav: "blok", za: OKNO_S } };
    polozky[id.digest] = { n: (z?.n ?? 0) + 1, do: z?.do ?? ted + OKNO_S };
    return { zapsat: true, vysledek: { stav: "ok" } };
  });
}

async function zaberOdeslani(email) {
  const id = identita("odeslani", `${process.env.MAGNET_TAG ?? ""}\0${email}`);
  const vlastnik = randomUUID();
  const vysledek = await zmenStridu(id, (polozky, ted) => {
    const z = polozky[id.digest];
    if (z?.stav === "hotovo")
      return { zapsat: false, vysledek: { stav: "duplikat" } };
    if (z?.stav === "neurcite" || z?.stav === "odesila"
        || (z?.stav === "overuje" && (z.leaseDo ?? 0) <= ted)) {
      polozky[id.digest] = {
        stav: "overuje", vlastnik, leaseDo: ted + LEASE_S,
        do: Math.max(z.do ?? 0, ted + NEURCITY_VYSLEDEK_S),
      };
      return { zapsat: true, vysledek: { stav: "overit", id, vlastnik } };
    }
    if (z)
      return { zapsat: false, vysledek: { stav: "souběh" } };
    if (Object.keys(polozky).length >= MAX_IDENTIT_NA_STRIDU)
      return { zapsat: false, vysledek: { stav: "blok" } };
    polozky[id.digest] = { stav: "bezi", vlastnik, do: ted + LEASE_S };
    return { zapsat: true, vysledek: { stav: "ok", id, vlastnik } };
  });
  return vysledek;
}

/** PŘED prvním remote POSTem přepni krátký lease na durable ambiguous stav. */
async function zacniVzdaleneOdeslani(id, vlastnik) {
  return zmenStridu(id, (polozky, ted) => {
    const z = polozky[id.digest];
    if (!z || z.stav !== "bezi" || z.vlastnik !== vlastnik)
      return { zapsat: false, vysledek: { stav: "stary" } };
    polozky[id.digest] = {
      stav: "odesila", vlastnik, do: ted + NEURCITY_VYSLEDEK_S,
    };
    return { zapsat: true, vysledek: { stav: "ok" } };
  });
}

async function dokoncitOdeslani(id, vlastnik) {
  return zmenStridu(id, (polozky, ted) => {
    const z = polozky[id.digest];
    if (!z || z.vlastnik !== vlastnik
        || !["bezi", "odesila", "overuje"].includes(z.stav))
      return { zapsat: false, vysledek: { stav: "stary" } };
    polozky[id.digest] = { stav: "hotovo", do: ted + IDEMPOTENCE_S };
    return { zapsat: true, vysledek: { stav: "ok" } };
  });
}

async function oznacNeurcityVysledek(id, vlastnik) {
  return zmenStridu(id, (polozky, ted) => {
    const z = polozky[id.digest];
    if (!z || z.vlastnik !== vlastnik
        || !["odesila", "overuje"].includes(z.stav))
      return { zapsat: false, vysledek: { stav: "stary" } };
    polozky[id.digest] = { stav: "neurcite", do: ted + NEURCITY_VYSLEDEK_S };
    return { zapsat: true, vysledek: { stav: "ok" } };
  });
}

async function uvolnitOdeslani(id, vlastnik) {
  return zmenStridu(id, (polozky) => {
    const z = polozky[id.digest];
    if (!z || z.stav !== "bezi" || z.vlastnik !== vlastnik)
      return { zapsat: false, vysledek: { stav: "stary" } };
    delete polozky[id.digest];
    return { zapsat: true, vysledek: { stav: "ok" } };
  });
}

export default async function leadFormHandler(req) {
  if (req.method !== "POST") return json({ chyba: "Podporovaná metoda je POST." }, 405);

  // Tělo se čte jako text kvůli stropu velikosti — bez něj sem jde poslat
  // megabajty a platí to klient ve spotřebě funkcí.
  let telo;
  try {
    const surove = await req.text();
    if (surove.length > 4000) return json({ chyba: "Neplatný požadavek." }, 400);
    telo = JSON.parse(surove);
    if (!telo || typeof telo !== "object") throw new Error("nesmysl");
  } catch {
    return json({ chyba: "Neplatný požadavek." }, 400);
  }

  // Past na roboty: pole `web` je ve formuláři skryté a člověk ho nevyplní.
  // Odpovídáme 200, ať si robot nemyslí, že našel filtr — jen nic neuložíme.
  if (String(telo.web ?? "").trim() !== "") return json({ ok: true });

  const email = String(telo.email ?? "").trim().toLowerCase();
  const jmeno = String(telo.jmeno ?? "").trim().slice(0, 120);
  const telefon = String(telo.telefon ?? "").trim().slice(0, 40);

  if (email.length > 254 || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return json({ chyba: "Zadejte prosím platný e-mail." }, 400);
  }
  if (telo.souhlas !== true) {
    return json({ chyba: "Bez souhlasu se zpracováním údajů to bohužel nejde." }, 400);
  }

  const [krestni, ...zbytek] = jmeno.split(/\s+/).filter(Boolean);
  try { konfigurace(); }
  catch {
    console.error("[lead] chybí povinná konfigurace");
    return json({ chyba: "Formulář teď není dostupný. Zkuste to prosím později." }, 503);
  }

  // Hlavičku nastavuje Netlify; x-forwarded-for je podvrhnutelné. Pevně
  // shardované úložiště omezuje počet Blobů i aktivních identit.
  const ip = req.headers.get("x-nf-client-connection-ip") || "nezname";
  const limit = await povolIp(ip);
  if (limit.stav !== "ok")
    return json({ chyba: "Příliš mnoho pokusů. Zkuste to prosím později." }, 429);

  // Krátký CAS lease zavře race lookup → create. Těsně před remote POSTem se
  // přepne na durable stav: timeout/kill pak vede jen k read-only reconcile,
  // nikdy k druhému create naslepo.
  const zabrano = await zaberOdeslani(email);
  if (zabrano.stav === "duplikat") return json({ ok: true });
  if (zabrano.stav === "souběh")
    return json({ chyba: "Požadavek se právě zpracovává. Počkejte prosím." }, 409);
  if (!["ok", "overit"].includes(zabrano.stav))
    return json({ chyba: "Příliš mnoho souběžných požadavků. Zkuste to prosím později." }, 429);

  if (zabrano.stav === "overit") {
    try {
      // Předchozí POST mohl u poskytovatele uspět a jen ztratit odpověď.
      // Proto už NIKDY znovu nezakládej; pouze hledej a případně doplň tag.
      const nalezeny = await najdiKontakt(email);
      if (!nalezeny) {
        await oznacNeurcityVysledek(zabrano.id, zabrano.vlastnik);
        return json({
          chyba: "Předchozí odeslání ještě ověřujeme. Zkuste to prosím později; kontakt znovu nezakládáme.",
        }, 503);
      }
      if (process.env.MAGNET_TAG)
        await ghl(`/contacts/${encodeURIComponent(nalezeny.id)}/tags`, { tags: [process.env.MAGNET_TAG] });
      const dokonceno = await dokoncitOdeslani(zabrano.id, zabrano.vlastnik);
      if (dokonceno.stav !== "ok") throw new Error("zastaralý reconcile lease");
      return json({ ok: true });
    } catch (err) {
      await oznacNeurcityVysledek(zabrano.id, zabrano.vlastnik);
      console.error("[lead] ověření neurčitého výsledku selhalo:", err?.message ?? "neznámá chyba");
      return json({
        chyba: "Předchozí odeslání ještě ověřujeme. Zkuste to prosím později; kontakt znovu nezakládáme.",
      }, 503);
    }
  }

  let vzdalenaMutaceZajistena = false;
  try {
    // 1) NEJDŘÍV se podíváme, jestli kontakt existuje.
    //    🛑 `upsert` u existujícího kontaktu PŘEPÍŠE profil (jméno, telefon,
    //    zdroj) podle nastavení duplicit v location. Magnet nesmí přepsat
    //    data, která o zákazníkovi klient už má — proto lookup, ne upsert.
    const nalezeny = await najdiKontakt(email);

    if (nalezeny) {
      // Existující kontakt: POUZE štítek. Profil zůstává nedotčený.
      if (process.env.MAGNET_TAG) {
        const pripraveno = await zacniVzdaleneOdeslani(zabrano.id, zabrano.vlastnik);
        if (pripraveno.stav !== "ok") throw new Error("zastaralý idempotency lease");
        vzdalenaMutaceZajistena = true;
        await ghl(`/contacts/${encodeURIComponent(nalezeny.id)}/tags`, { tags: [process.env.MAGNET_TAG] });
      }
      const dokonceno = await dokoncitOdeslani(zabrano.id, zabrano.vlastnik);
      if (dokonceno.stav !== "ok") throw new Error("idempotency stav se nepodařilo dokončit");
      return json({ ok: true });
    }

    // 2) Nový kontakt — teprve tady zakládáme profil.
    const pripraveno = await zacniVzdaleneOdeslani(zabrano.id, zabrano.vlastnik);
    if (pripraveno.stav !== "ok") throw new Error("zastaralý idempotency lease");
    vzdalenaMutaceZajistena = true;
    const { contact } = await ghl("/contacts/", {
      locationId: process.env.GHL_LOCATION_ID,
      email,
      firstName: krestni ?? "",
      lastName: zbytek.join(" "),
      ...(telefon ? { phone: telefon } : {}),
      source: process.env.MAGNET_SOURCE ?? "lead magnet",
      // Doklad souhlasu. `fieldValue` je aktuální tvar, `field_value` je
      // zastaralý. Pole musí v location existovat, jinak je vynech.
      ...(process.env.SOUHLAS_FIELD_ID ? {
        customFields: [{
          id: process.env.SOUHLAS_FIELD_ID,
          fieldValue: new Date().toISOString(),
        }],
      } : {}),
    });

    // 3) Štítek až druhým voláním — `tags` v těle by přepsaly celé pole.
    if (process.env.MAGNET_TAG) {
      await ghl(`/contacts/${encodeURIComponent(contact.id)}/tags`, { tags: [process.env.MAGNET_TAG] });
    }

    const dokonceno = await dokoncitOdeslani(zabrano.id, zabrano.vlastnik);
    if (dokonceno.stav !== "ok") throw new Error("idempotency stav se nepodařilo dokončit");
    return json({ ok: true });
  } catch (err) {
    if (vzdalenaMutaceZajistena)
      await oznacNeurcityVysledek(zabrano.id, zabrano.vlastnik);
    else
      await uvolnitOdeslani(zabrano.id, zabrano.vlastnik);
    // Jen typ chyby, nikdy tělo požadavku — obsahuje osobní údaje.
    console.error("[lead] neúspěch:", err?.message ?? "neznámá chyba");
    return json({ chyba: "Kontakt se nepodařilo uložit. Zkuste to prosím znovu." }, 502);
  }
}

/* --- Strana prohlížeče (do stránky, ne sem) ---------------------------------

const formular = document.querySelector("#magnet-form");
const hlaska = document.querySelector("#magnet-chyba");

formular.addEventListener("submit", async (e) => {
  e.preventDefault();
  const tlacitko = formular.querySelector("button[type=submit]");
  const puvodni = tlacitko.textContent;

  hlaska.textContent = "";
  tlacitko.disabled = true;                 // ať se to neodešle dvakrát
  tlacitko.textContent = "Odesílám…";

  try {
    const data = Object.fromEntries(new FormData(formular));
    const odpoved = await fetch("/api/lead", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ ...data, souhlas: formular.souhlas.checked }),
    });
    const vysledek = await odpoved.json();
    if (!odpoved.ok) throw new Error(vysledek.chyba);
    window.location.href = "dekujeme/";     // až PO úspěchu, nikdy dřív
  } catch (err) {
    hlaska.textContent = err.message || "Něco se nepovedlo. Zkuste to prosím znovu.";
    tlacitko.disabled = false;
    tlacitko.textContent = puvodni;
  }
});

--------------------------------------------------------------------------- */
