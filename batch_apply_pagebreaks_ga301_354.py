#!/usr/bin/env python3
"""
Batch-Anwendung von Pagebreak-Markern für GA301 bis GA354 (inkl. Suffixe)
"""

import io
import subprocess
import sys
from pathlib import Path

# Windows-Konsole UTF-8 Unterstützung
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent
PAGEBREAK_DIR = SCRIPT_DIR / "pagebreak-books"

def main():
    # GA301 bis GA354
    start_ga = 301
    end_ga = 354
    
    # Bekannte Suffixe für diesen Bereich
    suffixes = ['', 'A', 'B', 'C']
    
    print(f"{'='*60}")
    print(f"Batch-Anwendung Pagebreak-Marker: GA{start_ga:03d} bis GA{end_ga:03d}")
    print(f"(inkl. Suffixe A, B, C)")
    print(f"{'='*60}\n")
    
    # Pagebreak-Ordner erstellen
    PAGEBREAK_DIR.mkdir(exist_ok=True)
    
    # Erstelle Liste aller GA-Nummern mit Suffixen
    ga_numbers = []
    for i in range(start_ga, end_ga + 1):
        for suffix in suffixes:
            ga_numbers.append(f"GA{i:03d}{suffix}")
    
    total_processed = 0
    total_failed = 0
    total_skipped = 0
    total_no_data = 0
    
    for ga_number in ga_numbers:
        out_file = PAGEBREAK_DIR / f"{ga_number}.json"
        report_file = PAGEBREAK_DIR / f"{ga_number}-report.json"
        
        # Prüfe ob bereits verarbeitet
        if out_file.exists():
            print(f"  OK  {ga_number}: Bereits verarbeitet (uebersprungen)")
            total_skipped += 1
            continue
        
        print(f"\n{'='*60}")
        print(f"Verarbeite {ga_number}...")
        print(f"{'='*60}")
        
        # Rufe apply_page_break_markers_v4.py auf
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "apply_page_break_markers_v4.py"),
            ga_number,
            "--out", str(out_file),
            "--report", str(report_file)
        ]
        
        result = subprocess.run(
            cmd,
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True
        )
        
        # Prüfe Output auf "keine Daten"
        output = result.stdout + result.stderr
        if "keine Seitenumbruch-Marker" in output.lower() or "not found" in output.lower() or "keine Daten" in output.lower():
            total_no_data += 1
            print(f"  SKIP  {ga_number}: Keine Pagebreak-Daten vorhanden")
        elif result.returncode == 0:
            total_processed += 1
            print(f"  OK  {ga_number} erfolgreich verarbeitet")
        else:
            total_failed += 1
            print(f"  FEHLER  {ga_number} fehlgeschlagen")
            if result.stderr:
                print(f"    Fehler: {result.stderr[:200]}")
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    print(f"  Erfolgreich:     {total_processed}")
    print(f"  Bereits fertig:  {total_skipped}")
    print(f"  Keine Daten:     {total_no_data}")
    print(f"  Fehlgeschlagen:  {total_failed}")
    print(f"  Gesamt geprueft: {len(ga_numbers)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()


