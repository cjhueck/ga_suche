#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR-Script für Steiner GA PDFs

Macht gescannte PDFs mit OCR lesbar, sodass Text durchsuchbar wird.

INSTALLATION (Windows):
1. Tesseract installieren:
   - Download: https://github.com/UB-Mannheim/tesseract/wiki
   - Bei Installation: "German" Sprachpaket auswählen
   - Nach Installation: Tesseract zum PATH hinzufügen oder Pfad unten anpassen

2. Python-Pakete installieren:
   pip install ocrmypdf

VERWENDUNG:
   python ocr_pdfs.py              # Alle konfigurierten Bände
   python ocr_pdfs.py GA068c       # Nur ein Band
   python ocr_pdfs.py --list       # Zeige alle verfügbaren PDFs
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional
import shutil

# Konfiguration
SCRIPT_DIR = Path(__file__).parent
PDF_DIR = SCRIPT_DIR / "Steiner_GA_pdf"
OUTPUT_DIR = SCRIPT_DIR / "Steiner_GA_pdf_ocr"  # OCR-Versionen werden hier gespeichert

# Tesseract-Pfad (anpassen falls nötig)
# Standard-Installationspfad unter Windows:
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Bände die OCR benötigen
OCR_BANDS = [
    "GA 68c",
    "GA 68d", 
    "GA 69c",
    "GA 69d",
    "GA 70b",
    "GA 80a",
    "GA 80b",
    "GA 80c",
]


