import { spec, BRAND, ctaRoute, ROUTE_QUESTION_ID } from "../../../lib/spec";
import { getContactBundle } from "../../../lib/server";
import type { ContactBundle } from "../../../lib/server";
import { buildVars } from "../../../lib/funnel";
import { vocative } from "../../../lib/vocative";
import { withPersonaFallback } from "../../../lib/fallback";
import { categoryColor, mechanismForPains, mainResultView } from "../../../lib/ui";
import SalesCarousel from "../../../components/SalesCarousel";
import AnimatedStat from "../../../components/AnimatedStat";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export const metadata = {
  title: `Doporučení na míru | ${BRAND.name}`,
  robots: { index: false, follow: false },
};

/**
 * Volitelná obohacovací vrstva (21bl anatomie). Bloky, které nemají data
 * v dnešním funnel-specu, se renderují JEN když strategie doplní `spec.sales.*`.
 * Definováno lokálně (NE v spec.ts typech) → builduje dnes, bohatne, až spec
 * doroste. Čte se přes bezpečný cast s `?.` guardem — chybí-li klíč, blok se
 * nevyrenderuje (žádný crash, žádná díra v toku).
 */
interface SalesStat {
  value: string;
  label: string;
}
interface SalesQuote {
  quote: string;
  author: string;
  meta?: string;
  rating?: number;
  highlight?: string;
}
interface SalesStep {
  title: string;
  text: string;
}
interface SalesDay {
  title?: string;
  before: string;
  after: string;
}
interface SalesBonus {
  title: string;
  desc?: string;
  value?: string;
  img?: string;
}
interface SalesComponent {
  img?: string;
  label?: string;
  title: string;
  sub?: string;
  desc: string;
  icon?: string;
}
interface SalesSlide {
  img: string;
  title: string;
  desc?: string;
}
interface SalesForWhom {
  title?: string;
  yes: string[];
  no?: string[];
}
interface SalesComparison {
  columns: string[];
  rows: { label: string; cells: string[] }[];
}
interface SalesTimeline {
  title?: string;
  m1: string;
  m6: string;
  m12: string;
}
interface SalesGenesis {
  title: string;
  body: string;
  image?: string;
}
interface SalesFaq {
  q: string;
  a: string;
}
interface SalesExtras {
  promo?: string;
  social_proof?: { rating?: number; count?: number; text?: string };
  authority_stats?: SalesStat[];
  testimonial?: SalesQuote;
  steps?: SalesStep[];
  day?: SalesDay;
  bonuses?: SalesBonus[];
  carousel?: SalesSlide[];
  proof_numbers?: SalesStat[];
  proof_intro?: string;
  case_study?: SalesQuote;
  for_whom?: SalesForWhom;
  comparison?: SalesComparison;
  timeline?: SalesTimeline;
  genesis?: SalesGenesis;
  urgency?: string;
  stack2?: boolean;
  guarantee_aha?: string[];
  guarantee_aha_lead?: string;
  price?: { orig?: string; now?: string; save?: string; note?: string };
  stack_items?: string[];
  components?: SalesComponent[];
  components_title?: string;
  offer_image?: string;
  closing_line?: string;
  faq?: SalesFaq[];
}

const salesExtras = (spec as unknown as { sales?: SalesExtras }).sales ?? {};

const offer = spec.offer;
const uspItems = offer.usp
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

// Hlavní nákupní/kontaktní CTA — ze spec.brand.cta_url (builder validuje).
const CTA_URL = BRAND.cta_url || "#nabidka";

/* Product carousel — self-hostované /img/*. Čte z sales.carousel (titulky/popisy),
   ale obrázek VŽDY sanitizuje na /img/ cestu: pokud spec dodá /img/ path, použije
   se; cokoli jiného (cross-origin, prázdné) se nahradí bezpečným fallbackem podle
   pořadí. Chybí-li carousel úplně, jede plný hardcoded fallback → obrázky jsou
   vždy vidět a nikdy nevede na cizí doménu. */
const CAROUSEL_FALLBACK_IMGS = [
  "/img/result-product.jpg",
  "/img/result-detail.jpg",
  "/img/process.jpg",
  "/img/mockup.png",
  "/img/result-beforeafter.jpg",
];
const CAROUSEL_FALLBACK_COPY = [
  { title: "Řešení u Vás doma", desc: "Diskrétní instalace, každodenní klid." },
  { title: "Detail zblízka", desc: "Kvalita, kterou poznáte na první pohled." },
  { title: "Jak to funguje", desc: "Připraveno lidmi, kteří produktu rozumí." },
  { title: "Výsledek na míru", desc: "Sestaveno podle Vašich odpovědí." },
  { title: "Předtím a potom", desc: "Rozdíl, který ucítíte hned." },
];
const safeImg = (img: string | undefined, i: number) =>
  img && img.startsWith("/img/")
    ? img
    : CAROUSEL_FALLBACK_IMGS[i % CAROUSEL_FALLBACK_IMGS.length];

