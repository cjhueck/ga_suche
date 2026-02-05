# -*- coding: utf-8 -*-
"""
Fügt einzelne Vorträge eines GA-Bandes zu einer Gesamtdatei zusammen.

Verwendung:
    python merge_lectures.py <GA-Ordner-Pfad>
    python merge_lectures.py <GA-Ordner-Pfad> --output <Ausgabedatei>

Beispiel:
    python merge_lectures.py "Steiner_GA/GA235-Esoterische Betrachtungen karmischer Zusammenhänge. Band I"

Die Dateinamen werden zu # Überschriften:
    GA235 (1.) ERSTER VORTRAG, Dornach, 16. Februar 1924.md
    → # ERSTER VORTRAG, Dornach, 16. Februar 1924
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

def extract_lecture_number(filename):
    """Extrahiert die Vortragsnummer aus dem Dateinamen für Sortierung."""
    match = re.search(r'\((\d+)\.\)', filename)
    if match:
        return int(match.group(1))
    return 999  # Falls keine Nummer gefunden, ans Ende sortieren

def filename_to_heading(filename):
    """
    Konvertiert Dateinamen zu Überschrift.
    
    GA235 (1.) ERSTER VORTRAG, Dornach, 16. Februar 1924.md
    → # ERSTER VORTRAG, Dornach, 16. Februar 1924
    """
    # Entferne .md Endung
    name = filename.replace('.md', '')
    
    # Entferne GA-Präfix: GA235 (1.) → ERSTER VORTRAG...
    # Pattern: GAxx (x.) oder GAxxx (xx.) 
    name = re.sub(r'^GA\d{2,3}[a-z]?\s*\(\d+\.\)\s*', '', name)
    
    return f"# {name}"

def merge_lectures(ga_folder_path, output_file=None):
    """
    Fügt alle Einzelvorträge in einem GA-Ordner zusammen.
    
    Args:
        ga_folder_path: Pfad zum GA-Ordner
        output_file: Optionaler Ausgabedateiname (sonst automatisch)
    
    Returns:
        Pfad zur erstellten Gesamtdatei oder None bei Fehler
    """
    ga_folder = Path(ga_folder_path)
    
    if not ga_folder.exists():
        print(f"FEHLER: Ordner nicht gefunden: {ga_folder}")
        return None
    
    # Finde alle Einzelvortrags-Dateien: GA235 (1.) ... .md
    lecture_pattern = re.compile(r'^GA\d{2,3}[a-z]?\s*\(\d+\.\).*\.md$')
    
    lecture_files = []
    for f in ga_folder.iterdir():
        if f.is_file() and lecture_pattern.match(f.name):
            lecture_files.append(f)
    
    if not lecture_files:
        print(f"FEHLER: Keine Einzelvorträge gefunden in {ga_folder}")
        print("   Erwartet: Dateien wie 'GA235 (1.) ERSTER VORTRAG, ...md'")
        return None
    
    # Sortiere nach Vortragsnummer
    lecture_files.sort(key=lambda f: extract_lecture_number(f.name))
    
    print(f"Gefunden: {len(lecture_files)} Einzelvorträge")
    
    # Bestimme GA-Nummer und Titel für Header
    ga_match = re.match(r'(GA\d{2,3}[a-z]?)-(.+)', ga_folder.name)
    if ga_match:
        ga_num = ga_match.group(1)
        ga_title = ga_match.group(2).strip()
    else:
        ga_num = "GA???"
        ga_title = ga_folder.name
    
    # Bestimme Jahr aus erstem Vortrag
    first_file = lecture_files[0].name
    year_match = re.search(r'(\d{4})', first_file)
    year = year_match.group(1) if year_match else "????"
    
    # Bestimme Ausgabedatei
    if output_file:
        output_path = ga_folder / output_file
    else:
        output_path = ga_folder / f"{ga_num} - {ga_title} ({year})_merged.md"
    
    # Header
    header = f"""# RUDOLF STEINER - {ga_title.upper()} ({ga_num})

{len(lecture_files)} Vorträge, {year}

---

"""
    
    # Sammle alle Inhalte
    contents = [header]
    total_ids = 0
    
    for i, filepath in enumerate(lecture_files, 1):
        content = filepath.read_text(encoding='utf-8')
        
        # Zähle Absatz-IDs
        id_count = len(re.findall(r'\^[a-z0-9]+', content))
        total_ids += id_count
        
        # Erstelle Überschrift aus Dateinamen
        heading = filename_to_heading(filepath.name)
        
        # Füge Überschrift und Inhalt hinzu
        contents.append(f"{heading}\n\n")
        contents.append(content.strip())
        contents.append("\n\n---\n\n")
        
        print(f"  [{i:2d}/{len(lecture_files)}] {filepath.name[:50]}... ({id_count} IDs)")
    
    # Schreibe Gesamtdatei
    result = ''.join(contents)
    output_path.write_text(result, encoding='utf-8')
    
    # Statistik
    lines = result.count('\n')
    
    print(f"\n{'='*60}")
    print(f"Gesamtdatei erstellt: {output_path.name}")
    print(f"  Zeilen: {lines}")
    print(f"  Absatz-IDs: {total_ids}")
    print(f"  Vorträge: {len(lecture_files)}")
    
    return output_path

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    ga_folder = sys.argv[1]
    output_file = None
    
    # Parse optionale Argumente
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]
    
    result = merge_lectures(ga_folder, output_file)
    
    if result:
        print(f"\nErfolgreich: {result}")
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
