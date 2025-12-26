#!/usr/bin/env python3
"""
Batch-Verarbeitung von Seitenzahlen für mehrere GA-Bände.
Kombiniert Mapping und Pagebreak-Einfügung in einem Durchlauf.
Nutzt Multiprocessing für Parallelverarbeitung.

Verwendung:
  python batch_process_pagebreaks.py GA171 GA172 GA173
  python batch_process_pagebreaks.py GA171-GA200
  python batch_process_pagebreaks.py GA171-GA200 --exclude GA174A GA174B
"""

from __future__ import annotations

import io
import json
import re
import sys
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple

# Windows-Konsole UTF-8 Unterstützung
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent


def normalize_ga(ga_arg: str) -> Optional[str]:
    """Normalisiert GA-Nummer."""
    m = re.search(r"(\d+[a-z]?)", ga_arg, re.IGNORECASE)
    if not m:
        return None
    return f"GA{m.group(1).zfill(3).upper()}"


def parse_ga_range(args: List[str], exclude: List[str] = None) -> List[str]:
    """Parst GA-Argumente inkl. Ranges wie GA171-GA200."""
    result = []
    exclude_set = set(normalize_ga(e) for e in (exclude or []) if normalize_ga(e))
    
    for arg in args:
        # Range: GA171-GA200
        range_match = re.match(r"GA?(\d+)\s*[-–]\s*GA?(\d+)", arg, re.IGNORECASE)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            for num in range(start, end + 1):
                ga = f"GA{num:03d}"
                if ga not in exclude_set:
                    result.append(ga)
        else:
            ga = normalize_ga(arg)
            if ga and ga not in exclude_set:
                result.append(ga)
    
    return result


def process_single_ga(ga: str) -> Tuple[str, bool, str, float, float]:
    """Verarbeitet eine einzelne GA (Mapping + Pagebreaks)."""
    import time
    
    mapping_script = SCRIPT_DIR / "generate_lecture_page_mapping.py"
    pagebreak_script = SCRIPT_DIR / "apply_page_break_markers_v4.py"
    output_file = SCRIPT_DIR / "pagebreaks" / f"{ga}.json"
    
    start = time.time()
    
    # Mapping generieren
    try:
        result = subprocess.run(
            [sys.executable, str(mapping_script), ga],
            capture_output=True, text=True, timeout=300, encoding='utf-8', errors='replace'
        )
        mapping_time = time.time() - start
        
        # Erfolg prüfen
        if "Ergebnis:" in result.stdout:
            match = re.search(r"Ergebnis: (\d+)/(\d+)", result.stdout)
            if match:
                found, total = int(match.group(1)), int(match.group(2))
                mapping_info = f"{found}/{total}"
            else:
                mapping_info = "OK"
        elif "Keine PDF" in result.stdout or "nicht gefunden" in result.stdout:
            return (ga, False, "Keine PDF", 0, 0)
        else:
            mapping_info = "?"
            
    except subprocess.TimeoutExpired:
        return (ga, False, "Mapping Timeout", 0, 0)
    except Exception as e:
        return (ga, False, f"Mapping Fehler: {e}", 0, 0)
    
    # Pagebreaks einfügen
    pb_start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(pagebreak_script), ga, "--out", str(output_file)],
            capture_output=True, text=True, timeout=300, encoding='utf-8', errors='replace'
        )
        pb_time = time.time() - pb_start
        
        # Erfolg prüfen
        if "eingefügt" in result.stdout:
            match = re.search(r"eingefügt (\d+)/(\d+) \(([0-9.]+)%\)", result.stdout)
            if match:
                pb_info = f"{match.group(3)}%"
            else:
                pb_info = "OK"
        else:
            pb_info = "?"
            
    except subprocess.TimeoutExpired:
        return (ga, False, f"Mapping: {mapping_info}, Pagebreak Timeout", mapping_time, 0)
    except Exception as e:
        return (ga, False, f"Mapping: {mapping_info}, Pagebreak Fehler: {e}", mapping_time, 0)
    
    return (ga, True, f"Mapping: {mapping_info}, Pagebreaks: {pb_info}", mapping_time, pb_time)


def main():
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description="Batch-Verarbeitung von GA-Seitenzahlen")
    parser.add_argument("gas", nargs="+", help="GA-Nummern oder Ranges (z.B. GA171 GA172 oder GA171-GA200)")
    parser.add_argument("--exclude", nargs="*", default=[], help="GAs die ausgeschlossen werden sollen")
    parser.add_argument("--workers", type=int, default=4, help="Anzahl paralleler Prozesse (Standard: 4)")
    args = parser.parse_args()
    
    gas = parse_ga_range(args.gas, args.exclude)
    
    if not gas:
        print("Keine gültigen GA-Nummern angegeben.")
        return
    
    print(f"Verarbeite {len(gas)} GA-Bände mit {args.workers} parallelen Prozessen...")
    print(f"GAs: {', '.join(gas)}")
    print("-" * 60)
    
    start_time = time.time()
    results = []
    
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_single_ga, ga): ga for ga in gas}
        
        for future in as_completed(futures):
            ga, success, info, map_time, pb_time = future.result()
            total_time = map_time + pb_time
            status = "✓" if success else "✗"
            print(f"  {status} {ga}: {info} ({total_time:.1f}s)")
            results.append((ga, success, info))
    
    elapsed = time.time() - start_time
    successful = sum(1 for _, s, _ in results if s)
    
    print("-" * 60)
    print(f"Fertig: {successful}/{len(gas)} erfolgreich in {elapsed:.1f}s")
    
    # Fehler auflisten
    failed = [(ga, info) for ga, success, info in results if not success]
    if failed:
        print("\nFehlgeschlagen:")
        for ga, info in failed:
            print(f"  - {ga}: {info}")


if __name__ == "__main__":
    main()
