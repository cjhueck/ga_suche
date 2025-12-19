#!/usr/bin/env python3
"""
Batch-Generierung von Seitenzahlen für Vortragsbände GA052-150

Führt für jeden Band zwei Schritte aus:
1. export_page_markers_v4.py - extrahiert Page-Break-Marker aus PDF
2. apply_page_break_markers_v4.py - wendet Marker auf Vorträge an

Verwendung:
  python batch_generate_pagebreaks.py
  python batch_generate_pagebreaks.py 52 100   # nur GA052-100
  python batch_generate_pagebreaks.py --check  # nur prüfen welche PDFs existieren
"""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

# Windows-Konsole UTF-8 Unterstützung
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent
PDF_DIR = SCRIPT_DIR / "Steiner_GA_pdf"
PAGEBREAK_DIR = SCRIPT_DIR / "pagebreak-books"


def find_pdf_for_ga(ga_num: int) -> Path | None:
    """Findet die PDF-Datei für eine GA-Nummer."""
    ga_str = str(ga_num).zfill(3)
    ga_str_short = str(ga_num)
    
    for pdf_file in PDF_DIR.glob("*.pdf"):
        name_lower = pdf_file.name.lower()
        # Verschiedene Muster prüfen
        if f"ga {ga_str}" in name_lower or f"ga{ga_str}" in name_lower:
            return pdf_file
        if f"ga {ga_str_short}," in name_lower or f"ga {ga_str_short} " in name_lower:
            return pdf_file
        if f"ga {ga_str_short}-" in name_lower:
            return pdf_file
    return None


def check_existing_pagebreak(ga_num: int) -> bool:
    """Prüft ob bereits eine Pagebreak-Datei existiert."""
    ga_str = f"GA{str(ga_num).zfill(3)}"
    return (PAGEBREAK_DIR / f"{ga_str}.json").exists()


def process_ga(ga_num: int, dry_run: bool = False) -> bool:
    """Verarbeitet einen GA-Band."""
    ga_str = f"GA{str(ga_num).zfill(3)}"
    
    # PDF prüfen
    pdf_path = find_pdf_for_ga(ga_num)
    if not pdf_path:
        print(f"  ⚠️  {ga_str}: Keine PDF gefunden")
        return False
    
    # Bereits verarbeitet?
    if check_existing_pagebreak(ga_num):
        print(f"  ✓  {ga_str}: Bereits verarbeitet (übersprungen)")
        return True
    
    if dry_run:
        print(f"  →  {ga_str}: PDF gefunden ({pdf_path.name})")
        return True
    
    print(f"\n{'='*60}")
    print(f"Verarbeite {ga_str}...")
    print(f"PDF: {pdf_path.name}")
    print(f"{'='*60}")
    
    # Schritt 1: Page-Break-Marker exportieren
    print(f"\n[1/2] Exportiere Page-Break-Marker...")
    result1 = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "export_page_markers_v4.py"), ga_str],
        cwd=str(SCRIPT_DIR),
        capture_output=False
    )
    
    if result1.returncode != 0:
        print(f"  ❌ Fehler beim Export der Marker für {ga_str}")
        return False
    
    # Schritt 2: Marker auf Vorträge anwenden
    print(f"\n[2/2] Wende Marker auf Vorträge an...")
    out_file = PAGEBREAK_DIR / f"{ga_str}.json"
    report_file = PAGEBREAK_DIR / f"{ga_str}-report.json"
    
    result2 = subprocess.run(
        [
            sys.executable, 
            str(SCRIPT_DIR / "apply_page_break_markers_v4.py"), 
            ga_str,
            "--out", str(out_file),
            "--report", str(report_file)
        ],
        cwd=str(SCRIPT_DIR),
        capture_output=False
    )
    
    if result2.returncode != 0:
        print(f"  ❌ Fehler beim Anwenden der Marker für {ga_str}")
        return False
    
    print(f"  ✓  {ga_str} erfolgreich verarbeitet!")
    return True


def main():
    # Parameter parsen
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--check" in sys.argv
    
    # GA-Bereich bestimmen
    if len(args) >= 2:
        start_ga = int(args[0])
        end_ga = int(args[1])
    elif len(args) == 1:
        start_ga = int(args[0])
        end_ga = int(args[0])
    else:
        start_ga = 52
        end_ga = 150
    
    print(f"{'='*60}")
    print(f"Batch-Generierung Seitenzahlen: GA{start_ga:03d} bis GA{end_ga:03d}")
    if dry_run:
        print("(Nur Prüfung - keine Verarbeitung)")
    print(f"{'='*60}\n")
    
    # Pagebreak-Ordner erstellen falls nötig
    PAGEBREAK_DIR.mkdir(exist_ok=True)
    
    # Statistik
    processed = 0
    skipped = 0
    failed = 0
    no_pdf = 0
    
    for ga_num in range(start_ga, end_ga + 1):
        ga_str = f"GA{ga_num:03d}"
        
        # Prüfen
        pdf_exists = find_pdf_for_ga(ga_num) is not None
        already_done = check_existing_pagebreak(ga_num)
        
        if not pdf_exists:
            no_pdf += 1
            if not dry_run:
                print(f"  ⚠️  {ga_str}: Keine PDF")
            continue
        
        if already_done:
            skipped += 1
            if dry_run:
                print(f"  ✓  {ga_str}: Bereits verarbeitet")
            continue
        
        if dry_run:
            print(f"  →  {ga_str}: Bereit zur Verarbeitung")
            processed += 1
        else:
            if process_ga(ga_num, dry_run=False):
                processed += 1
            else:
                failed += 1
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    print(f"  Verarbeitet:     {processed}")
    print(f"  Bereits fertig:  {skipped}")
    print(f"  Keine PDF:       {no_pdf}")
    print(f"  Fehlgeschlagen:  {failed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()










