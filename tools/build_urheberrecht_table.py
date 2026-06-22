# -*- coding: utf-8 -*-
"""
Erzeugt aus den Band-PDFs (Steiner_GA_pdf/) einen AUTO-Entwurf der
Per-Text-Urheberrechtstabelle: pro Vortrag/Text die Textgrundlage + Ampel.

-> Ausgabe: GA-Urheberrecht-Texte-AUTO.md  (zur Verifikation)
Die handgepflegte Master-Datei GA-Urheberrecht-Texte.md wird NICHT angefasst.

Aufruf:
    python tools/build_urheberrecht_table.py            (alle relevanten Baende)
    python tools/build_urheberrecht_table.py 068c 070a  (nur diese)
"""
import os
import re
import sys

import fitz

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE = os.path.join(ROOT, "Steiner_GA_pdf")
# Zusatz-Ordner mit (oft besser durchsuchbaren) Neuausgaben
EXTRA_DIRS = [r"C:\Users\chuec\OneDrive\Anthroposophie\GA\Neue GAs",
              r"C:\Users\chuec\OneDrive\Anthroposophie\GA\Neue GAs\Neue GA-Bände ab Oktober 2020"]
OUT = os.path.join(ROOT, "GA-Urheberrecht-Texte-AUTO.md")

# Relevante Baende (in Sammlung, neue Edition). GA019 = handgeprueft, hier ausgelassen.
RELEVANT = ["037", "041a", "041b", "042", "043", "046",
            "068a", "068b", "068c", "068d", "069d", "069e",
            "070a", "070b", "071a", "071b", "080a", "080b", "080c",
            "087", "090a", "090b", "090c", "091", "111", "117a", "244",
            "250", "251", "252", "277a", "288", "289", "332b", "336"]

APP_HEAD = re.compile(
    r"(HINWEISE\b|Hinweise zum Text|Über die Veröffentlichungen|"
    r"Nachweis der Veröffentlichungen|ZU DEN TEXTGRUNDLAGEN)", re.IGNORECASE)

LECTURE_SPLIT = re.compile(r"(Zum Vortrag vom [^\n]+|Zur Ansprache vom [^\n]+)")
TG = re.compile(r"Textgrundlagen?:\s*(.+?)(?:\n\n|$)", re.DOTALL)

YEAR = re.compile(r"\b(1[89]\d\d|20[0-2]\d)\b")
BERICHT = re.compile(r"Bericht\s+in|erschien(?:en)?\s+in|abgedruckt\s+in|"
                     r"Wochenschrift|Zeitung|Chronik|Zeitschrift|Magazin", re.IGNORECASE)
PRIORGA = re.compile(r"\bGA\s?\d{1,3}[a-z]?\b.*?(19[5-9]\d|196\d|197\d|198\d|199[0-5])")
MS = re.compile(r"Aufzeichnung|Nachschrift|Stenogramm|Manuskript|Handschrift|"
                r"Vortragsregister|Originalvorlage nicht|maschinenschriftlich|"
                r"Notizbuch|Notizzettel|unver(?:ö|oe)ffentlich", re.IGNORECASE)


def find_pdf_list(gid):
    """Rangliste aller passenden PDFs: (path, year). Primaer-Volledition zuerst,
    dann durchsuchbare Zusatzversionen, dann Rest."""
    m = re.match(r"(\d+)([a-z]?)", gid.lower())
    num_i, suf = int(m.group(1)), m.group(2)
    cands = []
    dirs = [BASE] + [d for d in EXTRA_DIRS if os.path.isdir(d)]
    for d in dirs:
        try:
            files = os.listdir(d)
        except OSError:
            continue
        for f in files:
            if not f.lower().endswith(".pdf"):
                continue
            fm = re.search(r"ga\s*0*(\d+)\s*([a-z]?)", f.lower())
            if not fm or int(fm.group(1)) != num_i or fm.group(2) != suf:
                continue
            full = os.path.join(d, f)
            yr = re.search(r"\b(19|20)\d\d\b", f)
            year = int(yr.group(0)) if yr else 0
            searchable = 1 if ("durchsuchbar" in f.lower() or "korrigiert" in f.lower() or "editiert" in f.lower()) else 0
            lang = 1 if "(lang)" in f.lower() else 0
            primary = 1 if d == BASE and year >= 2016 else 0
            cands.append((primary, year, searchable, lang, os.path.getsize(full), full, year))
    cands.sort(reverse=True)
    return [(c[5], c[6]) for c in cands]


