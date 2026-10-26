#!/usr/bin/env node
/**
 * Safe GHL field provisioning for an AIQ funnel.
 *
 * Default:   read-only plan, persisted as fields-plan.json.
 * --apply:   create only the confirmed missing fields, then read back.
 * --verify:  read-only build gate; write fields-map.json only when complete.
 *
 * GHL credentials are accepted only through the short-lived child environment.
 * Their values are never logged or persisted.
 */

import { createHash } from "node:crypto";
import {
  readFileSync,
  renameSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { buildFieldPlan } from "./field-plan.mjs";

const DEFAULT_GHL_BASE = "https://services.leadconnectorhq.com";
const GHL_VERSION = "2021-07-28";
const __dirname = dirname(fileURLToPath(import.meta.url));
const configuredRoot = String(process.env.AIQ_APP_ROOT || "").trim();
if (
  configuredRoot &&
  process.env.CC_GHL_CREDENTIAL_SCOPE !== "aiq-funnel-builder"
) {
  throw new Error("AIQ_APP_ROOT lze použít jen přes credential-scoped launcher");
}
const ROOT = configuredRoot ? resolve(configuredRoot) : join(__dirname, "..");
const SPEC_PATH = join(ROOT, "funnel-spec.json");
const MAP_PATH = join(ROOT, "fields-map.json");
const PLAN_PATH = join(ROOT, "fields-plan.json");
const APPLY_REPORT_PATH = join(ROOT, "fields-apply-report.json");

function value(name) {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

const applyMode = process.argv.includes("--apply");
const verifyMode = process.argv.includes("--verify");
if (applyMode && verifyMode) {
  throw new Error("--apply a --verify nelze použít současně");
}
const mode = applyMode ? "apply" : verifyMode ? "verify" : "plan";
const confirmedPlanSha = value("confirm-plan-sha");
if (applyMode && !confirmedPlanSha) {
  throw new Error("--apply vyžaduje --confirm-plan-sha z read-only plánu");
}
if (!applyMode && confirmedPlanSha) {
  throw new Error("--confirm-plan-sha lze použít jen s --apply");
}

const apiKey = String(process.env.GHL_API_KEY || "").trim();
if (!apiKey) throw new Error("GHL integrace není pro tento běh dostupná");

let ghlBase = DEFAULT_GHL_BASE;
if (process.env.GHL_API_BASE_URL) {
  if (process.env.CC_GHL_ALLOW_TEST_BASE_URL !== "1") {
    throw new Error("vlastní GHL API base URL není v produkčním běhu povolená");
  }
  const candidate = new URL(String(process.env.GHL_API_BASE_URL));
  if (!["127.0.0.1", "::1", "localhost"].includes(candidate.hostname)) {
    throw new Error("testovací GHL API base URL musí být loopback");
  }
  ghlBase = candidate.toString().replace(/\/+$/, "");
}

let spec;
let specSource;
try {
  specSource = readFileSync(SPEC_PATH, "utf8");
  spec = JSON.parse(specSource);
} catch {
  throw new Error("funnel-spec.json není validní JSON");
}
if (!Array.isArray(spec.questions) || spec.questions.length === 0) {
  throw new Error("funnel-spec.json neobsahuje questions");
}
if (!Object.prototype.hasOwnProperty.call(spec, "consent_field_id")) {
  throw new Error("funnel-spec.json neobsahuje consent_field_id");
}

function normalizeLocationId(value) {
  let normalized = String(value || "").trim();
  if (!normalized) return "";
  try {
    const url = new URL(normalized);
    const match = url.pathname.match(/\/location\/([^/]+)/i);
    normalized = match?.[1] || url.searchParams.get("locationId") || "";
  } catch {
    // A bare location id is the normal input.
  }
  try {
    normalized = decodeURIComponent(normalized);
  } catch {
    return "";
  }
  normalized = normalized.trim().replace(/^loc_/i, "");
  return /^[A-Za-z0-9_-]{1,128}$/.test(normalized) ? normalized : "";
}

const envLocationRaw = String(process.env.GHL_LOCATION_ID || "").trim();
const specLocationRaw = String(spec.ghl_location_id || "").trim();
const envLocation = normalizeLocationId(envLocationRaw);
const specLocation = normalizeLocationId(specLocationRaw);
if ((envLocationRaw && !envLocation) || (specLocationRaw && !specLocation)) {
  throw new Error("GHL location ID má neplatný tvar");
}
if (envLocation && specLocation && envLocation !== specLocation) {
  throw new Error("GHL location ve funnel-spec.json neodpovídá zvolené integraci");
}
const locationId = envLocation || specLocation;
if (!locationId) throw new Error("GHL location ID chybí");

const tagPrefix = String(
  spec.ops?.tag_prefix || spec.ops?.magnet_tag || `AIQ ${spec.lead_magnet_name || ""}`
)
  .trim()
  .slice(0, 60);
if (!tagPrefix || tagPrefix === "AIQ") {
  throw new Error("funnel-spec.json neobsahuje použitelný tag prefix");
}

const personaFields = spec.persona_fields;
if (!Array.isArray(personaFields) || personaFields.length === 0) {
  throw new Error("funnel-spec.json neobsahuje persona_fields");
}

const fieldPlan = buildFieldPlan({
  tagPrefix,
  personaFields,
  magnetBlocks: [
    ...(Array.isArray(spec.magnet_structure) ? spec.magnet_structure : []),
    ...(Array.isArray(spec.magnet_middle) ? spec.magnet_middle : []),
  ],
});

function existingId(value) {
  if (typeof value !== "string" || !value.trim()) return null;
  const id = value.trim();
  if (!/^[A-Za-z0-9_-]{1,128}$/.test(id)) {
    throw new Error("funnel-spec.json obsahuje neplatný GHL field ID");
  }
  return id;
}

function questionDataType(question) {
  if (question?.type === "textarea") return "LARGE_TEXT";
  if (question?.type === "multi") return "MULTIPLE_OPTIONS";
  if (question?.type === "yesno" || question?.type === "single") {
    return "SINGLE_OPTIONS";
  }
  throw new Error(`otázka ${question?.id || "?"} má nepodporovaný typ`);
}

function compatibleQuestionTypes(dataType) {
  if (dataType === "LARGE_TEXT") return ["LARGE_TEXT", "TEXT"];
  if (dataType === "MULTIPLE_OPTIONS") {
    return ["MULTIPLE_OPTIONS", "LARGE_TEXT", "TEXT"];
  }
  return ["SINGLE_OPTIONS", "TEXT"];
}

const questionDefinitions = Array.isArray(spec.questions)
  ? spec.questions.map((question) => {
      const id = existingId(question?.field_id);
      const name = String(question?.field_name || "").trim();
      if (!id && !name) {
        throw new Error(
          `otázka ${question?.id || "?"} nemá field_id ani field_name`
        );
      }
      const dataType = questionDataType(question);
      const options =
        dataType === "SINGLE_OPTIONS" || dataType === "MULTIPLE_OPTIONS"
          ? [...(Array.isArray(question.options) ? question.options : [])].map(String)
          : [];
      if (
        (dataType === "SINGLE_OPTIONS" || dataType === "MULTIPLE_OPTIONS") &&
        options.length === 0
      ) {
        throw new Error(`otázka ${question?.id || "?"} nemá options`);
      }
      return {
        target: "question",
        key: String(question.id || ""),
        name: name || `existing:${id}`,
        dataType,
        compatibleDataTypes: compatibleQuestionTypes(dataType),
        options,
        existingId: id,
        assignSpecId: !id,
      };
    })
  : [];

const contractDefinitions = [];
if (Object.prototype.hasOwnProperty.call(spec, "consent_field_id")) {
  const id = existingId(spec.consent_field_id);
  contractDefinitions.push({
    target: "consent",
    key: "consent",
    name: `${tagPrefix} - Consent`,
    dataType: "TEXT",
    compatibleDataTypes: ["TEXT", "SINGLE_OPTIONS"],
    options: [],
    existingId: id,
    assignSpecId: !id,
  });
}
if (spec.derived_field_ids && typeof spec.derived_field_ids === "object") {
  for (const [key, label] of [
    ["score", "Score"],
    ["segment", "Segment"],
  ]) {
    if (!Object.prototype.hasOwnProperty.call(spec.derived_field_ids, key)) continue;
    const id = existingId(spec.derived_field_ids[key]);
    const dataType = key === "score" ? "NUMERICAL" : "TEXT";
    contractDefinitions.push({
      target: "derived",
      key,
      name: `${tagPrefix} - ${label}`,
      dataType,
      compatibleDataTypes: key === "score" ? ["NUMERICAL", "TEXT"] : ["TEXT"],
      options: [],
      existingId: id,
      assignSpecId: !id,
    });
  }
}

const definitions = [
  ...questionDefinitions,
  ...contractDefinitions,
  ...fieldPlan.persona.map((field) => ({
    ...field,
    target: "persona",
    compatibleDataTypes: [field.dataType],
    options: [],
    existingId: null,
    assignSpecId: false,
  })),
  {
    ...fieldPlan.temperature,
    key: "temperature",
    target: "special",
    compatibleDataTypes: [fieldPlan.temperature.dataType],
    options: [],
    existingId: null,
    assignSpecId: false,
  },
  {
    ...fieldPlan.scheduledIds,
    key: "scheduled_ids",
    target: "special",
    compatibleDataTypes: [fieldPlan.scheduledIds.dataType],
    options: [],
    existingId: null,
    assignSpecId: false,
  },
  {
    ...fieldPlan.sequenceEnd,
    key: "sequence_end",
    target: "special",
    compatibleDataTypes: [fieldPlan.sequenceEnd.dataType],
    options: [],
    existingId: null,
    assignSpecId: false,
  },
];

function assertUnique(values, label) {
  const seen = new Set();
  for (const rawValue of values) {
    const normalized = String(rawValue || "").trim().toLowerCase();
    if (!normalized || seen.has(normalized)) {
      throw new Error(`funnel-spec.json obsahuje duplicitní nebo prázdný ${label}`);
    }
    seen.add(normalized);
  }
}

assertUnique(questionDefinitions.map((field) => field.key), "question id");
assertUnique(personaFields, "persona field");
assertUnique(
  definitions.filter((field) => !field.existingId).map((field) => field.name),
  "název plánovaného GHL pole"
);
assertUnique(
  definitions.filter((field) => field.existingId).map((field) => field.existingId),
  "explicitní GHL field ID"
);

function headers() {
  return {
    Authorization: `Bearer ${apiKey}`,
    Version: GHL_VERSION,
    Accept: "application/json",
    "Content-Type": "application/json",
  };
}

function redactSecret(value) {
  if (typeof value === "string") return value.replaceAll(apiKey, "[REDACTED]");
  if (Array.isArray(value)) return value.map(redactSecret);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, redactSecret(item)])
    );
  }
  return value;
}

