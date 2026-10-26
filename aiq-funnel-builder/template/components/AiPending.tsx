"use client";

import { useEffect, useState, type CSSProperties } from "react";
import { useRouter } from "next/navigation";

/**
 * AI (spodní) zóna magnetu, dokud se nedogeneruje. Kickne personalizaci
 * (idempotentně), polluje stav a po dokončení obnoví stránku (router.refresh)
 * — server pak vyrenderuje hotové AI bloky místo tohoto loaderu. Deterministická
 * TOP zóna nad tímto zůstává vidět celou dobu.
 */
const PHASES = [
  "Čtu vaše odpovědi…",
  "Hledám souvislosti mezi nimi…",
  "Sestavuji hloubkový rozbor na míru…",
  "Ladím doporučení právě pro vás…",
];
const TIMEOUT_MS = 200000;

export default function AiPending({
  contactId,
  color,
}: {
  contactId: string;
  color: string;
}) {
  const router = useRouter();
  const [phase, setPhase] = useState(0);
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    let alive = true;
    const started = Date.now();

    // Kick (idempotentní — duplicitní kick řeší lease uvnitř runPersonalization).
    fetch("/api/personalize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ contactId }),
    }).catch(() => {});

    const phaseTimer = setInterval(
      () => setPhase((p) => Math.min(p + 1, PHASES.length - 1)),
      8000
    );
    const poll = setInterval(async () => {
      if (!alive) return;
      if (Date.now() - started > TIMEOUT_MS) {
        setTimedOut(true);
        clearInterval(poll);
        clearInterval(phaseTimer);
        return;
      }
      try {
        const r = await fetch(
          `/api/personalize/status?c=${encodeURIComponent(contactId)}`,
          { cache: "no-store" }
        );
        const j = await r.json();
        if (j.status === "ready") {
          clearInterval(poll);
          clearInterval(phaseTimer);
          router.refresh();
        }
      } catch {
        /* poll dál */
      }
    }, 4000);

    return () => {
      alive = false;
      clearInterval(poll);
      clearInterval(phaseTimer);
    };
  }, [contactId, router]);

  return (
    <section
      className="mag2-section mag2-pending"
      style={{ ["--band" as string]: color } as CSSProperties}
    >
      {!timedOut ? (
        <>
          <div className="mag2-spinner" aria-hidden="true" />
          <p className="mag2-pending-title">
            Připravujeme vaši hloubkovou analýzu na míru…
          </p>
          <p className="mag2-pending-phase">{PHASES[phase]}</p>
          <p className="mag2-pending-note">
            Nahoře máte svůj výsledek hned. Zbytek se dogeneruje během chvíle —
            stránku nezavírejte.
          </p>
        </>
      ) : (
        <p className="mag2-pending-title">
          Vaše analýza se dokončuje na pozadí — za okamžik ji najdete tady i ve
          svém e-mailu.
        </p>
      )}
    </section>
  );
}
