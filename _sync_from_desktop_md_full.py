# -*- coding: utf-8 -*-
"""
Synchronisiert IDs für GA205-GA209 mit VOLLEM Text-Matching.
Sucht für jeden alten Absatz den besten Match in allen neuen Absätzen.
"""
import json
import os
import re
import glob
from difflib import SequenceMatcher
from datetime import datetime

DESKTOP_GA_PATH = r"C:\Users\chuec\OneDrive\Desktop\Steiner_GA"
TARGET_GAS = ['GA205', 'GA206', 'GA207', 'GA208', 'GA209']

def normalize_text(text):
    """Normalisiert Text für Vergleich."""
    if not text:
        return ""
    # Entferne Seitenmarker wie |13|
    text = re.sub(r'\|\d+\|', '', text)
    # Entferne IDs
    text = re.sub(r'\^[a-z0-9]+', '', text)
    # Entferne überschüssige Leerzeichen
    text = ' '.join(text.split())
    return text.lower()

def text_similarity(text1, text2):
    """Berechnet Ähnlichkeit zwischen zwei Texten."""
    t1 = normalize_text(text1)
    t2 = normalize_text(text2)
    if not t1 or not t2:
        return 0.0
    # Verwende nur ersten Teil für schnelleren Vergleich
    t1 = t1[:500]
    t2 = t2[:500]
    return SequenceMatcher(None, t1, t2).ratio()

def extract_paragraphs_from_md(md_file):
    """Extrahiert Absätze mit IDs aus einer Markdown-Datei."""
    paragraphs = []
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Teile in Absätze (durch Leerzeilen getrennt)
    blocks = re.split(r'\n\n+', content)
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        # Suche nach ID am Ende des Blocks
        id_match = re.search(r'\^([a-z0-9]+)\s*$', block)
        if id_match:
            para_id = '^' + id_match.group(1)
            # Text ohne ID
            text = re.sub(r'\^[a-z0-9]+\s*$', '', block).strip()
            paragraphs.append({
                'index': para_id,
                'text': text
            })
    
    return paragraphs

def load_old_lectures_from_desktop(ga_number):
    """Lädt alte Vorträge aus Desktop-Markdown-Dateien."""
    lectures = {}
    
    # Finde GA-Ordner auf Desktop
    ga_folders = glob.glob(os.path.join(DESKTOP_GA_PATH, f"{ga_number}-*"))
    if not ga_folders:
        return lectures
    
    ga_folder = ga_folders[0]
    
    # Finde alle Vortragsdateien
    md_files = glob.glob(os.path.join(ga_folder, f"{ga_number} (*.md"))
    
    for md_file in md_files:
        basename = os.path.basename(md_file)
        num_match = re.search(rf'{ga_number}\s*\((\d+)\.\)', basename)
        if num_match:
            lecture_num = num_match.group(1)
            lecture_id = f"{ga_number}/{lecture_num}"
            
            paragraphs = extract_paragraphs_from_md(md_file)
            if paragraphs:
                lectures[lecture_id] = {'paragraphs': paragraphs}
    
    return lectures

def load_new_lectures(ga_number):
    """Lädt neue Vorträge aus exportierten JSON-Dateien."""
    lectures = {}
    ga_num = ga_number.replace('GA', '')
    
    pattern = f"steiner-full-lectures/steiner-full-lectures-{ga_num}-*.json"
    files = glob.glob(pattern)
    
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

def create_full_mapping(old_lectures, new_lectures, ga_number):
    """Erstellt ein vollständiges ID-Mapping mit Text-Matching über alle Absätze."""
    mapping = {}
    
    for lec_id in old_lectures:
        if lec_id not in new_lectures:
            continue
        
        old_paras = old_lectures[lec_id].get('paragraphs', [])
        new_paras = new_lectures[lec_id].get('paragraphs', [])
        
        # Erstelle Index für neue Absätze
        new_para_texts = []
        for np in new_paras:
            new_id = np.get('index', '')
            new_text = np.get('content', np.get('text', ''))
            new_para_texts.append((new_id, new_text))
        
        matched = 0
        for old_p in old_paras:
            old_id = old_p.get('index', '')
            old_text = old_p.get('text', '')
            
            if not old_id or old_id in mapping:
                continue
            
            # Suche besten Match in allen neuen Absätzen
            best_match = None
            best_score = 0.0
            
            for new_id, new_text in new_para_texts:
                if not new_id:
                    continue
                
                score = text_similarity(old_text, new_text)
                if score > best_score:
                    best_score = score
                    best_match = new_id
            
            if best_score >= 0.6 and best_match:
                mapping[old_id] = best_match
                matched += 1
        
        print(f"  {lec_id}: {matched}/{len(old_paras)} IDs gemappt")
    
    return mapping

def main():
    print("=== VOLLES Text-Matching von Desktop-Markdown-Dateien ===")
    print(f"Quelle: {DESKTOP_GA_PATH}")
    print(f"Ziel-GAs: {', '.join(TARGET_GAS)}\n")
    
    all_mappings = {}
    
    for ga in TARGET_GAS:
        print(f"\n--- {ga} ---")
        
        old_lectures = load_old_lectures_from_desktop(ga)
        if not old_lectures:
            print(f"  WARNUNG: Keine Vorträge auf Desktop gefunden!")
            continue
        print(f"  Alte Vorträge: {len(old_lectures)}")
        
        new_lectures = load_new_lectures(ga)
        if not new_lectures:
            print(f"  WARNUNG: Keine neuen Vorträge gefunden!")
            continue
        print(f"  Neue Vorträge: {len(new_lectures)}")
        
        # Volles Text-Matching
        mapping = create_full_mapping(old_lectures, new_lectures, ga)
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
        
        for item in entry.get('tableOfContents', []):
            old_idx = item.get('index', '')
            if old_idx in all_mappings:
                item['index'] = all_mappings[old_idx]
                summary_updated += 1
        
        for item in entry.get('headings', []):
            old_idx = item.get('index', '')
            if old_idx in all_mappings:
                item['index'] = all_mappings[old_idx]
                summary_updated += 1
        
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
        for field_name in list(concept.keys()):
            field_value = concept[field_name]
            if not isinstance(field_value, str):
                continue
            
            for old_id, new_id in all_mappings.items():
                if old_id in field_value:
                    concept[field_name] = concept[field_name].replace(old_id, new_id)
                    concepts_updated += 1
        
        for source in concept.get('sources', []):
            old_idx = source.get('index', '')
            if old_idx in all_mappings:
                source['index'] = all_mappings[old_idx]
                concepts_updated += 1
    
    with open('concepts-database.json', 'w', encoding='utf-8') as f:
        json.dump(concepts_db, f, ensure_ascii=False, indent=2)
    print(f"  Aktualisiert: {concepts_updated} Einträge")
    
    print("\n" + "=" * 50)
    print("=== FERTIG ===")
    print(f"Mapping: {len(all_mappings)} IDs")
    print(f"Summary-DB: {summary_updated} aktualisiert")
    print(f"Keywords-DB: {keywords_updated} aktualisiert")
    print(f"Concepts-DB: {concepts_updated} aktualisiert")

if __name__ == '__main__':
    main()
