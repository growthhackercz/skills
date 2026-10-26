/**
 * Behaviorální test skutečné lead šablony. Bez sítě a credentialů: fetch i
 * Netlify Blobs jsou lokální napodobeniny, produkční rozhodovací logika zůstává.
 */
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

process.env.GHL_API_KEY = "testovaci-nepouzitelny-klic";
process.env.GHL_LOCATION_ID = "test-location";
process.env.LEAD_GUARD_SECRET = "g".repeat(40);
process.env.MAGNET_TAG = "magnet-test";
process.env.MAGNET_SOURCE = "offline test";
process.env.SOUHLAS_FIELD_ID = "souhlas-field";
process.env.GHL_TIMEOUT_MS = "30";

class Store {
  constructor() { this.data = new Map(); this.seq = 0; }
  async getWithMetadata(key) {
    const z = this.data.get(key);
    return z ? { data: structuredClone(z.value), etag: z.etag } : null;
  }
  async setJSON(key, value, opts = {}) {
    const z = this.data.get(key);
    if (opts.onlyIfNew && z) return { modified: false };
    if (opts.onlyIfMatch !== undefined && (!z || z.etag !== opts.onlyIfMatch))
      return { modified: false };
    const etag = `e${++this.seq}`;
    this.data.set(key, { value: structuredClone(value), etag });
    return { modified: true, etag };
  }
}

const stores = new Map();
globalThis.__leadStores = stores;
globalThis.__LeadStore = Store;

const zde = dirname(fileURLToPath(import.meta.url));
const tmp = mkdtempSync(join(tmpdir(), "lead-test-"));
process.on("exit", () => rmSync(tmp, { recursive: true, force: true }));
writeFileSync(join(tmp, "mock-blobs.mjs"), `
export const getStore = ({ name }) => {
  if (!globalThis.__leadStores.has(name))
    globalThis.__leadStores.set(name, new globalThis.__LeadStore());
  return globalThis.__leadStores.get(name);
};
`);
const zdroj = readFileSync(join(zde, "..", "references", "lead-form.template.mjs"), "utf8")
  .replace('from "@netlify/blobs"', 'from "./mock-blobs.mjs"');
writeFileSync(join(tmp, "lead.mjs"), zdroj);
const { default: lead } = await import(pathToFileURL(join(tmp, "lead.mjs")).href);

const vysledky = [];
const zkus = async (popis, fn) => {
  try { await fn(); vysledky.push([true, popis]); }
  catch (e) { vysledky.push([false, `${popis} — ${e.message}`]); }
};

const req = (email, ip = "192.0.2.10", navic = {}) => ({
  method: "POST",
  headers: { get: (k) => k.toLowerCase() === "x-nf-client-connection-ip" ? ip : null },
  text: async () => JSON.stringify({
    email, jmeno: "Testovací Člověk", telefon: "+420 123 456 789",
    souhlas: true, web: "", ...navic,
  }),
});

const jsonResponse = (data, status = 200) => new Response(JSON.stringify(data), {
  status, headers: { "content-type": "application/json" },
});

await zkus("existující kontakt se pouze vyhledá a taguje — profil se nepřepisuje", async () => {
  stores.clear();
  const volani = [];
  globalThis.fetch = async (url, opts = {}) => {
    volani.push({ url: String(url), opts });
    if (String(url).includes("/contacts/search/duplicate"))
      return jsonResponse({ contact: { id: "kontakt/existuje" } });
    if (String(url).includes("/tags")) return jsonResponse({ ok: true });
    throw new Error(`neočekávané volání ${url}`);
  };
  const odpoved = await lead(req("existuje@example.cz"));
  assert.equal(odpoved.status, 200);
  assert.equal(volani.length, 2);
  assert.equal(volani.some((v) => v.opts.method === "POST" && /\/contacts\/$/.test(v.url)), false,
    "existující kontakt prošel create/upsert cestou");
  assert.match(volani[1].url, /kontakt%2Fexistuje\/tags$/);
  assert.deepEqual(JSON.parse(volani[1].opts.body), { tags: ["magnet-test"] });
});

await zkus("MAGNET_TAG je skutečně volitelný — bez něj se kontakt jen ověří", async () => {
  stores.clear();
  const puvodniTag = process.env.MAGNET_TAG;
  delete process.env.MAGNET_TAG;
  const volani = [];
  try {
    globalThis.fetch = async (url, opts = {}) => {
      volani.push({ url: String(url), opts });
      if (String(url).includes("/contacts/search/duplicate"))
        return jsonResponse({ contact: { id: "bez-tagu" } });
      throw new Error(`neočekávané volání ${url}`);
    };
    const odpoved = await lead(req("bez-tagu@example.cz", "192.0.2.11"));
    assert.equal(odpoved.status, 200);
    assert.equal(volani.length, 1, "volitelný tag vyvolal remote zápis");
  } finally { process.env.MAGNET_TAG = puvodniTag; }
});

await zkus("nový kontakt se založí jednou a tag se přidá samostatným voláním", async () => {
  stores.clear();
  const volani = [];
  globalThis.fetch = async (url, opts = {}) => {
    volani.push({ url: String(url), opts });
    if (String(url).includes("/contacts/search/duplicate")) return jsonResponse({}, 404);
    if (/\/contacts\/$/.test(String(url))) return jsonResponse({ contact: { id: "novy-1" } });
    if (String(url).endsWith("/contacts/novy-1/tags")) return jsonResponse({ ok: true });
    throw new Error(`neočekávané volání ${url}`);
  };
  const odpoved = await lead(req("novy@example.cz"));
  assert.equal(odpoved.status, 200);
  const create = volani.find((v) => v.opts.method === "POST" && /\/contacts\/$/.test(v.url));
  const telo = JSON.parse(create.opts.body);
  assert.equal(telo.email, "novy@example.cz");
  assert.equal(telo.source, "offline test");
  assert.equal("tags" in telo, false, "tags v create těle by mohly přepsat existující tagy");
  assert.equal(volani.filter((v) => v.url.endsWith("/tags")).length, 1);
});

