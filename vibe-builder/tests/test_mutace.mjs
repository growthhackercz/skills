/**
 * Mutation sensitivity: každá cílená bezpečnostní regrese se vloží do čisté
 * dočasné kopie a příslušný behaviorální test ji musí skutečně odmítnout.
 */
import assert from "node:assert/strict";
import { cpSync, mkdtempSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const zde = dirname(fileURLToPath(import.meta.url));
const skill = join(zde, "..");
const tmp = mkdtempSync(join(tmpdir(), "vibe-mutace-"));
process.on("exit", () => rmSync(tmp, { recursive: true, force: true }));

function zamen(cesta, puvodni, mutace) {
  const text = readFileSync(cesta, "utf8");
  const prvni = text.indexOf(puvodni);
  assert.notEqual(prvni, -1, `nenalezen cíl mutace v ${cesta}`);
  assert.equal(text.indexOf(puvodni, prvni + puvodni.length), -1,
    `cíl mutace není jednoznačný v ${cesta}`);
  writeFileSync(cesta, text.replace(puvodni, mutace));
}

const pripady = [
  {
    jmeno: "object-password",
    test: "test_endpointy.mjs",
    marker: "login: objekt hesla",
    mutuj(root) {
      zamen(join(root, "references", "auth.template.mjs"),
        '  if (!jeHeslo(heslo)) return false;\n  const [alg, salt, key]',
        '  const [alg, salt, key]');
      zamen(join(root, "references", "auth.template.mjs"),
        '  } catch { return false; }\n}\n\n/* ── sezení',
        '  } catch (e) { throw e; }\n}\n\n/* ── sezení');
      zamen(join(root, "references", "16-aplikace.md"),
        '  if (!email || !jeHeslo(heslo))\n    return json({ chyba: "nesprávný e-mail nebo heslo" }, 401);',
        '  if (!email) return json({ chyba: "nesprávný e-mail nebo heslo" }, 401);');
    },
  },
  {
    jmeno: "missing-account-fast-path",
    test: "test_endpointy.mjs",
    marker: "login: existující i chybějící účet udělají jednu scrypt práci",
    mutuj(root) {
      zamen(join(root, "references", "16-aplikace.md"),
        '  const hesloPlati = overHeslo(heslo, zaznam?.hash);\n  if (!zaznam || zaznam.zakazan || !hesloPlati)',
        '  const hesloPlati = zaznam && !zaznam.zakazan && overHeslo(heslo, zaznam.hash);\n  if (!hesloPlati)');
    },
  },
  {
    jmeno: "non-atomic-reset",
    test: "test_endpointy.mjs",
    marker: "reset: dva souběžné requesty",
    mutuj(root) {
      zamen(join(root, "references", "auth.template.mjs"),
        '  const vysledek = await store.setJSON(klic, { ...z, pouzit: ted }, { onlyIfMatch: nacteno.etag });',
        '  const vysledek = await store.setJSON(klic, { ...z, pouzit: ted });');
    },
  },
  {
    jmeno: "unbounded-rate-keys",
    test: "test_auth.mjs",
    marker: "brzda: libovolné e-maily mají bounded shard storage",
    mutuj(root) {
      zamen(join(root, "references", "auth.template.mjs"),
        '  return { digest, uloznyKlic: `v1/${typ}/${strida}` };',
        '  return { digest, uloznyKlic: klic };');
    },
  },
  {
    jmeno: "cookie-without-httponly",
    test: "test_auth.mjs",
    marker: "cookie: login i logout",
    mutuj(root) {
      zamen(join(root, "references", "auth.template.mjs"),
        '  const z = `${COOKIE}=${token}; HttpOnly; Secure; SameSite=Strict; Path=/`;',
        '  const z = `${COOKIE}=${token}; Secure; SameSite=Strict; Path=/`;');
    },
  },
  {
    jmeno: "blobs-without-prefix",
    test: "test_endpointy.mjs",
    marker: "Blobs: prefix i vlastník",
    mutuj(root) {
      zamen(join(root, "references", "16-aplikace.md"),
        '  const { blobs } = await store.list({ prefix: `v1/${tenant}/` }); // pravidlo 3',
        '  const { blobs } = await store.list();   // chybějící tenant prefix');
    },
  },
  {
    jmeno: "db-without-tenant-where",
    test: "test_endpointy.mjs",
    marker: "DB: tenant WHERE",
    mutuj(root) {
      zamen(join(root, "references", "16-aplikace.md"),
        '  const radky = await sql`SELECT * FROM zakazky WHERE vlastnik = ${u.email} ORDER BY id`;',
        '  const radky = await sql`SELECT * FROM zakazky ORDER BY id`;');
    },
  },
  {
    jmeno: "setup-without-canonical-email",
    test: "test_endpointy.mjs",
    marker: "identita: setup i login kanonizují e-mail",
    mutuj(root) {
      zamen(join(root, "references", "16-aplikace.md"),
        '  const { email: zadanyEmail, role = "uzivatel", obnovit = false } = telo;\n  const email = normalizujEmail(zadanyEmail);',
        '  const { email, role = "uzivatel", obnovit = false } = telo;');
    },
  },
  {
    jmeno: "tenant-key-coupled-to-session-secret",
    test: "test_auth.mjs",
    marker: "tenant: namespace přežije rotaci SESSION_SECRET",
    mutuj(root) {
      zamen(join(root, "references", "auth.template.mjs"),
        '  return createHash("sha256").update(`tenant\\0${canonicalEmail}`).digest("hex");',
        '  return createHmac("sha256", tajemstvi()).update(`tenant\\0${canonicalEmail}`).digest("hex");');
    },
  },
  {
    jmeno: "optional-magnet-tag-made-required",
    test: "test_lead.mjs",
    marker: "MAGNET_TAG je skutečně volitelný",
    mutuj(root) {
      zamen(join(root, "references", "lead-form.template.mjs"),
        '  const chybi = ["GHL_API_KEY", "GHL_LOCATION_ID", "LEAD_GUARD_SECRET"]',
        '  const chybi = ["GHL_API_KEY", "GHL_LOCATION_ID", "LEAD_GUARD_SECRET", "MAGNET_TAG"]');
    },
  },
  {
    jmeno: "ambiguous-create-released",
    test: "test_lead.mjs",
    marker: "ztracená create odpověď se usmíří lookupem bez druhého kontaktu",
    mutuj(root) {
      zamen(join(root, "references", "lead-form.template.mjs"),
        '    polozky[id.digest] = {\n      stav: "odesila", vlastnik, do: ted + NEURCITY_VYSLEDEK_S,\n    };',
        '    polozky[id.digest] = { stav: "bezi", vlastnik, do: ted - 1 };');
    },
  },
];

for (const pripad of pripady) {
  const kopie = join(tmp, pripad.jmeno);
  cpSync(skill, kopie, { recursive: true });
  pripad.mutuj(kopie);
  const beh = spawnSync(process.execPath, [join(kopie, "tests", pripad.test)], {
    encoding: "utf8", timeout: 30_000,
  });
  const vystup = `${beh.stdout}\n${beh.stderr}`;
  assert.notEqual(beh.status, 0, `mutace ${pripad.jmeno} prošla testy`);
  assert.ok(vystup.includes(`FAIL  ${pripad.marker}`),
    `mutaci ${pripad.jmeno} odmítla jiná chyba než cílený behaviorální test:\n${vystup}`);
  console.log(`PASS  mutace ${pripad.jmeno} byla behaviorálně odhalena`);
}

console.log(`\n${pripady.length}/${pripady.length} mutací odhaleno`);
