#!/usr/bin/env node

import {
  existsSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { validateFunnelSpec } from "./validate-spec.mjs";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const EXPECTED_CREDENTIAL_SCOPE = "aiq-funnel-builder";

function value(name) {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

function fail(message) {
  console.error(`[aiq-deploy] STOP: ${message}`);
  process.exit(2);
}

function netlifyImportFailure(result) {
  if (result.error) return "Netlify CLI se nepodařilo spustit";
  const output = `${result.stderr ?? ""}\n${result.stdout ?? ""}`.toLowerCase();
  if (/\b401\b|unauthori[sz]ed|invalid[^\n]*(token|auth)/.test(output)) {
    return "Netlify autorizace byla odmítnuta; znovu ověřte připojení v Control Center";
  }
  if (/\b403\b|forbidden|permission|not authorized/.test(output)) {
    return "Netlify token nemá oprávnění měnit proměnné propojené site";
  }
  if (/\b404\b|not found|site[^\n]*missing/.test(output)) {
    return "propojená Netlify site není pro uložený účet dostupná";
  }
  return "Netlify odmítlo synchronizaci proměnných";
}

if (!existsSync("funnel-spec.json")) {
  fail("spusť skript z kořene připravené funnel appky s funnel-spec.json");
}

let spec;
try {
  spec = JSON.parse(readFileSync("funnel-spec.json", "utf8"));
} catch {
  fail("funnel-spec.json není validní JSON");
}

const validationErrors = validateFunnelSpec(spec);
if (validationErrors.length > 0) {
  fail(`funnel-spec.json neprošel validací:\n- ${validationErrors.join("\n- ")}`);
}

if (value("confirm-publish") !== "yes") {
  fail("produkční nasazení vyžaduje --confirm-publish yes po výslovném souhlasu uživatele");
}
if (value("confirm-metered") !== "yes") {
  fail("OpenRouter provoz vyžaduje --confirm-metered yes po výslovném souhlasu uživatele");
}

const legacyTags = value("legacy-tags");
const allowedLegacyStates = new Set(["new", "clear", "migrated"]);
if (!legacyTags || !allowedLegacyStates.has(legacyTags)) {
  fail("--legacy-tags musí být new, clear nebo migrated podle provedeného preflightu");
}

for (const relativePath of [
  "scripts/ensure-fields.mjs",
  "scripts/field-plan.mjs",
]) {
  const appPath = join(process.cwd(), relativePath);
  const canonicalPath = join(SCRIPT_DIR, "..", "template", relativePath);
  if (
    !existsSync(appPath) ||
    readFileSync(appPath, "utf8") !== readFileSync(canonicalPath, "utf8")
  ) {
    fail(
      `${relativePath} není bezpečná verze z aktuálního skillu; před deployem synchronizujte runtime soubory šablony`
    );
  }
}
const netlifyConfig = existsSync("netlify.toml")
  ? readFileSync("netlify.toml", "utf8")
  : "";
let netlifySection = "";
const buildCommands = [];
for (const rawLine of netlifyConfig.split(/\r?\n/)) {
  const line = rawLine.trim();
  if (!line || line.startsWith("#")) continue;
  const section = line.match(/^\[([^\]]+)\]$/)?.[1];
  if (section) {
    netlifySection = section;
    continue;
  }
  if (netlifySection === "build") {
    const command = line.match(/^command\s*=\s*"([^"]*)"$/)?.[1];
    if (command !== undefined) buildCommands.push(command);
  }
}
if (
  buildCommands.length !== 1 ||
  buildCommands[0] !== "node scripts/ensure-fields.mjs --verify && npm ci && next build"
) {
  fail("netlify.toml nemá read-only custom-field verify build gate");
}

if (process.env.CC_GHL_CREDENTIAL_SCOPE !== EXPECTED_CREDENTIAL_SCOPE) {
  const result = spawnSync(
    "python3",
    [
      join(SCRIPT_DIR, "ghl-runner.py"),
      "deploy",
      "--",
      ...process.argv.slice(2),
    ],
    { cwd: process.cwd(), env: process.env, stdio: "inherit" }
  );
  if (result.error) {
    fail("store-first GHL credential launcher nelze spustit");
  }
  process.exit(result.status ?? 1);
}

for (const name of [
  "GHL_API_KEY",
  "GHL_LOCATION_ID",
  "NETLIFY_AUTH_TOKEN",
  "OPENROUTER_API_KEY",
]) {
  if (!(process.env[name] ?? "").trim()) fail(`chybí spravovaná runtime proměnná ${name}`);
}

const credentialValidationErrors = validateFunnelSpec(spec, {
  locationId: process.env.GHL_LOCATION_ID.trim(),
});
if (credentialValidationErrors.length > 0) {
  fail(
    `funnel-spec.json neodpovídá zvolené GHL integraci:\n- ${credentialValidationErrors.join("\n- ")}`
  );
}

function syncBuildEnvironment() {
  if (/[\u0000-\u001f\u007f]/.test(process.env.GHL_API_KEY)) {
    fail("GHL credential má neplatný tvar");
  }
  const directory = mkdtempSync(join(tmpdir(), "aiq-netlify-ghl-"));
  const path = join(directory, "ghl.env");
  let syncFailure = "";
  try {
    writeFileSync(
      path,
      `GHL_API_KEY=${JSON.stringify(process.env.GHL_API_KEY)}\n` +
        `GHL_LOCATION_ID=${JSON.stringify(process.env.GHL_LOCATION_ID)}\n` +
        `OPENROUTER_API_KEY=${JSON.stringify(process.env.OPENROUTER_API_KEY)}\n`,
      { encoding: "utf8", mode: 0o600 }
    );
    const importEnv = { ...process.env };
    delete importEnv.GHL_API_KEY;
    delete importEnv.GHL_LOCATION_ID;
    delete importEnv.CC_GHL_CREDENTIAL_SCOPE;
    delete importEnv.AIQ_APP_ROOT;
    const result = spawnSync("netlify", ["env:import", path], {
      cwd: process.cwd(),
      env: importEnv,
      encoding: "utf8",
    });
    if (result.error || result.status !== 0) {
      syncFailure = netlifyImportFailure(result);
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
  if (syncFailure) {
    fail(`Deploy proměnné se nepodařilo bezpečně synchronizovat: ${syncFailure}`);
  }
  console.log("[aiq-deploy] GHL a OpenRouter build/runtime proměnné bezpečně synchronizovány");
}

syncBuildEnvironment();

console.log(
  `[aiq-deploy] potvrzeno: funnel=${spec.funnel_slug}, legacy-tags=${legacyTags}; spouštím produkční build`
);
const result = spawnSync("netlify", ["deploy", "--build", "--prod"], {
  cwd: process.cwd(),
  env: process.env,
  stdio: "inherit",
});

if (result.error) {
  console.error(`[aiq-deploy] Netlify CLI nelze spustit: ${result.error.message}`);
  process.exit(1);
}
process.exit(result.status ?? 1);
