/**
 * Zlatá trasa nad SKUTEČNÝMI endpointy z dokumentace.
 *
 * 🛑 Proč tenhle soubor existuje: `test_auth.mjs` testuje šablonu a hlásil
 * 16/16, zatímco endpointy v `16-aplikace.md` měly rozbitý import a vůbec by
 * nenaběhly. Test, který si produkční logiku přepíše uvnitř sebe, nedokazuje
 * nic o tom, co agent klientovi reálně postaví.
 *
 * Tenhle test proto kód NEOPISUJE: vytáhne bloky z `references/16-aplikace.md`,
 * složí z nich funkce a zavolá je jako Netlify runtime.
 *
 * Spuštění: node skills/vibe-builder/tests/test_endpointy.mjs
 */
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

process.env.SESSION_SECRET = "x".repeat(40);
process.env.SETUP_TOKEN = "setup-token-pro-test";

const zde = dirname(fileURLToPath(import.meta.url));
const refs = join(zde, "..", "references");
const tmp = mkdtempSync(join(tmpdir(), "endpointy-"));
process.on("exit", () => rmSync(tmp, { recursive: true, force: true }));

/* ── napodobenina Netlify Blobs (smlouva onlyIfNew/onlyIfMatch) ────────── */
class Store {
  constructor(name) {
    this.name = name; this.data = new Map(); this.seq = 0; this.listCalls = 0;
    this.uspesneZapisy = new Map();
  }
  async getWithMetadata(k) {
    const z = this.data.get(k);
    return z ? { data: structuredClone(z.value), etag: z.etag } : null;
  }
  async get(k, o) {
    const z = this.data.get(k);
    if (!z) return null;
    return o?.type === "json" ? structuredClone(z.value) : JSON.stringify(z.value);
  }
  async setJSON(k, v, o = {}) {
    const z = this.data.get(k);
    if (o.onlyIfNew && z) return { modified: false };
    if (o.onlyIfMatch !== undefined && (!z || z.etag !== o.onlyIfMatch)) return { modified: false };
    this.data.set(k, { value: structuredClone(v), etag: `e${++this.seq}` });
    this.uspesneZapisy.set(k, (this.uspesneZapisy.get(k) ?? 0) + 1);
    return { modified: true, etag: `e${this.seq}` };
  }
  async delete(k) { this.data.delete(k); }
  async list(opts = {}) {
    this.listCalls += 1;
    const prefix = opts.prefix ?? "";
    return { blobs: [...this.data.keys()].filter((key) => key.startsWith(prefix)).map((key) => ({ key })) };
  }
}
const stores = new Map();
globalThis.__stores = stores;
globalThis.__Store = Store;

writeFileSync(join(tmp, "mock-blobs.mjs"), `
export const getStore = ({ name }) => {
  if (!globalThis.__stores.has(name)) globalThis.__stores.set(name, new globalThis.__Store(name));
  return globalThis.__stores.get(name);
};
`);

globalThis.__scryptCalls = 0;
writeFileSync(join(tmp, "mock-crypto.mjs"), `
import { createHash, createHmac, randomBytes, timingSafeEqual, scryptSync as realScryptSync } from "node:crypto";
export { createHash, createHmac, randomBytes, timingSafeEqual };
export const scryptSync = (...args) => {
  globalThis.__scryptCalls += 1;
  return realScryptSync(...args);
};
`);

writeFileSync(join(tmp, "mock-db.mjs"), `
// Behaviorální napodobenina: bez tenant WHERE vrátí oba tenanty a test padne.
export const getDatabase = () => ({
  sql: async (retezce, ...hodnoty) => {
    const text = retezce.join("?");
    globalThis.__dbCalls.push({ text, hodnoty });
    if (/SELECT\\s+\\*/i.test(text)) {
      if (!/WHERE\\s+vlastnik\\s*=\\s*\\?/i.test(text))
        return structuredClone(globalThis.__dbRows);
      return structuredClone(globalThis.__dbRows.filter((r) => r.vlastnik === hodnoty[0]));
    }
    return [];
  },
  driver: "mock", pool: null, connectionString: "postgres://mock",
});
export const getConnectionString = () => "postgres://mock";
`);
globalThis.__dbRows = [];
globalThis.__dbCalls = [];