async function listCustomFields() {
  let response;
  try {
    const url = new URL(
      `/locations/${encodeURIComponent(locationId)}/customFields`,
      `${ghlBase}/`
    );
    url.searchParams.set("model", "contact");
    response = await fetch(url, { headers: headers(), redirect: "error" });
  } catch {
    throw new Error("GET customFields se nepodařilo spojit s GHL");
  }
  if (!response.ok) {
    throw new Error(`GET customFields selhal (HTTP ${response.status})`);
  }
  const json = redactSecret(await response.json().catch(() => null));
  if (!Array.isArray(json?.customFields)) {
    throw new Error("GHL vrátil neočekávaný tvar seznamu custom fields");
  }
  return json.customFields;
}

async function createCustomField(field) {
  let response;
  try {
    response = await fetch(
      new URL(
        `/locations/${encodeURIComponent(locationId)}/customFields`,
        `${ghlBase}/`
      ),
      {
        method: "POST",
        headers: headers(),
        redirect: "error",
        body: JSON.stringify({
          name: field.name,
          dataType: field.dataType,
          model: "contact",
          ...(field.options.length > 0 ? { options: field.options } : {}),
        }),
      }
    );
  } catch {
    throw new Error(`vytvoření pole „${field.name}“ se nepodařilo spojit s GHL`);
  }
  if (!response.ok) {
    throw new Error(
      `vytvoření pole „${field.name}“ selhalo (HTTP ${response.status})`
    );
  }
  const json = redactSecret(await response.json().catch(() => null));
  const id = json?.customField?.id ?? json?.id;
  if (!/^[A-Za-z0-9_-]{1,128}$/.test(String(id || ""))) {
    throw new Error(`vytvoření pole „${field.name}“ nevrátilo platné id`);
  }
  return String(id);
}

