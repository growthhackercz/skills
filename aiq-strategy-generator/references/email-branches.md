# E-mailové větve — 3 sekvence podle lead_temperature

Follow-up NEJEDE přes GHL workflow (klient žádný nemá a nebude klikat).
Každý kontakt dostane **svoje kompletně vygenerované e-maily**, naplánované přes
GHL API jako **scheduled messages** — viditelné v konverzaci kontaktu jako
„Scheduled". Plná automatizace, nula ručního setupu.

Strategy skill definuje ve `funnel-spec.email_branches` **osnovy** (den + cíl per
e-mail per větev) — schvalují se ve STOP 4. **Plné texty** generuje runtime
(personalizer) per kontakt, s contactId napevno v URL (žádné template tagy).

## E0 — mimo větve, deterministický (K2)

E0 (potvrzení + odkaz na magnet) **nesmí záviset na LLM ani AI Teamu** — slib
„analýza do 5 minut" nesmí padnout s výpadkem personalizace. E0 odesílá přímo
`/api/submit` ze statické šablony (oslovení vokativem + čistý odkaz
`/magnet/<contactId>`).
Personalizace a plánování E1+ doběhne na pozadí.

## Tři větve

### 🔥 HORKÁ (hot) — 3 e-maily, krátká cesta

| # | Den | Cíl |
|---|---|---|
| E1 | D+1 | diagnóza→předpis + odkaz /r/ |
| E2 | D+2 | segmentový důkaz + JEHO hlavní námitka |
| E3 | D+4 | osobní výzva / reálná urgence (jen pokud `urgency_source` ≠ none) |

Navíc: horký lead → **GHL task na kontaktu + tag `[prefix] - hot lead`** (viz TAGS v `spec.ts`, konvence `aiq - [kvíz] - hot lead`) + notifikace
klientovi (výtah odpovědí + telefon leada) — horký lead musí mít cestu k člověku.

### 🌤 VLAŽNÁ (warm) — 5 e-mailů, plný nurture

| # | Den | Cíl |
|---|---|---|
| E1 | D+1 | **čistá hodnota** — personalizovaný tip, ŽÁDNÝ prodej (reciprocita) |
| E2 | D+2 | diagnóza→předpis + /r/ |
| E3 | D+3 | segmentová case study |
| E4 | D+4 | námitky + garance |
| E5 | D+5 | shrnutí + měkký závěr (reálná urgence jen s reálným zdrojem) |

### ❄️ STUDENÁ (cold) — 3 e-maily, ochrana doručitelnosti i značky

| # | Den | Cíl |
|---|---|---|
| E1 | D+2 | hodnotný tip |
| E2 | D+4 | edukace — explicitně problem-aware obsah (agitace z jeho odpovědí + cena nečinnosti), NE ořezaný pitch |
| E3 | D+7 | „jsme tu" — měkké připomenutí + možnost re-assessmentu |

Žádná urgence, žádný voucher ve studené větvi.

## Obálka — pevná, LLM generuje JEN tělo

- **Patičku s odhlášením vkládá GHL na úrovni sub-accountu automaticky** — neřešíme
  v kódu, ale při smoke testu vizuálně ověřit, že tam je.
- **Identifikace odesílatele hardcoded v šabloně obálky** (název + adresa firmy),
  + reply-to z `ops.reply_to`.
- LLM nikdy negeneruje hlavičky, patičku ani odkazy mimo whitelist.

## Post-generation lint (deterministický, závazný)

Každý vygenerovaný e-mail projde lintem PŘED naplánováním:

1. **Ceny / garance** — jen hodnoty z `offer` whitelistu (productDNA). Doporučení:
   cenu v e-mailech neuvádět vůbec — odkázat na prodejní stránku (jedna verze pravdy).
2. **URL** — jen whitelist: `/r/`, `/magnet/`, doména klienta. Nic jiného.
3. **Žádná vymyšlená čísla / statistiky / bonusy.**
4. **Vykání** v celém těle.
5. **Oslovení z vokativ tabulky** (`lib/vocative.ts` — deterministický lookup,
   nikdy LLM; fallback „Dobrý den", nikdy nominativ, nikdy celé jméno).
6. Délkové limity (plain-text konverzační styl, žádné eseje).

**Fail policy:** lint fail → 1× regenerace s chybovou zpětnou vazbou → druhý fail
→ **fallback statická šablona větve** (vždy funkční).

**Prompt-injection ochrana vstupů:** otevřené odpovědi z kvízu jsou ohraničená
nedůvěryhodná DATA (instruction-hardening), sanitizace + délkový limit, citace
jen po filtru, JSON schema validace všech generovaných polí.

## `urgency_source` — zákaz fake urgence

Povinný enum ve funnel-spec: `capacity` / `cohort` / `season` / `bonus` / `none`.

- **Default `none`** — bez reálného zdroje jede sekvence BEZ urgence; závěrečné
  e-maily staví na ceně nečinnosti (cost-of-inaction), ne na tlaku.
- Fake countdown u stálé nabídky = lež → ničí důvěru i doručitelnost. ZAKÁZÁNO.
- „Platnost personalizované analýzy" je vyřazená jako pseudo-fake zdroj.
- Reálný zdroj (např. kapacita konzultací) → smí do E3/E5 příslušné větve,
  formulovaný pravdivě a konkrétně.

## Předměty a styl

- Předmět z kvízových dat: „[Jméno], vaše skóre 80 znamená…" — konkrétní, ne clickbait.
- Plain-text konverzační styl, krátké odstavce.
- Všechny odkazy s `contactId` napevno; token se do URL nepřidává.

## Mechanika doručení (kontext — vykonává builder/runtime, ne strategy)

- Plánování: `POST /conversations/messages` `{type:"Email", contactId, subject,
  html, scheduledTimestamp}` — **Unix SEKUNDY** (ms → 422). Výchozí čas 9:00
  Europe/Prague v den D+N.
- Zrušení: `DELETE /conversations/messages/email/{emailMessageId}/schedule`.
- Message IDs se ukládají **append-only** do pole „AIQ - Scheduled IDs" — bez nich
  nejde stop-on-purchase ani kill switch.
- Před novým plánováním VŽDY zrušit existující AIQ scheduled zprávy kontaktu
  (idempotence, re-entry: nový běh kvízu ukončuje starý).
- Stop-on-purchase / kill switch: cron-guard (viz skill aiq-funnel-builder).
- **Pilot režim (volitelný, default vypnutý):** `pilot_mode.enabled: true` přidá
  předmětům prefix [PILOT] pro interní zkoušku. DND/consent check před
  každým odesláním.
