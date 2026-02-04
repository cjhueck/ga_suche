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

# 1. Sammle aktuelle gültige IDs
print("=== Aktuelle IDs ===")
current_ids = set()
current_text_to_id = {}

for jfile in glob.glob('steiner-full-lectures/steiner-full-lectures-*.json'):
    with open(jfile, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for lecture in data.get('lectures', []):
        for para in lecture.get('paragraphs', []):
            idx = para.get('index', '')
            text = para.get('text', '') or para.get('content', '')
            if idx and text:
                current_ids.add(idx)
                norm_text = normalize_text(text)
                if len(norm_text) > 50:
                    current_text_to_id[norm_text[:200]] = idx

print(f"Aktuelle IDs: {len(current_ids)}")
print(f"Text-zu-ID Mappings: {len(current_text_to_id)}")

# 2. Sammle gebrochene IDs aus Keywords
print("\n=== Gebrochene IDs ===")
with open('keywords-database.json', 'r', encoding='utf-8') as f:
    keywords = json.load(f)

broken_ids = set()
for lecture_id, kw_data in keywords.items():
    if isinstance(kw_data, dict):
        for kw in kw_data.get('keywords', []):
            if isinstance(kw, dict):
                idx = kw.get('index', '')
                if idx and idx not in current_ids:
                    broken_ids.add(idx)

print(f"Gebrochene IDs: {len(broken_ids)}")
sample_broken = list(broken_ids)[:5]
print(f"Beispiele: {sample_broken}")

# 3. Suche in alten Backups
print("\n=== Alte Backups ===")
old_folders = [
    'C:/Users/chuec/OneDrive/Obsidian/ga_suche - Kopien/ga_suche',
    'C:/Users/chuec/OneDrive/Obsidian/ga_suche - Kopien/ga_suche 14.10.2025',
]

old_id_to_text = {}

for old_folder in old_folders:
    if not os.path.exists(old_folder):
        print(f"  {old_folder}: NICHT GEFUNDEN")
        continue
    
    jsons = glob.glob(f'{old_folder}/steiner-full-lectures-*.json')
    print(f"  {os.path.basename(old_folder)}: {len(jsons)} JSON-Dateien")
    
    for jfile in jsons:
        try:
            with open(jfile, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for lecture in data.get('lectures', []):
                for para in lecture.get('paragraphs', []):
                    idx = para.get('index', '')
                    if idx in broken_ids and idx not in old_id_to_text:
                        text = para.get('text', '') or para.get('content', '')
                        if text:
                            old_id_to_text[idx] = text
        except Exception as e:
            print(f"    Fehler: {e}")

print(f"\nTexte für gebrochene IDs gefunden: {len(old_id_to_text)}")

# 4. Prüfe ein Beispiel
if old_id_to_text:
    sample_id = list(old_id_to_text.keys())[0]
    sample_text = old_id_to_text[sample_id]
    print(f"\nBeispiel alte ID: {sample_id}")
    print(f"Alter Text: {sample_text[:100]}...")
    norm_old = normalize_text(sample_text)
    print(f"Normalisiert: {norm_old[:100]}...")
    
    # Suche im aktuellen Index
    found = norm_old[:200] in current_text_to_id
    print(f"Gefunden in aktuellen Texten (200): {found}")
    if not found:
        found100 = norm_old[:100] in {k[:100]: v for k, v in current_text_to_id.items()}
        print(f"Gefunden in aktuellen Texten (100): {found100}")
