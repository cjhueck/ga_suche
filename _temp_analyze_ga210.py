#!/usr/bin/env python3
"""Temporäres Analyse-Skript für GA210 IDs"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(r'c:\Users\chuec\OneDrive\GitHub\ga_suche')

print('=' * 70)
print('  GA210 ID-ANALYSE')
print('=' * 70)

# 1. Lade aktuelle IDs aus JSON für GA210
current_ids = {}  # { lecture_id: set(ids) }
current_content = {}  # { lecture_id: { id: content } }

# Suche in allen steiner-full-lectures Dateien
search_paths = list(PROJECT_ROOT.glob('steiner-full-lectures-*.json'))
lectures_dir = PROJECT_ROOT / 'steiner-full-lectures'
if lectures_dir.exists():
    search_paths.extend(lectures_dir.glob('*.json'))

for json_file in search_paths:
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for lecture in data.get('lectures', []):
            lecture_id = lecture.get('ID', '')
            if not lecture_id.upper().startswith('GA210'):
                continue
            
            ids = set()
            content_map = {}
            for para in lecture.get('paragraphs', []):
                idx = para.get('index', '')
                content = para.get('content', '')
                if idx:
                    idx_clean = idx if idx.startswith('^') else f'^{idx}'
                    ids.add(idx_clean)
                    content_map[idx_clean] = content[:100]  # Nur erste 100 Zeichen
            
            if ids:
                current_ids[lecture_id] = ids
                current_content[lecture_id] = content_map
    except Exception as e:
        print(f"Fehler bei {json_file}: {e}")

print(f'\n[AKTUELLE JSON-DATEN]')
print(f'  Vorträge gefunden: {len(current_ids)}')
total_ids = sum(len(ids) for ids in current_ids.values())
print(f'  Gesamt IDs: {total_ids}')

# Zeige die ersten IDs pro Vortrag
for lid in sorted(current_ids.keys())[:3]:
    ids_list = sorted(list(current_ids[lid]))[:5]
    print(f'  {lid}: {ids_list}...')

# 2. Lade Keywords für GA210
print(f'\n[KEYWORDS-DATABASE]')
kw_db_path = PROJECT_ROOT / 'keywords-database.json'

if not kw_db_path.exists():
    print("  keywords-database.json nicht gefunden!")
else:
    with open(kw_db_path, 'r', encoding='utf-8') as f:
        kw_db = json.load(f)
    
    ga210_keywords = {k: v for k, v in kw_db.items() if k.upper().startswith('GA210')}
    print(f'  GA210 Einträge: {len(ga210_keywords)}')
    
    # Prüfe welche IDs nicht mehr existieren
    broken_kw = []
    valid_kw = 0
    
    for lecture_id, kw_data in ga210_keywords.items():
        current = current_ids.get(lecture_id, set())
        
        for kw in kw_data.get('keywords', []):
            idx = kw.get('index', '')
            idx_clean = idx if idx.startswith('^') else f'^{idx}'
            
            if idx_clean in current:
                valid_kw += 1
            else:
                broken_kw.append({
                    'lecture_id': lecture_id,
                    'index': idx,
                    'term': kw.get('term', ''),
                    'heading': kw.get('heading', '')[:60] if kw.get('heading') else ''
                })
    
    print(f'  Gültige IDs: {valid_kw}')
    print(f'  Ungültige IDs: {len(broken_kw)}')
    
    if broken_kw:
        print(f'\n[UNGÜLTIGE KEYWORD-REFERENZEN - GA210]')
        print('-' * 70)
        for i, bk in enumerate(broken_kw[:15]):
            print(f'{i+1}. Vortrag: {bk["lecture_id"]}')
            print(f'   Alte ID: {bk["index"]}')
            print(f'   Keyword: {bk["term"]}')
            if bk["heading"]:
                print(f'   Heading: {bk["heading"]}...')
            print()

# 3. Lade Concepts für GA210
print(f'\n[CONCEPTS-DATABASE]')
concepts_db_path = PROJECT_ROOT / 'concepts-database.json'

if not concepts_db_path.exists():
    print("  concepts-database.json nicht gefunden!")
else:
    with open(concepts_db_path, 'r', encoding='utf-8') as f:
        concepts_db = json.load(f)
    
    # Suche nach GA210 Referenzen in Concepts
    # Pattern: (GA210/5:^abc123) oder GA210/5:abc123
    ga210_pattern = re.compile(r'GA210/(\d+):\^?([a-z0-9]+)')
    
    broken_concepts = []
    valid_concepts = 0
    
    for concept in concepts_db:
        keyword = concept.get('keyword', '')
        
        # Durchsuche alle Text-Felder
        all_text = ''
        for field in ['text', 'definitionText', 'functionText', 'interactionText', 'specialText']:
            all_text += concept.get(field, '') + ' '
            overview = concept.get('overview', {})
            if isinstance(overview, dict):
                all_text += overview.get(field, '') + ' '
        
        # Finde alle GA210 Referenzen
        matches = ga210_pattern.findall(all_text)
        
        for lecture_num, ref_id in matches:
            lecture_id = f'GA210/{lecture_num}'
            idx_clean = f'^{ref_id}'
            
            current = current_ids.get(lecture_id, set())
            
            if idx_clean in current:
                valid_concepts += 1
            else:
                broken_concepts.append({
                    'concept': keyword,
                    'lecture_id': lecture_id,
                    'index': idx_clean
                })
        
        # Prüfe auch sources
        for source in concept.get('sources', []):
            source_id = source.get('id', '')
            if source_id.upper().startswith('GA210'):
                idx = source.get('index', '')
                idx_clean = idx if idx.startswith('^') else f'^{idx}'
                
                current = current_ids.get(source_id, set())
                if idx_clean in current:
                    valid_concepts += 1
                else:
                    broken_concepts.append({
                        'concept': keyword,
                        'lecture_id': source_id,
                        'index': idx_clean
                    })
    
    print(f'  Gültige GA210 Referenzen: {valid_concepts}')
    print(f'  Ungültige GA210 Referenzen: {len(broken_concepts)}')
    
    if broken_concepts:
        print(f'\n[UNGÜLTIGE CONCEPT-REFERENZEN - GA210]')
        print('-' * 70)
        # Dedupliziere
        seen = set()
        unique_broken = []
        for bc in broken_concepts:
            key = (bc['concept'], bc['lecture_id'], bc['index'])
            if key not in seen:
                seen.add(key)
                unique_broken.append(bc)
        
        for i, bc in enumerate(unique_broken[:15]):
            print(f'{i+1}. Concept: {bc["concept"]}')
            print(f'   Vortrag: {bc["lecture_id"]}')
            print(f'   Alte ID: {bc["index"]}')
            print()

print('=' * 70)
print('  ANALYSE ABGESCHLOSSEN')
print('=' * 70)
