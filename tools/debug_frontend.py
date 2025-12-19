#!/usr/bin/env python3
"""Debug: Prüfe wie Frontend die Bilder lädt."""

import json
from pathlib import Path
import urllib.request

base = Path(__file__).parent.parent

print("1. Prüfe GA074 in steiner-full-lectures:")
print("=" * 60)
f = base / 'steiner-full-lectures' / 'steiner-full-lectures-074-074.json'
data = json.load(open(f, 'r', encoding='utf-8'))
for lec in data['lectures']:
    print(f"\nVortrag: {lec.get('ID')}")
    tafel_paras = [p for p in lec['paragraphs'] if 'Tafel' in p.get('content', '')]
    print(f"  Tafel-Paragraphen: {len(tafel_paras)}")
    for p in tafel_paras:
        print(f"    Index: {p.get('index')}")
        print(f"    Content: {p.get('content')[:100]}...")

print("\n" + "=" * 60)
print("2. Prüfe steiner-images für GA074:")
print("=" * 60)

images_dir = base / 'steiner-images'
for f in sorted(images_dir.glob('*.json')):
    data = json.load(open(f, 'r', encoding='utf-8'))
    ga074_imgs = [img for img in data if img.get('lectureId', '').startswith('GA074')]
    if ga074_imgs:
        print(f"\n{f.name}:")
        for img in ga074_imgs:
            print(f"  lectureId: {img.get('lectureId')}")
            print(f"  index: {img.get('index')}")
            print(f"  path: {img.get('path')}")
            has_base64 = 'base64' in img and len(img.get('base64', '')) > 100
            print(f"  base64: {'JA (' + str(len(img.get('base64', ''))) + ' chars)' if has_base64 else 'NEIN'}")

print("\n" + "=" * 60)
print("3. Teste API-Endpunkt:")
print("=" * 60)
try:
    url = "http://localhost:3003/api/steiner-images/GA074/1"
    with urllib.request.urlopen(url, timeout=5) as response:
        data = json.loads(response.read().decode())
        print(f"API Response: {len(data)} Bilder")
        for img in data:
            print(f"  {img.get('index')}: {img.get('path')}")
except Exception as e:
    print(f"API Fehler: {e}")
