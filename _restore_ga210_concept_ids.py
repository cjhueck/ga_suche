#!/usr/bin/env python3
"""
Stellt die GA210-Concept-IDs wieder her durch Text-Matching zwischen
alten und neuen Paragraphen.

Strategie:
1. Lade alte GA210-Paragraphen von D:\steiner-full-lectures
2. Lade neue GA210-Paragraphen aus aktuellem Projekt
3. Matche Texte um alte ID -> neue ID Mapping zu erstellen
4. Aktualisiere concepts-database.json mit neuen IDs
"""

import json
import re
import shutil
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

# Pfade
PROJECT_ROOT = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche")
OLD_LECTURES_FILE = Path(r"D:\steiner-full-lectures\steiner-full-lectures-001-354-part12.json")
NEW_LECTURES_FILE = PROJECT_ROOT / "steiner-full-lectures" / "steiner-full-lectures-210-210.json"
CONCEPTS_FILE = PROJECT_ROOT / "concepts-database.json"
CONCEPTS_BACKUP = PROJECT_ROOT / "_backups" / "concepts-database_20260203_103725.json"
BACKUP_DIR = PROJECT_ROOT / "_backups"

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def normalize_text(text):
    """Normalisiert Text für Vergleich"""
    if not text:
        return ""
    # Entferne BOM, Whitespace normalisieren
    text = text.replace('\ufeff', '').strip()
    # Mehrfache Leerzeichen entfernen
    text = re.sub(r'\s+', ' ', text)
    return text

def text_similarity(a, b):
    """Berechnet Textähnlichkeit zwischen 0 und 1"""
    a = normalize_text(a)
    b = normalize_text(b)
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def extract_ga210_paragraphs(lectures_data):
    """Extrahiert alle GA210-Paragraphen"""
    paragraphs = {}  # {lecture_num: [(id, text, position)]}
    
    for lecture in lectures_data.get('lectures', []):
        lid = lecture.get('ID', '')
        match = re.match(r'GA210/(\d+)', lid, re.IGNORECASE)
        if not match:
            continue
        
        lecture_num = match.group(1)
        paragraphs[lecture_num] = []
        
        for i, para in enumerate(lecture.get('paragraphs', [])):
            para_id = para.get('index', '').lstrip('^')
            text = para.get('content', '')
            if para_id:
                paragraphs[lecture_num].append((para_id, text, i))
    
    return paragraphs

def build_id_mapping(old_paragraphs, new_paragraphs):
    """Erstellt Mapping alte ID -> neue ID durch Text-Matching"""
    mapping = {}  # {(lecture_num, old_id): (new_id, similarity, old_text_preview)}
    
    for lecture_num, old_paras in old_paragraphs.items():
        if lecture_num not in new_paragraphs:
            print(f"  WARNUNG: Vortrag GA210/{lecture_num} nicht in neuen Daten")
            continue
        
        new_paras = new_paragraphs[lecture_num]
        
        for old_id, old_text, old_pos in old_paras:
            best_match = None
            best_score = 0
            
            # Suche besten Match in neuen Paragraphen
            for new_id, new_text, new_pos in new_paras:
                score = text_similarity(old_text, new_text)
                if score > best_score:
                    best_score = score
                    best_match = (new_id, new_text, new_pos)
            
            if best_match and best_score > 0.5:  # Mindestens 50% Ähnlichkeit
                new_id, new_text, new_pos = best_match
                preview = old_text[:50].replace('\n', ' ') if old_text else ""
                mapping[(lecture_num, old_id)] = (new_id, best_score, preview)
    
    return mapping

