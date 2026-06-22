# -*- coding: utf-8 -*-
"""
Konsolidierte Urheberrechts-Gesamttabelle ueber alle relevanten GA-Baende.
Spalten: GA | Vortrag/Text (Nr/Titel) | Datum | Ampel | Begruendung | Textgrundlage

Quelle: PDFs in Steiner_GA_pdf/ (+ Zusatzordner 'Neue GAs'); MD-Fallback.
Ausgabe:
  GA-Urheberrecht-Gesamttabelle.md
  GA-Urheberrecht-Gesamttabelle.csv

Aufruf:  python tools/build_gesamttabelle.py [GAid ...]
"""
import os
import re
import csv
import sys

sys.path.insert(0, os.path.dirname(__file__))
import build_urheberrecht_table as B

ROOT = B.ROOT
OUT_MD = os.path.join(ROOT, "GA-Urheberrecht-Gesamttabelle.md")
OUT_CSV = os.path.join(ROOT, "GA-Urheberrecht-Gesamttabelle.csv")

# Vortrags-Marker: 'Zum Vortrag vom ...', 'Zum ersten/zweiten/N. Vortrag ...', 'Zur Ansprache vom ...'
ORD = (r"ersten|zweiten|dritten|vierten|fünften|fuenften|sechsten|siebten|siebenten|"
       r"achten|neunten|zehnten|elften|zwölften|zwoelften|dreizehnten|vierzehnten|"
       r"fünfzehnten|fuenfzehnten|sechzehnten|siebzehnten|achtzehnten|neunzehnten|zwanzigsten")
LEC = re.compile(r"(Zum (?:öffentlichen )?Vortrag vom\b|"
                 r"Zum (?:%s|\d{1,2}\.) Vortrag\b|"
                 r"Zur Ansprache vom\b)" % ORD)

MONTH = (r"Januar|Februar|März|Maerz|April|Mai|Juni|Juli|August|September|"
         r"Oktober|November|Dezember")
DATE = re.compile(r"(\d{1,2}\.\s?(?:%s)\s+\d{4})" % MONTH)
DATE_NUM = re.compile(r"(\d{1,2}\.\d{1,2}\.\d{4})")

REIHE = re.compile(r"((?:Die|Diese) Vortr[äa]ge wurden[^\n]{0,200}|"
                   r"[^\n]{0,40}steinerquellen[^\n]{0,140}|"
                   r"bereits[^\n]{0,30}publiziert[^\n]{0,140}|"
                   r"wurden[^\n]{0,40}(?:erstmals|bereits)[^\n]{0,140})", re.IGNORECASE)

PREPUB_THIRD = re.compile(r"steinerquellen|anthrowiki|fvn-archiv|website|online|Internet", re.IGNORECASE)

# --- Publikations-Logik ---
PUB_VERB = (r"erschien(?:en)?|abgedruckt|wieder\s?abgedruckt|publiziert|"
            r"ver[öo]ffentlicht|Bericht\s+in|Erstver[öo]ffentlichung|"
            r"Wiedergabe|wiedergegeben|Nachdruck|Erstdruck|Sonderausgabe")
BV_FIELD = re.compile(r"Bisherige Ver(?:ö|oe)ffentlichung(?:en)?:\s*(.*?)"
                      r"(?:Datierung:|Zu\s?S\.|$)", re.IGNORECASE | re.DOTALL)
UNPUB = re.compile(r"unver(?:ö|oe)ffentlich|Ver(?:ö|oe)ffentlichung(?:en)?:\s*keine|"
                   r":\s*keine\b|bisher unver", re.IGNORECASE)
TRANSCRIPT = re.compile(r"Aufzeichnung|Stenogramm|Nachschrift|Mitschrift|Vortragsregister|"
                        r"maschinenschriftlich|Notizbuch|Notizzettel|Manuskript|Handschrift|"
                        r"eigenem Entwurf|keine direkten", re.IGNORECASE)
YEAR_ANY = re.compile(r"\b(1[89]\d\d|20[0-2]\d)\b")

