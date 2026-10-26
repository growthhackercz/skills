"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { spec } from "../lib/spec";
import type { Question } from "../lib/spec";

type AnswerValue = string | string[] | undefined;
type AnswersState = Record<string, AnswerValue>;

interface ContactState {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  /** Souhlas se zasláním výsledku a doporučení e-mailem. */
  consent: boolean;
  /** Souhlas se zpracováním odpovědí pro analýzu (text per funnel v spec.consent_text). */
  consentProcessing: boolean;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Text souhlasu se zpracováním odpovědí. Píše ho strategie per funnel do
 * `spec.consent_text`, protože musí odpovídat tomu, na co se kvíz OPRAVDU ptá.
 *
 * Výchozí text je záměrně neutrální: šablona nesmí za klienta tvrdit, že
 * zpracovává citlivé údaje (zdraví, děti, finance) — u funnelu, který se na ně
 * neptá, by to bylo nepravdivé a zbytečně by odrazovalo od vyplnění.
 */
const CONSENT_TEXT =
  spec.consent_text?.trim() ||
  "Souhlasím se zpracováním odpovědí pro vytvoření personalizované analýzy — viz";

/** Klíč pro obnovení rozpracovaných odpovědí (localStorage). */
const STORAGE_KEY = `${spec.funnel_slug}-quiz-v1`;

interface StoredState {
  step?: number;
  answers?: AnswersState;
  contact?: Partial<Pick<ContactState, "firstName" | "lastName" | "email" | "phone">>;
}

export default function Quiz({ onClose }: { onClose?: () => void }) {
  const questions = spec.questions;
  const totalSteps = questions.length + 1; // +1 for the contact step (always last)

  const [step, setStep] = useState(0); // 0..questions.length-1 = questions, questions.length = contact
  const [answers, setAnswers] = useState<AnswersState>({});
  // Honeypot: skryté pole, které vidí jen bot. Legitimní uživatel ho nevyplní.
  const [website, setWebsite] = useState("");
  const [contact, setContact] = useState<ContactState>({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    consent: false,
    consentProcessing: false,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);
  /** Rozpracovaný kvíz jsme obnovili → řekneme to nahlas (viz níže). */
  const [restored, setRestored] = useState(false);

  // ---- Obnovení rozpracovaných odpovědí (po mountu, kvůli hydrataci) ----
  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const stored = JSON.parse(raw) as StoredState;
        if (stored.answers && typeof stored.answers === "object") {
          setAnswers(stored.answers);
        }
        if (typeof stored.step === "number") {
          setStep(Math.min(Math.max(stored.step, 0), questions.length));
        }
        // Obnovení hlásíme jen když je co obnovovat — jinak by lišta naskočila
        // i člověku, který kvíz jen otevřel a zavřel na první otázce.
        const hasAnswers =
          !!stored.answers && Object.keys(stored.answers).length > 0;
        if (hasAnswers || (stored.step ?? 0) > 0) setRestored(true);
        if (stored.contact && typeof stored.contact === "object") {
          setContact((prev) => ({
            ...prev,
            firstName: stored.contact?.firstName ?? "",
            lastName: stored.contact?.lastName ?? "",
            email: stored.contact?.email ?? "",
            phone: stored.contact?.phone ?? "",
            // Souhlasy se NIKDY neobnovují — musí být zaškrtnuté vědomě.
            consent: false,
            consentProcessing: false,
          }));
        }
      }
    } catch {
      /* poškozený stav ignorujeme */
    }
    setHydrated(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- Průběžné ukládání (bez souhlasů) ----
  useEffect(() => {
    if (!hydrated) return;
    try {
      const stored: StoredState = {
        step,
        answers,
        contact: {
          firstName: contact.firstName,
          lastName: contact.lastName,
          email: contact.email,
          phone: contact.phone,
        },
      };
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
    } catch {
      /* plné/nedostupné storage neblokuje kvíz */
    }
  }, [hydrated, step, answers, contact]);

  /** „Začít znovu" — zahodí obnovený rozpracovaný kvíz a vrátí se na start. */
  function restartQuiz() {
    try {
      window.localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* nedostupné storage nevadí, stav resetujeme i tak */
    }
    setAnswers({});
    setStep(0);
    setContact({
      firstName: "",
      lastName: "",
      email: "",
      phone: "",
      consent: false,
      consentProcessing: false,
    });
    setWebsite(""); // honeypot: ať oběť autofillu není trvale zablokovaná
    setError(null);
    setRestored(false);
  }

  const isContactStep = step === questions.length;
  const currentQuestion: Question | undefined = isContactStep
    ? undefined
    : questions[step];

  // Validity is derived from current state on every render — no stale closure.
  const canProceed = useMemo(() => {
    if (isContactStep) {
      const okName = contact.firstName.trim().length > 0;
      const okEmail = EMAIL_RE.test(contact.email.trim());
      return okName && okEmail && contact.consent && contact.consentProcessing;
    }
    if (!currentQuestion) return false;
    // Optional (textarea) questions never block progress.
    if (currentQuestion.type === "textarea") return true;
    const v = answers[currentQuestion.id];
    if (Array.isArray(v)) return v.length > 0;
    return typeof v === "string" && v.length > 0;
  }, [isContactStep, currentQuestion, answers, contact]);

  // Auto-advance (UX 2.0): u yesno/single se po výběru pokračuje automaticky
  // (~300 ms na "selected" animaci). Hodnota jde přímo z onClick parametru,
  // krok přes funkční update — žádný stale closure. Timer se čistí při
  // unmountu i ručním kliku Zpět.
  const advanceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => () => {
    if (advanceTimer.current) clearTimeout(advanceTimer.current);
  }, []);

