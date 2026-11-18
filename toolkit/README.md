# Toolkit – Werkzeuge für alle Sessions (Cloud + Mac)

Alles hier ist für **jede** Claude-Session gedacht, egal ob Handy/Web (Cloud) oder Mac (lokal).
Vor der Nutzung eines Tools: **dessen `BRIEFING.md` lesen** und **`FEHLER.md` prüfen** (bekannte Probleme).

| Tool | Zweck | Aufruf | Briefing |
|---|---|---|---|
| `jobsuche-bremen/` | Jobs ≤30 Min ab Mahndorf ohne Samstagsarbeit + Weserpark (Stellen & initiativ) → Excel + CSV mit Pro/Contra/Score/Fahrt/Sprit | `python3 toolkit/jobsuche-bremen/jobsuche.py` | [BRIEFING](jobsuche-bremen/BRIEFING.md) |

## Regeln für neue Tools
1. Eigener Ordner `toolkit/<name>/` mit Skript + `BRIEFING.md` (Vorlage: das Jobsuche-Briefing).
2. Eintrag in die Tabelle oben.
3. Kein Chrome/Browser voraussetzen, wenn es auch in der Cloud laufen soll.
4. Keine Geheimnisse im Code – Keys über `.env` / Environment-Variablen.
5. Probleme → `toolkit/FEHLER.md` (Claude **und** Nutzer tragen dort ein).
6. Optional: Skill unter `.claude/skills/<name>/SKILL.md`, damit Sessions das Tool automatisch finden.
