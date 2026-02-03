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

print(f"Neue IDs insgesamt: {len(new_ids)}")

# Prüfe GA212 Einträge in summary-database
total_toc = 0
matched_toc = 0

for lec_id in summary_db:
    if not lec_id.startswith('GA212/'):
        continue
    
    entry = summary_db[lec_id]
    toc = entry.get('tableOfContents', [])
    
    for h in toc:
        idx = h.get('index', '')
        total_toc += 1
        if idx in new_ids:
            matched_toc += 1

print(f"\nTableOfContents Einträge: {total_toc}")
print(f"Davon in neuer Datei gefunden: {matched_toc}")
print(f"Nicht gefunden: {total_toc - matched_toc}")