// Sdílená vrstva = skutečná šablona, jen s podvrženým úložištěm.
writeFileSync(join(tmp, "_lib.mjs"),
  readFileSync(join(refs, "auth.template.mjs"), "utf8")
    .replace('from "@netlify/blobs"', 'from "./mock-blobs.mjs"')
    .replace('from "node:crypto"', 'from "./mock-crypto.mjs"'));

/* ── vytažení endpointů Z DOKUMENTACE ─────────────────────────────────── */
const doc = readFileSync(join(refs, "16-aplikace.md"), "utf8");

/** Najde ```js blok, který obsahuje danou značku (např. cestu endpointu). */
function blokPodle(znacky) {
  const seznam = Array.isArray(znacky) ? znacky : [znacky];
  const bloky = [...doc.matchAll(/```js\n([\s\S]*?)```/g)].map((m) => m[1]);
  const nalezene = bloky.filter((b) => seznam.every((z) => b.includes(z)));
  if (nalezene.length === 0)
    throw new Error(`v 16-aplikace.md chybí blok se značkami ${seznam.join(" + ")}`);
  // Víc shod = test by mohl omylem prověřovat jiný endpoint, než si myslí.
  if (nalezene.length > 1)
    throw new Error(`značky ${seznam.join(" + ")} sedí na ${nalezene.length} bloků — zpřesni je`);
  return nalezene[0];
}

function nactiEndpoint(znacka, jmeno) {
  const kod = blokPodle(znacka)
    .replace(/from "@netlify\/blobs"/g, 'from "./mock-blobs.mjs"')
    .replace(/from "@netlify\/database"/g, 'from "./mock-db.mjs"');
  const cesta = join(tmp, `${jmeno}.mjs`);
  writeFileSync(cesta, kod);
  return import(pathToFileURL(cesta).href);
}

const vysledky = [];
const zkus = async (popis, fn) => {
  try { await fn(); vysledky.push([true, popis]); }
  catch (e) { vysledky.push([false, `${popis} — ${e.message}`]); }
};

const req = (metoda, telo, cookie = "", hlavicky = {}) => ({
  method: metoda,
  headers: { get: (k) => ({ cookie, ...hlavicky })[k.toLowerCase()] ?? null },
  text: async () => JSON.stringify(telo ?? {}),
  json: async () => structuredClone(telo ?? {}),
});
const cookieZ = (odpoved) => {
  const h = odpoved.headers.get("set-cookie") || "";
  return h.split(";")[0];
};

/* ── 1. endpointy se vůbec musí dát načíst ────────────────────────────── */
let prihlaseni, setup, nastavitHeslo, chranenyBlobs;

await zkus("endpointy z dokumentace jdou načíst a spustit", async () => {
  prihlaseni = await nactiEndpoint('path: "/api/prihlaseni"', "prihlaseni");
  setup = await nactiEndpoint('path: "/api/setup"', "setup");
  nastavitHeslo = await nactiEndpoint('path: "/api/nastavit-heslo"', "nastavit-heslo");
  for (const [jmeno, mod] of [["prihlaseni", prihlaseni], ["setup", setup], ["nastavit-heslo", nastavitHeslo]])
    assert.equal(typeof mod.default, "function", `${jmeno} nemá výchozí handler`);
});

