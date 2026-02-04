# -*- coding: utf-8 -*-
import json
import glob
import os
import re

def normalize_text(text):
    if not text:
        return ""
    text = text.replace('\ufeff', '').strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\|(\d+)\|', '', text)
    replacements = [
        ('daß', 'dass'), ('muß', 'muss'), ('läßt', 'lässt'),
        ('wußte', 'wusste'), ('mußte', 'musste'), ('bewußt', 'bewusst'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text.strip().lower()

# Welche GAs haben gebrochene Keywords?
print("=== GAs mit gebrochenen Keywords ===")
with open('keywords-database.json', 'r', encoding='utf-8') as f:
    keywords = json.load(f)

# Sammle aktuelle IDs
current_ids = set()
for jfile in glob.glob('steiner-full-lectures/steiner-full-lectures-*.json'):
    with open(jfile, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for lecture in data.get('lectures', []):
        for para in lecture.get('paragraphs', []):
            if para.get('index'):
                current_ids.add(para['index'])

broken_by_ga = {}
for lecture_id, kw_data in keywords.items():
    if isinstance(kw_data, dict):
        for kw in kw_data.get('keywords', []):
            if isinstance(kw, dict):
                idx = kw.get('index', '')
                if idx and idx not in current_ids:
                    ga = lecture_id.split('/')[0]
                    broken_by_ga[ga] = broken_by_ga.get(ga, 0) + 1

# Top 10
top_gas = sorted(broken_by_ga.items(), key=lambda x: -x[1])[:10]
print("Top 10 GAs mit gebrochenen Keywords:")
for ga, count in top_gas:
    print(f"  {ga}: {count}")

# Prüfe ein spezifisches GA - nehmen wir GA200, das angeblich exportiert ist
print("\n=== Prüfe GA200 ===")
ga200_current_ids = set()
ga200_current_texts = {}

for jfile in glob.glob('steiner-full-lectures/steiner-full-lectures-*.json'):
    with open(jfile, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for lecture in data.get('lectures', []):
        lid = lecture.get('ID', '') or lecture.get('id', '')
        if lid.startswith('GA200'):
            for para in lecture.get('paragraphs', []):
                idx = para.get('index', '')
                text = para.get('text', '') or para.get('content', '')
                if idx:
                    ga200_current_ids.add(idx)
                    if text:
                        ga200_current_texts[idx] = text[:100]

print(f"GA200 aktuelle IDs: {len(ga200_current_ids)}")
if ga200_current_ids:
    print(f"Beispiel: {list(ga200_current_ids)[:3]}")

# Prüfe broken IDs für GA200
ga200_broken = []
for lecture_id, kw_data in keywords.items():
    if lecture_id.startswith('GA200'):
        if isinstance(kw_data, dict):
            for kw in kw_data.get('keywords', []):
                if isinstance(kw, dict):
                    idx = kw.get('index', '')
                    if idx and idx not in current_ids:
                        ga200_broken.append(idx)

print(f"GA200 gebrochene Keyword-IDs: {len(ga200_broken)}")
if ga200_broken:
    print(f"Beispiele: {ga200_broken[:5]}")

# Prüfe ob diese IDs in den aktuellen GA200 Texten sind
if ga200_broken and ga200_current_ids:
    for broken_id in ga200_broken[:3]:
        in_current = broken_id in ga200_current_ids
        print(f"  {broken_id} in aktuellen GA200 IDs: {in_current}")