await zkus("ztracená create odpověď se usmíří lookupem bez druhého kontaktu", async () => {
  stores.clear();
  let vytvoreno = 0;
  let kontaktJeVidet = false;
  globalThis.fetch = async (url) => {
    if (String(url).includes("/contacts/search/duplicate"))
      return kontaktJeVidet
        ? jsonResponse({ contact: { id: "commit-bez-odpovedi" } })
        : jsonResponse({}, 404);
    if (/\/contacts\/$/.test(String(url))) {
      vytvoreno += 1;
      kontaktJeVidet = true; // provider commitnul, transport ale odpověď ztratil
      throw new Error("connection reset after commit");
    }
    if (String(url).endsWith("/contacts/commit-bez-odpovedi/tags"))
      return jsonResponse({ ok: true });
    throw new Error(`neočekávané volání ${url}`);
  };
  const prvni = await lead(req("ambiguous@example.cz", "203.0.113.30"));
  assert.equal(prvni.status, 502);
  const druhy = await lead(req("ambiguous@example.cz", "203.0.113.30"));
  assert.equal(druhy.status, 200, "reconcile nenašel už commitnutý kontakt");
  assert.equal(vytvoreno, 1, "retry po ztracené odpovědi založil druhý kontakt");
});

await zkus("neurčitý create bez viditelného kontaktu failne zavřeně", async () => {
  stores.clear();
  let vytvoreno = 0;
  globalThis.fetch = async (url) => {
    if (String(url).includes("/contacts/search/duplicate")) return jsonResponse({}, 404);
    if (/\/contacts\/$/.test(String(url))) {
      vytvoreno += 1;
      throw new Error("connection reset with unknown provider outcome");
    }
    throw new Error(`neočekávané volání ${url}`);
  };
  const prvni = await lead(req("still-ambiguous@example.cz", "203.0.113.31"));
  assert.equal(prvni.status, 502);
  const druhy = await lead(req("still-ambiguous@example.cz", "203.0.113.31"));
  const treti = await lead(req("still-ambiguous@example.cz", "203.0.113.31"));
  assert.equal(druhy.status, 503);
  assert.equal(treti.status, 503);
  assert.equal(vytvoreno, 1, "reconcile bez důkazu opakoval create");
});

await zkus("souběžný dvojklik vytvoří nejvýš jeden kontakt", async () => {
  stores.clear();
  let vytvoreno = 0;
  globalThis.fetch = async (url) => {
    if (String(url).includes("/contacts/search/duplicate")) return jsonResponse({}, 404);
    if (/\/contacts\/$/.test(String(url))) {
      vytvoreno += 1;
      return jsonResponse({ contact: { id: "race-1" } });
    }
    return jsonResponse({ ok: true });
  };
  const odpovedi = await Promise.all([
    lead(req("race@example.cz")),
    lead(req("race@example.cz")),
  ]);
  assert.deepEqual(odpovedi.map((r) => r.status).sort((a, b) => a - b), [200, 409]);
  assert.equal(vytvoreno, 1, "lookup/create race založil duplicitní kontakt");
});

await zkus("jeden trusted IP má pevný limit a guard nevytváří arbitrary Blob keys", async () => {
  stores.clear();
  globalThis.fetch = async (url) => {
    if (String(url).includes("/contacts/search/duplicate"))
      return jsonResponse({ contact: { id: "existujici" } });
    return jsonResponse({ ok: true });
  };
  const stavy = [];
  for (let i = 0; i < 11; i++)
    stavy.push((await lead(req(`rate-${i}@example.cz`, "198.51.100.7"))).status);
  assert.deepEqual(stavy, [200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 429]);
  const guard = stores.get("lead-ochrana");
  assert.ok(guard.data.size <= 64, `guard vytvořil ${guard.data.size} Blobů`);
  for (const key of guard.data.keys()) assert.match(key, /^v1\/(ip|odeslani)\/\d+$/);
});

await zkus("read-only GHL lookup má bounded timeout a lze ho zopakovat", async () => {
  stores.clear();
  let pokusy = 0;
  globalThis.fetch = async (_url, opts = {}) => {
    pokusy += 1;
    return new Promise((_resolve, reject) => {
      const zrus = () => reject(opts.signal.reason ?? new Error("timeout"));
      if (opts.signal.aborted) zrus();
      else opts.signal.addEventListener("abort", zrus, { once: true });
    });
  };
  // AbortSignal.timeout používá unref timer; držák simuluje otevřený socket
  // reálného fetch a nedovolí Node ukončit test před abortem.
  const drzak = setTimeout(() => {}, 600);
  try {
    const zacatek = Date.now();
    const prvni = await lead(req("timeout@example.cz", "203.0.113.8"));
    assert.equal(prvni.status, 502);
    assert.ok(Date.now() - zacatek < 500, "timeout nebyl rozumně omezený");
    const druhy = await lead(req("timeout@example.cz", "203.0.113.8"));
    assert.equal(druhy.status, 502, "selhání nechalo idempotency lease zamčený");
    assert.equal(pokusy, 2);
  } finally { clearTimeout(drzak); }
});

for (const [stav, popis] of vysledky) console.log(`${stav ? "PASS" : "FAIL"}  ${popis}`);
const selhalo = vysledky.filter(([s]) => !s).length;
console.log(`\n${vysledky.length - selhalo}/${vysledky.length} prošlo`);
process.exit(selhalo ? 1 : 0);
