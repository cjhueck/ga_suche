# -*- coding: utf-8 -*-
"""
Liste alle Concepts mit gebrochenen Links zu GA205-GA209.
"""
import json
import re
import glob

TARGET_GAS = ['GA205', 'GA206', 'GA207', 'GA208', 'GA209']

# Lade alle gültigen IDs
print("Lade gültige IDs...")
valid_ids = set()
for f in glob.glob("steiner-full-lectures/steiner-full-lectures-*.json"):
    try:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
        for lec in data.get('lectures', []):
            for p in lec.get('paragraphs', []):
                idx = p.get('index', '')
                if idx:
                    valid_ids.add(idx)
    except:
        pass

# Lade concepts
with open('concepts-database.json', 'r', encoding='utf-8') as f:
    concepts = json.load(f)

print(f"Prüfe {len(concepts)} Concepts...")
print('='*70)

# Sammle alle gebrochenen Links pro Concept
broken_by_concept = {}

for concept in concepts:
    # Finde Concept-Namen
    concept_name = None
    for key in ['concept', 'name', 'title', 'Begriff']:
        if key in concept and concept[key]:
            concept_name = concept[key]
            break
    
    if not concept_name:
        # Versuche aus erstem nicht-leeren String-Feld
        for k, v in concept.items():
            if isinstance(v, str) and len(v) > 3 and len(v) < 100:
                concept_name = v
                break
    
    if not concept_name:
        concept_name = "Unbenannt"
    
    broken_links = []
    
    # Durchsuche alle Textfelder
    for field_name, field_value in concept.items():
        if not isinstance(field_value, str):
            continue
        
        # Suche nach GA-Referenzen
        for ga in TARGET_GAS:
            pattern = rf'{ga}/(\d+):\^?([a-z0-9]+)'
            matches = re.findall(pattern, field_value)
            
            for m in matches:
                ref_id = '^' + m[1]
                lecture = f"{ga}/{m[0]}"
                
                if ref_id not in valid_ids:
                    broken_links.append((lecture, ref_id))
    
    if broken_links:
        # Deduplizieren
        broken_links = list(set(broken_links))
        broken_by_concept[concept_name] = broken_links

# Ausgabe
print(f"\n{'='*70}")
print(f"CONCEPTS MIT GEBROCHENEN LINKS ZU GA205-GA209:")
print(f"{'='*70}\n")

if not broken_by_concept:
    print("Keine gebrochenen Links gefunden!")
else:
    total_links = 0
    for concept_name in sorted(broken_by_concept.keys()):
        links = broken_by_concept[concept_name]
        total_links += len(links)
        safe_name = concept_name.encode('ascii', 'replace').decode('ascii')
        print(f"\n{safe_name}")
        for lecture, ref_id in sorted(links):
            print(f"    {lecture}: {ref_id}")
    
    print(f"\n{'='*70}")
    print(f"ZUSAMMENFASSUNG:")
    print(f"  {len(broken_by_concept)} Concepts betroffen")
    print(f"  {total_links} gebrochene Links insgesamt")
