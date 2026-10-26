# Rozbalení vstupu — market-aware extrakce údajů z textu

Sales Scout dostává v Krok 0 prompt v libovolném formátu. Tento dokument popisuje, jak z něj vytáhnout strukturované údaje.

## Tři typické tvary vstupu

### 1. Webhook (strukturovaný)

Control Center / CliqSales workflow může naformátovat webhook payload do prompt textu. Tento text je pouze vstup; před vytvořením GHL plánu musí existovat konkrétní task přiřazený `cso` a producer musí dostat jeho kladné `--task-id`, stabilní `--idempotency-key` a durable `--plan-artifact`.

> *„Udělej Scout brief na nový kontakt: market=SK, jméno=Marek Novák, email=marek@firma.sk, firma=Firma s.r.o., web=https://firma.sk, telefon=+421 901 234 567, contactId=abc123def456."*

Klíče (`market`, `jméno`, `email`, `firma`, `web`, `telefon`, `contactId`,
`registry_id_type`, `registry_id`) jsou předvídatelné a snadné na extrakci.

### 2. Manuální se všemi údaji

> *„Brief na Marka Nováka, marketingový manažer firmy Firma Alfa s.r.o., e-mail marek@produkt-a.cz, web produkt-a.cz."*

Údaje jsou v běžné větě. Extrakce přes regex + drobné LLM uvažování.

### 3. Manuální minimální

> *„Scout brief na Produkt A."*
> *„Brief na info@firma.cz."*
> *„Scout na Marka Nováka z Produkt A."*

Skill má **najít zbytek údajů sám**, ale pouze přes zdroje aktuálního market
adapteru: odvodit kandidátní web z firemní domény, ověřit firmu přes povolený
registry source a jméno vzít jen z veřejného podkladu.

## Pravidla extrakce

### Market

**Regex:** `\bmarket\s*[=:]\s*([A-Za-z]{2})\b`

Normalizuj na uppercase a ověř přes
`python3 {baseDir}/scripts/market_context.py market-plan --market <MARKET>`.
Z validovaného Prospector řádku market převezmi. U starého vstupu bez marketu
použij kompatibilní `CZ` a do briefu napiš `market origin: legacy_default`.
TLD nebo telefon jsou nápověda, ne důkaz pro jiný market.

### E-mail

**Regex:** `[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}`

**Validace:** musí obsahovat `@` a alespoň jednu tečku v doménové části.

**Odvození domény firmy:** `marek@firma.cz` → doména `firma.cz` → predikce webu `https://firma.cz` nebo `https://www.firma.cz`.

**Pozor:** veřejné e-mailové domény typu Gmail, Seznam, Outlook nebo Yahoo
nepoužívej jako web firmy. V takovém případě vezmi firmu z promptu nebo
ověřeného marketového registry/web zdroje.

### Telefon

**Regex:** `\+?\d[\d\s\-]{7,18}`

**Normalizace:** použij market helper. Prefix `+420`, `+421` nebo `+34` se
doplňuje jen podle explicitně zvoleného marketu.

### Registry ID

Pro `CZ/SK` přijmi osm číslic v kontextu IČO; pro `ES` přijmi NIF pouze v
kontextu NIF/CIF. Ulož obecně jako `registry_id_type` + `registry_id`.

Chybějící ID hledej výhradně přes `registry_verification` source z market
policy. `ares_lookup.py` je platný jen pro `market=CZ`.

### Web / URL

**Regex:** `https?://[\w\-\.]+(?:\.[a-zA-Z]{2,})+[/\w\-\.\?\=\&\#]*` nebo bez protokolu `\b[\w\-]+\.(?:cz|sk|com|eu|org|net|info|io|app|ai)\b`

**Normalizace:** doplň `https://` pokud chybí, odstraň trailing slash.

### Název firmy

Extrahuj přes regex pro **strukturovaný vstup** (klíč `firma=`), nebo přes LLM uvažování pro **manuální vstup**.

**LLM uvažování:** v promptu hledej:
- Předložky „pro", „z", „od", „u" + následující slova s velkým písmenem
- Sufixy „s.r.o.", „a.s.", „spol. s r.o.", „k.s.", „o.s.", „z.s.", „o.p.s."
- Zmínky „firma", „společnost", „klient" + následující slova s velkým písmenem

**Příklady:**
- *„Brief na Marka Nováka z Produkt A"* → firma = „Produkt A"
- *„Scout brief pro firmu Foo Pharma s.r.o."* → firma = „Foo Pharma s.r.o."
- *„Brief na info@produkt-a.cz"* → firma je kandidát odvozený z domény; ověř ji
  přes registry/web zdroj aktuálního marketu

### Jméno a příjmení osoby

Extrahuj přes regex pro **strukturovaný vstup** (klíč `jméno=`), nebo přes LLM uvažování pro **manuální vstup**.

**LLM uvažování:** hledej dva po sobě jdoucí tokeny začínající velkým písmenem (české jméno + příjmení). Vyloučit, pokud jsou součástí názvu firmy.

**Příklady:**
- *„Brief na Marka Nováka"* → jméno = „Marek", příjmení = „Novák" (převést skloňování do 1. pádu)
- *„Scout na Petra Havla z CliqSales"* → jméno = „Petr", příjmení = „Havel"