# Phrasen-verankerte Publikationsmuster (nur diese gelten als Vorveroeffentlichung)
BERICHT_PAT = re.compile(r"Bericht\s+(?:in|aus)\b.{0,260}?\b(1[89]\d\d)\b", re.IGNORECASE)
PUBIN_PAT = re.compile(r"\b(?:erschien(?:en)?|abgedruckt|wieder\s?abgedruckt|publiziert|"
                       r"ver[öo]ffentlicht|Erstver[öo]ffentlichung|Erstdruck|Nachdruck|"
                       r"Einzelausgabe|Sonderausgabe)\b.{0,170}?\b(1[89]\d\d|20[0-2]\d)\b",
                       re.IGNORECASE)
GA_PRIOR_PAT = re.compile(r"(?:ver[öo]ffentlicht in|abgedruckt in|publiziert in|Erstdruck in|"
                          r"Nachdruck in|Wiedergabe.{0,30}?in|Berichtigung zur Wiedergabe.{0,40}?in)"
                          r".{0,70}?GA\s?\d{1,3}[a-z]?.{0,45}?\b(1[89]\d\d|20[0-2]\d)\b",
                          re.IGNORECASE)
ANNOT = re.compile(r"(?m)\n\s*\d{1,3}\s+[«\"„A-ZÄÖÜ]")


def isolate_note(chunk):
    """Nur die Textgrundlagen-/Quellen-Aussage – ohne die nachfolgenden
    seitenbezogenen Sach-Anmerkungen (die viele Zitat-Jahre enthalten)."""
    m = re.search(r"Textgrundlage", chunk)
    seg = chunk[m.start():] if m else chunk
    cut = ANNOT.search(seg)
    if cut:
        seg = seg[:cut.start()]
    return seg[:900]


def pub_years(s):
    ys = []
    for pat in (BERICHT_PAT, PUBIN_PAT, GA_PRIOR_PAT):
        ys += [int(m.group(1)) for m in pat.finditer(s)]
    return ys


def classify_pub(note, reihe, ed_year):
    """Ampel + Begruendung aus Vorveroeffentlichungs-Vermerken (phrasen-verankert).
    Einzelnotiz (note) und Reihen-Notiz (reihe) werden getrennt ausgewertet,
    damit Reihen-Kopfdaten keine falschen Jahre in die Einzelnotiz tragen."""
    s = re.sub(r"\s+", " ", note).strip()
    r = re.sub(r"\s+", " ", (reihe or "")).strip()
    # §71 entsteht bei Erstdruck NACH 1995
    newed = isinstance(ed_year, int) and ed_year >= 1996
    # 1) Feld 'Bisherige Veröffentlichungen' (v.a. GA 46)
    bv = BV_FIELD.search(s)
    if bv:
        seg = bv.group(1)
        ys = [int(y) for y in YEAR_ANY.findall(seg)]
        if re.search(r"\bkeine\b|unver(ö|oe)ffentlich", seg, re.IGNORECASE) and not any(y < 1996 for y in ys):
            return "🔴 §71", "Bisherige Veröffentlichungen: keine → Erstdruck"
        if any(y < 1996 for y in ys):
            return "🟢 frei", "Vorabdruck %d (Bisherige Veröff.)" % min(y for y in ys if y < 1996)
        if any(y >= 1996 for y in ys):
            return "🔴 §71", "Erstdruck %d (Neuausgabe)" % min(y for y in ys if y >= 1996)
    # 2) explizit unveröffentlicht
    if UNPUB.search(s):
        return "🔴 §71", "als unveröffentlicht bezeichnet"
    # 3) Vorveröffentlichung in der Einzelnotiz (phrasen-verankert)
    ys = pub_years(s)
    if ys:
        if any(y < 1996 for y in ys):
            return "🟢 frei", "Vordruck %d" % min(y for y in ys if y < 1996)
        if PREPUB_THIRD.search(s):
            return "🟡 prüfen", "Vorabdruck %d durch Dritte – kein Verlags-Erstdruck" % min(ys)
        return "🔴 §71", "Erstdruck %d (nach 1995)" % min(ys)
    # 4) Reihen-Ebene (gilt für alle Vorträge der Reihe)
    if r:
        if PREPUB_THIRD.search(r):
            yr = re.search(r"\b(19[89]\d|20[0-2]\d)\b", r)
            return "🟡 prüfen", "Reihe vorpubliziert durch Dritte%s – kein Verlags-Erstdruck" % (
                (" " + yr.group(1)) if yr else "")
        ry = pub_years(r)
        if any(y < 1996 for y in ry):
            return "🟢 frei", "Reihe-Vordruck %d" % min(y for y in ry if y < 1996)
    # 5) 'bereits publiziert' ohne Jahr
    if re.search(r"bereits\s+(?:publiziert|ver[öo]ffentlicht)", s + " " + r, re.IGNORECASE):
        return "🟡 prüfen", "vorpubliziert (Jahr unklar)"
    # 6) Transkript ohne Vorabdruck-Vermerk
    if TRANSCRIPT.search(s):
        if newed:
            return "🔴 §71", "Transkript, kein Vorabdruck → Erstdruck %s" % ed_year
        return "🟡 prüfen", "Transkript, kein Vorabdruck-Vermerk"
    return "🟡 prüfen", "Quelle unklar"


