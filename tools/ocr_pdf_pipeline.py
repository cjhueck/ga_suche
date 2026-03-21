"""
Kette: (optional) ocrmypdf → einheitliche Seitenzahl unten.

1) ocrmypdf: nur wenn im PATH verfügbar und --ocr gesetzt ist.
   Install: https://ocrmypdf.readthedocs.io/ (benötigt Tesseract-OCR)
2) pdf_ocr_single_page_footer.py: entfernt doppelte Seitenzahlen und setzt eine.

Beispiele:
  python tools/ocr_pdf_pipeline.py scan.pdf -o fertig.pdf --ocr
  python tools/ocr_pdf_pipeline.py bereits-ocr.pdf -o fertig.pdf
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _footer_script() -> Path:
    return Path(__file__).resolve().parent / "pdf_ocr_single_page_footer.py"


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Optional ocrmypdf, danach einheitliche Fußzeilen-Seitenzahl."
    )
    ap.add_argument("src", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument(
        "--ocr",
        action="store_true",
        help="Zuerst ocrmypdf ausführen (muss installiert sein)",
    )
    ap.add_argument(
        "--ocrmypdf-extra",
        default="",
        help="Zusätzliche Argumente für ocrmypdf als ein String, z.B. '-l deu+eng --deskew'",
    )
    ap.add_argument("--start-at", type=int, default=1)
    ap.add_argument("--prefix", default="")
    ap.add_argument("--footer-strip-pt", type=float, default=52.0)
    ap.add_argument("--footer-window-pt", type=float, default=200.0)
    args = ap.parse_args()

    src = args.src.expanduser().resolve()
    out = args.output.expanduser().resolve()
    if not src.is_file():
        print(f"Datei nicht gefunden: {src}", file=sys.stderr)
        sys.exit(1)

    work = src
    tmp_path: Path | None = None

    if args.ocr:
        exe = shutil.which("ocrmypdf")
        if not exe:
            print(
                "ocrmypdf nicht im PATH. Installation siehe "
                "https://ocrmypdf.readthedocs.io/en/latest/installation.html",
                file=sys.stderr,
            )
            sys.exit(1)
        fd, tmp_path_str = tempfile.mkstemp(suffix=".pdf")
        import os

        os.close(fd)
        tmp_path = Path(tmp_path_str)
        cmd = [exe]
        if args.ocrmypdf_extra.strip():
            import shlex

            cmd.extend(shlex.split(args.ocrmypdf_extra))
        cmd.extend([str(src), str(tmp_path)])
        print("Ausführen:", " ".join(cmd))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            if tmp_path.is_file():
                tmp_path.unlink(missing_ok=True)
            sys.exit(r.returncode)
        work = tmp_path

    cmd2 = [
        sys.executable,
        str(_footer_script()),
        str(work),
        "-o",
        str(out),
        "--start-at",
        str(args.start_at),
        "--footer-strip-pt",
        str(args.footer_strip_pt),
        "--footer-window-pt",
        str(args.footer_window_pt),
    ]
    if args.prefix:
        cmd2.extend(["--prefix", args.prefix])

    print("Ausführen:", " ".join(cmd2))
    r2 = subprocess.run(cmd2)
    if tmp_path and tmp_path.is_file():
        tmp_path.unlink(missing_ok=True)
    sys.exit(r2.returncode)


if __name__ == "__main__":
    main()
