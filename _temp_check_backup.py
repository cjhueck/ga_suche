# -*- coding: utf-8 -*-
import json

# Ältestes Backup prüfen
print("IDs im ältesten Backup (GA205/1 keywords):")
with open('_backups/keywords-database_20260203_103725.json', 'r', encoding='utf-8') as f:
    old_kw = json.load(f)

kw = old_kw.get('GA205/1', {}).get('keywords', [])
for k in kw[:5]:
    print(f"  {k.get('index', '-')}")

print("\nIDs in aktuellem keywords-database (GA205/1):")
with open('keywords-database.json', 'r', encoding='utf-8') as f:
    curr_kw = json.load(f)

kw2 = curr_kw.get('GA205/1', {}).get('keywords', [])
for k in kw2[:5]:
    print(f"  {k.get('index', '-')}")
