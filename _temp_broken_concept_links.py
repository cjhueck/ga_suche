# -*- coding: utf-8 -*-
"""
Findet alle Concepts mit gebrochenen Links zu GA205-GA209.
"""
import json
import re
import glob

TARGET_GAS = ['GA205', 'GA206', 'GA207', 'GA208', 'GA209']

# Lade alle gültigen IDs aus exportierten Dateien
print("Lade exportierte Lecture-Dateien...")
valid_ids = {}  # ga_number -> set of ids

for f in glob.glob("steiner-full-lectures/steiner-full-lectures-*.json"):
    try:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        for lec in data.get('lectures', []):
            lec_id = lec.get('ID', '')
            if '/' in lec_id:
                ga = lec_id.split('/')[0]
                if ga in TARGET_GAS:
                    if ga not in valid_ids:
                        valid_ids[ga] = set()
                    for p in lec.get('paragraphs', []):
                        idx = p.get('index', '')
                        if idx:
                            valid_ids[ga].add(idx)
    except:
        pass

for ga in TARGET_GAS:
    count = len(valid_ids.get(ga, set()))
    print(f"  {ga}: {count} gültige IDs")

# Lade concepts-database
print("\nLade concepts-database.json...")
with open('concepts-database.json', 'r', encoding='utf-8') as f:
    concepts = json.load(f)

# Finde gebrochene Links
print(f"\n{'='*60}")
print("CONCEPTS MIT GEBROCHENEN LINKS ZU GA205-GA209:")
print('='*60)

broken_concepts = []

for concept in concepts:
    concept_name = concept.get('concept', concept.get('name', 'Unbekannt'))
    broken_links = []
    
    for source in concept.get('sources', []):
        # Prüfe index-Feld
        idx = source.get('index', '')
        text = source.get('text', '')
        
        # Finde GA-Referenz im Text
        ga_match = None
        for ga in TARGET_GAS:
            if ga in text or ga.lower() in text.lower():
                ga_match = ga
                break
            # Prüfe auch Pattern (GA205/1:^xxx)
            pattern = rf'\({ga}/\d+:\^[a-z0-9]+\)'
            if re.search(pattern, text):
                ga_match = ga
                break
        
        if ga_match and idx:
            # Prüfe ob ID gültig ist
            if ga_match in valid_ids and idx not in valid_ids[ga_match]:
                broken_links.append({
                    'ga': ga_match,
                    'id': idx,
                    'text': text[:80] if text else '-'
                })
    
    if broken_links:
        broken_concepts.append({
            'concept': concept_name,
            'broken': broken_links
        })

# Ausgabe
if not broken_concepts:
    print("\nKeine gebrochenen Links gefunden!")
else:
    print(f"\n{len(broken_concepts)} Concepts mit gebrochenen Links:\n")
    
    for bc in broken_concepts:
        print(f"\n### {bc['concept']}")
        for link in bc['broken']:
            print(f"    {link['ga']}: {link['id']}")
            if link['text']:
                # ASCII-safe output
                safe_text = link['text'].encode('ascii', 'replace').decode('ascii')
                print(f"      Text: {safe_text}...")

print(f"\n{'='*60}")
print(f"ZUSAMMENFASSUNG: {len(broken_concepts)} Concepts betroffen")
