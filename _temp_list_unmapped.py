#!/usr/bin/env python3
"""Listet alle Concepts mit nicht-mappbaren GA210-Referenzen auf"""

import json
import re
from difflib import SequenceMatcher

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_text(text):
    if not text:
        return ""
    text = text.replace('\ufeff', '').strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def text_similarity(a, b):
    a = normalize_text(a)
    b = normalize_text(b)
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Lade Daten
old_data = load_json(r"D:\steiner-full-lectures\steiner-full-lectures-001-354-part12.json")
new_data = load_json(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\steiner-full-lectures\steiner-full-lectures-210-210.json")
concepts_backup = load_json(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\_backups\concepts-database_20260203_103725.json")

# Extrahiere alte Paragraphen
old_paragraphs = {}
for lecture in old_data.get('lectures', []):
    lid = lecture.get('ID', '')
    match = re.match(r'GA210/(\d+)', lid, re.IGNORECASE)
    if match:
        lecture_num = match.group(1)
        old_paragraphs[lecture_num] = {}
        for para in lecture.get('paragraphs', []):
            para_id = para.get('index', '').lstrip('^')
            text = para.get('content', '')
            if para_id:
                old_paragraphs[lecture_num][para_id] = text

# Extrahiere neue Paragraphen
new_paragraphs = {}
for lecture in new_data.get('lectures', []):
    lid = lecture.get('ID', '')
    match = re.match(r'GA210/(\d+)', lid, re.IGNORECASE)
    if match:
        lecture_num = match.group(1)
        new_paragraphs[lecture_num] = []
        for para in lecture.get('paragraphs', []):
            para_id = para.get('index', '').lstrip('^')
            text = para.get('content', '')
            if para_id:
                new_paragraphs[lecture_num].append((para_id, text))

# Baue Mapping (mit niedriger Schwelle)
mapping = {}
for lecture_num, paras in old_paragraphs.items():
    if lecture_num not in new_paragraphs:
        continue
    for old_id, old_text in paras.items():
        best_score = 0
        best_new_id = None
        for new_id, new_text in new_paragraphs.get(lecture_num, []):
            score = text_similarity(old_text, new_text)
            if score > best_score:
                best_score = score
                best_new_id = new_id
        if best_score >= 0.5:
            mapping[(lecture_num, old_id)] = (best_new_id, best_score)

# Extrahiere GA210-Referenzen aus Concepts
ga210_pattern = re.compile(r'\(GA210/(\d+):\^?([a-z0-9]+)\)', re.IGNORECASE)
ga210_source_pattern = re.compile(r'^GA210/(\d+)$', re.IGNORECASE)

unmapped_concepts = {}  # {concept_keyword: [(lecture_num, old_id, field, old_text_preview)]}

for concept in concepts_backup:
    keyword = concept.get('keyword', '')
    unmapped_refs = []
    
    # Text-Felder pruefen
    for field in ['text', 'definitionText', 'functionText', 'interactionText', 'specialText']:
        if field in concept and concept[field]:
            for match in ga210_pattern.finditer(concept[field]):
                lecture_num = match.group(1)
                old_id = match.group(2)
                if (lecture_num, old_id) not in mapping:
                    old_text = old_paragraphs.get(lecture_num, {}).get(old_id, '')
                    preview = old_text[:100].replace('\n', ' ') if old_text else '(Text nicht gefunden)'
                    unmapped_refs.append((lecture_num, old_id, field, preview))
        
        overview = concept.get('overview', {})
        if isinstance(overview, dict) and field in overview and overview[field]:
            for match in ga210_pattern.finditer(overview[field]):
                lecture_num = match.group(1)
                old_id = match.group(2)
                if (lecture_num, old_id) not in mapping:
                    old_text = old_paragraphs.get(lecture_num, {}).get(old_id, '')
                    preview = old_text[:100].replace('\n', ' ') if old_text else '(Text nicht gefunden)'
                    unmapped_refs.append((lecture_num, old_id, f'overview.{field}', preview))
    
    # Sources pruefen
    for source in concept.get('sources', []):
        sid = source.get('id', '')
        match = ga210_source_pattern.match(sid)
        if match:
            lecture_num = match.group(1)
            old_id = source.get('index', '').lstrip('^')
            if old_id and (lecture_num, old_id) not in mapping:
                old_text = old_paragraphs.get(lecture_num, {}).get(old_id, '')
                preview = old_text[:100].replace('\n', ' ') if old_text else '(Text nicht gefunden)'
                unmapped_refs.append((lecture_num, old_id, 'source', preview))
    
    if unmapped_refs:
        unmapped_concepts[keyword] = unmapped_refs

# Ausgabe
print("=" * 80)
print("  CONCEPTS MIT NICHT-MAPPBAREN GA210-REFERENZEN")
print("=" * 80)
print(f"\nGesamt: {len(unmapped_concepts)} Concepts betroffen\n")

for i, (keyword, refs) in enumerate(sorted(unmapped_concepts.items()), 1):
    safe_keyword = keyword.encode('ascii', 'replace').decode('ascii')
    print(f"{i}. {safe_keyword}")
    
    # Gruppiere nach ID um Duplikate zu vermeiden
    seen = set()
    for lecture_num, old_id, field, preview in refs:
        key = (lecture_num, old_id)
        if key not in seen:
            seen.add(key)
            safe_preview = preview[:80].encode('ascii', 'replace').decode('ascii')
            print(f"   - GA210/{lecture_num}:^{old_id} ({field})")
            print(f"     Text: \"{safe_preview}...\"")
    print()

# Zusammenfassung nach Vortrag
print("=" * 80)
print("  ZUSAMMENFASSUNG NACH VORTRAG")
print("=" * 80)
all_ids = set()
for refs in unmapped_concepts.values():
    for lecture_num, old_id, field, preview in refs:
        all_ids.add((lecture_num, old_id))

by_lecture = {}
for lecture_num, old_id in all_ids:
    if lecture_num not in by_lecture:
        by_lecture[lecture_num] = []
    by_lecture[lecture_num].append(old_id)

print(f"\nEindeutige nicht-mappbare IDs: {len(all_ids)}\n")
for lecture_num in sorted(by_lecture.keys(), key=int):
    ids = by_lecture[lecture_num]
    print(f"GA210/{lecture_num}: {len(ids)} IDs")
    for old_id in ids[:3]:
        print(f"  - ^{old_id}")
    if len(ids) > 3:
        print(f"  - ... und {len(ids)-3} weitere")
