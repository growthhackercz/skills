"use client";

import { useEffect, useState } from "react";

export interface CarouselSlide {
  img: string;
  title: string;
  desc?: string;
}

/**
 * Produktový carousel — PLNÁ ŠÍŘKA, přesně 3 velké karty na desktopu (~100px
 * gutter, šipky samostatně v gutteru), jen obrázky (bez render textů). Klik na
 * kartu = zvětšení obrázku do POPUP (lightbox) — karty nesou detailní text.
 * Tečky = počet karet, jede dokola (autoplay + seamless loop). 1 a kus na mobilu.
 */
export default function SalesCarousel({ slides }: { slides: CarouselSlide[] }) {
  const n = slides.length;
  const [i, setI] = useState(0);
  const [anim, setAnim] = useState(true);
  const [zoom, setZoom] = useState<string | null>(null);
  const loop = [...slides, ...slides];

  // autoplay (pauza při otevřeném lightboxu)
  useEffect(() => {
    if (n <= 1 || zoom) return;
    const t = setInterval(() => setI((p) => p + 1), 4500);
    return () => clearInterval(t);
  }, [n, zoom]);

  useEffect(() => {
    if (i === n) {
      const t = setTimeout(() => {
        setAnim(false);
        setI(0);
      }, 560);
      return () => clearTimeout(t);
    }
  }, [i, n]);
  useEffect(() => {
    if (!anim) {
      const r = requestAnimationFrame(() => setAnim(true));
      return () => cancelAnimationFrame(r);
    }
  }, [anim]);

  // lightbox: Esc zavře + zamkne scroll
  useEffect(() => {
    if (!zoom) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setZoom(null);
    };
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [zoom]);

  const active = ((i % n) + n) % n;
  const prev = () => setI((p) => (p <= 0 ? n - 1 : p - 1));
  const next = () => setI((p) => p + 1);

  return (
    <div className="sp-car sp-car--full">
      <div className="sp-car__stage">
        <button className="sp-car__arrow sp-car__arrow--l" onClick={prev} aria-label="Předchozí" type="button">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6" /></svg>
        </button>
        <div className="sp-car__viewport">
          <div
            className="sp-car__track"
            style={{
              transform: `translateX(calc(-${i} * (var(--card) + var(--gap))))`,
              transition: anim ? undefined : "none",
            }}
          >
            {loop.map((s, k) => (
              <figure className="sp-car__card" key={k}>
                <button
                  className="sp-car__zoom"
                  onClick={() => setZoom(s.img)}
                  aria-label={`Zvětšit: ${s.title}`}
                  type="button"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={s.img} alt={s.title} loading="lazy" />
                </button>
              </figure>
            ))}
          </div>
        </div>
        <button className="sp-car__arrow sp-car__arrow--r" onClick={next} aria-label="Další" type="button">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18l6-6-6-6" /></svg>
        </button>
      </div>
      <div className="sp-car__dots">
        {slides.map((_, k) => (
          <button
            key={k}
            className={`sp-car__dot${k === active ? " is-active" : ""}`}
            onClick={() => setI(k)}
            aria-label={`Snímek ${k + 1}`}
            type="button"
          />
        ))}
      </div>

      {zoom && (
        <div className="sp-car__lb" onClick={() => setZoom(null)} role="dialog" aria-modal="true">
          <button className="sp-car__lb-close" onClick={() => setZoom(null)} aria-label="Zavřít" type="button">×</button>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={zoom} alt="" onClick={(e) => e.stopPropagation()} />
        </div>
      )}
    </div>
  );
}
