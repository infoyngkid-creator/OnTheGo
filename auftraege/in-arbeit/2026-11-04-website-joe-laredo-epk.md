---
titel: Website Joe Laredo (EPK / Film-Portfolio)
erstellt: 2026-11-04
von: cloud
status: in-arbeit
ort: egal   # egal | lokal | cloud
---

## Auftrag
EPK-/Portfolio-Website für Joe Laredo: Kurzfilme präsentieren, Kontakt zu Künstlern/Kunden aufbauen.
Look: Tarantino-/Grindhouse-inspiriert (Trunk-Shot-Intro, Chapter-Cards, Film-Grain, 70s-Typo).
Hosting: GitHub Pages, Domain später.

## Plan (Entwurf)
- **Tech**: statisches HTML/CSS/JS + GSAP/ScrollTrigger, kein Build-Step (auch vom Handy editierbar).
- **Videos**: volle Filme über Vimeo/YouTube einbetten; im Repo nur kurze, komprimierte Loops (< 10 MB).
- **Sektionen**: Intro (Trunk-Shot) → Chapter 1 „The Work“ (Filme) → Chapter 2 „The Man“ (Bio) →
  Chapter 3 „What I Do“ (Musikvideos, Kurzfilme, Content) → Chapter 4 „Press Kit“ (Download) → Kontakt/Booking.
- **Phasen**: 1 Konzept+Assets · 2 Prototyp (Intro + 1 Film) live · 3 alle Filme + EPK · 4 Domain.

## Entscheidungen (2026-11-04)
- Joe Laredo = Künstlername des Nutzers → persönliches Filmemacher-Portfolio
- Zielgruppe: Musiker & Künstler, Produktionsfirmen & Agenturen
- Sprache: Englisch (Impressum/Kontakt-Pflichtangaben DE)
- Trunk-Shot: erstmal animiert, echter Dreh evtl. später
- Filme: 1–3, liegen auf YouTube
- Material: Foto vorhanden; Logo entwerfen wir (70s-Schriftzug)
- Code: eigenes öffentliches Repo (z. B. joe-laredo-site), Nutzer legt es an

## Noch benötigt
- [x] Repo: https://github.com/infoyngkid-creator/joe-laredo-movies
- [ ] YouTube-Links + je Titel, Jahr, Länge, Rolle, 1 Satz; welcher ist das Aushängeschild
- [ ] Foto (Drive-Link oder ins Repo)
- [ ] Kontakt-E-Mail + Socials
- [ ] Kurz-Bio (ein paar Stichpunkte reichen)

## Fortschritt
- 2026-11-04 Plan erstellt, Fragen beantwortet.
- 2026-11-04 Prototyp gepusht (Repo joe-laredo-movies, main): Trunk-Shot-Intro (animiert), 4 Kapitel, Film-Player mit Countdown, Freeze-Frame-About, Services, Kontakt/Credits, Impressum-Platzhalter. Inhalte in content.js.
- 2026-11-04 Smoke Break (YouTube CdCyzSpCz6s) als Hauptfilm, YouTube-Kanal @Joelaredo_m, Impressum-Adresse eingetragen. Thumbnail über Proxy nicht ladbar → Still vom Nutzer nötig.
- 2026-11-04 GitHub Pages aktiv: https://infoyngkid-creator.github.io/joe-laredo-movies/ (geprüft, läuft)
- 2026-11-04 3 Fotos eingebaut (About-Portrait, Smoke-Break-Poster, Kontakt-Hintergrund), Bio (EN), E-Mail joe.laredo@outlook.com, Alter automatisch ab Geburtstag 19.05.2005.
- 2026-11-04 Film-Poster öffnet sich beim Scrollen wie ein Kofferraum (scroll-gesteuert). Instagram + TikTok @joelaredo_ verlinkt.
- 2026-11-04 Wunsch: echte Kofferraum-Szene aus Smoke Break (POV aus dem Kofferraum, Joe öffnet + raucht) als scroll-gesteuertes Intro (Frames per Scroll, dann Titel). YouTube-Download aus Cloud blockiert → Nutzer liefert Clip (Original-Export) per Drive oder lokal ins Repo assets/.
- NÄCHSTER SCHRITT: Clip holen → ffmpeg Frames → Canvas-Scrub-Intro. Außerdem Film-Details Smoke Break (Jahr, Länge, Rolle, Logline), weitere Filme, Domain.

## Ergebnis
