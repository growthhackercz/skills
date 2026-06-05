# Custom doména — průvodce klientem

Krok-po-kroku návod pro klienta, jak napojit jeho doménu na Netlify site.
CTO agent ho použije při `add-domain` workflow.

---

## Princip

Klient má dvě možnosti, jak doménu napojit:

| Metoda | Kdy zvolit | Setup |
|---|---|---|
| **A) CNAME u externího DNS providera** | Klient má doménu u Forpsi/CZ.NIC/Wedos/Active 24 a chce ji tam nechat | Klient přidá 1 CNAME záznam |
| **B) Delegace na Netlify DNS** | Klient chce mít plnou kontrolu nad DNS přes Netlify UI | Klient změní nameservery u registrátora na Netlify |

**Default doporučení = A (CNAME).** Je to méně invazivní, klient nepřesouvá DNS hosting.

---

## Metoda A — CNAME u externího providera

### Krok 1: Klient zjistí Netlify site URL

CTO agent klientovi sdělí cílovou URL z `ensure-site` outputu, např.:
```
obrat-dashboard.netlify.app
```

### Krok 2: Klient přidá CNAME u svého DNS providera

**Univerzální parametry pro CNAME:**

| Pole | Hodnota |
|---|---|
| Typ záznamu | `CNAME` |
| Host / Název | `dashboard` (pokud chce `dashboard.firma.cz`) nebo `@` (pro `firma.cz`) |
| Cíl / Hodnota | `obrat-dashboard.netlify.app` (= Netlify site URL bez `https://`) |
| TTL | `3600` (1 hodina) |

**Pozor pro apex doménu** (`firma.cz` bez subdomény): CNAME na apex není
podporován většinou DNS providerů. Klient musí použít buď:
- `ALIAS` / `ANAME` záznam (pokud provider podporuje)
- Nebo přesměrovat na `www.firma.cz` (subdoména) a přidat tam CNAME
- Nebo delegovat na Netlify DNS (metoda B)

### Krok 3: Návody pro konkrétní české providery

#### Forpsi (forpsi.com)

