# -*- coding: utf-8 -*-
"""
Überträgt IDs aus einer Quelldatei in eine bearbeitete Band-Datei.

Die Quelldatei hat separate Absätze mit IDs.
Die Band-Datei hat zusammengefügte Absätze ohne IDs.
Das Skript findet das Absatzende in der Quelldatei und fügt die ID an.

Verwendung:
    python tools/transfer_ids_from_source.py <band_datei> <quell_datei>
    python tools/transfer_ids_from_source.py <band_datei> <quell_datei> --dry-run
"""

import os
import re
import sys
from difflib import SequenceMatcher

def normalize_text(text):
    """Normalisiert Text für Vergleich (inkl. alte/neue Rechtschreibung)"""
    if not text:
        return ""
    text = text.replace('\ufeff', '').strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\|(\d+)\|', '', text)
    # Alte Rechtschreibung normalisieren
    replacements = [
        ('daß', 'dass'), ('Daß', 'Dass'),
        ('muß', 'muss'), ('Muß', 'Muss'),
        ('läßt', 'lässt'), ('Läßt', 'Lässt'),
        ('wußte', 'wusste'), ('mußte', 'musste'),
        ('bewußt', 'bewusst'), ('Bewußtsein', 'Bewusstsein'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text.strip()

def extract_source_paragraphs(content):
    """
    Extrahiert Absätze mit IDs aus der Quelldatei.
    Gibt Liste von (text_ohne_id, id) zurück.
    """
    paragraphs = []
    # Entferne --- Trennlinien
    content = re.sub(r'^---\s*$', '', content, flags=re.MULTILINE)
    
    # Finde alle Absätze mit IDs: Text ^id
    pattern = r'(.+?) \^([a-z0-9]+)\s*$'
    
    for match in re.finditer(pattern, content, re.MULTILINE):
        text = match.group(1).strip()
        para_id = match.group(2)
        if text:
            paragraphs.append((text, para_id))
    
    return paragraphs

def get_paragraph_ending(text, chars=100):
    """Gibt die letzten N Zeichen eines Absatzes zurück (normalisiert)."""
    normalized = normalize_text(text)
    return normalized[-chars:] if len(normalized) > chars else normalized

def find_matching_id(band_para_text, source_paragraphs):
    """
    Findet die passende ID aus der Quelldatei für einen Band-Absatz.
    Vergleicht das Absatzende der Band-Datei mit den Absatzenden der Quelldatei.
    """
    band_ending = get_paragraph_ending(band_para_text, 80)
    if not band_ending:
        return None
    
    best_match = None
    best_score = 0.7  # Minimum Threshold
    
    for source_text, source_id in source_paragraphs:
        source_ending = get_paragraph_ending(source_text, 80)
        if not source_ending:
            continue
        
        # Vergleiche die Enden
        score = SequenceMatcher(None, band_ending.lower(), source_ending.lower()).ratio()
        
        if score > best_score:
            best_score = score
            best_match = source_id
    
    return best_match

def transfer_ids(band_file, source_file, dry_run=False):
    """
    Hauptfunktion: Überträgt IDs von Quelldatei in Band-Datei.
    """
    print(f"=== ID-Transfer ===")
    print(f"Band-Datei: {os.path.basename(band_file)}")
    print(f"Quelldatei: {os.path.basename(source_file)}")
    print()
    
    # Dateien lesen
    with open(source_file, 'r', encoding='utf-8') as f:
        source_content = f.read()
    
    with open(band_file, 'r', encoding='utf-8') as f:
        band_content = f.read()
    
    # Extrahiere Quell-Absätze mit IDs
    source_paragraphs = extract_source_paragraphs(source_content)
    print(f"Gefunden: {len(source_paragraphs)} Absätze mit IDs in Quelldatei")
    
    # Verarbeite Band-Datei Zeile für Zeile
    lines = band_content.split('\n')
    new_lines = []
    ids_added = 0
    ids_already_present = 0
    no_match = 0
    
    for line in lines:
        # Überspringe leere Zeilen, Überschriften, Bilder, Trennlinien
        if not line.strip() or line.strip().startswith('#') or line.strip().startswith('!') or line.strip() == '---':
            new_lines.append(line)
            continue
        
        # Prüfe ob Zeile bereits eine ID hat
        if re.search(r' \^[a-z0-9]+$', line):
            ids_already_present += 1
            new_lines.append(line)
            continue
        
        # Suche passende ID
        matching_id = find_matching_id(line, source_paragraphs)
        
        if matching_id:
            new_line = f"{line} ^{matching_id}"
            new_lines.append(new_line)
            ids_added += 1
            if ids_added <= 5:
                print(f"  + ^{matching_id}: ...{line[-50:]}")
        else:
            new_lines.append(line)
            no_match += 1
    
    print()
    print(f"Ergebnis:")
    print(f"  {ids_added} IDs hinzugefügt")
    print(f"  {ids_already_present} IDs bereits vorhanden")
    print(f"  {no_match} Zeilen ohne Match")
    
    if dry_run:
        print()
        print("[DRY-RUN] Keine Änderungen vorgenommen.")
    else:
        # Backup erstellen
        backup_path = band_file + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(band_content)
        print(f"\nBackup erstellt: {os.path.basename(backup_path)}")
        
        # Speichern
        new_content = '\n'.join(new_lines)
        with open(band_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Gespeichert: {ids_added} IDs hinzugefügt")
    
    return ids_added

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Verwendung: python transfer_ids_from_source.py <band_datei> <quell_datei> [--dry-run]")
        sys.exit(1)
    
    band_file = sys.argv[1]
    source_file = sys.argv[2]
    dry_run = '--dry-run' in sys.argv
    
    if not os.path.exists(band_file):
        print(f"Fehler: Band-Datei nicht gefunden: {band_file}")
        sys.exit(1)
    
    if not os.path.exists(source_file):
        print(f"Fehler: Quelldatei nicht gefunden: {source_file}")
        sys.exit(1)
    
    transfer_ids(band_file, source_file, dry_run)
