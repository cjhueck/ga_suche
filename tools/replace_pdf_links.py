"""
replace_pdf_links.py

Ersetzt publish.obsidian.md-Links in einem Coggle-PDF durch Links zur
Online-App (rudolf-steiner-online.de/coggle-link.html#maps&scroll=...).

Voraussetzungen:
    pip install pikepdf

Verwendung:
    # Standard: Rhythmisches_System_neu.pdf -> Rhythmisches_System_neu_online.pdf
    python tools/replace_pdf_links.py

    # Beliebige PDF-Datei angeben:
    python tools/replace_pdf_links.py pfad/zur/datei.pdf

    # Ausgabepfad explizit angeben:
    python tools/replace_pdf_links.py pfad/zur/datei.pdf --out pfad/ausgabe.pdf

    # Andere Basis-URL (z.B. lokal testen):
    python tools/replace_pdf_links.py --base-url http://localhost:3003

    # Vorschau ohne Schreiben:
    python tools/replace_pdf_links.py --dry-run
"""

import sys
import os
import argparse
from urllib.parse import unquote_plus, quote

try:
    import pikepdf
except ImportError:
    print("FEHLER: pikepdf nicht installiert. Bitte: pip install pikepdf")
    sys.exit(1)

# ── Konfiguration ──────────────────────────────────────────────────────────────

DEFAULT_BASE_URL = "https://rudolf-steiner-online.de"

# Standard-PDF-Pfad (wie in backend.js konfiguriert)
DEFAULT_PDF_PATH = os.path.join(
    os.path.dirname(__file__), "..", "maps-pdf", "Rhythmisches_System_neu.pdf"
)

OBSIDIAN_PUBLISH_HOST = "publish.obsidian.md"

# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

def build_app_url(fragment_raw: str, base_url: str) -> str:
    """
    Wandelt ein Obsidian-Publish-URL-Fragment in eine coggle-link.html-URL um.

    Beispiel:
        fragment_raw = "3+Atmungssystem"
        -> "https://rudolf-steiner-online.de/coggle-link.html#maps&scroll=3%20Atmungssystem"
    """
    # Obsidian Publish kodiert Leerzeichen als +, rest als %XX
    heading = unquote_plus(fragment_raw)
    # Fuer scroll= Parameter: quote() kodiert Sonderzeichen, Leerzeichen als %20
    scroll_param = quote(heading, safe="")
    return f"{base_url.rstrip('/')}/coggle-link.html#maps&scroll={scroll_param}"


def replace_links_in_pdf(input_path: str, output_path: str, base_url: str,
                          dry_run: bool = False) -> dict:
    """
    Oeffnet das PDF, ersetzt alle publish.obsidian.md-Links und speichert die
    modifizierte Version unter output_path.

    Gibt ein Dict mit Statistiken zurueck.
    """
    stats = {"total": 0, "replaced": 0, "skipped": 0, "pages": 0}

    pdf = pikepdf.open(input_path)
    stats["pages"] = len(pdf.pages)

    for page_num, page in enumerate(pdf.pages, start=1):
        annots = page.get("/Annots", [])
        for ann in annots:
            if str(ann.get("/Subtype", "")) != "/Link":
                continue
            a = ann.get("/A", None)
            if a is None:
                continue
            uri_obj = a.get("/URI", None)
            if uri_obj is None:
                continue

            url = str(uri_obj)
            stats["total"] += 1

            if OBSIDIAN_PUBLISH_HOST not in url:
                stats["skipped"] += 1
                continue

            # Fragment extrahieren
            hash_idx = url.find("#")
            if hash_idx < 0:
                print(f"  [S.{page_num}] Kein Fragment: {url[:80]}")
                stats["skipped"] += 1
                continue

            fragment = url[hash_idx + 1:]
            new_url = build_app_url(fragment, base_url)

            heading_preview = unquote_plus(fragment)[:60]
            print(f"  [S.{page_num}] {heading_preview!r}")
            print(f"           -> {new_url}")

            if not dry_run:
                a["/URI"] = pikepdf.String(new_url)

            stats["replaced"] += 1

    if not dry_run:
        pdf.save(output_path)
        print(f"\nGespeichert: {output_path}")
    else:
        print("\n[Dry-run: keine Datei geschrieben]")

    pdf.close()
    return stats


# ── Hauptprogramm ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Ersetzt publish.obsidian.md-Links in einem PDF durch App-Links."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=DEFAULT_PDF_PATH,
        help="Eingabe-PDF (Standard: maps-pdf/Rhythmisches_System_neu.pdf)"
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Ausgabe-PDF (Standard: <input>_online.pdf)"
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Basis-URL der App (Standard: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur anzeigen, nicht schreiben"
    )
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    if not os.path.isfile(input_path):
        print(f"FEHLER: Datei nicht gefunden: {input_path}")
        sys.exit(1)

    if args.out:
        output_path = os.path.abspath(args.out)
    else:
        base, ext = os.path.splitext(input_path)
        output_path = base + "_online" + ext

    print(f"Eingabe:   {input_path}")
    print(f"Ausgabe:   {output_path}")
    print(f"Basis-URL: {args.base_url}")
    if args.dry_run:
        print("Modus:     Dry-run (kein Schreiben)")
    print()

    stats = replace_links_in_pdf(input_path, output_path, args.base_url, args.dry_run)

    print()
    print("-- Zusammenfassung ------------------------------------------")
    print(f"  Seiten:        {stats['pages']}")
    print(f"  Links gesamt:  {stats['total']}")
    print(f"  Ersetzt:       {stats['replaced']}")
    print(f"  Uebersprungen: {stats['skipped']} (keine publish.obsidian.md-Links)")


if __name__ == "__main__":
    main()
