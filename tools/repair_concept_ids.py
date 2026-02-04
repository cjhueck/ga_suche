# -*- coding: utf-8 -*-
"""
Repariert gebrochene Concept-IDs durch Text-Matching.

1. Sammelt alle gebrochenen IDs aus concepts-database.json
2. Findet den Text zu diesen IDs in alten Backup-JSONs
3. Sucht den gleichen Text in den aktuellen JSONs und findet die neue ID
4. Aktualisiert die concepts-database.json

Verwendung:
    python tools/repair_concept_ids.py --dry-run
    python tools/repair_concept_ids.py
"""

import json
import glob
import os
import re
import sys
import shutil
from datetime import datetime

def normalize_text(text):
    """Normalisiert Text für Vergleich"""
    if not text:
        return ""
    text = text.replace('\ufeff', '').strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\|(\d+)\|', '', text)
    # Alte Rechtschreibung
    replacements = [
        ('daß', 'dass'), ('Daß', 'Dass'),
        ('muß', 'muss'), ('Muß', 'Muss'),
        ('läßt', 'lässt'), ('Läßt', 'Lässt'),
        ('wußte', 'wusste'), ('Wußte', 'Wusste'),
        ('mußte', 'musste'), ('Mußte', 'Musste'),
        ('bewußt', 'bewusst'), ('Bewußt', 'Bewusst'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text.strip().lower()

def main():
    dry_run = '--dry-run' in sys.argv
    
    print("=== Concept-ID Reparatur ===\n")
    
    # 1. Sammle aktuelle gültige IDs und ihre Texte
    print("Lade aktuelle Vorträge...")
    current_ids = {}  # id -> text
    current_text_to_id = {}  # normalized_text_prefix -> id
    
    for jfile in glob.glob('steiner-full-lectures/steiner-full-lectures-*.json'):
        with open(jfile, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for lecture in data.get('lectures', []):
            for para in lecture.get('paragraphs', []):
                idx = para.get('index', '')
                text = para.get('text', '') or para.get('content', '')
                if idx and text:
                    current_ids[idx] = text
                    norm_text = normalize_text(text)
                    if len(norm_text) > 50:
                        current_text_to_id[norm_text[:200]] = idx
                        current_text_to_id[norm_text[:100]] = idx
                        current_text_to_id[norm_text[:50]] = idx
    
    print(f"  Aktuelle IDs: {len(current_ids):,}")
    
    # 2. Sammle gebrochene IDs aus Concepts
    print("\nLade Concepts...")
    with open('concepts-database.json', 'r', encoding='utf-8') as f:
        concepts = json.load(f)
    
    broken_ids = set()
    id_pattern = re.compile(r'\^[a-z0-9]+')
    
    for c in concepts:
        text = c.get('text', '')
        ids = id_pattern.findall(text)
        for id in ids:
            if id not in current_ids:
                broken_ids.add(id)
    
    print(f"  Gebrochene IDs: {len(broken_ids):,}")
    
    # 3. Lade alte Backups und finde Texte für gebrochene IDs
    print("\nLade alte Backups...")
    old_folders = [
        'C:/Users/chuec/OneDrive/Obsidian/ga_suche - Kopien/ga_suche',
        'C:/Users/chuec/OneDrive/Obsidian/ga_suche - Kopien/ga_suche 14.10.2025',
        'C:/Users/chuec/OneDrive/Obsidian/ga_suche - Kopien/ga_suche 18.10.2025',
        'C:/Users/chuec/OneDrive/Obsidian/ga_suche - Kopien/ga_suche 18.10.2025 - vor timeline',
        'C:/Users/chuec/OneDrive/Obsidian/ga_suche - Kopien/ga_suche 20.10.2025 - vor ZW Indizierung',
    ]
    
    old_id_to_text = {}  # broken_id -> text
    
    for old_folder in old_folders:
        if not os.path.exists(old_folder):
            continue
        for jfile in glob.glob(f'{old_folder}/steiner-full-lectures-*.json'):
            try:
                with open(jfile, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for lecture in data.get('lectures', []):
                    for para in lecture.get('paragraphs', []):
                        idx = para.get('index', '')
                        if idx and idx in broken_ids and idx not in old_id_to_text:
                            text = para.get('text', '') or para.get('content', '')
                            if text:
                                old_id_to_text[idx] = text
            except Exception as e:
                pass
    
    print(f"  Texte für gebrochene IDs gefunden: {len(old_id_to_text):,}")
    
    # 4. Finde neue IDs per Text-Matching
    print("\nSuche neue IDs per Text-Matching...")
    id_mapping = {}  # old_id -> new_id
    
    for old_id, old_text in old_id_to_text.items():
        norm_old = normalize_text(old_text)
        if len(norm_old) < 30:
            continue
        
        # Versuche verschiedene Prefix-Längen
        for prefix_len in [200, 100, 50]:
            prefix = norm_old[:prefix_len]
            if prefix in current_text_to_id:
                id_mapping[old_id] = current_text_to_id[prefix]
                break
    
    print(f"  ID-Mappings gefunden: {len(id_mapping):,}")
    
    # 5. Aktualisiere Concepts
    print("\nAktualisiere Concepts...")
    updated_count = 0
    
    for c in concepts:
        text = c.get('text', '')
        new_text = text
        
        for old_id, new_id in id_mapping.items():
            if old_id in new_text:
                new_text = new_text.replace(old_id, new_id)
                updated_count += 1
        
        if not dry_run and new_text != text:
            c['text'] = new_text
    
    print(f"  ID-Ersetzungen: {updated_count:,}")
    
    # 6. Speichern
    if dry_run:
        print("\n[DRY-RUN] Keine Änderungen gespeichert.")
    else:
        # Backup
        backup_path = f'_backups/concepts-database_pre_repair_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        shutil.copy('concepts-database.json', backup_path)
        print(f"\nBackup erstellt: {backup_path}")
        
        # Speichern
        with open('concepts-database.json', 'w', encoding='utf-8') as f:
            json.dump(concepts, f, ensure_ascii=False, indent=2)
        print("concepts-database.json gespeichert!")
    
    # Zusammenfassung
    still_broken = len(broken_ids) - len(id_mapping)
    print(f"\n=== Zusammenfassung ===")
    print(f"Gebrochene IDs vorher: {len(broken_ids):,}")
    print(f"IDs repariert: {len(id_mapping):,}")
    print(f"Noch gebrochen: {still_broken:,}")

if __name__ == "__main__":
    main()
