"use client";

import { useState, useEffect } from "react";
import Quiz from "../components/Quiz";
import { spec, BRAND } from "../lib/spec";

/** Count-up power čísel při scrollu do view (běží 1×). Zachová prefix/suffix
 *  i mezery ("4 000+", "100 %", "15+"). */
function useCountUp() {
  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return;
    const nums = Array.from(
      document.querySelectorAll<HTMLElement>(".cred-stat .num")
    );
    if (!nums.length) return;
    const run = (el: HTMLElement) => {
      const orig = el.textContent ?? "";
      const m = orig.match(/^([^\d]*)([\d \s]*\d)(.*)$/);
      if (!m) return;
      const prefix = m[1];
      const suffix = m[3];
      const target = parseInt(m[2].replace(/[^\d]/g, ""), 10) || 0;
      const group = (n: number) =>
        n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
      const dur = 1200;
      let start = 0;
      const ease = (t: number) => 1 - Math.pow(1 - t, 3);
      const tick = (now: number) => {
        if (!start) start = now;
        const p = Math.min(1, (now - start) / dur);
        el.textContent = prefix + group(Math.round(target * ease(p))) + suffix;
        if (p < 1) requestAnimationFrame(tick);
        else el.textContent = orig;
      };
      requestAnimationFrame(tick);
    };
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            io.unobserve(e.target);
            run(e.target as HTMLElement);
          }
        });
      },
      { threshold: 0.4 }
    );
    nums.forEach((n) => io.observe(n));
    return () => io.disconnect();
  }, []);
}

/**
 * Landing page — texty čte ze spec.landing (fallback generický základ ze spec).
 * Builder při nasazení dodává obrázky /img/hero.jpg + /img/process.jpg + /img/mockup.png
 * (deploy krok 3c — Pexels → browser → image_generate). Bez obrázků drží
 * layout tonální gradienty, nikdy rozbité <img>.
 *
 * Kompozice (vibe-builder): Mid Editorial Hero (foto + tonální overlay)
 * → dense karty → calm quote band → split kroky+foto → dense CTA panel.
 */
