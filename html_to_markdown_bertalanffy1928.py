"""
Convert the UB-Regensburg OCR HTML of
  Bertalanffy, "Kritische Theorie der Formbildung" (1928)
into a cleaned Markdown working copy.

Cleanup performed:
  - HTML entity decoding (umlauts, ß, etc.)
  - Soft-hyphen line-break joining (re-glue 'Abhand-\nlungen' -> 'Abhandlungen')
  - Removal of UB-Regensburg per-page headers ("UNIVERSITÄTSBIBLIOTHEK")
    and urn footers ("urn:nbn:de:bvb:355-ubr20817-8#NNNN")
  - Conversion of <b>/<i> to Markdown ** / *
  - Conversion of <br/> within paragraphs to spaces
  - Page boundaries marked as "## [S. N]" for arabic book pages
    (book page = scan page - 10) or "## [Scan #NNNN]" for front matter
  - Skips trivial pages (covers / library stamps with < MIN_CHARS of real text)
"""

from __future__ import annotations
import html as html_mod
import re
from pathlib import Path

SRC = Path(
    r"C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\Organicism (interwar)"
    r"\Bertalanffy 1928 - Kritische Theorie der Formbildung.html"
)
DST = SRC.with_suffix(".md")

# Pages whose remaining text content (after cleanup) is shorter than this
# are treated as "blank/junk" (covers, library stamps) and skipped.
MIN_CHARS_PER_PAGE = 25

PAGE_DIV_RE = re.compile(
    r'<div style="page-break-before:always;\s*page-break-after:always">'
    r'(.*?)</div></div>',
    re.DOTALL,
)
URN_RE = re.compile(r'urn:nbn:de:bvb:355-ubr20817-8#(\d{4})')
UB_HEADER_PARA_RE = re.compile(
    r'<p>[^<]*?(?:<br\s*/?>\s*)?UNIVERSIT[ÄA]TSBIBLIOTHEK\s*(?:<br\s*/?>)?\s*</p>',
    re.IGNORECASE,
)
URN_PARA_RE = re.compile(
    r'<p>\s*urn:nbn:de:bvb:355-ubr20817-8#\d+\s*</p>'
)
PARA_RE = re.compile(r'<p>(.*?)</p>', re.DOTALL)
BR_RE = re.compile(r'<br\s*/?>')
TAG_RE = re.compile(r'<[^>]+>')

# Running headers / footers that appear on virtually every body page.
# Anchored at the start of a paragraph; stripped (not the whole paragraph).
LEADING_HEADER_RES = [
    # Right (odd) page running header: "**1. Einleitung** 3" possibly
    # followed by body text on the same OCR line.
    re.compile(
        r'^\*\*\s*\d{1,3}(?:\.\d+)*\.\s+[^*\n]{1,80}?\*\*\s*\d{1,3}\b'
    ),
]

# Page footers / signatures stripped wherever they appear (whole-paragraph).
TRAILING_HEADER_RES = [
    # Bottom-of-page binding signature, in its many fragmented variants:
    # "Abhandlungen zur theoretischen Biologie. Heft 27 (Bertalanffy) 1"
    re.compile(
        r'^\*{0,2}\s*Abhandlungen zur theoretischen Biologie\.?\s+'
        r'Heft\s+\d+\s*\(Bertalanffy\)\s*\*{0,2}\s*\d{0,3}\*{0,2}\s*$'
    ),
    re.compile(
        r'^\*{0,2}Abhandlungen zur theoretischen Biologie\.\s+'
        r'Heft\s+\d+\s*\(Bertalanffy\)\*{0,2}\s+\*{0,2}\d{1,3}\*{0,2}\s*$'
    ),
    re.compile(r'^Abhandlungen zur theoretischen Biologie\.?\s*$'),
    re.compile(
        r'^\*{0,2}Heft\s+\d+\s*\(Bertalanffy\)\*{0,2}\s+\d{1,3}\s*$'
    ),
    # Stand-alone printing-signature glyphs like "1*", "2*", "i*", "**15***"
    re.compile(r'^[ivxlcm0-9]{1,4}\*+$', re.IGNORECASE),
    re.compile(r'^\*+\s*[ivxlcm0-9]{1,4}\s*\*+$', re.IGNORECASE),
    # Whole-paragraph bold ending in a page number, e.g.:
    #   **2. Das Prinzip des Mechanismus 11**
    #   **VII. Kapitel: Die Maschinentheorie 109**
    #   **a) Gesetz, Theorie, Erfahrung 93**
    #   **12**
    re.compile(r'^\*\*\s*\d{1,3}\s*\*\*\s*$'),
    re.compile(
        r'^\*\*[^*\n]{2,120}?\s+\d{1,3}\*\*\s*$'
    ),
    # Left (even) page running header (whole-paragraph), allowing the
    # bold to wrap the whole header, just "Kapitel: …", or the Roman+Kapitel:
    #   **2 I. Kapitel: …**
    #   12 I. **Kapitel: …**
    #   14 **I. Kapitel: …**
    #   **18 1. Kapitel: …**   (OCR misreads "I." as "1.")
    re.compile(
        r'^\*{0,2}\s*\d{1,3}\s+\*{0,2}\s*[IVXLCM\d]+\.?\s*\*{0,2}\s*'
        r'Kapitel:\s+[^*\n]{1,80}\*{0,2}\s*$'
    ),
    # Bibliography / index running headers in their many variants:
    #   240 Register             /  234 Literaturverzeichnis
    #   Register **241**         /  Literaturverzeichnis **233**
    #   **232** Literaturverzeichnis
    #   **Register** 243
    re.compile(
        r'^\d{1,3}\s+\*{0,2}(?:Register|Literaturverzeichnis)\*{0,2}\s*$'
    ),
    re.compile(
        r'^\*{0,2}(?:Register|Literaturverzeichnis)\*{0,2}'
        r'\s+\*{0,2}\d{1,3}\*{0,2}\s*$'
    ),
    re.compile(
        r'^\*{0,2}\d{1,3}\*{0,2}'
        r'\s+\*{0,2}(?:Register|Literaturverzeichnis)\*{0,2}\s*$'
    ),
]