/* Typografická hravost: klíčové slovo v nadpisu obalené `**…**` → zvýrazněné
   <em className="sp-hl"> (barva/váha z CSS). Bez markeru vrací čistý text. */
function withHl(text: string) {
  return text
    .split(/\*\*(.+?)\*\*/g)
    .map((part, i) => (i % 2 === 1 ? <em key={i} className="sp-hl">{part}</em> : part));
}

function Stars({ rating = 5 }: { rating?: number }) {
  const full = Math.max(0, Math.min(5, Math.round(rating)));
  return (
    <span className="sp-stars" aria-label={`${full} z 5`}>
      {"★★★★★".slice(0, full)}
    </span>
  );
}

// Inline ikony (Lucide-styl) — prémiová vizuální kotva u benefitů, kroků,
// bonusů, nabídky a garance. Multi-subpath dělený " M".
type IcoName =
  | "check" | "shield" | "droplet" | "display" | "gift" | "truck"
  | "tool" | "clock" | "spark" | "leaf" | "users" | "star" | "flask" | "home";
const ICO_PATHS: Record<IcoName, string> = {
  check: "M20 6 9 17l-5-5",
  shield: "M12 3l7 3v5c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6z M9.5 12l1.8 1.8 3.7-3.7",
  droplet: "M12 2.7c3.4 4 6 7 6 10.3a6 6 0 0 1-12 0c0-3.3 2.6-6.3 6-10.3z",
  display: "M4 5h16v10H4z M9 19h6 M12 15v4",
  gift: "M20 12v9H4v-9 M2 7h20v5H2z M12 7v14 M12 7S9 2 6.5 3.5 8 7 12 7z M12 7s3-5 5.5-3.5S16 7 12 7z",
  truck: "M3 6h11v9H3z M14 9h4l3 3v3h-7 M7 18a1.6 1.6 0 1 0 0-3.2A1.6 1.6 0 0 0 7 18z M17 18a1.6 1.6 0 1 0 0-3.2A1.6 1.6 0 0 0 17 18z",
  tool: "M21 4l-4.5 4.5 M15 7l2 2-8 8-3 1 1-3z M4 20l3-1",
  clock: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M12 7v5l3 2",
  spark: "M12 3l1.7 5L19 9l-5 1.6L12 16l-1.7-5.4L5 9l5.3-1z",
  leaf: "M4 20c8 0 16-6 16-16 0 0-12-2-14 8-1 5 0 8 0 8z M4 20c3-6 7-9 12-11",
  users: "M17 20v-1a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v1 M10 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z M20 20v-1a4 4 0 0 0-3-3.8",
  star: "M12 3l2.5 5.6L20 9l-4 4 1 6-5-3-5 3 1-6-4-4 5.5-.4z",
  flask: "M9 3h6 M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3 M7.5 15h9",
  home: "M3 11l9-7 9 7 M5 10v10h14V10 M10 20v-6h4v6",
};
function Ico({ name }: { name: IcoName }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {ICO_PATHS[name].split(" M").map((d, i) => (
        <path key={i} d={i === 0 ? d : "M" + d} />
      ))}
    </svg>
  );
}
// Produktové obrázky — SPEC-DRIVEN s generickými /img/ fallbacky (v template ŽÁDNÝ funnel obsah).
// Hero obrázek nabídky ze spec.sales.offer_image; jinak generický carousel snímek 01.
const OFFER_IMG =
  salesExtras.offer_image && salesExtras.offer_image.startsWith("/img/")
    ? salesExtras.offer_image
    : "/img/sp-c1.jpg";
// Neutrální ikonové defaulty (per-funnel ikony komponent tečou ze specu přes `icon`).
const BONUS_ICONS: IcoName[] = ["gift", "spark", "star"];
const STEP_ICONS: IcoName[] = ["check", "tool", "spark"];
const MIRROR_ICONS: IcoName[] = ["spark", "clock", "users"];
// String ze specu → validní IcoName (fallback „check").
const icoName = (s?: string): IcoName => (s && s in ICO_PATHS ? (s as IcoName) : "check");

