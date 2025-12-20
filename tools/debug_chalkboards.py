#!/usr/bin/env python3
"""Debug-Skript für Wandtafelzeichnungen."""

import json
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent

# Prüfe steiner-full-lectures
print("=" * 60)
print("1. STEINER-FULL-LECTURES")
print("=" * 60)

lectures_file = BASE_PATH / "steiner-full-lectures" / "steiner-full-lectures-030-354-part04.json"
data = json.load(open(lectures_file, 'r', encoding='utf-8'))
lectures = data.get('lectures', [])

# Finde GA074
for lec in lectures:
    if lec.get('gaNumber') == 'GA074' and lec.get('lectureNumber') == 1:
        paras = lec.get('paragraphs', [])
        print(f"GA074/1 gefunden: {len(paras)} Paragraphen")
        print("Letzte 3 Paragraphen:")
        for p in paras[-3:]:
            idx = p.get('index', 'keine')
            content = p.get('content', '')[:80]
            print(f"  {idx}: {content}")
        break
else:
    print("GA074/1 NICHT gefunden!")
    # Zeige welche GA-Nummern vorhanden sind
    ga_nums = set(l.get('gaNumber', '') for l in lectures)
    print(f"Vorhandene GA-Nummern (erste 10): {sorted(list(ga_nums))[:10]}")

# Prüfe steiner-images
print("\n" + "=" * 60)
print("2. STEINER-IMAGES")
print("=" * 60)

images_file = BASE_PATH / "steiner-images" / "steiner-images-part70.json"
if images_file.exists():
    images = json.load(open(images_file, 'r', encoding='utf-8'))
    print(f"steiner-images-part70.json: {len(images)} Bilder")
    print("Erste 3 Bilder:")
    for img in images[:3]:
        print(f"  lectureId: {img.get('lectureId')}")
        print(f"  index: {img.get('index')}")
        print(f"  path: {img.get('path')}")
        print()
else:
    print("steiner-images-part70.json NICHT gefunden!")

# Prüfe ob lectureId-Format übereinstimmt
print("\n" + "=" * 60)
print("3. VERGLEICH")
print("=" * 60)

# Sammle alle lectureIds aus images
if images_file.exists():
    image_lecture_ids = set(img.get('lectureId', '') for img in images)
    print(f"LectureIds in steiner-images-part70: {sorted(image_lecture_ids)}")
    
    # Prüfe ob diese in steiner-full-lectures existieren
    for lid in sorted(image_lecture_ids):
        parts = lid.split('/')
        if len(parts) == 2:
            ga_num, lec_num = parts
            found = False
            for lec in lectures:
                if lec.get('gaNumber') == ga_num and str(lec.get('lectureNumber')) == lec_num:
                    found = True
                    break
            status = "OK" if found else "NICHT GEFUNDEN"
            print(f"  {lid}: {status}")





