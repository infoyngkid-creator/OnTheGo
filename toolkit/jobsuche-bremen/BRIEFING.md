# Briefing: Jobsuche Bremen (für alle zukünftigen Sessions)

## Was das Tool macht
Sucht Stellen rund um Bremen (Standard 30 km), lädt den vollen Anzeigentext, sortiert Jobs **mit Samstagsarbeit** aus,
bewertet jede Stelle mit **Pro / Contra / Score (0–100)** und schreibt **Excel (.xlsx) + CSV**.
Läuft **ohne Chrome/Browser** – nur HTTP-Anfragen. Funktioniert in der Cloud, auch wenn der Mac zu ist.

## Kontext zum Nutzer
- Sucht eine Stelle im **Vertrieb mit Festgehalt + Provision**, Raum Bremen und umzu
  (Delmenhorst, Oldenburg, Achim, Verden, Osterholz, Stuhr, Weyhe, Lilienthal, Bremerhaven).
- **Samstags arbeiten kommt nicht in Frage.** Einzelhandel/Großhandel ist auch ok (seit 2026-11-18), aber nur Jobs von Montag bis Freitag.
- Lieber mehr Optionen als zu wenige.
- **Weserpark** (Einkaufszentrum Bremen-Osterholz) ausdrücklich gewünscht (seit 2026-11-18): Dort ist Samstag üblich, der Nutzer will aber bei der Bewerbung **5 Tage/Woche, 30 Std. ohne Samstag** verhandeln → Weserpark-Jobs werden nie aussortiert, sondern landen im eigenen Blatt „Weserpark“.
- **Wohnort Bremen-Mahndorf, Auto.** Max. **20–30 Min Fahrt** (Sprit!). Ausdrücklich ok: Achim/Uphusen, Oyten, Syke, Weyhe, Stuhr, Verden. **Oldenburg nicht.** → Tabelle `ORTE` (km/Min ab Mahndorf), `PLZ`, `MAX_MINUTEN`.
- **Weserpark: überall initiativ bewerben möglich**, auch ohne Ausschreibung → Blatt „Weserpark (initiativ)“ aus dem Shopverzeichnis.
- Teilzeit (~30 Std.) ist okay → „Teilzeit möglich“ ist ein Pro; Minijob/Aushilfe bleibt Contra.
- Zugehöriger Auftrag: `auftraege/in-arbeit/2026-10-23-bewerbung-vertrieb-bremen.md`, Bewerbungsordner: `projekte/bewerbung/`.

## Aufruf (vom Repo-Root)
```bash
pip install requests openpyxl                     # falls nötig
python3 toolkit/jobsuche-bremen/jobsuche.py       # Standard, ~45 s, ~280 Stellen
python3 toolkit/jobsuche-bremen/jobsuche.py --schnell                  # ohne Volltext (Samstags-Check ungenauer)
python3 toolkit/jobsuche-bremen/jobsuche.py -b "Vertrieb" "Kundenservice" --radius 40 --seiten 3
python3 toolkit/jobsuche-bremen/jobsuche.py --mit-samstag              # nichts aussortieren
python3 toolkit/jobsuche-bremen/jobsuche.py --max-minuten 25            # Fahrzeit-Grenze ab Mahndorf
python3 toolkit/jobsuche-bremen/jobsuche.py --out /pfad/zum/ordner     # anderer Ausgabeordner
```
Standard-Suchbegriffe: Vertrieb, Vertriebsmitarbeiter, Außendienst, Vertriebsinnendienst, Sales, Kundenberater,
Key Account, Quereinsteiger Vertrieb, Account Manager, Verkaufsberater, Kundenservice, Business Development
sowie Einzel-/Großhandel: Einzelhandel, Verkäufer, Kaufmann im Einzelhandel, Verkaufsmitarbeiter, Großhandel,
Kaufmann Groß- und Außenhandel, Fachberater, Kassierer, Filialleitung, Verkauf Innendienst
(in `STANDARD_BEGRIFFE` bzw. `HANDEL` im Skript änderbar). Spalte **Bereich** = Vertrieb / Handel / Kundenservice.

## Ausgabe
`projekte/jobsuche-bremen/ergebnisse/jobs_bremen_<JJJJ-MM-TT>.xlsx` und `.csv`
- Excel-Blätter: **Jobs ohne Samstag** (≤30 Min, nach Score), **Weserpark (Stellen)**, **Weserpark (initiativ)**, **Zu weit (>30 Min)**, **Aussortiert (Samstag)** (mit Textstelle als Begründung), **Info**.
- CSV: Semikolon, UTF-8 mit BOM → öffnet direkt korrekt in deutschem Excel/Numbers.
- Spalten: Score, Bereich, Stelle, Firma, Ort, Fahrt ab Mahndorf (km · Min · €/Monat Sprit), Min., Gehalt, Samstagsarbeit?, Pro, Contra, Homeoffice, Anstellung, Online seit, Läuft bis, Quelle, Suchbegriff, Link, Mein Status.
- Nach dem Lauf: Dateien dem Nutzer schicken (SendUserFile) und `scripts/sync.sh` bzw. committen + pushen.

