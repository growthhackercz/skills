import specJson from "../funnel-spec.json";

export type QuestionType = "yesno" | "single" | "multi" | "textarea";

/**
 * Role otázky — řídí, jestli patří do „problémového zrcadla" na magnetu.
 * Do TOP-N verbatim (uvědomění problému) jdou jen problémové/diagnostické otázky;
 * námitka/routing/otevřená se vylučují (nejsou to problémy klienta).
 * Chybí-li role: single/multi ≥3 možnosti = problémová, yes/no jen se `score`.
 */
export type QuestionRole =
  | "diagnostic" // odhaluje problém/mezeru (nese i skóre)
  | "problem" // problém/přání (co chce zlepšit) — synonymum k diagnostic pro mirror
  | "objection" // co ho brzdí (cena, čas…) — NENÍ problém
  | "routing" // preferovaný další krok / signál rozpočtu
  | "qualifying" // jiná kvalifikace
  | "open"; // otevřená / textarea

export interface Question {
  id: string;
  type: QuestionType;
  field_id: string;
  text: string;
  options?: string[];
  score?: Record<string, number>;
  /** Viz QuestionRole — řídí zařazení do problémového zrcadla na magnetu. */
  role?: QuestionRole;
  /**
   * Deterministické KONSTATOVÁNÍ odpovědi pro „punch list" pod hero (rychlé
   * uvědomění rizik). Klíč = PŘESNÁ hodnota PROBLÉMOVÉ odpovědi (u yesno typicky
   * „Ne" nebo „Ano") → věta-fakt (vykání), např. „[danou věc] jste nikdy neviděli".
   * Uveď JEN problémovou odpověď (ta, co odhaluje mezeru/riziko); neproblémovou
   * vynech. Render je deterministický a INSTANTNÍ (bez AI) — vždy přesná sada,
   * žádné vynechání ani záměna (Flash to spolehlivě netrefil). Typicky u yesno.
   */
  problem_statement?: Record<string, string>;
}

export interface ScoringBand {
  min: number;
  max: number;
  category: string;
  action: string;
  /** Lidsky čitelný název kategorie pro UI (např. „vysoká zátěž"). */
  label?: string;
}

export interface SegmentTrigger {
  q: string;
  contains?: string;
  equals?: string;
}

export interface Segment {
  key: string;
  trigger: SegmentTrigger;
  headline: string;
  proof: string;
}

export interface Offer {
  product: string;
  usp: string;
  guarantee: string;
  price_note: string;
  variants: string[];
}

/**
 * Recenze zákazníka (social proof pro render `reviews`). Data VÝHRADNĚ ze
 * spec.reviews per funnel — šablona nesmí nést recenzi žádného produktu.
 * Jen křestní jméno / jméno + kontext, žádné příjmení ani fotka.
 *
 * ⚠️ Placeholder-flag: pokud productDNA nemá reálné recenze, strategie sem
 * vloží UKÁZKOVÉ a v 01-strategie.md to VÝSLOVNĚ označí jako dočasné k nahrazení
 * / smazání klientem. Nikdy nevydávat vymyšlenou recenzi za pravou.
 */
export interface Review {
  /** Křestní jméno nebo jméno + město (bez příjmení, bez fotky). */
  name: string;
  /** Volitelný kontext („Brno", „majitelka 2 roky"). */
  meta?: string;
  /** Text recenze — 1–3 věty, hlas zákazníka. */
  text: string;
  /** Volitelné hodnocení 1–5 (render ukáže hvězdičky). */
  rating?: number;
}

/**
 * Barvy a typografie z klientova DESIGN.md / Brand Kitu. Tečou do šablony
 * runtime přes designTokenStyle() (inline :root na <html>) — každý chybějící
 * klíč spadne na neutrální default (TOKEN_FALLBACK), takže starší funnely bez
 * kompletní palety běží dál. Názvy jsou ROLE, ne doména: `gold` = akcent
 * nejvyššího pásma, `tertiary` (starší alias `health_green`) = akcent nejnižšího.
 */
