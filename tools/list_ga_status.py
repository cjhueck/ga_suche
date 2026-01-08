#!/usr/bin/env python3
"""Liste aller verarbeiteten und fehlenden GAs"""

import json
from pathlib import Path
import re

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent

def main():
    books_dir = ROOT_DIR / "steiner-books"
    lectures_dir = ROOT_DIR / "steiner-full-lectures"
    pagebreaks_dir = ROOT_DIR / "pagebreaks"
    
    all_gas = set()
    
    # Bücher laden
    for f in books_dir.glob("steiner-books-*.json"):
        try:
            data = json.load(open(f, encoding="utf-8"))
            for book in data.get("books", []):
                ga = book.get("gaNumber", "").upper()
                if ga:
                    all_gas.add(ga)
        except:
            pass
    
    # Vorträge laden
    for f in lectures_dir.glob("steiner-full-lectures-*.json"):
        try:
            data = json.load(open(f, encoding="utf-8"))
            for lecture in data.get("lectures", []):
                ga = lecture.get("gaNumber", "").upper()
                if ga:
                    all_gas.add(ga)
        except:
            pass
    
    # Report-Dateien (verarbeitete GAs)
    processed_gas = set()
    for f in pagebreaks_dir.glob("*-report.json"):
        ga = f.stem.replace("-report", "").upper()
        processed_gas.add(ga)
    
    # Auch .json Dateien ohne -report prüfen
    for f in pagebreaks_dir.glob("GA*.json"):
        if "-report" not in f.name and ".old" not in f.name:
            ga = f.stem.upper()
            processed_gas.add(ga)
    
    def sort_key(ga):
        m = re.match(r"GA(\d+)([A-Z]?)", ga)
        if m:
            return (int(m.group(1)), m.group(2) or "")
        return (9999, ga)
    
    # Haupt-GA-Nummern extrahieren
    main_gas = set()
    for ga in all_gas:
        m = re.match(r"GA(\d+)", ga)
        if m:
            main_gas.add(int(m.group(1)))
    
    main_processed = set()
    for ga in processed_gas:
        m = re.match(r"GA(\d+)", ga)
        if m:
            main_processed.add(int(m.group(1)))
    
    print("=" * 70)
    print("ÜBERSICHT GA-SEITENZAHLEN")
    print("=" * 70)
    print(f"Gesamt GAs in Datenbank: {len(all_gas)}")
    print(f"Davon mit Report/Verarbeitung: {len(processed_gas)}")
    print(f"Haupt-GA-Nummern in Datenbank: {len(main_gas)}")
    print(f"Davon verarbeitet: {len(main_processed)}")
    print()
    
    # Fehlende Haupt-GAs
    missing_main = sorted(main_gas - main_processed)
    if missing_main:
        print("=" * 70)
        print("FEHLENDE HAUPT-GAs (keine Seitenzahlen)")
        print("=" * 70)
        for n in missing_main:
            print(f"  GA{n:03d}")
        print()
    else:
        print("[OK] Alle Haupt-GAs wurden verarbeitet!")
        print()
    
    # Verarbeitete GAs als kompakte Ranges
    print("=" * 70)
    print("VERARBEITETE GAs")
    print("=" * 70)
    
    ranges = []
    start = None
    prev = None
    for n in sorted(main_processed):
        if start is None:
            start = n
            prev = n
        elif n == prev + 1:
            prev = n
        else:
            if start == prev:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{prev}")
            start = n
            prev = n
    
    if start is not None:
        if start == prev:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{prev}")
    
    print(f"GA: {', '.join(ranges)}")
    print()
    
    # Detaillierte Liste mit Suffixen
    print("=" * 70)
    print("ALLE VERARBEITETEN GAs (inkl. Suffixe)")
    print("=" * 70)
    processed_sorted = sorted(processed_gas, key=sort_key)
    for i in range(0, len(processed_sorted), 12):
        print("  " + ", ".join(processed_sorted[i:i+12]))
    print()
    print(f"Gesamt: {len(processed_sorted)} Einträge")

if __name__ == "__main__":
    main()