export default function LandingPage() {
  const [started, setStarted] = useState(false);
  // Landing copy ze spec.landing (dřív landing-copy.md, zrušeno). Fallback = generický základ ze spec.
  const landing =
    (spec as unknown as {
      landing?: {
        hero_headline?: string;
        hero_sub?: string;
        areas?: { title?: string; desc?: string }[];
        authority?: string;
        cta?: string;
        quiz_microcopy?: string;
      };
    }).landing ?? {};
  const areas = Array.isArray(landing.areas) ? landing.areas : [];
  const startLabel = landing.cta || `Spustit ${spec.lead_magnet_name}`;
  useCountUp();

  return (
    <main>
      {started && <Quiz onClose={() => setStarted(false)} />}

      {/* ---- HERO: Mid Editorial — video/foto podklad + overlay, mockup jako plovoucí karta ---- */}
      <section className="hero-media">
        {/* Video pozadí (volitelné): /img/hero-video.mp4; poster = hero.jpg.
            Chybí-li video, přehrávač drží poster; chybí-li obojí, drží
            gradient z .hero-media. */}
        <video
          className="hero-video"
          autoPlay
          muted
          loop
          playsInline
          poster="/img/hero.jpg"
          aria-hidden="true"
        >
          <source src="/img/hero-video.mp4" type="video/mp4" />
        </video>
        <div className="hero-overlay" aria-hidden="true" />
        <div className="container hero-inner">
          <div className="hero-copy">
            <span className="eyebrow">
              {spec.lead_magnet_name} · {BRAND.name}
            </span>
            <h1>
              {landing.hero_headline ||
                `${spec.lead_magnet_name}: zjistěte, jak jste na tom`}
            </h1>
            <p className="hero-sub">
              {landing.hero_sub ||
                "Pár krátkých otázek vám ukáže, jak jste na tom a co řešit nejdřív. Žádné strašení, jen věcný přehled a doporučení na míru."}
            </p>
            <div className="hero-cta">
              <button
                className="btn btn-gold"
                style={{ marginTop: 10 }}
                onClick={() => setStarted(true)}
              >
                {startLabel}
              </button>
              <p className="hero-note">
                Zabere jen pár minut. Výsledek uvidíte hned a souhrn vám
                pošleme na e-mail.
              </p>
            </div>
          </div>

          <div className="hero-visual">
            <div className="hero-mock" aria-hidden="true" />
          </div>
        </div>
      </section>

      {/* ---- Stats pás překrývající hero (vrstvení + proof) ---- */}
      <div className="container">
        <div className="hero-stats">
          {/* Počet otázek jen když je NÍZKÝ (láká „rychlé"); jinak čas (počet by
              působil jako práce → snižoval konverzi). Zdarma + ihned vždy. */}
          {spec.questions.length <= 8 ? (
            <div className="hero-stat">
              <span className="num">{spec.questions.length}</span>
              <span className="lbl">krátkých otázek</span>
            </div>
          ) : (
            <div className="hero-stat">
              <span className="num">
                ~{Math.max(2, Math.round(spec.questions.length / 6))}{" "}
                <em>min</em>
              </span>
              <span className="lbl">vyplnění</span>
            </div>
          )}
          <div className="hero-stat">
            <span className="num">zdarma</span>
            <span className="lbl">bez závazku</span>
          </div>
          <div className="hero-stat">
            <span className="num">ihned</span>
            <span className="lbl">výsledek na míru</span>
          </div>
        </div>
      </div>

      {/* ---- Co zjistíte: bento grid (1 velká tmavá + 2 různé) ---- */}
      <section className="section">
        <div className="container">
          <span className="eyebrow">Co zjistíte</span>
          <h2 style={{ maxWidth: "22ch" }}>
            Tři věci, které vám výsledek řekne
          </h2>
          <div className="bento">
            <div className="bento-card lead">
              <span className="bento-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="7" />
                  <path d="M21 21l-4.35-4.35" />
                </svg>
              </span>
              <div>
                <h3>{areas[0]?.title || "Co vás trápí"}</h3>
                <p>{areas[0]?.desc || "Kde se problém projevuje nejčastěji a co ho spouští."}</p>
              </div>
            </div>
            <div className="bento-card">
              <span className="bento-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 11l3 3L20 4" />
                  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                </svg>
              </span>
              <h3>{areas[1]?.title || "Co už děláte"}</h3>
              <p>{areas[1]?.desc || "Co z dosavadních řešení funguje a co jen bere čas."}</p>
            </div>
            <div className="bento-card gold">
              <span className="bento-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="9" />
                  <circle cx="12" cy="12" r="5" />
                  <circle cx="12" cy="12" r="1" />
                </svg>
              </span>
              <h3>{areas[2]?.title || "Co s tím dál"}</h3>
              <p>{areas[2]?.desc || "Doporučení sestavené přímo podle vašich odpovědí."}</p>
            </div>
          </div>
        </div>
      </section>

      {/* ---- Funnel-recenze: hodnotí TEST — až ZA bento cards, budují důvěru vyplnit ---- */}
      {(spec.funnel_reviews ?? []).length > 0 && (
        <section className="funnel-reviews">
          <div className="container">
            <span className="eyebrow fr-eyebrow">
              Co říkají ti, co test vyplnili
            </span>
            <div className="reviews-grid">
              {(spec.funnel_reviews ?? []).slice(0, 3).map((r, i) => (
                <figure className="review-card" key={i}>
                  {typeof r.rating === "number" && (
                    <div className="review-stars" aria-label={`${r.rating} z 5`}>
                      {"★".repeat(
                        Math.max(0, Math.min(5, Math.round(r.rating)))
                      )}
                    </div>
                  )}
                  <blockquote>{r.text}</blockquote>
                  <figcaption>
                    <span className="review-avatar" aria-hidden="true">
                      {(r.name || "?").trim().charAt(0).toUpperCase()}
                    </span>
                    <span className="review-meta">
                      <strong>{r.name}</strong>
                      {r.meta ? <span className="review-loc">{r.meta}</span> : null}
                    </span>
                  </figcaption>
                </figure>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ---- Autorita: calm quote band ---- */}
      <section className="quote-band">
        <div className="container">
          <blockquote>
            „Test jsme sestavili tak, abyste hned viděli, kde má smysl řešit
            situaci přednostně a kde zatím ne.“
            <span className="quote-attribution">tým {BRAND.name}</span>
          </blockquote>
        </div>
      </section>

      {/* ---- Kredibilita: autoritní pás s velkými „power" čísly — VLASTNÍ
             archetyp, NE klon split-media níž. Bez fotky (AI halucinuje loga).
             Čísla jsou placeholder — builder je nahradí REÁLNÝMI z productDNA/
             brandDNA (nikdy vymyšlené); bez podkladu piš z reálné praxe. ---- */}
      <section className="section">
        <div className="container">
          <div className="credibility">
            <div className="credibility-body">
              <span className="eyebrow">Kdo test připravil</span>
              <h2>Sestavili ho lidé, kteří to řeší v praxi</h2>
              <p className="muted" style={{ maxWidth: "48ch" }}>
                {landing.authority ||
                  `Za testem stojí tým ${BRAND.name}. Otázky vycházejí z reálné praxe, ne z letáku — proto vám ukážou, kde má smysl řešit situaci přednostně a kde zatím ne.`}
              </p>
              <div className="cred-stats">
                <div className="cred-stat">
                  <span className="num">15+</span>
                  <span className="lbl">let zkušeností v oboru</span>
                </div>
                <div className="cred-stat">
                  <span className="num">4 000+</span>
                  <span className="lbl">vyřešených případů</span>
                </div>
                <div className="cred-stat">
                  <span className="num">100&nbsp;%</span>
                  <span className="lbl">na základě vašich odpovědí</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---- Jak to probíhá: split kroky + foto ---- */}
      <section className="section">
        <div className="container split-grid">
          <div>
            <span className="eyebrow">Jak to probíhá</span>
            <h2>
              {spec.questions.length} krátkých otázek, na konci přehledný
              výsledek
            </h2>
            <div className="steps">
              <div className="step">
                <span className="step-num">01</span>
                <div>
                  <h3>Odpovíte na otázky</h3>
                  <p>
                    Pár minut, bez přemýšlení nad správnou odpovědí. Jde o
                    vaši situaci, ne o test znalostí.
                  </p>
                </div>
              </div>
              <div className="step">
                <span className="step-num">02</span>
                <div>
                  <h3>Uvidíte výsledek hned</h3>
                  <p>
                    Vyhodnocení a klíčové poznatky se zobrazí okamžitě po
                    vyplnění.
                  </p>
                </div>
              </div>
              <div className="step">
                <span className="step-num">03</span>
                <div>
                  <h3>Dostanete doporučení na míru</h3>
                  <p>
                    Kompletní rozbor a další kroky připravené přímo podle
                    vašich odpovědí vám pošleme na e-mail.
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div className="split-media" aria-hidden="true" />
        </div>
      </section>

      {/* ---- Závěrečný CTA panel: dense close ---- */}
      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          <div className="cta-panel">
            <span className="eyebrow">{spec.lead_magnet_name}</span>
            <h2>Zjistěte ještě dnes, jak jste na tom</h2>
            <p>
              Vyhodnocení máte hned a doporučení na míru v e-mailu. Vše
              nezávazně a bez tlaku.
            </p>
            <button className="btn btn-gold" onClick={() => setStarted(true)}>
              {startLabel}
            </button>
          </div>
        </div>
      </section>

      <div className="footer-note">
        {BRAND.name} · {spec.lead_magnet_name}
      </div>
    </main>
  );
}