def extract_ga210_ids_from_concepts(concepts):
    """Extrahiert alle GA210-Referenzen aus Concepts"""
    ga210_pattern = re.compile(r'\(GA210/(\d+):\^?([a-z0-9]+)\)', re.IGNORECASE)
    ga210_source_pattern = re.compile(r'^GA210/(\d+)$', re.IGNORECASE)
    
    refs = []  # [(concept_keyword, field, lecture_num, old_id, full_match)]
    
    for concept in concepts:
        keyword = concept.get('keyword', '')
        
        # Text-Felder prüfen
        for field in ['text', 'definitionText', 'functionText', 'interactionText', 'specialText']:
            # Hauptebene
            if field in concept and concept[field]:
                for match in ga210_pattern.finditer(concept[field]):
                    refs.append((keyword, field, match.group(1), match.group(2), match.group(0)))
            
            # Overview
            overview = concept.get('overview', {})
            if isinstance(overview, dict) and field in overview and overview[field]:
                for match in ga210_pattern.finditer(overview[field]):
                    refs.append((keyword, f'overview.{field}', match.group(1), match.group(2), match.group(0)))
        
        # Sources prüfen
        for source in concept.get('sources', []):
            sid = source.get('id', '')
            match = ga210_source_pattern.match(sid)
            if match:
                old_id = source.get('index', '').lstrip('^')
                if old_id:
                    refs.append((keyword, 'source', match.group(1), old_id, None))
    
    return refs

def update_concepts_with_mapping(concepts, mapping):
    """Aktualisiert Concepts mit neuen IDs"""
    ga210_pattern = re.compile(r'\(GA210/(\d+):\^?([a-z0-9]+)\)', re.IGNORECASE)
    ga210_source_pattern = re.compile(r'^GA210/(\d+)$', re.IGNORECASE)
    
    updated_count = 0
    not_found = []
    
    for concept in concepts:
        keyword = concept.get('keyword', '')
        
        # Text-Felder aktualisieren
        for field in ['text', 'definitionText', 'functionText', 'interactionText', 'specialText']:
            # Hauptebene
            if field in concept and concept[field]:
                original = concept[field]
                
                def replace_ref(match):
                    lecture_num = match.group(1)
                    old_id = match.group(2)
                    key = (lecture_num, old_id)
                    if key in mapping:
                        new_id, score, _ = mapping[key]
                        return f"(GA210/{lecture_num}:^{new_id})"
                    else:
                        not_found.append((keyword, field, lecture_num, old_id))
                        return match.group(0)  # Unverändert lassen
                
                concept[field] = ga210_pattern.sub(replace_ref, original)
                if concept[field] != original:
                    updated_count += 1
            
            # Overview
            overview = concept.get('overview', {})
            if isinstance(overview, dict) and field in overview and overview[field]:
                original = overview[field]
                overview[field] = ga210_pattern.sub(replace_ref, original)
                if overview[field] != original:
                    updated_count += 1
        
        # Sources aktualisieren
        for source in concept.get('sources', []):
            sid = source.get('id', '')
            match = ga210_source_pattern.match(sid)
            if match:
                lecture_num = match.group(1)
                old_id = source.get('index', '').lstrip('^')
                if old_id:
                    key = (lecture_num, old_id)
                    if key in mapping:
                        new_id, score, _ = mapping[key]
                        source['index'] = f"^{new_id}"
                        updated_count += 1
                    else:
                        not_found.append((keyword, 'source', lecture_num, old_id))
    
    return updated_count, not_found

