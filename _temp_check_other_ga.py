# -*- coding: utf-8 -*-
"""
Prüft ob IDs in keywords-database und summary-database 
mit den exportierten JSON-Dateien übereinstimmen.
"""
import json
import os
import glob

def load_lecture_ids(json_file):
    """Lädt alle Paragraph-IDs aus einer Lecture-JSON-Datei."""
    ids = {}
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        lectures = data.get('lectures', [])
        for lec in lectures:
            lec_id = lec.get('ID', lec.get('lectureId', ''))
            if lec_id:
                para_ids = set()
                for p in lec.get('paragraphs', []):
                    idx = p.get('index', '')
                    if idx:
                        para_ids.add(idx)
                ids[lec_id] = para_ids
    except Exception as e:
        print(f"  Fehler bei {json_file}: {e}")
    return ids

# Lade alle Lecture-IDs aus steiner-full-lectures
print("=== Lade alle exportierten Lecture-Dateien ===")
all_lecture_ids = {}

lecture_files = glob.glob("steiner-full-lectures/steiner-full-lectures-*.json")
for f in lecture_files:
    ids = load_lecture_ids(f)
    all_lecture_ids.update(ids)
    
print(f"Geladen: {len(all_lecture_ids)} Vorträge")

# Prüfe summary-database
print("\n=== Prüfe summary-database.json ===")
with open('summary-database.json', 'r', encoding='utf-8') as f:
    summary_db = json.load(f)

# Prüfe einige GA-Bände (nicht GA212)
test_gas = ['GA210', 'GA211', 'GA209', 'GA208', 'GA207', 'GA206', 'GA205']
for ga in test_gas:
    total = 0
    found = 0
    missing = []
    
    for lec_id in summary_db:
        if not lec_id.startswith(ga + '/'):
            continue
        
        if lec_id not in all_lecture_ids:
            continue
        
        lecture_ids = all_lecture_ids[lec_id]
        toc = summary_db[lec_id].get('tableOfContents', [])
        
        for h in toc:
            idx = h.get('index', '')
            if idx:
                total += 1
                if idx in lecture_ids:
                    found += 1
                else:
                    missing.append((lec_id, idx))
    
    if total > 0:
        pct = (found / total) * 100
        print(f"{ga}: {found}/{total} TOC-IDs gefunden ({pct:.0f}%)")
        if missing and len(missing) <= 3:
            for m in missing:
                print(f"    Fehlt: {m[0]} -> {m[1]}")

# Prüfe keywords-database
print("\n=== Prüfe keywords-database.json ===")
with open('keywords-database.json', 'r', encoding='utf-8') as f:
    keywords_db = json.load(f)

for ga in test_gas:
    total = 0
    found = 0
    
    for lec_id in keywords_db:
        if not lec_id.startswith(ga + '/'):
            continue
        
        if lec_id not in all_lecture_ids:
            continue
        
        lecture_ids = all_lecture_ids[lec_id]
        keywords = keywords_db[lec_id].get('keywords', [])
        
        for kw in keywords:
            idx = kw.get('index', '')
            if idx:
                total += 1
                if idx in lecture_ids:
                    found += 1
    
    if total > 0:
        pct = (found / total) * 100
        print(f"{ga}: {found}/{total} Keyword-IDs gefunden ({pct:.0f}%)")
