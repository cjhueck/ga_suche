# -*- coding: utf-8 -*-
"""
Synchronisiert IDs aus Einzelvortragsdateien in die GA-Band-Datei.

Verwendung:
    python tools/sync_ids_from_lectures.py GA214
    python tools/sync_ids_from_lectures.py GA214 --dry-run    # Nur anzeigen, nicht ändern

Das Skript:
1. Findet alle Einzelvortragsdateien im GA-Ordner
2. Extrahiert die Absatz-IDs und Texte aus den Einzelvortragsdateien
3. Findet die entsprechenden Absätze in der GA-Band-Datei (per Textabgleich)
4. Ersetzt die IDs in der GA-Band-Datei durch die IDs aus den Einzelvortragsdateien
"""

import os
import re
import sys
import glob
from pathlib import Path
from difflib import SequenceMatcher

def normalize_text(text):
    """Normalisiert Text für Vergleich (inkl. alte/neue Rechtschreibung)"""
    if not text:
        return ""
    # Entferne BOM und Whitespace
    text = text.replace('\ufeff', '').strip()
    # Normalisiere Whitespace
    text = re.sub(r'\s+', ' ', text)
    # Entferne Seitenmarker |XX|
    text = re.sub(r'\|(\d+)\|', '', text)
    # Normalisiere alte Rechtschreibung zu neuer (für Vergleich)
    # ß nach kurzem Vokal wird zu ss
    replacements = [
        ('daß', 'dass'), ('Daß', 'Dass'),
        ('muß', 'muss'), ('Muß', 'Muss'),
        ('laß', 'lass'), ('Laß', 'Lass'),
        ('läßt', 'lässt'), ('Läßt', 'Lässt'),
        ('faßt', 'fasst'), ('Faßt', 'Fasst'),
        ('paßt', 'passt'), ('Paßt', 'Passt'),
        ('haßt', 'hasst'), ('Haßt', 'Hasst'),
        ('wußte', 'wusste'), ('Wußte', 'Wusste'),
        ('mußte', 'musste'), ('Mußte', 'Musste'),
        ('bewußt', 'bewusst'), ('Bewußt', 'Bewusst'),
        ('Bewußtsein', 'Bewusstsein'),
        ('gewußt', 'gewusst'),
        ('Fluß', 'Fluss'), ('Schluß', 'Schluss'),
        ('Einfluß', 'Einfluss'), ('Abschluß', 'Abschluss'),
        ('Anschluß', 'Anschluss'), ('Entschluß', 'Entschluss'),
        ('Kuß', 'Kuss'), ('Nuß', 'Nuss'), ('Genuß', 'Genuss'),
        ('Überfluß', 'Überfluss'), ('Zufluß', 'Zufluss'),
        ('Biß', 'Biss'), ('Riß', 'Riss'), ('Schriß', 'Schriss'),
        ('Misverständnis', 'Missverständnis'),
        ('mißverstehen', 'missverstehen'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text.strip()

def text_similarity(a, b):
    """Berechnet Textähnlichkeit zwischen 0 und 1"""
    a = normalize_text(a)
    b = normalize_text(b)
    if not a or not b:
        return 0
    # Quick check: Längenunterschied > 50% = keine Übereinstimmung
    len_ratio = min(len(a), len(b)) / max(len(a), len(b)) if max(len(a), len(b)) > 0 else 0
    if len_ratio < 0.5:
        return 0
    # Vergleiche nur die ersten 100 Zeichen für Performance
    return SequenceMatcher(None, a[:100].lower(), b[:100].lower()).ratio()

def extract_paragraphs_with_ids(content):
    """
    Extrahiert Absätze mit IDs aus Markdown-Inhalt.
    
    Returns:
        List of (text, id) tuples
    """
    paragraphs = []
    
    # Pattern: Text mit ID am Ende ^xxxxx
    # Absätze sind durch Leerzeilen getrennt
    blocks = re.split(r'\n\s*\n', content)
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        # Suche ID am Ende des Blocks
        id_match = re.search(r'\^([a-z0-9]+)\s*$', block)
        if id_match:
            para_id = id_match.group(1)
            # Text ohne ID
            text = block[:id_match.start()].strip()
            if text and len(text) > 20:  # Nur substantielle Absätze
                paragraphs.append((text, para_id))
    
    return paragraphs

def find_lecture_files(ga_folder):
    """
    Findet Einzelvortragsdateien im GA-Ordner.
    Pattern: GA214 (1.) ERSTER VORTRAG...md
    """
    lecture_files = []
    
    # Pattern für Einzelvorträge: GA214 (1.) ...
    pattern = os.path.join(ga_folder, "GA* (*.) *.md")
    files = glob.glob(pattern)
    
    # Sortiere nach Vortragsnummer
    def extract_num(f):
        match = re.search(r'\((\d+)\.\)', os.path.basename(f))
        return int(match.group(1)) if match else 999
    
    files.sort(key=extract_num)
    return files

def find_ga_band_file(ga_folder, ga_number):
    """
    Findet die GA-Band-Datei.
    Pattern: GA214 - Titel (Jahr).md
    """
    # Pattern für GA-Band-Datei
    pattern = os.path.join(ga_folder, f"{ga_number} - *.md")
    files = glob.glob(pattern)
    
    if files:
        return files[0]
    
    # Alternative: GA214 - Titel.md (ohne Jahr)
    pattern = os.path.join(ga_folder, f"{ga_number} *.md")
    files = [f for f in glob.glob(pattern) if not re.search(r'\(\d+\.\)', os.path.basename(f))]
    
    if files:
        # Wähle die Datei mit " - " im Namen (wahrscheinlich die Band-Datei)
        for f in files:
            if ' - ' in os.path.basename(f):
                return f
    
    return None

def sync_ids(ga_number, dry_run=False):
    """
    Synchronisiert IDs aus Einzelvortragsdateien in die GA-Band-Datei.
    """
    # Finde GA-Ordner
    project_root = Path(__file__).parent.parent
    steiner_ga = project_root / "Steiner_GA"
    
    # Suche GA-Ordner
    ga_folders = list(steiner_ga.glob(f"{ga_number}-*"))
    if not ga_folders:
        ga_folders = list(steiner_ga.glob(f"{ga_number}*"))
    
    if not ga_folders:
        print(f"Fehler: GA-Ordner für {ga_number} nicht gefunden")
        return False
    
    ga_folder = str(ga_folders[0])
    print(f"GA-Ordner: {ga_folder}")
    
    # Finde Einzelvortragsdateien
    lecture_files = find_lecture_files(ga_folder)
    if not lecture_files:
        print(f"Fehler: Keine Einzelvortragsdateien gefunden")
        return False
    
    print(f"Gefunden: {len(lecture_files)} Einzelvortragsdateien")
    
    # Finde GA-Band-Datei
    band_file = find_ga_band_file(ga_folder, ga_number)
    if not band_file:
        print(f"Fehler: GA-Band-Datei nicht gefunden")
        return False
    
    print(f"GA-Band-Datei: {os.path.basename(band_file)}")
    
    # Sammle alle IDs aus Einzelvortragsdateien
    lecture_paragraphs = []  # (text, id, lecture_num)
    
    for lf in lecture_files:
        # Extrahiere Vortragsnummer
        match = re.search(r'\((\d+)\.\)', os.path.basename(lf))
        lecture_num = int(match.group(1)) if match else 0
        
        with open(lf, 'r', encoding='utf-8') as f:
            content = f.read()
        
        paras = extract_paragraphs_with_ids(content)
        for text, para_id in paras:
            lecture_paragraphs.append((text, para_id, lecture_num))
    
    print(f"Extrahiert: {len(lecture_paragraphs)} Absätze mit IDs aus Einzelvorträgen")
    
    # Lade GA-Band-Datei
    with open(band_file, 'r', encoding='utf-8') as f:
        band_content = f.read()
    
    # Extrahiere Absätze aus GA-Band-Datei
    band_paragraphs = extract_paragraphs_with_ids(band_content)
    print(f"GA-Band-Datei enthält: {len(band_paragraphs)} Absätze mit IDs")
    
    # Erstelle Index für schnelles Matching: erste 50 Zeichen (normalisiert) -> (id, text)
    lec_index = {}
    for lec_text, lec_id, lec_num in lecture_paragraphs:
        key = normalize_text(lec_text)[:50].lower()
        if key not in lec_index:
            lec_index[key] = []
        lec_index[key].append((lec_id, lec_text, lec_num))
    
    # Erstelle Mapping: alte ID (Band) -> neue ID (Einzelvortrag)
    id_mapping = {}
    matched = 0
    unmatched = 0
    
    for band_text, band_id in band_paragraphs:
        band_key = normalize_text(band_text)[:50].lower()
        best_match = None
        best_score = 0
        
        # Suche zuerst im Index (exakter Key-Match)
        if band_key in lec_index:
            for lec_id, lec_text, lec_num in lec_index[band_key]:
                score = text_similarity(band_text, lec_text)
                if score > best_score and score >= 0.8:
                    best_score = score
                    best_match = (lec_id, lec_num, score)
        
        # Falls kein Match, suche in ähnlichen Keys
        if not best_match:
            for key, entries in lec_index.items():
                # Quick check: Key-Ähnlichkeit
                if abs(len(key) - len(band_key)) > 20:
                    continue
                if band_key[:20] != key[:20]:
                    continue
                for lec_id, lec_text, lec_num in entries:
                    score = text_similarity(band_text, lec_text)
                    if score > best_score and score >= 0.8:
                        best_score = score
                        best_match = (lec_id, lec_num, score)
        
        if best_match:
            lec_id, lec_num, score = best_match
            if band_id != lec_id:
                id_mapping[band_id] = lec_id
                matched += 1
        else:
            unmatched += 1
    
    print(f"\nErgebnis:")
    print(f"  {matched} IDs müssen ersetzt werden")
    print(f"  {len(band_paragraphs) - matched - unmatched} IDs sind bereits identisch")
    print(f"  {unmatched} Absätze ohne Match (< 80% Ähnlichkeit)")
    
    if not id_mapping:
        print("\nKeine Änderungen notwendig.")
        return True
    
    # Zeige erste 10 Ersetzungen
    print(f"\nBeispiele (erste 10 von {len(id_mapping)}):")
    for i, (old_id, new_id) in enumerate(list(id_mapping.items())[:10]):
        print(f"  ^{old_id} -> ^{new_id}")
    
    if dry_run:
        print("\n[DRY-RUN] Keine Änderungen vorgenommen.")
        return True
    
    # Ersetze IDs in GA-Band-Datei
    new_content = band_content
    replaced = 0
    
    for old_id, new_id in id_mapping.items():
        # Ersetze ^oldid durch ^newid
        pattern = rf'\^{old_id}(\s|$)'
        replacement = f'^{new_id}\\1'
        new_content, count = re.subn(pattern, replacement, new_content)
        if count > 0:
            replaced += count
    
    if replaced > 0:
        # Backup erstellen
        backup_file = band_file + '.backup'
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(band_content)
        print(f"\nBackup erstellt: {os.path.basename(backup_file)}")
        
        # Neue Datei speichern
        with open(band_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Gespeichert: {replaced} IDs ersetzt in {os.path.basename(band_file)}")
    
    return True

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nVerwendung: python sync_ids_from_lectures.py GA214 [--dry-run]")
        sys.exit(1)
    
    ga_number = sys.argv[1].upper()
    if not ga_number.startswith('GA'):
        ga_number = 'GA' + ga_number
    
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    print(f"=== ID-Synchronisierung für {ga_number} ===\n")
    
    success = sync_ids(ga_number, dry_run=dry_run)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