**Skloňování:** Scout může převést jméno do **1. pádu** pro brief. Nepoužívá je
k LinkedIn lookupu. Přibližná pravidla:
- 4. pád: „Marka" → 1. pád „Marek"; „Petra" → „Petr"; „Pavla" → „Pavel"; „Nováka" → „Novák"; „Havla" → „Havel"
- Pokud si nejsi jistý → použij přímo to, co je v textu (riziko špatné formy, ale lepší než hádat)

### CliqSales `contactId`

**Regex:** `\bcontactId\s*[=:]\s*([a-zA-Z0-9]{8,})` nebo `\bID\s+([a-zA-Z0-9]{16,})`

**Použití:** pokud `contactId` v promptu, **přeskoč Krok 7 vyhledání kontaktu v CRM** — víme přesně, ke kterému kontaktu poznámku připojit.

### `refresh` flag (vynucení nového briefu, obejití cache)

**Regex:** `\brefresh\s*[=:]\s*true\b` nebo zmínka v textu: „refresh", „aktualizuj brief", „nový brief", „přegeneruj"

**Použití:** pokud nalezeno, **přeskoč Krok 1 (kontrola opakovaného briefu)** a vždy vyrob nový brief, i pokud existuje mladší 60 dnů.

### Produkt (pro fit posouzení a sales úhly)

**Regex pro strukturovaný klíč:** `\bproduct\s*[=:]\s*([a-z0-9\-]+)`

Zachytí `product=produkt-a`, `product: produkt-b`, `Product=produkt-c`.

**LLM extrakce ze zmínky v textu:** hledej fráze:
- „pro [Název produktu]"
- „nabízíme [Název produktu]"
- „prodáváme [Název produktu]"
- „[Název produktu] pro [firmu]"

**Příklady:**
- *„Scout brief na Firma Alfa pro Produkt A"* → `product = "produkt-a"`
- *„Brief na info@firma.cz, nabízíme Produkt A"* → `product = "produkt-a"`
- *„Připrav brief, prodáváme Produkt B"* → `product = "produkt-b"`

**Mapování na slug:** porovnej extrahované jméno se slugy v `/documents/brand/products/`. Použij case-insensitive substring match. Pokud match nejednoznačný, vyber nejdelší slug (typicky nejspecifičtější).

Pokud žádný produkt v promptu, použije se **multi-product režim** (viz `product-context.md` Krok 0.5).

## Postup v Krok 0

1. **Pokus 1:** strukturovaná extrakce pro `klíč=hodnota` páry (regex)
2. **Pokus 2:** regex pro market / e-mail / telefon / web / registry ID
3. **Pokus 3:** LLM extrakce pro název firmy a jméno osoby
4. **Pokus 4:** odvození chybějících údajů
   - Pokud máme e-mail s firemní doménou → web = doména
   - Pokud máme web → ověř název/registry ID přes market policy
   - Pokud máme jen název firmy → použij registry/web discovery aktuálního marketu

**Minimální požadavek pro pokračování:** podporovaný explicitní nebo legacy CZ
market a alespoň jeden identifikátor firmy (název / web / registry ID /
`contactId`).

**Pokud chybí identifikátor** → STOP s lidskou zprávou požadující alespoň jeden
identifikátor. Chybějící market používá výhradně legacy CZ kompatibilitu;
neznámý explicitní market fail-closed odmítni.

## Příklady úplné extrakce

### Příklad 1 — webhook (strukturovaný, včetně produktu)

**Vstup:**
> *„Udělej Scout brief na nový kontakt: market=CZ, jméno=Marek Novák, email=marek@produkt-a.cz, firma=Firma Alfa s.r.o., web=https://produkt-a.cz, telefon=+420 777 123 456, contactId=abc123, product=produkt-a."*

**Výstup:**
```json
{
  "market": "CZ",
  "firstName": "Marek",
  "lastName": "Novák",
  "email": "marek@produkt-a.cz",
  "companyName": "Firma Alfa s.r.o.",
  "website": "https://produkt-a.cz",
  "phone": "+420777123456",
  "contactId": "abc123",
  "product": "produkt-a",
  "refresh": false,
  "mode": "webhook"
}
```

### Příklad 2 — manuální s e-mailem

**Vstup:**
> *„Market CZ, brief na info@produkt-a.cz, firma se jmenuje Firma Alfa s.r.o."*

**Výstup:**
```json
{
  "market": "CZ",
  "firstName": null,
  "lastName": null,
  "email": "info@produkt-a.cz",
  "companyName": "Firma Alfa s.r.o.",
  "website": "https://produkt-a.cz",  // odvozeno z domény
  "phone": null,
  "contactId": null,
  "mode": "manual"
}
```

### Příklad 3 — manuální minimální

**Vstup:**
> *„Market CZ, Scout brief na Produkt A."*

**Výstup:**
```json
{
  "market": "CZ",
  "firstName": null,
  "lastName": null,
  "email": null,
  "companyName": "Produkt A",
  "website": null,                 // doplní se přes marketový registry/web source
  "phone": null,
  "contactId": null,
  "mode": "manual"
}
```

### Příklad 4 — minimum s osobou

**Vstup:**
> *„Market CZ, brief na Marka Nováka z Produkt A."*

**Výstup:**
```json
{
  "market": "CZ",
  "firstName": "Marek",
  "lastName": "Novák",
  "email": null,
  "companyName": "Produkt A",
  "website": null,
  "phone": null,
  "contactId": null,
  "mode": "manual"
}
```