function analyze(existing) {
  const byName = new Map();
  const byId = new Map();
  for (const field of existing) {
    if (!field?.name || !field?.id) continue;
    if (!/^[A-Za-z0-9_-]{1,128}$/.test(String(field.id))) {
      throw new Error("GHL vrátil custom field s neplatným id");
    }
    byId.set(String(field.id), field);
    const key = String(field.name).trim().toLowerCase();
    const matches = byName.get(key) || [];
    matches.push(field);
    byName.set(key, matches);
  }

  const duplicates = [];
  const reused = [];
  const missing = [];
  const missingReferences = [];
  for (const definition of definitions) {
    if (definition.existingId) {
      const field = byId.get(definition.existingId);
      if (field) reused.push({ definition, field });
      else {
        missingReferences.push({
          target: definition.target,
          key: definition.key,
          id: definition.existingId,
        });
      }
      continue;
    }
    const matches = byName.get(definition.name.trim().toLowerCase()) || [];
    if (matches.length > 1) {
      duplicates.push({ name: definition.name, count: matches.length });
    } else if (matches.length === 1) {
      reused.push({ definition, field: matches[0] });
    } else {
      missing.push(definition);
    }
  }

  const mismatches = reused.flatMap(({ definition, field }) => {
    const actual = String(field.dataType || "").trim().toUpperCase() || "NEZNÁMÝ";
    const expected = String(definition.dataType).trim().toUpperCase();
    return definition.compatibleDataTypes.includes(actual)
      ? []
      : [
          {
            name: String(field.name),
            expected,
            compatible: definition.compatibleDataTypes,
            actual,
          },
        ];
  });
  function normalizedOptions(field) {
    const rawOptions = Array.isArray(field.picklistOptions)
      ? field.picklistOptions
      : Array.isArray(field.options)
        ? field.options
        : [];
    return rawOptions
      .map((option) =>
        typeof option === "string" ? option : String(option?.label || "")
      )
      .filter(Boolean);
  }
  const optionMismatches = reused.flatMap(({ definition, field }) => {
    if (definition.options.length === 0) return [];
    const actualType = String(field.dataType || "").trim().toUpperCase();
    if (!actualType.endsWith("_OPTIONS")) return [];
    const actual = normalizedOptions(field);
    const missingOptions = definition.options.filter(
      (option) => !actual.includes(option)
    );
    return missingOptions.length === 0
      ? []
      : [{ name: String(field.name), missing_options: missingOptions }];
  });
  const canonical = {
    schema: "aiq.ghl_field_plan.v1",
    funnel_slug: String(spec.funnel_slug || ""),
    location_id: locationId,
    tag_prefix: tagPrefix,
    fields: definitions.map((definition) => {
      const current = reused.find(
        (item) => item.definition === definition
      )?.field;
      return {
        target: definition.target,
        key: definition.key,
        name: definition.name,
        data_type: definition.dataType,
        compatible_data_types: definition.compatibleDataTypes,
        options: definition.options,
        expected_id: definition.existingId,
        current: current
          ? {
              id: String(current.id),
              data_type: String(current.dataType || "").trim().toUpperCase(),
              options: normalizedOptions(current),
            }
          : null,
      };
    }),
    duplicates,
    missing_references: missingReferences,
    mismatches,
    option_mismatches: optionMismatches,
  };
  const sha256 = createHash("sha256")
    .update(JSON.stringify(canonical))
    .digest("hex");
  return {
    canonical,
    sha256,
    duplicates,
    missingReferences,
    mismatches,
    optionMismatches,
    missing,
    reused,
  };
}