let chranenyDb;
await zkus("chráněné datové endpointy jdou načíst A ZAVOLAT", async () => {
  chranenyBlobs = await nactiEndpoint(
    ['from "@netlify/blobs"', "prihlasenyUzivatel(req)"], "chraneny-blobs");
  chranenyDb = await nactiEndpoint(
    ['from "@netlify/database"', "prihlasenyUzivatel(req)"], "chraneny-db");
  for (const [jmeno, mod] of [["Blobs", chranenyBlobs], ["DB", chranenyDb]]) {
    assert.equal(typeof mod.default, "function", `${jmeno} nemá handler`);
    // Samotný import projde i při špatném jménu ve `import {...}` — chyba
    // spadne až při VOLÁNÍ. Proto se každý handler musí opravdu zavolat.
    const odpoved = await mod.default(req("GET", null, ""));
    assert.equal(odpoved.status, 401,
      `${jmeno} endpoint nevrátil 401 pro nepřihlášeného (běží vůbec?)`);
  }
});

/* ── 2. celá trasa přes SKUTEČNÉ handlery ─────────────────────────────── */
await zkus("trasa: setup → nastavení hesla → přihlášení → chráněná data", async () => {
  stores.clear();
  const s = await setup.default(req("POST", { email: "a@b.cz", role: "majitel" },
    "", { "x-setup-token": process.env.SETUP_TOKEN }));
  assert.equal(s.status, 200, "setup neprošel");
  const odkaz = (await s.json()).odkaz;
  const token = odkaz.split("token=")[1];

  const ucetPred = stores.get("uzivatele").data.get("a@b.cz").value;
  assert.equal(Object.values(ucetPred).includes(token), false,
    "bearer reset token je uložený v účtu místo digestu");
  assert.match(ucetPred.resetKlic, /^[a-f0-9]{64}$/);

  const n = await nastavitHeslo.default(req("POST", { token, heslo: "dlouhe-heslo-123" }));
  assert.equal(n.status, 200, "nastavení hesla neprošlo");

  const p = await prihlaseni.default(req("POST", { email: "a@b.cz", heslo: "dlouhe-heslo-123" }));
  assert.equal(p.status, 200, "přihlášení neprošlo");
  const cookie = cookieZ(p);
  assert.ok(cookie.startsWith("relace="), "chybí cookie relace");

  const d = await chranenyBlobs.default(req("GET", null, cookie));
  assert.notEqual(d.status, 401, "chráněná data odmítla přihlášeného uživatele");
});

await zkus("identita: setup i login kanonizují e-mail a nevytvoří case-duplicitní účet", async () => {
  stores.clear();
  const s = await setup.default(req("POST", {
    email: "  Owner@Example.COM  ", role: "majitel",
  }, "", { "x-setup-token": process.env.SETUP_TOKEN }));
  assert.equal(s.status, 200, "setup smí přijmout běžnou case/whitespace variantu");
  const telo = await s.json();
  assert.equal(telo.email, "owner@example.com");
  assert.deepEqual([...stores.get("uzivatele").data.keys()], ["owner@example.com"],
    "účet není uložený pod jedinou kanonickou identitou");

  const duplikat = await setup.default(req("POST", { email: "owner@example.com" }, "",
    { "x-setup-token": process.env.SETUP_TOKEN }));
  assert.equal(duplikat.status, 409, "case varianta založila druhý účet");

  const token = telo.odkaz.split("token=")[1];
  assert.equal((await nastavitHeslo.default(req("POST", {
    token, heslo: "kanonicke-heslo-123",
  }))).status, 200);
  const login = await prihlaseni.default(req("POST", {
    email: "OWNER@example.com", heslo: "kanonicke-heslo-123",
  }, "", { "x-nf-client-connection-ip": "192.0.2.22" }));
  assert.equal(login.status, 200, "login nevyhledal kanonickou identitu");
  assert.equal((await login.json()).email, "owner@example.com");
});

