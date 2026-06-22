# -*- coding: utf-8 -*-
"""
Extrahiert aus den GA-Baenden (Steiner_GA/) die editorischen Angaben zur
Erstveroeffentlichung / Textgrundlage der einzelnen Texte/Vortraege und
erzeugt einen Markdown-Report fuer die Urheberrechtspruefung.

Grundlage: GA-Baende_zu_loeschen.pdf (Abschlussbaende der GA 2016-2025).
"""
import os
import re
import glob

BASE = os.path.join(os.path.dirname(__file__), "..", "Steiner_GA")
BASE = os.path.abspath(BASE)
OUT = os.path.join(os.path.dirname(__file__), "..", "GA-Erstveroeffentlichungen-Urheberrecht.md")
OUT = os.path.abspath(OUT)

# Reihenfolge wie in der PDF. (Label, Titel, PDF-Erscheinungsjahr, Ordner-Praefix oder None)
PDF_LIST = [
    ("GA 1f",   "Goethes Naturwissenschaftliche Schriften",                 "2017", "GA001"),
    ("GA 18a",  "Welt- und Lebensanschauungen im 19. Jahrhundert",          "2022", None),
    ("GA 19",   "Gedanken waehrend der Zeit des Krieges",                    "2023", "GA019"),
    ("GA 37",   "Das lebendige Wesen der Anthroposophie (AG-Geschichte)",    "2019", "GA037"),
    ("GA 38/1-6","Saemtliche Briefe (Neuausgabe)",                          "2021-28", None),
    ("GA 41a",  "Uebersetzungen aus dem Alten und Neuen Testament",         "2018", "GA041a"),
    ("GA 41b",  "Uebertragungen verschiedener Werke (Blavatsky u.a.)",      "2018", "GA041b"),
    ("GA 42",   "Buehnenbearbeitungen I (Schure)",                          "2021", "GA042"),
    ("GA 43",   "Buehnenbearbeitungen II (Oberuferer Weihnachtsspiele)",    "2023", "GA043"),
    ("GA 46",   "Nachgelassene Abhandlungen und Fragmente 1879-1924",       "2020", "GA046"),
    ("GA 47/48","Aus Notizbuechern und Notizzetteln",                       "2025", None),
    ("GA 49",   "Niederschriften ueber Helmuth und Eliza von Moltke",       "2025", None),
    ("GA 68a",  "Ueber das Wesen des Christentums",                         "2020", "GA068a"),
    ("GA 68b",  "Der Kreislauf des Menschen ...",                           "2021", "GA068b"),
    ("GA 68c",  "Goethe und die Gegenwart",                                 "2017", "GA068c"),
    ("GA 68d",  "Das Wesen des Menschen im Lichte der Geisteswissenschaft", "2022", "GA068d"),
    ("GA 69d",  "Tod und Unsterblichkeit",                                  "2017", "GA069d"),
    ("GA 69e",  "Geisteswissenschaft und die geistigen Ziele unserer Zeit","2017", "GA069e"),
    ("GA 70a",  "Menschenseele, Schicksal und Tod",                         "2022", "GA070a"),
    ("GA 70b",  "Wege zur Erkenntnis der ewigen Kraefte der Menschenseele", "2023", "GA070b"),
    ("GA 71a",  "Seelenunsterblichkeit, Schicksalskraefte ...",            "2025", "GA071a"),
    ("GA 71b",  "Der Mensch als Geist- und Seelenwesen",                    "2022", "GA071b"),
    ("GA 80a",  "Das Wesen der Anthroposophie",                             "2019", "GA080a"),
    ("GA 80b",  "Das Innere der Natur und das Wesen der Menschenseele",     "2020", "GA080b"),
    ("GA 80c",  "Die anthroposophische Geisteswissenschaft ...",          "2020", "GA080c"),
    ("GA 85",   "Nachtragsband: Einzelne oeffentliche Vortraege",          "2025", None),
    ("GA 87",   "Antike Mysterien und Christentum",                         "2021", "GA087"),
    ("GA 90a",  "Selbsterkenntnis und Gotteserkenntnis I",                  "2018", "GA090a"),
    ("GA 90b",  "Selbsterkenntnis und Gotteserkenntnis II",                 "2018", "GA090b"),
    ("GA 90c",  "Theosophie und Okkultismus",                              "2021", "GA090c"),
    ("GA 91",   "Kosmologie und menschliche Evolution. Farbenlehre",       "2018", "GA091"),
    ("GA 111",  "Einfuehrung in die Grundlagen der Theosophie",            "2018", "GA111"),
    ("GA 117a", "Das Johannes-Evangelium und die drei anderen Evangelien", "2018", "GA117a"),
    ("GA 244",  "Gesammelte Fragenbeantwortungen und Interviews",          "2022", "GA244"),
    ("GA 246",  "Nachtragsband: Einzelne Mitgliedervortraege",            "2025", None),
    ("GA 250",  "Deutsche Sektion der Theosophischen Gesellschaft",        "2020", "GA250"),
    ("GA 251",  "Anthroposophische Gesellschaft 1912-1924",               "2023", "GA251"),
    ("GA 252",  "Johannesbau-Verein und Goetheanum-Verein",               "2019", "GA252"),
    ("GA 265a", "Lehrstunden erkenntniskultische Arbeit",                  "2024", None),
    ("GA 277a", "Entstehung und Entwicklung der Eurythmie 1911-1918",      "2022", "GA277a"),
    ("GA 277b", "Eurythmie 1918-1920",                                     "2023", None),
    ("GA 277c", "Eurythmie 1921-1922",                                     "2024", None),
    ("GA 277d", "Eurythmie 1923-1924",                                     "2025", None),
    ("GA 288",  "Architektur, Plastik und Malerei des Ersten Goetheanum",  "2016", "GA288"),
    ("GA 289",  "Der Baugedanke des Goetheanum",                           "2017", "GA289"),
    ("GA 332b", "Vortraege zu wirtschaftlichen und sozialen Fragen",       "2020", "GA332b"),
    ("GA 336",  "Die grossen Fragen der Zeit",                             "2019", "GA336"),
    ("GA K 1-10/57","Das architektonische Werk I",                         "2022", None),
    ("GA K 27-43",  "Das architektonische Werk II",                        "2024", None),
    ("GA K 26b",    "Eurythmiefiguren",                                    "2018", None),
    ("GA K 17-22/25/48/49","Zeichnungen, Karikaturen, Kostueme",           "2025", None),
    ("GA HB",   "Handbuch zur Gesamtausgabe",                              "2026", None),
]

