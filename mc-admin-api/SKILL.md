---
name: mc-admin-api
description: "Správa agentů, dovedností, nastavení a integrací prostřednictvím Control Center API"
category: integrations
status: ready
version: "1.2"
publishedAt: "2026-09-14"
---

# Control Center Admin API

Platformu můžete spravovat prostřednictvím těchto koncových bodů HTTP. Použijte `curl` prostřednictvím vašeho nástroje exec.

**Základní adresa URL:** $CC_URL
**Záhlaví ověření:** `-H "x-api-key: $CC_API_KEY"`

`***`, `[masked]`, `[redacted]`, `OPENCLAW_REDACTED` a
`__OPENCLAW_REDACTED__` jsou jen zobrazovací zástupné hodnoty, nikdy vstupní
credential. Nekopíruj je do příkazů ani skriptů. Zachovej shellový odkaz
`$CC_API_KEY` nebo `${CC_API_KEY}` až do provedení příkazu. `401` s kódem
`AUTH_REDACTED_PLACEHOLDER` znamená, že příkaz omylem použil zástupnou hodnotu:
sestav jej znovu z runtime proměnné. Není to důvod k výměně klíče, provider
fallbacku ani restartu.

## Agenti

### Seznam všech agentů
```bash
curl -s "$CC_URL/api/agents" -H "x-api-key: $CC_API_KEY"
```

### Aktualizovat agenta
```bash
curl -s -X PUT "$CC_URL/api/agents" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"id": AGENT_ID, "name": "new-name", "role": "New Role"}'
```

### Synchronizační agenti (OpenClaw ↔ Control Center)
```bash
curl -s -X POST "$CC_URL/api/agents/sync" \
  -H "x-api-key: $CC_API_KEY"
```

## Dovednosti

### Vyjmenujte všechny dovednosti
```bash
curl -s "$CC_URL/api/local-skills" -H "x-api-key: $CC_API_KEY"
```

### Skenování katalogu dovedností (cs-skills/ + user-skills/)
```bash
curl -s -X POST "$CC_URL/api/local-skills/scan" \
  -H "x-api-key: $CC_API_KEY"
```

Odpověď obsahuje také read-only `invalidCount` a sanitizovaný seznam `invalid`; scan žádný skill automaticky nepřepisuje.

### Vytvořte dovednost
Nový `SKILL.md` musí mít ve frontmatteru `version: "1.0"` a `publishedAt: "YYYY-MM-DD"`.
`publishedAt` nastav na den zveřejnění aktuální verze. Při vydání nové verze ho
aktualizuj spolu s `version`; bez nové verze ho neměň. Control Center podle něj
zobrazuje štítek „Nový“ 14 dní od poslední publikované aktualizace.
Pokud tato metadata v requestu chybí, Control Center je doplní automaticky pro `user-skills`, ale při ruční tvorbě souboru je vždy zapiš explicitně.
Do `content` posílej tělo bez YAML frontmatteru. Starší klienti, kteří pošlou celý `SKILL.md`, zůstávají podporovaní a Control Center jejich úvodní frontmatter normalizuje na jeden.

```bash
curl -s -X POST "$CC_URL/api/local-skills" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"name": "skill-name", "category": "category", "content": "# Skill instructions...", "description": "What this skill does"}'
```

### Aktualizujte metadata dovednosti
```bash
curl -s -X PUT "$CC_URL/api/local-skills/SKILL_ID" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"description": "Updated description", "version": "1.1", "publishedAt": "2026-09-01"}'
```

### Aktualizujte obsah dovednosti
```bash
curl -s -X PUT "$CC_URL/api/local-skills/SKILL_ID/content" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"content": "# Updated instructions..."}'
```

Starší zápis přes `PUT /api/local-skills/SKILL_ID` s polem `content` zůstává kompatibilní, ale nový workflow používá oddělený `/content` endpoint.

### Přidělte agentovi dovednost
```bash
curl -s -X POST "$CC_URL/api/agents/AGENT_ID/skills" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"skill_id": "SKILL_ID"}'
```

### Odeberte agentovi dovednost
```bash
curl -s -X DELETE "$CC_URL/api/agents/AGENT_ID/skills?skill_id=SKILL_ID" \
  -H "x-api-key: $CC_API_KEY"
```

