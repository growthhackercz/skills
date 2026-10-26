# Nastavení Google Analytics — 4 kroky (pro klienta / Success Managera)

Jednorázové nastavení, zabere ~5 minut. Potřebujete přístup do Google Analytics účtu klienta a libovolný Google účet pro Google Cloud.

## Krok 1 — Vytvořte service account (technický účet pro čtení)

1. Otevřete https://console.cloud.google.com → vyberte/založte projekt (název libovolný, např. „AI Team").
2. V menu: **IAM a správa → Účty služeb → Vytvořit účet služby.**
3. Název např. `ai-team-analytics` → Vytvořit → (role přeskočte, žádná není potřeba) → Hotovo.
4. Ještě v Cloud Console: **API a služby → Knihovna → „Google Analytics Data API" → Povolit.**

## Krok 2 — Stáhněte JSON klíč

1. Klikněte na vytvořený účet služby → záložka **Klíče**.
2. **Přidat klíč → Vytvořit nový klíč → JSON → Vytvořit.**
3. Stáhne se soubor `*.json` — otevřete ho v poznámkovém bloku, budete kopírovat celý obsah.

## Krok 3 — Dejte účtu přístup do Google Analytics (jen ČTENÍ)

1. V souboru z kroku 2 najděte `client_email` (končí na `.iam.gserviceaccount.com`) a zkopírujte ho.
2. V **Google Analytics**: Správce → (sloupec Služba) **Přístup k službě** → ➕ **Přidat uživatele**.
3. Vložte ten e-mail, role **Čtenář (Viewer)** → Přidat.

> Nejčastější chyba: tento krok se přeskočí → agent pak hlásí „přístup odmítnut (403)".

## Krok 4 — Vložte do AI Teamu

1. V Google Analytics: Správce → **Nastavení služby** → zkopírujte **ID služby** (jen číslo).
2. V AI Teamu: **Nastavení → Integrace** → přidejte dvě položky:
   - `GA_SERVICE_ACCOUNT_JSON` = celý obsah staženého JSON souboru (vložit vše od `{` po `}`)
   - `GA4_PROPERTY_ID` = číslo z bodu 1
3. Hotovo. Vyzkoušejte v chatu: **„Kolik lidí bylo tento týden na webu?"**

## Řešení potíží

| Hláška agenta | Příčina | Řešení |
|---|---|---|
| „přístup odmítnut (403)" | service account není přidaný v GA | Krok 3 |
| „property nenalezena (404)" | špatné ID | Krok 4.1 — jen číslo, bez `properties/` |
| „není platný JSON" | vložená jen část souboru | vložit celý obsah včetně `{ }` |
| „invalid_grant" | klíč smazaný/poškozený | vytvořit nový klíč (Krok 2) |