export interface DesignTokens {
  /** Provenience tokenů (DESIGN.md / Brand Kit / neutrální theme). Metadata, neinjektuje se. */
  source?: string;
  primary?: string;
  accent?: string;
  gold?: string;
  /** Akcent nejnižšího pásma. Neutrální název; `health_green` je starší alias. */
  tertiary?: string;
  /** Starší alias pro `tertiary` (specy před brand rourou). */
  health_green?: string;
  bg?: string;
  surface?: string;
  text?: string;
  text_soft?: string;
  radius?: string;
  /**
   * Informational — záznam brandových fontů z DESIGN.md. Šablona dnes renderuje
   * Montserrat + Open Sans (next/font); designTokenStyle() tyto klíče NEČTE.
   * Deklarované, ne drátované — dynamické načítání fontu je mimo aktuální builder.
   */
  font_head?: string;
  font_body?: string;
}

/* ---------- v0.5 additions ---------- */

export interface PilotMode {
  enabled: boolean;
  redirect_all_emails_to?: string;
  note?: string;
}

export interface MainResult {
  type: string;
  label: string;
  unit: string;
  meaning: Record<string, string>;
}

/**
 * Odkud se bere teplota leada (hot/warm/cold).
 *
 * `score` je historický default a drží zpětnou kompatibilitu se staršími specy.
 * Pozor: skóre měří MEZERU („jak na tom jste"), ne nákupní záměr — kdo dodržuje
 * všechny doporučené postupy, je spokojený, a spokojený člověk nekupuje. Nové
 * funnely proto kvalifikují z bloku kvalifikace (`urgency_budget`).
 */
export type TemperatureSource =
  /** Práh na skóre kvízu (hot_min / warm_min). Historický default. */
  | "score"
  /** Z odpovědi nesoucí signál rozpočtu: `question` + `hot[]` / `warm[]`. */
  | "urgency_budget"
  /** Počet kritických odpovědí u `question` proti prahům. */
  | "critical_areas";
// Pozn.: `number_urgency` (práh na hlavním čísle kalkulačky) ZÁMĚRNĚ chybí —
// runtime má k dispozici jen skóre 0–100, ne vypočtené číslo magnetu. Dokud
// pro to nebude pipeline, slibovat ho v kontraktu = spec by lhal a spadlo by
// to tiše (hot_min: 500 proti skóre ≤ 100 → všichni cold, bez varování).

export interface TemperatureRules {
  // Jen TemperatureSource (ne `| string`): `X | string` v TS zkolabuje na `string`
  // a union pak nekontroluje nic. Neznámá hodnota se stejně chytí runtime
  // fallbackem s warn v temperature().
  source: TemperatureSource;
  /** Práh pro `score`; u `critical_areas` = počet kritických oblastí. */
  hot_min: number;
  warm_min: number;
  /** `urgency_budget` / `critical_areas`: id otázky nesoucí signál. */
  question?: string;
  /** `urgency_budget`: přesné hodnoty odpovědí → hot / warm. Zbytek = cold. */
  hot?: string[];
  warm?: string[];
  /** `critical_areas`: hodnoty považované za kritické. */
  critical?: string[];
  note?: string;
}

export interface MechanismItem {
  title: string;
  text: string;
}

/**
 * Sekce „Jak to funguje" na prodejní stránce — jak produkt řeší konkrétní
 * bolest. Data jsou VŽDY per funnel (viz G17): `by_pain` mapuje odpověď na
 * bolestivou otázku na blok, `default` se použije, když se nic netrefí.
 * Šablona nesmí obsahovat žádný konkrétní produkt — bez tohoto bloku se
 * sekce poskládá nouzově z offer.usp.
 */
export interface Mechanisms {
  /** Klíč = přesná hodnota odpovědi z options bolestivé otázky. */
  by_pain?: Record<string, MechanismItem>;
  default?: MechanismItem[];
}

export type Temperature = "hot" | "warm" | "cold";

export interface CtaRoute {
  cta: string;
  type: string;
  variant?: string;
}

/**
 * Společný tvar legacy magnet_structure metadata a bloků dynamického
 * magnet_middle. Builder 1.0 skládá dynamicky pouze magnet_middle; pořadí celé
 * stránky drží pevná šablona. `render` říká, jak se blok středu vykreslí.
 *
 * Starší specy (bez `render`/`persona_field`) se mapují podle `key` přes
 * MAGNET_LEGACY v lib/ui.ts — proto zůstávají funkční.
 */