# Band-Typ + Urheberrechts-Einschaetzung auf Bandebene (vom Autor gepflegt).
BAND_TYP = {
    "GA001": ("Buch (zu Lebzeiten gedruckt)", "frei", "Einleitungen 1884-1897 erschienen; Steiner-Text gemeinfrei, nur Apparat (§70)."),
    "GA019": ("Aufsatz + Nachlass-Dokumente", "gemischt", "Essay 1915 gedruckt (frei); Memoranden Erstdruck 1929 (frei); einzelne Aufzeichnungen pruefen."),
    "GA037": ("Aufsaetze (Periodika)", "frei", "Aufsaetze 1902-1925 in Zeitschriften erschienen; Steiner-Text gemeinfrei."),
    "GA041a": ("Uebersetzungen/Uebertragungen", "gemischt", "Bibeluebertragungen tlw. zu Lebzeiten verwendet; Erstdrucke einzeln pruefen."),
    "GA041b": ("Uebertragungen", "gemischt", "Blavatsky-Uebertragung 1907-1911; einzelne Texte pruefen."),
    "GA042": ("Buehnenbearbeitungen", "gemischt", "Schure-Dramen zu Lebzeiten aufgefuehrt/gedruckt; Bearbeitungen pruefen."),
    "GA043": ("Buehnenbearbeitungen", "frei", "Weihnachtsspiele + Aufsaetze (Das Goetheanum 1922 ff.) gedruckt; weitgehend frei."),
    "GA046": ("Nachlass (Manuskripte/Notizen)", "§71-Kandidat", "Ueberwiegend Erstdruck 2020 aus Manuskripten/Notizbuechern -> §71 wahrscheinlich."),
    "GA068a": ("Oeffentliche Vortraege (ALTE Ausg. 2002)", "frei", "Du hast die Ausgabe 2002, nicht die Neuausgabe 2020."),
    "GA068b": ("Oeffentliche Vortraege", "gemischt", "Oeffentliche Vortraege 1903-1910 (Stenogramme); Erstdruck-Status pruefen."),
    "GA068c": ("Oeffentliche Vortraege", "gemischt", "Oeffentliche Vortraege 1889-1912 (Stenogramme); Erstdruck-Status pruefen."),
    "GA068d": ("Oeffentliche Vortraege", "gemischt", "Oeffentliche Vortraege 1905-1910 (Stenogramme); Erstdruck-Status pruefen."),
    "GA069d": ("Oeffentliche Vortraege", "gemischt", "Vortraege 1910-1918 (Stenogramme); Erstdruck-Status pruefen."),
    "GA069e": ("Oeffentliche Vortraege", "gemischt", "Vortraege 1910-1914 (Stenogramme); Erstdruck-Status pruefen."),
    "GA070a": ("Oeffentliche Vortraege", "gemischt", "Vortraege 1914/15 (Stenogramme); viele evtl. Erstdruck 2022 -> §71 pruefen."),
    "GA070b": ("Oeffentliche Vortraege", "gemischt", "Vortraege 1915/16 (Stenogramme); §71 pruefen."),
    "GA071a": ("Oeffentliche Vortraege", "gemischt", "Vortraege 1916/17 (Stenogramme); Erstdruck 2025 -> §71 wahrscheinlich."),
    "GA071b": ("Oeffentliche Vortraege", "gemischt", "Vortraege 1918 (Stenogramme); §71 pruefen."),
    "GA080a": ("Oeffentliche Vortraege", "gemischt", "Vortraege 1922 (Stenogramme); §71 pruefen."),
    "GA080b": ("Oeffentliche Vortraege", "gemischt", "Vortraege 1920-1923 (Stenogramme); §71 pruefen."),
    "GA080c": ("Oeffentliche Vortraege", "gemischt", "Vortraege 1921-1922 (Stenogramme); §71 pruefen."),
    "GA087": ("Mitgliedervortraege", "gemischt", "Vortraege 1901/02 (Nachschriften); §71 pruefen."),
    "GA090a": ("Mitgliedervortraege", "gemischt", "Berlin 1903/04 (Nachschriften); §71 pruefen."),
    "GA090b": ("Mitgliedervortraege", "gemischt", "1905 (Nachschriften); §71 pruefen."),
    "GA090c": ("Lehrstunden", "§71-Kandidat", "13 Lehrstunden vmtl. 1903 (Nachschriften); Erstdruck 2021 -> §71 wahrscheinlich."),
    "GA091": ("Private Lehrstunden", "§71-Kandidat", "Private Lehrstunden 1904/05 (Aufzeichnungen); Erstdruck 2018 -> §71 wahrscheinlich."),
    "GA111": ("Mitgliedervortraege", "gemischt", "Zyklen 1907/1909 (Nachschriften); §71 pruefen."),
    "GA117a": ("Mitgliedervortraege", "gemischt", "Stockholm 1910 (Nachschriften); §71 pruefen."),
    "GA244": ("Fragenbeantwortungen/Interviews", "§71-Kandidat", "Aus Stenogrammen/Notizen, viele Erstdruck 2022; Interviews tlw. zu Lebzeiten gedruckt (frei)."),
    "GA250": ("Ansprachen/Vortraege (Periodika+Nachschr.)", "gemischt", "1902-1912; tlw. dokumentarisch gedruckt, tlw. Erstdruck -> pruefen."),
    "GA251": ("Ansprachen/Vortraege", "gemischt", "1912-1924; §71 pruefen."),
    "GA252": ("Ansprachen/Vortraege", "gemischt", "1911-1924; §71 pruefen."),
    "GA277a": ("Vortraege/Ansprachen", "gemischt", "Eurythmie 1911-1918 (Nachschriften); §71 pruefen."),
    "GA288": ("Vortraege", "gemischt", "Bis 1920 (Stenogramme); §71 pruefen."),
    "GA289": ("Vortraege", "gemischt", "Nach 1920 (Stenogramme); §71 pruefen."),
    "GA332b": ("Vortraege/Ansprachen", "gemischt", "Wirtschaft/Soziales; §71 pruefen."),
    "GA336": ("Vortraege (Soziale Frage)", "gemischt", "1919-1921 (Stenogramme); §71 pruefen."),
}

