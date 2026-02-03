# -*- coding: utf-8 -*-
"""
Synchronisiert IDs für mehrere GA-Bände zwischen alter und neuer Version.
Aktualisiert keywords-database.json, summary-database.json und concepts-database.json.
"""
import json
import os
import re
import glob
from difflib import SequenceMatcher
from datetime import datetime

# GA-Bände die synchronisiert werden sollen
# GA205, GA206, GA207 haben einzelne Dateien auf D:
# GA208 nicht gefunden
# GA209 nur in part-Dateien (bereits synchronisiert)
TARGET_GAS = ['GA205', 'GA206', 'GA207']

def normalize_text(text):
    """Normalisiert Text für Vergleich."""
    if not text:
        return ""
    # Entferne Seitenmarker wie |13|
    text = re.sub(r'\|\d+\|', '', text)
    # Entferne überschüssige Leerzeichen
    text = ' '.join(text.split())
    return text.lower()[:500]

def text_similarity(text1, text2):
    """Berechnet Ähnlichkeit zwischen zwei Texten."""
    t1 = normalize_text(text1)
    t2 = normalize_text(text2)
    if not t1 or not t2:
        return 0.0
    return SequenceMatcher(None, t1, t2).ratio()

def load_old_lectures_from_all_parts(ga_prefix):
    """Lädt alte Vorträge aus allen Dateien auf D:."""
    lectures = {}
    ga_num = ga_prefix.replace('GA', '')
    
    # Erst einzelne GA-Datei suchen
    single_file = rf"D:\steiner-full-lectures\steiner-full-lectures-{ga_num}-{ga_num}.json"
    if os.path.exists(single_file):
        print(f"  Alte Datei: {os.path.basename(single_file)}")
        try:
            with open(single_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            for lec in data.get('lectures', []):
                lec_id = lec.get('ID', lec.get('lectureId', ''))
                if lec_id.startswith(ga_prefix + '/'):
                    lectures[lec_id] = lec
        except Exception as e:
            print(f"  Fehler bei {single_file}: {e}")
        
        if lectures:
            return lectures
    
    # Fallback: part-Dateien durchsuchen
    old_files = glob.glob(r"D:\steiner-full-lectures\steiner-full-lectures-001-354-part*.json")
    
    for f in old_files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            for lec in data.get('lectures', []):
                lec_id = lec.get('ID', lec.get('lectureId', ''))
                if lec_id.startswith(ga_prefix + '/'):
                    lectures[lec_id] = lec
        except Exception as e:
            print(f"  Fehler bei {f}: {e}")
    
    return lectures

def load_new_lectures(ga_number):
    """Lädt neue Vorträge aus dem steiner-full-lectures Ordner."""
    lectures = {}
    
    # Suche passende Datei
    pattern = f"steiner-full-lectures/steiner-full-lectures-{ga_number[2:]}-*.json"
    files = glob.glob(pattern)
    
    if not files:
        # Versuche in part-Dateien zu suchen
        for f in glob.glob("steiner-full-lectures/steiner-full-lectures-*-*-part*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                for lec in data.get('lectures', []):
                    lec_id = lec.get('ID', '')
                    if lec_id.startswith(ga_number + '/'):
                        lectures[lec_id] = lec
            except:
                pass
        return lectures
    
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
            for lec in data.get('lectures', []):
                lec_id = lec.get('ID', '')
                if lec_id.startswith(ga_number + '/'):
                    lectures[lec_id] = lec
        except Exception as e:
            print(f"  Fehler bei {f}: {e}")
    
    return lectures

def create_id_mapping(old_lectures, new_lectures, ga_number):
    """Erstellt ein ID-Mapping basierend auf Textähnlichkeit."""
    mapping = {}
    
    for lec_id in old_lectures:
        if lec_id not in new_lectures:
            continue
        
        old_paras = old_lectures[lec_id].get('paragraphs', [])
        new_paras = new_lectures[lec_id].get('paragraphs', [])
        
        matched = 0
        for i, old_p in enumerate(old_paras):
            old_id = old_p.get('index', '')
            if not old_id:
                continue
            
            if i < len(new_paras):
                new_p = new_paras[i]
                new_id = new_p.get('index', '')
                
                if new_id:
                    old_text = old_p.get('content', old_p.get('text', ''))
                    new_text = new_p.get('content', new_p.get('text', ''))
                    score = text_similarity(old_text, new_text)
                    
                    if score >= 0.5:
                        mapping[old_id] = new_id
                        matched += 1
        
        print(f"  {lec_id}: {matched}/{len(old_paras)} IDs gemappt")
    
    return mapping

def main():
    print("=== Multi-GA ID-Synchronisierung ===")
    print(f"Ziel-GAs: {', '.join(TARGET_GAS)}\n")
    
    # Gesamt-Mapping aufbauen
    all_mappings = {}
    
    for ga in TARGET_GAS:
        print(f"\n--- {ga} ---")
        
        # Alte Vorträge aus allen part-Dateien laden
        old_lectures = load_old_lectures_from_all_parts(ga)
        if not old_lectures:
            print(f"  WARNUNG: Keine Vorträge auf D: gefunden!")
            continue
        print(f"  Alte Vorträge: {len(old_lectures)}")
        
        # Neue Vorträge laden
        new_lectures = load_new_lectures(ga)
        if not new_lectures:
            print(f"  WARNUNG: Keine neuen Vorträge gefunden!")
            continue
        print(f"  Neue Vorträge: {len(new_lectures)}")
        
        # Mapping erstellen
        mapping = create_id_mapping(old_lectures, new_lectures, ga)
        all_mappings.update(mapping)
        print(f"  Mapping: {len(mapping)} IDs")
    
    print(f"\n=== Gesamt-Mapping: {len(all_mappings)} IDs ===")
    
    if not all_mappings:
        print("Kein Mapping erstellt - Abbruch.")
        return
    
    # Backup-Verzeichnis
    backup_dir = "_backups"
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # === SUMMARY-DATABASE ===
    print("\n=== Aktualisiere summary-database.json ===")
    with open('summary-database.json', 'r', encoding='utf-8') as f:
        summary_db = json.load(f)
    
    backup_path = os.path.join(backup_dir, f"summary-database_{timestamp}.json")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(summary_db, f, ensure_ascii=False)
    print(f"  Backup: {backup_path}")
    
    summary_updated = 0
    for lec_id in summary_db:
        ga = lec_id.split('/')[0]
        if ga not in TARGET_GAS:
            continue
        
        entry = summary_db[lec_id]
        
        # tableOfContents
        for item in entry.get('tableOfContents', []):
            old_idx = item.get('index', '')
            if old_idx in all_mappings:
                item['index'] = all_mappings[old_idx]
                summary_updated += 1
        
        # headings
        for item in entry.get('headings', []):
            old_idx = item.get('index', '')
            if old_idx in all_mappings:
                item['index'] = all_mappings[old_idx]
                summary_updated += 1
        
        # lectureKeywords
        for item in entry.get('lectureKeywords', []):
            old_idx = item.get('index', '')
            if old_idx in all_mappings:
                item['index'] = all_mappings[old_idx]
                summary_updated += 1
    
    with open('summary-database.json', 'w', encoding='utf-8') as f:
        json.dump(summary_db, f, ensure_ascii=False, indent=2)
    print(f"  Aktualisiert: {summary_updated} Einträge")
    
    # === KEYWORDS-DATABASE ===
    print("\n=== Aktualisiere keywords-database.json ===")
    with open('keywords-database.json', 'r', encoding='utf-8') as f:
        keywords_db = json.load(f)
    
    backup_path = os.path.join(backup_dir, f"keywords-database_{timestamp}.json")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(keywords_db, f, ensure_ascii=False)
    print(f"  Backup: {backup_path}")
    
    keywords_updated = 0
    for lec_id in keywords_db:
        ga = lec_id.split('/')[0]
        if ga not in TARGET_GAS:
            continue
        
        for kw in keywords_db[lec_id].get('keywords', []):
            old_idx = kw.get('index', '')
            if old_idx in all_mappings:
                kw['index'] = all_mappings[old_idx]
                keywords_updated += 1
    
    with open('keywords-database.json', 'w', encoding='utf-8') as f:
        json.dump(keywords_db, f, ensure_ascii=False, indent=2)
    print(f"  Aktualisiert: {keywords_updated} Einträge")
    
    # === CONCEPTS-DATABASE ===
    print("\n=== Aktualisiere concepts-database.json ===")
    with open('concepts-database.json', 'r', encoding='utf-8') as f:
        concepts_db = json.load(f)
    
    backup_path = os.path.join(backup_dir, f"concepts-database_{timestamp}.json")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(concepts_db, f, ensure_ascii=False)
    print(f"  Backup: {backup_path}")
    
    concepts_updated = 0
    for concept in concepts_db:
        # Prüfe sources
        for source in concept.get('sources', []):
            # Index-Feld direkt
            old_idx = source.get('index', '')
            if old_idx in all_mappings:
                source['index'] = all_mappings[old_idx]
                concepts_updated += 1
            
            # Auch in text nach (GAXXX/Y:^id) Pattern suchen
            text = source.get('text', '')
            for ga in TARGET_GAS:
                pattern = rf'\({ga}/\d+:\^([a-z0-9]+)\)'
                for match in re.finditer(pattern, text):
                    old_id = '^' + match.group(1)
                    if old_id in all_mappings:
                        new_id = all_mappings[old_id]
                        old_ref = match.group(0)
                        new_ref = old_ref.replace(old_id, new_id)
                        source['text'] = source['text'].replace(old_ref, new_ref)
                        concepts_updated += 1
    
    with open('concepts-database.json', 'w', encoding='utf-8') as f:
        json.dump(concepts_db, f, ensure_ascii=False, indent=2)
    print(f"  Aktualisiert: {concepts_updated} Einträge")
    
    # === ZUSAMMENFASSUNG ===
    print("\n" + "=" * 50)
    print("=== FERTIG ===")
    print(f"Mapping: {len(all_mappings)} IDs")
    print(f"Summary-DB: {summary_updated} aktualisiert")
    print(f"Keywords-DB: {keywords_updated} aktualisiert")
    print(f"Concepts-DB: {concepts_updated} aktualisiert")

if __name__ == '__main__':
    main()
