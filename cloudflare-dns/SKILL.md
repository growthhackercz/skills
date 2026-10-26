---
name: Cloudflare DNS
description: Automaticky nastaví DNS záznam u Cloudflare pro připojení vlastní domény na web (typicky publikovaný přes netlify-publisher). Najde zónu, založí CNAME na <site>.netlify.app (díky CNAME flattening funguje i apex). DNS-only (neproxuje), aby Netlify zvládl TLS. Použij když je doména vedená na Cloudflare. Vyžaduje CLOUDFLARE_API_TOKEN (Zone:DNS:Edit + Zone:Read).
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":["CLOUDFLARE_API_TOKEN"]},"primaryEnv":"CLOUDFLARE_API_TOKEN","emoji":"🌐"}}
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-06-16"
---

# Cloudflare DNS

Připojí vlastní doménu vedenou na **Cloudflare** na publikovaný web (Netlify) — **automaticky
založí CNAME** přes Cloudflare API v4. Společné rozhraní s `active24-dns` (`connect`/`list`).

API: `https://api.cloudflare.com/client/v4`, auth `Authorization: Bearer $CLOUDFLARE_API_TOKEN`
(token scope **Zone:DNS:Edit** + **Zone:Read**).

## Co skill dělá

1. **`list`** — vypíše zóny (`GET /zones`), u `--domain` i DNS záznamy.
2. **`connect <fqdn> --target <site>.netlify.app`** — najde zónu, založí **CNAME** záznam
   `name=<fqdn>` → `content=<target>`, **`proxied=false`** (DNS-only, Netlify řeší TLS/CDN).
   Díky **CNAME flattening** Cloudflare zvládne CNAME i na apexu, takže apex i subdoména jdou
   stejně. (`POST /zones/{id}/dns_records`.)

## Použití

```bash
export CLOUDFLARE_API_TOKEN=...   # per-tenant, injektuje CC přes SecretRef
python3 scripts/cloudflare_dns.py list --domain example.com
python3 scripts/cloudflare_dns.py connect www.example.com --target mysite.netlify.app
python3 scripts/cloudflare_dns.py connect example.com --target mysite.netlify.app   # apex (flattening)
```

## Kdy použít

- Po `netlify-publisher` a klient připojuje doménu vedenou na Cloudflare. Pro domény na Active24
  použij `active24-dns`.
