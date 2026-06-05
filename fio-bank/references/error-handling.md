# FIO API — Error handling

## Přehled HTTP kódů

| Kód | Význam | Akce |
|---|---|---|
| **200** | OK | Pokračuj, parsuj odpověď |
| **401** | Špatný / expirovaný token | Řekni uživateli, ať vygeneruje nový token |
| **403** | Token nemá oprávnění pro tuto operaci | Skill volá jen read endpointy — pokud dostaneš 403, je něco vážně špatně |
| **404** | Endpoint nebo zdroj neexistuje | Zkontroluj URL (např. neexistující výpis ve `/by-id/`) |
| **409** | Rate limit (1 req / 30 s) | Helper `fio_get.py` retry automaticky; jinak počkej 30+ s |
| **500** | FIO server error | Retry za 1–5 minut. Pokud přetrvává, FIO má výpadek |
| **503** | FIO služba dočasně nedostupná | Retry za 5+ minut |

## Diagnóza per kód

### 401 Unauthorized

**Co se stalo:** Token je špatný, expirovaný, nebo byl smazán v IB FIO.

**Akce:**
1. Ověř, že FIO profil v Control Center odpovídá tokenu z IB FIO.
2. Pokud token starší než 180 dní → vypršel. Klient musí vygenerovat nový (viz `authentication.md`).
3. **NIKDY token „neopravuj"** — neguessuj znaky, neměň nic. Buď je správný, nebo není.

**Hláška uživateli:**
> Tvůj FIO API token je neplatný nebo vypršel. Vygeneruj nový v IB FIO (Nastavení → API → Vytvořit token, oprávnění „pouze čtení") a aktualizuj příslušný FIO profil v Control Center.

### 403 Forbidden

**Co se stalo:** Token neumí požadovanou operaci. V tomto skillu by nemělo nastat (voláme jen read endpointy).

**Akce:**
1. Zkontroluj, jestli jsi omylem nepoužil write endpoint (žádný v tomto skillu).
2. Pokud volání bylo read a token je read-only → kontaktuj FIO podporu, něco není v pořádku.
3. Pokud klient omylem token nastavil s IP whitelist a běžíš z jiné IP → klient musí v IB whitelist upravit.

### 404 Not Found

**Co se stalo:**
- Špatně sestavená URL (překlep v endpointu).
- Neexistující výpis ve `/by-id/{rok}/{cislo}/` (např. výpis 99 v roce 2026, který nikdy nebyl).

**Akce:**
1. Zkontroluj URL proti `references/endpoints.md`.
2. Pokud `/by-id/` → volej `/lastStatement/` pro zjištění posledního dostupného čísla.

### 409 Conflict (Rate limit)

**Co se stalo:** Stejný token byl volán v posledních 30 sekundách.

**Akce:**
- `scripts/fio_get.py` retry automaticky (30 s → 60 s → 120 s).
- Pokud retry vyčerpán → pravděpodobně **jiný proces** používá stejný token (cron, jiný agent). Zkontroluj.
- **NIKDY nevolat opakovaně v cyklu bez prodlevy.** I když dostaneš 409, počkej alespoň 30 s před dalším pokusem.

### 500 / 503 Server Error

**Co se stalo:** FIO API má vnitřní problém nebo výpadek.

**Akce:**
1. Retry za 1–5 minut.
2. Pokud přetrvává >15 minut, podívej se na FIO status (stránka FIO, případně Twitter).
3. Hláška uživateli, ať počká a zkusí později.

## Network errors (mimo HTTP)

### Connection timeout

**Možné příčiny:**
- VPS klienta nemá internet (firewall).
- DNS resolver problém.
- FIO server pomalý / down.

**Akce:**
- Helper `fio_get.py` má `timeout=30` s. Po timeoutu vyhodí exception.
- Retry za 1–2 minuty.

### SSL error

**Akce:**
- Zkontroluj systémový čas na VPS (`date`). Špatný čas → SSL cert validace selže.
- Aktualizuj `ca-certificates` v kontejneru pokud problém přetrvává.

## Obecné principy

### Neopakuj nekonečně

Při jakékoli chybě **maximálně 3 retry**. Pak nech agenta rozhodnout, zda dál pokračovat (zeptej se uživatele) nebo zda failnout.

### Neukazuj token v hlášce

Pokud chyba obsahuje URL s tokenem, **maskuj ho** před zobrazením uživateli:

```python
def safe_error(url: str, token: str) -> str:
    return url.replace(token, "{TOKEN}")
```

Helper `fio_get.py` to dělá automaticky v error message.

### Logování

Při debug logu **VŽDY** maskuj token. Ideálně použij `--debug` flag helperu, který tohle řeší.
