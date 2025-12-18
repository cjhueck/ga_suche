#!/usr/bin/env python3
"""
Batch-Verarbeitung aller GA-Bände mit Suffix (z.B. GA068a, GA069a, etc.)
"""
import subprocess
import sys
import re
from pathlib import Path

PDF_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf")
SCRIPT_DIR = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche")

def find_suffix_gas():
    """Findet alle GA-Bände mit Suffix in den PDFs"""
    suffix_gas = []
    pattern = re.compile(r"GA\s*(\d{3}[a-z])", re.IGNORECASE)
    
    for pdf in PDF_DIR.glob("*.pdf"):
        match = pattern.search(pdf.name)
        if match:
            ga_num = match.group(1).upper()
            ga_id = f"GA{ga_num}"
            if ga_id not in suffix_gas:
                suffix_gas.append(ga_id)
    
    return sorted(suffix_gas)

def run_command(cmd, description):
    """Führt einen Befehl aus und zeigt das Ergebnis"""
    print(f"  {description}...")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=SCRIPT_DIR, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        print(f"    FEHLER: {result.stderr[:200]}")
        return False
    return True

def process_ga(ga_id):
    """Verarbeitet einen einzelnen GA-Band"""
    print(f"\n{'='*60}")
    print(f"Verarbeite: {ga_id}")
    print('='*60)
    
    # 1. Seitenzahlen extrahieren
    if not run_command(
        [sys.executable, "export_page_markers_v4.py", ga_id],
        "Extrahiere Seitenzahlen"
    ):
        return False
    
    # 2. Lecture-Page-Mapping generieren (für Vorträge)
    run_command(
        [sys.executable, "generate_lecture_page_mapping.py", ga_id],
        "Generiere Lecture-Mapping"
    )
    
    # 3. Seitenzahlen anwenden
    if not run_command(
        [sys.executable, "apply_page_break_markers_v4.py", ga_id],
        "Wende Seitenzahlen an"
    ):
        return False
    
    # 4. Nach pagebreak-books kopieren
    src = SCRIPT_DIR / f"{ga_id}-with-pagebreaks.json"
    dst = SCRIPT_DIR / "pagebreak-books" / f"{ga_id}.json"
    if src.exists():
        import shutil
        shutil.copy(src, dst)
        print(f"  Kopiert nach {dst.name}")
    
    # 5. Bibliographie aktualisieren
    run_command(
        [sys.executable, "tools/update_pagebreak_bib.py", ga_id],
        "Aktualisiere Bibliographie"
    )
    
    return True

def main():
    suffix_gas = find_suffix_gas()
    print(f"Gefunden: {len(suffix_gas)} GA-Bände mit Suffix")
    print(", ".join(suffix_gas))
    
    # Nur bestimmte GAs verarbeiten wenn angegeben
    if len(sys.argv) > 1:
        suffix_gas = [ga.upper() if ga.startswith('GA') else f'GA{ga.upper()}' for ga in sys.argv[1:]]
        print(f"\nVerarbeite nur: {suffix_gas}")
    
    success = 0
    failed = []
    
    for ga_id in suffix_gas:
        try:
            if process_ga(ga_id):
                success += 1
            else:
                failed.append(ga_id)
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            failed.append(ga_id)
    
    print(f"\n{'='*60}")
    print(f"FERTIG: {success}/{len(suffix_gas)} erfolgreich")
    if failed:
        print(f"Fehlgeschlagen: {', '.join(failed)}")
    
    print("\nBitte Server neu laden: Invoke-RestMethod -Uri 'http://localhost:3003/api/reload-books' -Method POST")

if __name__ == "__main__":
    main()
