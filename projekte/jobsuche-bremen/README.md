# Jobsuche Bremen – ohne Samstag

Python-Tool **ohne Browser/Chrome**. Läuft in der Cloud-Session (Handy) und auf dem Mac.

```bash
python3 projekte/jobsuche-bremen/jobsuche.py            # Standard (~45 s, ~280 Stellen)
python3 projekte/jobsuche-bremen/jobsuche.py --schnell  # schneller, ohne Volltext
python3 projekte/jobsuche-bremen/jobsuche.py -b "Vertrieb" "Kundenservice" --radius 40 --seiten 3
python3 projekte/jobsuche-bremen/jobsuche.py --mit-samstag   # nichts aussortieren
```
Benötigt: `pip install requests openpyxl`

**Ausgabe** in `ergebnisse/`: `jobs_bremen_<datum>.xlsx` (Blätter: *Jobs ohne Samstag*, *Aussortiert (Samstag)*, *Info*) und `.csv` (Semikolon, UTF-8 → öffnet direkt in Excel/Numbers).
Spalten: Score, Stelle, Firma, Ort, Gehalt, Samstagsarbeit?, Pro, Contra, Homeoffice, Anstellung, Datum, Link, Mein Status.

**Quellen:** StepStone (Suchliste + Volltext der Anzeige), Arbeitnow-API.
Arbeitsagentur-API und Indeed blocken Anfragen aus der Cloud (403).

**Samstags-Check:** Volltext wird nach „Samstag“, „Mo–Sa“, „am Wochenende“, Schichtdienst usw. durchsucht → aussortiert.
„Wochenende frei“/„Mo–Fr“ → bestätigt. „nicht erwähnt“ = meist Büro/Außendienst Mo–Fr, aber vor der Bewerbung gegenprüfen.
Pro/Contra/Score sind regelbasiert aus dem Anzeigentext; Gehalt „geschätzt“ = StepStone-Schätzung.
