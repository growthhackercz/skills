# Rozbalení vstupu — extrakce údajů z textu

Sales Scout dostává v Krok 0 prompt v libovolném formátu. Tento dokument popisuje, jak z něj vytáhnout strukturované údaje.

## Tři typické tvary vstupu

### 1. Webhook (strukturovaný)

Control Center / CliqSales workflow naformátuje webhook payload do prompt textu:

> *„Udělej Scout brief na nový kontakt: jméno=Marek Novák, email=marek@firma.cz, firma=Firma s.r.o., web=https://firma.cz, telefon=+420 777 123 456, contactId=abc123def456."*

Klíče (`jméno`, `email`, `firma`, `web`, `telefon`, `contactId`) jsou předvídatelné, snadné na extrakci přes jednoduché regexové vzory.

### 2. Manuální se všemi údaji

> *„Brief na Marka Nováka, marketingový manažer firmy Bioptron Medall s.r.o., e-mail marek@bioptron-medall.cz, web bioptron-medall.cz."*

Údaje jsou v běžné větě. Extrakce přes regex + drobné LLM uvažování.

### 3. Manuální minimální

> *„Scout brief na Bioptron Medall."*
> *„Brief na info@firma.cz."*
> *„Scout na Marka Nováka z Bioptron Medall."*

Skill má **najít zbytek údajů sám** — odvodit web z názvu (přes Brave Search nebo ARES → najít web v ARES), odvodit firmu z e-mailové domény, odvodit jméno z kontextu.

## Pravidla extrakce

### E-mail

**Regex:** `[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}`

**Validace:** musí obsahovat `@` a alespoň jednu tečku v doménové části.

**Odvození domény firmy:** `marek@firma.cz` → doména `firma.cz` → predikce webu `https://firma.cz` nebo `https://www.firma.cz`.

**Pozor:** doménu `gmail.com`, `seznam.cz`, `email.cz`, `centrum.cz`, `outlook.com`, `yahoo.com`, `icloud.com`, `volny.cz`, `tiscali.cz`, `post.cz` **nepoužívej** jako web firmy (jsou to free e-mailové služby). V takovém případě extrahuj firmu odjinud (z prompt textu, z LinkedIn).

### Telefon

**Regex:** `\+?420\s?\d{3}\s?\d{3}\s?\d{3}` (české číslo) nebo obecný `\+?\d[\d\s\-]{8,15}`

**Normalizace:** odstraň mezery a pomlčky, doplň `+420` pokud chybí a číslo má 9 číslic začínajících 6, 7 nebo 9.

### IČO

**Regex:** `\b\d{8}\b` v kontextu „IČO", „IČ", „IC" — explicit označení v textu.

Pokud IČO není v textu, **odvoď ho z názvu firmy přes ARES** (Krok 2 workflow).

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
- *„Brief na Marka Nováka z Bioptron Medall"* → firma = „Bioptron Medall"
- *„Scout brief pro firmu Foo Pharma s.r.o."* → firma = „Foo Pharma s.r.o."
- *„Brief na info@bioptron-medall.cz"* → firma odvozená z domény = „Bioptron Medall" (vyhledat přes ARES podle doménového jména)

### Jméno a příjmení osoby

Extrahuj přes regex pro **strukturovaný vstup** (klíč `jméno=`), nebo přes LLM uvažování pro **manuální vstup**.

**LLM uvažování:** hledej dva po sobě jdoucí tokeny začínající velkým písmenem (české jméno + příjmení). Vyloučit, pokud jsou součástí názvu firmy.

**Příklady:**
- *„Brief na Marka Nováka"* → jméno = „Marek", příjmení = „Novák" (převést skloňování do 1. pádu)
- *„Scout na Petra Havla z CliqSales"* → jméno = „Petr", příjmení = „Havel"

**Skloňování:** Scout musí převést jméno do **1. pádu** pro LinkedIn lookup a brief. Přibližná pravidla:
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

Zachytí `product=bioptron-medall`, `product: ai-akcelerator`, `Product=Live100-vitaminy`.