await zkus("login: objekt hesla vrací stejnou 401 pro existující i cizí účet", async () => {
  stores.clear();
  const lib = await import(pathToFileURL(join(tmp, "_lib.mjs")).href);
  await lib.uzivateleStore().setJSON("objekt@b.cz", {
    email: "objekt@b.cz", role: "uzivatel", tokenVerze: 0,
    hash: lib.hashHesla("platne-heslo-123"),
  });
  const existuje = await prihlaseni.default(req("POST", { email: "objekt@b.cz", heslo: {} }));
  const chybi = await prihlaseni.default(req("POST", { email: "chybi@b.cz", heslo: {} }));
  assert.equal(existuje.status, 401);
  assert.equal(chybi.status, 401);
  assert.deepEqual(await existuje.json(), await chybi.json(),
    "objekt hesla enumeruje existenci účtu odlišnou odpovědí");
});

await zkus("login: existující i chybějící účet udělají jednu scrypt práci", async () => {
  stores.clear();
  const lib = await import(pathToFileURL(join(tmp, "_lib.mjs")).href);
  await lib.uzivateleStore().setJSON("cas@b.cz", {
    email: "cas@b.cz", role: "uzivatel", tokenVerze: 0,
    hash: lib.hashHesla("platne-heslo-123"),
  });
  globalThis.__scryptCalls = 0;
  const existuje = await prihlaseni.default(req("POST", {
    email: "cas@b.cz", heslo: "spatne-heslo-123",
  }, "", { "x-nf-client-connection-ip": "192.0.2.20" }));
  const poExistujicim = globalThis.__scryptCalls;
  const chybi = await prihlaseni.default(req("POST", {
    email: "nikdo@b.cz", heslo: "spatne-heslo-123",
  }, "", { "x-nf-client-connection-ip": "192.0.2.21" }));
  assert.equal(existuje.status, 401);
  assert.equal(chybi.status, 401);
  assert.equal(poExistujicim, 1, "existující účet neudělal právě jeden scrypt");
  assert.equal(globalThis.__scryptCalls, 2,
    "chybějící účet přeskočil dummy scrypt a jde odhadnout podle času");
});

await zkus("reset: dva souběžné requesty spotřebují token právě jednou bez scanování účtů", async () => {
  stores.clear();
  const s = await setup.default(req("POST", { email: "race@b.cz" },
    "", { "x-setup-token": process.env.SETUP_TOKEN }));
  const token = (await s.json()).odkaz.split("token=")[1];
  const tokenStore = stores.get("reset-tokeny");
  const [tokenKlic] = tokenStore.data.keys();
  const odpovedi = await Promise.all([
    nastavitHeslo.default(req("POST", { token, heslo: "souběžné-heslo-123" }, "",
      { "x-nf-client-connection-ip": "192.0.2.10" })),
    nastavitHeslo.default(req("POST", { token, heslo: "souběžné-heslo-456" }, "",
      { "x-nf-client-connection-ip": "192.0.2.11" })),
  ]);
  assert.deepEqual(odpovedi.map((r) => r.status).sort((a, b) => a - b), [200, 400],
    "stejný bearer token uspěl více než jednou");
  assert.equal(tokenStore.uspesneZapisy.get(tokenKlic), 2,
    "tokenový záznam byl úspěšně přivlastněn více než jedním requestem");
  assert.equal(stores.get("uzivatele").listCalls, 0, "reset skenoval seznam účtů");
  assert.equal(stores.get("reset-tokeny").listCalls, 0, "reset skenoval tokenový index");
});

await zkus("trasa: bez přihlášení chráněná data vrací 401", async () => {
  const d = await chranenyBlobs.default(req("GET", null, ""));
  assert.equal(d.status, 401, "chráněná data pustila nepřihlášeného");
});

