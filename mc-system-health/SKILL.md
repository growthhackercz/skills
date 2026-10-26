---
name: mc-system-health
description: "Kontroluje Control Center, runtime OpenClaw, dokumenty, wiki, disk, paměť a recent runtime logy z kontejneru agenta"
category: operations
status: ready
version: "1.0"
publishedAt: "2026-04-25"
---

# System Health Check

Použij tento skill, když se uživatel ptá, jestli je platforma zdravá, když je
nahlášen technický problém nebo během plánované diagnostiky platformy.

Tento skill běží uvnitř kontejneru OpenClaw. Nepředpokládej přístup na úrovni
hostu. Nespouštěj tady `docker`, `systemctl`, `journalctl` ani `sqlite3`.
Pokud je potřeba kontrola služeb na hostu, řekni operátorovi, co má
zkontrolovat.

## Quick Health Check

Nejdřív spusť tyto kontroly:

```bash
CC="${CC_URL:-http://control-center:3000}"

echo "=== Control Center API ==="
curl -fsS "$CC/api/health" >/dev/null && echo "OK" || echo "FAIL"

echo "=== OpenClaw Gateway ==="
curl -fsS "http://127.0.0.1:18789/health" >/dev/null && echo "OK" || \
curl -fsS "http://openclaw:18789/health" >/dev/null && echo "OK" || echo "FAIL"

echo "=== Documents root ==="
test -d /documents && test -w /documents && echo "OK" || echo "FAIL"

echo "=== OpenClaw state ==="
test -d "$HOME/.openclaw" && test -w "$HOME/.openclaw" && echo "OK" || echo "FAIL"
```

## Disk a paměť

```bash
echo "=== Disk ==="
df -h / /documents "$HOME/.openclaw" 2>/dev/null

echo "=== Directory sizes ==="
du -sh /documents "$HOME/.openclaw" 2>/dev/null

echo "=== Memory ==="
free -h
```

## Wiki vault

```bash
echo "=== Wiki vault ==="
test -d /documents/wiki/main && echo "wiki exists" || echo "wiki missing"
find /documents/wiki/main -type f -name '*.md' 2>/dev/null | wc -l
du -sh /documents/wiki/main 2>/dev/null || true
```

## Recent Runtime Logy

Používej lokální runtime logy místo host journal příkazů:

```bash
echo "=== Runtime log errors ==="
for log in "$HOME/.openclaw/logs/runtime.log" /tmp/openclaw/*.log; do
  test -f "$log" || continue
  echo "--- $log"
  grep -iE "error|failed|exception|unauthorized|permission denied|not found" "$log" | tail -40 || true
done
```

## Volitelné kontroly Control Centeru

Použij Control Center API, když je dostupné:

```bash
CC="${CC_URL:-http://control-center:3000}"
KEY="${CC_API_KEY:-${API_KEY:-}}"

if [ -n "$KEY" ]; then
  echo "=== Agents ==="
  curl -fsS "$CC/api/agents" -H "x-api-key: $KEY" | python3 -m json.tool | head -80

  echo "=== Open tasks ==="
  curl -fsS "$CC/api/tasks?status=inbox,assigned,in_progress&limit=20" \
    -H "x-api-key: $KEY" | python3 -m json.tool | head -120
fi
```

## Co reportovat

Reportuj v jazyce uživatele:

- co je OK
- co selhává
- jestli je problém uvnitř Control Centeru, OpenClaw runtime, documents/wiki,
  model auth nebo host/container infrastruktury
- co můžeš udělat z runtime agenta
- co vyžaduje přístup operátora nebo serveru

## Eskalace

Pokud kontrola vyžaduje `docker`, `systemctl`, `journalctl`, přímý volume access
nebo instalaci balíčků, nepředstírej, že jsi to spustil. Řekni jasně:

> I cannot verify host-level service state from inside the agent runtime. The
> operator should check container status and host logs.

Pak vypiš přesné host-level kontroly, které má operátor spustit.