function atomicJson(path, valueToWrite) {
  const temporary = `${path}.tmp-${process.pid}`;
  try {
    writeFileSync(temporary, `${JSON.stringify(valueToWrite, null, 2)}\n`, {
      encoding: "utf8",
      mode: 0o600,
    });
    renameSync(temporary, path);
  } finally {
    rmSync(temporary, { force: true });
  }
}

function planDocument(analysis) {
  return {
    schema: "aiq.ghl_field_plan.v1",
    generated_at: new Date().toISOString(),
    plan_sha256: analysis.sha256,
    funnel_slug: analysis.canonical.funnel_slug,
    location_id: locationId,
    tag_prefix: tagPrefix,
    summary: {
      total: definitions.length,
      create: analysis.missing.length,
      reuse: analysis.reused.length,
      type_mismatches: analysis.mismatches.length,
      option_mismatches: analysis.optionMismatches.length,
      duplicate_names: analysis.duplicates.length,
      missing_references: analysis.missingReferences.length,
    },
    creates: analysis.missing.map((field) => ({
      target: field.target,
      key: field.key,
      name: field.name,
      data_type: field.dataType,
      options: field.options,
    })),
    reuses: analysis.reused.map(({ definition, field }) => ({
      target: definition.target,
      key: definition.key,
      name: String(field.name),
      id: String(field.id),
      data_type: String(field.dataType || "").trim().toUpperCase(),
    })),
    type_mismatches: analysis.mismatches,
    option_mismatches: analysis.optionMismatches,
    duplicate_names: analysis.duplicates,
    missing_references: analysis.missingReferences,
  };
}