# Such-Muster fuer editorische Hinweise
# (1) Zeilen, die fast immer editorisch sind (Anfangs-Marker)
STRONG_RE = re.compile(
    r"^(Textgrundlage[n]?\b|Erstver(?:ö|oe)ffentlichung|Erstdruck|Druckvorlage|"
    r"Erschienen\s+in|Ver(?:ö|oe)ffentlicht\s+in)",
    re.IGNORECASE)
# (2) Hinweis-Begriffe, die NUR zusammen mit Jahr/Quelle als editorisch gelten
NOTE_RE = re.compile(
    r"(Textgrundlage[n]?\b|Erstver(?:ö|oe)ffentlichung|Erstdruck|Druckvorlage|"
    r"erstmals\s+(?:ver(?:ö|oe)ffentlicht|gedruckt|abgedruckt|publiziert|erschienen)|"
    r"zuerst\s+(?:ver(?:ö|oe)ffentlicht|gedruckt|erschienen)|"
    r"(?:wieder)?abgedruckt\s+in|erschien(?:en)?\s+(?:zuerst|erstmals|in)|"
    r"ver(?:ö|oe)ffentlicht\s+in|Nachschrift\s+von|Wochenschrift|"
    r"Zeitschrift|Vortragsnachschrift|Bericht\s+(?:in|aus|erschien)|"
    r"Lucifer-?Gnosis|Das\s+Goetheanum|Mitteilungen\s+f(?:ü|ue)r|Der\s+Vahan|"
    r"Stenogramm|Nachschrift)",
    re.IGNORECASE)

