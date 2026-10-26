#!/bin/sh
# Archivuje autopilot config z verzí < 2.2 (gen1 tvar: "active" flag, rozvrh
# v configu, jediný společný cron) — agent ho jinak imituje místo aktuální
# per-kanál architektury (nález N9). Idempotentní; gen2 config (channels)
# nechává být.
set -eu
CFG="/documents/content/autopilot/config.json"
[ -f "$CFG" ] || exit 0
grep -q '"active"' "$CFG" || exit 0
grep -q '"channels"' "$CFG" && exit 0
ARCHIVE="/documents/content/autopilot/archive-pre-2.2"
mkdir -p "$ARCHIVE"
mv "$CFG" "$ARCHIVE/config.json"
[ -f /documents/content/autopilot/setup.md ] && mv /documents/content/autopilot/setup.md "$ARCHIVE/setup.md" || true
cat > /documents/content/autopilot/MIGRATED.md <<'NOTE'
# Zastaralá konfigurace přesunuta (migrace skillu content-strategist)

Původní `config.json` (starší verze skillu) je v `archive-pre-2.2/`.
NEKOPÍRUJ jeho tvar ani postup — aktuální schéma a postup určuje výhradně
SKILL.md: vlastní pravidelný úkol per kanál + ohlašovací úkol, config bez
rozvrhu a bez `active` flagu (zdroj pravdy o zapnutí = existence cronu).
NOTE
echo "[migrace] gen1 autopilot config archivován do ${ARCHIVE}"
