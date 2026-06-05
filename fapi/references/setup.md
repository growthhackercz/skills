# Nastavení skillu `fapi`

Skill potřebuje dva údaje z tvého FAPI účtu, aby se mohl ptát na tvá data. Tady je návod, jak to nastavit za 5 minut.

## 1) Vygeneruj si API klíč ve FAPI

1. Přihlas se do FAPI: https://web.fapi.cz
2. Vpravo nahoře otevři **Můj účet → API klíče**.
   Přímý odkaz: https://web.fapi.cz/account-settings/api-tokens
3. Klikni na **Nový API klíč** (případně **Vytvořit klíč** — záleží na verzi UI).
4. FAPI ti zobrazí dvojici:
   - **Uživatelské jméno** — to je e-mail tvého FAPI účtu (např. `tvuj-email@firma.cz`)
   - **API klíč** — citlivý řetězec, který se v Control Center uloží jako secret
5. **Zkopíruj si oboje hned.** Klíč později uvidíš znovu (tlačítko „Zobrazit"), ale ulehčíš si práci tím, že si ho vezmeš teď.

> 🔒 **Bezpečnost:** API klíč je stejně citlivý jako heslo do FAPI. Nesdílej ho, neukládej do veřejných repozitářů, nikomu ho neposílej Slackem ani e-mailem. Pokud si myslíš, že ti unikl, ve FAPI ho smaž a vygeneruj nový.

## 2) Vlož údaje do Control Center

V Control Center otevři **Integrace → Operations → FAPI** a vyplň:

- `FAPI_USER` — e-mail účtu FAPI
- `FAPI_TOKEN` — API klíč

Control Center uloží token do secret store a agentovi předá jen runtime SecretRef. Neukládej token ručně do `openclaw.json`, do dokumentů ani do task výstupů.

## 3) Restartuj agenta

Aby si OpenClaw načetl novou konfiguraci:

- **Z chatu:** napiš `/new` — otevře novou session s aktuálním snapshotem skillů.
- **Z příkazové řádky na serveru:** `openclaw gateway restart` (případně `sudo docker restart openclaw`, pokud běží jako kontejner).

## 4) Vyzkoušej

V chatu zkus jednu z těchto otázek:

- *„Které faktury jsou po splatnosti?"*
- *„Kolik jsem za poslední měsíc vydělal?"*
- *„Top 5 produktů za letošek"*

Agent ti odpoví tabulkou s čísly přímo z tvého FAPI účtu.

## Když to nefunguje

| Symptom | Co s tím |
|---|---|
| Agent říká *„nemám přístup k FAPI"* nebo *„chybí FAPI_USER"* | Integrace není nastavená nebo session běží se starým snapshotem. Zkontroluj Control Center → Integrace → FAPI a spusť novou session. |
| Agent volá API, ale vrací *„HTTP 401"* | API klíč je špatně. Buď v `FAPI_USER` není e-mail účtu, nebo v `FAPI_TOKEN` je překlep. Klíč si můžeš v UI FAPI znovu zobrazit (`Můj účet → API klíče → Zobrazit`). Pokud si nejsi jistý, vygeneruj nový a starý smaž. |
| Agent vrací *„HTTP 400"* na konkrétní dotaz | Chyba ve filtru. Většinou špatný formát data nebo nepodporovaný parametr na daném zdroji — nahlas to Pavlovi, doplníme do skillu výjimku. |
| Reporty mají divná čísla (chybí storno, mix měn) | Skill při výpočtu sám upozorní. Pokud čísla nesedí proti FAPI dashboardu, podívej se na `references/omezeni-a-pasti.md` — nejčastější příčiny jsou storno a mix měn. |

## Jak klíč zrušit

Když chceš agentovi přístup do FAPI odebrat:

1. Ve FAPI: `Můj účet → API klíče → Smazat` u příslušného klíče.
2. V Control Center → Integrace → FAPI odeber uložené údaje.
3. Restartuj agenta (`/new` v chatu).

Hotovo.