YEAR_RE = re.compile(r"\b(1[89]\d\d|20[0-2]\d)\b")
PRINT_HINT = re.compile(r"(Zeitschrift|Jahrgang|Jahrg\.|Jg\.|Nr\.|Auflage|Aufl\.|erschien|abgedruckt|gedruckt|"
                        r"Lucifer|Goetheanum|Dreigliederung|Magazin|Mitteilungen|Vahan|Matin|Verlag)", re.IGNORECASE)
MS_HINT = re.compile(r"(Manuskript|Notizbuch|Notizzettel|Notizblatt|Stenogramm|Nachschrift|Handschrift|"
                     r"maschinenschriftlich|Typoskript|RSA\s|NZ\s?\d|NB\s?\d|verschollen|Original\s+erhalten)", re.IGNORECASE)


def find_folder(prefix):
    if not prefix:
        return None
    for name in os.listdir(BASE):
        full = os.path.join(BASE, name)
        if not os.path.isdir(full):
            continue
        if name.startswith(prefix + "-") or name.startswith("x " + prefix + "-") or name == prefix:
            return full
    return None


def apparatus_file(folder):
    mds = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in (".obsidian", ".trash", "assets", ".backups", "images")]
        for f in files:
            if f.lower().endswith(".md"):
                p = os.path.join(root, f)
                try:
                    mds.append((os.path.getsize(p), p))
                except OSError:
                    pass
    if not mds:
        return None
    mds.sort(reverse=True)
    return mds[0][1]


