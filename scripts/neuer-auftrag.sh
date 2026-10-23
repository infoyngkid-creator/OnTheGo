#!/usr/bin/env bash
# Legt einen neuen Auftrag an und synct ihn sofort.
#   scripts/neuer-auftrag.sh "Titel des Auftrags" ["Beschreibung"]
set -euo pipefail
cd "$(dirname "$0")/.."
titel="${1:?Titel angeben}"; beschr="${2:-}"
slug="$(printf '%s' "$titel" | LC_ALL=C tr '[:upper:]' '[:lower:]' | LC_ALL=C tr -cs 'a-z0-9' '-' | sed -E 's/^-+|-+$//g')"
datei="auftraege/offen/$(date '+%Y-%m-%d')-${slug}.md"
cat > "$datei" <<MD
---
titel: ${titel}
erstellt: $(date '+%Y-%m-%d %H:%M')
von: $( [ -n "${CLAUDE_CODE_REMOTE:-}" ] && echo cloud || echo lokal )
status: offen
ort: egal   # egal | lokal | cloud
---

## Auftrag
${beschr}

## Fortschritt
-

## Ergebnis
MD
echo "Angelegt: $datei"
scripts/sync.sh
