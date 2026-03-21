"""
Nach OCR: Doppelte Seitenzahlen (Scan + Textlayer) entfernen und genau eine
Seitenzahl unten setzen.

Vorgehen pro Seite:
1. Textspannen, die nur der Seitennummer entsprechen, im unteren Fenster
   (Standard: 200 pt vom unteren Rand) per Redaction entfernen.
2. Unteren Bildstreifen (Standard: 52 pt) weiß überdecken (Scan-Zahl).
3. Zentriert eine neue Seitenzahl einfügen.

Idempotent: Mehrfaches Ausführen ersetzt die Fußzeile erneut, ohne zu „verdoppeln“.

Abhängigkeit: PyMuPDF (import fitz).

Beispiel:
  python tools/pdf_ocr_single_page_footer.py eingabe.pdf -o ausgabe.pdf
  python tools/pdf_ocr_single_page_footer.py eingabe.pdf --footer-strip-pt 52 --footer-window-pt 220
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import fitz


def _iter_text_spans(page: fitz.Page):
    for b in page.get_text("dict").get("blocks", []):
        if b.get("type") != 0:
            continue
        for line in b.get("lines", []):
            for span in line.get("spans", []):
                yield span


def _span_rect(span: dict) -> fitz.Rect:
    return fitz.Rect(span["bbox"])


def _redact_duplicate_page_numbers(
    page: fitz.Page,
    page_no: int,
    *,
    footer_window_pt: float,
    max_number_width_pt: float,
) -> int:
    """
    Entfernt Textspannen, die nur die gedruckte Seitennummer sind und im
    unteren Fenster liegen. Gibt die Anzahl der Redactions zurück.
    """
    rect = page.rect
    threshold_y = rect.y1 - footer_window_pt
    target = str(page_no)
    count = 0
    for span in _iter_text_spans(page):
        t = span.get("text", "")
        if re.sub(r"\s+", "", t) != target:
            continue
        r = _span_rect(span)
        if r.y0 < threshold_y:
            continue
        if r.width > max_number_width_pt:
            continue
        pad = 2.0
        rr = fitz.Rect(
            r.x0 - pad,
            r.y0 - pad,
            r.x1 + pad,
            r.y1 + pad,
        )
        page.add_redact_annot(rr, fill=(1, 1, 1))
        count += 1
    return count


def _redact_footer_image_strip(page: fitz.Page, footer_strip_pt: float) -> None:
    r = page.rect
    strip = fitz.Rect(r.x0, r.y1 - footer_strip_pt, r.x1, r.y1)
    page.add_redact_annot(strip, fill=(1, 1, 1))


def _insert_footer_number(
    page: fitz.Page,
    label: str,
    *,
    footer_strip_pt: float,
    fontsize: float,
) -> None:
    r = page.rect
    foot = fitz.Rect(
        r.x0,
        r.y1 - footer_strip_pt + 2,
        r.x1,
        r.y1 - 4,
    )
    page.insert_textbox(
        foot,
        label,
        fontsize=fontsize,
        fontname="helv",
        color=(0, 0, 0),
        align=fitz.TEXT_ALIGN_CENTER,
    )


def process_pdf(
    src: Path,
    dst: Path,
    *,
    page_number_start: int = 1,
    label_prefix: str = "",
    footer_strip_pt: float = 52.0,
    footer_window_pt: float = 200.0,
    max_number_width_pt: float = 72.0,
    footer_fontsize: float = 11.0,
    max_pages: int | None = None,
) -> None:
    doc = fitz.open(src)
    end = len(doc) if max_pages is None else min(len(doc), max_pages)

    for i in range(end):
        page = doc[i]
        page_no = page_number_start + i
        label = f"{label_prefix}{page_no}" if label_prefix else str(page_no)

        _redact_duplicate_page_numbers(
            page,
            page_no,
            footer_window_pt=footer_window_pt,
            max_number_width_pt=max_number_width_pt,
        )
        _redact_footer_image_strip(page, footer_strip_pt)

        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_PIXELS)
        _insert_footer_number(
            page,
            label,
            footer_strip_pt=footer_strip_pt,
            fontsize=footer_fontsize,
        )

    doc.save(dst, garbage=4, deflate=True, incremental=False)
    doc.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="OCR-PDF: doppelte Seitenzahl entfernen, eine Fußzeilen-Zahl setzen."
    )
    ap.add_argument("src", type=Path)
    ap.add_argument("-o", "--output", type=Path, help="Ziel-PDF")
    ap.add_argument("--start-at", type=int, default=1, help="Erste Seitenzahl (Standard: 1)")
    ap.add_argument("--prefix", default="", help="Vor der Zahl, z.B. 'Seite '")
    ap.add_argument(
        "--footer-strip-pt",
        type=float,
        default=52.0,
        help="Höhe des unteren Bildstreifens zum Überdecken des Scans (Standard: 52)",
    )
    ap.add_argument(
        "--footer-window-pt",
        type=float,
        default=200.0,
        help="Ab unterem Rand: OCR-Text mit Seitennummer hier entfernen (Standard: 200)",
    )
    ap.add_argument(
        "--max-number-width-pt",
        type=float,
        default=72.0,
        help="Max. Breite einer Zahlenspanne, sonst ignorieren (Schutz vor Texttreffern)",
    )
    ap.add_argument("--max-pages", type=int, default=None)
    args = ap.parse_args()

    src = args.src.expanduser().resolve()
    if not src.is_file():
        print(f"Datei nicht gefunden: {src}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        dst = args.output.expanduser().resolve()
    else:
        dst = src.parent / f"{src.stem} - einheitliche Seitenzahl.pdf"

    process_pdf(
        src,
        dst,
        page_number_start=args.start_at,
        label_prefix=args.prefix,
        footer_strip_pt=args.footer_strip_pt,
        footer_window_pt=args.footer_window_pt,
        max_number_width_pt=args.max_number_width_pt,
        max_pages=args.max_pages,
    )

    print(f"Geschrieben: {dst}")


if __name__ == "__main__":
    main()