def _slice_apparatus(txt):
    half = len(txt) // 2
    start = 0
    for m in APP_HEAD.finditer(txt):
        if m.start() > half:
            start = m.start()
            break
    return txt[start:] if start else txt


def get_apparatus(path):
    doc = fitz.open(path)
    txt = "\n".join(p.get_text("text") for p in doc)
    doc.close()
    # Marker ('Zum Vortrag vom', 'Textgrundlage:') kommen nur im Apparat vor,
    # daher kann der Volltext durchsucht werden (Schnitt wuerde Notizen abschneiden).
    return txt


def md_fallback(gid):
    """Wenn kein PDF: groesste MD-Datei im Steiner_GA-Bandordner nutzen."""
    sg = os.path.join(ROOT, "Steiner_GA")
    m = re.match(r"(\d+)([a-z]?)", gid.lower())
    pref = "GA%03d%s" % (int(m.group(1)), m.group(2))
    if not os.path.isdir(sg):
        return None
    for name in os.listdir(sg):
        if name.lower().startswith(pref.lower()) or name.lower().startswith("x " + pref.lower()):
            folder = os.path.join(sg, name)
            best = None
            for r, ds, fs in os.walk(folder):
                ds[:] = [d for d in ds if d not in (".obsidian", ".trash", "assets", "images")]
                for f in fs:
                    if f.lower().endswith(".md"):
                        p = os.path.join(r, f)
                        sz = os.path.getsize(p)
                        if not best or sz > best[0]:
                            best = (sz, p)
            if best:
                with open(best[1], "r", encoding="utf-8", errors="replace") as fh:
                    return fh.read(), best[1]
    return None


def classify(src):
    s = re.sub(r"\s+", " ", src)
    # 1) Vorrang: explizites Feld "Bisherige Veröffentlichungen:"
    bv = re.search(r"Bisherige Ver(?:ö|oe)ffentlichung(?:en)?:\s*(.*?)"
                   r"(?:Datierung:|Zu\s?S\.|$)", s, re.IGNORECASE)
    if bv:
        seg = bv.group(1)
        seg_years = [int(y) for y in re.findall(r"\b(1[89]\d\d|20[0-2]\d)\b", seg)]
        if re.search(r"\bkeine\b|unver(ö|oe)ffentlich", seg, re.IGNORECASE) and not any(y < 1996 for y in seg_years):
            return "🔴 §71", "bisher unveröffentlicht → Erstdruck Neuausgabe"
        if any(y < 1996 for y in seg_years):
            return "🟢 frei", "Vorabdruck %d" % min(y for y in seg_years if y < 1996)
        if any(y >= 1996 for y in seg_years):
            return "🔴 §71", "Erstdruck %d" % min(y for y in seg_years if y >= 1996)
        return "🟡 prüfen", "Vorveröffentlichung ohne Jahr"
    # 2) Vortragsbaende ohne BV-Feld – Datierung ausblenden (kein Publikationsjahr)
    s2 = re.sub(r"Datierung:.*", "", s)
    if re.search(r"unver(ö|oe)ffentlich", s, re.IGNORECASE):
        return "🔴 §71", "als unveröffentlicht bezeichnet"
    if BERICHT.search(s2) and re.search(r"\b(18\d\d|19[0-8]\d|199[0-5])\b", s2):
        return "🟢 frei", "zeitgen. Druck/Bericht vor 1996"
    if MS.search(s):
        return "🟡 prüfen", "Transkript – Erstdruck-Status prüfen"
    y2 = [int(y) for y in re.findall(r"\b(1[89]\d\d|20[0-2]\d)\b", s2)]
    if any(y < 1996 for y in y2):
        return "🟢 frei", "Quelle vor 1996"
    return "🟡 prüfen", "Quelle unklar"


def shorten(s, n=240):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n] + " […]"


