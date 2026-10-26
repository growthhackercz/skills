import Link from "next/link";
import { redirect } from "next/navigation";
import { spec, BRAND, ctaRoute, ROUTE_QUESTION_ID } from "../../../lib/spec";
import { getContactBundle } from "../../../lib/server";
import type { ContactBundle } from "../../../lib/server";
import { withPersonaFallback } from "../../../lib/fallback";
import { categoryColor, mainResultView, mechanismForPains } from "../../../lib/ui";
import {
  computeAreaScores,
  quotableAnswers,
  benchmarkRow,
  czVocative,
  buildHeadline,
} from "../../../lib/funnel";
import { Markdown } from "../../../lib/markdown";
import AiPending from "../../../components/AiPending";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export const metadata = {
  title: `Kompletní analýza | ${BRAND.name}`,
  robots: { index: false, follow: false },
};

/**
 * Parser karet pro render `cards` ve flexibilním STŘEDU. Tolerantní: nejdřív dělí
 * na prázdné řádky, jinak po řádcích; zvládne i formát "**Nadpis** popis" na jednom
 * řádku. Vrací {title, body}[] — bez titulku se karta zahodí.
 */
function parseCards(text: string): { title: string; body: string }[] {
  const chunks = text.split(/\n\s*\n/).map((c) => c.trim()).filter(Boolean);
  const list =
    chunks.length >= 2 ? chunks : text.split(/\n/).map((c) => c.trim()).filter(Boolean);
  return list
    .map((chunk) => {
      const one = chunk.match(/^\s*[-*]?\s*\*\*(.+?)\*\*[\s—:.-]*([\s\S]*)$/);
      if (one) return { title: one[1].trim(), body: one[2].replace(/\*\*/g, "").trim() };
      const lines = chunk.split("\n");
      const title = (lines[0] ?? "")
        .replace(/\*\*/g, "")
        .replace(/^#+\s*/, "")
        .replace(/^\s*[-*]\s*/, "")
        .replace(/[—:.\s-]+$/, "")
        .trim();
      const body = lines.slice(1).join(" ").replace(/\*\*/g, "").trim();
      return { title, body };
    })
    .filter((c) => c.title);
}

export default async function MagnetPage({
  params,
}: {
  params: Promise<{ contactId: string }>;
}) {
  const { contactId } = await params;

  // Čistá URL (bez tokenu) — contactId je capability klíč. Neexistující kontakt
  // → getContactBundle vrátí null → redirect na generickou stránku.
  if (!contactId) redirect("/doporuceni");

  let bundle: ContactBundle | null = null;
  try {
    bundle = await getContactBundle(contactId);
  } catch {
    bundle = null;
  }
  if (!bundle) redirect("/doporuceni");

  const { vars, answers } = bundle;
  // AI hotová? = raw persona z GHL má vygenerovaný rozbor. Řídí, jestli se AI
  // (spodní) zóna vykreslí, nebo běží loader. Musí být PŘED withPersonaFallback.
  const aiReady = Boolean((bundle.persona?.magnet_rozbor ?? "").trim());
  const persona = withPersonaFallback(bundle.persona);
  const color = categoryColor(vars.category_key);
  const headlineDet = buildHeadline(answers);
  const meaning = spec.main_result.meaning[vars.category_key] ?? "";
  const mrView = mainResultView(vars.score, answers);

  const rHref = `/online/${encodeURIComponent(contactId)}`;

  // Dílčí skóre oblastí (F2).
  const areas = computeAreaScores(answers);

  // Kartičky „pod lupou" — AI vybere z odpovědí 5 nejsilnějších (aha-momenty) a
  // přepíše je do KONSTATOVÁNÍ (problemN_question = tvrzení, ne „otázka? → Ne")
  // + hloubkového dopadu (problemN_impact). Čistě AI. Deterministické zrcadlo
  // „černé na bílém" ZRUŠENO: hero je deterministický, zbytek personalizovaný.
  // Punch list pod hero — DETERMINISTICKÝ (instantní, bez AI): ANO/NE problémové
  // odpovědi jako konstatování ze `spec.questions[].problem_statement`. Vždy přesná
  // sada, žádné vynechání ani záměna (Flash to netrefil spolehlivě).
  const punchList = spec.questions
    .filter((q) => q.problem_statement)
    .map((q) => {
      const raw = answers[q.id];
      const val = String((Array.isArray(raw) ? raw[0] : raw) ?? "");
      return q.problem_statement?.[val] ?? "";
    })
    .filter(Boolean);

  // POD LUPOU = jen BOHATÉ odpovědi (single/multi); ANO/NE jsou v punch listu nad tím.
  // DETERMINISTICKÉ párování podle pořadí — otázka i odpověď se berou přímo z odpovědi
  // (vždy sedí), AI dodává jen hloubkový dopad (problemN_impact) do svého slotu.
  const richAnswers = quotableAnswers(answers).filter((q) => {
    const qq = spec.questions.find((x) => x.id === q.qid);
    return qq && qq.type !== "yesno";
  });
  const podLupou = richAnswers
    .map((rich, idx) => ({
      question: rich.question,
      answer: rich.answer,
      impact: (persona[`problem${idx + 1}_impact`] ?? "").trim(),
    }))
    .filter((c) => c.impact);

  // Benchmark (F3).
  const bm = benchmarkRow(answers);

  // Měsíční cena odkladu (deterministicky z ročního benchmarku / 12) — reálné číslo,
  // NE z AI, takže mimo money-lint. Feeduje urgenci ve fázi 5. Chybí-li benchmark → "".
  const bmDigits = parseInt((bm?.row.money ?? "").replace(/[^\d]/g, ""), 10);
  const monthlyCost =
    Number.isFinite(bmDigits) && bmDigits > 0 ? Math.round(bmDigits / 12 / 10) * 10 : 0;
  const monthlyCostLabel =
    monthlyCost > 0
      ? `${String(monthlyCost).replace(/\B(?=(\d{3})+(?!\d))/g, " ")} Kč`
      : "";

  // Žebříček oblastí (nejvyšší potřeba nahoře) + mechanismus (redukovaný, třída řešení).
  const rankedAreas = [...areas].sort((a, b) => b.pct - a.pct);
  const pains = quotableAnswers(answers)
    .flatMap((q) => q.answer.split(", "))
    .slice(0, 3);
  const mechanisms = mechanismForPains(pains);

  const routeRaw = answers[ROUTE_QUESTION_ID];
  const routeAnswer = Array.isArray(routeRaw) ? routeRaw[0] ?? "" : routeRaw ?? "";
  const route = ctaRoute(routeAnswer);

  // Vizuály výsledku (silné produktové fotky). Chybí-li klíč → slot se přeskočí.
  const img = spec.magnet_images ?? {};

  // Flexibilní STŘED (fáze 3) — bloky navržené strategií v spec.magnet_middle.
  // Každý má vygenerovaný text v persona[persona_field]. Prázdné texty se vynechají.
  // Chybí-li magnet_middle (starší funnely) → middleBlocks je prázdné a runtime
  // spadne na dnešní pevný střed (rozbor/žebříček/akce) níž. AIQ Engine = tenhle
  // střed dělá každý magnet unikátní při stejném psychologickém oblouku.
  const middleBlocks = (spec.magnet_middle ?? [])
    .filter((b) => b.render && b.persona_field)
    .map((b) => ({
      key: b.key,
      title: b.title,
      subtitle: b.subtitle ?? "",
      render: b.render as "text" | "cards" | "steps",
      text: (persona[b.persona_field as string] ?? "").trim(),
    }))
    .filter((b) => b.text && ["text", "cards", "steps"].includes(b.render));

  // Deterministický H1 (předpřipravená kombinace) + oslovení ve vokativu —
  // celá TOP zóna se vykreslí HNED, bez čekání na AI.
  const heroH1 = vars.first_name
    ? `${czVocative(vars.first_name)}, ${headlineDet}`
    : headlineDet.charAt(0).toUpperCase() + headlineDet.slice(1);

  return (
    <div className="mag2">
      {/* ==================== TOP ZÓNA — DETERMINISTICKÁ (vykreslí se HNED) ==================== */}
      <section
        className="mag2-hero"
        style={{ ["--band" as string]: color } as React.CSSProperties}
      >
        <div className="mag2-hero-inner">
          <span className="mag2-eyebrow">
            {spec.lead_magnet_name} · {BRAND.name}
          </span>
          <h1 className="mag2-h1">{heroH1}</h1>

          <div className="mag2-hero-grid">
            {/* Hlavní číslo / gauge */}
            <div className="mag2-score">
              {mrView.kind === "score" ? (
                <div
                  className="gauge mag2-gauge"
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
              <span className="mag2-pill" style={{ background: color }}>
                {vars.score_category}
              </span>
            </div>

            {/* Area bary (F2) + meaning */}
            <div className="mag2-areas">
              {areas.map((a) => (
                <div className="mag2-area" key={a.key}>
                  <div className="mag2-area-top">
                    <span className="mag2-area-label">{a.label}</span>
                    <span className="mag2-area-verdict">
                      {a.showPct ? `${a.pct} %` : a.verdict}
                    </span>
                  </div>
                  <div className="mag2-bar">
                    <span
                      className="mag2-bar-fill"
                      style={{ width: `${a.pct}%`, background: color }}
                    />
                  </div>
                </div>
              ))}
              {meaning && <p className="mag2-meaning">{meaning}</p>}
            </div>
          </div>
        </div>
      </section>

      <div className="mag2-body">
        {/* ===== Punch list pod hero — ANO/NE rizika, DETERMINISTICKY a HNED ===== */}
        {punchList.length > 0 && (
          <section className="mag2-section">
            <span className="mag2-eyebrow dark">Na co pozor</span>
            <h2 className="mag2-h2">Vaše hlavní rizika</h2>
            <ul className="mag2-punchlist">
              {punchList.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </section>
        )}

        {/* ============ Benchmark „šok z čísla" ============ */}
        {bm && (
          <section className="mag2-section mag2-benchmark">
            <div className="mag2-bm-number" style={{ color }}>
              {bm.row.headline}
            </div>
            {bm.row.money && (
              <div className="mag2-bm-money" style={{ color }}>
                {bm.row.money}
              </div>
            )}
            {bm.row.sub && <p className="mag2-bm-sub">{bm.row.sub}</p>}
            {/* Benchmark = šok z čísla, BEZ produktu (ten až v sekci „Řešení" níž).
               Vždy textové sloupce Dnes → S řešením, nikdy produktové foto. */}
            <div className="mag2-bm-cols">
              <div className="mag2-bm-col">
                <span className="mag2-bm-tag">Dnes</span>
                <p>{bm.todayText ?? "Současný stav, který vás stojí čas i peníze"}</p>
              </div>
              <div className="mag2-bm-arrow" aria-hidden="true">
                →
              </div>
              <div className="mag2-bm-col mag2-bm-sol">
                <span className="mag2-bm-tag" style={{ background: color }}>
                  {bm.solutionLabel ?? "S řešením"}
                </span>
                <p>{bm.solutionText ?? "Řešení, které to sundá z krku"}</p>
              </div>
            </div>
            {bm.row.assumption && (
              <p className="mag2-bm-note">Orientačně, {bm.row.assumption}.</p>
            )}
          </section>
        )}

        {/* ==================== ZBYTEK — AI ZÓNA (progresivně) ====================
           Hotovo → hloubkové bloky. Negeneruje se → loader, co kickne + polluje
           a po dogenerování stránku obnoví (router.refresh). */}
        {aiReady ? (
          <>
            {/* Diagnóza — konstatování odpovědi (ne „otázka? → Ne") + hloubkový dopad */}
            {podLupou.length > 0 && (
              <section className="mag2-section">
                <span className="mag2-eyebrow dark">Pod lupou</span>
                <h2 className="mag2-h2">Co se skrývá za vašimi odpověďmi</h2>
                <div className="mag2-quotes">
                  {podLupou.map((c, i) => (
                    <figure className="mag2-quote-card" key={i}>
                      <div className="mag2-quote-head">
                        <span className="mag2-quote-mark" aria-hidden="true">
                          „
                        </span>
                        <div>
                          {c.question && (
                            <p className="mag2-quote-q">{c.question}</p>
                          )}
                          <p className="mag2-quote-a">{c.answer}</p>
                        </div>
                      </div>
                      <div className="mag2-quote-impact">
                        <Markdown text={c.impact} />
                      </div>
                    </figure>
                  ))}
                </div>
              </section>
            )}

        {/* ======================================================================
            FÁZE 3 — FLEXIBILNÍ STŘED (AIQ Engine). Když spec.magnet_middle existuje,
            renderuje se smyčkou (text/cards/steps) → každý magnet unikátní. Jinak
            fallback na pevný střed níž (rozbor/žebříček/akce) — starší funnely beze
            změny.
        ====================================================================== */}
        {middleBlocks.length > 0 ? (
          <>
            {middleBlocks.map((b) => (
              <section className="mag2-section" key={b.key}>
                {b.subtitle && <span className="mag2-eyebrow dark">{b.subtitle}</span>}
                <h2 className="mag2-h2">{b.title}</h2>
                {b.render === "cards" ? (
                  <div className="mag2-midcards">
                    {parseCards(b.text).map((c, i) => (
                      <div
                        className="mag2-midcard"
                        key={i}
                        style={{ ["--band" as string]: color } as React.CSSProperties}
                      >
                        <h3>{c.title}</h3>
                        {c.body && <p>{c.body}</p>}
                      </div>
                    ))}
                  </div>
                ) : b.render === "steps" ? (
                  <Markdown className="mag2-steps" text={b.text} />
                ) : (
                  <Markdown className="mag2-prose" text={b.text} />
                )}
              </section>
            ))}
          </>
        ) : (
          <>
            {/* ===== Legacy pevný střed (funnely bez magnet_middle) — beze změny ===== */}
            {persona.magnet_rozbor?.trim() && (
              <section className="mag2-section">
                <span className="mag2-eyebrow dark">Souvislosti</span>
                <h2 className="mag2-h2">Jak to u vás zapadá dohromady</h2>
                <Markdown className="mag2-prose" text={persona.magnet_rozbor} />
              </section>
            )}

            {rankedAreas.filter((a) => a.pct > 0).length > 0 && (
              <section className="mag2-section">
                <span className="mag2-eyebrow dark">Kde je největší prostor</span>
                <h2 className="mag2-h2">Na co se u vás vyplatí zaměřit</h2>
                <div className="mag2-ranked">
                  {rankedAreas
                    .filter((a) => a.pct > 0)
                    .slice(0, 3)
                    .map((a, i) => (
                      <div className="mag2-rank-item" key={a.key}>
                        <span className="mag2-rank-num" style={{ background: color }}>
                          {i + 1}
                        </span>
                        <div>
                          <h3>{a.label}</h3>
                          {mechanisms[i]?.title && (
                            <p>
                              <strong>{mechanisms[i].title}.</strong>{" "}
                              {mechanisms[i].text}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                </div>
              </section>
            )}
            {/* Sekce „Co můžete udělat hned" odstraněna — odkláněla od nákupu. */}
          </>
        )}

        {/* Segment box odstraněn (spec-dump výkonových čísel nepatří do magnetu). */}

        {/* ===== Fáze 4: Shrnutí — kde jste ↔ kam chcete + silná pointa ===== */}
        {persona.pointa?.trim() && (
          <section className="mag2-section">
            <span className="mag2-eyebrow dark">Shrnutí</span>
            <h2 className="mag2-h2">Kde jste dnes a kde byste chtěli být</h2>
            {(persona.souhrn_ted?.trim() || persona.souhrn_chci?.trim()) && (
              <div className="mag2-gap">
                {persona.souhrn_ted?.trim() && (
                  <div className="mag2-gap-col now">
                    <span className="mag2-gap-l">Současný stav</span>
                    <p>{persona.souhrn_ted}</p>
                  </div>
                )}
                <div className="mag2-gap-arrow" aria-hidden="true">→</div>
                {persona.souhrn_chci?.trim() && (
                  <div className="mag2-gap-col want" style={{ ["--band" as string]: color } as React.CSSProperties}>
                    <span className="mag2-gap-l">Váš cíl</span>
                    <p>{persona.souhrn_chci}</p>
                  </div>
                )}
              </div>
            )}
            <p
              className="mag2-punch"
              style={{ ["--band" as string]: color } as React.CSSProperties}
            >
              {persona.pointa}
            </p>
          </section>
        )}

        {/* ==================================================================
            FÁZE 5 — Co s tím? Řešení (dle schválené AIQ šablony):
            1) mechanismus + produkt jako odpověď (obr. 04 detail)
            2) přínos → vize předtím/potom (obr. 05 před→po)
            3) obraz potom + shrnutí, emoční vrchol (obr. 06 lifestyle)
            Všechny 3 obrázky na plnou šířku. Žádný „Váš předpis".
        ================================================================== */}
        <section className="mag2-section mag2-solution">
          <span className="mag2-eyebrow gold">Co s tím?</span>
          <h2 className="mag2-h2">Řešení na míru vaší situaci</h2>

          {/* Krok 1 — mechanismus + produkt jako odpověď */}
          <div className="mag2-solstep">
            <div className="mag2-solstep-h">
              <span className="mag2-solstep-n" style={{ background: color }}>
                1
              </span>
              <div>
                <h3>{spec.offer.product}</h3>
                <p className="mag2-solstep-sub">Jak to řeší vaši situaci</p>
              </div>
            </div>
            {persona.predpis_config?.trim() ? (
              <Markdown className="mag2-prose" text={persona.predpis_config} />
            ) : (
              <p className="mag2-prose">{spec.offer.usp}</p>
            )}
            {img.detail && (
              // Dynamic self-hosted asset from the funnel spec; intrinsic dimensions vary.
              // eslint-disable-next-line @next/next/no-img-element
              <img
                className="mag2-solimg"
                src={img.detail}
                alt={spec.offer.product}
                loading="lazy"
              />
            )}
          </div>

          {/* Krok 2 — přínos → vize předtím/potom (benefity navázané na jeho problémy) */}
          <div className="mag2-solstep">
            <div className="mag2-solstep-h">
              <span className="mag2-solstep-n" style={{ background: color }}>
                2
              </span>
              <div>
                <h3>Co získáte</h3>
                <p className="mag2-solstep-sub">Konkrétní přínosy pro vás</p>
              </div>
            </div>
            <div className="mag2-benefits">
              {[
                { t: persona.benefit_1_title, d: persona.benefit_1_description },
                { t: persona.benefit_2_title, d: persona.benefit_2_description },
                { t: persona.benefit_3_title, d: persona.benefit_3_description },
              ]
                .map((b) => ({
                  t: (b.t ?? "").replace(/\*\*/g, "").trim(),
                  d: (b.d ?? "").trim(),
                }))
                .filter((b) => b.t)
                .map((b, i) => (
                  <div
                    className="mag2-benefit"
                    key={i}
                    style={{ ["--band" as string]: color } as React.CSSProperties}
                  >
                    <h4>{b.t}</h4>
                    {b.d && <Markdown className="mag2-benefit-d" text={b.d} />}
                  </div>
                ))}
            </div>
            {img.beforeafter && (
              // Dynamic self-hosted asset from the funnel spec; intrinsic dimensions vary.
              // eslint-disable-next-line @next/next/no-img-element
              <img
                className="mag2-solimg"
                src={img.beforeafter}
                alt=""
                loading="lazy"
              />
            )}
          </div>

          {/* Krok 3 — obraz „potom" + shrnutí (emoční vrchol, future pacing) */}
          {(persona.obraz_potom?.trim() || img.product) && (
            <div className="mag2-solstep">
              <div className="mag2-solstep-h">
                <span className="mag2-solstep-n" style={{ background: color }}>
                  3
                </span>
                <div>
                  <h3>Vaše nová realita</h3>
                  <p className="mag2-solstep-sub">Vize budoucnosti</p>
                </div>
              </div>
              {persona.obraz_potom?.trim() && (
                <Markdown className="mag2-prose" text={persona.obraz_potom} />
              )}
              {img.product && (
                // Dynamic self-hosted asset from the funnel spec; intrinsic dimensions vary.
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  className="mag2-solimg"
                  src={img.product}
                  alt={spec.offer.product}
                  loading="lazy"
                />
              )}
            </div>
          )}
        </section>

        {/* ============ Fáze 5: Urgence — proč to neodkládat (Product DNA + deterministický měsíční náklad) ============ */}
        {persona.nalehavost?.trim() && (
          <section className="mag2-section">
            <div
              className="mag2-urgency"
              style={{ ["--band" as string]: color } as React.CSSProperties}
            >
              <span className="mag2-eyebrow gold">Proč to neodkládat</span>
              <p className="mag2-urgency-lead">{persona.nalehavost}</p>
              {monthlyCostLabel && (
                <p className="mag2-urgency-cost">
                  Každý měsíc odkladu vás stojí zhruba{" "}
                  <strong>{monthlyCostLabel}</strong> navíc.
                </p>
              )}
            </div>
          </section>
        )}

        {/* ============ Jediné CTA ============ */}
        <section className="mag2-section">
          <div className="mag2-cta" style={{ ["--band" as string]: color } as React.CSSProperties}>
            <span className="mag2-eyebrow gold">Další krok</span>
            <h2 className="mag2-h2">
              {routeAnswer
                ? `Vybrali jste si: ${routeAnswer}`
                : "Váš další krok"}
            </h2>
            <p>{vars.cta_offer}</p>
            <Link href={rHref} className="btn btn-gold">
              {route.cta}
            </Link>
          </div>
        </section>
          </>
        ) : (
          <AiPending contactId={contactId} color={color} />
        )}

        <div className="footer-note">
          {BRAND.name} · {spec.lead_magnet_name}
        </div>
      </div>
    </div>
  );
}
