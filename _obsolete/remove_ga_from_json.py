#!/usr/bin/env python3
"""Entfernt einen GA-Band aus einer steiner-full-lectures-*.json Datei"""
import json
import sys

if len(sys.argv) < 3:
    print("Verwendung: python remove_ga_from_json.py <json-datei> <GA-nummer>")
    print("Beispiel: python remove_ga_from_json.py steiner-full-lectures-030-100-part01.json GA035")
    sys.exit(1)

json_file = sys.argv[1]
ga_to_remove = sys.argv[2].upper()

print(f"Entferne {ga_to_remove} aus {json_file}...")

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

lectures = data.get('lectures', [])
original_count = len(lectures)

# Filtere Vorträge
filtered = [l for l in lectures if l.get('gaNumber', '').upper() != ga_to_remove]
removed_count = original_count - len(filtered)

if removed_count > 0:
    data['lectures'] = filtered
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Entfernt: {removed_count} Vortraege")
    print(f"  Verbleibend: {len(filtered)} Vortraege")
else:
    print(f"  Keine {ga_to_remove} Vortraege gefunden")