def parse_rows(app):
    rows = []
    marks = list(re.finditer(r"Zum (?:öffentlichen )?Vortrag vom|Zur Ansprache vom", app))
    if len(marks) >= 3:
        # Vortragsband: positionsbasiert zwischen den Markern aufteilen
        for i, mk in enumerate(marks):
            s_ = mk.start()
            e_ = marks[i + 1].start() if i + 1 < len(marks) else len(app)
            chunk = app[s_:e_]
            label = re.sub(r"\s+", " ", chunk[:90]).strip()
            tgm = re.search(r"Textgrundlagen?:\s*(.+)", chunk, re.DOTALL)
            src = shorten(tgm.group(1)) if tgm else shorten(chunk[len(label):][:320])
            amp, why = classify(src)
            rows.append((label, amp, why, src))
    else:
        # Editions-/Aufsatzband: jede 'Textgrundlage(n)' als Einheit (Doppelpunkt optional)
        for m in re.finditer(r"Textgrundlagen?:?\s+(.+?)(?:\n\n|$)", app, re.DOTALL):
            src = shorten(m.group(1))
            pre = app[max(0, m.start() - 90):m.start()]
            label = shorten(pre.replace("\n", " "), 70)
            amp, why = classify(src)
            rows.append((label or "(Text)", amp, why, src))
    return rows


def process(gid):
    lines = []
    candidates = find_pdf_list(gid)
    chosen = None
    rows = []
    # Rangliste durchprobieren, bis Eintraege gefunden werden
    for pdf, year in candidates:
        app_try = get_apparatus(pdf)
        rows_try = parse_rows(app_try)
        if rows_try and (not chosen or len(rows_try) > len(rows)):
            chosen, app, year_sel, rows = pdf, app_try, year, rows_try
        if chosen and rows:
            break
    if chosen:
        srcname = "PDF: `%s`" % os.path.basename(chosen)
        year = year_sel
    else:
        fb = md_fallback(gid)
        if not fb and candidates:
            # PDF da, aber 0 Eintraege erkannt
            pdf, year = candidates[0]
            app = get_apparatus(pdf)
            rows = parse_rows(app)
            srcname = "PDF: `%s`" % os.path.basename(pdf)
        elif fb:
            app, mdpath = fb
            year = "?"
            rows = parse_rows(app)
            srcname = "MD-Fallback (kein PDF): `%s`" % os.path.basename(mdpath)
        else:
            return ["\n## GA %s — KEIN PDF/MD gefunden\n" % gid]
    lines.append("\n<a id='ga%s'></a>\n## GA %s — Edition %s\n" % (gid, gid, year or "?"))
    lines.append("%s\n\n" % srcname)

    if not rows:
        lines.append("_(keine 'Textgrundlage'-Eintraege im PDF-Apparat gefunden – manuell pruefen)_\n")
        return lines

    g = sum(1 for r in rows if r[1].startswith("🟢"))
    y = sum(1 for r in rows if r[1].startswith("🟡"))
    rd = sum(1 for r in rows if r[1].startswith("🔴"))
    lines.append("**%d Einheiten:** 🟢 %d frei · 🟡 %d prüfen · 🔴 %d §71\n\n" % (len(rows), g, y, rd))
    lines.append("| Text/Vortrag | Ampel | Begründung | Textgrundlage (Auszug) |\n")
    lines.append("|---|---|---|---|\n")
    for marker, amp, why, src in rows:
        marker = marker.replace("|", "/")
        src = src.replace("|", "/")
        why = why.replace("|", "/")
        lines.append("| %s | %s | %s | %s |\n" % (marker[:90], amp, why, src[:200]))
    return lines


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    bands = args if args else RELEVANT
    head = ["# AUTO-Entwurf: Per-Text-Urheberrecht (aus PDFs)\n\n",
            "> Maschinell aus `Steiner_GA_pdf/` erzeugt. **Zu verifizieren.** ",
            "Ampel-Heuristik: 🟢 frei (Druck/GA vor 1996), 🔴 §71 (unveröff.), 🟡 prüfen (Transkript ohne Druckjahr).\n\n",
            "Verifizierte Bände stehen in `GA-Urheberrecht-Texte.md`.\n\n---\n"]
    body = []
    for gid in bands:
        try:
            body += process(gid)
            print("OK GA", gid)
        except Exception as e:
            body.append("\n## GA %s — FEHLER: %s\n" % (gid, e))
            print("ERR GA", gid, e)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("".join(head) + "".join(body))
    print("\nGeschrieben:", OUT)


if __name__ == "__main__":
    main()
