#!/usr/bin/env python3
"""
Parallele Verarbeitung von Pagebreaks für mehrere GAs.
Verwendet concurrent.futures für schnellere Verarbeitung.
"""

import sys
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse

# Füge das tools-Verzeichnis zum Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent))

from apply_pagebreaks_from_pdf import process_ga as process_ga_json
from apply_pagebreaks_to_md import process_ga_md


def process_single_ga(ga_number: str, do_json: bool = True, do_md: bool = True) -> dict:
    """Verarbeitet eine einzelne GA (JSON und/oder MD)."""
    result = {
        'ga': ga_number,
        'json_markers': 0,
        'md_markers': 0,
        'json_error': None,
        'md_error': None
    }
    
    if do_json:
        try:
            json_result = process_ga_json(ga_number)
            result['json_markers'] = json_result.get('total_markers', 0)
            if json_result.get('errors'):
                result['json_error'] = json_result['errors'][0] if json_result['errors'] else None
        except Exception as e:
            result['json_error'] = str(e)
    
    if do_md:
        try:
            md_result = process_ga_md(ga_number, dry_run=False)
            result['md_markers'] = md_result.get('total_markers', 0)
            if md_result.get('errors'):
                result['md_error'] = md_result['errors'][0] if md_result['errors'] else None
        except Exception as e:
            result['md_error'] = str(e)
    
    return result


def parse_ga_range(range_str: str) -> list:
    """Parst einen GA-Bereich wie '051-067' oder '051,052,053' oder '051'."""
    gas = []
    
    for part in range_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            start = int(start.replace('GA', '').replace('ga', ''))
            end = int(end.replace('GA', '').replace('ga', ''))
            for i in range(start, end + 1):
                gas.append(f"GA{i:03d}")
        else:
            num = int(part.replace('GA', '').replace('ga', ''))
            gas.append(f"GA{num:03d}")
    
    return gas


def main():
    parser = argparse.ArgumentParser(description='Parallele Pagebreak-Verarbeitung')
    parser.add_argument('range', help='GA-Bereich, z.B. "181-200" oder "051,052,053"')
    parser.add_argument('--json-only', action='store_true', help='Nur JSON verarbeiten')
    parser.add_argument('--md-only', action='store_true', help='Nur MD verarbeiten')
    parser.add_argument('--workers', type=int, default=4, help='Anzahl paralleler Prozesse (Standard: 4)')
    
    args = parser.parse_args()
    
    do_json = not args.md_only
    do_md = not args.json_only
    
    gas = parse_ga_range(args.range)
    print(f"\n{'='*60}")
    print(f"Parallele Verarbeitung von {len(gas)} GAs")
    print(f"JSON: {'Ja' if do_json else 'Nein'}, MD: {'Ja' if do_md else 'Nein'}")
    print(f"Worker: {args.workers}")
    print(f"{'='*60}\n")
    
    results = []
    errors = []
    
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        # Starte alle Tasks
        future_to_ga = {
            executor.submit(process_single_ga, ga, do_json, do_md): ga 
            for ga in gas
        }
        
        # Sammle Ergebnisse
        for future in as_completed(future_to_ga):
            ga = future_to_ga[future]
            try:
                result = future.result()
                results.append(result)
                
                # Kurze Statusmeldung
                status = f"  {ga}: "
                if do_json:
                    status += f"JSON={result['json_markers']}"
                    if result['json_error']:
                        status += f" (FEHLER)"
                if do_md:
                    if do_json:
                        status += ", "
                    status += f"MD={result['md_markers']}"
                    if result['md_error']:
                        status += f" (FEHLER)"
                print(status)
                
                if result['json_error']:
                    errors.append(f"{ga} JSON: {result['json_error']}")
                if result['md_error']:
                    errors.append(f"{ga} MD: {result['md_error']}")
                    
            except Exception as e:
                print(f"  {ga}: FEHLER - {e}")
                errors.append(f"{ga}: {e}")
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    
    total_json = sum(r['json_markers'] for r in results)
    total_md = sum(r['md_markers'] for r in results)
    
    print(f"  Verarbeitet: {len(results)} GAs")
    if do_json:
        print(f"  JSON Marker gesamt: {total_json}")
    if do_md:
        print(f"  MD Marker gesamt: {total_md}")
    
    if errors:
        print(f"\n  FEHLER ({len(errors)}):")
        for err in errors[:10]:  # Zeige max 10 Fehler
            print(f"    - {err}")
        if len(errors) > 10:
            print(f"    ... und {len(errors) - 10} weitere")
    
    print()


if __name__ == '__main__':
    main()