await zkus("trasa: zakázaný účet se nepřihlásí", async () => {
  stores.clear();
  const lib = await import(pathToFileURL(join(tmp, "_lib.mjs")).href);
  await lib.uzivateleStore().setJSON("z@b.cz", {
    email: "z@b.cz", role: "uzivatel", tokenVerze: 0,
    hash: lib.hashHesla("dlouhe-heslo-123"), zakazan: true,
  });
  const p = await prihlaseni.default(req("POST", { email: "z@b.cz", heslo: "dlouhe-heslo-123" }));
  assert.equal(p.status, 401, "zakázaný účet se přihlásil");
});

await zkus("cookie: endpoint vydá i smaže cookie se všemi atributy", async () => {
  stores.clear();
  const lib = await import(pathToFileURL(join(tmp, "_lib.mjs")).href);
  await lib.uzivateleStore().setJSON("cookie@b.cz", {
    email: "cookie@b.cz", role: "uzivatel", tokenVerze: 0,
    hash: lib.hashHesla("cookie-heslo-123"),
  });
  const login = await prihlaseni.default(req("POST", {
    email: "cookie@b.cz", heslo: "cookie-heslo-123",
  }, "", { "x-nf-client-connection-ip": "192.0.2.1" }));
  const loginCookie = login.headers.get("set-cookie");
  for (const atribut of ["HttpOnly", "Secure", "SameSite=Strict", "Path=/", "Max-Age=28800"])
    assert.ok(loginCookie.includes(atribut), `login cookie postrádá ${atribut}`);
  const logout = await prihlaseni.default(req("DELETE", null));
  const logoutCookie = logout.headers.get("set-cookie");
  for (const atribut of ["HttpOnly", "Secure", "SameSite=Strict", "Path=/", "Max-Age=0"])
    assert.ok(logoutCookie.includes(atribut), `logout cookie postrádá ${atribut}`);
});

await zkus("Blobs: prefix i vlastník ze session izolují dva tenanty", async () => {
  stores.clear();
  const lib = await import(pathToFileURL(join(tmp, "_lib.mjs")).href);
  const users = lib.uzivateleStore();
  for (const email of ["prvni@b.cz", "druhy@b.cz", "prvni@b.cz/evil"])
    await users.setJSON(email, { email, role: "uzivatel", tokenVerze: 0 });
  const zaznamy = new Store("zaznamy");
  stores.set("zaznamy", zaznamy);
  await zaznamy.setJSON(`v1/${lib.tenantKlic("prvni@b.cz")}/a`,
    { id: "a", vlastnik: "prvni@b.cz" });
  await zaznamy.setJSON(`v1/${lib.tenantKlic("druhy@b.cz")}/b`,
    { id: "b", vlastnik: "druhy@b.cz" });
  await zaznamy.setJSON(`v1/${lib.tenantKlic("prvni@b.cz/evil")}/c`,
    { id: "c", vlastnik: "prvni@b.cz/evil" });
  const cookie = `relace=${lib.vytvorToken("prvni@b.cz", 0)}`;
  const get = await chranenyBlobs.default(req("GET", null, cookie));
  const telo = await get.json();
  assert.deepEqual(telo.zaznamy.map((z) => z.vlastnik), ["prvni@b.cz"],
    "chybějící nebo raw-email prefix propustil cizí Blob");

  const post = await chranenyBlobs.default(req("POST", {
    nazev: "útok", castka: 1, vlastnik: "druhy@b.cz",
  }, cookie));
  assert.equal((await post.json()).zaznam.vlastnik, "prvni@b.cz",
    "vlastník z requestu přepsal vlastníka ze session");
});