  function setSingle(qid: string, value: string) {
    setAnswers((prev) => ({ ...prev, [qid]: value }));
    if (advanceTimer.current) clearTimeout(advanceTimer.current);
    advanceTimer.current = setTimeout(() => {
      setError(null);
      setStep((s) => Math.min(s + 1, questions.length));
    }, 300);
  }

  function toggleMulti(qid: string, value: string) {
    setAnswers((prev) => {
      const cur = Array.isArray(prev[qid]) ? (prev[qid] as string[]) : [];
      const next = cur.includes(value)
        ? cur.filter((x) => x !== value)
        : [...cur, value];
      return { ...prev, [qid]: next };
    });
  }

  function setText(qid: string, value: string) {
    setAnswers((prev) => ({ ...prev, [qid]: value }));
  }

  function goNext() {
    setError(null);
    if (!canProceed) return;
    if (isContactStep) {
      void submit();
      return;
    }
    setStep((s) => Math.min(s + 1, questions.length));
  }

  function goBack() {
    if (advanceTimer.current) clearTimeout(advanceTimer.current);
    setError(null);
    setStep((s) => Math.max(s - 1, 0));
  }

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          answers,
          website, // honeypot — server vyplněný požadavek odmítne bez zápisu
          contact: {
            firstName: contact.firstName.trim(),
            lastName: contact.lastName.trim(),
            email: contact.email.trim(),
            phone: contact.phone.trim(),
            consent: contact.consent,
            consentProcessing: contact.consentProcessing,
          },
        }),
      });

      if (!res.ok) {
        throw new Error(`Odeslání se nezdařilo (${res.status}).`);
      }

      const data = (await res.json()) as { contactId?: string };
      if (!data.contactId) {
        throw new Error("Server nevrátil identifikátor kontaktu.");
      }

      // Rozpracovaný audit je odeslaný — úklid.
      try {
        window.localStorage.removeItem(STORAGE_KEY);
      } catch {
        /* ignore */
      }

      // Čistá URL bez tokenu — contactId (náhodné GHL id) je capability klíč.
      window.location.href = `/vysledek?c=${encodeURIComponent(
        data.contactId
      )}`;
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Něco se pokazilo. Zkuste to prosím znovu."
      );
      setSubmitting(false);
    }
  }

  // Kontaktní krok NENÍ otázka — počet otázek = questions.length, ať landing
  // („N otázek") a kvíz ukazují totéž. Na kontaktu se místo „Otázka X z N"
  // ukáže „Poslední krok".
  const stepLabel = isContactStep
    ? "Poslední krok"
    : `Otázka ${step + 1} z ${questions.length}`;
  const progressPct = ((step + 1) / totalSteps) * 100;

  const showNextButton =
    isContactStep ||
    (currentQuestion &&
      (currentQuestion.type === "multi" || currentQuestion.type === "textarea"));

  return (
    <div className="quiz-overlay" role="dialog" aria-modal="true">
      <div className="quiz-card quiz-modal">
        <div className="quiz-head">
          <div className="progress-label">{stepLabel}</div>
          {onClose && (
            <button
              type="button"
              className="quiz-close"
              aria-label="Zavřít (rozpracované odpovědi zůstanou uložené)"
              onClick={onClose}
            >
              ×
            </button>
          )}
        </div>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{ width: `${progressPct}%` }}
          />
        </div>

        {/* Obnovený rozpracovaný kvíz — řekneme to nahlas. Bez toho lead spadne
            doprostřed s předvybranou odpovědí a vypadá to, že mu výsledek
            předpřipravujeme. */}
        {restored && (
          <div className="quiz-restored" role="status">
            <span>Navázali jsme tam, kde jste skončili.</span>
            <button
              type="button"
              className="quiz-restart"
              onClick={restartQuiz}
            >
              Začít znovu
            </button>
          </div>
        )}

        <div className="quiz-step-anim" key={step}>
        {isContactStep ? (
          <ContactStep
            contact={contact}
            onChange={setContact}
            website={website}
            onWebsiteChange={setWebsite}
          />
        ) : (
          currentQuestion && (
            <QuestionStep
              question={currentQuestion}
              value={answers[currentQuestion.id]}
              onSingle={(v) => setSingle(currentQuestion.id, v)}
              onToggle={(v) => toggleMulti(currentQuestion.id, v)}
              onText={(v) => setText(currentQuestion.id, v)}
            />
          )
        )}

        </div>

        {error && <div className="error-msg">{error}</div>}

        <div className="quiz-nav">
          {step > 0 ? (
            <button
              className="btn btn-ghost"
              onClick={goBack}
              disabled={submitting}
            >
              Zpět
            </button>
          ) : (
            <span />
          )}

          {showNextButton ? (
            <button
              className="btn"
              onClick={goNext}
              disabled={!canProceed || submitting}
            >
              {isContactStep
                ? submitting
                  ? "Odesílám…"
                  : "Zobrazit můj výsledek"
                : currentQuestion?.type === "textarea" &&
                    !(typeof answers[currentQuestion.id] === "string" &&
                      (answers[currentQuestion.id] as string).length > 0)
                  ? "Přeskočit"
                  : "Pokračovat"}
            </button>
          ) : (
            <span className="auto-hint">Vyberte odpověď, pokračujeme hned</span>
          )}
        </div>
      </div>
    </div>
  );
}

