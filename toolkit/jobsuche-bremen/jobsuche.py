#!/usr/bin/env python3
"""
Jobsuche Bremen & umzu – ohne Browser/Chrome, läuft lokal und in der Cloud.

Quellen:  StepStone (Suchergebnis + Detailseiten, strukturierte JSON-Daten)
          Arbeitnow (offene JSON-API)
Filter:   Region Bremen (+ Umkreis), Samstagsarbeit wird erkannt und aussortiert
Ausgabe:  projekte/jobsuche-bremen/ergebnisse/jobs_bremen_<datum>.xlsx und .csv
Briefing: toolkit/jobsuche-bremen/BRIEFING.md   Fehler: toolkit/FEHLER.md

Aufruf:
  python3 toolkit/jobsuche-bremen/jobsuche.py                      # Standard-Suchbegriffe (Vertrieb & Co.)
  python3 toolkit/jobsuche-bremen/jobsuche.py -b "Vertrieb" "Kundenberater" --seiten 3 --radius 40
  python3 toolkit/jobsuche-bremen/jobsuche.py --schnell            # nur 1 Seite je Begriff, keine Detailseiten
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

UA = "OnTheGo-Jobsuche/1.0 (privates Bewerbungstool)"
HDR = {"User-Agent": UA, "Accept-Language": "de-DE,de;q=0.9"}
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "projekte" / "jobsuche-bremen" / "ergebnisse"
FEHLER = REPO / "toolkit" / "FEHLER.md"
PROBLEME: list[str] = []


def fehler_melden(text: str) -> None:
    """Problem merken; am Ende landet es automatisch in toolkit/FEHLER.md."""
    PROBLEME.append(text)
    print(f"⚠️  {text}", flush=True)


def fehler_schreiben() -> None:
    if not PROBLEME or not FEHLER.exists():
        return
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    zeilen = "".join(f"| {stamp} | jobsuche-bremen | {p} | offen | automatisch gemeldet |\n" for p in PROBLEME)
    s = FEHLER.read_text(encoding="utf-8")
    marker = "<!-- AUTO-EINTRAEGE -->\n"
    FEHLER.write_text(s.replace(marker, marker + zeilen, 1) if marker in s else s + zeilen, encoding="utf-8")
    print(f"📝 {len(PROBLEME)} Problem(e) in {FEHLER} eingetragen.")

STANDARD_BEGRIFFE = [
    "Vertrieb", "Vertriebsmitarbeiter", "Außendienst", "Vertriebsinnendienst",
    "Sales", "Kundenberater", "Key Account", "Quereinsteiger Vertrieb",
    "Account Manager", "Verkaufsberater", "Kundenservice", "Business Development",
    # Einzel-/Großhandel (Großhandel & Fachhandel B2B sind oft Mo–Fr)
    "Einzelhandel", "Verkäufer", "Kaufmann im Einzelhandel", "Verkaufsmitarbeiter",
    "Großhandel", "Kaufmann Groß- und Außenhandel", "Fachberater", "Kassierer",
    "Filialleitung", "Verkauf Innendienst",
]
HANDEL = {"Einzelhandel", "Verkäufer", "Kaufmann im Einzelhandel", "Verkaufsmitarbeiter",
          "Großhandel", "Kaufmann Groß- und Außenhandel", "Fachberater", "Kassierer",
          "Filialleitung", "Verkauf Innendienst"}

REGION = [
    "bremen", "bremerhaven", "delmenhorst", "oldenburg", "achim", "verden",
    "osterholz", "stuhr", "weyhe", "lilienthal", "ganderkesee", "syke",
    "ritterhude", "schwanewede", "oyten", "brinkum", "rotenburg", "diepholz",
    "wildeshausen", "hude", "worpswede", "grasberg", "tarmstedt", "harpstedt",
    "bassum", "thedinghausen", "langwedel", "ottersberg", "zeven", "cuxhaven",
    "norddeutschland", "niedersachsen", "nordwest", "region nord",
]

# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
S = requests.Session()
S.headers.update(HDR)


def get(url: str, **kw) -> requests.Response | None:
    for versuch in range(3):
        try:
            r = S.get(url, timeout=25, **kw)
            if r.status_code == 200:
                return r
            if r.status_code in (403, 404):
                return None
        except requests.RequestException:
            pass
        time.sleep(1.5 * (versuch + 1))
    return None


def clean(t: str | None) -> str:
    t = html.unescape(t or "")
    t = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"[ \t\xa0]+", " ", t).strip()


# --------------------------------------------------------------------------- #
# Fahrt ab Mahndorf (Wohnort): Straßen-km und Minuten mit dem Auto, grob geschätzt
# (A1/A27/Hansalinie berücksichtigt). Keine externe Abfrage – Tabelle hier pflegen.
# --------------------------------------------------------------------------- #
MAX_MINUTEN = 30            # alles darüber → Blatt „Zu weit“
SPRIT_L_100KM = 6.5         # Verbrauch
SPRIT_EUR_L = 1.75          # Preis pro Liter
ARBEITSTAGE = 21            # pro Monat (5-Tage-Woche)

# Ort/Stadtteil → (km, Minuten) ab Bremen-Mahndorf
ORTE = {
    "mahndorf": (0, 0), "hansalinie": (3, 6), "uphusen": (3, 5), "arbergen": (4, 8), "weserpark": (4, 7),
    "weser-park": (4, 7), "osterholz": (5, 9), "tenever": (6, 10), "hemelingen": (6, 11), "sebaldsbrück": (6, 10),
    "bierden": (6, 9), "vahr": (9, 14), "achim": (8, 12), "oyten": (9, 12), "embsen": (9, 12),
    "baden": (13, 16), "uesen": (12, 15), "oberneuland": (10, 15), "horn": (11, 17), "borgfeld": (14, 20),
    "habenhausen": (9, 14), "obervieland": (11, 15), "arsten": (11, 15), "kattenturm": (12, 16), "flughafen": (13, 17),
    "airport": (13, 17), "neustadt": (14, 21), "östliche vorstadt": (11, 18), "schwachhausen": (12, 19),
    "bremen": (13, 20), "mitte": (13, 20), "überseestadt": (17, 25), "findorff": (14, 22), "walle": (17, 25),
    "woltmershausen": (17, 24), "gröpelingen": (20, 27), "huchting": (19, 25), "lilienthal": (16, 22),
    "fischerhude": (16, 20), "ottersberg": (19, 20), "posthausen": (18, 18), "sottrum": (27, 24),
    "langwedel": (21, 22), "etelsen": (17, 19), "thedinghausen": (21, 25), "verden": (28, 25), "kirchlinteln": (33, 30),
    "weyhe": (16, 18), "leeste": (16, 19), "kirchweyhe": (17, 20), "dreye": (13, 17), "brinkum": (15, 18),
    "stuhr": (19, 22), "moordeich": (19, 22), "syke": (26, 27), "barrien": (24, 26), "grasberg": (22, 28),
    "worpswede": (26, 33), "ritterhude": (28, 31), "burglesum": (29, 30), "burg-grambke": (25, 28), "vegesack": (33, 33),
    "blumenthal": (38, 38), "farge": (41, 42), "delmenhorst": (30, 30), "ganderkesee": (40, 37),
    "osterholz-scharmbeck": (33, 34), "bassum": (38, 38), "hoya": (40, 40), "dörverden": (37, 35), "rotenburg": (40, 35),
    "zeven": (50, 45), "schwanewede": (40, 40), "wildeshausen": (47, 40), "oldenburg": (58, 45), "hude": (48, 42),
    "bremerhaven": (72, 55), "cuxhaven": (115, 85), "hamburg": (110, 80), "hannover": (120, 85), "diepholz": (62, 50),
    "nienburg": (60, 55),
}
ORTE["sieke"] = ORTE["syke"]          # häufige Schreibweise
ORTE["euthen"] = ORTE["oyten"]
BREMER_TEILE = {k for k in ORTE if k not in {"bremen", "mitte"}} & {
    "mahndorf", "hansalinie", "arbergen", "weserpark", "weser-park", "osterholz", "tenever", "hemelingen", "sebaldsbrück",
    "vahr", "oberneuland", "horn", "borgfeld", "habenhausen", "obervieland", "arsten", "kattenturm", "flughafen", "airport",
    "neustadt", "östliche vorstadt", "schwachhausen", "überseestadt", "findorff", "walle", "woltmershausen", "gröpelingen",
    "huchting", "burglesum", "burg-grambke", "vegesack", "blumenthal", "farge"}
# PLZ-Präfix → Ort (genauer als „Bremen“)
PLZ = {
    "28307": "mahndorf", "28309": "hemelingen", "28325": "osterholz", "28327": "osterholz", "28329": "vahr",
    "28832": "achim", "28876": "oyten", "28870": "ottersberg", "28844": "weyhe", "28816": "stuhr", "28857": "syke",
    "27283": "verden", "28865": "lilienthal", "28879": "grasberg", "27726": "worpswede", "27721": "ritterhude",
    "27711": "osterholz-scharmbeck", "28355": "oberneuland", "28357": "horn", "28359": "horn", "28277": "obervieland",
    "28279": "obervieland", "28199": "neustadt", "28197": "neustadt", "28201": "neustadt", "28203": "östliche vorstadt",
    "28205": "östliche vorstadt", "28209": "schwachhausen", "28211": "schwachhausen", "28213": "schwachhausen",
    "28215": "findorff", "28217": "überseestadt", "28219": "walle", "28237": "gröpelingen", "28239": "gröpelingen",
    "28259": "huchting", "28195": "mitte", "28717": "burglesum", "28719": "burg-grambke", "28755": "vegesack",
    "28757": "vegesack", "28759": "vegesack", "28777": "blumenthal", "28779": "blumenthal", "27749": "delmenhorst",
    "27751": "delmenhorst", "27753": "delmenhorst", "27755": "delmenhorst", "27777": "ganderkesee", "26121": "oldenburg",
    "26122": "oldenburg", "26123": "oldenburg", "26125": "oldenburg", "26127": "oldenburg", "26129": "oldenburg",
    "26131": "oldenburg", "26133": "oldenburg", "26135": "oldenburg", "28199": "neustadt", "28197": "neustadt",
    "27299": "langwedel", "27308": "kirchlinteln", "27330": "thedinghausen", "27367": "sottrum", "27356": "rotenburg",
    "28211": "schwachhausen", "28239": "gröpelingen",
}
REGIONAL = re.compile(r"norddeutschland|niedersachsen|nordwest|region|gebiet|bundesweit|deutschlandweit|"
                      r"home-?office|remote|schleswig|plz", re.I)


def fahrt(ort: str, plz: str = "", text: str = "") -> tuple[int | None, str]:
    """→ (Minuten oder None, Beschreibung) für den nächstgelegenen genannten Arbeitsort."""
    o = ort.lower()
    kandidaten = set()
    for code in re.findall(r"\b(\d{5})\b", f"{plz} {ort}"):
        if code in PLZ:
            kandidaten.add(PLZ[code])
    for name in sorted(ORTE, key=len, reverse=True):
        if re.search(r"(?<![a-zäöüß])" + re.escape(name) + r"(?![a-zäöüß])", o):
            kandidaten.add(name)
    if not kandidaten and WESERPARK_RX.search(text):
        kandidaten.add("weserpark")
    if kandidaten & BREMER_TEILE:
        kandidaten -= {"bremen", "mitte"}
    if not kandidaten:
        if REGIONAL.search(o):
            return None, "Außendienst/Region/Homeoffice – Fahrt variiert"
        return None, "unbekannt"
    best = min(kandidaten, key=lambda k: ORTE[k][1])
    km, minuten = ORTE[best]
    sprit = km * 2 * ARBEITSTAGE * SPRIT_L_100KM / 100 * SPRIT_EUR_L
    zusatz = " (+ weitere Orte)" if REGIONAL.search(o) else ""
    return minuten, f"{best.title()}: ~{km} km · ~{minuten} Min · ~{sprit:.0f} €/Monat Sprit{zusatz}"


# --------------------------------------------------------------------------- #
# Quelle 1: StepStone
# --------------------------------------------------------------------------- #
def _stepstone_state(text: str) -> dict:
    key = 'window.__PRELOADED_STATE__["app-unifiedResultlist"]'
    i = text.find(key)
    if i < 0:
        return {}
    s = text[i:]
    s = s[s.find("=") + 1:].lstrip()
    try:
        obj, _ = json.JSONDecoder().raw_decode(s)
        return obj
    except ValueError:
        return {}


def stepstone(begriff: str, radius: int, seiten: int, ort: str = "bremen") -> list[dict]:
    slug = urllib.parse.quote(begriff.lower().replace(" ", "-"))
    jobs = []
    for page in range(1, seiten + 1):
        url = f"https://www.stepstone.de/jobs/{slug}/in-{ort}?radius={radius}&page={page}"
        r = get(url)
        if not r:
            if page == 1:
                fehler_melden(f"StepStone nicht erreichbar/blockiert (Begriff '{begriff}')")
            break
        state = _stepstone_state(r.text)
        if page == 1 and not state:
            fehler_melden("StepStone: Datenblock app-unifiedResultlist nicht gefunden – Seitenstruktur geändert?")
        items = state.get("searchResults", {}).get("items", [])
        if not items:
            break
        for it in items:
            us = it.get("unifiedSalary") or {}
            gehalt = ""
            if us.get("salaryAvailable") and (us.get("min") or us.get("exactValue")):
                lo, hi = us.get("min"), us.get("max")
                art = "geschätzt" if us.get("salaryType") == "Predicted" else "laut Anzeige"
                per = {"Annually": "/Jahr", "Monthly": "/Monat", "Hourly": "/Std"}.get(us.get("period"), "")
                gehalt = (f"{lo:,.0f}–{hi:,.0f} €{per} ({art})" if lo and hi else f"{us.get('exactValue') or lo} €{per} ({art})").replace(",", ".")
            u = it.get("url", "")
            if u.startswith("/"):
                u = "https://www.stepstone.de" + u
            jobs.append({
                "quelle": "StepStone",
                "id": f"ss-{it.get('id')}",
                "titel": clean(it.get("title")),
                "firma": clean(it.get("companyName")),
                "ort": clean(it.get("location")),
                "plz": str(it.get("postCode") or ""),
                "gehalt": gehalt,
                "homeoffice": {"1": "teilweise", "2": "teilweise", "3": "ja"}.get(str(it.get("workFromHome")), ""),
                "datum": (it.get("datePosted") or "")[:10],
                "link": u.split("?")[0],
                "text": clean(it.get("textSnippet")) + " " + clean(it.get("jobBenefitsHtml")),
                "suchbegriff": begriff,
            })
        if len(items) < 20:
            break
        time.sleep(0.6)
    return jobs


def stepstone_detail(job: dict) -> None:
    r = get(job["link"])
    if not r:
        return
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', r.text, re.S):
        if "JobPosting" not in m.group(1):
            continue
        try:
            d = json.loads(m.group(1))
        except ValueError:
            continue
        job["text"] = clean(d.get("description")) or job["text"]
        et = d.get("employmentType")
        job["anstellung"] = ", ".join(et) if isinstance(et, list) else (et or "")
        job["bewerben_bis"] = (d.get("validThrough") or "")[:10]
        locs = d.get("jobLocation") or []
        locs = locs if isinstance(locs, list) else [locs]
        plz = [str((l.get("address") or {}).get("postalCode") or "") for l in locs if isinstance(l, dict)]
        orte = [str((l.get("address") or {}).get("addressLocality") or "") for l in locs if isinstance(l, dict)]
        job["plz"] = " ".join(x for x in [job.get("plz", "")] + plz if x)
        job["ort_detail"] = ", ".join(x for x in orte if x)
        return


# --------------------------------------------------------------------------- #
# Quelle 2: Arbeitnow (offene API, v. a. internationale Firmen)
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Quelle 3: Weserpark (Einkaufszentrum Bremen-Osterholz, eigene Jobbörse)
# Samstag ist dort normal → Jobs werden NICHT aussortiert, sondern eigenes Blatt
# („5 Tage / 30 Std. verhandeln“).
# --------------------------------------------------------------------------- #
WESERPARK = re.compile(r"weser ?-?park|hans-bredow-str", re.I)
WESERPARK_RX = WESERPARK


def _weserpark_detail(job: dict) -> None:
    r = get(job["link"])
    if not r:
        return
    m = re.search(r"<main.*?</main>", r.text, re.S)
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", m.group(0) if m else r.text, flags=re.S)
    job["text"] = clean(t) or job["text"]


def weserpark() -> list[dict]:
    base = "https://www.weserpark.de"
    r = get(base + "/aktuelles/jobs")
    if not r:
        fehler_melden("Weserpark-Jobseite nicht erreichbar (weserpark.de/aktuelles/jobs)")
        return []
    jobs = []
    for card in r.text.split("Partials/List/Item.html")[1:]:
        link = re.search(r'href="(/aktuelles/jobs/[^"]+)"', card)
        titel = re.search(r'itemprop="headline">(.*?)</h3>', card, re.S)
        if not (link and titel):
            continue
        firma = re.search(r'news-list-tags"[^>]*><span[^>]*>(.*?)</span>', card, re.S)
        teaser = re.search(r'itemprop="description">(.*?)</div>', card, re.S)
        jobs.append({
            "quelle": "Weserpark", "id": "wp-" + link.group(1).rsplit("-", 1)[-1],
            "titel": clean(titel.group(1)), "firma": clean(firma.group(1)) if firma else "",
            "ort": "Bremen, Weserpark", "gehalt": "", "homeoffice": "", "datum": "",
            "link": base + link.group(1), "text": clean(teaser.group(1)) if teaser else "",
            "suchbegriff": "Weserpark",
        })
    if not jobs:
        fehler_melden("Weserpark: keine Job-Karten gefunden – Seitenstruktur geändert?")
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(_weserpark_detail, jobs))
    return jobs


# Weserpark-Shops für Initiativbewerbungen (auch ohne ausgeschriebene Stelle)
PASSUNG = [  # (Kategorie-/Namensmuster, Passung 0–100, Begründung)
    (r"telekom|vodafone|o2|freenet|mobilcom|mobile point|myswooop|media ?markt", 80, "Verkauf mit Provision/Zielprämie üblich – passt zu Vertrieb"),
    (r"\bswb\b", 75, "Energie-Kundenberatung (Vertrieb, Verträge)"),
    (r"dertour|tui|urlaub & ferien|reise", 70, "Reiseverkauf/Beratung, eher Büro-Rhythmus"),
    (r"vorwerk|opti-wohnwelt|hornbach|elektronik", 65, "Beratungsverkauf mit höherem Warenwert"),
    (r"optik|fielmann|krass|eyes|apollo|juwelier|pandora|douglas|parfüm|pieper", 60, "Beratungsverkauf"),
    (r"mode|fashion|schuhe|lederwaren|schmuck|accessoires|haushalt|dekoration|bücher|schreibwaren|kindermode|"
     r"gesundheit|beauty|pflege|tabak", 55, "Einzelhandel Verkauf/Kundenberatung"),
    (r"lebensmittel|frischwaren|edeka|aldi", 40, "Lebensmittelhandel – oft Früh/Spät/Samstag"),
    (r"gastronomie|food|lounge|freizeit", 25, "Gastro/Freizeit – passt wenig, viel Wochenende"),
]
NICHT_INITIATIV = re.compile(r"polizei|sparkasse \(sb|zahnarzt|augenärzte|csl plasma|fotofix|service punkt|"
                             r"aba logistics|stichweh|fahrschule|tankstelle|hbi\b|studioline|nail|nails|barber|"
                             r"frisör|super cut|styleboxx|furkans|mish mish|ellen", re.I)


def weserpark_initiativ() -> list[dict]:
    base = "https://www.weserpark.de"
    r = get(base + "/shopping/shops-von-a-z")
    if not r:
        fehler_melden("Weserpark-Shopverzeichnis nicht erreichbar (shops-von-a-z)")
        return []
    rows = []
    for block in r.text.split('<div class="shopgrid-item">')[1:]:
        n = re.search(r'<span class="name d-none">(.*?)</span>', block, re.S)
        k = re.search(r'<span class="kats d-none([^"]*)"', block)
        if not n:
            continue
        name, kat = clean(n.group(1)), (k.group(1).strip() if k else "")
        if NICHT_INITIATIV.search(name):
            continue
        link = re.search(r'href="(/shops/[^"]+)"', block)
        fit, grund = 45, "Einzelhandel"
        for rx, f, g in PASSUNG:
            if re.search(rx, f"{name} {kat}", re.I):
                fit, grund = f, g
                break
        q = urllib.parse.quote_plus(f"{name} Karriere Jobs Bremen Weserpark")
        rows.append({
            "quelle": "Weserpark-Shops", "id": "wpi-" + re.sub(r"\W+", "", name.lower()),
            "titel": "Initiativbewerbung (Verkauf/Beratung)", "firma": name, "ort": "Bremen, Weserpark",
            "gehalt": "", "homeoffice": "", "datum": "", "anstellung": kat, "bewerben_bis": "",
            "link": base + link.group(1) if link else f"https://www.google.com/search?q={q}",
            "text": "", "suchbegriff": "Weserpark initiativ", "kategorie": "Weserpark initiativ",
            "samstag": "im Center üblich → 5 Tage/30 Std. ohne Samstag verhandeln",
            "pro": f"{grund} · Weserpark – kurzer Weg", "contra": "Keine Stelle ausgeschrieben → im Laden/Bewerbung direkt fragen",
            "score": fit, "status": "", "weserpark": True,
        })
    rows = [r for r in rows if r["score"] >= 25]
    minuten, txt = fahrt("weserpark")
    for r_ in rows:
        r_["minuten"], r_["fahrt"] = minuten, txt
    return sorted(rows, key=lambda x: -x["score"])


def arbeitnow(seiten: int = 5) -> list[dict]:
    jobs = []
    for page in range(1, seiten + 1):
        r = get(f"https://www.arbeitnow.com/api/job-board-api?page={page}")
        if not r:
            if page == 1:
                fehler_melden("Arbeitnow-API nicht erreichbar")
            break
        data = r.json().get("data", [])
        if not data:
            break
        for j in data:
            if not any(x in (j.get("location") or "").lower() for x in REGION[:30]):
                continue
            jobs.append({
                "quelle": "Arbeitnow",
                "id": f"an-{j.get('slug')}",
                "titel": j.get("title", ""),
                "firma": j.get("company_name", ""),
                "ort": j.get("location", ""),
                "gehalt": "",
                "homeoffice": "ja" if j.get("remote") else "",
                "datum": dt.datetime.fromtimestamp(j.get("created_at", 0)).strftime("%Y-%m-%d"),
                "link": j.get("url", ""),
                "text": clean(j.get("description")),
                "anstellung": ", ".join(j.get("job_types") or []),
                "suchbegriff": "Arbeitnow",
            })
    return jobs


# --------------------------------------------------------------------------- #
# Bewertung: Samstag, Pro/Contra, Score
# --------------------------------------------------------------------------- #
FREI = re.compile(
    r"(kein\w*|ohne)\s+(samstags?|wochenend)\w*|(samstags?|samstagen)\s+(ist\s+|hast du\s+)?frei|wochenenden?\s+(sind\s+|ist\s+)?frei|"
    r"freie[sn]?\s+wochenende", re.I)
SAMSTAG_JA = re.compile(
    r"samstag|\bsa\.?\s*(?:von|ab|\d)|mo(?:ntag)?\.?\s*(?:-|–|bis)\s*sa(?:mstag)?\b|"
    r"wochenend(?:arbeit|dienst|einsä|schicht)|am wochenende|6[- ]tage[- ]woche|sechs[- ]tage|"
    r"schichtdienst|rollierend|verkaufsoffen", re.I)
# Hinweise auf Laden/Filiale/Callcenter ohne klare Zeitangabe → meist auch samstags
HANDEL_HINWEIS = re.compile(
    r"einzelhandel|filiale|\bstore\b|im markt|verkaufsfläche|ladengeschäft|im laden\b|an der kasse|\bkasse\b|"
    r"kassierer|öffnungszeiten|callcenter|call center|kundenkontaktcenter|möbelhaus|baumarkt|"
    r"autohaus|supermarkt|drogerie|outlet|\bshop\b|geschäft in der innenstadt", re.I)
# Ketten mit Ladenöffnung am Samstag → immer „prüfen“, auch wenn „Mo–Fr“ (z. B. Berufsschule) im Text steht
LADENKETTEN = re.compile(
    r"\b(bauhaus|obi|hornbach|toom|hagebau|globus|rewe|edeka|lidl|aldi|penny|netto|kaufland|famila|"
    r"combi|rossmann|\bdm\b|müller|ikea|media ?markt|saturn|h&m|primark|decathlon|deichmann|tedi|"
    r"action|poco|roller|xxxlutz|porta|dänisches bettenlager|jysk|fressnapf|thalia|douglas|"
    r"intersport|zara|c&a|tk maxx|kik|woolworth|depot|apollo|fielmann|vorwerk store|telekom shop|"
    r"vodafone shop|o2 shop|expert|euronics|karstadt|galeria)\b", re.I)
RELEVANT = re.compile(
    r"vertrieb|verkauf|verkäuf|sales|kunde|berat|account|handel|kauf(frau|mann|leute)|filial|kass|"
    r"innendienst|außendienst|aussendienst|service|business|key|gebiet|store|shop|markt|einzelhand|"
    r"großhand|telefon|akquise|vermittl|disponent|disposition|repräsent|agent|promoter", re.I)
MO_FR = re.compile(r"mo(?:ntag|\.)?\s*(?:-|–|bis)\s*fr(?:eitag|\.)?|5[- ]tage[- ]woche|fünf[- ]tage", re.I)


def samstag(text: str, kopf: str = "") -> str:
    if FREI.search(text):
        return "nein (Wochenende frei)"
    kette = LADENKETTEN.search(kopf)
    if kette and not SAMSTAG_JA.search(text):
        return f"prüfen – Ladenkette „{kette.group(0)}“, meist auch samstags"
    ja = SAMSTAG_JA.search(text)
    if ja:
        ctx = text[max(0, ja.start() - 60): ja.end() + 60].replace("\n", " ").strip()
        return f"ja/möglich: „…{ctx}…“"
    if MO_FR.search(text):
        return "nein (Mo–Fr)"
    h = HANDEL_HINWEIS.search(text)
    if h:
        return f"prüfen – Laden/Filiale/Callcenter („{h.group(0)}“), oft auch samstags"
    return "nicht erwähnt (Büro/Außendienst → meist Mo–Fr)"


PRO = [
    (r"fix(um|gehalt|es gehalt)|festgehalt|grundgehalt", "Festgehalt"),
    (r"provision|bonus|variable[rn]? (vergütung|gehalt)|erfolgsbeteiligung|prämie", "Provision/Bonus"),
    (r"firmenwagen|dienstwagen|firmen-?pkw|auch zur privaten nutzung", "Firmenwagen"),
    (r"home-?office|mobiles arbeiten|remote", "Homeoffice möglich"),
    (r"unbefristet", "Unbefristet"),
    (r"quereinst|keine (vorkenntnisse|erfahrung)|ohne erfahrung|berufseinsteiger", "Quereinsteiger willkommen"),
    (r"3[0-9] (urlaubs)?tage|30 tage urlaub", "≥30 Tage Urlaub"),
    (r"weiterbildung|schulung|einarbeitung|akademie|coaching", "Einarbeitung/Weiterbildung"),
    (r"altersvorsorge|bav\b|pensionskasse", "Betriebliche Altersvorsorge"),
    (r"jobrad|e-?bike|fahrrad-?leasing", "JobRad"),
    (r"deutschlandticket|jobticket|deutschland-?ticket", "Jobticket"),
    (r"gleitzeit|flexible arbeitszeit", "Flexible Arbeitszeit"),
    (r"teilzeit|\b(25|30|32|35) ?(std|stunden|h)\b", "Teilzeit möglich (z. B. 30 Std.)"),
    (r"weihnachtsgeld|urlaubsgeld|13\.? (monats)?gehalt", "Urlaubs-/Weihnachtsgeld"),
]
CONTRA = [
    (r"reisebereitschaft|reisetätigkeit|übernachtung|bundesweit", "Reisetätigkeit"),
    (r"mehrjährige|(\d|drei|fünf)\+? jahre .{0,30}erfahrung|einschlägige erfahrung|nachweisbare erfolge", "Erfahrung gefordert"),
    (r"(?<!un)befristet", "Befristet"),
    (r"auf selbstst?ändiger basis|selbstst?ändige[rn]? (handelsvertreter|tätigkeit|vertriebspartner|unternehmer)|als selbstst?ändige|freiberuflich|handelsvertreter|§ ?84|freie[rn]? mitarbeit|reine provision|provisionsbasis|ohne fixum", "Selbstständig/Provision ohne Fix"),
    (r"zeitarbeit|personaldienstleist|arbeitnehmerüberlassung|im auftrag unseres kunden", "Zeitarbeit/Vermittler"),
    (r"schicht", "Schichtarbeit"),
    (r"kaltakquise|telefonakquise|door[- ]to[- ]door|haustür", "Kaltakquise/Haustür"),
    (r"minijob|midijob|aushilf|geringfügig|520 ?€|538 ?€|556 ?€|603 ?€", "Minijob/Aushilfe"),
    (r"verhandlungssicher(es)? englisch|fließend(es)? englisch|business english", "Englisch verhandlungssicher"),
    (r"studium|hochschulabschluss|bachelor|master", "Studium gewünscht"),
]
SENIOR = re.compile(r"\b(leiter|head of|director|teamlead|teamleiter|senior|vertriebsleit|geschäftsführ)", re.I)


def bewerten(job: dict) -> None:
    t = f"{job['titel']} {job['text']} {job.get('anstellung', '')}".lower()
    pros = [label for rx, label in PRO if re.search(rx, t)]
    cons = [label for rx, label in CONTRA if re.search(rx, t)]
    if job["gehalt"]:
        pros.insert(0, f"Gehalt: {job['gehalt']}")
        nums = [int(x.replace(".", "")) for x in re.findall(r"\d{1,3}(?:\.\d{3})+", job["gehalt"])]
        if nums and "/Jahr" in job["gehalt"] and max(nums) < 36000:
            cons.append("Eher niedriges Gehalt")
    if SENIOR.search(job["titel"]):
        cons.append("Führungs-/Senior-Rolle")
    job["minuten"], job["fahrt"] = fahrt(f"{job['ort']} {job.get('ort_detail', '')}", job.get("plz", ""), f"{job['titel']} {job['text'][:3000]}")
    m = job["minuten"]
    if m is not None:
        if m <= 15:
            pros.append(f"Kurzer Weg (~{m} Min)")
        elif m > MAX_MINUTEN:
            cons.append(f"Weit weg (~{m} Min)")
        elif m > 25:
            cons.append(f"Fahrt ~{m} Min")
    job["samstag"] = samstag(f"{job['titel']} {job['firma']} {job['text']}", f"{job['titel']} {job['firma']}")
    if re.search(r"\bausbildung|azubi|duales studium|werkstudent|praktik", job["titel"], re.I):
        cons.append("Ausbildung/Studentenjob")
    job["weserpark"] = job["quelle"] == "Weserpark" or bool(WESERPARK.search(f"{job['ort']} {job['titel']} {job['text']}"))
    if job["weserpark"]:
        pros.append("Weserpark – 5 Tage/30 Std. verhandeln")
    job["kategorie"] = "Weserpark" if job["weserpark"] else ("Handel" if job["suchbegriff"].split(", ")[0] in HANDEL
                        else "Kundenservice" if "kundenservice" in job["suchbegriff"].lower() else "Vertrieb")
    score = 40 + 4 * len(pros) - 8 * len(cons)
    score += 10 if "Festgehalt" in pros and "Provision/Bonus" in pros else 0
    score += 8 if job["samstag"].startswith("nein") else 0
    score -= 15 if job["samstag"].startswith("prüfen") and not job["weserpark"] else 0
    score -= 20 if "Selbstständig/Provision ohne Fix" in cons else 0
    score += 6 if m is not None and m <= 15 else 0
    job["pro"] = " · ".join(pros) or "–"
    job["contra"] = " · ".join(cons) or "–"
    job["score"] = max(0, min(100, score))


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #
SPALTEN = [
    ("score", "Score", 8), ("kategorie", "Bereich", 12), ("titel", "Stelle", 48), ("firma", "Firma", 30), ("ort", "Ort", 24), ("fahrt", "Fahrt ab Mahndorf", 30), ("minuten", "Min.", 6),
    ("gehalt", "Gehalt", 26), ("samstag", "Samstagsarbeit?", 30), ("pro", "Pro", 55),
    ("contra", "Contra", 45), ("homeoffice", "Homeoffice", 11), ("anstellung", "Anstellung", 14),
    ("datum", "Online seit", 11), ("bewerben_bis", "Läuft bis", 11), ("quelle", "Quelle", 10),
    ("suchbegriff", "Suchbegriff", 18), ("link", "Link", 60), ("status", "Mein Status", 14),
]


def export(jobs: list[dict], aussortiert: list[dict], stamp: str, wp: list[dict] | None = None,
           initiativ: list[dict] | None = None, zuweit: list[dict] | None = None) -> tuple[Path, Path]:
    wp, initiativ, zuweit = wp or [], initiativ or [], zuweit or []
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    OUT.mkdir(parents=True, exist_ok=True)
    csv_p, xls_p = OUT / f"jobs_bremen_{stamp}.csv", OUT / f"jobs_bremen_{stamp}.xlsx"

    # CSV: Semikolon + UTF-8-BOM → öffnet sauber in deutschem Excel/Numbers
    with csv_p.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([h for _, h, _ in SPALTEN])
        for j in jobs + wp + initiativ:
            w.writerow([j.get(k, "") for k, _, _ in SPALTEN])

    wb = Workbook()
    head_fill = PatternFill("solid", fgColor="1F3864")

    def sheet(ws, rows):
        ws.append([h for _, h, _ in SPALTEN])
        for c in ws[1]:
            c.font, c.fill = Font(bold=True, color="FFFFFF"), head_fill
            c.alignment = Alignment(vertical="center", wrap_text=True)
        for j in rows:
            ws.append([j.get(k, "") for k, _, _ in SPALTEN])
            r = ws.max_row
            link = ws.cell(r, [k for k, _, _ in SPALTEN].index("link") + 1)
            if link.value:
                link.hyperlink, link.style = link.value, "Hyperlink"
            sa = ws.cell(r, [k for k, _, _ in SPALTEN].index("samstag") + 1)
            if str(sa.value).startswith("prüfen"):
                sa.fill = PatternFill("solid", fgColor="FFD966")
            elif str(sa.value).startswith("nein"):
                sa.fill = PatternFill("solid", fgColor="C6EFCE")
            sc = ws.cell(r, 1)
            sc.fill = PatternFill("solid", fgColor="C6EFCE" if j["score"] >= 70 else "FFEB9C" if j["score"] >= 50 else "FFC7CE")
        for i, (_, _, wdt) in enumerate(SPALTEN, 1):
            ws.column_dimensions[get_column_letter(i)].width = wdt
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(vertical="top", wrap_text=True)
        ws.freeze_panes = "C2"
        ws.auto_filter.ref = ws.dimensions

    ws = wb.active
    ws.title = "Jobs ohne Samstag"
    sheet(ws, jobs)
    sheet(wb.create_sheet("Weserpark (Stellen)"), wp)
    sheet(wb.create_sheet("Weserpark (initiativ)"), initiativ)
    sheet(wb.create_sheet(f"Zu weit (>{MAX_MINUTEN} Min)"), zuweit)
    sheet(wb.create_sheet("Aussortiert (Samstag)"), aussortiert)
    info = wb.create_sheet("Info")
    for row in [
        ["Erstellt", dt.datetime.now().strftime("%d.%m.%Y %H:%M")],
        ["Treffer (ohne Samstag, ≤ Fahrzeit)", len(jobs)], ["Aussortiert wegen Samstag", len(aussortiert)],
        ["Fahrt", f"ab Bremen-Mahndorf, max. {MAX_MINUTEN} Min (darüber → Blatt „Zu weit“, {len(zuweit)} Stellen). Sprit: {SPRIT_L_100KM} l/100 km × {SPRIT_EUR_L} €/l × {ARBEITSTAGE} Tage hin+zurück. Werte sind Schätzungen."],
        ["Weserpark initiativ", f"{len(initiativ)} Geschäfte ohne ausgeschriebene Stelle – Passung als Score (Mobilfunk/Elektronik am besten). Link = Shopseite oder Google-Suche nach Karriereseite."],
        ["Weserpark", f"{len(wp)} Stellen – Samstag dort üblich, aber bewusst drin: bei der Bewerbung 5 Tage/Woche, 30 Std. ohne Samstag verhandeln."],
        ["Score", "40 Basis, +4 je Pro, −8 je Contra, +10 Fix+Provision, +6 Fahrt ≤15 Min, +8 Mo–Fr bestätigt, −15 Samstag prüfen (Laden/Filiale), −20 reine Provision"],
        ["Samstag-Check", "grün = Mo–Fr/Wochenende frei bestätigt · gelb = prüfen (Laden/Filiale/Callcenter) · ohne Farbe = nicht erwähnt. Samstag ausdrücklich genannt → Blatt „Aussortiert“."],
        ["Gehalt", "„geschätzt“ = StepStone-Schätzung, nicht Angabe des Arbeitgebers."],
    ]:
        info.append(row)
    info.column_dimensions["A"].width, info.column_dimensions["B"].width = 26, 100
    wb.save(xls_p)
    return xls_p, csv_p


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Jobsuche Bremen ohne Samstagsarbeit → Excel + CSV")
    ap.add_argument("-b", "--begriffe", nargs="+", default=STANDARD_BEGRIFFE)
    ap.add_argument("--radius", type=int, default=30, help="Umkreis km um Bremen (Standard 30)")
    ap.add_argument("--max-minuten", type=int, default=MAX_MINUTEN, help="max. Fahrzeit ab Mahndorf (Standard 30)")
    ap.add_argument("--seiten", type=int, default=2, help="Ergebnisseiten je Begriff (à 25)")
    ap.add_argument("--schnell", action="store_true", help="1 Seite, keine Detailseiten")
    ap.add_argument("--out", type=Path, help="Ausgabeordner (Standard: projekte/jobsuche-bremen/ergebnisse)")
    ap.add_argument("--mit-samstag", action="store_true", help="Samstagsjobs nicht aussortieren")
    a = ap.parse_args()
    if a.schnell:
        a.seiten = 1
    if a.out:
        global OUT
        OUT = a.out

    t0 = time.time()
    print(f"🔎 Suche {len(a.begriffe)} Begriffe, Radius {a.radius} km …", flush=True)
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda b: stepstone(b, a.radius, a.seiten), a.begriffe))
        res += list(ex.map(lambda b: stepstone(b, 10, 1, "verden-aller"), a.begriffe))  # Ostseite bis Verden
        res.append(stepstone("weser-park", 10, 2))  # StepStone-Anzeigen mit Weserpark-Bezug
        ini = ex.submit(weserpark_initiativ)
        an = ex.submit(arbeitnow)
        wpf = ex.submit(weserpark)
        alle = [j for r in res for j in r] + an.result() + wpf.result()

    uniq: dict[str, dict] = {}
    for j in alle:
        key = re.sub(r"\W+", "", (j["titel"] + j["firma"]).lower())
        if key in uniq:
            if j["suchbegriff"] not in uniq[key]["suchbegriff"]:
                uniq[key]["suchbegriff"] += ", " + j["suchbegriff"]
            continue
        uniq[key] = j
    jobs = list(uniq.values())
    print(f"   {len(alle)} Treffer → {len(jobs)} eindeutige Stellen", flush=True)

    if not a.schnell:
        print("📄 Lade Detailseiten (Volltext für Samstags-Check) …", flush=True)
        with ThreadPoolExecutor(8) as ex:
            list(ex.map(stepstone_detail, [j for j in jobs if j["quelle"] == "StepStone"]))

    vorher = len(jobs)
    jobs = [j for j in jobs if j["quelle"] == "Weserpark" or RELEVANT.search(j["titel"])]
    print(f"   {vorher - len(jobs)} fachfremde Stellen (Titel ohne Vertrieb/Verkauf/Handel/Kunde …) entfernt", flush=True)
    for j in jobs:
        j.setdefault("anstellung", "")
        j.setdefault("bewerben_bis", "")
        j["status"] = ""
        bewerten(j)

    wp = sorted([j for j in jobs if j["weserpark"]], key=lambda j: -j["score"])
    rest = [j for j in jobs if not j["weserpark"]]
    for j in rest:
        if j["fahrt"] == "unbekannt":
            j["fahrt"] = "Ort nicht in Tabelle → vermutlich > 30 Min (bei Bedarf ORTE ergänzen)"
            j["minuten"] = 99
    zuweit = sorted([j for j in rest if j["minuten"] is not None and j["minuten"] > a.max_minuten], key=lambda j: j["minuten"])
    rest = [j for j in rest if j not in zuweit]
    vorhanden = {re.sub(r"\W+", "", j["firma"].lower())[:8] for j in wp}
    initiativ = [r for r in ini.result() if re.sub(r"\W+", "", r["firma"].lower())[:8] not in vorhanden]
    ok = [j for j in rest if a.mit_samstag or not j["samstag"].startswith("ja")]
    raus = [j for j in rest if j not in ok]
    ok.sort(key=lambda j: -j["score"])
    raus.sort(key=lambda j: -j["score"])

    if not jobs:
        fehler_melden("0 Stellen gefunden – alle Quellen leer")
    if jobs and all(not j["text"].strip() for j in jobs):
        fehler_melden("Kein Anzeigentext geladen – Samstags-Check/Pro/Contra wertlos")
    stamp = dt.date.today().isoformat()
    xls, csvp = export(ok, raus, stamp, wp, initiativ, zuweit)
    fehler_schreiben()
    print(f"✅ {len(ok)} Jobs (≤{a.max_minuten} Min, ohne Samstag), {len(wp)} Weserpark-Stellen, "
          f"{len(initiativ)} Weserpark-Shops initiativ, {len(zuweit)} zu weit, {len(raus)} Samstag aussortiert  ({time.time() - t0:.0f}s)")
    print(f"   Excel: {xls}\n   CSV:   {csvp}")


if __name__ == "__main__":
    sys.exit(main())
