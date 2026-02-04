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

# Sammle aktuelle GA200 Texte
print("=== Aktuelle GA200 Texte ===")
ga200_current = {}  # id -> text

for jfile in glob.glob('steiner-full-lectures/steiner-full-lectures-*.json'):
    with open(jfile, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for lecture in data.get('lectures', []):
        lid = lecture.get('ID', '') or lecture.get('id', '')
        if lid.startswith('GA200'):
            for para in lecture.get('paragraphs', []):
                idx = para.get('index', '')
                text = para.get('text', '') or para.get('content', '')
                if idx and text:
                    ga200_current[idx] = text

print(f"GA200 Absätze: {len(ga200_current)}")

# Suche alten Text für gebrochene ID ^y088hz in Backups
target_id = '^y088hz'
print(f"\n=== Suche alten Text für {target_id} ===")

old_folders = [
    'C:/Users/chuec/OneDrive/Obsidian/ga_suche - Kopien/ga_suche',
    'C:/Users/chuec/OneDrive/Obsidian/ga_suche - Kopien/ga_suche 14.10.2025',
]

old_text = None
for old_folder in old_folders:
    if not os.path.exists(old_folder):
        continue
    for jfile in glob.glob(f'{old_folder}/steiner-full-lectures-*.json'):
        try:
            with open(jfile, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for lecture in data.get('lectures', []):
                for para in lecture.get('paragraphs', []):
                    if para.get('index') == target_id:
                        old_text = para.get('text', '') or para.get('content', '')
                        break
                if old_text:
                    break
            if old_text:
                break
        except:
            pass
    if old_text:
        break

if old_text:
    print(f"Alter Text gefunden: {old_text[:150]}...")
    norm_old = normalize_text(old_text)
    print(f"Normalisiert: {norm_old[:100]}...")
    
    # Suche diesen Text in aktuellen GA200 Texten
    print("\n=== Suche in aktuellen GA200 Texten ===")
    found = False
    for current_id, current_text in ga200_current.items():
        norm_current = normalize_text(current_text)
        if norm_old[:50] in norm_current or norm_current[:50] in norm_old:
            print(f"MATCH: {current_id}")
            print(f"  Aktuell: {current_text[:100]}...")
            found = True
            break
    
    if not found:
        print("Kein Match gefunden.")
        print("\nErste 3 aktuelle GA200 Texte:")
        for i, (cid, ctext) in enumerate(list(ga200_current.items())[:3]):
            print(f"  {cid}: {ctext[:80]}...")
else:
    print(f"Kein alter Text für {target_id} gefunden")
    print("Versuche aus Keywords-Heading...")
    
    # Vielleicht können wir aus dem Heading etwas erfahren
    with open('keywords-database.json', 'r', encoding='utf-8') as f:
        keywords = json.load(f)
    
    for lecture_id, kw_data in keywords.items():
        if lecture_id.startswith('GA200') and isinstance(kw_data, dict):
            for kw in kw_data.get('keywords', []):
                if isinstance(kw, dict) and kw.get('index') == target_id:
                    print(f"Lecture: {lecture_id}")
                    print(f"Keyword: {kw.get('keyword') or kw.get('term')}")
                    print(f"Heading: {kw.get('heading')}")
                    break