export type MagnetRender =
  | "main_result" // deterministický výsledek (gauge / plán / číslo)
  | "text" // LLM: nadpis + odstavce
  | "cards" // LLM: nadpis + 2–3 karty (nadpis karty + text) — flexibilní STŘED
  | "steps" // LLM: nadpis + očíslované kroky
  | "openloop" // LLM: teaser + odkaz na /online/ (open loop)
  | "segment" // deterministický segment box ze spec.segments
  | "reviews" // deterministický blok recenzí ze spec.reviews (social proof)
  | "cta"; // deterministický CTA blok

export interface MagnetBlock {
  block: number;
  key: string;
  type: string;
  title: string;
  /** Eyebrow/podnadpis nad blokem (flexibilní STŘED, fáze 3). */
  subtitle?: string;
  desc?: string;
  /** Jak vykreslit. Chybí u starších speců → mapuje se z `key`. */
  render?: MagnetRender;
  /** LLM bloky: persona pole, kam se text uloží (např. "magnet_rozbor"). */
  persona_field?: string;
  /** LLM bloky: co má LLM vygenerovat (jde do promptu personalizace). */
  instruction?: string;
}

export interface EmailStep {
  id: string;
  day: number;
  goal: string;
}

export interface EmailBranches {
  delivery?: string;
  envelope?: string;
  lint?: string[];
  hot: EmailStep[];
  warm: EmailStep[];
  cold: EmailStep[];
}

/** DEPRECATED — staré generické tagy. Ponecháno jen ať starší specy parsují. */
export interface StateTags {
  pending?: string;
  processing?: string;
  ready?: string;
  seen_offer?: string;
  sequence_cancelled?: string;
}

export interface Ops {
  hot_lead?: string;
  reply_to?: string | null;
  /**
   * Prefix VŠECH tagů funnelu (typicky „aiq - [název]"). Z něj se odvozují stavy
   * `[prefix] - active/processing/completed/converted/hot lead` (jednotný „ - "
   * oddělovač, jako u polí). Namespace per funnel, aby se tagy nemíchaly, když má
   * klient víc AIQ funnelů. Chybí-li, odvodí se z `magnet_tag` nebo z názvu magnetu.
   */
  tag_prefix?: string;
  // Legacy (staré specy) — nový kód je ignoruje, jen musí parsovat:
  kill_switch_tag?: string;
  purchase_tag?: string;
  magnet_tag?: string;
  state_tags?: StateTags;
}

/** Odvozené tagy funnelu (namespacnuté prefixem). */
export interface FunnelTags {
  /** origin — přišel z magnetu (permanentní). */
  base: string;
  /** v sekvenci, e-maily jedou. */
  active: string;
  /** sekvence dojela do konce (guard). */
  completed: string;
  /** klient přidal → dosáhl cíle → guard stáhne zbytek. */
  converted: string;
  /** horký lead k obvolání. */
  hot: string;
  /** přechodný lease proti 2× personalizaci. */
  processing: string;
}

/** Identita klienta pro user-facing texty (weby, e-maily, zásady OÚ). */
export interface Brand {
  /** Zobrazované jméno klienta (patičky, oslovení „tým X", zásady OÚ). */
  name: string;
  /** Hlavní nákupní/kontaktní URL — cíl CTA tlačítek na prodejní stránce. */
  cta_url: string;
  /** Kontaktní e-mail správce osobních údajů (stránka /zasady). */
  privacy_email: string;
  /** Identifikace odesílatele v patičce e-mailů (název + adresa). */
  email_footer?: string;
}

/** Field ID odvozených polí — doplní builder do funnel-spec.json při setupu. */
export interface DerivedFieldIds {
  comment?: string;
  score: string | null;
  segment: string | null;
}

