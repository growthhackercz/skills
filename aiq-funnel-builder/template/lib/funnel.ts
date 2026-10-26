import { spec, BRAND, Segment, Temperature } from "./spec";
import type { BenchmarkRow } from "./spec";

export type Answers = Record<string, string | string[] | undefined>;

export interface Vars {
  first_name: string;
  score: number;
  score_category: string; // human label, e.g. "vysoká zátěž"
  category_key: string; // raw key: vysoka_zatez | stredni | nizka
  top_pain: string;
  recommended_variant: string;
  segment_headline: string;
  segment_proof: string;
  cta_offer: string;
}

// Human-readable label for a category key.
export const CATEGORY_LABELS: Record<string, string> = {
  vysoka_zatez: "vysoká zátěž",
  stredni: "střední zátěž",
  nizka: "nízká zátěž",
};

/** Lidsky čitelný název kategorie: band.label ze specu → známý label → klíč. */
export function categoryLabel(categoryKey: string): string {
  const band = spec.scoring_bands.find((b) => b.category === categoryKey);
  return (
    band?.label ?? CATEGORY_LABELS[categoryKey] ?? categoryKey.replace(/_/g, " ")
  );
}

// Vokativ (5. pád) — nepravidelné/prchavé -e a měkké kmeny, co pravidla netrefí.
const VOC_EXCEPTIONS: Record<string, string> = {
  petr: "Petře",
  pavel: "Pavle",
  karel: "Karle",
  havel: "Havle",
  bedřich: "Bedřichu",
};

/**
 * Křestní jméno v českém 5. pádě (oslovení): Jan→Jane, Petra→Petro, Tomáš→Tomáši,
 * Marek→Marku, Dominik→Dominiku. Heuristika pro běžná jména; u nejistých ponechá
 * 1. pád (oslovení je pořád, jen bez skloňování). Víceslovné → jen první jméno.
 */
export function czVocative(name: string): string {
  const raw = (name || "").trim();
  if (!raw) return "";
  const first = raw.split(/\s+/)[0];
  const low = first.toLowerCase();
  if (VOC_EXCEPTIONS[low]) return VOC_EXCEPTIONS[low];
  const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
  const a = low.slice(-1);
  const a2 = low.slice(-2);

  if (a === "a") return cap(low.slice(0, -1) + "o"); // Petra→Petro, Jarda→Jardo
  if (a === "e") return first; // Marie, Lucie — beze změny
  if ("iíyýoóuů".includes(a)) return first; // Jiří, Ivo — vokál na konci
  if (a2 === "ek") return cap(low.slice(0, -2) + "ku"); // Marek→Marku
  if ("šžčřjcďťň".includes(a)) return cap(low + "i"); // Tomáš→Tomáši, Ondřej→Ondřeji
  if ("kgh".includes(a)) return cap(low + "u"); // Dominik→Dominiku, Bedřich→…chu
  return cap(low + "e"); // Jan→Jane, Martin→Martine, Dalibor→Dalibore
}

/**
 * Skóre = součet bodů ze VŠECH otázek, které mají `score` mapu — bez ohledu na
 * typ. Rozhoduje přítomnost mapy, ne `type`: mechanismus „šok z čísla" používá
 * `single` s odstupňovanými body (kolik lahví ročně…), ne jen ano/ne.
 *
 * U `multi` se sečtou body za všechny vybrané hodnoty. Strop 100.
 */
export function computeScore(answers: Answers): number {
  let total = 0;
  for (const q of spec.questions) {
    if (!q.score) continue;
    const raw = answers[q.id];
    if (raw == null || raw === "") continue;
    const values = Array.isArray(raw) ? raw : [raw];
    for (const v of values) {
      const points = q.score[String(v)];
      if (typeof points === "number") total += points;
    }
  }
  // Podlaha 0: penalizační body ve `score` mapě by jinak daly záporné skóre,
  // které /vysledek ukáže jako „-10/100" a server.ts si ho clampne na 0 →
  // submit a reload by se rozešly.
  return Math.min(Math.max(total, 0), 100);
}

/* ===== F2: dílčí skóre oblastí (rozpad hlavního skóre) ===== */

export interface AreaScore {
  key: string;
  label: string;
  /** 0–100, šířka baru. */
  pct: number;
  /** kvalitativní verdikt (nízká/střední/vysoká) — label místo pseudo-%. */
  verdict: string;
  /** ukázat číslo %? Jen u oblastí s ≥4 gradacemi (jinak pseudo-přesnost). */
  showPct: boolean;
}

