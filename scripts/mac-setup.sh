#!/usr/bin/env bash
# Einmalig auf dem Mac ausführen:
#   git clone https://github.com/infoyngkid-creator/OnTheGo.git ~/OnTheGo && ~/OnTheGo/scripts/mac-setup.sh
# Richtet einen launchd-Job ein, der alle 5 Minuten synct.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.onthego.sync"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
INTERVAL="${1:-300}"

chmod +x "$REPO"/scripts/*.sh
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"

cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$REPO/scripts/sync.sh</string></array>
  <key>StartInterval</key><integer>$INTERVAL</integer>
  <key>RunAtLoad</key><true/>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string></dict>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/onthego-sync.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/onthego-sync.log</string>
</dict></plist>
PL

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "✅ Auto-Sync aktiv (alle ${INTERVAL}s). Log: ~/Library/Logs/onthego-sync.log"
echo "   Deaktivieren: launchctl unload $PLIST"