# Editionsjahr der in der Sammlung vorhandenen Ausgabe (verbindlich)
EDITION_YEAR = {
    "019": 2023, "037": 2019, "041a": 2018, "041b": 2018, "042": 2021, "043": 2023,
    "046": 2020, "068a": 2002, "068b": 2021, "068c": 2017, "068d": 2022,
    "069d": 2017, "069e": 2017, "070a": 2022, "070b": 2023, "071a": 2025, "071b": 2022,
    "080a": 2019, "080b": 2020, "080c": 2020, "087": 2019, "090a": 2018, "090b": 2018,
    "090c": 2021, "091": 2018, "111": 2018, "117a": 2018, "244": 2022, "250": 2020,
    "251": 2023, "252": 2019, "277a": 2022, "288": 2016, "289": 2017, "332b": 2020, "336": 2019,
}


def detect_year(gid, app, fname_year):
    if gid.lower() in EDITION_YEAR:
        return EDITION_YEAR[gid.lower()]
    if isinstance(fname_year, int) and fname_year >= 1900:
        return fname_year
    for pat in (r"1\.\s*Auflage[^\n]{0,30}?(20\d\d|19\d\d)",
                r"©?\s*0?(20[12]\d)\s+Rudolf Steiner", r"©\s*(20\d\d)"):
        m = re.search(pat, app)
        if m:
            return int(m.group(1))
    return fname_year or "?"


def choose_apparatus(gid):
    best = None
    for pdf, year in B.find_pdf_list(gid):
        app = B.get_apparatus(pdf)
        score = len(LEC.findall(app)) * 3 + len(re.findall(r"Textgrundlage", app))
        if not best or score > best[0]:
            best = (score, app, os.path.basename(pdf), year)
    if best and best[0] > 0:
        return best[1], best[2], detect_year(gid, best[1], best[3])
    fb = B.md_fallback(gid)
    if fb:
        app = fb[0]
        return app, os.path.basename(fb[1]) + " (MD-Fallback)", detect_year(gid, app, None)
    return None, None, None


def find_date(text):
    m = DATE.search(text) or DATE_NUM.search(text)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def clean(s, n=200):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n] + " […]"


def nearest_reihe(reihen, pos):
    cur = ""
    for r_start, r_text in reihen:
        if r_start < pos:
            cur = r_text
        else:
            break
    return cur