def split_files(folder):
    pat = re.compile(r"\(\d+[a-z]?\.\)")
    res = []
    for f in os.listdir(folder):
        if f.lower().endswith(".md") and pat.search(f):
            res.append(f)
    def keyf(n):
        m = re.search(r"\((\d+)([a-z]?)\.\)", n)
        return (int(m.group(1)), m.group(2)) if m else (9999, "")
    res.sort(key=keyf)
    return res


def classify(text):
    years = [int(y) for y in YEAR_RE.findall(text)]
    has_old_print = bool(PRINT_HINT.search(text)) and any(y < 1996 for y in years)
    has_ms = bool(MS_HINT.search(text))
    if has_old_print:
        return "frei (Druck vor 1996)"
    if has_ms and not any(y < 1996 for y in years):
        return "§71-Kandidat (Nachlass/Erstdruck)"
    if any(y < 1996 for y in years):
        return "frei (Quelle vor 1996)"
    if any(y >= 1996 for y in years):
        return "§71-Kandidat"
    return "unklar -> pruefen"


def extract_notes(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        return []
    seen = set()
    notes = []
    for ln in lines:
        s = ln.strip()
        s = re.sub(r"\s*\^\w{6,}\s*$", "", s)  # Block-ID-Anker entfernen
        if len(s) < 8:
            continue
        is_strong = bool(STRONG_RE.search(s))
        if not is_strong:
            if not NOTE_RE.search(s):
                continue
            # Fliesstext-Filter: schwache Treffer nur akzeptieren, wenn
            # eine Jahres- oder Quellen-/Archivangabe vorhanden ist und die
            # Zeile nicht uebermaessig lang ist (lange Absaetze = Fliesstext).
            has_year = bool(YEAR_RE.search(s))
            has_src = bool(MS_HINT.search(s)) or bool(re.search(r"Nr\.|Jg\.|Jahrgang|S\.\s?\d", s))
            if not (has_year or has_src):
                continue
            if len(s) > 600 and "Textgrundlage" not in s:
                continue
        key = s[:80].lower()
        if key in seen:
            continue
        seen.add(key)
        disp = s if len(s) <= 400 else s[:400] + " [...]"
        notes.append((disp, classify(s)))
    return notes


def main():
    head = []
    head.append("# Erstveroeffentlichung / Textgrundlagen der GA-Abschlussbaende (2016-2025)\n")
    head.append("Automatisch extrahiert aus `Steiner_GA/`. Grundlage: `GA-Baende_zu_loeschen.pdf`.\n")
    head.append("> **Hinweis:** Keine Rechtsberatung. Ampel ist eine automatische Heuristik aus den ")
    head.append("editorischen Hinweisen und muss im Einzelfall geprueft werden.\n")
    head.append("\n**Urheberrechtlicher Rahmen:** Steiner +1925 -> Werktext seit 1.1.1996 gemeinfrei (§64). ")
    head.append("Erstveroeffentlichung aus dem Nachlass nach 1995 -> §71 (25 J. ab Erscheinen). ")
    head.append("Wissenschaftlicher Apparat -> §70 (25 J.).\n\n---\n")

    present = 0
    missing = []
    # erst Daten sammeln (fuer Uebersichtstabelle), dann Details schreiben
    rows = []
    details = []
    for label, title, pdfyear, prefix in PDF_LIST:
        folder = find_folder(prefix) if prefix else None
        if not folder:
            missing.append((label, title, pdfyear))
            rows.append((label, title, pdfyear, "nein", "", "", "", "", ""))
            continue
        present += 1
        base = os.path.basename(folder)
        key = prefix
        typ, ampel, hinweis = BAND_TYP.get(key, ("", "?", ""))
        app = apparatus_file(folder)
        splits = split_files(folder)
        notes = extract_notes(app) if app else []
        rows.append((label, title, pdfyear, "ja", typ, ampel, str(len(splits)), str(len(notes)), hinweis))

        out = details
        out.append("\n<a id='{p}'></a>\n## {label} — {title}\n".format(p=(prefix or label), label=label, title=title))
        out.append("- **PDF-Erscheinungsjahr:** {y}\n".format(y=pdfyear))
        out.append("- **Ordner:** `{b}`\n".format(b=base))
        out.append("- **Apparat-Datei:** `{a}`\n".format(a=os.path.basename(app) if app else "—"))
        out.append("- **Bandtyp:** {t}\n".format(t=typ))
        out.append("- **Einschaetzung (Band):** **{a}** — {h}\n".format(a=ampel, h=hinweis))
        out.append("- **Anzahl Einzeltexte (Dateien):** {n}\n".format(n=len(splits)))

        if splits:
            out.append("\n### Enthaltene Texte/Vortraege\n")
            for f in splits:
                t = re.sub(r"\.md$", "", f)
                out.append("- {t}\n".format(t=t))

        out.append("\n### Editorische Quellen-/Erstveroeffentlichungshinweise ({n} gefunden)\n".format(n=len(notes)))
        if not notes:
            has_app = False
            if app:
                try:
                    with open(app, "r", encoding="utf-8", errors="replace") as fh:
                        txt = fh.read()
                    has_app = bool(re.search(r"Hinweise|Ueber die Ver|Über die Ver|Editionsgeschichte|Nachweis", txt))
                except OSError:
                    pass
            if has_app:
                out.append("_(Apparat vorhanden, aber keine maschinell erkennbaren ")
                out.append("'Textgrundlage/Erstveroeffentlichung'-Zeilen — bitte Hinweise-Teil manuell sichten)_\n")
            else:
                out.append("_(Editorischer Apparat in der exportierten MD NICHT enthalten — ")
                out.append("Erstveroeffentlichung bitte im gedruckten Band / PDF pruefen)_\n")
        else:
            for disp, amp in notes:
                out.append("- **[{amp}]** {d}\n".format(amp=amp, d=disp))
        out.append("\n---\n")

    details.append("\n## Nicht in der Sammlung enthaltene PDF-Baende\n")
    for label, title, pdfyear in missing:
        details.append("- **{l}** — {t} ({y})\n".format(l=label, t=title, y=pdfyear))

    details.append("\n## Sonderfaelle\n")
    details.append("- **GA 1f / GA 38/1-6:** Du hast GA001 bzw. die alten GA038/GA039 (Briefe I/II), ")
    details.append("nicht die in der PDF gemeinte Neuausgabe.\n")
    details.append("- **GA 68a:** vorhandene Datei = Ausgabe 2002 (nicht Neuausgabe 2020).\n")

    # --- Uebersichtstabelle ---
    AMPEL_SYM = {"frei": "🟢 frei", "gemischt": "🟡 gemischt",
                 "§71-Kandidat": "🔴 §71", "?": "", "": ""}
    ov = []
    ov.append("## Uebersicht aller PDF-Baende\n\n")
    ov.append("| Band | Titel | PDF-Jahr | In Sammlung | Bandtyp | Einschaetzung | # Texte | # Hinweise |\n")
    ov.append("|---|---|---|---|---|---|---|---|\n")
    for label, title, pdfyear, insamm, typ, ampel, ntex, nnotes, hinweis in rows:
        amp = AMPEL_SYM.get(ampel, ampel)
        ov.append("| {l} | {t} | {y} | {s} | {typ} | {a} | {nt} | {nn} |\n".format(
            l=label, t=title, y=pdfyear, s=insamm, typ=typ, a=amp, nt=ntex, nn=nnotes))
    ov.append("\n---\n")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("".join(head) + "".join(ov) + "".join(details))

    print("Report geschrieben:", OUT)
    print("Baende vorhanden:", present, "| fehlen:", len(missing))


if __name__ == "__main__":
    main()
