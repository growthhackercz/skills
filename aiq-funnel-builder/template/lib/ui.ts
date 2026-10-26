/** Shared UI helpers for category presentation (color + copy). */

export function categoryColor(categoryKey: string): string {
  // Barvy VÝHRADNĚ z design tokenů (brand roura) — dřív natvrdo. Univerzálně
  // přes pořadí scoring_bands (klíče kategorií jsou per funnel).
  const bands = _spec.scoring_bands.map((b) => b.category);
  if (categoryKey === bands[0]) return token("gold"); // nejvyšší pásmo
  if (categoryKey === bands[1]) return token("accent"); // střední pásmo
  return token("tertiary"); // nízké pásmo
}

export type { MechanismItem } from "./spec";

/**
 * Nouzové mechanismy z offer.usp — použije se, JEN když spec nemá blok
 * `mechanisms`. Řeže i na čárkách, protože usp bývá jedno dlouhé souvětí a
 * split jen na tečkách by vrátil jediný blok přes celou sekci.
 *
 * Vrací záměrně jen nadpis bez textu: usp je výčet vlastností, ne vysvětlení
 * mechanismu. Dopisovat k němu prózu by znamenalo fabulovat, useknout ho na
 * nadpis+text zase dělá kartu, kde je nadpis půlka vlastní věty. Pořádné
 * bloky patří do spec.mechanisms (G17).
 */
function uspMechanisms(): _MechanismItem[] {
  return _spec.offer.usp
    .split(/[.;,]\s+/)
    .map((t) => t.trim().replace(/\.$/, ""))
    .filter((t) => t.length > 8)
    .slice(0, 3)
    .map((t) => ({
      title: t.charAt(0).toUpperCase() + t.slice(1),
      text: "",
    }));
}

/**
 * Vybere 2–3 mechanismus bloky relevantní k odpovědím na bolestivou otázku.
 *
 * Data jsou VÝHRADNĚ ze spec.mechanisms (per funnel) — šablona nesmí obsahovat
 * copy žádného konkrétního produktu (G17). Když spec blok nemá, poskládá se
 * nouzově z offer.usp; prázdné pole = volající sekci skryje.
 */
export function mechanismForPains(pains: string[]): _MechanismItem[] {
  const byPain = _spec.mechanisms?.by_pain ?? {};
  const defaults = _spec.mechanisms?.default ?? [];

  const picked: _MechanismItem[] = [];
  for (const pain of pains) {
    const item = byPain[pain];
    if (item && !picked.some((p) => p.title === item.title)) picked.push(item);
    if (picked.length === 3) break;
  }

  if (picked.length === 0) {
    return defaults.length > 0 ? defaults.slice(0, 3) : uspMechanisms();
  }
  // Doplň na 2 bloky (sekce s jednou kartou vypadá rozbitě) — nejdřív z defaults,
  // pak nouzově z usp. Fallback pár po title, ať se blok nezopakuje.
  const fillers = [...defaults, ...uspMechanisms()];
  for (const f of fillers) {
    if (picked.length >= 2) break;
    if (!picked.some((p) => p.title === f.title)) picked.push(f);
  }
  return picked.slice(0, 3);
}

/** Short, calm framing sentence per category (vykání, no scare tactics). */
export function categorySummary(categoryKey: string): string {
  // Interpretace kategorie žije ve specu (main_result.meaning per funnel).
  const meaning = _spec.main_result?.meaning?.[categoryKey];
  if (meaning) return meaning;
  return "Vaše odpovědi jsme vyhodnotili a připravili z nich doporučení na míru.";
}


/* ===== Variant-agnostický main_result render (v0.5: score | plan) ===== */
import { spec as _spec, token } from "./spec";
import type { MechanismItem as _MechanismItem } from "./spec";
import type { Answers as _Answers } from "./funnel";

export interface MainResultView {
  kind: "score" | "plan";
  label: string;
  score?: number | null;
  unit?: string;
  /** plan variantě: hotový text plánu (z plan_by_priority dle prioritní otázky) */
  display?: string;
}

export function mainResultView(
  score: number | null,
  answers: _Answers
): MainResultView {
  const mr = _spec.main_result as unknown as {
    type?: string;
    label: string;
    unit?: string;
    priority_question?: string;
    plan_by_priority?: Record<string, string>;
  };
  if (mr.type === "plan") {
    const pq = mr.priority_question || "q7";
    const raw = answers[pq];
    const key =
      typeof raw === "string" ? raw : Array.isArray(raw) ? raw[0] ?? "" : "";
    const map = mr.plan_by_priority ?? {};
    const display = map[key] ?? map["_default"] ?? mr.label;
    return { kind: "plan", label: mr.label, display };
  }
  return { kind: "score", label: mr.label, score, unit: mr.unit || "/100" };
}

/* ===== Dynamický magnet: normalizace bloků ze spec.magnet_structure ===== */
import type { MagnetBlock, MagnetRender } from "./spec";

