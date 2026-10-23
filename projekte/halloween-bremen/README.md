# Halloween Bremen 2026 – Event-Vergleich

Statische Single-File-Website zum Vergleichen von Halloween-Events in Bremen
und Umgebung. Kein Build, keine Abhängigkeiten.

## Öffnen
`index.html` im Browser öffnen (Doppelklick) oder über GitHub Pages ausliefern.

## Funktionen
- Volltextsuche + Filter: Ort, Tag (Fr 30.10. / Sa 31.10.), Kategorie, Sortierung
- Event-Karten mit Zeit, Preis, Alter, Dresscode, Ansprechpartner
- Direktlink pro Event zu Veranstalter/Tickets
- Abschnitt „Ansprechpersonen & Veranstalter"

## Events ergänzen / ändern
Alle Daten stehen im `EVENTS`-Array oben im `<script>` von `index.html`.
Neues Event = neues Objekt mit:

```js
{
  name: "…", cat: "party|familie|kultur|sport|dinner", ort: "Bremen|Bremerhaven|Umzu",
  venue: "Location, Adresse", day: 30|31, time: "…",
  priceFrom: Zahl|null,   // für Sortierung/Filter; 0 = frei, null = unbekannt
  price: "Anzeigetext", age: "…", dress: "…",
  desc: "…", contact: "Veranstalter", url: "https://…"
}
```

## Hinweis
Angaben ohne Gewähr, recherchiert am 23.10.2026 aus öffentlichen Quellen.
Unbekanntes ist mit „k. A." markiert, nichts erfunden. Vor dem Besuch beim
Veranstalter prüfen.
