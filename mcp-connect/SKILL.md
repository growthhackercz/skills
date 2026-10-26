---
name: MCP Connect
description: Připoj a spravuj MCP servery (Model Context Protocol) v OpenClaw runtime přes `openclaw mcp` — agenti tak získají nativní externí tooly
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-06-26"
---

# MCP Connect

Umožní ti **připojit externí MCP server** (Model Context Protocol) do běhu OpenClaw.
Po připojení se tooly serveru *materializují* jako nativní agentí tooly (které pak
smí volat agenti, kteří mají daný MCP v tool policy).

MCP server je buď **HTTP** (vzdálená služba s URL) nebo **stdio** (lokální proces,
který se spustí příkazem). Konfigurace žije v `mcp.servers` v `openclaw.json` a spravuje
se výhradně přes CLI `openclaw mcp` — needituj `openclaw.json` ručně.

> Vyžaduje `exec` tool. Přidání serveru může být za exec-approvalem podle exec policy.
> Hlavičky/secrets nikdy nevypisuj do chatu; ber je z env proměnných.

## Přidat HTTP MCP server

```bash
openclaw mcp add <jmeno> \
  --url <https URL> \
  --transport streamable-http \      # nebo: sse
  --header "Authorization=Bearer $TOKEN" \
  --header "X-Custom=hodnota"
```

`add` se **před uložením připojí a oprobuje** (proto případnou chybu uvidíš hned).
Když nechceš probovat, přidej `--no-probe`. OAuth server: `--auth oauth` + následně
`openclaw mcp login <jmeno>`.

## Přidat stdio MCP server (lokální proces)

```bash
openclaw mcp add <jmeno> \
  --command npx \
  --arg -y --arg @some/mcp-server \
  --env "API_KEY=$API_KEY" \
  --cwd /home/node
```

## Omezit, které tooly server vystaví

```bash
openclaw mcp add <jmeno> --url <url> --include "create_*,list_*"   # jen tyhle
openclaw mcp add <jmeno> --url <url> --exclude "delete_*"          # všechny krom těchto
```

## Spravovat existující servery

```bash
openclaw mcp list                       # přehled nakonfigurovaných serverů
openclaw mcp show <jmeno>               # detail jednoho serveru
openclaw mcp probe                      # připoj se a vypiš dostupné tooly/capabilities
openclaw mcp doctor                     # statická kontrola konfigurace
openclaw mcp configure <jmeno> --disable   # dočasně vypnout (nebo --enable)
openclaw mcp configure <jmeno> --exclude "risky_tool"
openclaw mcp reload                     # zahodit cache, nová konfigurace platí od dalšího běhu
```

## Postup, který drž

1. Zjisti typ serveru (HTTP URL, nebo stdio příkaz) a potřebné credentials.
2. Přidej server přes `openclaw mcp add …` (nech proběhnout probe — ověří spojení).
3. `openclaw mcp probe` / `openclaw mcp doctor` → potvrď, že server jede a vidíš jeho tooly.
4. Pokud server nabízí destruktivní operace, omez je přes `--include`/`--exclude`.
5. `openclaw mcp reload`, aby se nová konfigurace načetla.
6. Operátorovi stručně napiš: jaký server, jaké tooly, a jestli je potřeba ještě
   povolit MCP tooly v tool policy konkrétního agenta (to je samostatný krok mimo tenhle skill).

## Co NEDĚLAT

- Needituj `mcp.servers` v `openclaw.json` ručně — používej `openclaw mcp`.
- Nepřidávej neznámé/nedůvěryhodné MCP servery bez potvrzení operátora.
- Nevypisuj tokeny/hlavičky do chatu ani do task výstupů.
