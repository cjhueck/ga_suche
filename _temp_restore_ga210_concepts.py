#!/usr/bin/env python3
"""
Versucht, die alten GA210-IDs in Concepts durch neue IDs zu ersetzen.

Strategie:
1. Sammle alle alten GA210-IDs aus dem Concepts-Backup
2. Für jede alte ID: Finde den zugehörigen Text im Vortrag
3. Matche den Text mit den neuen Paragraphen
4. Erstelle Mapping alte ID -> neue ID
5. Aktualisiere die concepts-database
"""

import json
import re
from difflib import SequenceMatcher
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def text_similarity(a, b):
    """Berechnet Textähnlichkeit zwischen 0 und 1"""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def extract_ga210_ids_from_concepts(concepts_backup):
    """Extrahiert alle GA210-IDs aus dem Concepts-Backup"""
    ga210_pattern = re.compile(r'\(GA210/(\d+):\^?([a-z0-9]+)\)', re.IGNORECASE)
    ga210_source_pattern = re.compile(r'^GA210/(\d+)$', re.IGNORECASE)
    
    old_ids = {}  # {(lecture_num, old_id): [(concept_keyword, field, full_ref)]}
    
    for concept in concepts_backup:
        keyword = concept.get('keyword', 'Unbekannt')
        
        # Prüfe Text-Felder
        for field in ['text', 'definitionText', 'functionText', 'interactionText', 'specialText']:
            # Hauptebene
            if field in concept and concept[field]:
                for match in ga210_pattern.finditer(concept[field]):
                    lecture_num = match.group(1)
                    old_id = match.group(2)
                    key = (lecture_num, old_id)
                    if key not in old_ids:
                        old_ids[key] = []
                    old_ids[key].append((keyword, field, match.group(0)))
            
            # Overview-Ebene
            overview = concept.get('overview', {})
            if isinstance(overview, dict) and field in overview and overview[field]:
                for match in ga210_pattern.finditer(overview[field]):
                    lecture_num = match.group(1)
                    old_id = match.group(2)
                    key = (lecture_num, old_id)
                    if key not in old_ids:
                        old_ids[key] = []
                    old_ids[key].append((keyword, f'overview.{field}', match.group(0)))
        
        # Prüfe sources
        for source in concept.get('sources', []):
            sid = source.get('id', '')
            match = ga210_source_pattern.match(sid)
            if match:
                lecture_num = match.group(1)
                old_id = source.get('index', '').lstrip('^')
                if old_id:
                    key = (lecture_num, old_id)
                    if key not in old_ids:
                        old_ids[key] = []
                    old_ids[key].append((keyword, 'source', f"{sid}:{old_id}"))
    
    return old_ids

def build_new_paragraph_index(lectures_json):
    """Baut einen Index der neuen Paragraphen"""
    new_paragraphs = {}  # {lecture_num: [(new_id, text, position)]}
    
    for lecture in lectures_json.get('lectures', []):
        lecture_id = lecture.get('ID', '')
        match = re.match(r'GA210/(\d+)', lecture_id, re.IGNORECASE)
        if not match:
            continue
        
        lecture_num = match.group(1)
        paragraphs = lecture.get('paragraphs', [])
        
        new_paragraphs[lecture_num] = []
        for i, para in enumerate(paragraphs):
            new_id = para.get('index', '').lstrip('^')
            text = para.get('content', '')
            if new_id and text:
                new_paragraphs[lecture_num].append((new_id, text, i))
    
    return new_paragraphs

def build_old_heading_index(keywords_backup):
    """Baut einen Index der alten Headings aus dem Keywords-Backup"""
    old_headings = {}  # {(lecture_num, old_id): heading}
    
    for lecture_id, data in keywords_backup.items():
        match = re.match(r'GA210/(\d+)', lecture_id, re.IGNORECASE)
        if not match:
            continue
        
        lecture_num = match.group(1)
        
        for kw in data.get('keywords', []):
            old_id = kw.get('index', '').lstrip('^')
            heading = kw.get('heading', '')
            if old_id and heading:
                old_headings[(lecture_num, old_id)] = heading
    
    return old_headings