// Sociální důkaz: vždy zvýrazni nejklíčovější frázi citátu (highlight), jinak
// zvýrazni první větu (obvykle pointa). Font řeší CSS (větší, výraznější).
function EmphQuote({ text, highlight }: { text: string; highlight?: string }) {
  if (highlight && text.includes(highlight)) {
    const i = text.indexOf(highlight);
    return (
      <>
        {text.slice(0, i)}
        <strong className="sp-key">{highlight}</strong>
        {text.slice(i + highlight.length)}
      </>
    );
  }
  const m = text.match(/^(.*?[.!?])(\s+)([\s\S]*)$/);
  if (m) {
    return (
      <>
        <strong className="sp-key">{m[1]}</strong>
        {m[2]}
        {m[3]}
      </>
    );
  }
  return <>{text}</>;
}

export default async function SalesPage({
  params,
}: {
  params: Promise<{ contactId: string }>;
}) {
  const { contactId } = await params;

  // Čistá URL (bez tokenu) — contactId je capability klíč. Neexistující kontakt
  // = generická verze (obsah /doporuceni inline).
  let bundle: ContactBundle | null = null;
  if (contactId) {
    try {
      bundle = await getContactBundle(contactId);
    } catch {
      bundle = null;
    }
  }

  // Sjednocená stránka: s platným kontaktem = personalizovaná; bez kontaktu
  // (neexistující / expirované ID) = TÁŽ stránka v generickém režimu — žádný
  // samostatný GenericSales. Sekce závislé na odpovědích se níže skryjí.
  const personalized = !!bundle;

  const vars = bundle?.vars ?? buildVars({ firstName: "", answers: {} });
  const temperature = bundle?.temperature ?? "warm";
  const persona = withPersonaFallback(bundle?.persona ?? {});
  const color = categoryColor(vars.category_key);

  const voc = vocative(bundle?.firstName ?? "");
  const mrView = mainResultView(vars.score, bundle?.answers ?? {});
  const greeting = voc ?? "Dobrý den";

  const routeRaw = bundle?.answers[ROUTE_QUESTION_ID];
  const routeAnswer = Array.isArray(routeRaw) ? routeRaw[0] ?? "" : routeRaw ?? "";
  const route = ctaRoute(routeAnswer);

  const scoreLabel =
    mrView.kind === "score"
      ? `${mrView.label}: ${vars.score}${mrView.unit}`
      : `${mrView.label}: ${mrView.display}`;

  // Bez schovávání sekcí podle stavu leadu — vždy plná
  // stránka. Teplota leadu smí ladit jen TÓN copy, ne skrývat celé sekce.
  const show = {
    benefits: true,
    mechanism: true,
    segment: true,
    offerStack: true,
    objections: true,
  };

  const problems = [
    { q: persona.problem1_question, i: persona.problem1_impact },
    { q: persona.problem2_question, i: persona.problem2_impact },
    { q: persona.problem3_question, i: persona.problem3_impact },
  ].filter((p) => p.q && p.i);

  const benefits = [
    { t: persona.benefit_1_title, d: persona.benefit_1_description },
    { t: persona.benefit_2_title, d: persona.benefit_2_description },
    { t: persona.benefit_3_title, d: persona.benefit_3_description },
  ].filter((b) => b.t && b.d);

  const heroBullets = benefits.map((b) => b.t).slice(0, 3);

  const objections = [
    { t: persona.objection_1_title, r: persona.objection_1_response },
    { t: persona.objection_2_title, r: persona.objection_2_response },
  ].filter((o) => o.t && o.r);

  const q7Raw = bundle?.answers["q7"];
  const pains = Array.isArray(q7Raw) ? q7Raw : q7Raw ? [q7Raw] : [];
  const mechanism = mechanismForPains(pains);

  const sx = salesExtras;

  // Value stack = reálné „co získáte" (spec.stack_items), fallback na USP.
  const stackItems =
    sx.stack_items && sx.stack_items.length > 0 ? sx.stack_items : uspItems;

  // Personalizované shrnutí do close panelu (proč to potřebuje) — z jeho dat.
  const closeSummary = personalized
    ? (problems[0]?.q ? `${problems[0].q} ` : "") +
      `Vaše odpovědi mluví jasně a ${offer.product} řeší přesně to, co z kvízu vyplynulo. ` +
      `Zbývá jediné rozhodnutí.`
    : `S ${offer.product} máte řešení i poradenství od lidí, kteří produktu rozumí. ` +
      `Zbývá jediné rozhodnutí.`;

  // Hero: personalizovaný (jméno + AI headline) vs generický (produkt + benefit).
  const heroHeadline = personalized
    ? `${greeting}, ${persona.main_headline}`
    : `${offer.product}: řešení na **míru** Vaší situaci`;
  const heroSub = personalized
    ? persona.sub_headline
    : `Podívejte se, jak Vám ${offer.product} pomůže. V klidu a bez tlaku.`;

  // Carousel — data ze specu s /img/ sanitizací + fallback (viz nahoře).
  const carousel =
    sx.carousel && sx.carousel.length > 0
      ? sx.carousel.map((c, i) => ({
          img: safeImg(c.img, i),
          title: c.title,
          desc: c.desc,
        }))
      : CAROUSEL_FALLBACK_IMGS.map((img, i) => ({
          img,
          title: CAROUSEL_FALLBACK_COPY[i].title,
          desc: CAROUSEL_FALLBACK_COPY[i].desc,
        }));

  return (
    <main className="has-sticky-cta">
      {/* ---- Promo lišta (volitelná) ---- */}
      {sx.promo && <div className="sp-promo">{sx.promo}</div>}

      {/* ---- Personalizovaný ribbon (jen s platným kontaktem) ---- */}
      {personalized && (
        <div className="sp-ribbon">
          <span className="sp-ribbon__lead">
            <Ico name="spark" />
            Sestaveno pro Vás z Vašich odpovědí
          </span>
          <span className="sp-ribbon__chip">{vars.score_category}</span>
          {vars.top_pain && <span className="sp-ribbon__chip">{vars.top_pain}</span>}
        </div>
      )}

      {/* ---- 1) HERO — hero-media pattern (lifestyle foto + overlay + plovoucí produkt) ---- */}
      <section className="hero-media sp-hero-photo">
        <div className="hero-overlay" aria-hidden="true" />
        <div className="container hero-inner sp-hero-center">
          <div className="hero-copy">
            <span className="eyebrow">Doporučení na míru · {BRAND.name}</span>

            {personalized && (
              <span className="sp-hero-badge">
                <strong>{scoreLabel}</strong>
                <span aria-hidden="true">·</span>
                <span>{vars.score_category}</span>
              </span>
            )}

            <h1 className="sp-display">{withHl(heroHeadline)}</h1>
            <p className="hero-sub">{heroSub}</p>

            {heroBullets.length > 0 && (
              <ul className="sp-hero-bullets">
                {heroBullets.map((b, i) => (
                  <li key={i}>
                    <span className="sp-check">✓</span>
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
            )}

            <div className="hero-cta">
              <a
                href={CTA_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-gold"
              >
                {route.cta}
              </a>
              {sx.social_proof && (
                <div className="sp-hero-social">
                  <Stars rating={sx.social_proof.rating ?? 5} />
                  <span className="sp-hero-social__rating">
                    {(sx.social_proof.rating ?? 5).toString().replace(".", ",")} z 5
                  </span>
                  {sx.social_proof.text && (
                    <span className="sp-hero-social__count">· {sx.social_proof.text}</span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ---- 2) Autoritní pás — 3 power čísla jako přesahující stats band (jako landing) ---- */}
      {sx.authority_stats && sx.authority_stats.length > 0 && (
        <div className="sp-stats-band">
          <div className="container">
            <div className="hero-stats">
              {sx.authority_stats.slice(0, 3).map((s, i) => (
                <div className="hero-stat" key={i}>
                  <AnimatedStat value={s.value} />
                  <span className="lbl">{s.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ---- 3) Zrcadlo „řekli jste" + diagnóza + předpis (jen personalizované) ---- */}
      {personalized && problems.length > 0 && (
        <section className="section sp-tint" id="diagnoza">
          <div className="container">
            <span className="eyebrow">Z Vašich odpovědí</span>
            <h2>Řekli jste nám víc, než si myslíte</h2>
            <div className="sp-grid sp-grid--3">
              {problems.map((p, idx) => (
                <div
                  className="card sp-mirror"
                  key={idx}
                  style={{ borderTopColor: color }}
                >
                  <span className="sp-ico sp-ico--gold sp-mirror__ic">
                    <Ico name={MIRROR_ICONS[idx % MIRROR_ICONS.length]} />
                  </span>
                  <h3>{p.q}</h3>
                  <p className="muted">{p.i}</p>
                </div>
              ))}
            </div>

            <div className="sp-diagnosis" style={{ borderLeftColor: color }}>
              <div className="sp-diagnosis__score" style={{ color }}>
                {scoreLabel}
              </div>
              <p className="muted">
                {vars.top_pain
                  ? `Nejvíc Vás teď trápí ${vars.top_pain}. `
                  : ""}
                Níže Vám ukážeme přesně, jak to {offer.product} řeší — krok po
                kroku, bez tlaku.
              </p>
              <a href="#nabidka" className="sp-textlink">
                Chci to vyřešit →
              </a>
            </div>
          </div>
        </section>
      )}

      {/* ---- 4) Social proof #2 — reference jako produktový foto-band ---- */}
      {sx.testimonial?.quote && (
        <section className="sp-band sp-band--lp2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="sp-band__bg" src="/img/sp-lifep2.jpg" alt="" loading="lazy" />
          <div className="container">
            <blockquote>
              „<EmphQuote text={sx.testimonial.quote} highlight={sx.testimonial.highlight} />“
              <span className="quote-attribution">
                {sx.testimonial.author}
                {sx.testimonial.meta ? ` · ${sx.testimonial.meta}` : ""}
              </span>
            </blockquote>
          </div>
        </section>
      )}

      {/* ---- 5) Produkt + unikátní mechanismus — split kroky + foto (jako landing) ---- */}
      {show.mechanism && mechanism.length > 0 && (
        <section className="section">
          <div className="container split-grid">
            <div>
              <span className="eyebrow">Jak to funguje</span>
              <h2>
                {vars.top_pain
                  ? `Jak ${offer.product} řeší přesně to, co Vás trápí`
                  : `Jak ${offer.product} pracuje`}
              </h2>
              <div className="steps">
                {mechanism.map((m, idx) => (
                  <div className="step" key={idx}>
                    <span className="step-num">
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                    <div>
                      <h3>{m.title}</h3>
                      {m.text && <p>{m.text}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="split-media sp-split--detail" aria-hidden="true" />
          </div>
        </section>
      )}

      {/* ---- 6) Jak to funguje — 3 kroky ---- */}
      {sx.steps && sx.steps.length > 0 && (
        <section className="section sp-tint">
          <div className="container sp-center">
            <span className="eyebrow">Jednoduše</span>
            <h2>Ke {offer.product} vedou jen 3 kroky</h2>
            <div className="sp-grid sp-grid--3">
              {sx.steps.slice(0, 3).map((s, idx) => (
                <div className="card sp-center" key={idx}>
                  <span className="sp-ico sp-ico--gold" style={{ marginBottom: 12 }}>
                    <Ico name={STEP_ICONS[idx % STEP_ICONS.length]} />
                  </span>
                  <div>
                    <span className="sp-time__badge">Krok {idx + 1}</span>
                  </div>
                  <h3 style={{ marginTop: 12 }}>{s.title}</h3>
                  <p className="muted">{s.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ---- 7) Váš den — předtím / potom ---- */}
      {sx.day && (
        <section className="sp-band sp-band--lp3">
          <div className="container">
            {sx.day.title && <h2 className="sp-center">{sx.day.title}</h2>}
            <div className="sp-day">
              <div className="sp-day__col sp-day__before">
                <span className="sp-day__tag">Dnes</span>
                <p>{sx.day.before}</p>
              </div>
              <div className="sp-day__col sp-day__after">
                <span className="sp-day__tag">S {offer.product}</span>
                <p>{sx.day.after}</p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* ---- 8) Benefity / komponenty — bento grid (jako landing „Co změří") ---- */}
      {show.benefits && benefits.length > 0 && (
        <section className="section sp-tint">
          <div className="container">
            <span className="eyebrow">Co tím získáte</span>
            <h2 className="bento-title">Hlavní přínosy pro Vás</h2>
            <div className="bento">
              {benefits.map((b, idx) => (
                <div
                  className={
                    idx === 0
                      ? "bento-card lead"
                      : idx === 2
                      ? "bento-card gold"
                      : "bento-card"
                  }
                  key={idx}
                >
                  <span className="bento-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 6L9 17l-5-5" />
                    </svg>
                  </span>
                  <div>
                    <h3>{b.t}</h3>
                    <p>{b.d}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ---- 8b) Komponenty / vlastnosti — alternující PAS bloky (spec-driven, skryje se bez dat) ---- */}
      {/* Pozadí bílé (ne sp-tint) — benefity nad tím jsou tintované, dvě tinty za sebou = šedý slepenec (rytmus). */}
      {sx.components && sx.components.length > 0 && (
        <section className="section">
          <div className="container sp-center">
            <span className="eyebrow">Co je uvnitř</span>
            <h2>{sx.components_title ?? "Co všechno dostanete"}</h2>
          </div>
          <div className="container sp-pas">
            {sx.components.map((c, i) => (
              <div
                className={
                  "sp-pas__row" + (i % 2 === 1 ? " sp-pas__row--rev" : "")
                }
                key={i}
              >
                <div className="sp-pas__media">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={safeImg(c.img, i)} alt={c.title} loading="lazy" />
                </div>
                <div className="sp-pas__text">
                  <span className="sp-pas__label">
                    <Ico name={icoName(c.icon)} />
                    {c.label ?? "Součást řešení"}
                  </span>
                  <h3>{c.title}</h3>
                  {c.sub && <p className="sp-pas__sub">{c.sub}</p>}
                  <p className="sp-pas__body">{c.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ---- 9) Bonusy — karty s fotkami ---- */}
      {sx.bonuses && sx.bonuses.length > 0 && (
        <section className="section">
          <div className="container sp-center">
            <span className="eyebrow">Dárky k objednávce</span>
            <h2>Co dnes získáte navíc</h2>
            <div className="sp-bonuses">
              {sx.bonuses.map((b, idx) => (
                <div className="sp-bonus sp-bonus--photo" key={idx}>
                  <span className="sp-bonus__tag">Dárek</span>
                  <div className="sp-bonus__media">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={safeImg(b.img, idx)}
                      alt={b.title}
                      loading="lazy"
                    />
                  </div>
                  <div className="sp-bonus__in">
                    <span className="sp-bonus__ic">
                      <Ico name={BONUS_ICONS[idx % BONUS_ICONS.length]} />
                    </span>
                    <h3>{b.title}</h3>
                    {b.desc && <p>{b.desc}</p>}
                    {b.value && <div className="sp-bonus__val">{b.value}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ---- 10) Produktový carousel — jen když je víc než 1 slide (jinak prázdný pás).
           carousel.slice(1): snímek 01 jde do value stacku (viz OFFER_IMG), pruh nese 02+. ---- */}
      {carousel.length > 1 && (
        <section className="section sp-tint">
          <div className="container">
            <span className="eyebrow">Prohlédněte si to</span>
            <h2 className="bento-title">Takhle to vypadá v praxi</h2>
          </div>
          <SalesCarousel slides={carousel.slice(1)} />
        </section>
      )}

      {/* ---- 11) Value stack #1 + garance (min-viable z offer) ---- */}
      {show.offerStack && (
        <section className="section" id="nabidka">
          <div className="container">
            <div className="sp-center">
              <span className="eyebrow">Nabídka</span>
              <h2>{offer.product} — co všechno získáte</h2>
            </div>

            <div className="sp-offer2">
              <div className="sp-offer2__media">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={OFFER_IMG} alt={offer.product} loading="lazy" />
              </div>
              <div className="sp-offer2__body">
                <ul className="sp-stack__list">
                  {stackItems.map((item, i) => (
                    <li className="sp-stack__row" key={i}>
                      <span className="sp-stack__ck">✓</span>
                      <span className="sp-stack__item">{item}</span>
                    </li>
                  ))}
                </ul>

                {sx.price && sx.price.now ? (
                  <>
                    <div className="sp-price">
                      {sx.price.orig && (
                        <span className="sp-price__orig">{sx.price.orig}</span>
                      )}
                      <span className="sp-price__now">{sx.price.now}</span>
                      {sx.price.save && (
                        <span className="sp-price__save">{sx.price.save}</span>
                      )}
                    </div>
                    {sx.price.note && (
                      <p className="sp-price__sub">{sx.price.note}</p>
                    )}
                  </>
                ) : (
                  <p className="sp-stack__price">{offer.price_note}</p>
                )}

                {route.variant && (
                  <span className="variant-tag sp-variant">
                    Vaše preferovaná varianta: {route.variant}
                  </span>
                )}

                <div className="sp-guarantee">
                  <span className="sp-guarantee__seal">
                    <Ico name="shield" />
                  </span>
                  <p>{offer.guarantee}</p>
                </div>

                <div className="sp-stack__cta">
                  <a
                    href={CTA_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-gold"
                  >
                    {route.cta}
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* ---- 12) Proof / tvrdá čísla — credibility band (jako landing) ---- */}
      {sx.proof_numbers && sx.proof_numbers.length > 0 && (
        <section className="sp-band sp-band--vecer">
          <div className="container sp-center">
            <span className="eyebrow">Důkazy</span>
            <h2>Nemusíte nám věřit. Stačí čísla.</h2>
            <p style={{ maxWidth: "48ch", margin: "0 auto" }}>
              {sx.proof_intro ?? "Čísla mluví za nás. Tady jsou."}
            </p>
            <div className="sp-proofg" style={{ marginTop: 26 }}>
              {sx.proof_numbers.map((p, idx) => (
                <div className="sp-proofg__c" key={idx}>
                  <div className="sp-proofg__n">{p.value}</div>
                  <div className="sp-proofg__l">{p.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ---- 13) Case study — stejný styl jako první recenze (foto-band) ---- */}
      {sx.case_study?.quote && (
        <section className="sp-band sp-band--lp4">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="sp-band__bg" src="/img/sp-lifep4.jpg" alt="" loading="lazy" />
          <div className="container">
            <blockquote>
              „<EmphQuote text={sx.case_study.quote} highlight={sx.case_study.highlight} />“
              <span className="quote-attribution">
                {sx.case_study.author}
                {sx.case_study.meta ? ` · ${sx.case_study.meta}` : ""}
              </span>
            </blockquote>
          </div>
        </section>
      )}

      {/* ---- 14) Pro koho / pro koho NE ---- */}
      {sx.for_whom?.yes && sx.for_whom.yes.length > 0 && (
        <section className="section sp-tint">
          <div className="container">
            <h2 className="sp-center">
              {sx.for_whom.title ?? "Je to pro Vaši situaci?"}
            </h2>
            <div className={`sp-fw${sx.for_whom.no?.length ? "" : " sp-fw--single"}`}>
              <div className="card sp-fw__yes">
                <h3>Je pro Vás</h3>
                <ul className="sp-fw__list">
                  {sx.for_whom.yes.map((y, i) => (
                    <li key={i}>
                      <span className="sp-check">✓</span>
                      <span>{y}</span>
                    </li>
                  ))}
                </ul>
              </div>
              {sx.for_whom.no && sx.for_whom.no.length > 0 && (
                <div className="card sp-fw__no">
                  <h3>Není pro Vás</h3>
                  <ul className="sp-fw__list">
                    {sx.for_whom.no.map((n, i) => (
                      <li key={i}>
                        <span className="sp-x">✕</span>
                        <span>{n}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* ---- 15) Srovnávací tabulka ---- */}
      {sx.comparison?.rows && sx.comparison.rows.length > 0 && (
        <section className="section">
          <div className="container">
            <span className="eyebrow">Srovnání</span>
            <h2>Rozdíl uvidíte na první pohled</h2>
            <div className="card sp-cmp-wrap">
              <table className="sp-cmp">
                <thead>
                  <tr>
                    <th />
                    {sx.comparison.columns.map((c, i) => (
                      <th key={i} className={i === 0 ? "sp-cmp__us" : ""}>
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sx.comparison.rows.map((r, i) => (
                    <tr key={i}>
                      <td className="sp-cmp__label">{r.label}</td>
                      {r.cells.map((cell, j) => {
                        const v = cell.trim().toLowerCase();
                        const cls = j === 0 ? "sp-cmp__us" : "";
                        return (
                          <td key={j} className={cls}>
                            {v === "ano" ? (
                              <span className="sp-cmp__yes" aria-label="ano">✓</span>
                            ) : v === "ne" ? (
                              <span className="sp-cmp__no" aria-label="ne">✕</span>
                            ) : (
                              <span className="sp-cmp__txt">{cell}</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* ---- 16) Stroj času 1 / 6 / 12 ---- */}
      {sx.timeline && (
        <section className="sp-band sp-band--lp5">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="sp-band__bg" src="/img/sp-lifep5.jpg" alt="" loading="lazy" />
          <div className="container sp-center">
            <span className="eyebrow">Vize budoucnosti</span>
            <h2>{sx.timeline.title ?? "Kde budete za rok?"}</h2>
            <div className="sp-grid sp-grid--3">
              {[
                { b: "za 1 měsíc", t: sx.timeline.m1 },
                { b: "za 6 měsíců", t: sx.timeline.m6 },
                { b: "za 12 měsíců", t: sx.timeline.m12 },
              ].map((it, i) => (
                <div className="sp-tl-card" key={i}>
                  <span className="sp-tl-card__step">{i + 1}</span>
                  <span className="sp-tl-card__badge">{it.b}</span>
                  <p>{it.t}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ---- 17) Genesis / příběh — editoriál (velký nadpis → fotka 4:3 → 2sl. text) ---- */}
      {sx.genesis && (
        <section className="section sp-genesis-sec">
          <div className="container sp-genesis-ed">
            <header className="sp-genesis-ed__head">
              <span className="eyebrow">Proč to děláme</span>
              <h2>{sx.genesis.title}</h2>
            </header>
            {sx.genesis.image && (
              <figure className="sp-genesis-ed__media">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={safeImg(sx.genesis.image, 4)} alt="" loading="lazy" />
              </figure>
            )}
            <div className="sp-genesis-ed__body">
              {sx.genesis.body
                .split(/\n\s*\n/)
                .map((s) => s.trim())
                .filter(Boolean)
                .map((para, i) => (
                  <p key={i} className={i === 0 ? "sp-lead" : ""}>
                    {para}
                  </p>
                ))}
            </div>
          </div>
        </section>
      )}

      {/* ---- 18) Osobní vzkaz — personalizované shrnutí PROČ (bez CTA; stack se svým CTA je hned pod tím) ---- */}
      <section className="sp-band sp-band--lp6" id="dalsi-krok">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="sp-band__bg" src="/img/sp-lifep6.jpg" alt="" loading="lazy" />
        <div className="container">
          <div className="cta-panel">
            <span className="eyebrow">Proč právě Vy</span>
            <h2>
              {voc ? `${voc}, ` : ""}proč to má smysl právě pro Vás
            </h2>
            <p className="cta-panel__lead">{closeSummary}</p>
            {sx.urgency && temperature !== "cold" && (
              <p className="sp-cta-urgency">{sx.urgency}</p>
            )}
          </div>
        </div>
      </section>

      {/* ---- 19) Value stack #2 — rekapitulace ---- */}
      {show.offerStack && sx.stack2 && (
        <section className="section" id="objednat">
          <div className="container">
            <div className="sp-center">
              <span className="eyebrow">Shrnutí</span>
              <h2>Co získáte, když se rozhodnete dnes</h2>
            </div>
            <div className="sp-offer2">
              <div className="sp-offer2__media">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={OFFER_IMG} alt={offer.product} loading="lazy" />
              </div>
              <div className="sp-offer2__body">
                <ul className="sp-stack__list">
                  {stackItems.slice(0, 6).map((item, i) => (
                    <li className="sp-stack__row" key={i}>
                      <span className="sp-stack__ck">✓</span>
                      <span className="sp-stack__item">{item}</span>
                    </li>
                  ))}
                </ul>
                {sx.price && sx.price.now ? (
                  <div className="sp-price">
                    {sx.price.orig && (
                      <span className="sp-price__orig">{sx.price.orig}</span>
                    )}
                    <span className="sp-price__now">{sx.price.now}</span>
                    {sx.price.save && (
                      <span className="sp-price__save">{sx.price.save}</span>
                    )}
                  </div>
                ) : (
                  <p className="sp-stack__price">{offer.price_note}</p>
                )}
                <div className="sp-stack__cta">
                  <a
                    href={CTA_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-gold"
                  >
                    {route.cta}
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* ---- 20) Garance — aha moment (silná karta s pečetí) ---- */}
      {sx.guarantee_aha && sx.guarantee_aha.length > 0 && (
        <section className="section">
          <div className="container sp-narrow">
            <div className="sp-gbox">
              <div className="sp-gbox__seal">
                <Ico name="shield" />
                <span>Bez rizika</span>
              </div>
              <div className="sp-gbox__body">
                <span className="eyebrow">Garance</span>
                <h2>Nenesete žádné riziko</h2>
                {sx.guarantee_aha_lead && (
                  <p className="sp-gbox__lead">{sx.guarantee_aha_lead}</p>
                )}
                <ul className="sp-gbox__list">
                  {sx.guarantee_aha.map((g, i) => (
                    <li key={i}>
                      <span className="sp-check">✓</span>
                      <span>{g}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* ---- 21) FAQ / námitky — řazené dle segmentu ---- */}
      {(show.objections && objections.length > 0) ||
      (sx.faq && sx.faq.length > 0) ? (
        <section className="section sp-faq-band">
          <div className="container sp-narrow">
            <span className="eyebrow">Možná si říkáte</span>
            <h2>Odpovědi na Vaše otázky</h2>
            <div className="sp-faq">
              {show.objections &&
                objections.map((o, idx) => (
                  <details className="sp-faq__item" key={`o${idx}`}>
                    <summary>{o.t}</summary>
                    <p>{o.r}</p>
                  </details>
                ))}
              {sx.faq?.map((f, idx) => (
                <details className="sp-faq__item" key={`f${idx}`}>
                  <summary>{f.q}</summary>
                  <p>{f.a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>
      ) : null}

      {/* ---- Sticky mobile CTA bar ---- */}
      <div className="sticky-cta">
        <span className="sticky-cta-label">
          {personalized
            ? mrView.kind === "score"
              ? `${mrView.label}: ${vars.score}${mrView.unit}`
              : mrView.label
            : offer.product}
        </span>
        <a
          className="btn btn-gold"
          href={CTA_URL}
          target="_blank"
          rel="noopener noreferrer"
        >
          {route.cta}
        </a>
      </div>
    </main>
  );
}
