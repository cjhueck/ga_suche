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

import os
import re
import sys
from dataclasses import dataclass
from typing import List, Optional

import pdfplumber
import difflib


MD_DIR = r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA052-Spirituelle Seelenlehre und Weltbetrachtung"
PDF_PATH = os.path.join(MD_DIR, "Steiner, Rudolf GA 052, 1986 - Spirituelle Seelenlehre und Weltbetrachtung.pdf")
REPORT_PATH = os.path.join(
    os.path.dirname(MD_DIR),
    "..",
    "reports",
    "ga052_diff_report.md",
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


def load_pdf_text(path: str) -> str:
    with pdfplumber.open(path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    raw = "\n".join(pages)
    # Fix Silbentrennungen und vereinheitliche Whitespace.
    raw = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", raw)
    raw = raw.replace("\n", " ")
    raw = re.sub(r"\s+", " ", raw)
    raw = raw.translate(CHAR_MAP)
    return raw.lower().strip()


def normalize_md_text(md: str) -> str:
    # Entferne Seitenmarker wie |13| und Fußnotenmarker ^abc123.
    md = re.sub(r"\|\d+\|", " ", md)
    md = re.sub(r"\^[a-z0-9]{5,}", " ", md)
    md = md.replace("\n", " ")
    md = re.sub(r"(?<=\w)-\s+(?=\w)", "", md)
    md = re.sub(r"\s+", " ", md)
    md = md.translate(CHAR_MAP)
    return md.lower().strip()


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


def find_segment_boundaries(pdf_text: str, lectures: List[LectureSegment]) -> None:
    pdf_lower = pdf_text.lower()
    starts = []
    for lec in lectures:
        anchor = lec.title.lower()
        pos = pdf_lower.find(anchor)
        if pos == -1:
            # Fallback: erster Satz aus MD
            md_norm = normalize_md_text(lec.md_text)
            anchor = md_norm[:120].lower()
            pos = pdf_lower.find(anchor)
        if pos == -1:
            lec.notes = "Anker nicht im PDF gefunden"
        else:
            lec.start_idx = pos
        starts.append(pos if pos != -1 else None)

    # Grenzen setzen
    for idx, lec in enumerate(lectures):
        if lec.start_idx is None:
            continue
        next_starts = [s for s in starts[idx + 1 :] if s is not None]
        end = min(next_starts) if next_starts else len(pdf_text)
        # Falls ein Segment unplausibel groß wird, lieber deckeln.
        if end - lec.start_idx > 200_000:
            end = lec.start_idx + 200_000
            lec.notes = (lec.notes or "") + " Segment gekürzt (200k Zeichen)"
        lec.end_idx = end
        lec.pdf_text = pdf_text[lec.start_idx:end]


def compute_diffs(lecture: LectureSegment) -> None:
    if lecture.pdf_text is None:
        return
    md_norm = normalize_md_text(lecture.md_text)
    pdf_norm = normalize_md_text(lecture.pdf_text)

    max_len = 60_000
    truncated = False
    if len(md_norm) > max_len:
        md_norm = md_norm[:max_len]
        truncated = True
    if len(pdf_norm) > max_len:
        pdf_norm = pdf_norm[:max_len]
        truncated = True
    if truncated:
        lecture.notes = (lecture.notes or "") + " Vergleich auf 60k Zeichen gekürzt"

    sm = difflib.SequenceMatcher(None, md_norm, pdf_norm)
    lecture.ratio = round(sm.ratio() * 100, 2)
    lecture.length_diff = len(md_norm) - len(pdf_norm)

    snippets = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        md_snip = md_norm[i1:i2][:160]
        pdf_snip = pdf_norm[j1:j2][:160]
        snippets.append(f"{tag}: md='{md_snip}...' | pdf='{pdf_snip}...'")
        if len(snippets) >= 5:
            break
    lecture.snippets = snippets


def render_report(pdf_found: bool, lectures: List[LectureSegment]) -> str:
    lines = []
    lines.append("# GA052: Vergleich MD vs. PDF")
    lines.append("")
    lines.append(f"- PDF gefunden: {'ja' if pdf_found else 'nein'}")
    lines.append("- Metrik: difflib.SequenceMatcher-Ratio (0-100, höher = ähnlicher)")
    lines.append("- length_diff: Zeichenanzahl MD minus PDF-Segment (negativ = PDF länger)")
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
    if not os.path.isfile(PDF_PATH):
        print(f"PDF nicht gefunden: {PDF_PATH}", file=sys.stderr)
        pdf_found = False
        pdf_text = ""
    else:
        pdf_text = load_pdf_text(PDF_PATH)
        pdf_found = True

    lectures = read_md_files()
    if pdf_found:
        find_segment_boundaries(pdf_text, lectures)
        for lec in lectures:
            compute_diffs(lec)

    report = render_report(pdf_found, lectures)
    report_path = os.path.abspath(REPORT_PATH)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Bericht geschrieben nach: {report_path}")


if __name__ == "__main__":
    main()
