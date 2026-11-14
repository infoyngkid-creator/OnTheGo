---
name: jobsuche-bremen
description: Jobs rund um Bremen ohne Samstagsarbeit suchen und als Excel + CSV mit Pro/Contra/Score ausgeben – ohne Chrome/Browser, läuft auch in der Cloud. Verwenden bei "Jobsuche", "Jobs Bremen", "neue Stellen", "Jobliste aktualisieren", "Vertriebsjobs suchen".
---
1. `toolkit/jobsuche-bremen/BRIEFING.md` lesen (Kontext, Optionen, Grenzen).
2. `toolkit/FEHLER.md` auf offene Probleme prüfen.
3. Vom Repo-Root: `python3 toolkit/jobsuche-bremen/jobsuche.py` (Optionen siehe Briefing; ggf. vorher `pip install requests openpyxl`).
4. Excel + CSV aus `projekte/jobsuche-bremen/ergebnisse/` dem Nutzer schicken, Top-Treffer kurz nennen.
5. Neue Probleme in `toolkit/FEHLER.md` eintragen, dann `scripts/sync.sh` (bzw. committen + pushen).
