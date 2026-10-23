# OnTheGo

Zwei-Wege-Hub: Aufträge und Ergebnisse laufen über dieses Repo zwischen **Mac (lokal)** und **Claude Code in der Cloud** (Handy/Web) – in beide Richtungen.

```
 Mac (Claude Code lokal) ──push/pull──▶  GitHub main  ◀──push/pull── Cloud-Session (Handy/Web)
        ▲ launchd alle 5 min                                    ▲ SessionStart-/Stop-Hook
```

## Einrichtung auf dem Mac (einmalig)
```bash
git clone https://github.com/infoyngkid-creator/OnTheGo.git ~/OnTheGo
~/OnTheGo/scripts/mac-setup.sh        # Auto-Sync alle 5 Minuten
cd ~/OnTheGo && claude                # Claude lokal im Repo starten
```
Optional, damit du vom Handy aus direkt den Mac steuern kannst: im Repo `claude remote-control` starten –
die Session erscheint dann in der Claude-App.

## Benutzung
- **Neuer Auftrag:** `scripts/neuer-auftrag.sh "Titel" "Beschreibung"` oder Claude darum bitten.
- **Manuell syncen:** `scripts/sync.sh`
- Claude-Sessions (lokal & Cloud) ziehen beim Start automatisch und pushen nach jeder Antwort.

## Sicherheit
Keine API-Keys/Passwörter ins Repo. Lokal: `.env` (ignoriert). Cloud: Environment-Variablen in claude.ai/code.
