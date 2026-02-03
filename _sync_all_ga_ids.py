# -*- coding: utf-8 -*-
"""
Synchronisiert IDs für ALLE GA-Vortragsbände, wo nötig.
"""
import os
import sys
import glob
import re

# Füge tools-Ordner zum Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))
from sync_ids_from_lectures import sync_ids, find_lecture_files, find_ga_band_file, extract_paragraphs_with_ids, text_similarity, normalize_text

def check_needs_sync(ga_folder, ga_number):
    """Prüft ob ein GA-Band Synchronisierung benötigt."""
    # Finde Einzelvortragsdateien
    lecture_files = find_lecture_files(ga_folder)
    if not lecture_files:
        return False, "Keine Einzelvortragsdateien"
    
    # Finde GA-Band-Datei
    band_file = find_ga_band_file(ga_folder, ga_number)
    if not band_file:
        return False, "Keine Band-Datei"
    
    # Lese ersten Absatz aus Einzelvortrag
    with open(lecture_files[0], 'r', encoding='utf-8') as f:
        lec_content = f.read()
    lec_paras = extract_paragraphs_with_ids(lec_content)
    if not lec_paras:
        return False, "Keine Absätze in Einzelvortrag"
    
    # Lese ersten Absatz aus Band-Datei
    with open(band_file, 'r', encoding='utf-8') as f:
        band_content = f.read()
    band_paras = extract_paragraphs_with_ids(band_content)
    if not band_paras:
        return False, "Keine Absätze in Band-Datei"
    
    # Vergleiche erste IDs
    lec_text, lec_id = lec_paras[0]
    band_text, band_id = band_paras[0]
    
    # Prüfe ob Texte übereinstimmen (gleicher Absatz)
    similarity = text_similarity(lec_text, band_text)
    if similarity < 0.8:
        return False, f"Texte unterschiedlich ({similarity:.0%})"
    
    # Prüfe ob IDs unterschiedlich
    if lec_id == band_id:
        return False, "IDs bereits identisch"
    
    return True, f"IDs unterschiedlich: ^{band_id} vs ^{lec_id}"

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    steiner_ga = os.path.join(project_root, "Steiner_GA")
    
    print("=" * 70)
    print("  PRÜFE ALLE GA-BÄNDE AUF ID-SYNCHRONISIERUNGSBEDARF")
    print("=" * 70)
    
    # Sammle alle GA-Ordner
    ga_folders = []
    for folder_name in sorted(os.listdir(steiner_ga)):
        folder_path = os.path.join(steiner_ga, folder_name)
        if os.path.isdir(folder_path) and folder_name.startswith('GA'):
            # Extrahiere GA-Nummer
            match = re.match(r'(GA\d{2,3}[a-z]?)', folder_name)
            if match:
                ga_number = match.group(1)
                ga_folders.append((ga_number, folder_path))
    
    print(f"\nGefunden: {len(ga_folders)} GA-Ordner\n")
    
    # Prüfe jeden Ordner
    needs_sync = []
    no_sync_needed = []
    
    for ga_number, folder_path in ga_folders:
        needs, reason = check_needs_sync(folder_path, ga_number)
        if needs:
            needs_sync.append((ga_number, reason))
            print(f"  [SYNC] {ga_number}: {reason}")
        else:
            no_sync_needed.append((ga_number, reason))
    
    print(f"\n{'=' * 70}")
    print(f"ERGEBNIS:")
    print(f"  {len(needs_sync)} Bände benötigen Synchronisierung")
    print(f"  {len(no_sync_needed)} Bände OK oder nicht anwendbar")
    print(f"{'=' * 70}")
    
    if not needs_sync:
        print("\nKeine Synchronisierung notwendig.")
        return
    
    # Zeige Liste
    print(f"\nFolgende Bände werden synchronisiert:")
    for ga, reason in needs_sync:
        print(f"  - {ga}")
    
    # Auto-confirm wenn --yes Parameter
    if '--yes' not in sys.argv and '-y' not in sys.argv:
        print(f"\nFortfahren? (j/n): ", end='')
        response = input().lower()
        if response not in ['j', 'ja', 'y', 'yes']:
            print("Abgebrochen.")
            return
    
    # Führe Synchronisierung durch
    print(f"\n{'=' * 70}")
    print("  STARTE SYNCHRONISIERUNG")
    print(f"{'=' * 70}\n")
    
    success = 0
    failed = 0
    
    for ga_number, reason in needs_sync:
        print(f"\n--- {ga_number} ---")
        try:
            result = sync_ids(ga_number, dry_run=False)
            if result:
                success += 1
            else:
                failed += 1
        except Exception as e:
            print(f"FEHLER: {e}")
            failed += 1
    
    print(f"\n{'=' * 70}")
    print(f"ABGESCHLOSSEN:")
    print(f"  {success} erfolgreich")
    print(f"  {failed} fehlgeschlagen")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
