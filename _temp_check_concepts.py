#!/usr/bin/env python3
"""Prüft GA210-Referenzen in concepts-database.json"""

import json
import re

with open('concepts-database.json', 'r', encoding='utf-8') as f:
    concepts = json.load(f)

# Pattern für GA210-Referenzen
ga210_pattern = re.compile(r'^GA210', re.IGNORECASE)
ga210_ref_pattern = re.compile(r'\(GA210/\d+:\^?[a-z0-9]+\)', re.IGNORECASE)

found = []
for concept in concepts:
    keyword = concept.get('keyword', 'Unbekannt')
    matches = []
    
    # Prüfe Text-Felder
    for field in ['text', 'definitionText', 'functionText', 'interactionText', 'specialText']:
        if field in concept and concept[field]:
            refs = ga210_ref_pattern.findall(concept[field])
            if refs:
                matches.extend([(field, r) for r in refs])
        
        # Prüfe overview
        overview = concept.get('overview', {})
        if isinstance(overview, dict) and field in overview and overview[field]:
            refs = ga210_ref_pattern.findall(overview[field])
            if refs:
                matches.extend([('overview.' + field, r) for r in refs])
    
    # Prüfe sources
    sources = concept.get('sources', [])
    for s in sources:
        sid = s.get('id', '')
        if ga210_pattern.match(sid):
            matches.append(('source', f"{sid} (index: {s.get('index', '?')})"))
    
    if matches:
        found.append({'keyword': keyword, 'matches': matches})

print("=" * 60)
print("  GA210-REFERENZEN IN CONCEPTS-DATABASE")
print("=" * 60)
print(f"\nGefunden: {len(found)} Concepts mit GA210-Verweisen\n")

if not found:
    print("Keine GA210-Referenzen gefunden.")
    print("(Das Bereinigungsskript hat sie bereits entfernt)")
else:
    for item in found:
        print(f"** {item['keyword']} **")
        for field, ref in item['matches']:
            print(f"   - {field}: {ref}")
        print()
