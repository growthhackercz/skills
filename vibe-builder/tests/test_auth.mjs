/**
 * Testy přihlašovací šablony — snaží se brány OBEJÍT, ne potvrdit.
 *
 * Spuštění: node skills/vibe-builder/tests/test_auth.mjs
 * Bez sítě, bez Netlify — Blobs je nahrazený věrnou napodobeninou, která
 * dodržuje smlouvu onlyIfMatch/onlyIfNew a vrací { modified }.
 */
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

process.env.SESSION_SECRET = "x".repeat(40);

/* ── napodobenina Netlify Blobs ───────────────────────────────────────── */
class Store {
  constructor() { this.data = new Map(); this.seq = 0; }
  async getWithMetadata(key) {
    const z = this.data.get(key);
    return z ? { data: structuredClone(z.value), etag: z.etag } : null;
  }
  async get(key, opts) {
    const z = this.data.get(key);
    if (!z) return null;
    return opts?.type === "json" ? structuredClone(z.value) : JSON.stringify(z.value);
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
  async delete(key) { this.data.delete(key); }
}

const stores = new Map();
globalThis.__stores = stores;
globalThis.__Store = Store;

// Testuje se SKUTEČNÁ šablona — jen s podvrženým `@netlify/blobs`. Kopie
// vzniká v dočasné složce, originál se nikdy nemění.
const zde = dirname(fileURLToPath(import.meta.url));
const tmp = mkdtempSync(join(tmpdir(), "auth-test-"));
writeFileSync(join(tmp, "mock-blobs.mjs"), `
export const getStore = ({ name }) => {
  if (!globalThis.__stores.has(name)) globalThis.__stores.set(name, new globalThis.__Store());
  return globalThis.__stores.get(name);
};
`);
const zdroj = readFileSync(join(zde, "..", "references", "auth.template.mjs"), "utf8")
  .replace('from "@netlify/blobs"', 'from "./mock-blobs.mjs"');
writeFileSync(join(tmp, "lib.mjs"), zdroj);
const lib = await import(pathToFileURL(join(tmp, "lib.mjs")).href);
process.on("exit", () => rmSync(tmp, { recursive: true, force: true }));

const vysledky = [];
const zkus = async (popis, fn) => {
  try { await fn(); vysledky.push([true, popis]); }
  catch (e) { vysledky.push([false, `${popis} — ${e.message}`]); }
};

/* ── 1. brzda: souběh nesmí limit obejít ──────────────────────────────── */
await zkus("brzda: 5 souběžných pokusů se započítá všech 5", async () => {
  stores.clear();
  const vysledek = await Promise.all(
    Array.from({ length: 5 }, () => lib.brzda("email/a@b.cz"))
  );
  assert.equal(vysledek.filter((v) => !v.blok).length, 5, "mělo projít přesně 5 pokusů");
});

await zkus("brzda: šestý pokus je zablokovaný i při souběhu", async () => {
  stores.clear();
  await Promise.all(Array.from({ length: 5 }, () => lib.brzda("email/a@b.cz")));
  const sesty = await lib.brzda("email/a@b.cz");
  assert.equal(sesty.blok, true, "šestý pokus prošel — brzda nebrzdí");
});

await zkus("brzda: 20 souběžných pokusů pustí nejvýš 5", async () => {
  stores.clear();
  const vysledek = await Promise.all(
    Array.from({ length: 20 }, () => lib.brzda("ip/1.2.3.4"))
  );
  const proslo = vysledek.filter((v) => !v.blok).length;
  assert.ok(proslo <= 5, `prošlo ${proslo} pokusů, limit je 5`);
});

await zkus("brzda: vynuluj odemkne", async () => {
  stores.clear();
  await Promise.all(Array.from({ length: 5 }, () => lib.brzda("email/c@d.cz")));
  await lib.vynuluj("email/c@d.cz");
  assert.equal((await lib.brzda("email/c@d.cz")).blok, false);
});

await zkus("brzda: libovolné e-maily mají bounded shard storage", async () => {
  stores.clear();
  for (let i = 0; i < 10_000; i++) await lib.brzda(`email/utocnik-${i}@example.cz`);
  const store = stores.get("pokusy");
  assert.ok(store.data.size <= 64, `email scope vytvořil ${store.data.size} Blobů místo max. 64`);
  for (const [key, zaznam] of store.data) {
    assert.match(key, /^v1\/email\/\d+$/, `v úložišti zůstal arbitrary klíč ${key}`);
    assert.ok(Object.keys(zaznam.value.polozky).length <= 128,
      `střída ${key} přerostla pevný strop`);
  }
});

await zkus("brzda: dotčená střída uklidí prošlé identity", async () => {
  stores.clear();
  const puvodniNow = Date.now;
  let tedMs = puvodniNow();
  Date.now = () => tedMs;
  try {
    await lib.brzda("email/stary@example.cz");
    const store = stores.get("pokusy");
    const [key] = store.data.keys();
    assert.equal(Object.keys(store.data.get(key).value.polozky).length, 1);
    tedMs += 16 * 60 * 1000;
    await lib.brzda("email/stary@example.cz");
    assert.equal(Object.keys(store.data.get(key).value.polozky).length, 1,
      "prošlý záznam nebyl při dotyku nahrazen čistým oknem");
  } finally { Date.now = puvodniNow; }
});

/* ── 2. token a odvolání sezení ───────────────────────────────────────── */
await zkus("token: platný projde, podvržený ne", async () => {
  const t = lib.vytvorToken("a@b.cz", 0);
  assert.equal(lib.overToken(t).email, "a@b.cz");
  assert.equal(lib.overToken(t.slice(0, -3) + "xxx"), null, "podvržený podpis prošel");
});

await zkus("token: poškozené hodnoty vrací null, nepadají", async () => {
  for (const zly of ["", "x", "a.b", "..", "%%%.%%%", "a.b.c", null, undefined])
    assert.equal(lib.overToken(zly), null, `${zly} nevrátilo null`);
});

await zkus("token: bez pole expiruje neplatí navždy", async () => {
  const { createHmac } = await import("node:crypto");
  const telo = Buffer.from(JSON.stringify({ email: "a@b.cz" })).toString("base64url");
  const podpis = createHmac("sha256", process.env.SESSION_SECRET).update(telo).digest("base64url");
  assert.equal(lib.overToken(`${telo}.${podpis}`), null, "token bez expirace prošel");
});

await zkus("tenant: opaque prefix nemůže kolidovat přes lomítko v e-mailu", async () => {
  const prvni = lib.tenantKlic("owner@example.com");
  const kolizni = lib.tenantKlic("owner@example.com/evil");
  assert.match(prvni, /^[a-f0-9]{64}$/);
  assert.match(kolizni, /^[a-f0-9]{64}$/);
  assert.notEqual(prvni, kolizni, "dva účty dostaly stejný tenant namespace");
  assert.equal(lib.tenantKlic("OWNER@example.com"), prvni, "normalizace case není stabilní");
  assert.ok(!prvni.includes("owner"), "tenant key prozrazuje raw identitu");
});

await zkus("tenant: namespace přežije rotaci SESSION_SECRET", async () => {
  const puvodniSecret = process.env.SESSION_SECRET;
  const pred = lib.tenantKlic("owner@example.com");
  try {
    process.env.SESSION_SECRET = "y".repeat(40);
    assert.equal(lib.tenantKlic("owner@example.com"), pred,
      "rotace přihlašovacího tajemství odpojila tenantova data");
  } finally { process.env.SESSION_SECRET = puvodniSecret; }
});

await zkus("sezení: po odvolání starý token neprojde", async () => {
  stores.clear();
  await lib.uzivateleStore().setJSON("a@b.cz", { email: "a@b.cz", role: "majitel", tokenVerze: 0 });
  const stary = lib.vytvorToken("a@b.cz", 0);
  const req = { headers: { get: () => `relace=${stary}` } };
  assert.ok(await lib.prihlasenyUzivatel(req), "platný token neprošel");
  await lib.odvolejSezeni("a@b.cz");
  assert.equal(await lib.prihlasenyUzivatel(req), null, "odvolané sezení pořád platí");
});

await zkus("sezení: zakázaný účet neprojde", async () => {
  stores.clear();
  await lib.uzivateleStore().setJSON("z@b.cz", { email: "z@b.cz", role: "uzivatel", tokenVerze: 0, zakazan: true });
  const req = { headers: { get: () => `relace=${lib.vytvorToken("z@b.cz", 0)}` } };
  assert.equal(await lib.prihlasenyUzivatel(req), null, "zakázaný účet prošel");
});

/* ── 3. hesla a vstup ─────────────────────────────────────────────────── */
await zkus("heslo: ověří správné, odmítne špatné", async () => {
  const h = lib.hashHesla("velmi-dlouhe-heslo");
  assert.equal(lib.overHeslo("velmi-dlouhe-heslo", h), true);
  assert.equal(lib.overHeslo("jine-heslo", h), false);
  assert.equal(lib.overHeslo("x", "nesmysl"), false);
});

await zkus("heslo: objekt ani přerostlý vstup nikdy neshodí scrypt", async () => {
  const h = lib.hashHesla("velmi-dlouhe-heslo");
  for (const vstup of [{}, [], null, 42, "x".repeat(201)])
    assert.doesNotThrow(() => assert.equal(lib.overHeslo(vstup, h), false));
});

await zkus("cookie: login i logout mají povinné bezpečnostní atributy", async () => {
  const login = lib.cookieHlavicka("abc");
  for (const atribut of ["HttpOnly", "Secure", "SameSite=Strict", "Path=/", "Max-Age=28800"])
    assert.ok(login.includes(atribut), `login cookie postrádá ${atribut}`);
  const logout = lib.cookieHlavicka(null);
  for (const atribut of ["HttpOnly", "Secure", "SameSite=Strict", "Path=/", "Max-Age=0"])
    assert.ok(logout.includes(atribut), `logout cookie postrádá ${atribut}`);
});

await zkus("tělo: poškozené vrací null, přerostlé taky", async () => {
  const req = (t) => ({ text: async () => t });
  assert.equal(await lib.ctiTelo(req("{neplatny")), null);
  assert.equal(await lib.ctiTelo(req('"retezec"')), null);
  assert.equal(await lib.ctiTelo(req("x".repeat(20000))), null);
  assert.deepEqual(await lib.ctiTelo(req('{"a":1}')), { a: 1 });
});

await zkus("role: výčet obsahuje majitele i správce", async () => {
  for (const r of ["majitel", "spravce", "uzivatel"])
    assert.ok(lib.ROLE.includes(r), `role ${r} chybí ve výčtu`);
});

/* ── 4. INTEGRAČNÍ trasa: login → data → revoke → nový login ──────────
   Unit testy helperů tenhle scénář minuly. Simuluje se přesně to, co dělá
   `16-aplikace.md`: přihlášení podepíše aktuální tokenVerze, chráněná trasa
   používá přísný helper, změna hesla verzi zvýší. */
const prihlas = async (email) => {
  const u = await lib.uzivateleStore().get(email, { type: "json" });
  if (!u || u.zakazan || !u.hash) return null;
  return lib.vytvorToken(u.email, u.tokenVerze ?? 0);   // AKTUÁLNÍ verze
};
const req = (t) => ({ headers: { get: () => `relace=${t}` } });

await zkus("trasa: po revokaci projde NOVÉ přihlášení", async () => {
  stores.clear();
  await lib.uzivateleStore().setJSON("a@b.cz", {
    email: "a@b.cz", role: "majitel", tokenVerze: 0, hash: lib.hashHesla("dlouhe-heslo-1"),
  });
  const t1 = await prihlas("a@b.cz");
  assert.ok(await lib.prihlasenyUzivatel(req(t1)), "první přihlášení neprošlo");

  await lib.odvolejSezeni("a@b.cz");
  assert.equal(await lib.prihlasenyUzivatel(req(t1)), null, "starý token po revokaci platí");

  const t2 = await prihlas("a@b.cz");
  assert.ok(await lib.prihlasenyUzivatel(req(t2)), "po revokaci nejde se znovu přihlásit");
});

await zkus("trasa: změna hesla odhlásí staré sezení", async () => {
  stores.clear();
  const store = lib.uzivateleStore();
  await store.setJSON("c@d.cz", {
    email: "c@d.cz", role: "uzivatel", tokenVerze: 0, hash: lib.hashHesla("stare-heslo-xx"),
  });
  const stary = await prihlas("c@d.cz");
  assert.ok(await lib.prihlasenyUzivatel(req(stary)));

  const u = await store.get("c@d.cz", { type: "json" });
  await store.setJSON("c@d.cz", {
    ...u, hash: lib.hashHesla("nove-heslo-xxx"), tokenVerze: (u.tokenVerze ?? 0) + 1,
  });
  assert.equal(await lib.prihlasenyUzivatel(req(stary)), null,
    "po změně hesla zůstal útočník přihlášený");
});

await zkus("trasa: zákaz účtu odřízne i platné sezení", async () => {
  stores.clear();
  const store = lib.uzivateleStore();
  await store.setJSON("e@f.cz", {
    email: "e@f.cz", role: "uzivatel", tokenVerze: 0, hash: lib.hashHesla("heslo-dlouhe-1"),
  });
  const t = await prihlas("e@f.cz");
  assert.ok(await lib.prihlasenyUzivatel(req(t)));
  const u = await store.get("e@f.cz", { type: "json" });
  await store.setJSON("e@f.cz", { ...u, zakazan: true });
  assert.equal(await lib.prihlasenyUzivatel(req(t)), null, "zakázaný účet má pořád přístup");
  assert.equal(await prihlas("e@f.cz"), null, "zakázaný účet se znovu přihlásil");
});

await zkus("trasa: změna role se projeví bez odhlášení", async () => {
  stores.clear();
  const store = lib.uzivateleStore();
  await store.setJSON("g@h.cz", {
    email: "g@h.cz", role: "uzivatel", tokenVerze: 0, hash: lib.hashHesla("heslo-dlouhe-2"),
  });
  const t = await prihlas("g@h.cz");
  assert.equal((await lib.prihlasenyUzivatel(req(t))).role, "uzivatel");
  const u = await store.get("g@h.cz", { type: "json" });
  await store.setJSON("g@h.cz", { ...u, role: "majitel" });
  assert.equal((await lib.prihlasenyUzivatel(req(t))).role, "majitel",
    "role se čte z tokenu, ne z účtu");
});

/* ── výpis ────────────────────────────────────────────────────────────── */
for (const [stav, popis] of vysledky) console.log(`${stav ? "PASS" : "FAIL"}  ${popis}`);
const selhalo = vysledky.filter(([s]) => !s).length;
console.log(`\n${vysledky.length - selhalo}/${vysledky.length} prošlo`);
process.exit(selhalo ? 1 : 0);