## Wie es funktioniert (für Änderungen)
| Teil | Funktion im Skript | Hinweis |
|---|---|---|
| StepStone-Suche | `stepstone()` | liest JSON aus `window.__PRELOADED_STATE__["app-unifiedResultlist"]` der Suchseite `stepstone.de/jobs/<begriff>/in-bremen?radius=&page=` + zusätzlich `in-verden-aller` (r=10). Achtung: `in-achim` liefert Raum Hannover – nicht verwenden! |
| StepStone-Volltext | `stepstone_detail()` | JSON-LD `JobPosting` der Detailseite (description, employmentType, validThrough) |
| Weserpark | `weserpark()`, `WESERPARK` | Jobbörse `weserpark.de/aktuelles/jobs` (Karten getrennt durch `Partials/List/Item.html`) + StepStone-Suche „weser-park“; alles mit Weserpark-Bezug → Blatt „Weserpark“, kein Samstags-Abzug |
| Fahrt ab Mahndorf | `fahrt()`, `ORTE`, `PLZ`, `REGIONAL` | PLZ (aus JSON-LD der Detailseite) → Stadtteil/Ort; sonst Ortsname; Bremer Stadtteil schlägt „Bremen“. Spritkosten: `SPRIT_L_100KM`, `SPRIT_EUR_L`, `ARBEITSTAGE`. Unbekannte Orte → „Zu weit“ (bei Bedarf in `ORTE` ergänzen) |
| Weserpark initiativ | `weserpark_initiativ()`, `PASSUNG`, `NICHT_INITIATIV` | Shopverzeichnis `weserpark.de/shopping/shops-von-a-z` (`shopgrid-item`, Name + Kategorie); Passung: Mobilfunk/Elektronik 80, swb 75, Reise 70 … Gastro 25; Ärzte/Polizei/Friseur usw. raus |
| Arbeitnow | `arbeitnow()` | offene API, filtert auf Orte aus `REGION`; liefert nur wenige Treffer |
| Samstags-Check | `samstag()` + Regex `FREI`, `SAMSTAG_JA`, `MO_FR` | Reihenfolge: „Wochenende frei“ → nein; „Samstag/am Wochenende/Schicht…“ → ja (aussortiert); „Mo–Fr“ → nein; sonst „nicht erwähnt“ |
| Samstag „prüfen“ | `HANDEL_HINWEIS`, `LADENKETTEN` | Laden/Filiale/Store/Callcenter oder bekannte Ladenkette (BAUHAUS, ALDI, Action …) ohne klare Zeitangabe → gelb markiert, −15 Score, bleibt in der Liste |
| Relevanzfilter | `RELEVANT` | Titel muss nach Vertrieb/Verkauf/Handel/Kunde/Beratung … klingen, sonst raus (StepStone liefert bei Handelsbegriffen viel Fachfremdes) |
| Pro/Contra | Listen `PRO`, `CONTRA`, `SENIOR` | einfache Regex auf Titel+Text – neue Kriterien einfach als Zeile ergänzen |
| Score | `bewerten()` | 40 Basis, +4 je Pro, −8 je Contra, +10 Fix+Provision, +8 Mo–Fr bestätigt, −15 Samstag prüfen, −20 reine Provision |
| Export | `export()` | openpyxl; Spalten in `SPALTEN` |
| Fehler-Logging | `fehler_melden()` / `fehler_schreiben()` | trägt Probleme automatisch in `toolkit/FEHLER.md` ein |

## Bekannte Grenzen (Stand 2026-11-14)
- **Arbeitsagentur-API** (`rest.arbeitsagentur.de`) und **Indeed** antworten aus der Cloud mit **403** → nicht eingebunden.
  User-Agent-Fälschung (App vortäuschen) wurde bewusst **nicht** gemacht und von der Rechteprüfung blockiert – nicht erneut versuchen.
- Quellen fast nur StepStone. Weser-Kurier-Jobs (`jobs.weser-kurier.de`) wäre per HTML erreichbar (Kandidat für Erweiterung).
- „nicht erwähnt“ beim Samstag heißt nicht sicher Mo–Fr → vor Bewerbung gegenprüfen.
- Gehalt „geschätzt“ = StepStone-Schätzung, keine Arbeitgeberangabe.
- Dubletten möglich, wenn eine Firma dieselbe Stelle mit anderem Titel ausschreibt.

## Bei Problemen
1. `toolkit/FEHLER.md` lesen – evtl. schon bekannt, ggf. mit Lösung.
2. Neues Problem dort eintragen (Datum, Tool, Beschreibung, Status, Lösung/Workaround).
3. Wenn behoben: Status auf `behoben` setzen und Lösung eintragen.
