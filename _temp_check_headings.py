#!/usr/bin/env python3
"""Prüft welche Datenstrukturen von ID-Änderungen betroffen sind"""

import json

# Lade Datenbanken
with open('summary-database.json', 'r', encoding='utf-8') as f:
    summary_db = json.load(f)

with open('keywords-database.json', 'r', encoding='utf-8') as f:
    keywords_db = json.load(f)

# Zeige GA210/1 Beispiel
print("=" * 70)
print("  DATENSTRUKTUREN MIT ABSATZ-IDs")
print("=" * 70)

entry = summary_db.get('GA210/1', {})
print("\n=== SUMMARY-DATABASE: GA210/1 ===\n")

# tableOfContents (H3-Überschriften)
toc = entry.get('tableOfContents', [])
print(f"1. tableOfContents (H3): {len(toc)} Eintraege")
for t in toc[:3]:
    heading = t.get('heading', '')[:50]
    index = t.get('index', '?')
    print(f"   - '{heading}...'")
    print(f"     index: {index}")
print()

# headings (falls vorhanden)
headings = entry.get('headings', [])
print(f"2. headings: {len(headings)} Eintraege")
if headings:
    for h in headings[:2]:
        if isinstance(h, dict):
            print(f"   - title: {h.get('title', '')[:40]}")
            print(f"     index: {h.get('index', '?')}")
        else:
            print(f"   - {str(h)[:60]}")
print()

# lectureKeywords
kws = entry.get('lectureKeywords', [])
print(f"3. lectureKeywords: {len(kws)} Eintraege")
for k in kws[:3]:
    print(f"   - term: {k.get('term', '')}")
    print(f"     index: {k.get('index', '?')}")
    print(f"     heading: {k.get('heading', '')[:40]}")
print()

# Keywords-Database
print("\n=== KEYWORDS-DATABASE: GA210/1 ===\n")
kw_entry = keywords_db.get('GA210/1', {})
kws2 = kw_entry.get('keywords', [])
print(f"4. keywords: {len(kws2)} Eintraege")
for k in kws2[:3]:
    print(f"   - term: {k.get('term', '')}")
    print(f"     index: {k.get('index', '?')}")
    print(f"     heading: {k.get('heading', '')[:40]}")

print("\n" + "=" * 70)
print("  FAZIT: Was bricht bei ID-Änderung?")
print("=" * 70)
print("""
Bei Neugenerierung von Block-IDs brechen:

1. summary-database.json:
   - tableOfContents[].index  --> H3-Überschriften-Links
   - lectureKeywords[].index  --> Keyword-Links zu Absätzen
   
2. keywords-database.json:
   - keywords[].index         --> Keyword-Links zu Absätzen
   
3. concepts-database.json:
   - text, overview etc. mit (GAXXX/Y:^id) Referenzen
   - sources[].index          --> Quellen-Links zu Absätzen

LÖSUNG: Nach ID-Neugenerierung müssen:
   - Summary/Keywords neu generiert werden (Backend-API)
   - Concepts manuell oder per Skript aktualisiert werden
""")