1. Přihlas se na [admin.forpsi.com](https://admin.forpsi.com)
2. **Domény** → vyber doménu → **DNS servery a záznamy**
3. **Přidat nový záznam DNS**
4. Vyplň:
   - Typ: `CNAME`
   - Subdoména: `dashboard` (pro `dashboard.firma.cz`)
   - Cíl: `obrat-dashboard.netlify.app.` (s tečkou na konci!)
   - TTL: `3600`
5. **Uložit**
6. Propagace: 30 min — 4 hodiny

#### CZ.NIC (registr.cz)

CZ.NIC je jen registr, DNS hosting bývá u jiného providera. Identifikuj kde
běží DNS klientova doména:

```bash
dig +short NS firma.cz
```

Pak postupuj podle providera (Forpsi, Wedos, Active 24, Cloudflare, ...).

#### Wedos (wedos.cz)

1. Přihlas se na [client.wedos.com](https://client.wedos.com)
2. **Domény** → vyber doménu → **DNS záznamy**
3. **Přidat nový záznam**
4. Vyplň:
   - Typ: `CNAME`
   - Název: `dashboard.firma.cz.` (FQDN s tečkou)
   - RDATA: `obrat-dashboard.netlify.app.`
   - TTL: `3600`
5. **Uložit a aktivovat**
6. Propagace: 30 min — 24 hodin

#### Active 24 (active24.cz)

1. Přihlas se na [admin.active24.com](https://admin.active24.com)
2. **Domény** → vyber doménu → **DNS záznamy**
3. **Nový záznam** → typ `CNAME`
4. Vyplň:
   - Host: `dashboard`
   - Hodnota: `obrat-dashboard.netlify.app`
   - TTL: `3600`
5. **Uložit**
6. Propagace: 1—4 hodiny

#### Cloudflare

1. Přihlas se na [dash.cloudflare.com](https://dash.cloudflare.com)
2. Vyber doménu → **DNS** → **Records**
3. **Add record**
4. Vyplň:
   - Type: `CNAME`
   - Name: `dashboard`
   - Target: `obrat-dashboard.netlify.app`
   - Proxy status: **DNS only** (šedý mrak, NE oranžový — Cloudflare Proxy by konfliktoval s Netlify SSL)
   - TTL: Auto
5. **Save**
6. Propagace: okamžitá (Cloudflare je rychlý)

### Krok 4: Klient potvrdí „hotovo"

Klient v CC chatu napíše „hotovo", „přidal jsem", „je to nastavené".

### Krok 5: CTO agent zavolá publisher

```bash
python3 scripts/netlify_publish.py add-domain --site-id <id> --domain dashboard.firma.cz --json
python3 scripts/netlify_publish.py verify-domain --site-id <id> --domain dashboard.firma.cz --json
```

`add-domain` registruje doménu u Netlify. `verify-domain` poll-uje SSL
provisioning (max 5 min). SSL je auto-provisionován přes Let's Encrypt.

### Krok 6: Hotovo

```
Doména dashboard.firma.cz je aktivní s SSL.
URL: https://dashboard.firma.cz
```

---

## Metoda B — Delegace na Netlify DNS

Klient přesouvá DNS hosting kompletně na Netlify (nameserver change).

### Kdy to dává smysl

- Klient chce mít všechny DNS záznamy na jednom místě (Netlify dashboard)
- Klient potřebuje wildcard SSL pro `*.firma.cz` (Netlify auto-provisionuje)
- Klient deployuje víc projektů na různé subdomény jedné domény
- Klient chce **apex doménu** `firma.cz` na Netlify (CNAME na apex nefunguje
  u většiny providerů, ALIAS/ANAME ano, ale Netlify DNS je nejjistější)

### Postup

1. V Netlify dashboardu: **Domains** → **Add domain** → zadej `firma.cz`
2. Netlify zobrazí 4 nameservery (např. `dns1.p01.nsone.net`, ...)
3. Klient se přihlásí na **registrátora** (Forpsi, Wedos, ...) a změní
   **nameservery** na Netlify hodnoty
4. Propagace: 24—48 hodin (změna nameserverů je pomalejší než CNAME)
5. Po propagaci Netlify auto-provisionuje SSL pro celou doménu

**Pozor:** delegace přesouvá VŠECHNY DNS záznamy. Klient musí předem migrovat
e-mailové MX záznamy, případné A záznamy pro jiné služby, atd. Vždy se
klienta zeptej, jestli má v aktuálním DNS jiné záznamy (MX, TXT pro SPF/DKIM,
A pro VPN, ...) a před delegací je všechny převést do Netlify DNS.

---

## Edge cases

### „CNAME nemůže být na apex" error

Klient chce `firma.cz` (apex, bez subdomény). Řešení:
- Použít `www.firma.cz` jako primary + apex redirect na `www.`
- Nebo Metoda B (Netlify DNS)
- Nebo provider s `ALIAS`/`ANAME` podporou (Cloudflare, AWS Route 53)

### SSL provisioning > 30 min

Netlify SSL přes Let's Encrypt obvykle trvá 5—30 min. Pokud >1 hodinu:
- Zkontroluj, že CNAME ukazuje na správnou Netlify URL (`dig CNAME dashboard.firma.cz`)
- Cloudflare uživatelé: ověř, že Proxy status je **DNS only** (šedý mrak)
- Zkus přes Netlify UI: site → **Domain management** → **HTTPS** → **Renew certificate**

### DNS propagation > 24 hodin

Většina providerů má TTL 3600 (1 hod) nebo méně. Pokud klient měl TTL 86400
(24 hod), může to trvat déle. Zkontroluj přes:
```bash
dig +short CNAME dashboard.firma.cz
```

### Klient nemá přístup k DNS providerovi

Klient někdy nezná své DNS credentials (registroval doménu před lety,
správce odešel, ...). Řešení:
- Doporuč klientovi kontaktovat svého IT správce
- Nebo pomocnou alternativu: subdoména pod doménou, kterou klient ovládá
- Nebo dočasně publikovat na Netlify default URL (`obrat-dashboard.netlify.app`)
  a custom doménu vyřešit později

---

## Co publisher dělá automaticky

Po klientově „hotovo":

1. `add-domain` zavolá `netlify api updateSite` s `custom_domain`
2. Netlify spustí SSL provisioning (Let's Encrypt)
3. `verify-domain` poll-uje status max 5 min (interval 15 s)
4. Pokud SSL aktivní → vrátí klientovi `https://dashboard.firma.cz`
5. Pokud timeout → vrátí klientovi „SSL provisioning trvá obvykle 5—30 min,
   zavolej `verify-domain` znovu za chvíli"

Klient nikdy nemusí otevírat Netlify dashboard.