def has_real_word(s: str) -> bool:
    """A 'real word' here is a >=4-letter run of letters that has at
    least one vowel and no upper-case letter after position 0
    (so 'ftegensoufQ' fails, 'Buchbinder' passes)."""
    for word in re.findall(r'[A-Za-zÄÖÜäöüß]{4,}', s):
        if not any(c.lower() in 'aeiouäöü' for c in word):
            continue
        if any(c.isupper() for c in word[1:]):
            continue
        return True
    return False


def fmt_emphasis(m: re.Match, marker: str) -> str:
    """Convert <b>/<i> content. Pads the marker with spaces so that
    closing/opening tags adjacent to letters (e.g. "<b>Kepler</b>und")
    do not produce malformed Markdown like "**Kepler**und". The
    redundant spaces are collapsed in `process_paragraph`."""
    inner = m.group(1)
    inner = BR_RE.sub(' ', inner)
    inner = TAG_RE.sub('', inner)
    inner = re.sub(r'\s+', ' ', inner).strip()
    if not inner:
        return ' '
    return f' {marker}{inner}{marker} '


def merge_adjacent_emphasis(text: str) -> str:
    """Merge `**A** **B**` -> `**A B**` (and italics analogously)."""
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r'\*\*\s+\*\*', ' ', text)
        text = re.sub(r'(?<!\*)\*\s+\*(?!\*)', ' ', text)
    return text


def process_paragraph(html: str) -> str:
    p = html
    p = re.sub(r'^(\s|<br\s*/?>)+', '', p)
    p = re.sub(r'(\s|<br\s*/?>)+$', '', p)
    p = re.sub(
        r'<b>(.*?)</b>',
        lambda m: fmt_emphasis(m, '**'),
        p,
        flags=re.DOTALL,
    )
    p = re.sub(
        r'<i>(.*?)</i>',
        lambda m: fmt_emphasis(m, '*'),
        p,
        flags=re.DOTALL,
    )
    p = BR_RE.sub(' ', p)
    p = TAG_RE.sub('', p)
    p = re.sub(r'\s+', ' ', p).strip()
    p = merge_adjacent_emphasis(p)
    p = re.sub(r'\s+', ' ', p).strip()
    return p


INLINE_SIGNATURE_RE = re.compile(
    r'\s+\*{0,2}Heft\s+\d+\s*\(Bertalanffy\)\*{0,2}\s+\d+\s*$'
)


def strip_running_headers(text: str) -> str:
    """Remove leading running headers and standalone footer signatures.
    Iterates until the text is stable."""
    text = INLINE_SIGNATURE_RE.sub('', text).strip()
    prev = None
    while prev != text:
        prev = text
        for pat in LEADING_HEADER_RES:
            text = pat.sub('', text, count=1).strip()
        for pat in TRAILING_HEADER_RES:
            new = pat.sub('', text, count=1).strip()
            if new != text:
                text = new
    return text


