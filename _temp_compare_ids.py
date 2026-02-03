# -*- coding: utf-8 -*-
import json

# IDs aus summary-database
with open('summary-database.json', 'r', encoding='utf-8') as f:
    summary_db = json.load(f)

toc = summary_db.get('GA212/1', {}).get('tableOfContents', [])
summary_ids = [h.get('index', '') for h in toc[:5]]
print("IDs in summary-database.json (GA212/1 TOC):")
for idx in summary_ids:
    print(f"  {idx}")

# IDs aus alter Datei auf D:
print("\nIDs in alter Datei (D:):")
with open(r'D:\steiner-full-lectures\steiner-full-lectures-001-354-part12.json', 'r', encoding='utf-8') as f:
    old_data = json.load(f)

for lec in old_data.get('lectures', []):
    if lec.get('ID') == 'GA212/1':
        paras = lec.get('paragraphs', [])
        for p in paras[:5]:
            print(f"  {p.get('index', '')}")
        break

# IDs aus neuer Datei
print("\nIDs in neuer Datei:")
with open('steiner-full-lectures/steiner-full-lectures-212-212.json', 'r', encoding='utf-8') as f:
    new_data = json.load(f)

for lec in new_data.get('lectures', []):
    if lec.get('ID') == 'GA212/1':
        paras = lec.get('paragraphs', [])
        for p in paras[:5]:
            print(f"  {p.get('index', '')}")
        break
