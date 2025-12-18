#!/usr/bin/env python3
"""Test: Duplikate in Vortrags-JSONs finden"""

import json
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(r'c:\Users\chuec\OneDrive\GitHub\ga_suche')

# Alle Vortrags-GAs die wir testen wollen
TEST_GAS = ['GA030', 'GA051', 'GA052', 'GA089', 'GA093']

print("Suche nach Duplikaten in Vortrags-JSONs...")
print("=" * 60)
print()

for ga in TEST_GAS:
    # Sammle alle Vortraege dieser GA aus allen JSON-Dateien
    lectures_by_id = defaultdict(list)  # ID -> Liste von (Datei, Vortrag)
    
    for jf in sorted(SCRIPT_DIR.glob('steiner-full-lectures-*.json')):
        try:
            with open(jf, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for lec in data.get('lectures', []):
                if (lec.get('gaNumber') or '').upper() == ga:
                    lec_id = lec.get('ID') or lec.get('title') or 'UNKNOWN'
                    lectures_by_id[lec_id].append((jf.name, lec))
        except Exception as e:
            pass
    
    total_lectures = sum(len(v) for v in lectures_by_id.values())
    unique_lectures = len(lectures_by_id)
    duplicates = {k: v for k, v in lectures_by_id.items() if len(v) > 1}
    
    print(f"{ga}:")
    print(f"  Gesamt: {total_lectures} Vortraege in JSON-Dateien")
    print(f"  Eindeutig: {unique_lectures} verschiedene IDs")
    
    if duplicates:
        print(f"  DUPLIKATE: {len(duplicates)} IDs kommen mehrfach vor!")
        for lec_id, occurrences in list(duplicates.items())[:3]:
            files = [occ[0] for occ in occurrences]
            print(f"    - {lec_id}: {len(occurrences)}x in {files}")
    else:
        print(f"  Keine Duplikate")
    print()