/**
 * Rozpad skóre na oblasti ze `spec.score_areas`. `area% = body / max × 100`.
 * Verdikt = kvalitativní label (u yes/no oblastí je 0/50/100 jen binární, tak
 * ukazujeme slovo, ne fake %). Prázdné `score_areas` → [].
 */
export function computeAreaScores(answers: Answers): AreaScore[] {
  const areas = spec.score_areas ?? [];
  return areas.map((area) => {
    let got = 0;
    let max = 0;
    const grads = new Set<number>();
    for (const qid of area.questions) {
      const q = spec.questions.find((x) => x.id === qid);
      if (!q || !q.score) continue;
      const pts = Object.values(q.score);
      max += Math.max(0, ...pts);
      pts.forEach((p) => {
        if (p > 0) grads.add(p);
      });
      for (const v of answerValues(answers, qid)) {
        const p = q.score[v];
        if (typeof p === "number" && p > 0) got += p;
      }
    }
    const pct = max > 0 ? Math.round(Math.min(100, Math.max(0, (got / max) * 100))) : 0;
    const level = pct >= 67 ? "high" : pct >= 34 ? "mid" : "low";
    const fallbackVerdict = { high: "vysoká", mid: "střední", low: "nízká" }[level];
    const verdict = area.verdicts?.[level] ?? fallbackVerdict;
    return { key: area.key, label: area.label, pct, verdict, showPct: grads.size >= 4 };
  });
}

/* ===== F1: verbatim odpovědi pro citační kartičky ===== */

export interface QuotableAnswer {
  qid: string;
  question: string;
  answer: string;
}

/**
 * Odpovědi do „problémového zrcadla" na magnetu — TOP-N otázek, které odhalují
 * REÁLNÝ PROBLÉM klienta (uvědomění si problému, ještě před produktem).
 *
 * Zařazení:
 *  - VYLOUČIT: textarea (PII/injection); routing otázku (nese CTA směr / signál
 *    rozpočtu — není to problém); role objection/routing/qualifying/open.
 *  - ZAHRNOUT bohaté problémové: single/multi s ≥3 možnostmi (přání i diagnostika).
 *  - ZAHRNOUT diagnostické yes/no: jen ty se `score` (nebo role diagnostic) —
 *    holé „Ne" u diagnostické otázky (viděli/víte/znáte) odhaluje mezeru; generické ano/ne ne.
 *
 * POŘADÍ: bohaté (single/multi) první → dostanou hloubkový dopad (problem1-3);
 * diagnostické yes/no za nimi jako čistý mirror „černé na bílém".
 */
/**
 * Qids, které MOHOU jít do problémového zrcadla (bez ohledu na konkrétní odpovědi)
 * — jediný zdroj pravdy pro pořadí i pro validaci `problemN_source` v personalize.
 * Pořadí: bohaté (single/multi ≥3) první, diagnostické yes/no (se `score`/role
 * diagnostic) za nimi. Vyloučené: textarea, routing otázka, role objection/…/open.
 */
export function quotableQids(): string[] {
  const routeQid = spec.questions.find((q) =>
    (q.options ?? []).some((o) => Boolean(spec.cta_routes[o]))
  )?.id;
  const EXCLUDE_ROLES = new Set(["objection", "routing", "qualifying", "open"]);

  const rich: string[] = [];
  const diagnostic: string[] = [];
  for (const q of spec.questions) {
    if (q.type === "textarea") continue;
    if (q.id === routeQid) continue;
    if (q.role && EXCLUDE_ROLES.has(q.role)) continue;
    if (q.type === "yesno") {
      if (!q.score && q.role !== "diagnostic") continue;
      diagnostic.push(q.id);
    } else {
      if ((q.options?.length ?? 0) < 3) continue;
      rich.push(q.id);
    }
  }
  return [...rich, ...diagnostic];
}

export function quotableAnswers(answers: Answers): QuotableAnswer[] {
  const out: QuotableAnswer[] = [];
  for (const qid of quotableQids()) {
    const q = spec.questions.find((x) => x.id === qid);
    if (!q) continue;
    const vals = answerValues(answers, qid);
    if (vals.length === 0) continue;
    out.push({ qid, question: q.text, answer: vals.join(", ") });
  }
  return out;
}

/** Verbatim odpověď na konkrétní otázku (pro párování problemN_source). */
export function answerText(answers: Answers, qid: string): string {
  return answerValues(answers, qid).join(", ");
}

/* ===== F3: benchmark „šok z čísla" ===== */