function assertUsable(analysis) {
  if (analysis.duplicates.length > 0) {
    throw new Error(
      "GHL obsahuje duplicitní názvy plánovaných polí; je nutná ruční analýza"
    );
  }
  if (analysis.mismatches.length > 0) {
    throw new Error(
      "existující GHL pole mají nekompatibilní typ; je nutná řízená migrace"
    );
  }
  if (analysis.optionMismatches.length > 0) {
    throw new Error(
      "existující GHL výběrová pole neobsahují všechny hodnoty ze specu"
    );
  }
  if (analysis.missingReferences.length > 0) {
    throw new Error(
      "funnel-spec.json odkazuje na GHL field ID, které v cílové location neexistuje"
    );
  }
}

function writeResolvedSpec(analysis) {
  if (readFileSync(SPEC_PATH, "utf8") !== specSource) {
    throw new Error(
      "funnel-spec.json se během apply změnil; field ID nebyla zapsána přes stale obsah"
    );
  }
  const nextSpec = JSON.parse(JSON.stringify(spec));
  for (const { definition, field } of analysis.reused) {
    if (!definition.assignSpecId) continue;
    const id = String(field.id);
    if (definition.target === "question") {
      const question = nextSpec.questions.find(
        (candidate) => String(candidate.id || "") === definition.key
      );
      if (!question) throw new Error(`otázka ${definition.key} zmizela ze specu`);
      question.field_id = id;
      question.field_name = null;
    } else if (definition.target === "consent") {
      nextSpec.consent_field_id = id;
    } else if (definition.target === "derived") {
      nextSpec.derived_field_ids[definition.key] = id;
    }
  }
  atomicJson(SPEC_PATH, nextSpec);
}

function resolvedSpecAssignments(analysis) {
  return analysis.reused
    .filter(({ definition }) => definition.assignSpecId)
    .map(({ definition, field }) => ({
      target: definition.target,
      key: definition.key,
      id: String(field.id),
    }));
}

function assertSpecReferencesResolved(analysis) {
  const unresolved = analysis.reused.filter(
    ({ definition }) => definition.assignSpecId
  );
  if (unresolved.length > 0) {
    throw new Error(
      "GHL pole existují, ale funnel-spec.json ještě nemá jejich ID; spusťte potvrzený apply"
    );
  }
}

