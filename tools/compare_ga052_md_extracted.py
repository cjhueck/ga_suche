import os
import re
import sys
import difflib
from dataclasses import dataclass
from typing import List, Optional


MD_DIR = r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA052-Spirituelle Seelenlehre und Weltbetrachtung"
EXTRACTED_PATH = r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_md\Steiner, Rudolf GA 052, 1986 - Spirituelle Seelenlehre und Weltbetrachtung_extracted.md"
REPORT_PATH = os.path.join(
    os.path.dirname(MD_DIR),
    "..",
    "reports",
    "ga052_diff_report_quick.md",
)

CHAR_MAP = str.maketrans(
    {
        "ä": "a",
        "ö": "o",
        "ü": "u",
        "Ä": "a",
        "Ö": "o",
        "Ü": "u",
        "ß": "s",
        "�": " ",
    }
)


@dataclass
class LectureSegment:
    number: int
    filename: str
    title: str
    md_text: str
    pdf_text: Optional[str] = None
    start_idx: Optional[int] = None
    end_idx: Optional[int] = None
    ratio: Optional[float] = None
    length_diff: Optional[int] = None
    notes: Optional[str] = None
    snippets: Optional[List[str]] = None


def normalize_text(text: str) -> str:
    text = text.translate(CHAR_MAP)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_extracted_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    # Entferne Seitentrenner und Copyright-Zeilen, entzerre Zeilenumbrüche.
    raw = re.sub(r"^# Page.*$", " ", raw, flags=re.MULTILINE)
    raw = re.sub(r"Copyright Rudolf Steiner Nachlass-Verwaltung.*", " ", raw)
    raw = raw.replace("\n", " ")
    raw = re.sub(r"\s+", " ", raw)
    return normalize_text(raw)


def normalize_md(md: str) -> str:
    # Kopfzeile "Quelle: ..." entfernen
    md = re.sub(r"^Quelle:.*$", " ", md, flags=re.MULTILINE)
    md = re.sub(r"\|\d+\|", " ", md)  # Seitenmarker
    md = re.sub(r"\^[a-z0-9]{5,}", " ", md)  # Fußnoten-Codes
    md = md.replace("\n", " ")
    md = re.sub(r"(?<=\w)-\s+(?=\w)", "", md)  # Silbentrennung
    md = re.sub(r"\s+", " ", md)
    return normalize_text(md)


def date_anchor_from_title(title: str) -> Optional[str]:
    # Erwartet ", Berlin, 6. September 1903" o.ä. im Titel
    m = re.search(r"Berlin,\s*([\d]{1,2})\.\s*([A-Za-zäöüÄÖÜ]+)\s+(\d{4})", title)
    if not m:
        return None
    day, month, year = m.group(1), m.group(2), m.group(3)
    anchor = f"berlin {day} {month} {year}"
    return normalize_text(anchor)


def extract_anchor_from_filename(name: str) -> Optional[tuple]:
    m = re.match(r"GA052 \((\d+)\.\)\s*(.+)\.md$", name)
    if not m:
        return None
    num = int(m.group(1))
    title = m.group(2)
    return num, title


def read_md_files() -> List[LectureSegment]:
    items: List[LectureSegment] = []
    for fname in os.listdir(MD_DIR):
        if not fname.endswith(".md"):
            continue
        if "_backup" in fname:
            continue
        if fname.startswith("GA052 - Spirituelle Seelenlehre"):
            continue  # Gesamtdatei, nicht Vortrag
        anchor = extract_anchor_from_filename(fname)
        if not anchor:
            continue
        num, title = anchor
        with open(os.path.join(MD_DIR, fname), "r", encoding="utf-8") as f:
            content = f.read()
        items.append(
            LectureSegment(
                number=num,
                filename=fname,
                title=title,
                md_text=content,
            )
        )
    items.sort(key=lambda x: x.number)
    return items


