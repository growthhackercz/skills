---
name: Active24 DNS
description: Automaticky nastaví DNS záznamy u Active24 pro připojení vlastní domény na web (typicky publikovaný přes netlify-publisher). Najde spravovanou zónu, apex doménu nasměruje A záznamem na Netlify (75.2.60.5), subdoménu (např. www) CNAME záznamem na <site>.netlify.app. Použij po publikaci webu, když klient připojuje vlastní doménu vedenou na Active24. Vyžaduje ACTIVE24_API_KEY (identifikátor) a ACTIVE24_API_SECRET (tajný).
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":["ACTIVE24_API_KEY","ACTIVE24_API_SECRET"]},"primaryEnv":"ACTIVE24_API_SECRET","emoji":"🌐"}}
category: integrations
status: ready
version: "2.0"
publishedAt: "2026-06-17"
---

# Active24 DNS

Připojí vlastní doménu vedenou u **Active24** na publikovaný web (Netlify), tím že
**automaticky založí DNS záznamy** přes Active24 **v2** REST API. Nahrazuje ruční zadávání
CNAME/A u registrátora. Společné rozhraní s `cloudflare-dns` (stejný `connect`/`list`).
Idempotentní — existující záznam aktualizuje, nezdvojuje.

API: `https://rest.active24.cz` (v2). Auth = **HMAC-SHA1 podepsané requesty** (ne Bearer):
- `canonicalRequest = "{METHOD} {path-bez-query} {unixČas}"`
- `signature = hex(HMAC-SHA1(tajný, canonicalRequest))`
- hlavičky: `Authorization: Basic base64("{identifikátor}:{signature}")` + `Date: YYYYMMDDTHHMMSSZ` (UTC, stejný okamžik).

**Credentials** (z Active24 panelu): `ACTIVE24_API_KEY` = identifikátor, `ACTIVE24_API_SECRET` = tajný. Per-tenant injektuje CC přes SecretRef.

## Co skill dělá

1. **`list`** — bez `--domain` vypíše domény se spravovaným DNS (`GET /v1/user/self/service`);
   s `--domain` vypíše záznamy zóny (`GET /v2/service/{service}/dns/record`, stránkováno).
2. **`connect <fqdn> --target <site>.netlify.app`** — připojí doménu na web:
   - resolve **service/zóny** přes `GET /v1/user/self/zone/{doména}`,
   - **apex** (zóna == fqdn) → A záznam na **`75.2.60.5`** (Netlify),
   - **subdoména** (např. `www`) → CNAME na `<target>`,
   - `name` záznamu je **plné FQDN**; vytvoří `POST /v2/service/{service}/dns/record`, nebo
     `PUT …/{record}` když už existuje (idempotentní).

## Použití

```bash
export ACTIVE24_API_KEY=...      # identifikátor (per-tenant, injektuje CC přes SecretRef)
export ACTIVE24_API_SECRET=...   # tajný
python3 scripts/active24_dns.py list
python3 scripts/active24_dns.py list --domain example.cz
python3 scripts/active24_dns.py connect www.example.cz --target mysite.netlify.app
python3 scripts/active24_dns.py connect example.cz --target mysite.netlify.app   # apex → A 75.2.60.5
```

## Kdy použít

- Po `netlify-publisher` (web je live na `<site>.netlify.app`) a klient chce vlastní doménu
  vedenou na Active24. Pro domény na Cloudflare použij `cloudflare-dns`.

## Pozn.

Auth + read endpointy (`list`) ověřeny proti živému v2 API (2026-06-17). Zápisové operace
(`connect` → POST/PUT záznamu) jsou dle v2 specu (`rest.active24.cz/v2/docs/openapi.json`);
na produkční doméně je vhodné je poprvé ověřit kontrolovaně.
