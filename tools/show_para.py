#!/usr/bin/env python3
import json
from pathlib import Path

f = Path(__file__).parent.parent / 'steiner-full-lectures' / 'steiner-full-lectures-074-074.json'
data = json.load(open(f, 'r', encoding='utf-8'))
lec = [l for l in data['lectures'] if l.get('ID') == 'GA074/1'][0]

print('Letzte 5 Paragraphen von GA074/1:')
for p in lec['paragraphs'][-5:]:
    print('---')
    idx = p.get('index', '')
    content = p.get('content', '')
    print(f'index: {idx}')
    print(f'content ({len(content)} chars):')
    print(repr(content[:200]))

