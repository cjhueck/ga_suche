# -*- coding: utf-8 -*-
"""
Synchronisiert GA212-IDs zwischen alter und neuer Version.
Aktualisiert summary-database.json und keywords-database.json.
"""
import json
import os
import re
from difflib import SequenceMatcher
from datetime import datetime

def normalize_text(text):
    """Normalisiert Text für Vergleich."""
    if not text:
        return ""
    # Entferne Seitenmarker wie |13|
    text = re.sub(r'\|\d+\|', '', text)
    # Entferne überschüssige Leerzeichen
    text = ' '.join(text.split())
    return text.lower()[:500]  # Nur erste 500 Zeichen für Performance

def text_similarity(text1, text2):
    """Berechnet Ähnlichkeit zwischen zwei Texten."""
    t1 = normalize_text(text1)
    t2 = normalize_text(text2)
    if not t1 or not t2:
        return 0.0
    return SequenceMatcher(None, t1, t2).ratio()

def main():
    print("=== GA212 ID-Synchronisierung ===\n")
    
    # Alte GA212-Daten laden
    print("Lade alte GA212-Daten von D:...")
    old_file = r"D:\steiner-full-lectures\steiner-full-lectures-001-354-part12.json"
    with open(old_file, 'r', encoding='utf-8') as f:
        old_data = json.load(f)
    
    # Alte GA212-Vorträge extrahieren
    old_lectures = {}
    lectures_list = old_data.get('lectures', old_data) if isinstance(old_data, dict) else old_data
    if isinstance(lectures_list, dict):
        lectures_list = lectures_list.get('lectures', [])
    
    for lec in lectures_list:
        lec_id = lec.get('ID', lec.get('lectureId', ''))
        if lec_id.startswith('GA212/'):
            old_lectures[lec_id] = lec
            print(f"  Gefunden: {lec_id}")
    
    if not old_lectures:
        print("FEHLER: Keine GA212-Vorträge in alter Datei gefunden!")
        return
    
    # Neue GA212-Daten laden
    print("\nLade neue GA212-Daten...")
    new_file = "steiner-full-lectures/steiner-full-lectures-212-212.json"
    with open(new_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
    
    new_lectures = {}
    for lec in new_data.get('lectures', []):
        lec_id = lec.get('ID', '')
        if lec_id.startswith('GA212/'):
            new_lectures[lec_id] = lec
            print(f"  Gefunden: {lec_id}")
    
    # ID-Mapping erstellen (positionsbasiert + Textverifikation)
    print("\n=== Erstelle ID-Mapping ===")
    id_mapping = {}  # old_id -> new_id
    
    for lec_id in old_lectures:
        if lec_id not in new_lectures:
            print(f"  WARNUNG: {lec_id} nicht in neuer Datei!")
            continue
        
        old_paras = old_lectures[lec_id].get('paragraphs', [])
        new_paras = new_lectures[lec_id].get('paragraphs', [])
        
        print(f"{lec_id}: {len(old_paras)} alte -> {len(new_paras)} neue Absätze")
        
        # Positionsbasiertes Mapping mit Verifikation
        matched = 0
        low_score = 0
        for i, old_p in enumerate(old_paras):
            old_id = old_p.get('index', '')
            if not old_id:
                continue
            
            # Versuche gleiche Position zuerst
            if i < len(new_paras):
                new_p = new_paras[i]
                new_id = new_p.get('index', '')
                
                if new_id:
                    old_text = old_p.get('content', old_p.get('text', ''))
                    new_text = new_p.get('content', new_p.get('text', ''))
                    score = text_similarity(old_text, new_text)
                    
                    if score >= 0.5:
                        id_mapping[old_id] = new_id
                        matched += 1
                        if score < 0.8:
                            low_score += 1
        
        print(f"  -> {matched} gemappt ({low_score} mit niedrigem Score)")
    
    print(f"\n=== Mapping erstellt: {len(id_mapping)} IDs ===")
    
    # Backup erstellen
    backup_dir = "_backups"
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Summary-Database aktualisieren
    print("\n=== Aktualisiere summary-database.json ===")
    with open('summary-database.json', 'r', encoding='utf-8') as f:
        summary_db = json.load(f)
    
    # Backup
    backup_path = os.path.join(backup_dir, f"summary-database_{timestamp}.json")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(summary_db, f, ensure_ascii=False)
    print(f"  Backup: {backup_path}")
    
    summary_updated = 0
    for lec_id in list(summary_db.keys()):
        if not lec_id.startswith('GA212/'):
            continue
        
        entry = summary_db[lec_id]
        
        # tableOfContents aktualisieren
        toc = entry.get('tableOfContents', [])
        for item in toc:
            old_idx = item.get('index', '')
            if old_idx in id_mapping:
                item['index'] = id_mapping[old_idx]
                summary_updated += 1
        
        # headings aktualisieren (falls vorhanden)
        headings = entry.get('headings', [])
        for item in headings:
            old_idx = item.get('index', '')
            if old_idx in id_mapping:
                item['index'] = id_mapping[old_idx]
                summary_updated += 1
        
        # lectureKeywords aktualisieren (falls vorhanden)
        keywords = entry.get('lectureKeywords', [])
        for item in keywords:
            old_idx = item.get('index', '')
            if old_idx in id_mapping:
                item['index'] = id_mapping[old_idx]
                summary_updated += 1
    
    with open('summary-database.json', 'w', encoding='utf-8') as f:
        json.dump(summary_db, f, ensure_ascii=False, indent=2)
    print(f"  Aktualisiert: {summary_updated} Einträge")
    
    # Keywords-Database aktualisieren
    print("\n=== Aktualisiere keywords-database.json ===")
    with open('keywords-database.json', 'r', encoding='utf-8') as f:
        keywords_db = json.load(f)
    
    # Backup
    backup_path = os.path.join(backup_dir, f"keywords-database_{timestamp}.json")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(keywords_db, f, ensure_ascii=False)
    print(f"  Backup: {backup_path}")
    
    keywords_updated = 0
    for lec_id in list(keywords_db.keys()):
        if not lec_id.startswith('GA212/'):
            continue
        
        entry = keywords_db[lec_id]
        keywords = entry.get('keywords', [])
        for kw in keywords:
            old_idx = kw.get('index', '')
            if old_idx in id_mapping:
                kw['index'] = id_mapping[old_idx]
                keywords_updated += 1
    
    with open('keywords-database.json', 'w', encoding='utf-8') as f:
        json.dump(keywords_db, f, ensure_ascii=False, indent=2)
    print(f"  Aktualisiert: {keywords_updated} Einträge")
    
    print("\n=== Fertig! ===")
    print(f"Mapping: {len(id_mapping)} IDs")
    print(f"Summary-DB: {summary_updated} aktualisiert")
    print(f"Keywords-DB: {keywords_updated} aktualisiert")

if __name__ == '__main__':
    main()
