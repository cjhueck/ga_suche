# -*- coding: utf-8 -*-
"""
Fügt Einzelvortragsdateien zu einer Gesamtdatei zusammen.

Verwendung:
    python tools/combine_lectures.py GA126
    python tools/combine_lectures.py GA201

Das Skript:
1. Findet den GA-Ordner mit Einzelvorträgen
2. Sortiert die Vorträge nach Nummer
3. Extrahiert Überschriften aus Dateinamen (z.B. "GA126 (1.) ERSTER VORTRAG..." -> "# ERSTER VORTRAG...")
4. Fügt alles zu einer Gesamtdatei zusammen
"""

import os
import re
import sys

def find_ga_folder(ga_number):
    """Findet den GA-Ordner."""
    steiner_ga = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Steiner_GA')
    
    for folder in os.listdir(steiner_ga):
        if folder.startswith(ga_number + '-') or folder.startswith(ga_number + ' '):
            return os.path.join(steiner_ga, folder)
    
    return None

def get_lecture_files(ga_folder):
    """Findet und sortiert alle Vortragsdateien."""
    files = []
    
    for fname in os.listdir(ga_folder):
        if not fname.endswith('.md'):
            continue
        # Suche nach Muster wie (1.), (2.), etc.
        match = re.search(r'\((\d+)\.\)', fname)
        if match:
            num = int(match.group(1))
            files.append((num, fname))
    
    files.sort(key=lambda x: x[0])
    return files

def extract_title(filename):
    """Extrahiert den Titel aus dem Dateinamen."""
    # GA126 (1.) ERSTER VORTRAG, Stuttgart, 27. Dezember 1910.md
    # -> ERSTER VORTRAG, Stuttgart, 27. Dezember 1910
    match = re.search(r'\(\d+\.\)\s*(.+)\.md$', filename)
    if match:
        return match.group(1)
    return filename.replace('.md', '')

def combine_lectures(ga_number):
    """Hauptfunktion: Fügt Vorträge zusammen."""
    print(f"=== Vorträge zusammenfügen für {ga_number} ===\n")
    
    # Finde Ordner
    ga_folder = find_ga_folder(ga_number)
    if not ga_folder:
        print(f"Fehler: Ordner für {ga_number} nicht gefunden!")
        return None
    
    print(f"Ordner: {ga_folder}")
    
    # Finde Vortragsdateien
    lecture_files = get_lecture_files(ga_folder)
    if not lecture_files:
        print(f"Fehler: Keine Vortragsdateien gefunden!")
        return None
    
    print(f"Gefunden: {len(lecture_files)} Vorträge\n")
    
    # Zusammenfügen
    combined_content = []
    
    for num, fname in lecture_files:
        title = extract_title(fname)
        filepath = os.path.join(ga_folder, fname)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Füge Titel als H1 hinzu
        vortrag_content = f"# {title}\n\n{content}"
        combined_content.append(vortrag_content)
        print(f"  {num}. # {title[:55]}{'...' if len(title) > 55 else ''}")
    
    # Ausgabedatei bestimmen
    folder_name = os.path.basename(ga_folder)
    # Extrahiere Titel aus Ordnernamen: GA126-Okkulte Geschichte -> Okkulte Geschichte
    folder_title_match = re.search(r'GA\d+[a-z]?-(.+)', folder_name)
    if folder_title_match:
        folder_title = folder_title_match.group(1)
    else:
        folder_title = folder_name
    
    output_filename = f"{ga_number} - {folder_title} - Gesamt.md"
    output_path = os.path.join(ga_folder, output_filename)
    
    # Speichern
    final_content = '\n\n'.join(combined_content)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"\nGespeichert: {output_filename}")
    print(f"Größe: {len(final_content):,} Zeichen")
    
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python tools/combine_lectures.py GA126")
        sys.exit(1)
    
    ga_number = sys.argv[1].upper()
    combine_lectures(ga_number)
