# -*- coding: utf-8 -*-
"""
Prüft ALLE GA-Bände mit Einzelvortragsdateien UND Band-Datei auf Sync-Bedarf.
"""
import os
import sys
import glob
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))
from sync_ids_from_lectures import find_lecture_files, find_ga_band_file, extract_paragraphs_with_ids

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    steiner_ga = os.path.join(project_root, "Steiner_GA")
    
    print("Prüfe alle GA-Bände mit Einzelvorträgen + Band-Datei...\n")
    
    needs_sync = []
    
    for folder_name in sorted(os.listdir(steiner_ga)):
        folder_path = os.path.join(steiner_ga, folder_name)
        if not os.path.isdir(folder_path) or not folder_name.startswith('GA'):
            continue
        
        match = re.match(r'(GA\d{2,3}[a-z]?)', folder_name)
        if not match:
            continue
        ga_number = match.group(1)
        
        # Finde Dateien
        lecture_files = find_lecture_files(folder_path)
        if not lecture_files:
            continue
        
        band_file = find_ga_band_file(folder_path, ga_number)
        if not band_file:
            continue
        
        # Extrahiere IDs
        try:
            with open(lecture_files[0], 'r', encoding='utf-8') as f:
                lec_paras = extract_paragraphs_with_ids(f.read())
            with open(band_file, 'r', encoding='utf-8') as f:
                band_paras = extract_paragraphs_with_ids(f.read())
            
            if not lec_paras or not band_paras:
                continue
            
            # Vergleiche erste 3 IDs
            lec_ids = [p[1] for p in lec_paras[:3]]
            band_ids = [p[1] for p in band_paras[:3]]
            
            # Wenn mindestens eine ID unterschiedlich
            different = False
            for lid, bid in zip(lec_ids, band_ids):
                if lid != bid:
                    different = True
                    break
            
            if different:
                needs_sync.append((ga_number, f"^{band_ids[0]} vs ^{lec_ids[0]}"))
                print(f"  [SYNC] {ga_number}: IDs unterschiedlich")
        except Exception as e:
            pass
    
    print(f"\n{len(needs_sync)} Bände benötigen noch Synchronisierung:")
    for ga, info in needs_sync:
        print(f"  {ga}: {info}")
    
    if needs_sync and len(sys.argv) > 1 and sys.argv[1] == '--sync':
        print("\nSynchronisiere...")
        from sync_ids_from_lectures import sync_ids
        for ga, _ in needs_sync:
            print(f"\n--- {ga} ---")
            sync_ids(ga, dry_run=False)

if __name__ == "__main__":
    main()