/* ---------------- Question step ---------------- */

function QuestionStep({
  question,
  value,
  onSingle,
  onToggle,
  onText,
}: {
  question: Question;
  value: AnswerValue;
  onSingle: (v: string) => void;
  onToggle: (v: string) => void;
  onText: (v: string) => void;
}) {
  const selectedArr = Array.isArray(value) ? value : [];
  const selectedStr = typeof value === "string" ? value : "";

  return (
    <div>
      <div className="q-text">{question.text}</div>

      {question.type === "yesno" && (
        <>
          <div className="options two-col">
            {(question.options ?? []).map((opt) => {
              const selected = selectedStr === opt;
              return (
                <button
                  key={opt}
                  type="button"
                  className={`option radio${selected ? " selected" : ""}`}
                  onClick={() => onSingle(opt)}
                  aria-pressed={selected}
                >
                  <span className="mark">{selected ? "●" : ""}</span>
                  {opt}
                </button>
              );
            })}
          </div>
        </>
      )}

      {question.type === "single" && (
        <>
          <div className="options">
            {(question.options ?? []).map((opt) => {
              const selected = selectedStr === opt;
              return (
                <button
                  key={opt}
                  type="button"
                  className={`option radio${selected ? " selected" : ""}`}
                  onClick={() => onSingle(opt)}
                  aria-pressed={selected}
                >
                  <span className="mark">{selected ? "●" : ""}</span>
                  {opt}
                </button>
              );
            })}
          </div>
        </>
      )}

      {question.type === "multi" && (
        <>
          <div className="q-hint">Můžete vybrat více možností.</div>
          <div className="options">
            {(question.options ?? []).map((opt) => {
              const selected = selectedArr.includes(opt);
              return (
                <button
                  key={opt}
                  type="button"
                  className={`option${selected ? " selected" : ""}`}
                  onClick={() => onToggle(opt)}
                  aria-pressed={selected}
                >
                  <span className="mark">{selected ? "✓" : ""}</span>
                  {opt}
                </button>
              );
            })}
          </div>
        </>
      )}

      {question.type === "textarea" && (
        <>
          <div className="q-hint">Tato otázka je nepovinná.</div>
          <textarea
            className="textarea"
            value={selectedStr}
            onChange={(e) => onText(e.target.value)}
            placeholder="Napište nám pár slov…"
          />
        </>
      )}
    </div>
  );
}