/**
 * Mapování starých `key` → (render, persona_field) pro specy bez nového
 * kontraktu. Díky tomu živé funnely (starý magnet_structure) fungují beze změny.
 */
const MAGNET_LEGACY: Record<string, { render: MagnetRender; persona_field?: string }> = {
  main_result: { render: "main_result" },
  rozbor: { render: "text", persona_field: "magnet_rozbor" },
  // `benchmark` záměrně chybí → resolveMagnetBlocks ho vynechá, jako se
  // static_optional blok vynechával v pevném renderu (nemá vlastní data ani pole).
  dobre: { render: "text", persona_field: "magnet_dobre" },
  rizika: { render: "text", persona_field: "magnet_rizika" },
  akce: { render: "steps", persona_field: "magnet_akce" },
  predpis_teaser: { render: "openloop", persona_field: "predpis_config" },
  segment_dukaz: { render: "segment" },
  cta: { render: "cta" },
};

/**
 * Výchozí pořadí bloků, když spec.magnet_structure chybí nebo se nedá vyřešit.
 * Všechny klíče existují v MAGNET_LEGACY → resolvnou se na plnohodnotný magnet
 * (jinak by stránka byla jen H1 + patička a nic mezi tím). `benchmark` tu
 * záměrně není (nemá vlastní data ani pole).
 */
export const DEFAULT_MAGNET_KEYS = [
  "main_result",
  "rozbor",
  "dobre",
  "rizika",
  "akce",
  "predpis_teaser",
  "segment_dukaz",
  "cta",
];

/** Fallback nadpisy pro default magnet (spec by je jinak dodal v `title`). */
const DEFAULT_MAGNET_TITLES: Record<string, string> = {
  main_result: "Váš výsledek",
  rozbor: "Co říkají vaše odpovědi",
  dobre: "Co už děláte dobře",
  rizika: "Kde máte největší rezervy",
  akce: "Co můžete udělat hned",
  predpis_teaser: "Váš předpis na míru",
  segment_dukaz: "Nejste v tom sami",
  cta: "Další krok",
};

export interface ResolvedMagnetBlock {
  key: string;
  title: string;
  render: MagnetRender;
  /** LLM bloky: persona pole s vygenerovaným textem. */
  personaField?: string;
}

/**
 * Kanonizuje spec.magnet_structure na bloky, které runtime umí vykreslit.
 * Nový formát (blok má `render`) se použije přímo; starý se dohledá v
 * MAGNET_LEGACY podle `key`. Bloky, které nejde vyřešit, se vynechají (ne crash).
 */
export function resolveMagnetBlocks(): ResolvedMagnetBlock[] {
  const blocks = (_spec.magnet_structure ?? []) as MagnetBlock[];
  const personaFields = _spec.persona_fields ?? [];
  const out: ResolvedMagnetBlock[] = [];
  for (const b of blocks) {
    const render = b.render ?? MAGNET_LEGACY[b.key]?.render;
    if (!render) {
      // Tichý drop = neviditelná díra v magnetu. Řekni to nahlas.
      console.warn(
        `[magnet] blok "${b.key}" nemá render ani MAGNET_LEGACY mapování → vynechán.`
      );
      continue;
    }
    const personaField =
      b.persona_field ?? MAGNET_LEGACY[b.key]?.persona_field;
    // Cross-validace: pole, které není v persona_fields, se nikdy nevytvoří
    // (ensure-fields) ani nenaplní (personalize). Blok nezahazuj, jen varuj.
    if (personaField && !personaFields.includes(personaField)) {
      console.warn(
        `[magnet] blok "${b.key}" odkazuje persona_field "${personaField}", ` +
          `který není v spec.persona_fields — nevytvoří se ani nevygeneruje.`
      );
    }
    out.push({ key: b.key, title: b.title, render, personaField });
  }

  // Guard: rozbité/chybějící magnet_structure (prázdný výstup) → default legacy
  // pořadí. Bez toho by se magnet vyrenderoval jen jako H1 + patička.
  if (out.length === 0) {
    console.warn(
      "[magnet] magnet_structure prázdné/nevyřešitelné, používám default."
    );
    return resolveDefaultMagnetBlocks();
  }
  return out;
}

/** Sestaví magnet z DEFAULT_MAGNET_KEYS přes MAGNET_LEGACY (nouzový fallback). */
function resolveDefaultMagnetBlocks(): ResolvedMagnetBlock[] {
  const out: ResolvedMagnetBlock[] = [];
  for (const key of DEFAULT_MAGNET_KEYS) {
    const legacy = MAGNET_LEGACY[key];
    if (!legacy) continue;
    out.push({
      key,
      title: DEFAULT_MAGNET_TITLES[key] ?? key,
      render: legacy.render,
      personaField: legacy.persona_field,
    });
  }
  return out;
}