export interface FunnelSpec {
  funnel_slug: string;
  product: string;
  client: string;
  ghl_location_id: string;
  variant: string;
  lead_magnet_name: string;
  mode: string;
  contact_position: string;
  questions: Question[];
  consent_field_id: string;
  /** Doba uchování osobních údajů v měsících (zásady OÚ). Default 24. */
  retention_months?: number;
  /**
   * Text souhlasu se zpracováním odpovědí — POVINNĚ per funnel, protože musí
   * odpovídat tomu, na co se kvíz skutečně ptá. Zmínku o citlivých údajích
   * (zdraví, děti, finance) piš JEN když se na ně kvíz opravdu ptá; jinak je to
   * nepravdivé a zbytečně odrazuje. Bez tohoto klíče se použije neutrální
   * výchozí text.
   */
  consent_text?: string;
  scoring_bands: ScoringBand[];
  segments: Segment[];
  personalization_vars: string[];
  offer: Offer;
  design_tokens: DesignTokens;
  /* v0.5 */
  spec_version: string;
  personalization_mode: string;
  pilot_mode: PilotMode;
  main_result: MainResult;
  temperature_rules: TemperatureRules;
  cta_routes: Record<string, CtaRoute>;
  urgency_source: string;
  magnet_structure: MagnetBlock[];
  /**
   * FLEXIBILNÍ STŘED magnetu (fáze 3) — bloky, které strategie navrhne AI per
   * funnel (text/cards/steps). Runtime je vykreslí ve smyčce mezi pevnou kostrou
   * (fáze 1/2 nahoře, fáze 4/5 dole). Chybí-li → runtime spadne na dnešní pevný
   * střed (rozbor/žebříček/akce), takže starší funnely fungují beze změny.
   */
  magnet_middle?: MagnetBlock[];
  persona_fields: string[];
  email_branches: EmailBranches;
  ops: Ops;
  brand?: Brand;
  derived_field_ids?: DerivedFieldIds;
  /** Volitelné — bez něj se sekce „Jak to funguje" skládá z offer.usp. */
  mechanisms?: Mechanisms;
  /** Volitelné — PRODUKTOVÉ recenze pro render `reviews` na magnetu. Skryje se prázdné. */
  reviews?: Review[];
  /**
   * Volitelné — recenze FUNNELU (hodnotí test/kvíz, ne produkt) na landingu hned
   * po hero. Budují důvěru VYPLNIT test. Odlišné od `reviews` (produktové na magnetu).
   */
  funnel_reviews?: Review[];
  /** F2 — dílčí skóre oblastí (rozpad hlavního skóre pro „víc oblastí k analýze"). */
  score_areas?: ScoreArea[];
  /** F3 — benchmark „šok z čísla" (předpočítané hodnoty per odpověď). */
  benchmark?: Benchmark;
  /** Fotky do výsledku magnetu (silné vizuály). Chybí-li klíč → slot se přeskočí. */
  magnet_images?: MagnetImages;
  /** Deterministický nadpis (předpřipravené kombinace) — H1 se ukáže HNED, bez AI. */
  headline?: HeadlineSpec;
  /** Plné Product DNA (bohatý kontext do promptu — benefity, parametry, námitky,
   *  cílovka, úhel). Strategie ho plní z productDNA.md; AI z něj čerpá hloubku. */
  product_dna?: string;
}

/**
 * Deterministický H1 magnetu: předpřipravené varianty nadpisu vybírané odpovědí
 * klienta (žádné AI, zobrazí se okamžitě). Do renderu se prependuje oslovení.
 */
export interface HeadlineSpec {
  /** qid, jehož odpovědí se vybírá varianta (typicky otázka na cíl/přání). */
  by_question: string;
  /** hodnota odpovědi → nadpis (BEZ oslovení, malým písmenem — navazuje na „Jméno, "). */
  variants: Record<string, string>;
  /** fallback, když se žádná varianta netrefí. */
  default: string;
}

/** Vizuály výsledkové stránky (cesty pod /public). Vše volitelné (graceful skip). */
export interface MagnetImages {
  /** Full-width vizuální pás (typicky hned pod HERO). */
  band?: string;
  /** Benchmark — before/after záběr. */
  beforeafter?: string;
  /** Product reveal u „předpisu" (čistý produktový/lifestyle záběr). */
  product?: string;
  /** Volitelný detail. */
  detail?: string;
}

/**
 * Dílčí skóre oblasti (F2) — 3–4 oblasti, každá mapuje 1–3 skórované otázky.
 * `area% = získané body / max možných bodů × 100`. Agregát 0–100 se nemění;
 * jen ho rozpadne na čitelné oblasti. `verdicts` = kvalitativní label per pásmo
 * (nízká/střední/vysoká), aby se u 0/50/100 (yes/no) neukazovala pseudo-přesnost.
 */