def main():
    print("=" * 70)
    print("  GA210 CONCEPT-IDs WIEDERHERSTELLEN")
    print("=" * 70)
    
    # 1. Lade Daten
    print("\n[1/5] Lade Daten...")
    
    old_lectures = load_json(OLD_LECTURES_FILE)
    new_lectures = load_json(NEW_LECTURES_FILE)
    concepts_backup = load_json(CONCEPTS_BACKUP)
    
    print(f"  Alte Vortraege: {OLD_LECTURES_FILE.name}")
    print(f"  Neue Vortraege: {NEW_LECTURES_FILE.name}")
    print(f"  Concepts-Backup: {CONCEPTS_BACKUP.name}")
    
    # 2. Extrahiere Paragraphen
    print("\n[2/5] Extrahiere Paragraphen...")
    
    old_paragraphs = extract_ga210_paragraphs(old_lectures)
    new_paragraphs = extract_ga210_paragraphs(new_lectures)
    
    old_count = sum(len(v) for v in old_paragraphs.values())
    new_count = sum(len(v) for v in new_paragraphs.values())
    print(f"  Alte Paragraphen: {old_count}")
    print(f"  Neue Paragraphen: {new_count}")
    
    # 3. Erstelle ID-Mapping
    print("\n[3/5] Erstelle ID-Mapping durch Text-Matching...")
    
    mapping = build_id_mapping(old_paragraphs, new_paragraphs)
    print(f"  Erfolgreiche Mappings: {len(mapping)}")
    
    # Zeige einige Beispiele
    print("\n  Beispiel-Mappings:")
    for i, ((lecture_num, old_id), (new_id, score, preview)) in enumerate(list(mapping.items())[:5]):
        print(f"    GA210/{lecture_num}: ^{old_id} -> ^{new_id} ({score:.0%})")
        # Entferne problematische Unicode-Zeichen für Konsole
        safe_preview = preview.encode('ascii', 'replace').decode('ascii')
        print(f"      Text: {safe_preview}...")
    
    # 4. Finde betroffene Concepts
    print("\n[4/5] Analysiere Concepts...")
    
    refs = extract_ga210_ids_from_concepts(concepts_backup)
    unique_ids = set((r[2], r[3]) for r in refs)
    print(f"  GA210-Referenzen in Concepts: {len(refs)}")
    print(f"  Eindeutige alte IDs: {len(unique_ids)}")
    
    # Prüfe wie viele gemappt werden können
    mappable = sum(1 for (ln, oid) in unique_ids if (ln, oid) in mapping)
    print(f"  Davon mappbar: {mappable}")
    
    # 5. Aktualisiere Concepts
    print("\n[5/5] Aktualisiere Concepts...")
    
    # Erstelle Backup der aktuellen Concepts
    backup_name = f"concepts-database_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    backup_path = BACKUP_DIR / backup_name
    current_concepts = load_json(CONCEPTS_FILE)
    save_json(backup_path, current_concepts)
    print(f"  Backup erstellt: {backup_name}")
    
    # Aktualisiere mit dem Backup (das noch die alten Referenzen hat)
    updated_count, not_found = update_concepts_with_mapping(concepts_backup, mapping)
    
    # Speichern
    save_json(CONCEPTS_FILE, concepts_backup)
    
    print(f"\n  Aktualisierte Referenzen: {updated_count}")
    print(f"  Nicht gefundene IDs: {len(not_found)}")
    
    if not_found:
        print("\n  Nicht gemappte Referenzen:")
        shown = set()
        for keyword, field, lecture_num, old_id in not_found[:15]:
            key = (lecture_num, old_id)
            if key not in shown:
                shown.add(key)
                print(f"    GA210/{lecture_num}:^{old_id} ({keyword})")
        if len(set((ln, oid) for kw, f, ln, oid in not_found)) > 15:
            remaining = len(set((ln, oid) for kw, f, ln, oid in not_found)) - 15
            print(f"    ... und {remaining} weitere")
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("  ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"""
  ID-Mapping:
    - Alte Paragraphen: {old_count}
    - Neue Paragraphen: {new_count}
    - Erfolgreiche Mappings: {len(mapping)} ({len(mapping)/old_count*100:.1f}%)
    
  Concepts:
    - GA210-Referenzen gesamt: {len(refs)}
    - Aktualisiert: {updated_count}
    - Nicht gefunden: {len(set((ln, oid) for kw, f, ln, oid in not_found))} unique IDs
    
  Backup erstellt: {backup_path}
  Concepts aktualisiert: {CONCEPTS_FILE}
    """)

if __name__ == '__main__':
    main()