**LLM extrakce ze zmínky v textu:** hledej fráze:
- „pro [Název produktu]"
- „nabízíme [Název produktu]"
- „prodáváme [Název produktu]"
- „[Název produktu] pro [firmu]"

**Příklady:**
- *„Scout brief na Effect Clinic pro Bioptron"* → `product = "bioptron"`
- *„Brief na info@firma.cz, nabízíme Bioptron MedAll"* → `product = "bioptron-medall"`
- *„Připrav brief, prodáváme AI Akcelerátor"* → `product = "ai-akcelerator"`

**Mapování na slug:** porovnej extrahované jméno se slugy v `/documents/brand/products/`. Použij case-insensitive substring match. Pokud match nejednoznačný, vyber nejdelší slug (typicky nejspecifičtější).

Pokud žádný produkt v promptu, použije se **multi-product režim** (viz `product-context.md` Krok 0.5).

## Postup v Krok 0

1. **Pokus 1:** strukturovaná extrakce pro `klíč=hodnota` páry (regex)
2. **Pokus 2:** regex pro e-mail / telefon / web / IČO (volné v textu)
3. **Pokus 3:** LLM extrakce pro název firmy a jméno osoby
4. **Pokus 4:** odvození chybějících údajů
   - Pokud máme e-mail s firemní doménou → web = doména
   - Pokud máme web → ARES lookup pro IČO a název firmy
   - Pokud máme jen název firmy → ARES lookup pro IČO + web (z ARES detail nebo z webu firmy)

**Minimální požadavek pro pokračování:** alespoň jeden identifikátor firmy (název / web / IČO / `contactId`).

**Pokud chybí všechny** → STOP s lidskou zprávou: *„V tvém zadání chybí identifikace firmy. Doplň alespoň jedno: název firmy, web, IČO nebo `contactId` z CliqSales CRM."*

## Příklady úplné extrakce

### Příklad 1 — webhook (strukturovaný, včetně produktu)

**Vstup:**
> *„Udělej Scout brief na nový kontakt: jméno=Marek Novák, email=marek@bioptron-medall.cz, firma=Bioptron Medall s.r.o., web=https://bioptron-medall.cz, telefon=+420 777 123 456, contactId=abc123, product=bioptron-medall."*

**Výstup:**
```json
{
  "firstName": "Marek",
  "lastName": "Novák",
  "email": "marek@bioptron-medall.cz",
  "companyName": "Bioptron Medall s.r.o.",
  "website": "https://bioptron-medall.cz",
  "phone": "+420777123456",
  "contactId": "abc123",
  "product": "bioptron-medall",
  "refresh": false,
  "mode": "webhook"
}
```

### Příklad 2 — manuální s e-mailem

**Vstup:**
> *„Brief na info@bioptron-medall.cz, firma se jmenuje Bioptron Medall s.r.o."*

**Výstup:**
```json
{
  "firstName": null,
  "lastName": null,
  "email": "info@bioptron-medall.cz",
  "companyName": "Bioptron Medall s.r.o.",
  "website": "https://bioptron-medall.cz",  // odvozeno z domény
  "phone": null,
  "contactId": null,
  "mode": "manual"
}
```

### Příklad 3 — manuální minimální

**Vstup:**
> *„Scout brief na Bioptron Medall."*

**Výstup:**
```json
{
  "firstName": null,
  "lastName": null,
  "email": null,
  "companyName": "Bioptron Medall",
  "website": null,                 // doplní se v Kroku 2 přes ARES
  "phone": null,
  "contactId": null,
  "mode": "manual"
}
```

### Příklad 4 — minimum s osobou

**Vstup:**
> *„Brief na Marka Nováka z Bioptron Medall."*

**Výstup:**
```json
{
  "firstName": "Marek",
  "lastName": "Novák",
  "email": null,
  "companyName": "Bioptron Medall",
  "website": null,
  "phone": null,
  "contactId": null,
  "mode": "manual"
}
```
