# -*- coding: utf-8 -*-
"""
Zieht aus den Band-PDFs in Steiner_GA_pdf/ den editorischen Apparat
(Hinweise / Erstveroeffentlichung / Textgrundlage / Nachweis der
Veroeffentlichungen) heraus, damit pro Text die Erstveroeffentlichung
kuratiert werden kann.

Aufruf:
    python tools/extract_pdf_hinweise.py 068c 070a 046
    python tools/extract_pdf_hinweise.py 019 --full   (ganzen Apparat dumpen)
"""
import os
import re
import sys

import fitz  # PyMuPDF

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Steiner_GA_pdf"))
OUTDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "urheberrecht_pdf_dump"))

APP_HEAD = re.compile(
    r"(HINWEISE|Hinweise zum Text|Zu dieser Ausgabe|Zu dieser Auflage|"
    r"Über die Veröffentlichungen|UEBER DIE VERÖFFENTLICHUNGEN|"
    r"Nachweis der Veröffentlichungen|Nachweise|Textnachweise|"
    r"NACHWEIS|Editionsangaben|Zur Edition|ZU DEN TEXTGRUNDLAGEN|Textgrundlagen)",
    re.IGNORECASE)

NOTE_RE = re.compile(
    r"(Textgrundlage|Erstver(?:ö|oe)ffentlichung|Erstdruck|Druckvorlage|"
    r"erstmals\s+(?:ver(?:ö|oe)ffentlicht|gedruckt|abgedruckt|erschienen)|"
    r"zuerst\s+(?:ver(?:ö|oe)ffentlicht|gedruckt|erschienen)|"
    r"(?:wieder)?abgedruckt\s+in|erschien(?:en)?\s+(?:zuerst|erstmals|in|am)|"
    r"ver(?:ö|oe)ffentlicht\s+in|Nachschrift|Stenogramm|Wochenschrift|"
    r"unver(?:ö|oe)ffentlich|nicht\s+ver(?:ö|oe)ffentlich)",
    re.IGNORECASE)

YEAR = re.compile(r"\b(1[89]\d\d|20[0-2]\d)\b")
MS = re.compile(r"(Manuskript|Notizbuch|Notizzettel|Stenogramm|Nachschrift|Handschrift|"
                r"maschinenschriftlich|Typoskript|RSA|verschollen|unver(?:ö|oe)ffentlich)", re.IGNORECASE)
PRINT = re.compile(r"(Zeitschrift|Jahrgang|Jahrg\.|Jg\.|Nr\.|Auflage|Aufl\.|erschien|abgedruckt|"
                   r"Wochenschrift|Lucifer|Goetheanum|Dreigliederung|Verlag|Magazin)", re.IGNORECASE)


def find_pdf(gid):
    """gid z.B. '068c','70a','019'. Findet bevorzugt die neue Edition."""
    g = gid.lower().lstrip("0") or "0"
    # Zielnummer normalisieren: Ziffern + optionaler Buchstabe
    m = re.match(r"(\d+)([a-z]?)", gid.lower())
    num, suf = m.group(1), m.group(2)
    num_i = int(num)
    cands = []
    for f in os.listdir(BASE):
        if not f.lower().endswith(".pdf"):
            continue
        # GA-Nummer aus Dateiname
        fm = re.search(r"ga\s*0*(\d+)\s*([a-z]?)", f.lower())
        if not fm:
            continue
        if int(fm.group(1)) != num_i or fm.group(2) != suf:
            continue
        yr = re.search(r"\b(19|20)\d\d\b", f)
        year = int(yr.group(0)) if yr else 0
        lang = 1 if "(lang)" in f.lower() else 0
        size = os.path.getsize(os.path.join(BASE, f))
        cands.append((lang, year, size, f))
    if not cands:
        return None
    # bevorzugt: (lang), dann hoechstes Jahr, dann groesste Datei
    cands.sort(reverse=True)
    return os.path.join(BASE, cands[0][3])


def extract_text(path):
    doc = fitz.open(path)
    parts = []
    for page in doc:
        parts.append(page.get_text("text"))
    doc.close()
    return "\n".join(parts)


def classify(t):
    years = [int(y) for y in YEAR.findall(t)]
    if PRINT.search(t) and any(y < 1996 for y in years):
        return "frei"
    if re.search(r"unver(ö|oe)ffentlich|nicht ver(ö|oe)ffentlich", t, re.IGNORECASE):
        return "§71?"
    if MS.search(t) and not any(y < 1996 for y in years):
        return "§71?"
    if any(y < 1996 for y in years):
        return "frei?"
    if any(y >= 1996 for y in years):
        return "§71?"
    return "pruefen"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    full = "--full" in sys.argv
    if not args:
        print("Aufruf: python tools/extract_pdf_hinweise.py <GAid> [<GAid> ...] [--full]")
        return
    os.makedirs(OUTDIR, exist_ok=True)
    for gid in args:
        pdf = find_pdf(gid)
        if not pdf:
            print("GA", gid, "-> KEIN PDF gefunden")
            continue
        text = extract_text(pdf)
        # Apparat-Beginn finden (letztes Vorkommen einer Apparat-Ueberschrift
        # in der zweiten Haelfte des Buches)
        half = len(text) // 2
        app_start = 0
        for m in APP_HEAD.finditer(text):
            if m.start() > half:
                app_start = m.start()
                break
        apparatus = text[app_start:] if app_start else text
        paras = re.split(r"\n\s*\n", apparatus)
        out = []
        out.append("PDF: " + os.path.basename(pdf))
        out.append("Apparat-Start bei Zeichen: %d von %d" % (app_start, len(text)))
        out.append("=" * 80)
        if full:
            out.append(apparatus)
        else:
            n = 0
            for p in paras:
                s = re.sub(r"\s+", " ", p).strip()
                if len(s) < 12:
                    continue
                if NOTE_RE.search(s):
                    cls = classify(s)
                    disp = s if len(s) <= 600 else s[:600] + " [...]"
                    out.append("[%s] %s" % (cls, disp))
                    n += 1
            out.append("=" * 80)
            out.append("Treffer: %d" % n)
        outpath = os.path.join(OUTDIR, "GA%s.txt" % gid.lower())
        with open(outpath, "w", encoding="utf-8") as fh:
            fh.write("\n\n".join(out))
        print("GA %s -> %s  (%s)" % (gid, os.path.basename(outpath), os.path.basename(pdf)))


if __name__ == "__main__":
    main()
