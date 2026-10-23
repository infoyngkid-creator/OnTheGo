#!/usr/bin/env bash
# Zwei-Wege-Sync: holt Änderungen von GitHub und schiebt lokale Änderungen hoch.
# Läuft auf dem Mac (manuell / launchd) und in Cloud-Sessions (Hooks).
#   scripts/sync.sh            -> pull + commit + push
#   scripts/sync.sh pull       -> nur pull
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

BRANCH="${ONTHEGO_BRANCH:-main}"
HOST="$( [ -n "${CLAUDE_CODE_REMOTE:-}" ] && echo cloud || hostname -s 2>/dev/null || echo lokal )"

retry() { local n=0 d=2; until "$@"; do n=$((n+1)); [ $n -ge 4 ] && return 1; sleep $d; d=$((d*2)); done; }

# Nur syncen, wenn wir auf dem Sync-Branch sind (Feature-Branches nicht anfassen).
current="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
if [ "$current" != "$BRANCH" ]; then
  echo "[sync] auf Branch '$current' statt '$BRANCH' – übersprungen."; exit 0
fi

if [ "${1:-}" != "pull" ] && [ -n "$(git status --porcelain)" ]; then
  git add -A
  msg="sync: ${HOST} $(date '+%Y-%m-%d %H:%M')"
  [ -n "${ONTHEGO_COMMIT_TRAILER:-}" ] && msg="$msg"$'\n\n'"$ONTHEGO_COMMIT_TRAILER"
  git commit -q -m "$msg" || true
fi

retry git pull -q --rebase --autostash origin "$BRANCH" || {
  echo "[sync] Pull fehlgeschlagen (Konflikt?). Bitte 'git status' prüfen."; git rebase --abort 2>/dev/null; exit 1; }

[ "${1:-}" = "pull" ] && { echo "[sync] aktualisiert."; exit 0; }

if [ -n "$(git log "origin/$BRANCH..HEAD" --oneline 2>/dev/null)" ]; then
  retry git push -q -u origin "$BRANCH" && echo "[sync] hochgeladen." || { echo "[sync] Push fehlgeschlagen."; exit 1; }
else
  echo "[sync] nichts hochzuladen."
fi
