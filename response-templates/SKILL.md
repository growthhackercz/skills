---
name: response-templates
description: "Udržuje a zlepšuje knihovnu zákaznických odpovědí."
category: operations
status: ready
version: "1.0"
publishedAt: "2026-04-25"
---

# Šablony odpovědí

Udržuj knihovnu osvědčených šablon odpovědí. Vždy je personalizuj podle
zákazníka a sleduj, co skutečně funguje. Průběžně iteruj.

## Ukládání šablon

Ukládej šablony do `memory/response-templates.json`:

```json
{
  "templates": [
    {
      "id": "password-reset",
      "category": "account",
      "trigger": "Customer can't log in or needs password reset",
      "template": "Hi {name},\n\nHere's how to reset your password:\n\n1. Go to {product_url}/reset\n2. Enter your email address\n3. Check your inbox (and spam folder) for the reset link\n4. Click the link and set a new password\n\nIf the email doesn't show up within a few minutes, let me know and I'll look into it from our end.\n\n{signoff}",
      "variables": ["name", "product_url", "signoff"],
      "useCount": 0,
      "resolvedCount": 0,
      "avgSatisfaction": null,
      "lastUsed": null,
      "notes": ""
    }
  ]
}
```

## Knihovna základních šablon

Začněte s těmito. Přizpůsobte svému produktu:

### Problémy s účtem
- **password-reset** - Pokyny pro resetování hesla
- **account-locked** - Account locked/suspended vysvětlení
- **problémy s přihlášením** - Obecné kroky pro řešení problémů s přihlášením
- **account-deletion** - Zpracování žádosti o smazání účtu

### Fakturace
- **refund-approved** - Potvrzení vrácení peněz
- **refund-denied** - Odmítnutí vrácení peněz s odůvodněním
- **fakturační-otázka** - Vysvětlení poplatku
- **změna plánu** - Jak upgradovat/downgrade
- **storno-uložit** - Retenční odpověď, když chce zákazník zrušit

### Chyby
- **bug-acknowledged** - Vidíme chybu, jsme na ní
- **bug-workaround** - Chyba existuje, zde je návod, jak ji obejít
- **chyba opravena** - Oprava je nasazena, zkuste to prosím znovu
- **cant-reprodukovat** - K reprodukci je potřeba více detailů

### Jak na to
- **začínáme** - Základy registrace
- **příručka funkcí** - Jak používat konkrétní funkci
- **integration-setup** - Kroky integrace třetích stran

### Obecné
- **feature-request-ack** - Díky za návrh, zaprotokolováno
- **pozitivní zpětná vazba-díky** - Díky za milá slova
- **následná kontrola** - Kontrola po vyřešení
- **oznámení o eskalaci** - Informujeme zákazníka, že jsme eskalovali

## Používání šablon

### 1. Najdi nejlepší shodu

Když přijde ticket, najdi nejbližší shodu šablony. Zvaž:
- O jakou kategorii se jedná?
- Na co se vlastně zákazník ptá?
- Existuje přesná shoda, nebo se musíme přizpůsobit?

### 2. Přizpůsob

Šablonu nikdy neposílej neopracovanou. Vždy:
- Použij jméno zákazníka
- Uveď jejich konkrétní situaci („Vidím, že se pokoušíte připojit svůj účet Stripe...“)
- Přizpůsob tón zákazníkovi (technický zákazník dostane techničtější detail)
- Přidejte kontext z jejich účtu nebo historie
- Odstraňte kroky, které se nevztahují na jejich situaci

### 3. Odeslat a přihlásit

Po odeslání aktualizujte záznam šablony:
```json
{
  "useCount": 15,
  "resolvedCount": 12,
  "avgSatisfaction": 4.2,
  "lastUsed": "2025-01-15"
}
```

## Účinnost šablony

Sledujte, které šablony skutečně řeší problémy:

**Poměr rozlišení** = resolvedCount / useCount
- Nad 80 %: šablona funguje dobře
- 50–80 %: zkontrolovat a zlepšit
- Pod 50 %: přepsat nebo rozdělit na specifičtější šablony

**Korelace spokojenosti**: Pokud má šablona nízké skóre CSAT, odpověď může být technicky správná, ale hluchá. Zkontrolujte jazyk.

## Testování A/B

Když chcete šablonu vylepšit:

1. Vytvořte variantu (např. „password-reset-v2“)
2. Střídavě používejte originál a variantu
3. Sledujte míru rozlišení a spokojenost pro každého
4. Po 20+ použitích každého porovnejte výsledky
5. Vítěze si nechte, poraženého archivujte

Uložte výsledky testu do `memory/template-tests.json`:
```json
{
  "tests": [
    {
      "original": "bug-acknowledged",
      "variant": "bug-acknowledged-v2",
      "change": "Added estimated fix timeline and workaround upfront",
      "originalStats": { "uses": 25, "resolved": 18, "avgSat": 3.8 },
      "variantStats": { "uses": 22, "resolved": 20, "avgSat": 4.4 },
      "winner": "variant",
      "decidedDate": "2025-01-20"
    }
  ]
}
```

## Vytváření nových šablon

Když se přistihnete, že píšete podobné odpovědi 3+krát:

1. Navrhněte šablonu z nejlepší verze, kterou jste napsali
2. Identifikujte proměnné (jméno zákazníka, oblast produktu, konkrétní podrobnosti)
3. Přidejte jej do knihovny
4. Začněte sledovat využití

**Dobré vlastnosti šablony:**
- Pokud je to možné, řeší problém jednou odpovědí
- Začíná potvrzením, nikoli pokyny
- Kroky jsou očíslované a specifické
- Končí jasným dalším krokem
- Zní to, jako by to napsal člověk, ne systém

## Pravidla

- Šablony jsou výchozí body, ne autopilot. Vstupenku si vždy přečtěte a personalizujte.
- Pokud zákazník již kontaktoval, použijte historii. "Vidím, že jsi na to minulý týden taky narazil" ukazuje, že dáváš pozor.
- Nepoužívejte šablony pro naštvané zákazníky. Pište tyto odpovědi čerstvé, opatrně.
- Měsíčně kontrolujte knihovnu šablon. Kill šablony, které nikdo nepoužívá. Aktualizujte ty, které odkazují na staré funkce.
- Když šablona potřebuje podrobnosti specifické pro produkt, ponechte jasné proměnné značky, abyste omylem neposlali `{product_url}` zákazníkovi.
