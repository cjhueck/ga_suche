"""
Erzeugt aus einem bildbasierten GA-PDF eine Lesefassung:
pro Seite nur der Haupt-Bildinhalt (größtes Bild), ohne kleine Logos,
unten zentriert die Seitenzahl.

Voraussetzung: PyMuPDF (import fitz).

Beispiel:
  python tools/pdf_content_only_with_page_footer.py ^
    "Steiner_GA/.../Quelle.pdf" -o "Steiner_GA/.../Quelle - Lesefassung.pdf"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz


def _largest_image_block(blocks: list) -> dict | None:
    best: dict | None = None
    best_area = 0.0
    for b in blocks:
        if b.get("type") != 1:
            continue
        x0, y0, x1, y1 = b["bbox"]
        area = (x1 - x0) * (y1 - y0)
        if area > best_area:
            best_area = area
            best = b
    return best


def _fit_image_rect(
    page_rect: fitz.Rect,
    img_w: int,
    img_h: int,
    *,
    top_margin: float,
    bottom_reserve: float,
    side_margin: float,
) -> fitz.Rect:
    """Berechnet ein Rechteck, in das das Bild proportional passt."""
    inner_w = page_rect.width - 2 * side_margin
    inner_h = page_rect.height - top_margin - bottom_reserve
    if inner_w <= 0 or inner_h <= 0:
        raise ValueError("Margins zu groß für die Seitengröße.")
    scale = min(inner_w / img_w, inner_h / img_h)
    disp_w = img_w * scale
    disp_h = img_h * scale
    x0 = page_rect.x0 + side_margin + (inner_w - disp_w) / 2
    y0 = page_rect.y0 + top_margin + (inner_h - disp_h) / 2
    return fitz.Rect(x0, y0, x0 + disp_w, y0 + disp_h)


def build_reader_pdf(
    src_path: Path,
    dst_path: Path,
    *,
    page_number_start: int = 1,
    label_prefix: str = "",
    top_margin: float = 28.0,
    bottom_reserve: float = 44.0,
    side_margin: float = 24.0,
    footer_fontsize: float = 11.0,
    max_pages: int | None = None,
) -> None:
    src = fitz.open(src_path)
    out = fitz.open()
    n = len(src)
    end = n if max_pages is None else min(n, max_pages)

    for i in range(end):
        sp = src[i]
        d = sp.get_text("dict")
        blocks = d.get("blocks", [])
        main = _largest_image_block(blocks)
        dp = out.new_page(width=sp.rect.width, height=sp.rect.height)
        page_no = page_number_start + i

        if main is None or "image" not in main:
            note = f"[Kein Bild auf Seite {page_no}]"
            dp.insert_text(
                (side_margin, top_margin + 20),
                note,
                fontsize=12,
                color=(0.5, 0.5, 0.5),
            )
        else:
            iw = int(main["width"])
            ih = int(main["height"])
            rect = _fit_image_rect(
                dp.rect,
                iw,
                ih,
                top_margin=top_margin,
                bottom_reserve=bottom_reserve,
                side_margin=side_margin,
            )
            dp.insert_image(
                rect,
                stream=main["image"],
                keep_proportion=True,
                alpha=0,
            )

        label = f"{label_prefix}{page_no}" if label_prefix else str(page_no)
        foot = fitz.Rect(
            dp.rect.x0,
            dp.rect.y1 - bottom_reserve + 4,
            dp.rect.x1,
            dp.rect.y1 - 4,
        )
        dp.insert_textbox(
            foot,
            label,
            fontsize=footer_fontsize,
            fontname="helv",
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_CENTER,
        )

    out.save(dst_path, garbage=4, deflate=True)
    out.close()
    src.close()


def main() -> None:
    p = argparse.ArgumentParser(description="PDF: nur Hauptbild + Seitenzahl unten.")
    p.add_argument("src", type=Path, help="Quell-PDF")
    p.add_argument("-o", "--output", type=Path, help="Ziel-PDF (Standard: ... - Lesefassung.pdf)")
    p.add_argument("--start-at", type=int, default=1, help="Erste gedruckte Seitenzahl (Standard: 1)")
    p.add_argument("--prefix", default="", help="Optional vor der Zahl, z.B. 'S. '")
    p.add_argument("--max-pages", type=int, default=None, help="Nur erste N Seiten (Test)")
    args = p.parse_args()

    src = args.src.expanduser().resolve()
    if not src.is_file():
        print(f"Datei nicht gefunden: {src}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        dst = args.output.expanduser().resolve()
    else:
        dst = src.parent / f"{src.stem} - Lesefassung.pdf"

    build_reader_pdf(
        src,
        dst,
        page_number_start=args.start_at,
        label_prefix=args.prefix,
        max_pages=args.max_pages,
    )
    print(f"Geschrieben: {dst}")


if __name__ == "__main__":
    main()