/* ---------------- Contact step (always last) ---------------- */

function ContactStep({
  contact,
  onChange,
  website,
  onWebsiteChange,
}: {
  contact: ContactState;
  onChange: (next: ContactState) => void;
  website: string;
  onWebsiteChange: (value: string) => void;
}) {
  function patch(p: Partial<ContactState>) {
    onChange({ ...contact, ...p });
  }

  return (
    <div>
      <div className="q-text">Kam vám máme poslat výsledek?</div>
      <p className="q-hint" style={{ marginTop: -14 }}>
        Pošleme vám personalizovaný výsledek a doporučení na míru.
      </p>

      <div className="field">
        <label htmlFor="firstName">Jméno *</label>
        <input
          id="firstName"
          type="text"
          autoComplete="given-name"
          value={contact.firstName}
          onChange={(e) => patch({ firstName: e.target.value })}
        />
      </div>

      <div className="field">
        <label htmlFor="lastName">Příjmení</label>
        <input
          id="lastName"
          type="text"
          autoComplete="family-name"
          value={contact.lastName}
          onChange={(e) => patch({ lastName: e.target.value })}
        />
      </div>

      <div className="field">
        <label htmlFor="email">E-mail *</label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          value={contact.email}
          onChange={(e) => patch({ email: e.target.value })}
        />
      </div>

      <div className="field">
        <label htmlFor="phone">Telefon (nepovinné)</label>
        <input
          id="phone"
          type="tel"
          autoComplete="tel"
          value={contact.phone}
          onChange={(e) => patch({ phone: e.target.value })}
        />
      </div>

      {/* Honeypot — skrytý před lidmi, viditelný pro boty. Nevyplněné = člověk. */}
      <input
        type="text"
        name="website"
        tabIndex={-1}
        autoComplete="off"
        aria-hidden="true"
        value={website}
        onChange={(e) => onWebsiteChange(e.target.value)}
        style={{
          position: "absolute",
          left: "-9999px",
          width: 1,
          height: 1,
          opacity: 0,
        }}
      />

      <label className="consent-row">
        <input
          type="checkbox"
          checked={contact.consentProcessing}
          onChange={(e) => patch({ consentProcessing: e.target.checked })}
        />
        <span>
          {CONSENT_TEXT}{" "}
          <a href="/zasady" target="_blank" rel="noopener noreferrer">
            Zásady zpracování
          </a>
          . *
        </span>
      </label>

      <label className="consent-row">
        <input
          type="checkbox"
          checked={contact.consent}
          onChange={(e) => patch({ consent: e.target.checked })}
        />
        <span>
          Souhlasím se zasláním výsledku a souvisejících doporučení e-mailem.
          Souhlas mohu kdykoli odvolat. *
        </span>
      </label>
    </div>
  );
}
