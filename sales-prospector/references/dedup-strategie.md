# Strategie ošetření duplicit — pět vrstev

Tento dokument popisuje, jak Sales Prospector zajišťuje, že vám **stejnou firmu nebude opakovaně dodávat**. Cílem je chránit obchodníky před zaplavením duplicitními kontakty a chránit kontakty před opakovaným oslovováním.

## Pět vrstev v pořadí, ve kterém se aplikují

Skill aplikuje pravidla v Kroku 5 (po nasbírání a doplnění informací o kandidátech). U každé vyřazené firmy si uloží **důvod**, který uvidíte v `prospects-review.md`.

### Vrstva 1 — Povinná kritéria z profilu ideálního klienta

Zdroj: `idealni-klient.md` (sekce „Firmografika" a „Vyhledávací předpis").

Vyřadí kandidáty, kteří **nesplňují základní požadavky** — region, velikost, právní forma, kontaktní minimum (musí mít alespoň web a buď e-mail nebo telefon).

### Vrstva 2 — Vyřazovací kritéria z profilu (disqualifikátory)

Zdroj: `idealni-klient.md` (sekce „Vyřazovací kritéria").

Typicky:
- **Insolvence nebo likvidace** — ověří se v Justice.cz / ISIR
- **Konkurence** — firmy, které prodávají stejný produkt
- **Oborové vyloučení** — sektory, kam neprodáváme (zbraně, hazard, ...)

### Vrstva 3 — Černá listina

Zdroj: `/documents/sales/blacklist.csv`

Černá listina je **lokální soubor**, který spravujete ručně. Slouží pro firmy, které z jakéhokoli důvodu **nikdy nechcete oslovovat** (ex-zaměstnanec, partner konkurence, NDA, soudní spor, prostě nechci).

**Formát souboru** (CSV s hlavičkou):

```csv
email,phone,domain,ico,company_pattern,reason,added_date
info@konkurence.cz,,,,,,Hlavní konkurent,2026-02-15
,+420777123456,,,,,Bývalý zaměstnanec,2025-11-03
,,partner-konkurence.cz,,,Partner konkurence,2026-01-20
,,,12345678,,,IČO firmy, kterou nechceme,2026-04-08
,,,,*Manufaktura*,,Vzor názvu (regulární výraz pro shodu),2025-09-12
```

**Pravidla shody:**

| Sloupec | Typ shody | Příklad shody |
|---|---|---|
| `email` | přesná, malá písmena | `info@konkurence.cz` = `Info@Konkurence.cz` ✅ |
| `phone` | po normalizaci do E.164 | `+420777123456` = `777 123 456` ✅ |
| `domain` | přesná shoda domény z webu nebo e-mailu | `konkurence.cz` blokuje `pepa@konkurence.cz` i `web: https://konkurence.cz` |
| `ico` | přesná shoda 8místného IČO | `12345678` ✅ |
| `company_pattern` | regulární výraz na název firmy | `*Manufaktura*` blokuje „Manufaktura s.r.o." i „Naturální Manufaktura a.s." |

**Pokud černá listina neexistuje**, skill ji ignoruje (žádná chyba, jen poznámka v logu *„blacklist.csv nenalezen, vrstva 3 přeskočena"*).

### Vrstva 4 — Karanténa mezi kampaněmi (lokální paměť)

Zdroj: `/documents/sales/.dedup-history.jsonl`

Tento soubor je **živá paměť skillu** — pokaždé, když skill v Kroku 7 dodá prospekty, **připíše** záznam o každém z nich. Při příštím běhu (i v jiné kampani) zkontroluje, zda už danou firmu nedodal v posledních **180 dnech** (výchozí karanténa).

**Formát souboru** (JSONL — jeden JSON objekt na řádek, append-only):

```json
{"email":"info@firma.cz","phone":"+420777123456","ico":"12345678","domain":"firma.cz","company":"Firma s.r.o.","campaign":"eko-kosmetika-eshopy","date":"2026-05-25","status":"delivered"}
{"email":"obchod@dalsi.cz","phone":null,"ico":"87654321","domain":"dalsi.cz","company":"Další s.r.o.","campaign":"b2b-praha","date":"2026-05-20","status":"delivered_revisit"}
```

**Shoda se kontroluje podle** (v tomto pořadí, první shoda vyhrává):
1. `email` (přesně)
2. `ico` (přesně — nejjistější pro CZ firmy)
3. `phone` (po normalizaci do E.164)
4. `domain` (přesně — slabší shoda, generuje varování v review.md, ne tvrdé vyřazení)

**Hodnota `status`:**
- `delivered` — dodán do CSV (řádný prospekt)
- `delivered_revisit` — dodán s příznakem [PROBĚHL DLOUHO]
- `pushed_to_crm` — kromě dodání byl i vložen do CliqSales CRM (zapisuje se v Kroku 8)

**Změna karantény:** uživatel může v Kroku 2 (plán vyhledávání) nastavit jinou hodnotu než výchozích 180 dní. Skill přijme hodnoty 30, 90, 180, 365 nebo „bez karantény".

**Souborem nelze nic poškodit:** je append-only. Žádný záznam se v něm nemaže ani neupravuje. Pokud chcete kontakt vyňmout z karantény, smažete přímo řádek (editor).

### Vrstva 5 — Kontrola v CliqSales CRM

Skript volá `GET /contacts/search?locationId=<ID>&email=<email>` (a paralelně `?phone=<phone>` pokud e-mail chybí) u každého zbývajícího kandidáta.

Z odpovědi se hodnotí tři údaje:

1. **`dnd` (Do Not Disturb — nerušit)** — pokud `true`, nebo pokud `dndSettings.{Call|SMS|Email}.status === 'active'` → **tvrdé vyřazení**. Respektujeme nativní příznak v CliqSales.
2. **`lastActivity`** — datum poslední aktivity v CRM. Pokud spadá do **posledních 180 dní** (výchozí), kandidát se vyřadí (někdo už ho oslovil).
3. **`lastActivity` starší než 180 dní** + kontakt **není** v koncové fázi (pipeline stage `won` / `lost`) → kandidát se **ponechá v seznamu, ale označí příznakem [PROBĚHL DLOUHO]** s informací o poslední aktivitě a fázi. Obchodník sám rozhodne, zda znovu oslovit.

**Pokud kontakt v CRM neexistuje**, prochází bez výjimky.

**Pokud CliqSales integrace není nakonfigurovaná**, vrstva 5 se přeskočí (kandidáti pokračují, ale skill vypíše upozornění *„Vrstva 5 přeskočena — CliqSales integrace není nastavená. Riziko duplikátů zůstává."*).

## Souhrnný výstup v chatu (Krok 5)

Skill po dokončení všech vrstev vypíše souhrn:

```
🚦 Krok 5 — vyřazení nevyhovujících
Z 47 nasbíraných firem odfiltrováno 22:
  • bez kontaktu (vrstva 1):           5
  • insolvence (vrstva 2):              3
  • černá listina (vrstva 3):           2
  • karanténa kampaně 180d (vrstva 4):  8
  • nedávno v CRM 180d (vrstva 5):      3
  • DND v CRM (vrstva 5):               1

Zbývá 25 prospektů k oslovení.
Plus 3 prospekty s příznakem [PROBĚHL DLOUHO] (CRM aktivita > 180d, ne v koncové fázi).
```

## Hraniční případy

### Stejný kontakt na různých e-mailech (`marek@firma.cz` vs `info@firma.cz`)

- Vrstvy 1–4 se na to dívají jako na dva různé kontakty (pokud `domain` nemá záznam v černé listině).
- Vrstva 5 (CRM) je strict na e-mail — pokud máte v CRM jen `marek@firma.cz`, nový `info@firma.cz` neukáže shodu.
- Doporučení: pokud chcete blokovat celou doménu, přidejte ji do `blacklist.csv` na řádek `domain`.

### Firma změnila e-mail nebo telefon

- Vrstva 4 stále zachytí shodu přes `ico` (pokud byla zachycena při minulém běhu).
- Pro CZ firmy je `ico` nejjistější identifikátor — proto se vždy ukládá do historie, i když nemáme e-mail.

### Stejná firma má více poboček (vícero IČO)

- Každé IČO se chová jako samostatná firma. To je správně — pobočka v Praze a pobočka v Brně jsou často samostatní rozhodovatelé.
- Pokud chcete řešit jako jednu firmu, vlož mateřské IČO do `blacklist.csv` (pravidlo `company_pattern` na obchodní jméno).

### Soubor historie je porušený (JSONL parse error)

- Skill ho přečte řádek po řádku. Vadné řádky přeskočí a vypíše varování *„dedup-history.jsonl: 3 vadné řádky, přeskočeno"*. Nikdy soubor sám neopraví.
- Záloha souboru: protože je append-only, doporučujeme jeho denní snapshot do `/documents/sales/.dedup-history-backup/`.

### Skill neběží od nuly — co se starými výsledky před zavedením historie?

- Pokud `dedup-history.jsonl` neexistuje, vrstva 4 se přeskočí (jen log *„historie zatím prázdná, vrstva 4 přeskočena"*).
- Po prvním běhu se soubor založí a od dalších běhů karanténa funguje.
- Pokud chcete „prosytit" historii starými kampaněmi, ručně do ní vložíte JSON řádky pro každý kontakt, který nechcete znovu oslovit.

## Konfigurace v Kroku 2

Uživatel v Kroku 2 (plán vyhledávání) může změnit tyto výchozí hodnoty:

| Parametr | Výchozí | Možné hodnoty |
|---|---|---|
| `dedup_window_days` (karanténa kampaně) | 180 | 30, 90, 180, 365, „bez karantény" |
| `crm_recent_activity_days` (CRM aktivita) | 180 | 30, 90, 180, 365 |
| `use_blacklist` (použít černou listinu) | ano | ano, ne |
| `revisit_threshold_days` (označovat [PROBĚHL DLOUHO]) | 180 | 90, 180, 365 |

Skill tyto hodnoty zapíše do `plan-vyhledavani.md` a do `meta.json`, abyste se k nastavení mohli později vrátit.
