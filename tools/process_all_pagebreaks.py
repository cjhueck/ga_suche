#!/usr/bin/env python3
"""
Verarbeitet alle Pagebreaks für einen GA-Bereich und protokolliert Ergebnisse.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from apply_pagebreaks_from_pdf import process_ga as process_ga_json
from apply_pagebreaks_to_md import process_ga_md


def process_range(start: int, end: int, log_file: Path):
    """Verarbeitet einen GA-Bereich."""
    
    results = {
        'processed': [],
        'errors': [],
        'no_pdf': [],
        'no_md': [],
        'conflicts': []
    }
    
    for i in range(start, end + 1):
        ga = f"GA{i:03d}"
        print(f"\n{'='*60}")
        print(f"Verarbeite {ga}")
        print(f"{'='*60}")
        
        ga_result = {
            'ga': ga,
            'json_markers': 0,
            'md_markers': 0,
            'json_error': None,
            'md_error': None
        }
        
        # JSON verarbeiten
        try:
            json_result = process_ga_json(ga)
            ga_result['json_markers'] = json_result.get('total_markers', 0)
            if json_result.get('errors'):
                ga_result['json_error'] = json_result['errors']
                results['errors'].append(f"{ga} JSON: {json_result['errors']}")
        except Exception as e:
            error_msg = str(e)
            ga_result['json_error'] = error_msg
            if 'Keine PDF' in error_msg or 'PDF nicht gefunden' in error_msg:
                results['no_pdf'].append(ga)
            else:
                results['errors'].append(f"{ga} JSON: {error_msg}")
        
        # MD verarbeiten
        try:
            md_result = process_ga_md(ga)
            ga_result['md_markers'] = md_result.get('total_markers', 0)
            if md_result.get('errors'):
                ga_result['md_error'] = md_result['errors']
        except Exception as e:
            error_msg = str(e)
            ga_result['md_error'] = error_msg
            if 'Kein MD-Ordner' in error_msg:
                results['no_md'].append(ga)
        
        results['processed'].append(ga_result)
        
        # Kurze Zusammenfassung
        print(f"  JSON: {ga_result['json_markers']} Marker")
        print(f"  MD: {ga_result['md_markers']} Marker")
        if ga_result['json_error']:
            print(f"  JSON-Fehler: {ga_result['json_error'][:100]}")
        if ga_result['md_error']:
            print(f"  MD-Fehler: {ga_result['md_error'][:100]}")
    
    # Ergebnisse speichern
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results


def main():
    if len(sys.argv) < 3:
        print("Usage: python process_all_pagebreaks.py START END")
        print("Example: python process_all_pagebreaks.py 1 50")
        sys.exit(1)
    
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(f"pagebreaks_ga{start:03d}-{end:03d}_{timestamp}.json")
    
    print(f"\n{'#'*60}")
    print(f"# Verarbeite GA{start:03d} bis GA{end:03d}")
    print(f"# Log: {log_file}")
    print(f"{'#'*60}")
    
    results = process_range(start, end, log_file)
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    
    total_json = sum(r['json_markers'] for r in results['processed'])
    total_md = sum(r['md_markers'] for r in results['processed'])
    
    print(f"  Verarbeitet: {len(results['processed'])} GAs")
    print(f"  JSON Marker: {total_json}")
    print(f"  MD Marker: {total_md}")
    
    if results['no_pdf']:
        print(f"\n  Keine PDF ({len(results['no_pdf'])}): {', '.join(results['no_pdf'])}")
    
    if results['no_md']:
        print(f"\n  Kein MD-Ordner ({len(results['no_md'])}): {', '.join(results['no_md'])}")
    
    if results['errors']:
        print(f"\n  Fehler ({len(results['errors'])}):")
        for err in results['errors'][:10]:
            print(f"    - {err[:80]}")
    
    print(f"\n  Log gespeichert: {log_file}")


if __name__ == '__main__':
    main()

