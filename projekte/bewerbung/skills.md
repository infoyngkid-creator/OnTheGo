# Claude-Skills für Bewerbungen – geprüft 2026-10-23 (noch NICHT installiert)

Alle drei Repos geklont und gelesen: reine Anleitungen (SKILL.md), keine Netzwerkzugriffe, keine verdächtigen Skripte.

| Skill | Repo | Was es kann | Passt? |
|---|---|---|---|
| **job-seeker-helper** (+ resume-optimizer, cover-letter, interview-coach, job-application-tracker) | [Faizee-Asad/job-seeker-claude-skills](https://github.com/Faizee-Asad/job-seeker-claude-skills) | Komplettpaket: angepasster Lebenslauf, Anschreiben, ATS-Keyword-Check, Interview-Vorbereitung, Follow-up-Mail, CSV-Tracker. Kleine Python-Helfer (lokal, offline). | ⭐ Beste Basis – englisch, muss auf deutsche Konventionen angepasst werden |
| **resume-tailoring** | [amanattar/resume-tailoring-skill](https://github.com/amanattar/resume-tailoring-skill) (MIT, ~124 ⭐) | Lebenslauf je Stelle zuschneiden, Firma recherchieren, Fit-Score, fragt nicht dokumentierte Erfahrungen ab – „erfindet nichts“ | Gut als Ergänzung, sehr ausführlich (1.300 Zeilen) |
| **cv** (claude-resume) | [deusyu/claude-resume](https://github.com/deusyu/claude-resume) | LaTeX-Lebenslauf aus strukturierten Daten (`/cv init`, `/cv generate`) | Optional, nur Lebenslauf, LaTeX nötig |

Bereits vorhanden in dieser Umgebung: `anthropic-skills:docx` (Word), `anthropic-skills:pdf` (PDF), `anthropic-skills:docs` (teilbare Dokumente).

**Vorschlag:** job-seeker-helper nach `.claude/skills/` in dieses Repo übernehmen (dann lokal UND Cloud verfügbar) und um eine deutsche Variante ergänzen
(tabellarischer Lebenslauf, Anschreiben nach DIN 5008, Gehaltsvorstellung, Eintrittstermin, Foto optional).
