# -*- coding: utf-8 -*-
import json

# IDs aus summary-database
with open('summary-database.json', 'r', encoding='utf-8') as f:
    summary_db = json.load(f)

# IDs aus neuer Datei
with open('steiner-full-lectures/steiner-full-lectures-212-212.json', 'r', encoding='utf-8') as f:
    new_data = json.load(f)

# Sammle alle neuen IDs
new_ids = set()
for lec in new_data.get('lectures', []):
    if lec.get('ID', '').startswith('GA212/'):
        for p in lec.get('paragraphs', []):
            idx = p.get('index', '')
            if idx:
                new_ids.add(idx)

# Finde fehlende TOC-IDs
print("Fehlende TOC-IDs:")
for lec_id in sorted(summary_db.keys()):
    if not lec_id.startswith('GA212/'):
        continue
    
    entry = summary_db[lec_id]
    toc = entry.get('tableOfContents', [])
    
    for h in toc:
        idx = h.get('index', '')
        if idx and idx not in new_ids:
            heading = h.get('heading', '')[:50]
            print(f"  {lec_id}: {idx} - {heading}")
