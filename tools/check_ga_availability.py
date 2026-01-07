#!/usr/bin/env python3
"""Prüft PDF- und Vortragsverfügbarkeit für GA-Bände."""
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent
PDF_DIR = SCRIPT_DIR / "Steiner_GA_pdf"

def check_ga_range(start: int, end: int):
    for ga in range(start, end + 1):
        ga_str = f"GA{str(ga).zfill(3)}"
        
        # PDF prüfen
        pdf_found = False
        for pdf in PDF_DIR.glob("*.pdf"):
            name_lower = pdf.name.lower()
            ga_num_str = str(ga).zfill(3)
            if f"ga {ga_num_str}" in name_lower or f"ga{ga_num_str}" in name_lower or f"ga {ga}," in name_lower:
                pdf_found = True
                break
        
        # JSON prüfen
        lectures_found = False
        for json_file in SCRIPT_DIR.glob("steiner-full-lectures-*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for lec in data.get("lectures", []):
                    if (lec.get("gaNumber") or "").upper() == ga_str:
                        lectures_found = True
                        break
            except:
                pass
            if lectures_found:
                break
        
        status = []
        if not pdf_found:
            status.append("Kein PDF")
        if not lectures_found:
            status.append("Keine Vortraege")
        
        if status:
            print(f"{ga_str}: {', '.join(status)}")
        else:
            print(f"{ga_str}: OK")

if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 61
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 70
    check_ga_range(start, end)