function writeFieldsMap(analysis) {
  assertUsable(analysis);
  if (analysis.missing.length > 0) {
    throw new Error(
      `GHL schema není kompletní; chybí ${analysis.missing.length} polí`
    );
  }
  const ids = new Map(
    analysis.reused.map(({ definition, field }) => [definition.name, String(field.id)])
  );
  const persona = {};
  for (const field of fieldPlan.persona) persona[field.key] = ids.get(field.name);
  atomicJson(MAP_PATH, {
    _generated: true,
    generated_at: new Date().toISOString(),
    location_id: locationId,
    persona,
    temperature_field_id: ids.get(fieldPlan.temperature.name),
    scheduled_ids_field_id: ids.get(fieldPlan.scheduledIds.name),
    sequence_end_field_id: ids.get(fieldPlan.sequenceEnd.name),
  });
}

async function readbackComplete() {
  const delays = [0, 500, 1500, 3000];
  let latest;
  for (const delay of delays) {
    if (delay) await new Promise((resolve) => setTimeout(resolve, delay));
    latest = analyze(await listCustomFields());
    if (
      latest.missing.length === 0 &&
      latest.mismatches.length === 0 &&
      latest.optionMismatches.length === 0 &&
      latest.missingReferences.length === 0 &&
      latest.duplicates.length === 0
    ) {
      return latest;
    }
  }
  return latest;
}

async function runPlan() {
  const analysis = analyze(await listCustomFields());
  atomicJson(PLAN_PATH, planDocument(analysis));
  console.log(
    `[ensure-fields] read-only plán: vytvořit ${analysis.missing.length}, použít ${analysis.reused.length}`
  );
  for (const field of analysis.missing) {
    console.log(`  + plán: ${field.name} (${field.dataType})`);
  }
  console.log(`[ensure-fields] plan SHA-256: ${analysis.sha256}`);
  console.log(`[ensure-fields] plán uložen: ${PLAN_PATH}`);
  assertUsable(analysis);
}

async function runApply() {
  const before = analyze(await listCustomFields());
  atomicJson(PLAN_PATH, planDocument(before));
  assertUsable(before);
  if (before.sha256 !== confirmedPlanSha) {
    throw new Error(
      "GHL stav se od schváleného plánu změnil; vytvořte nový read-only plán"
    );
  }

  const created = [];
  const report = {
    schema: "aiq.ghl_field_apply_report.v1",
    started_at: new Date().toISOString(),
    completed_at: null,
    status: "running",
    confirmed_plan_sha256: confirmedPlanSha,
    location_id: locationId,
    requested_creates: before.missing.length,
    created,
    assigned_spec_ids: [],
    error: null,
  };
  atomicJson(APPLY_REPORT_PATH, report);
  try {
    for (const field of before.missing) {
      const id = await createCustomField(field);
      created.push({ name: field.name, data_type: field.dataType, id });
      atomicJson(APPLY_REPORT_PATH, report);
      console.log(`  + vytvořeno: ${field.name} (${field.dataType})`);
    }
    const after = await readbackComplete();
    assertUsable(after);
    writeResolvedSpec(after);
    writeFieldsMap(after);
    report.assigned_spec_ids = resolvedSpecAssignments(after);
    report.status = "complete";
    report.completed_at = new Date().toISOString();
    atomicJson(APPLY_REPORT_PATH, report);
    console.log(
      `[ensure-fields] apply ověřen — vytvořeno ${created.length}, použito ${after.reused.length}`
    );
    console.log(`[ensure-fields] mapa zapsána: ${MAP_PATH}`);
  } catch (error) {
    report.status = created.length > 0 ? "partial" : "failed";
    report.completed_at = new Date().toISOString();
    report.error = error instanceof Error ? error.message : "neznámá chyba";
    atomicJson(APPLY_REPORT_PATH, report);
    throw error;
  }
}

async function runVerify() {
  const analysis = analyze(await listCustomFields());
  assertSpecReferencesResolved(analysis);
  writeFieldsMap(analysis);
  console.log(
    `[ensure-fields] read-only verify OK — ${analysis.reused.length} polí, žádný GHL zápis`
  );
}

async function main() {
  console.log(`[ensure-fields] režim: ${mode}; location: ${locationId}`);
  if (mode === "plan") return runPlan();
  if (mode === "apply") return runApply();
  return runVerify();
}

main().catch((error) => {
  console.error(
    `[ensure-fields] STOP: ${error instanceof Error ? error.message : "neznámá chyba"}`
  );
  process.exitCode = 1;
});