export interface ScoreArea {
  key: string;
  label: string;
  questions: string[];
  /** Volitelné verdikty { high | mid | low } — label místo pseudo-%. */
  verdicts?: { high?: string; mid?: string; low?: string };
}

/**
 * Benchmark „šok z čísla" (F3) — předpočítané hodnoty per odpověď na jednu otázku.
 * `counts` = čistá aritmetika (lahve/rok), zobrazí se bez disclaimeru; `money` =
 * odhad, POVINNĚ s `assumption` (render ho ukáže drobně „orientačně, při X").
 * Validace patří do builder validate skriptu, ne do offer whitelistu.
 */
export interface BenchmarkRow {
  headline: string;
  sub?: string;
  /** Peněžní vyčíslení („≈ X Kč ročně") — deterministické,
   *  s cenovým předpokladem v `assumption`. Zobrazí se výrazně u headline. */
  money?: string;
  /** Peněžní odhad → povinný předpoklad (jinak „vymyšlené číslo"). */
  assumption?: string;
}
export interface Benchmark {
  /** id otázky, jejíž odpověď určuje řádek. */
  question: string;
  /** klíč = přesná hodnota odpovědi → zobrazované hodnoty. */
  rows: Record<string, BenchmarkRow>;
  /** volitelný nadpis „S řešením" sloupce (třída řešení, ne produkt). */
  solution_label?: string;
  /** text sloupce „Dnes" (současný stav bez řešení). Bez něj generický fallback. */
  today_text?: string;
  /** text sloupce „S řešením" (třída řešení, NE jméno produktu). Bez něj generický fallback. */
  solution_text?: string;
}

export const spec = specJson as unknown as FunnelSpec;

// Normalizace: scoring_bands seřaď nejvyšší-první. band()/ctaOffer()/categoryColor()
// na tom pořadí stojí (bands[0] = top). Kdyby strategie zapsala pásma vzestupně,
// bez tohohle by nejvyšší skóre spadlo do nejnižší kategorie (zelená, cold CTA).
if (Array.isArray(spec.scoring_bands)) {
  spec.scoring_bands.sort((a, b) => b.min - a.min);
}

/** Resolved brand — builder validace vyžaduje spec.brand, fallbacky jen jistí. */
export const BRAND: Brand = {
  name: spec.brand?.name ?? spec.client,
  cta_url: spec.brand?.cta_url ?? "",
  privacy_email: spec.brand?.privacy_email ?? "",
  email_footer: spec.brand?.email_footer ?? spec.brand?.name ?? spec.client,
};

/**
 * Prefix VŠECH tagů funnelu (typicky `ops.tag_prefix` = „aiq - [název]", pomlčka
 * po „aiq" už je v prefixu). Fallback: starší `magnet_tag`, jinak odvození z názvu
 * magnetu. Namespace per funnel → tagy se nemíchají, když má klient víc AIQ funnelů.
 * Konvence stavů: prefix + „ - <stav>" (jednotný „ - " oddělovač, jako u polí níže).
 * Výsledek: `aiq - [název] - active` / `- hot lead` / … — NE dvojitá pomlčka.
 */
const TAG_PREFIX: string = (
  spec.ops?.tag_prefix ||
  spec.ops?.magnet_tag ||
  `AIQ ${spec.lead_magnet_name}`
)
  .trim()
  .slice(0, 60);

/**
 * Odvozené tagy funnelu — všechny namespacnuté prefixem, jednotný „ - " oddělovač.
 * ⚠️ LOWERCASE: GHL tagy na svém konci lowercasuje (GET vrací „aiq - … - active"),
 * takže je držíme lowercase i tady, aby case-sensitive `includes`/`===` porovnání
 * matchlo (guard-core i lease v run-personalization). Pole níže zůstávají v původním
 * case (custom field names GHL case zachovává).
 */
const TAG_PREFIX_LC = TAG_PREFIX.toLowerCase();
export const TAGS: FunnelTags = {
  base: TAG_PREFIX_LC,
  active: `${TAG_PREFIX_LC} - active`,
  completed: `${TAG_PREFIX_LC} - completed`,
  converted: `${TAG_PREFIX_LC} - converted`,
  hot: `${TAG_PREFIX_LC} - hot lead`,
  processing: `${TAG_PREFIX_LC} - processing`,
};

