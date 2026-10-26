/* text-motion.ts — engine vrstvy „Text v pohybu" (vibe-builder).
 *
 * ŠABLONA: zkopíruj do <slug>/src/lib/text-motion.ts. Engine řeší MECHANIKU
 * (split, mask, cleanup, a11y, reduced-motion, výkon) — VZHLED přichází ze
 * SIGNATURE v lib/motion.config.ts (generuje concept-seed.py, brána hlídá lock).
 * Helpery volej UVNITŘ useGSAP(() => {...}, { scope }) — revert řeší kontext.
 *
 * Invarianty (nejsou parametrizovatelné — drží čitelnost a 60 fps):
 * - výchozí stav v markupu = plný viditelný text; from-stavy nastavuje JS
 * - prefers-reduced-motion → okamžitý finální stav, žádný tween
 * - dlouhé nadpisy nad SIG.maxChars degradují z words na lines
 * - scrubText mění JEN opacity/barvu, nikdy pozici; plný stav do 60 % rozsahu
 * - mask wrappery dostávají padding kvůli českým háčkům (Ř/Ů/Á)
 * - will-change jen po dobu tweenu
 * - text se NIKDY nehýbe do stran ani nenaklání (skew/velocity osy a
 *   houpání jsou zakázané) — kinetika žije v nástupu, stojící text stojí
 */
import gsap from "gsap";
import { SplitText } from "gsap/SplitText";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { brandEase, DUR, SIGNATURE } from "./motion.config";

// SIGNATURE je v configu `as const` (literály per svět) — pro obecný engine
// rozšiř na šířkové typy, jinak porovnání s jinými flavory nezkompiluje
const SIG = SIGNATURE as unknown as {
  unit: "words" | "lines"; verb: string; origin: string;
  tempo: number; ease: string; overshoot: number; distort: string;
  accentDelay: number; maxChars: number;
};

gsap.registerPlugin(SplitText, ScrollTrigger);

type Target = string | Element;
interface Opts {
  accent?: string;          // selektor zvýrazněného slova (span) — mikro-timing
  trigger?: Target;         // ScrollTrigger trigger (default: target)
  start?: string;           // default "top 82%"
  delay?: number;
}

const reduced = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Runtime potvrzení, že se motion engine opravdu rozběhl.
 *
 *  Brány (design-gate.js, visual-gate.mjs) čekají `data-motion-ready` na prvku
 *  s `data-motion`. Marker smí nastavit VÝHRADNĚ tenhle engine a až po skutečné
 *  aktivaci — nikdy se nepíše do markupu, jinak by potvrzoval pohyb, který
 *  neběží. Při reduced-motion je finální stav dosažený hned (žádný tween),
 *  takže marker patří i tam: „hotovo" znamená hotovo, ne „animovalo se". */
function markReady(target: Element | null) {
  if (target) (target as HTMLElement).dataset.motionReady = "1";
}

/** from-vars podle slovesa podpisu — jiná transformní gramatika per svět. */
function verbFrom(verb: string, overshoot: number): gsap.TweenVars {
  switch (verb) {
    case "clipUp":      return { yPercent: 110 };                      // v masce
    case "wipe":        return { clipPath: "inset(0 100% 0 0)" };
    case "blurIn":      return { filter: "blur(12px)", opacity: 0 };
    case "weight":      return { opacity: 0, "--wght": 200 } as gsap.TweenVars;
    default:            return { yPercent: 60, opacity: 0 };           // rise
  }
}

function staggerFrom(origin: string): gsap.StaggerVars["from"] {
  return origin === "start" ? 0 : (origin as "center" | "edges" | "random");
}

function guardMask(split: SplitText) {
  // háčky na verzálkách nesmí oříznout mask overflow
  for (const m of (split as unknown as { masks?: Element[] }).masks ?? []) {
    (m as HTMLElement).style.paddingBlock = "0.18em";
    (m as HTMLElement).style.marginBlock = "-0.18em";
  }
}

function accentKick(accent: string | undefined, scopeEl: Element | null) {
  if (!accent || !scopeEl) return;
  const el = scopeEl.querySelector(accent);
  if (el) gsap.from(el, { color: "inherit", duration: DUR.fast, delay: SIG.accentDelay, ease: brandEase });
}

/** Hero nadpis — words/lines choreografie. <h1 data-motion="words"> povinné.
 *  ZÁKAZ animace po písmenech (chars) — viz 10-motion-web.md. */
