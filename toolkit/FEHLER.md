# Fehlerliste – Toolkit

Gemeinsame Liste für **alle Claude-Sessions und den Nutzer**.
Bearbeiten geht auch direkt auf GitHub (Datei öffnen → Stift-Symbol) oder auf dem Mac in jedem Texteditor.

**Status:** `offen` · `in Arbeit` · `behoben` · `bekannt/hinnehmen`
Neue Einträge **oben** in die Tabelle. Das Jobsuche-Tool trägt Probleme automatisch ein (Zeilen „automatisch gemeldet“).

## Schnell selbst beheben (für den Nutzer)
| Problem | Lösung |
|---|---|
| `ModuleNotFoundError: requests` / `openpyxl` | `pip3 install requests openpyxl` |
| CSV zeigt kaputte Umlaute | Datei per Doppelklick in Excel öffnen (ist UTF-8 mit BOM); in Numbers: Ablage → Öffnen |
| Zu wenige Treffer | `--radius 50 --seiten 4` oder weitere Begriffe mit `-b "..."` |
| Ein Job mit Samstag ist trotzdem drin / ein guter wurde aussortiert | Wort/Phrase in `SAMSTAG_JA` bzw. `FREI` in `toolkit/jobsuche-bremen/jobsuche.py` ergänzen (ganz einfache Regex) und hier eintragen |
| Pro/Contra fehlt etwas | Zeile in `PRO` oder `CONTRA` im Skript ergänzen, Muster: `(r"suchwort|anderes wort", "Anzeigetext"),` |
| „StepStone: Datenblock … nicht gefunden“ | StepStone hat die Seite umgebaut → Claude-Session bitten, `stepstone()` anzupassen |
| `permission denied` beim Start | `python3 toolkit/jobsuche-bremen/jobsuche.py` statt `./jobsuche.py` verwenden |

## Einträge
| Datum | Tool | Problem | Status | Lösung / Workaround |
|---|---|---|---|---|
<!-- AUTO-EINTRAEGE -->
| 2026-11-18 | jobsuche-bremen | HUMANIC-Job im Weserpark steht doppelt (Firma direkt + über meinestadt.de) | bekannt/hinnehmen | – |
| 2026-11-18 | jobsuche-bremen | „selbständig arbeiten“ wurde als „Selbstständig/Provision ohne Fix“ gewertet (18 Fälle bleiben, prüfen) | behoben | Regex auf „auf selbstständiger Basis“, „Handelsvertreter“ usw. eingeschränkt |
| 2026-11-18 | jobsuche-bremen | Teilzeit wurde als Contra gewertet, Nutzer will aber ~30 Std. | behoben | Teilzeit = Pro, nur Minijob/Aushilfe = Contra |
| 2026-11-18 | jobsuche-bremen | Spalte „Bereich“ nach erstem Suchbegriff – z. B. Ströer-Außendienst steht unter „Handel“ | offen | Beim Filtern nicht nur auf „Bereich“ verlassen |
| 2026-11-18 | jobsuche-bremen | „Filiale“ markiert auch Bank-Filialen (Sparkasse) als „prüfen“, obwohl meist Mo–Fr | bekannt/hinnehmen | Anzeige ansehen |
| 2026-11-18 | jobsuche-bremen | Ladenketten (BAUHAUS, Vorwerk Store) rutschten durch, weil „Mo–Fr“ (Berufsschule) im Text stand | behoben | `LADENKETTEN` → immer „prüfen“ |
| 2026-11-18 | jobsuche-bremen | Handels-Suchbegriffe liefern viele fachfremde Jobs (Zimmerer, SAP-Berater) | behoben | Relevanzfilter `RELEVANT` auf Titel |
| 2026-11-18 | jobsuche-bremen | „laden“ (z. B. „wir laden dich ein“), „Krankenkasse“ und „Workshop“ wurden als Laden/Kasse/Shop erkannt | behoben | Regex mit Wortgrenzen/„im Laden“ |
| 2026-11-14 | jobsuche-bremen | Dubletten, wenn eine Firma dieselbe Stelle unter leicht anderem Titel ausschreibt (z. B. DeterTech) | offen | In Excel nach Firma sortieren; Fix: Dubletten-Schlüssel unschärfer machen |
| 2026-11-14 | jobsuche-bremen | Samstag „nicht erwähnt“ bei ~270 von 280 Stellen – nicht sicher Mo–Fr | bekannt/hinnehmen | Vor Bewerbung Anzeige prüfen |
| 2026-11-14 | jobsuche-bremen | Arbeitnow liefert kaum Bremen-Treffer (1 Stelle) | bekannt/hinnehmen | Weitere Quelle ergänzen (z. B. jobs.weser-kurier.de) |
| 2026-11-14 | jobsuche-bremen | Indeed antwortet aus der Cloud mit 403 | bekannt/hinnehmen | Nicht nutzbar ohne Browser |
| 2026-11-14 | jobsuche-bremen | Arbeitsagentur-Jobsuche-API antwortet aus der Cloud mit 403 (blockiert per User-Agent) | bekannt/hinnehmen | Kein UA-Spoofing; ggf. lokal auf dem Mac testen |
| 2026-11-14 | jobsuche-bremen | „unbefristet“ wurde als „Befristet“ erkannt | behoben | Regex `(?<!un)befristet` |
| 2026-11-14 | jobsuche-bremen | „an Samstagen frei“ führte zum Aussortieren | behoben | `FREI`-Regex erweitert |
