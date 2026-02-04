# -*- coding: utf-8 -*-
import json
import glob
import random

# Aktuelle gültige IDs
current_ids = set()
for jfile in glob.glob('steiner-full-lectures/steiner-full-lectures-*.json'):
    with open(jfile, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for lecture in data.get('lectures', []):
        for para in lecture.get('paragraphs', []):
            if para.get('index'):
                current_ids.add(para['index'])

# Gebrochene Keywords sammeln
with open('keywords-database.json', 'r', encoding='utf-8') as f:
    keywords = json.load(f)

broken_keywords = []
for lecture_id, kw_data in keywords.items():
    if isinstance(kw_data, dict):
        kw_list = kw_data.get('keywords', [])
    else:
        continue
    for kw in kw_list:
        if isinstance(kw, dict):
            idx = kw.get('index', '')
            if idx and idx not in current_ids:
                # Hole keyword ODER term (zwei verschiedene Schemata)
                kw_name = kw.get('keyword') or kw.get('term') or 'N/A'
                broken_keywords.append({
                    'lecture': lecture_id,
                    'keyword': kw_name,
                    'index': idx,
                    'heading': kw.get('heading', '')[:35]
                })

# Zufällige 30 auswählen
random.shuffle(broken_keywords)
sample = broken_keywords[:30]

print(f'Gebrochene Keywords gesamt: {len(broken_keywords)}')
print()
for i, kw in enumerate(sample, 1):
    lecture = kw['lecture']
    keyword = kw['keyword'][:25] if kw['keyword'] else 'N/A'
    heading = kw['heading'][:30] if kw['heading'] else ''
    index = kw['index']
    print(f"{i:2}. {lecture:12} | {keyword:25} | {heading:30} | {index}")
