#!/usr/bin/env python3
"""Prüfe GA074 in allen steiner-full-lectures Dateien."""

import json
from pathlib import Path

base = Path(__file__).parent.parent

# Prüfe alle steiner-full-lectures Dateien nach GA074
lectures_dir = base / 'steiner-full-lectures'
print("GA074 in steiner-full-lectures:")
print("=" * 60)

for f in sorted(lectures_dir.glob('*.json')):
    data = json.load(open(f, 'r', encoding='utf-8'))
    lectures = data.get('lectures', [])
    ga074 = [l for l in lectures if l.get('gaNumber') == 'GA074']
    if ga074:
        print(f"\n{f.name}: {len(ga074)} GA074 Vortraege")
        for lec in ga074:
            paras = lec.get('paragraphs', [])
            tafel = [p for p in paras if 'Tafel' in p.get('content', '')]
            print(f"  Vortrag {lec.get('lectureNumber')}: {len(paras)} Abs., {len(tafel)} Tafel(n)")
            for t in tafel:
                print(f"    -> {t.get('index')}: {t.get('content')[:50]}")

# Prüfe auch steiner-images
print("\n" + "=" * 60)
print("GA074 in steiner-images:")
print("=" * 60)

images_dir = base / 'steiner-images'
for f in sorted(images_dir.glob('*.json')):
    data = json.load(open(f, 'r', encoding='utf-8'))
    ga074_imgs = [img for img in data if img.get('lectureId', '').startswith('GA074')]
    if ga074_imgs:
        print(f"\n{f.name}: {len(ga074_imgs)} GA074 Bilder")
        for img in ga074_imgs:
            print(f"  {img.get('lectureId')} {img.get('index')}: {img.get('path')}")