def rows_for_band(gid):
    app, src, year = choose_apparatus(gid)
    if not app:
        return [], "—", "?"
    rows = []
    marks = list(LEC.finditer(app))
    reihen = [(m.start(), clean(app[m.start():m.start() + 240], 240)) for m in REIHE.finditer(app)]
    CONTENT = re.compile(r"Textgrundlage|Aufzeichnung|Stenogramm|Nachschrift|Mitschrift|"
                         r"Bericht\s+(?:in|aus)|folgt\s+ein|maschinenschriftlich|"
                         r"Vortragsregister|keine direkten", re.IGNORECASE)
    # echte Hinweis-Eintraege (mit Inhalt) – TOC-Treffer ('......') ueberspringen
    real = []
    for i, mk in enumerate(marks):
        s_ = mk.start()
        e_ = marks[i + 1].start() if i + 1 < len(marks) else min(len(app), s_ + 8000)
        chunk = app[s_:e_]
        # echter Hinweis: Inhalts-Marker steht direkt nach dem Vortrags-Header
        if CONTENT.search(chunk[:500]):
            real.append((s_, chunk))
    if len(real) >= 3:
        seen = {}
        for s_, chunk in real:
            head = chunk.split("\n", 1)[0]
            head = re.sub(r"[.\u2026]{3,}.*$", "", head)        # Punktfuehrung weg
            head = re.sub(r"\s+\d{1,4}\s*$", "", head).strip()  # Seitenzahl weg
            datum = find_date(head) or find_date(chunk[:400])
            tgm = re.search(r"Textgrundlagen?:?\s+(.+)", chunk, re.DOTALL)
            tg = clean(tgm.group(1), 220) if tgm else clean(chunk[len(head):], 220)
            rnote = nearest_reihe(reihen, s_)
            amp, why = classify_pub(isolate_note(chunk), rnote, year)
            key = (datum, head[:30])
            if key in seen:
                continue
            seen[key] = 1
            rows.append((str(len(rows) + 1), head, datum, amp, why, tg))
    else:
        for j, m in enumerate(re.finditer(r"Textgrundlagen?:?\s+(.+?)(?:\n\n|$)", app, re.DOTALL)):
            tg = clean(m.group(1), 220)
            pre = app[max(0, m.start() - 110):m.start()]
            title = clean(pre.replace("\n", " "), 80)
            datum = ""
            dm = re.search(r"Datierung:[^\n]*?(\d{1,2}\.\s?(?:%s)\s+\d{4}|\b1[89]\d\d\b|\b20[0-2]\d\b)" % MONTH, m.group(1))
            if dm:
                datum = dm.group(1)
            amp, why = classify_pub(m.group(1), "", year)
            rows.append((str(j + 1), title or "(Text)", datum, amp, why, tg))
    return rows, src, year


def main():
    bands = [a for a in sys.argv[1:] if not a.startswith("--")] or B.RELEVANT
    bands = ["019"] + [b for b in bands if b != "019"]  # GA19 mit aufnehmen
    all_rows = []
    md = ["# Urheberrecht – Gesamttabelle (alle relevanten GA-Bände)\n\n",
          "> Maschinell aus den PDFs erzeugt (`tools/build_gesamttabelle.py`). **Heuristik – zu verifizieren.**\n",
          "> **Ampel:** 🟢 frei (Vor-/Erstdruck vor 1996 belegt) · 🔴 §71 (Erstdruck nach 1995: «keine»/unveröffentlicht oder Transkript ohne Vorabdruck) · 🟡 prüfen (Quelle unklar / Dritt-Vorabdruck).\n",
          "> **Datum** = Vortrags-/Abfassungsdatum (nicht Publikationsjahr). **Begründung** nennt das erkannte Publikationsjahr.\n",
          "> Bei 🔴 aus «Transkript, kein Vorabdruck» gilt: Apparat nennt nur Stenogramm/Manuskript → Erstdruck in der genannten Edition. Gegenprobe via Reihen-/Einzelvermerk möglich.\n",
          "> Verbindliche, handgeprüfte Fassungen: `GA-Urheberrecht-Texte.md`.\n\n",
          "| GA | Nr | Vortrag/Text | Datum | Ampel | Begründung | Textgrundlage |\n",
          "|---|---|---|---|---|---|---|\n"]
    for gid in bands:
        try:
            rows, src, year = rows_for_band(gid)
        except Exception as e:
            md.append("| GA %s | | FEHLER: %s | | | | |\n" % (gid, e))
            print("ERR", gid, e)
            continue
        if not rows:
            md.append("| GA %s | | _(kein PDF/Apparat – manuell)_ | | 🟡 | offen | |\n" % gid)
            print("LEER", gid, "(", src, ")")
            continue
        for nr, title, datum, amp, why, tg in rows:
            gacol = "GA %s" % gid
            md.append("| %s | %s | %s | %s | %s | %s | %s |\n" % (
                gacol, nr, title.replace("|", "/"), datum, amp,
                why.replace("|", "/"), tg.replace("|", "/")))
            all_rows.append([gacol, nr, title, datum, amp, why, tg])
        print("OK", gid, len(rows), "Zeilen")
    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("".join(md))
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["GA", "Nr", "Vortrag/Text", "Datum", "Ampel", "Begruendung", "Textgrundlage"])
        w.writerows(all_rows)
    print("\nGeschrieben:", OUT_MD, "|", len(all_rows), "Zeilen +", OUT_CSV)


if __name__ == "__main__":
    main()