def find_segment_boundaries(full_text_norm: str, lectures: List[LectureSegment]) -> None:
    starts = []
    for lec in lectures:
        anchor = date_anchor_from_title(lec.title)
        pos = full_text_norm.find(anchor) if anchor else -1
        if pos == -1:
            # Fallback: vollständiger Titel
            anchor = normalize_text(lec.title)
            pos = full_text_norm.find(anchor)
        if pos == -1:
            # Fallback: erster Satz aus MD
            md_norm = normalize_md(lec.md_text)
            anchor = md_norm[:120]
            pos = full_text_norm.find(anchor)
        if pos == -1:
            lec.notes = "Anker nicht im Extrakt gefunden"
        else:
            lec.start_idx = pos
        starts.append(pos if pos != -1 else None)

    for idx, lec in enumerate(lectures):
        if lec.start_idx is None:
            continue
        next_starts = [s for s in starts[idx + 1 :] if s is not None]
        end = min(next_starts) if next_starts else len(full_text_norm)
        lec.end_idx = end
        lec.pdf_text = full_text_norm[lec.start_idx:end]


def compute_diffs(lecture: LectureSegment) -> None:
    if lecture.pdf_text is None:
        return
    md_norm = normalize_md(lecture.md_text)
    pdf_norm = lecture.pdf_text

    max_len = 40_000
    truncated = False
    if len(md_norm) > max_len:
        md_norm = md_norm[:max_len]
        truncated = True
    if len(pdf_norm) > max_len:
        pdf_norm = pdf_norm[:max_len]
        truncated = True
    if truncated:
        lecture.notes = (lecture.notes or "") + " Vergleich auf 40k Zeichen gekürzt"

    sm = difflib.SequenceMatcher(None, md_norm, pdf_norm)
    lecture.ratio = round(sm.ratio() * 100, 2)
    lecture.length_diff = len(md_norm) - len(pdf_norm)

    snippets = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        md_snip = md_norm[i1:i2][:160]
        pdf_snip = pdf_norm[j1:j2][:160]
        snippets.append(f"{tag}: md='{md_snip}...' | extract='{pdf_snip}...'")
        if len(snippets) >= 5:
            break
    lecture.snippets = snippets


def render_report(extract_found: bool, lectures: List[LectureSegment]) -> str:
    lines = []
    lines.append("# GA052: Schnellvergleich MD vs. Extrakt")
    lines.append("")
    lines.append(f"- Extrakt gefunden: {'ja' if extract_found else 'nein'}")
    lines.append("- Metrik: difflib.SequenceMatcher-Ratio (0-100, höher = ähnlicher)")
    lines.append("- length_diff: Zeichenanzahl MD minus Extrakt-Segment (negativ = Extrakt länger)")
    lines.append("")
    lines.append("| Nr. | Vortrag | Ratio | length_diff | Hinweis |")
    lines.append("| --- | --- | --- | --- | --- |")
    for lec in lectures:
        hint = lec.notes or ""
        ratio = f"{lec.ratio:.2f}" if lec.ratio is not None else "-"
        ldiff = str(lec.length_diff) if lec.length_diff is not None else "-"
        lines.append(f"| {lec.number} | {lec.title} | {ratio} | {ldiff} | {hint} |")

    lines.append("")
    for lec in lectures:
        lines.append(f"## {lec.number}. {lec.title}")
        if lec.notes:
            lines.append(f"- Hinweis: {lec.notes}")
        if lec.ratio is not None:
            lines.append(f"- Ratio: {lec.ratio}")
            lines.append(f"- length_diff: {lec.length_diff}")
        if lec.snippets:
            lines.append("- Beispiele für Abweichungen (erste 5):")
            for snip in lec.snippets:
                lines.append(f"  - {snip}")
        lines.append("")
    return "\n".join(lines)


def main():
    if not os.path.isfile(EXTRACTED_PATH):
        print(f"Extrakt nicht gefunden: {EXTRACTED_PATH}", file=sys.stderr)
        extract_found = False
        full_text_norm = ""
    else:
        full_text_norm = load_extracted_text(EXTRACTED_PATH)
        extract_found = True

    lectures = read_md_files()
    if extract_found:
        find_segment_boundaries(full_text_norm, lectures)
        for lec in lectures:
            compute_diffs(lec)

    report = render_report(extract_found, lectures)
    report_path = os.path.abspath(REPORT_PATH)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Bericht geschrieben nach: {report_path}")


if __name__ == "__main__":
    main()