export function benchmarkRow(
  answers: Answers
): {
  row: BenchmarkRow;
  solutionLabel?: string;
  todayText?: string;
  solutionText?: string;
} | null {
  const bm = spec.benchmark;
  if (!bm) return null;
  const val = answerValues(answers, bm.question)[0];
  if (!val) return null;
  const row = bm.rows[val];
  if (!row) return null;
  return {
    row,
    solutionLabel: bm.solution_label,
    todayText: bm.today_text,
    solutionText: bm.solution_text,
  };
}

/**
 * Práh na číslo. Chybějící prahy NESMÍ tiše spadnout na „cold" — spec, který
 * kvalifikuje z odpovědí, je klidně vynechá a bez téhle kontroly by pak byl
 * každý lead studený bez jediné stopy v logu.
 */
function byThreshold(value: number): Temperature {
  const rules = spec.temperature_rules;
  if (typeof rules.hot_min !== "number" || typeof rules.warm_min !== "number") {
    console.warn(
      "[funnel] temperature_rules nemá hot_min/warm_min — nelze prahovat, " +
        "vracím cold. Doplň prahy, nebo použij source, který je nepotřebuje."
    );
    return "cold";
  }
  if (value >= rules.hot_min) return "hot";
  if (value >= rules.warm_min) return "warm";
  return "cold";
}

/** Odpověď na otázku jako pole hodnot (multi → pole, single → 1 prvek). */
function answerValues(answers: Answers, questionId: string): string[] {
  const raw = answers[questionId];
  if (raw == null || raw === "") return [];
  return (Array.isArray(raw) ? raw : [raw]).map(String).filter(Boolean);
}

/**
 * Teplota leada (hot/warm/cold) podle `spec.temperature_rules.source`.
 *
 * Skóre měří MEZERU („jak na tom jste"), ne nákupní záměr — proto nové funnely
 * kvalifikují z bloku kvalifikace (`urgency_budget`), typicky z otázky na
 * preferované řešení, která nese signál rozpočtu. `score` zůstává výchozí kvůli
 * starším specům.
 *
 * Když je zdroj nakonfigurovaný špatně (chybí `question` apod.), spadne to na
 * práh skóre a **zaloguje se to** — tichý fallback by znamenal, že spec slibuje
 * jednu logiku a běží jiná.
 */
export function temperature(score: number, answers: Answers): Temperature {
  const rules = spec.temperature_rules;
  const source = rules.source || "score";

  switch (source) {
    case "urgency_budget": {
      if (!rules.question) break;
      // Prázdné hot[] i warm[] = každý lead cold. To je skoro jistě chyba
      // konfigurace, ne záměr — nesmí projít potichu.
      if ((rules.hot?.length ?? 0) === 0 && (rules.warm?.length ?? 0) === 0) {
        console.warn(
          `[funnel] urgency_budget u "${rules.question}" nemá hot[] ani warm[] — ` +
            "všichni by byli cold. Padám na práh skóre."
        );
        break;
      }
      const values = answerValues(answers, rules.question);
      if (values.length === 0) return "cold"; // neodpověděl → nekvalifikovaný
      if (values.some((v) => (rules.hot ?? []).includes(v))) return "hot";
      if (values.some((v) => (rules.warm ?? []).includes(v))) return "warm";
      return "cold";
    }

    case "critical_areas": {
      if (!rules.question) break;
      const critical = rules.critical ?? [];
      if (critical.length === 0) {
        console.warn(
          `[funnel] critical_areas u "${rules.question}" nemá critical[] — ` +
            "nic se nikdy netrefí. Padám na práh skóre."
        );
        break;
      }
      const hits = answerValues(answers, rules.question).filter((v) =>
        critical.includes(v)
      ).length;
      return byThreshold(hits);
    }

    case "score":
      return byThreshold(score);
  }

  console.warn(
    `[funnel] temperature_rules.source="${source}" nelze vyhodnotit ` +
      `(chybí question/critical?) — padám na práh skóre.`
  );
  return byThreshold(score);
}

/** @deprecated Použij temperature(score, answers) — zdroj řídí spec. */
export function temperatureFromScore(score: number): Temperature {
  return byThreshold(score);
}

/**
 * Namapuje skóre na kategorii pásma. Pásma jsou řazená shora dolů (nejvyšší
 * první — na to spoléhá i ctaOffer).
 *
 * Fallback je SMĚROVÝ, ne „poslední pásmo": když skóre přeteče horní hranici
 * nejvyššího pásma (dosažitelné maximum > strop pásem — chyba konfigurace),
 * dřívější „vezmi poslední" poslalo nejlepší lead do NEJNIŽŠÍ kategorie
 * (zelená, cold CTA). Teď skóre nad rozsah → nejvyšší pásmo, pod rozsah →
 * nejnižší.
 */
