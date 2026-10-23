# OnTheGo – Zwei-Wege-Hub zwischen Mac (lokal) und Cloud

Dieses Repo ist die gemeinsame Ablage für **alle Aufträge, Notizen und Ergebnisse**.
Es wird sowohl lokal auf dem Mac als auch in Claude-Code-Cloud-Sessions (Handy/Web) genutzt.
GitHub (`main`) ist die einzige Quelle der Wahrheit.

## Regeln für Claude (lokal UND Cloud)
1. **Beim Start**: Der SessionStart-Hook macht `git pull`. Danach `auftraege/in-arbeit/` und `auftraege/offen/` lesen.
2. **Auftrag übernehmen**: Datei von `offen/` nach `in-arbeit/` verschieben (`git mv`), `status:` anpassen, sofort `scripts/sync.sh`.
3. **Während der Arbeit**: Fortschritt im Abschnitt „Fortschritt“ der Auftragsdatei festhalten – so kann die jeweils andere Seite nahtlos weitermachen.
4. **Fertig**: Ergebnis eintragen, nach `erledigt/` verschieben, `scripts/sync.sh`.
5. **Ende jeder Antwort**: Der Stop-Hook ruft `scripts/sync.sh` auf (commit + push auf `main`). Bei Konflikt: auflösen, nicht force-pushen.
6. `ort: lokal` = braucht den Mac (lokale Apps/Dateien). Cloud-Session legt dann nur Notizen an und überlässt es der lokalen Session.
7. **Keine Geheimnisse committen** (API-Keys, Passwörter, Tokens). Das Repo kann öffentlich sein. Keys gehören in `.env` (lokal) bzw. Environment-Variablen (Cloud).
8. Größere Code-Projekte: als Unterordner unter `projekte/<name>/` oder als eigenes Repo; hier dann nur der Auftrag mit Link.

## Struktur
- `auftraege/offen|in-arbeit|erledigt/` – Aufträge als Markdown (Vorlage: `scripts/neuer-auftrag.sh`)
- `notizen/` – freie Notizen, Kontext, Wissen
- `projekte/` – Arbeitsergebnisse/Code
- `scripts/` – `sync.sh`, `neuer-auftrag.sh`, `mac-setup.sh`, `session-start.sh`

## Verbundene Dienste (über claude.ai-Konnektoren, lokal & Cloud gleich)
Gmail, Google Drive, GitHub. Weitere (Slack, Notion, Linear, …) müssen unter claude.ai → Einstellungen → Konnektoren autorisiert werden.

Sprache: Deutsch.
