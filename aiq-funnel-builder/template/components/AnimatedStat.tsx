"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Power číslo s count-up animací při najetí do viewportu.
 * Vytáhne první celé číslo z `value` (např. „40 let", „15 milionů", „10 000")
 * a odpočítá ho 0 → N (exponenciální ease-out), zbytek textu (jednotka) drží.
 *
 * GRACEFUL: initial/SSR render = PLNÉ číslo. Když JS/animace neběží (skrytý tab,
 * vypnutý JS), zůstane plné číslo — nikdy „0". Animace jen na klientovi, po
 * najetí do viewportu: krátce srazí na 0 a nabíhá zpět.
 */
export default function AnimatedStat({ value }: { value: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const match = value.match(/\d[\d \s]*\d|\d/);
  const raw = match ? match[0] : null;
  const target = raw ? parseInt(raw.replace(/\D/g, ""), 10) : NaN;
  const animatable = raw != null && Number.isFinite(target) && target > 1;
  const [display, setDisplay] = useState(value);

  useEffect(() => {
    if (!animatable || !ref.current) return;
    // Respektuj prefers-reduced-motion — číslo nech rovnou na cílové hodnotě.
    if (
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    )
      return;
    const el = ref.current;
    let raf = 0;
    const fmt = (n: number) => value.replace(raw!, n.toLocaleString("cs-CZ"));
    const run = () => {
      const dur = 1200;
      const t0 = performance.now();
      const step = (t: number) => {
        const p = Math.min(1, (t - t0) / dur);
        const eased = 1 - Math.pow(1 - p, 3);
        setDisplay(fmt(Math.round(eased * target)));
        if (p < 1) raf = requestAnimationFrame(step);
        else setDisplay(value);
      };
      raf = requestAnimationFrame(step);
    };
    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          io.disconnect();
          run();
        }
      },
      { threshold: 0.4 }
    );
    io.observe(el);
    return () => {
      io.disconnect();
      cancelAnimationFrame(raf);
    };
  }, [animatable, target, value, raw]);

  return (
    <span ref={ref} className="num">
      {display}
    </span>
  );
}
