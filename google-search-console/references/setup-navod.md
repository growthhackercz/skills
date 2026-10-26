# Nastavení Google Search Console — pro klienta / Success Managera

Navazuje na nastavení Google Analytics. Pokud už máte hotový service account pro GA, přidáváte jen přístup do Search Console a jednu proměnnou. ~3 minuty.

## Předpoklad

Web má ověřenou property v Google Search Console (search.google.com/search-console). Pokud ne, je potřeba ji nejdřív ověřit (obvykle přes DNS záznam nebo GA) — s tím pomůže technický kontakt.

## Krok 1 — Použijte existující service account

Stejný service account (a stejný stažený JSON klíč) jako pro Google Analytics. Pokud GA nemáte, vytvořte ho podle návodu GA skillu (Google Cloud → účet služby → JSON klíč) a v Cloud Console navíc povolte **Google Search Console API** (API a služby → Knihovna).

## Krok 2 — Přidejte účet do Search Console (čtení)

1. Z JSON klíče zkopírujte `client_email` (končí na `.iam.gserviceaccount.com`).
2. V Search Console: **Nastavení → Uživatelé a oprávnění → Přidat uživatele.**
3. Vložte e-mail, oprávnění **Úplné** nebo **Omezené** (obojí stačí ke čtení) → Přidat.

## Krok 3 — Vložte do AI Teamu

V **Nastavení → Integrace**:

- `GA_SERVICE_ACCOUNT_JSON` — pokud už tam je (sdílené s GA), nechte být; jinak vložte celý obsah JSON klíče.
- `GSC_SITE_URL` — adresa webu **přesně jak je uvedená v Search Console**:
  - doménová property → `sc-domain:vasedomena.cz`
  - URL property → `https://vasedomena.cz/` (i s koncovým lomítkem)

Ověřte v chatu: **„Na jaká slova nás lidé najdou?"**

## Řešení potíží

| Hláška agenta | Příčina | Řešení |
|---|---|---|
| „přístup odmítnut (403)" | SA e-mail není uživatel v GSC | Krok 2 |
| „web nenalezen (404)" | špatný tvar GSC_SITE_URL | doménová = `sc-domain:...`, URL = celá adresa s `https://` a lomítkem |
| „(žádná data)" | nová/čerstvá property | GSC potřebuje pár dní nasbírat data |
