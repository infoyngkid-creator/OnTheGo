#!/usr/bin/env python3
"""
Jobsuche Bremen & umzu – ohne Browser/Chrome, läuft lokal und in der Cloud.

Quellen:  StepStone (Suchergebnis + Detailseiten, strukturierte JSON-Daten)
          Arbeitnow (offene JSON-API)
Filter:   Region Bremen (+ Umkreis), Samstagsarbeit wird erkannt und aussortiert
Ausgabe:  ergebnisse/jobs_bremen_<datum>.xlsx  und  .csv  (mit Pro/Contra & Score)

Aufruf:
  python3 jobsuche.py                      # Standard-Suchbegriffe (Vertrieb & Co.)
  python3 jobsuche.py -b "Vertrieb" "Kundenberater" --seiten 3 --radius 40
  python3 jobsuche.py --schnell            # nur 1 Seite je Begriff, keine Detailseiten
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
OUT = Path(__file__).resolve().parent / "ergebnisse"

STANDARD_BEGRIFFE = [
    "Vertrieb", "Vertriebsmitarbeiter", "Außendienst", "Vertriebsinnendienst",
    "Sales", "Kundenberater", "Key Account", "Quereinsteiger Vertrieb",
    "Account Manager", "Verkaufsberater", "Kundenservice", "Business Development",
]

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


def stepstone(begriff: str, radius: int, seiten: int) -> list[dict]:
    slug = urllib.parse.quote(begriff.lower().replace(" ", "-"))
    jobs = []
    for page in range(1, seiten + 1):
        url = f"https://www.stepstone.de/jobs/{slug}/in-bremen?radius={radius}&page={page}"
        r = get(url)
        if not r:
            break
        items = _stepstone_state(r.text).get("searchResults", {}).get("items", [])
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
        return


# --------------------------------------------------------------------------- #
# Quelle 2: Arbeitnow (offene API, v. a. internationale Firmen)
# --------------------------------------------------------------------------- #
def arbeitnow(seiten: int = 5) -> list[dict]:
    jobs = []
    for page in range(1, seiten + 1):
        r = get(f"https://www.arbeitnow.com/api/job-board-api?page={page}")
        if not r:
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
MO_FR = re.compile(r"mo(?:ntag|\.)?\s*(?:-|–|bis)\s*fr(?:eitag|\.)?|5[- ]tage[- ]woche|fünf[- ]tage", re.I)


def samstag(text: str) -> str:
    if FREI.search(text):
        return "nein (Wochenende frei)"
    ja = SAMSTAG_JA.search(text)
    if ja:
        ctx = text[max(0, ja.start() - 60): ja.end() + 60].replace("\n", " ").strip()
        return f"ja/möglich: „…{ctx}…“"
    if MO_FR.search(text):
        return "nein (Mo–Fr)"
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
    (r"weihnachtsgeld|urlaubsgeld|13\.? (monats)?gehalt", "Urlaubs-/Weihnachtsgeld"),
]
CONTRA = [
    (r"reisebereitschaft|reisetätigkeit|übernachtung|bundesweit", "Reisetätigkeit"),
    (r"mehrjährige|(\d|drei|fünf)\+? jahre .{0,30}erfahrung|einschlägige erfahrung|nachweisbare erfolge", "Erfahrung gefordert"),
    (r"(?<!un)befristet", "Befristet"),
    (r"selbstständig|selbständig|handelsvertreter|§ ?84|freie[rn]? mitarbeit|reine provision|provisionsbasis", "Selbstständig/Provision ohne Fix"),
    (r"zeitarbeit|personaldienstleist|arbeitnehmerüberlassung|im auftrag unseres kunden", "Zeitarbeit/Vermittler"),
    (r"schicht", "Schichtarbeit"),
    (r"kaltakquise|telefonakquise|door[- ]to[- ]door|haustür", "Kaltakquise/Haustür"),
    (r"teilzeit|minijob|520|538|603 ?€", "Teilzeit/Minijob"),
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
    ort = job["ort"].lower()
    if "bremen" in ort:
        pros.append("In Bremen")
    elif not any(r in ort for r in REGION):
        cons.append("Ort außerhalb Kernregion")
    job["samstag"] = samstag(job["text"])
    score = 40 + 4 * len(pros) - 8 * len(cons)
    score += 10 if "Festgehalt" in pros and "Provision/Bonus" in pros else 0
    score += 5 if job["samstag"].startswith("nein") else 0
    score -= 20 if "Selbstständig/Provision ohne Fix" in cons else 0
    job["pro"] = " · ".join(pros) or "–"
    job["contra"] = " · ".join(cons) or "–"
    job["score"] = max(0, min(100, score))


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #
SPALTEN = [
    ("score", "Score", 8), ("titel", "Stelle", 48), ("firma", "Firma", 30), ("ort", "Ort", 24),
    ("gehalt", "Gehalt", 26), ("samstag", "Samstagsarbeit?", 30), ("pro", "Pro", 55),
    ("contra", "Contra", 45), ("homeoffice", "Homeoffice", 11), ("anstellung", "Anstellung", 14),
    ("datum", "Online seit", 11), ("bewerben_bis", "Läuft bis", 11), ("quelle", "Quelle", 10),
    ("suchbegriff", "Suchbegriff", 18), ("link", "Link", 60), ("status", "Mein Status", 14),
]


def export(jobs: list[dict], aussortiert: list[dict], stamp: str) -> tuple[Path, Path]:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    OUT.mkdir(exist_ok=True)
    csv_p, xls_p = OUT / f"jobs_bremen_{stamp}.csv", OUT / f"jobs_bremen_{stamp}.xlsx"

    # CSV: Semikolon + UTF-8-BOM → öffnet sauber in deutschem Excel/Numbers
    with csv_p.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([h for _, h, _ in SPALTEN])
        for j in jobs:
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
            link = ws.cell(r, len(SPALTEN) - 1)
            if link.value:
                link.hyperlink, link.style = link.value, "Hyperlink"
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
    sheet(wb.create_sheet("Aussortiert (Samstag)"), aussortiert)
    info = wb.create_sheet("Info")
    for row in [
        ["Erstellt", dt.datetime.now().strftime("%d.%m.%Y %H:%M")],
        ["Treffer (ohne Samstag)", len(jobs)], ["Aussortiert wegen Samstag", len(aussortiert)],
        ["Score", "40 Basis, +4 je Pro, −8 je Contra, +10 Fix+Provision, +5 Mo–Fr bestätigt, −20 reine Provision"],
        ["Samstag-Check", "Automatisch aus dem Anzeigentext – vor der Bewerbung bitte gegenprüfen."],
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
    ap.add_argument("--seiten", type=int, default=2, help="Ergebnisseiten je Begriff (à 25)")
    ap.add_argument("--schnell", action="store_true", help="1 Seite, keine Detailseiten")
    ap.add_argument("--mit-samstag", action="store_true", help="Samstagsjobs nicht aussortieren")
    a = ap.parse_args()
    if a.schnell:
        a.seiten = 1

    t0 = time.time()
    print(f"🔎 Suche {len(a.begriffe)} Begriffe, Radius {a.radius} km …", flush=True)
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda b: stepstone(b, a.radius, a.seiten), a.begriffe))
        an = ex.submit(arbeitnow)
        alle = [j for r in res for j in r] + an.result()

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

    for j in jobs:
        j.setdefault("anstellung", "")
        j.setdefault("bewerben_bis", "")
        j["status"] = ""
        bewerten(j)

    ok = [j for j in jobs if a.mit_samstag or not j["samstag"].startswith("ja")]
    raus = [j for j in jobs if j not in ok]
    ok.sort(key=lambda j: -j["score"])
    raus.sort(key=lambda j: -j["score"])

    stamp = dt.date.today().isoformat()
    xls, csvp = export(ok, raus, stamp)
    print(f"✅ {len(ok)} Jobs ohne Samstag, {len(raus)} aussortiert  ({time.time() - t0:.0f}s)")
    print(f"   Excel: {xls}\n   CSV:   {csvp}")


if __name__ == "__main__":
    sys.exit(main())
