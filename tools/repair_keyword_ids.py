# -*- coding: utf-8 -*-
"""
Repariert gebrochene Keyword-IDs durch Text-Matching.

1. Sammelt alle gebrochenen IDs aus keywords-database.json
2. Findet den Text zu diesen IDs in alten Backup-JSONs
3. Sucht den gleichen Text in den aktuellen JSONs und findet die neue ID
4. Aktualisiert die keywords-database.json

Verwendung:
    python tools/repair_keyword_ids.py --dry-run
    python tools/repair_keyword_ids.py
"""

import json
import glob
import os
import re
import sys
from difflib import SequenceMatcher

def normalize_text(text):
    """Normalisiert Text für Vergleich"""
    if not text:
        return ""
    text = text.replace('\ufeff', '').strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\|(\d+)\|', '', text)
    # Alte Rechtschreibung
    replacements = [
        ('daß', 'dass'), ('muß', 'muss'), ('läßt', 'lässt'),
        ('wußte', 'wusste'), ('mußte', 'musste'), ('bewußt', 'bewusst'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text.strip().lower()

def main():
    dry_run = '--dry-run' in sys.argv
    
    print("=== Keyword-ID Reparatur ===\n")
    
    # 1. Sammle aktuelle gültige IDs und ihre Texte
    print("Lade aktuelle Vorträge...")
    current_ids = {}  # id -> text
    current_text_to_id = {}  # normalized_text -> id
    
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
                    if len(norm_text) > 50:  # Nur sinnvolle Texte
                        current_text_to_id[norm_text[:200]] = idx
    
    print(f"  Aktuelle IDs: {len(current_ids):,}")
    
    # 2. Sammle gebrochene IDs aus Keywords
    print("\nLade Keywords...")
    with open('keywords-database.json', 'r', encoding='utf-8') as f:
        keywords = json.load(f)
    
    broken_ids = set()
    for lecture_id, kw_data in keywords.items():
        if isinstance(kw_data, dict):
            kw_list = kw_data.get('keywords', [])
        else:
            continue
        for kw in kw_list:
            if isinstance(kw, dict):
                idx = kw.get('index', '')
                if idx and idx not in current_ids:
                    broken_ids.add(idx)
    
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
    
    # 4. Finde neue IDs per Text-Matching (nur direktes Matching für Geschwindigkeit)
    print("\nSuche neue IDs per Text-Matching...")
    id_mapping = {}  # old_id -> new_id
    
    # Erstelle mehrere Indices für besseres Matching
    text_index_100 = {}  # erste 100 Zeichen
    text_index_50 = {}   # erste 50 Zeichen
    
    for text_prefix, idx in current_text_to_id.items():
        text_index_100[text_prefix[:100]] = idx
        text_index_50[text_prefix[:50]] = idx
    
    for old_id, old_text in old_id_to_text.items():
        norm_old = normalize_text(old_text)
        if len(norm_old) < 30:
            continue
        
        # Versuche verschiedene Prefix-Längen
        if norm_old[:200] in current_text_to_id:
            id_mapping[old_id] = current_text_to_id[norm_old[:200]]
        elif norm_old[:100] in text_index_100:
            id_mapping[old_id] = text_index_100[norm_old[:100]]
        elif norm_old[:50] in text_index_50:
            id_mapping[old_id] = text_index_50[norm_old[:50]]
    
    print(f"  ID-Mappings gefunden: {len(id_mapping):,}")
    
    # 5. Aktualisiere Keywords
    print("\nAktualisiere Keywords...")
    updated_count = 0
    
    for lecture_id, kw_data in keywords.items():
        if isinstance(kw_data, dict):
            kw_list = kw_data.get('keywords', [])
        else:
            continue
        
        for kw in kw_list:
            if isinstance(kw, dict):
                old_idx = kw.get('index', '')
                if old_idx in id_mapping:
                    if not dry_run:
                        kw['index'] = id_mapping[old_idx]
                    updated_count += 1
    
    print(f"  Keywords aktualisiert: {updated_count:,}")
    
    # 6. Speichern
    if dry_run:
        print("\n[DRY-RUN] Keine Änderungen gespeichert.")
    else:
        # Backup
        import shutil
        backup_path = '_backups/keywords-database_pre_repair.json'
        shutil.copy('keywords-database.json', backup_path)
        print(f"\nBackup erstellt: {backup_path}")
        
        # Speichern
        with open('keywords-database.json', 'w', encoding='utf-8') as f:
            json.dump(keywords, f, ensure_ascii=False, indent=2)
        print("keywords-database.json gespeichert!")
    
    # Zusammenfassung
    still_broken = len(broken_ids) - len(id_mapping)
    print(f"\n=== Zusammenfassung ===")
    print(f"Gebrochene IDs vorher: {len(broken_ids):,}")
    print(f"IDs repariert: {len(id_mapping):,}")
    print(f"Noch gebrochen: {still_broken:,}")

if __name__ == "__main__":
    main()