def check_dependencies() -> bool:
    """Prüft ob alle nötigen Tools installiert sind."""
    errors = []
    
    # Prüfe ocrmypdf
    try:
        result = subprocess.run(
            ["ocrmypdf", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            errors.append("ocrmypdf nicht gefunden")
    except FileNotFoundError:
        errors.append("ocrmypdf nicht gefunden. Installation: pip install ocrmypdf")
    
    # Prüfe Tesseract
    tesseract_cmd = "tesseract"
    if os.path.exists(TESSERACT_PATH):
        tesseract_cmd = TESSERACT_PATH
    
    try:
        result = subprocess.run(
            [tesseract_cmd, "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            errors.append("Tesseract nicht gefunden")
    except FileNotFoundError:
        errors.append(f"""
Tesseract nicht gefunden!

Installation für Windows:
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Installer ausführen
3. Bei Installation: "German" Sprachpaket auswählen
4. Nach Installation entweder:
   a) Tesseract zum System-PATH hinzufügen, ODER
   b) TESSERACT_PATH in diesem Script anpassen

Aktuell gesuchter Pfad: {TESSERACT_PATH}
""")
    
    if errors:
        print("=" * 60)
        print("FEHLER: Abhängigkeiten fehlen!")
        print("=" * 60)
        for e in errors:
            print(f"\n{e}")
        print()
        return False
    
    return True


def find_pdfs(band_filter: Optional[str] = None) -> List[Path]:
    """Findet alle relevanten PDFs."""
    if not PDF_DIR.exists():
        print(f"FEHLER: PDF-Verzeichnis nicht gefunden: {PDF_DIR}")
        return []
    
    pdfs = []
    for pdf_file in PDF_DIR.glob("*.pdf"):
        name = pdf_file.name
        
        # Prüfe ob PDF zu einem OCR-Band gehört
        for band in OCR_BANDS:
            if name.startswith(band):
                # Filter anwenden falls angegeben
                if band_filter:
                    # Normalisiere: "GA068c" -> "GA 68c"
                    normalized = band_filter.upper()
                    if not normalized.startswith("GA "):
                        normalized = normalized.replace("GA", "GA ")
                    # Entferne führende Null: "GA 068c" -> "GA 68c"
                    normalized = normalized.replace("GA 0", "GA ")
                    
                    if band.upper() != normalized.upper():
                        continue
                
                pdfs.append(pdf_file)
                break
    
    return sorted(pdfs)


def ocr_pdf(input_path: Path, output_path: Path, language: str = "deu") -> bool:
    """
    Führt OCR auf einer PDF durch.
    
    Args:
        input_path: Eingabe-PDF
        output_path: Ausgabe-PDF mit OCR-Text
        language: Tesseract-Sprachcode (deu = Deutsch)
    
    Returns:
        True bei Erfolg
    """
    print(f"  Verarbeite: {input_path.name}")
    
    # Erstelle Output-Verzeichnis falls nötig
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # ocrmypdf Aufruf
    cmd = [
        "ocrmypdf",
        "--language", language,
        "--deskew",                    # Schieflage korrigieren
        "--clean",                     # Bild-Rauschen entfernen
        "--optimize", "1",             # Leichte Optimierung
        "--skip-text",                 # Überspringe Seiten die bereits Text haben
        "--jobs", "4",                 # Parallele Verarbeitung
        str(input_path),
        str(output_path)
    ]
    
    # Tesseract-Pfad setzen falls nötig
    env = os.environ.copy()
    if os.path.exists(TESSERACT_PATH):
        tesseract_dir = str(Path(TESSERACT_PATH).parent)
        env["PATH"] = tesseract_dir + os.pathsep + env.get("PATH", "")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env
        )
        
        if result.returncode == 0:
            print(f"    ✓ Erfolgreich: {output_path.name}")
            return True
        elif result.returncode == 6:
            # Returncode 6 = PDF hat bereits Text (bei --skip-text)
            print(f"    ⊘ Übersprungen (hat bereits Text): {output_path.name}")
            # Kopiere Original falls noch nicht vorhanden
            if not output_path.exists():
                shutil.copy2(input_path, output_path)
            return True
        else:
            print(f"    ✗ Fehler: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"    ✗ Ausnahme: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="OCR für Steiner GA PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "band",
        nargs="?",
        help="Bestimmter Band (z.B. GA068c, GA80a) oder leer für alle"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Zeige alle verfügbaren PDFs"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Ausgabe-Verzeichnis (Standard: {OUTPUT_DIR})"
    )
    parser.add_argument(
        "--language",
        default="deu",
        help="OCR-Sprache (Standard: deu für Deutsch)"
    )
    
    args = parser.parse_args()
    
    # Finde PDFs
    pdfs = find_pdfs(args.band)
    
    if args.list:
        print(f"\nVerfügbare PDFs für OCR ({len(pdfs)} Dateien):\n")
        current_band = None
        for pdf in pdfs:
            # Extrahiere Band-Name
            band = " ".join(pdf.name.split()[:2])
            if band != current_band:
                if current_band:
                    print()
                print(f"=== {band} ===")
                current_band = band
            print(f"  {pdf.name}")
        return
    
    if not pdfs:
        if args.band:
            print(f"Keine PDFs gefunden für Band: {args.band}")
        else:
            print("Keine PDFs gefunden!")
        print(f"\nKonfigurierte Bände: {', '.join(OCR_BANDS)}")
        print(f"PDF-Verzeichnis: {PDF_DIR}")
        return
    
    # Prüfe Abhängigkeiten
    if not check_dependencies():
        return
    
    print("=" * 60)
    print("  OCR für Steiner GA PDFs")
    print("=" * 60)
    print(f"\nEingabe-Verzeichnis: {PDF_DIR}")
    print(f"Ausgabe-Verzeichnis: {args.output}")
    print(f"Sprache: {args.language}")
    print(f"Zu verarbeiten: {len(pdfs)} PDFs\n")
    
    # Verarbeite PDFs
    success = 0
    failed = 0
    
    for pdf in pdfs:
        output_path = args.output / pdf.name
        
        if ocr_pdf(pdf, output_path, args.language):
            success += 1
        else:
            failed += 1
    
    print()
    print("=" * 60)
    print(f"  FERTIG: {success} erfolgreich, {failed} fehlgeschlagen")
    print("=" * 60)
    print(f"\nOCR-PDFs gespeichert in: {args.output}")


if __name__ == "__main__":
    main()


