#!/usr/bin/env python3
"""
Batch-Export von Pagebreak-Markern für GA251 bis GA300
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

def main():
    # GA251 bis GA300
    start_ga = 251
    end_ga = 300
    
    print(f"{'='*60}")
    print(f"Batch-Export Pagebreak-Marker: GA{start_ga:03d} bis GA{end_ga:03d}")
    print(f"{'='*60}\n")
    
    # Erstelle Liste aller GA-Nummern
    ga_numbers = [f"GA{i:03d}" for i in range(start_ga, end_ga + 1)]
    
    # Verarbeite in Gruppen von 10
    batch_size = 10
    total_processed = 0
    total_failed = 0
    
    for i in range(0, len(ga_numbers), batch_size):
        batch = ga_numbers[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(ga_numbers) + batch_size - 1) // batch_size
        
        print(f"\n{'='*60}")
        print(f"Batch {batch_num}/{total_batches}: {batch[0]} bis {batch[-1]}")
        print(f"{'='*60}\n")
        
        # Rufe export_page_markers_v4.py auf
        cmd = [sys.executable, str(SCRIPT_DIR / "export_page_markers_v4.py")] + batch
        
        result = subprocess.run(
            cmd,
            cwd=str(SCRIPT_DIR),
            capture_output=False
        )
        
        if result.returncode == 0:
            total_processed += len(batch)
            print(f"\nOK: Batch {batch_num} erfolgreich verarbeitet ({len(batch)} Bände)")
        else:
            total_failed += len(batch)
            print(f"\nFEHLER: Batch {batch_num} fehlgeschlagen")
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    print(f"  Erfolgreich:     {total_processed}")
    print(f"  Fehlgeschlagen:  {total_failed}")
    print(f"  Gesamt:          {len(ga_numbers)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()








