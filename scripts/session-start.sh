#!/usr/bin/env bash
# SessionStart-Hook (lokal + Cloud): neuesten Stand holen und offene Aufträge anzeigen.
cd "$(dirname "$0")/.." || exit 0
scripts/sync.sh pull >/dev/null 2>&1 || echo "[OnTheGo] Hinweis: Pull fehlgeschlagen – 'git status' prüfen."
offen=$(ls auftraege/offen/*.md 2>/dev/null | wc -l | tr -d ' ')
arbeit=$(ls auftraege/in-arbeit/*.md 2>/dev/null | wc -l | tr -d ' ')
echo "[OnTheGo] Repo aktuell. Aufträge: ${offen} offen, ${arbeit} in Arbeit."
for f in auftraege/in-arbeit/*.md auftraege/offen/*.md; do [ -f "$f" ] && echo "  - $f"; done
exit 0
