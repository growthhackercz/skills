"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

const PHASES = [
  "Porovnáváme kombinace vašich odpovědí…",
  "Hledáme souvislosti mezi tím, co jste napsali…",
  "Vyhodnocujeme, kde máte největší rezervy…",
  "Počítáme, co to pro vás konkrétně znamená…",
  "Sestavujeme doporučení na míru…",
  "Připravujeme kompletní analýzu…",
];

/**
 * Rozestupy mezi dotazy na stav, v ms. Každý dotaz = jeden GET do GHL a ten má
 * limit 100 req / 10 s na lokaci, takže při náporu z reklamy se pevný interval
 * sčítá napříč leady. Hustě se ptáme v okně, kdy generace typicky dobíhá, pak
 * řidčeji. Poslední hodnota se opakuje až do TIMEOUT_MS (cadence pokrývá ~3 min).
 * Hlubší Sonnet analýza trvá průměrně ~3 min — proto delší okno než dřív.
 */
const POLL_STEPS_MS = [
  2000, 3000, 3000, 4000, 4000, 5000, 6000, 8000, 10000, 12000, 15000, 15000,
  15000, 15000, 15000, 15000,
];
const TIMEOUT_MS = 180000;

type KickerStatus = "running" | "ready" | "timeout";

/**
 * Po mountu spustí POST /api/personalize a ptá se na stav s narůstajícími
 * rozestupy (max 60 s). ready → karta s odkazem na kompletní analýzu;
 * timeout → pošleme e-mailem.
 *
 * Když server při renderu už viděl tag „ready" (initialReady), nepošle se
 * jediný request — hotová personalizace se zobrazí rovnou.
 */
export default function PersonalizeKicker({
  contactId,
  initialReady = false,
}: {
  contactId: string;
  initialReady?: boolean;
}) {
  const [status, setStatus] = useState<KickerStatus>(
    initialReady ? "ready" : "running"
  );
  const [phase, setPhase] = useState(0);
  const doneRef = useRef(false);

  useEffect(() => {
    // Personalizace byla hotová už při renderu stránky → nic nefetchujeme.
    if (initialReady) return;

    let cancelled = false;
    let pollTimer: ReturnType<typeof setTimeout> | undefined;
    const startedAt = Date.now();

    function markReady() {
      if (cancelled || doneRef.current) return;
      doneRef.current = true;
      setStatus("ready");
    }

    function markTimeout() {
      if (cancelled || doneRef.current) return;
      doneRef.current = true;
      setStatus("timeout");
    }

    // Fázový progress text (6 fází rozprostřených přes ~3 min).
    const phaseTimer = setInterval(() => {
      setPhase((p) => Math.min(p + 1, PHASES.length - 1));
    }, 26000);

    // Kick: spustí generaci (server je idempotentní).
    void (async () => {
      try {
        const res = await fetch("/api/personalize", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ contactId }),
        });
        if (res.ok) {
          const j = (await res.json()) as { status?: string };
          if (j.status === "ready") markReady();
        }
      } catch {
        // Poll rozhodne — případný timeout ukáže e-mailový fallback.
      }
    })();

    // Poll stavových tagů s narůstajícím rozestupem.
    let step = 0;

    function scheduleNext() {
      if (cancelled || doneRef.current) return;
      const delay = POLL_STEPS_MS[step] ?? POLL_STEPS_MS[POLL_STEPS_MS.length - 1];
      step += 1;
      pollTimer = setTimeout(poll, delay);
    }

    async function poll() {
      if (cancelled || doneRef.current) return;
      if (Date.now() - startedAt > TIMEOUT_MS) {
        markTimeout();
        return;
      }
      try {
        const res = await fetch(
          `/api/personalize/status?c=${encodeURIComponent(contactId)}`
        );
        if (res.ok) {
          const j = (await res.json()) as { status?: string };
          if (j.status === "ready") {
            markReady();
            return;
          }
        }
      } catch {
        // Spadlý dotaz nevadí, zkusíme to znovu v dalším kroku.
      }
      scheduleNext();
    }

    scheduleNext();

    return () => {
      cancelled = true;
      clearInterval(phaseTimer);
      if (pollTimer) clearTimeout(pollTimer);
    };
  }, [contactId, initialReady]);

  if (status === "ready") {
    return (
      <div className="kicker-card kicker-ready">
        <span className="eyebrow" style={{ marginBottom: 8 }}>
          Hotovo
        </span>
        <h3>Vaše kompletní analýza je připravena</h3>
        <p className="muted" style={{ marginBottom: 14 }}>
          Rozbor vašich odpovědí, co děláte dobře, hlavní rezervy a kroky, které
          můžete udělat hned.
        </p>
        <Link
          href={`/magnet/${encodeURIComponent(contactId)}`}
          className="btn"
        >
          Otevřít kompletní analýzu
        </Link>
      </div>
    );
  }

  if (status === "timeout") {
    return (
      <div className="kicker-card">
        <h3>Analýzu vám pošleme e-mailem</h3>
        <p className="muted" style={{ margin: 0 }}>
          Příprava trvá o chvíli déle. Jakmile bude kompletní analýza hotová,
          přijde vám odkaz e-mailem — nemusíte tu čekat.
        </p>
      </div>
    );
  }

  return (
    <div className="kicker-card" aria-live="polite">
      <div className="kicker-progress">
        <span className="spinner" aria-hidden="true" />
        <span>{PHASES[phase]}</span>
      </div>
      <p className="muted" style={{ margin: "10px 0 0", fontSize: 14 }}>
        Připravujeme hloubkovou analýzu na míru — čteme každou vaši odpověď.
        Obvykle to zabere 2–3 minuty. Nemusíte tu čekat, výsledek vám dorazí
        i e-mailem.
      </p>
      {/* Deterministic-first: výsledek je k nahlédnutí hned, AI výklad doteče. */}
      <Link
        href={`/magnet/${encodeURIComponent(contactId)}`}
        className="btn btn-ghost"
        style={{ marginTop: 14 }}
      >
        Zatím se podívat na svůj výsledek
      </Link>
    </div>
  );
}
