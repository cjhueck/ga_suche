#!/usr/bin/env python3
"""
Verarbeitet alle Bücher (GA001-028, GA045) mit apply_page_break_markers_v4.py

Die v4-Version ist speziell für Bücher mit Fußnoten konzipiert und
verwendet die (left/right)-Anker aus page-break-markers.json.

Verwendung:
  python process_books_v4.py           # Alle Bücher
  python process_books_v4.py GA001     # Einzelnes Buch
  python process_books_v4.py 1 10      # Bereich GA001-GA010
"""

import subprocess
import sys
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
V4_SCRIPT = SCRIPT_DIR / "tools" / "apply_page_break_markers_v4.py"
PAGEBREAKS_DIR = SCRIPT_DIR / "pagebreaks"

# Bücher: GA001-GA028 und GA045
BOOK_GAS = list(range(1, 29)) + [45]


def normalize_ga(ga_arg: str) -> str:
    """Normalisiert GA-Nummer."""
    m = re.search(r"(\d+)", ga_arg)
    if not m:
        return None
    return f"GA{m.group(1).zfill(3)}"


def process_book(ga_num: int) -> dict:
    """Verarbeitet ein Buch mit v4."""
    ga = f"GA{ga_num:03d}"
    out_file = PAGEBREAKS_DIR / f"{ga}.json"
    
    print(f"\n{'='*60}")
    print(f"Verarbeite {ga}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(V4_SCRIPT), ga, "--out", str(out_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            return {"ga": ga, "status": "success", "output": str(out_file)}
        else:
            return {"ga": ga, "status": "error", "error": result.stderr or "Unknown error"}
    
    except Exception as e:
        print(f"  FEHLER: {e}")
        return {"ga": ga, "status": "error", "error": str(e)}


def main():
    # Bestimme zu verarbeitende GAs
    gas_to_process = []
    
    if len(sys.argv) == 1:
        # Alle Bücher
        gas_to_process = BOOK_GAS
    else:
        # Einzelne GAs oder Bereich
        for arg in sys.argv[1:]:
            ga = normalize_ga(arg)
            if ga:
                num = int(re.search(r"\d+", ga).group())
                if num not in gas_to_process:
                    gas_to_process.append(num)
        
        # Prüfe auf Bereich (zwei Zahlen)
        if len(sys.argv) == 3:
            try:
                start = int(re.search(r"\d+", sys.argv[1]).group())
                end = int(re.search(r"\d+", sys.argv[2]).group())
                if start < end:
                    gas_to_process = [n for n in range(start, end + 1)]
            except:
                pass
    
    if not gas_to_process:
        print("Keine Bücher zu verarbeiten")
        return
    
    print(f"\n{'#'*60}")
    print(f"# BÜCHER VERARBEITEN (v4)")
    print(f"# GAs: {', '.join(f'GA{n:03d}' for n in gas_to_process)}")
    print(f"{'#'*60}")
    
    # Verarbeite alle
    results = []
    for ga_num in gas_to_process:
        result = process_book(ga_num)
        results.append(result)
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    
    success = [r for r in results if r["status"] == "success"]
    errors = [r for r in results if r["status"] == "error"]
    
    print(f"  Erfolgreich: {len(success)}")
    print(f"  Fehler: {len(errors)}")
    
    if errors:
        print(f"\n  Fehler bei:")
        for r in errors:
            print(f"    - {r['ga']}: {r.get('error', 'Unbekannt')}")
    
    if success:
        print(f"\n  Output-Dateien in: pagebreaks/")
        print(f"\n  WICHTIG: Server neu starten! (nb)")


if __name__ == "__main__":
    main()