export function band(score: number): string {
  const bands = spec.scoring_bands;
  for (const b of bands) {
    if (score >= b.min && score <= b.max) return b.category;
  }
  const top = bands[0];
  const bottom = bands[bands.length - 1];
  if (score > top.max) return top.category;
  return bottom.category;
}

/** Normalise an answer to an array of selected string values. */
function asArray(value: string | string[] | undefined): string[] {
  if (value == null) return [];
  if (Array.isArray(value)) return value;
  // multi-select stored as CSV string -> split back
  return value.includes(", ") ? value.split(", ") : [value];
}

/**
 * First segment whose trigger matches.
 * - trigger.contains: the answer (multi) contains the value
 * - trigger.equals: the answer equals the value
 */
export function pickSegment(answers: Answers): Segment | null {
  for (const segment of spec.segments) {
    const { q, contains, equals } = segment.trigger;
    const answer = answers[q];
    if (contains != null) {
      if (asArray(answer).includes(contains)) return segment;
    } else if (equals != null) {
      const single = Array.isArray(answer) ? answer[0] : answer;
      if (single === equals) return segment;
    }
  }
  return null;
}

/** top_pain = first 1–2 items from q7, joined by "a", lowercase. */
export function buildTopPain(answers: Answers): string {
  const items = asArray(answers["q7"]).slice(0, 2);
  if (items.length === 0) return "";
  return items.map((s) => s.toLowerCase()).join(" a ");
}

/**
 * Deterministický H1 (předpřipravená kombinace) — vybere variantu podle odpovědi
 * klienta na `spec.headline.by_question`. Zobrazí se HNED (žádné AI). Do renderu
 * se prependuje oslovení ve vokativu, proto varianty začínají malým písmenem.
 */
export function buildHeadline(answers: Answers): string {
  const h = spec.headline;
  if (!h) return "";
  for (const v of asArray(answers[h.by_question])) {
    if (h.variants[v]) return h.variants[v];
  }
  return h.default;
}

/** CTA copy keyed by category. */
export function ctaOffer(categoryKey: string, routeAnswer?: string): string {
  const route = routeAnswer ? spec.cta_routes[routeAnswer] : undefined;
  if (route?.cta) {
    return `Váš další krok: ${route.cta}.`;
  }
  // Univerzálně přes scoring_bands pořadí (klíče kategorií jsou per funnel):
  // 1. band = nejvyšší → konzultace; 2. = doporučení; ostatní → klidný přehled.
  const bands = spec.scoring_bands.map((b) => b.category);
  const product = spec.offer.product;
  if (categoryKey === bands[0]) {
    return `Rezervujte si osobní konzultaci ${BRAND.name} — pomůžeme vybrat řešení a probereme další krok.`;
  }
  if (categoryKey === bands[1]) {
    return "Pošleme vám doporučení na míru. Když budete chtít, probereme to osobně.";
  }
  return `Pošleme vám klidný přehled, podle čeho poznat, kdy má ${product} opravdu smysl.`;
}

export function routeAnswerFromAnswers(answers: Answers): string {
  const routeQuestion = spec.questions.find((q) =>
    (q.options ?? []).some((option) => Boolean(spec.cta_routes[option]))
  );
  const raw = routeQuestion ? answers[routeQuestion.id] : answers["q13"];
  return Array.isArray(raw) ? raw[0] ?? "" : raw ?? "";
}

export interface BuildVarsInput {
  firstName: string;
  answers: Answers;
}

/**
 * Build the full personalization Vars object from answers.
 * Shared between /api/submit and bundleFromContact so the two stay in sync.
 */
export function buildVars({ firstName, answers }: BuildVarsInput): Vars {
  const score = computeScore(answers);
  const categoryKey = band(score);
  const segment = pickSegment(answers);

  const recommendedVariant = routeAnswerFromAnswers(answers);

  // Fallback (žádný segment nematchnul) — NEJMENUJ produkt (magnet neprodává;
  // produkt patří až na /r). Cold lead by jinak dostal nejtvrdší pitch.
  const fallbackHeadline = `Doporučení sestavené podle vašich odpovědí`;
  const fallbackProof = `Připravili jsme přehled přesně pro vaši situaci — z toho, co vás trápí a co chcete zlepšit. Bez tlaku, jen věcně.`;

  return {
    first_name: firstName || "",
    score,
    score_category: categoryLabel(categoryKey),
    category_key: categoryKey,
    top_pain: buildTopPain(answers),
    recommended_variant: recommendedVariant,
    segment_headline: segment ? segment.headline : fallbackHeadline,
    segment_proof: segment ? segment.proof : fallbackProof,
    cta_offer: ctaOffer(categoryKey, recommendedVariant),
  };
}