await zkus("DB: tenant WHERE je behaviorálně nutný pro izolaci řádků", async () => {
  stores.clear();
  globalThis.__dbCalls.length = 0;
  globalThis.__dbRows = [
    { id: 1, vlastnik: "prvni@b.cz", nazev: "A" },
    { id: 2, vlastnik: "druhy@b.cz", nazev: "B" },
  ];
  const lib = await import(pathToFileURL(join(tmp, "_lib.mjs")).href);
  await lib.uzivateleStore().setJSON("prvni@b.cz", {
    email: "prvni@b.cz", role: "uzivatel", tokenVerze: 0,
  });
  const cookie = `relace=${lib.vytvorToken("prvni@b.cz", 0)}`;
  const odpoved = await chranenyDb.default(req("GET", null, cookie));
  const telo = await odpoved.json();
  assert.deepEqual(telo.zakazky.map((z) => z.vlastnik), ["prvni@b.cz"],
    "mutace SQL bez tenant WHERE vrátila cizí řádek");
  const select = globalThis.__dbCalls.find((c) => /SELECT/i.test(c.text));
  assert.match(select.text, /WHERE\s+vlastnik\s*=\s*\?/i);
  assert.equal(select.hodnoty[0], "prvni@b.cz");
});

await zkus("trasa: změna hesla odhlásí staré sezení, nové přihlášení projde", async () => {
  stores.clear();
  const s = await setup.default(req("POST", { email: "c@d.cz" },
    "", { "x-setup-token": process.env.SETUP_TOKEN }));
  const token1 = (await s.json()).odkaz.split("token=")[1];
  await nastavitHeslo.default(req("POST", { token: token1, heslo: "prvni-heslo-123" }));

  const p1 = await prihlaseni.default(req("POST", { email: "c@d.cz", heslo: "prvni-heslo-123" }));
  const staraCookie = cookieZ(p1);
  assert.notEqual((await chranenyBlobs.default(req("GET", null, staraCookie))).status, 401);

  // nový odkaz a změna hesla
  const s2 = await setup.default(req("POST", { email: "c@d.cz", obnovit: true },
    "", { "x-setup-token": process.env.SETUP_TOKEN }));
  const token2 = (await s2.json()).odkaz.split("token=")[1];
  await nastavitHeslo.default(req("POST", { token: token2, heslo: "druhe-heslo-123" }));

  assert.equal((await chranenyBlobs.default(req("GET", null, staraCookie))).status, 401,
    "po změně hesla zůstalo staré sezení platné");

  const p2 = await prihlaseni.default(req("POST", { email: "c@d.cz", heslo: "druhe-heslo-123" }));
  assert.equal(p2.status, 200, "po změně hesla se nejde znovu přihlásit");
  assert.notEqual((await chranenyBlobs.default(req("GET", null, cookieZ(p2)))).status, 401);
});

await zkus("trasa: brzda po 5 pokusech vrací 429 i se správným heslem", async () => {
  stores.clear();
  const s = await setup.default(req("POST", { email: "e@f.cz" },
    "", { "x-setup-token": process.env.SETUP_TOKEN }));
  const t = (await s.json()).odkaz.split("token=")[1];
  await nastavitHeslo.default(req("POST", { token: t, heslo: "spravne-heslo-1" }));

  for (let i = 0; i < 5; i++)
    await prihlaseni.default(req("POST", { email: "e@f.cz", heslo: "spatne-heslo" }));
  const p = await prihlaseni.default(req("POST", { email: "e@f.cz", heslo: "spravne-heslo-1" }));
  assert.equal(p.status, 429, "brzda pustila i po pěti pokusech");
});

await zkus("trasa: setup bez tokenu je 403, poškozené tělo 400", async () => {
  const bez = await setup.default(req("POST", { email: "x@y.cz" }));
  assert.equal(bez.status, 403, "setup prošel bez tokenu");
  const zle = await prihlaseni.default({
    method: "POST",
    headers: { get: () => null },
    text: async () => "{tohle-neni-json",
  });
  assert.equal(zle.status, 400, "poškozené tělo nevrátilo 400");
});

for (const [stav, popis] of vysledky) console.log(`${stav ? "PASS" : "FAIL"}  ${popis}`);
const selhalo = vysledky.filter(([s]) => !s).length;
console.log(`\n${vysledky.length - selhalo}/${vysledky.length} prošlo`);
process.exit(selhalo ? 1 : 0);