def find_best_match(lecture_num, old_id, old_headings, new_paragraphs, new_summary_db):
    """Findet die beste neue ID für eine alte ID"""
    
    # Strategie 1: Heading-Match über neue summary-database
    old_heading = old_headings.get((lecture_num, old_id), '')
    
    if old_heading:
        # Suche in neuer summary-database nach ähnlichem Heading
        lecture_key = f"GA210/{lecture_num}"
        if lecture_key in new_summary_db:
            toc = new_summary_db[lecture_key].get('tableOfContents', [])
            best_match = None
            best_score = 0
            
            for entry in toc:
                new_heading = entry.get('heading', '')
                new_id = entry.get('index', '').lstrip('^')
                
                if not new_heading or not new_id:
                    continue
                
                score = text_similarity(old_heading, new_heading)
                if score > best_score and score > 0.6:
                    best_score = score
                    best_match = (new_id, new_heading, score, 'heading-match')
            
            if best_match:
                return best_match
    
    # Strategie 2: Position-basiertes Matching (falls keine bessere Option)
    # Suche nach ähnlicher Position im Vortrag
    if lecture_num in new_paragraphs:
        paras = new_paragraphs[lecture_num]
        # Keine gute Strategie ohne alte Texte
        pass
    
    return None

def main():
    print("=" * 70)
    print("  GA210 CONCEPT-IDs WIEDERHERSTELLEN")
    print("=" * 70)
    
    # Lade Dateien
    print("\n[1/5] Lade Dateien...")
    
    concepts_backup = load_json(PROJECT_ROOT / '_backups/concepts-database_20260203_103725.json')
    keywords_backup = load_json(PROJECT_ROOT / '_backups/keywords-database_20260203_103725.json')
    new_lectures = load_json(PROJECT_ROOT / 'steiner-full-lectures/steiner-full-lectures-210-210.json')
    new_summary_db = load_json(PROJECT_ROOT / 'summary-database.json')
    current_concepts = load_json(PROJECT_ROOT / 'concepts-database.json')
    
    print(f"  Concepts-Backup: {len(concepts_backup)} Eintraege")
    print(f"  Keywords-Backup: {len(keywords_backup)} Eintraege")
    print(f"  Neue Vortraege: {len(new_lectures.get('lectures', []))}")
    
    # Extrahiere alte IDs
    print("\n[2/5] Extrahiere alte GA210-IDs aus Concepts...")
    old_ids = extract_ga210_ids_from_concepts(concepts_backup)
    print(f"  Gefunden: {len(old_ids)} eindeutige alte IDs")
    
    # Baue Indizes
    print("\n[3/5] Baue Indizes...")
    new_paragraphs = build_new_paragraph_index(new_lectures)
    old_headings = build_old_heading_index(keywords_backup)
    print(f"  Alte Headings: {len(old_headings)}")
    print(f"  Neue Paragraphen pro Vortrag: {[(k, len(v)) for k, v in sorted(new_paragraphs.items())]}")
    
    # Finde Mappings
    print("\n[4/5] Finde ID-Mappings...")
    mappings = {}  # {(lecture_num, old_id): (new_id, method, score)}
    no_match = []
    
    for (lecture_num, old_id), refs in old_ids.items():
        result = find_best_match(lecture_num, old_id, old_headings, new_paragraphs, new_summary_db)
        
        if result:
            new_id, matched_text, score, method = result
            mappings[(lecture_num, old_id)] = (new_id, method, score)
            print(f"  GA210/{lecture_num}:^{old_id} -> ^{new_id} ({method}, {score:.0%})")
        else:
            no_match.append((lecture_num, old_id, refs))
    
    print(f"\n  Erfolgreich gemappt: {len(mappings)}")
    print(f"  Nicht gefunden: {len(no_match)}")
    
    if no_match:
        print("\n  Nicht gefundene IDs:")
        for lecture_num, old_id, refs in no_match[:10]:
            print(f"    GA210/{lecture_num}:^{old_id}")
            for kw, field, ref in refs[:2]:
                print(f"      - {kw} ({field})")
        if len(no_match) > 10:
            print(f"    ... und {len(no_match) - 10} weitere")
    
    # Zeige Mapping-Zusammenfassung
    print("\n" + "=" * 70)
    print("  MAPPING-ZUSAMMENFASSUNG")
    print("=" * 70)
    
    print(f"\n  Alte IDs gesamt: {len(old_ids)}")
    print(f"  Erfolgreich gemappt: {len(mappings)}")
    print(f"  Match-Rate: {len(mappings)/len(old_ids)*100:.1f}%" if old_ids else "N/A")
    
    if mappings:
        print("\n  Alle gefundenen Mappings:")
        for (lecture_num, old_id), (new_id, method, score) in sorted(mappings.items()):
            print(f"    GA210/{lecture_num}: ^{old_id} -> ^{new_id} ({score:.0%})")
    
    return mappings, no_match, old_ids

if __name__ == '__main__':
    main()
