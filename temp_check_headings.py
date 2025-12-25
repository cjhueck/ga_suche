#!/usr/bin/env python3
import json

with open('summary-database.json', encoding='utf-8') as f:
    data = json.load(f)

ga005 = data.get('GA005', {})
headings = ga005.get('headings', [])

print(f'Anzahl Headings: {len(headings)}')
print()
for i, h in enumerate(headings):
    text = h.get('text', '')
    print(f"{i}: {text}")










