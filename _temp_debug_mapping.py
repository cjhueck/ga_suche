# -*- coding: utf-8 -*-
import json

# IDs in summary-database für GA205/1
with open('summary-database.json', 'r', encoding='utf-8') as f:
    summary_db = json.load(f)

toc = summary_db.get('GA205/1', {}).get('tableOfContents', [])
print("IDs in summary-database.json (GA205/1 TOC):")
for h in toc[:5]:
    print(f"  {h.get('index', '-')}")

# IDs in neuer exportierter Datei
print("\nIDs in neuer exportierter Datei (GA205/1):")
with open('steiner-full-lectures/steiner-full-lectures-205-205.json', 'r', encoding='utf-8') as f:
    new_data = json.load(f)

for lec in new_data.get('lectures', []):
    if lec.get('ID') == 'GA205/1':
        for p in lec.get('paragraphs', [])[:5]:
            print(f"  {p.get('index', '-')}")
        break

# IDs in alter Datei auf D:
print("\nIDs in alter Datei auf D: (GA205/1):")
with open(r'D:\steiner-full-lectures\steiner-full-lectures-205-205.json', 'r', encoding='utf-8') as f:
    old_data = json.load(f)

for lec in old_data.get('lectures', []):
    if lec.get('ID') == 'GA205/1':
        for p in lec.get('paragraphs', [])[:5]:
            print(f"  {p.get('index', '-')}")
        break
