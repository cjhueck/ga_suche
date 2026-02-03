# -*- coding: utf-8 -*-
"""
Findet ALLE Concepts mit gebrochenen Links zu ALLEN GA-Bänden.
"""
import json
import re
import glob

# Lade alle gültigen IDs aus exportierten Dateien
print("Lade alle gültigen IDs aus exportierten Lecture-Dateien...")
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

print(f"  {len(valid_ids)} gültige IDs geladen")

# Lade concepts
print("Lade concepts-database.json...")
with open('concepts-database.json', 'r', encoding='utf-8') as f:
    concepts = json.load(f)

print(f"Prüfe {len(concepts)} Concepts auf gebrochene Links...")
print('='*80)

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
        
        # Suche nach allen GA-Referenzen: GA123/1:^abc123 oder GA123/1:abc123
        pattern = r'GA(\d+[a-z]?)/(\d+):\^?([a-z0-9]+)'
        matches = re.findall(pattern, field_value)
        
        for m in matches:
            ga_num = 'GA' + m[0]
            lecture_num = m[1]
            ref_id = '^' + m[2]
            lecture = f"{ga_num}/{lecture_num}"
            
            if ref_id not in valid_ids:
                broken_links.append((lecture, ref_id))
    
    if broken_links:
        # Deduplizieren
        broken_links = list(set(broken_links))
        broken_by_concept[concept_name] = broken_links

# Ausgabe
print(f"\n{'='*80}")
print(f"VOLLSTÄNDIGE LISTE: CONCEPTS MIT GEBROCHENEN LINKS")
print(f"{'='*80}\n")

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
    
    print(f"\n{'='*80}")
    print(f"ZUSAMMENFASSUNG:")
    print(f"  {len(broken_by_concept)} Concepts betroffen")
    print(f"  {total_links} gebrochene Links insgesamt")
    
    # Gruppiere nach GA
    by_ga = {}
    for concept_name, links in broken_by_concept.items():
        for lecture, ref_id in links:
            ga = lecture.split('/')[0]
            if ga not in by_ga:
                by_ga[ga] = 0
            by_ga[ga] += 1
    
    print(f"\n  Gebrochene Links nach GA-Band:")
    for ga in sorted(by_ga.keys()):
        print(f"    {ga}: {by_ga[ga]} Links")
