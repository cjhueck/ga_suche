# -*- coding: utf-8 -*-
"""
Findet ALLE Concepts die GA205-GA209 referenzieren und prüft deren IDs.
"""
import json
import re
import glob

TARGET_GAS = ['GA205', 'GA206', 'GA207', 'GA208', 'GA209']

# Lade alle gültigen IDs aus exportierten Dateien
print("Lade exportierte Lecture-Dateien...")
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

# Lade concepts-database
print("\nLade concepts-database.json...")
with open('concepts-database.json', 'r', encoding='utf-8') as f:
    concepts = json.load(f)

# Suche nach allen GA205-GA209 Referenzen
print(f"\nSuche nach Referenzen zu: {', '.join(TARGET_GAS)}")
print('='*70)

broken = []
valid_refs = []

for concept in concepts:
    concept_name = concept.get('concept', concept.get('name', 'Unbekannt'))
    
    # Durchsuche alle Textfelder
    fields_to_check = ['text', 'definitionText', 'functionText', 'interactionText']
    
    for field in fields_to_check:
        text = concept.get(field, '')
        if not text:
            continue
        
        # Suche nach GA-Referenzen: GA205/1:^abc123 oder GA205/1:abc123
        for ga in TARGET_GAS:
            # Pattern: GA205/1:^abc123 oder GA205/1:abc123
            pattern = rf'{ga}/(\d+):\^?([a-z0-9]+)'
            matches = re.findall(pattern, text)
            
            for m in matches:
                lecture_num = m[0]
                ref_id = '^' + m[1] if not m[1].startswith('^') else m[1]
                lecture = f"{ga}/{lecture_num}"
                
                if ref_id in valid_ids:
                    valid_refs.append((concept_name, lecture, ref_id))
                else:
                    # Extrahiere Kontext
                    idx = text.find(f"{ga}/{lecture_num}")
                    context = text[max(0, idx-20):idx+50] if idx >= 0 else ""
                    broken.append((concept_name, lecture, ref_id, context))
    
    # Auch sources prüfen
    for source in concept.get('sources', []):
        source_text = source.get('text', '')
        source_idx = source.get('index', '')
        
        for ga in TARGET_GAS:
            if ga in source_text and source_idx:
                if source_idx in valid_ids:
                    valid_refs.append((concept_name, ga, source_idx))
                else:
                    broken.append((concept_name, ga, source_idx, source_text[:80]))

print(f"\nGültige Referenzen: {len(valid_refs)}")
print(f"Gebrochene Referenzen: {len(broken)}")

if broken:
    print(f"\n{'='*70}")
    print("GEBROCHENE LINKS:")
    print('='*70)
    
    # Gruppiere nach Concept
    by_concept = {}
    for b in broken:
        concept_name = b[0]
        if concept_name not in by_concept:
            by_concept[concept_name] = []
        by_concept[concept_name].append(b[1:])
    
    for concept_name, refs in sorted(by_concept.items()):
        safe_name = concept_name.encode('ascii', 'replace').decode('ascii')
        print(f"\n### {safe_name}")
        for ref in refs:
            lecture, ref_id = ref[0], ref[1]
            context = ref[2] if len(ref) > 2 else ""
            print(f"    {lecture}: {ref_id}")
            if context:
                safe_context = context.encode('ascii', 'replace').decode('ascii')
                print(f"      Kontext: ...{safe_context}...")
    
    print(f"\n{'='*70}")
    print(f"ZUSAMMENFASSUNG:")
    print(f"  {len(by_concept)} Concepts betroffen")
    print(f"  {len(broken)} gebrochene Links insgesamt")
else:
    print("\nKeine gebrochenen Links gefunden!")