/** Namespacnutá jména custom polí stavu sekvence (per funnel). Sdílí ensure-fields.mjs. */
export const SCHEDULED_IDS_FIELD_NAME = `${TAG_PREFIX} - Scheduled IDs`;
export const SEQUENCE_END_FIELD_NAME = `${TAG_PREFIX} - Sequence End`;

/**
 * Neutrální default paleta. Použije se pro každý klíč, který spec.design_tokens
 * nedodá — tím starší funnely (bez kompletní palety) i funnely bez DESIGN.md
 * běží beze změny vzhledu. Barvy nejsou CliqSales paleta, jsou to neutrální
 * prémiové odstíny.
 */
const TOKEN_FALLBACK = {
  primary: "#1b2a4a",
  accent: "#006799",
  gold: "#c5a55a",
  tertiary: "#4a7c59",
  bg: "#ffffff",
  surface: "#f5f5f5",
  text: "#333333",
  text_soft: "#666666",
  radius: "10px",
} as const;

export type TokenKey = keyof typeof TOKEN_FALLBACK;

/**
 * Hodnota design tokenu — spec-first, s fallbackem na neutrální default.
 * Třetí (nejnižší) pásmo čte `tertiary` i starší alias `health_green`, takže
 * brand roura i staré specy fungují.
 */
export function token(key: TokenKey): string {
  const t = (spec.design_tokens ?? {}) as Record<string, string | undefined>;
  if (key === "tertiary") return t.tertiary || t.health_green || TOKEN_FALLBACK.tertiary;
  return t[key] || TOKEN_FALLBACK[key];
}

/**
 * Inline `:root` proměnné na `<html>` (layout.tsx). Inline style přebíjí :root
 * default v globals.css deterministicky (bez řešení pořadí stylů), takže barvy
 * skutečně tečou ze specu — dřív byly natvrdo. Fonty řeší next/font, jejich
 * proměnné sem nepatří. CSS var `--health-green` drží jméno (globals.css ho
 * používá napříč), plní se ale z role „tertiary".
 */
export function designTokenStyle(): Record<string, string> {
  return {
    "--primary": token("primary"),
    "--accent": token("accent"),
    "--gold": token("gold"),
    "--health-green": token("tertiary"),
    "--bg": token("bg"),
    "--surface": token("surface"),
    "--text": token("text"),
    "--text-soft": token("text_soft"),
    "--radius": token("radius"),
  };
}

// Derived field IDs — builder je doplní do funnel-spec.json (deploy krok 3b).
// Prázdné ID ⇒ hodnota se do GHL nezapíše a dopočítá se z odpovědí.
export const SCORE_FIELD_ID = spec.derived_field_ids?.score ?? "";
export const SEGMENT_FIELD_ID = spec.derived_field_ids?.segment ?? "";

// Field ID otázek čtených zpět pro personalizaci (q7 = top_pain).
export const Q7_FIELD_ID = getQuestion("q7")?.field_id ?? "";

export const ROUTE_QUESTION_ID =
  spec.questions.find((q) =>
    (q.options ?? []).some((option) => Boolean(spec.cta_routes[option]))
  )?.id ?? "q13";

export const ROUTE_FIELD_ID = getQuestion(ROUTE_QUESTION_ID)?.field_id ?? "";

/** Public base URL of the deployed funnel (for links in e-mails). */
export const BASE_URL = process.env.AIQ_BASE_URL || "";
if (!BASE_URL) {
  console.warn(
    "[spec] AIQ_BASE_URL není nastavené — odkazy v e-mailech nebudou fungovat."
  );
}

export function getQuestion(id: string): Question | undefined {
  return spec.questions.find((q) => q.id === id);
}

/** CTA route for the configured route answer, with `_default` fallback. */
export function ctaRoute(routeAnswer: string | undefined): CtaRoute {
  if (routeAnswer && spec.cta_routes[routeAnswer]) return spec.cta_routes[routeAnswer];
  return spec.cta_routes["_default"] ?? { cta: "Prohlédnout doporučené řešení", type: "soft" };
}
