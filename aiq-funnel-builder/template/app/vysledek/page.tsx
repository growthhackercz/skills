import Link from "next/link";
import { getContactBundle } from "../../lib/server";
import { spec, BRAND } from "../../lib/spec";
import { categoryColor, mainResultView, categorySummary } from "../../lib/ui";
import { vocative } from "../../lib/vocative";
import PersonalizeKicker from "../../components/PersonalizeKicker";
import type { ContactBundle } from "../../lib/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export const metadata = {
  title: `Váš výsledek | ${BRAND.name}`,
  robots: { index: false, follow: false },
};

export default async function ResultPage({
  searchParams,
}: {
  searchParams: Promise<{ c?: string }>;
}) {
  const { c } = await searchParams;
  const contactId = c?.trim() ?? "";

  let bundle: ContactBundle | null = null;
  if (contactId) {
    try {
      bundle = await getContactBundle(contactId);
    } catch {
      bundle = null;
    }
  }

  // Graceful fallback when contactId missing or contact not found.
  if (!bundle) {
    return (
      <div className="result-shell">
        <div className="result-card">
          <span className="eyebrow">{spec.lead_magnet_name}</span>
          <h1>Výsledek zatím nemáme</h1>
          <p className="muted">
            Nepodařilo se nám najít vaše odpovědi. Vyplňte je prosím znovu —
            zabere to jen pár minut.
          </p>
          <Link href="/" className="btn" style={{ marginTop: 12 }}>
            Vyplnit znovu
          </Link>
        </div>
      </div>
    );
  }

  const vars = bundle.vars;
  const color = categoryColor(vars.category_key);
  // Vokativ (5. pád), ne nominativ — G11. Neznámé jméno → bez oslovení.
  const voc = vocative(vars.first_name);
  const greeting = voc ? `${voc}, ` : "";
  const meaning =
    spec.main_result.meaning[vars.category_key] ??
    categorySummary(vars.category_key);
  const insights = buildInsights(vars.top_pain, vars.recommended_variant);
  const mrView = mainResultView(vars.score, bundle.answers);

  const rHref = `/online/${encodeURIComponent(contactId)}`;

  return (
    <div className="result-shell">
      <div className="result-card">
        <span className="eyebrow">
          {spec.lead_magnet_name} · {BRAND.name}
        </span>
        <h1>{greeting}tady je váš výsledek</h1>

        {/* ---- Blok 1: main_result (deterministický; score = gauge, plan = režim) ---- */}
        <div className="score-wrap">
          {mrView.kind === "score" ? (
            <div
              className="gauge"
              style={
                {
                  ["--val" as string]: String(vars.score),
                  ["--gauge-color" as string]: color,
                } as React.CSSProperties
              }
            >
              <div className="gauge-inner">
                <span className="gauge-num">{vars.score}</span>
                <span className="gauge-of">{mrView.unit}</span>
              </div>
            </div>
          ) : (
            <div className="plan-box" style={{ borderColor: color }}>
              {mrView.display}
            </div>
          )}

          <div>
            <span className="category-pill" style={{ background: color }}>
              {mrView.label}: {vars.score_category}
            </span>
            <p className="muted" style={{ maxWidth: "44ch", marginBottom: 0 }}>
              {meaning}
            </p>
          </div>
        </div>

        {/* ---- Co z auditu vyplývá (deterministické insights) ---- */}
        <h2 style={{ fontSize: 22 }}>Co z vašich odpovědí vyplývá</h2>
        <div className="insights">
          {insights.map((ins, i) => (
            <div className="insight" key={i}>
              <span className="dot" style={{ background: color }} />
              <span>{ins}</span>
            </div>
          ))}
        </div>

        {/* ---- Segment (deterministický) ---- */}
        <div className="segment-box">
          <h3>{vars.segment_headline}</h3>
          <p>{vars.segment_proof}</p>
        </div>

        {/* ---- Předpis-teaser (open loop) + CTA na /online/ ---- */}
        <div className="openloop-box">
          <span className="eyebrow" style={{ color: "var(--gold)" }}>
            Doporučení na míru
          </span>
          <h3 style={{ marginBottom: 8 }}>
            Pro vaši situaci existuje konkrétní konfigurace
          </h3>
          <p className="muted" style={{ marginBottom: 14 }}>
            Z kombinace vašich odpovědí jsme sestavili doporučení přesně pro
            vaši situaci — s prioritami podle toho, co jste nám napsali, a s
            dalším krokem, který jste si sami vybrali.
          </p>
          <Link href={rHref} className="btn">
            Zobrazit doporučení na míru
          </Link>
        </div>

        {/* ---- Personalizace na pozadí (LLM) ---- */}
        <PersonalizeKicker
          contactId={contactId}
          initialReady={bundle.personalizationReady}
        />
      </div>

      <div className="footer-note">
        {BRAND.name} · {spec.offer.product} — doporučení na míru
      </div>
    </div>
  );
}

/** 2–3 calm, factual insights (plně deterministické — žádné LLM). */
function buildInsights(
  topPain: string,
  recommendedVariant: string
): string[] {
  const out: string[] = [];

  if (topPain) {
    out.push(
      `Nejvíc vás trápí ${topPain}. Přesně na to cílí doporučení, které pro vás připravujeme.`
    );
  }

  out.push(
    `${spec.main_result.label} vychází z kombinace vašich odpovědí — z toho, jak to u vás dnes vypadá a co vám na tom vadí.`
  );

  if (recommendedVariant) {
    out.push(
      `Podle vašich preferencí dává smysl jako další krok: ${recommendedVariant}.`
    );
  } else {
    out.push(
      "Doporučení na míru vám připravíme tak, aby odpovídalo přesně vaší situaci. Bez tlaku a zbytečných slibů."
    );
  }

  return out.slice(0, 3);
}
