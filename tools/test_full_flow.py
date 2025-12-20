#!/usr/bin/env python3
"""Vollstaendiger Test der Bilder-Anzeige-Kette."""

import json
import urllib.request
from pathlib import Path

base = Path(__file__).parent.parent
API = "http://localhost:3003"

print("=" * 60)
print("TEST: Vollstaendige Bilder-Anzeige-Kette")
print("=" * 60)

# Test 1: API-Endpunkt
print("\n1. API-Endpunkt /api/steiner-images/GA074/1:")
try:
    with urllib.request.urlopen(f"{API}/api/steiner-images/GA074/1", timeout=5) as r:
        data = json.loads(r.read().decode())
        print(f"   OK: {len(data)} Bild(er)")
        for img in data:
            print(f"      index={img.get('index')}, path={img.get('path')}")
            print(f"      base64-Laenge: {len(img.get('base64', ''))} chars")
except Exception as e:
    print(f"   FEHLER: {e}")

# Test 2: Vortrag GA074/1 in fullLectures
print("\n2. Vortrag GA074/1 in steiner-full-lectures:")
f = base / 'steiner-full-lectures' / 'steiner-full-lectures-074-074.json'
data = json.load(open(f, 'r', encoding='utf-8'))
lec = [l for l in data['lectures'] if l.get('ID') == 'GA074/1'][0]
print(f"   Vortrag: {lec.get('ID')}")
tafel_paras = [p for p in lec['paragraphs'] if 'Tafel' in p.get('content', '')]
print(f"   Tafel-Paragraphen: {len(tafel_paras)}")
for p in tafel_paras:
    print(f"      {p.get('index')}: {p.get('content')[:60]}...")

# Test 3: Index-Matching
print("\n3. Index-Matching zwischen API und Paragraphen:")
try:
    with urllib.request.urlopen(f"{API}/api/steiner-images/GA074/1", timeout=5) as r:
        api_images = json.loads(r.read().decode())
    
    for img in api_images:
        api_index = img.get('index')
        matching_para = [p for p in tafel_paras if p.get('index') == api_index]
        if matching_para:
            print(f"   OK: {api_index} -> Paragraph gefunden")
        else:
            print(f"   FEHLER: {api_index} -> Kein Paragraph mit diesem Index!")
            print(f"      Vorhandene Paragraph-Indices: {[p.get('index') for p in tafel_paras]}")
except Exception as e:
    print(f"   FEHLER: {e}")

print("\n" + "=" * 60)
print("Test abgeschlossen")
print("=" * 60)



