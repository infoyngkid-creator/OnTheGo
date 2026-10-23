#!/usr/bin/env bash
# Ruft den Nutzer über Bland AI an (lokal + Cloud).
#   scripts/anruf.sh "Worum es geht / was gefragt werden soll" [+49...]
#   scripts/anruf.sh --status <call_id>     -> Status + Transkript abrufen
# Braucht: BLAND_API_KEY (Cloud: Environment-Secret, lokal: .env)
#          ONTHEGO_PHONE (Zielnummer, E.164 z. B. +49170...) oder 2. Argument
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
: "${BLAND_API_KEY:?BLAND_API_KEY fehlt (Cloud: Environment-Secret, lokal: .env)}"

if [ "${1:-}" = "--status" ]; then
  curl -sS "https://api.bland.ai/v1/calls/${2:?call_id angeben}" -H "authorization: $BLAND_API_KEY" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print("Status:", d.get("status"), "| Dauer:", d.get("call_length")); print(d.get("concatenated_transcript") or "")'
  exit 0
fi

anliegen="${1:?Anliegen angeben}"
nummer="${2:-${ONTHEGO_PHONE:-}}"
: "${nummer:?Zielnummer fehlt (ONTHEGO_PHONE oder 2. Argument)}"

payload="$(python3 - "$nummer" "$anliegen" <<'PY'
import json, sys
nummer, anliegen = sys.argv[1], sys.argv[2]
print(json.dumps({
  "phone_number": nummer,
  "language": "de",
  "wait_for_greeting": True,
  "max_duration": 5,
  "first_sentence": "Hallo, hier ist Claude von deinem OnTheGo-Repo. Hast du kurz Zeit?",
  "task": ("Du bist Claude, der Assistent des Nutzers. Sprich Deutsch, kurz und freundlich. "
           "Grund des Anrufs: " + anliegen + " "
           "Stell die nötigen Fragen, hör zu, fasse die Antworten am Ende kurz zusammen und verabschiede dich."),
}))
PY
)"
curl -sS https://api.bland.ai/v1/calls -H "authorization: $BLAND_API_KEY" -H "Content-Type: application/json" -d "$payload"
echo