## Nastavení

### Přečtěte si všechna nastavení
```bash
curl -s "$CC_URL/api/settings" -H "x-api-key: $CC_API_KEY"
```

### Aktualizovat nastavení
```bash
curl -s -X PUT "$CC_URL/api/settings" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"key": "setting.key", "value": "new-value"}'
```

## Integrace

### Seznam integrací (se stavem)
```bash
curl -s "$CC_URL/api/integrations" -H "x-api-key: $CC_API_KEY"
```

### Integrace aktualizací (nastavení klíče API)
```bash
curl -s -X PUT "$CC_URL/api/integrations" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"provider": "openrouter", "vars": {"OPENROUTER_API_KEY": "sk-or-..."}}'
```

### Otestujte integrační připojení
```bash
curl -s -X POST "$CC_URL/api/integrations" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"action": "test", "provider": "openrouter"}'
```

## Cron Jobs

### Seznam všech úloh cronu
```bash
curl -s "$CC_URL/api/cron?action=list" -H "x-api-key: $CC_API_KEY"
```

### Přidat úlohu cron (opakující se)
```bash
curl -s -X POST "$CC_URL/api/cron" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"action": "add", "jobName": "my-job", "agentId": "ceo", "schedule": "0 9 * * *", "command": "Check inbox and summarize new emails"}'
```
Formát rozvrhu: standardní výraz cron (minuta hodina den měsíc v týdnu).
Pro jednorázové použití: použijte vzdálené datum a po prvním spuštění jej deaktivujte.

### Upravit existující opakující se úlohu cron
Nejdřív si načti seznam a vezmi přesné `id`, `name`, `schedule` a `command`:
```bash
curl -s "$CC_URL/api/cron?action=list" -H "x-api-key: $CC_API_KEY"
```

Pak uprav sérii přes `jobId`; pokud měníš název, pošli původní název jako `oldJobName`:
```bash
curl -s -X POST "$CC_URL/api/cron" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"action": "update", "jobId": "JOB_ID", "oldJobName": "Původní název", "jobName": "Nový název", "agentId": "ceo", "schedule": "0 9 * * 1-5", "command": "Nové zadání pro agenta"}'
```

### Přepnout úlohu cron (enable/disable = pauza/resume)
Toto pozastaví nebo obnoví celou opakující se sérii. Úloha zůstane uložená, jen se nebude spouštět, když je `enabled: false`.
```bash
curl -s -X POST "$CC_URL/api/cron" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"action": "toggle", "jobId": "JOB_ID", "jobName": "Název úlohy", "applyToSeries": true, "enabled": false}'
```

### Smazat celou opakující se úlohu cron
Používej pro zrušení série. `removeSeries: true` odstraní i skryté duplicitní záznamy se stejným názvem.
```bash
curl -s -X POST "$CC_URL/api/cron" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"action": "remove", "jobId": "JOB_ID", "jobName": "Název úlohy", "removeSeries": true}'
```

### Ruční spuštění úlohy cron
```bash
curl -s -X POST "$CC_URL/api/cron" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"action": "trigger", "jobId": "JOB_ID"}'
```

### Rozhodnutí: bash cron vs agent cron
- **Bash cron** (systemd timer): 0 LLM tokenů, pro rutinní kontroly (zdraví, zálohování, aktualizace)
- **Agent cron** (úloha OpenClaw cron): používá tokeny LLM pro úkoly vyžadující zdůvodnění
Použijte bash pro jednoduché kontroly, které probudí agenta pouze v případě potřeby.
Agent cron použijte pouze v případě, že úloha vyžaduje zdůvodnění LLM při každém spuštění.

## Servery MCP

### Seznam nakonfigurovaných serverů MCP
```bash
curl -s "$CC_URL/api/integrations/mcp" -H "x-api-key: $CC_API_KEY"
```

### Konfigurace serveru GHL MCP
```bash
curl -s -X POST "$CC_URL/api/integrations/mcp" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{"action": "configure-ghl", "apiKey": "pit-xxx", "locationId": "loc-xxx"}'
```