def is_letter_spaced_noise(text: str) -> bool:
    """Detect OCR-broken letter-spaced text such as the back-cover stamp
    'U N I V E R S I T Ä T S B I B L I O T H E K' which OCRs as many
    1-letter pseudo-words. True if avg alphabetic-token length < 1.6
    and there are at least 6 such tokens."""
    tokens = re.findall(r'[A-Za-zÄÖÜäöüß]+', text)
    if len(tokens) < 6:
        return False
    avg_len = sum(len(t) for t in tokens) / len(tokens)
    return avg_len < 1.6


def is_cover_garbage(text: str) -> bool:
    """Drop short, mostly-non-alphabetic OCR noise from cover scans."""
    if is_letter_spaced_noise(text):
        return True
    if len(text) > 80:
        return False
    if not has_real_word(text):
        return True
    letters = sum(c.isalpha() for c in text)
    if letters / max(len(text), 1) < 0.45:
        return True
    return False


def main() -> None:
    raw = SRC.read_text(encoding='utf-8')
    text = html_mod.unescape(raw)
    text = re.sub(r'\u00AD\s*<br\s*/?>\s*', '', text)
    text = text.replace('\u00AD', '')

    out: list[str] = []
    out.append('---')
    out.append('title: "Kritische Theorie der Formbildung"')
    out.append('author: "Ludwig von Bertalanffy"')
    out.append('publisher: "Berlin: Borntraeger"')
    out.append('year: 1928')
    out.append('series: "Abhandlungen zur theoretischen Biologie, Heft 27"')
    out.append('editor: "Julius Schaxel"')
    out.append('source_html: "Bertalanffy 1928 - Kritische Theorie der Formbildung.html"')
    out.append('source_pdf: "Bertalanffy 1928 - Kritische Theorie der Formbildung.pdf"')
    out.append('digitization: "Universitätsbibliothek Regensburg, urn:nbn:de:bvb:355-ubr20817-8"')
    out.append('---')
    out.append('')
    out.append('> **Hinweis zur Seitennummerierung:** `## [S. N]` markiert die')
    out.append('> Buchseiten ab Beginn des Haupttextes (Kapitel I, Einleitung,')
    out.append('> Buchseite 1 = Scan #0011). Vorher (Titelei, Vorwort, Inhalt)')
    out.append('> sind die Seiten als `## [Scan #NNNN]` markiert.')
    out.append('> Quelle: bereinigte Konvertierung der OCR-HTML-Fassung der')
    out.append('> UB Regensburg. Worttrennungen, UB-Header und urn-Footer wurden')
    out.append('> entfernt; Hervorhebungen (fett/kursiv) als Markdown übernommen.')
    out.append('')

    pages_seen = 0
    pages_kept = 0
    for page_html in PAGE_DIV_RE.findall(text):
        pages_seen += 1

        urn_match = URN_RE.search(page_html)
        if not urn_match:
            continue
        scan_n = int(urn_match.group(1))

        cleaned = page_html
        cleaned = UB_HEADER_PARA_RE.sub('', cleaned)
        cleaned = URN_PARA_RE.sub('', cleaned)

        is_front_matter = scan_n < 11

        raw_paras: list[str] = []
        for p_match in PARA_RE.finditer(cleaned):
            p_text = process_paragraph(p_match.group(1))
            if p_text:
                raw_paras.append(p_text)

        # On all pages: drop letter-spaced OCR noise (back-cover stamps).
        # On body pages: strip running headers in-place (preserve body
        # text that the OCR may have merged onto the same line).
        # On front-matter pages: drop cover OCR garbage.
        paragraphs: list[str] = []
        for p in raw_paras:
            if is_letter_spaced_noise(p):
                continue
            if is_front_matter:
                if is_cover_garbage(p):
                    continue
            else:
                p = strip_running_headers(p)
            if p:
                paragraphs.append(p)

        total_chars = sum(len(p) for p in paragraphs)
        if total_chars < MIN_CHARS_PER_PAGE:
            continue

        if scan_n >= 11:
            book_n = scan_n - 10
            marker = f"## [S. {book_n}]"
        else:
            marker = f"## [Scan #{scan_n:04d}]"

        out.append('')
        out.append(marker)
        out.append('')
        for p in paragraphs:
            out.append(p)
            out.append('')
        pages_kept += 1

    DST.write_text('\n'.join(out), encoding='utf-8')
    size_kb = DST.stat().st_size / 1024
    print(
        f"Wrote {DST.name}: {size_kb:.1f} KB | "
        f"{pages_seen} scan pages seen, {pages_kept} kept "
        f"(skipped {pages_seen - pages_kept} blank/junk pages)."
    )


if __name__ == '__main__':
    main()
