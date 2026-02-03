#!/usr/bin/env python3
"""Diagnostiziert warum bestimmte IDs nicht gemappt werden konnten"""

import json
from difflib import SequenceMatcher

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_text(text):
    import re
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

# Teste spezifische IDs die nicht gefunden wurden
test_ids = [
    ("8", "c2wmz7"),
    ("9", "vjx5iq"),
    ("7", "s7qtbt"),
    ("14", "eeisqz"),
]

print("=" * 70)
print("  DIAGNOSE: Warum werden bestimmte IDs nicht gemappt?")
print("=" * 70)

for lecture_num, old_id in test_ids:
    print(f"\n--- GA210/{lecture_num}:^{old_id} ---")
    
    # Finde alten Text
    old_text = None
    for lecture in old_data.get('lectures', []):
        if lecture.get('ID', '').endswith(f"/{lecture_num}"):
            for para in lecture.get('paragraphs', []):
                if para.get('index', '').lstrip('^') == old_id:
                    old_text = para.get('content', '')
                    break
            break
    
    if old_text:
        safe_text = old_text[:150].encode('ascii', 'replace').decode('ascii')
        print(f"ALTER TEXT: {safe_text}...")
        
        # Finde besten Match in neuen Daten
        best_match = None
        best_score = 0
        
        for lecture in new_data.get('lectures', []):
            if lecture.get('ID', '').upper().endswith(f"/{lecture_num}"):
                for para in lecture.get('paragraphs', []):
                    new_id = para.get('index', '').lstrip('^')
                    new_text = para.get('content', '')
                    score = text_similarity(old_text, new_text)
                    if score > best_score:
                        best_score = score
                        best_match = (new_id, new_text)
        
        if best_match:
            new_id, new_text = best_match
            safe_new = new_text[:150].encode('ascii', 'replace').decode('ascii')
            print(f"BESTER MATCH: ^{new_id} ({best_score:.0%})")
            print(f"NEUER TEXT:  {safe_new}...")
        else:
            print("KEIN MATCH GEFUNDEN")
    else:
        print(f"Alte ID nicht in alten Daten gefunden!")

print("\n" + "=" * 70)