export function heroWords(target: Target, o: Opts = {}) {
  const el = typeof target === "string" ? document.querySelector(target) : target;
  if (!el) return null;
  if (reduced()) { markReady(el); return null; }
  const text = el.textContent ?? "";
  const unit: "words" | "lines" =
    SIG.unit === "words" && text.length > SIG.maxChars ? "lines" : SIG.unit;
  (el as HTMLElement).style.fontKerning = "none";
  return SplitText.create(el, {
    type: unit === "lines" ? "lines" : `${unit}`,
    mask: SIG.verb === "clipUp" ? unit : undefined,
    autoSplit: true,
    aria: "auto",
    onSplit(self) {
      guardMask(self);
      const parts = unit === "lines" ? self.lines : self.words;
      const tl = gsap.timeline({ delay: o.delay ?? 0.1, onStart: () => gsap.set(parts, { willChange: "transform" }), onComplete: () => gsap.set(parts, { willChange: "auto", clearProps: "filter" }) });
      tl.from(parts, {
        ...verbFrom(SIG.verb, SIG.overshoot),
        duration: DUR.base,
        ease: brandEase,
        stagger: { each: 0.06, from: staggerFrom(SIG.origin) },
      });
      accentKick(o.accent, el);
      markReady(el); // engine běží — teprve teď smí brána vidět potvrzení
      return tl; // vrácená animace = autoSplit ji při resize správně přestaví
    },
  });
}

/** Sekční h2 — řádky v masce. <h2 data-motion="lines"> povinné. */
export function linesMask(target: Target, o: Opts = {}) {
  const el = typeof target === "string" ? document.querySelector(target) : target;
  if (!el) return null;
  if (reduced()) { markReady(el); return null; }
  return SplitText.create(el, {
    type: "lines",
    mask: "lines",
    autoSplit: true,
    aria: "auto",
    onSplit(self) {
      guardMask(self);
      markReady(el); // engine běží — teprve teď smí brána vidět potvrzení
      return gsap.from(self.lines, {
        yPercent: 110,
        duration: DUR.base,
        ease: brandEase,
        stagger: 0.08,
        scrollTrigger: { trigger: (o.trigger as Element) ?? el, start: o.start ?? "top 82%" },
        onComplete: () => accentKick(o.accent, el),
      });
    },
  });
}

/** Scrub-text: slova se rozsvěcují rolováním. JEN opacity — text se při
 *  čtení nesmí hýbat. Plný stav do 60 % rozsahu triggeru. */
export function scrubText(target: Target, o: Opts = {}) {
  const el = typeof target === "string" ? document.querySelector(target) : target;
  if (!el) return null;
  if (reduced()) return null;
  return SplitText.create(el, {
    type: "words",
    aria: "auto",
    autoSplit: true,
    onSplit(self) {
      return gsap.from(self.words, {
        opacity: 0.22,
        stagger: 0.04,
        ease: "none",
        scrollTrigger: {
          trigger: (o.trigger as Element) ?? el,
          start: o.start ?? "top 75%",
          end: "top 30%",   // dojezd dřív, než čtenář dočte — žádné honění světla
          scrub: true,
        },
      });
    },
  });
}

/** Counter velkých čísel — tabular-nums na cíli je povinnost (brána). */
export function countUp(target: Target, to: number, o: Opts & { decimals?: number; suffix?: string } = {}) {
  const el = typeof target === "string" ? document.querySelector(target) : target;
  if (!el) return null;
  const obj = { v: 0 };
  const render = () => { (el as HTMLElement).textContent = obj.v.toFixed(o.decimals ?? 0) + (o.suffix ?? ""); };
  if (reduced()) { obj.v = to; render(); return null; }
  return gsap.to(obj, {
    v: to, duration: DUR.slow, ease: brandEase, onUpdate: render,
    scrollTrigger: { trigger: (o.trigger as Element) ?? el, start: o.start ?? "top 85%" },
  });
}

/** Slovní ruleta — jedno slovo nadpisu střídá 2–4 varianty (mask, klid okolo). */
export function wordSwap(target: Target, words: string[], o: Opts & { hold?: number } = {}) {
  const el = typeof target === "string" ? document.querySelector(target) : target;
  if (!el || reduced() || words.length < 2) return null;
  const wrap = document.createElement("span");
  wrap.style.cssText = "display:inline-block;overflow:clip;vertical-align:bottom;padding-block:0.18em;margin-block:-0.18em";
  const inner = document.createElement("span");
  inner.style.display = "inline-block";
  inner.textContent = words[0];
  wrap.appendChild(inner);
  el.replaceChildren(wrap);
  const tl = gsap.timeline({ repeat: -1, repeatDelay: o.hold ?? 2.2 });
  for (let i = 1; i <= words.length; i++) {
    tl.to(inner, { yPercent: -110, duration: DUR.fast, ease: brandEase })
      .add(() => { inner.textContent = words[i % words.length]; })
      .fromTo(inner, { yPercent: 110 }, { yPercent: 0, duration: DUR.fast, ease: brandEase })
      .to({}, { duration: o.hold ?? 2.2 });
  }
  return tl;
}

/* velocityAxis (skew/wght dle rychlosti scrollu) ODSTRANĚN — text
   naklánějící se do stran působí neprofesionálně. Zákaz platí trvale. */
