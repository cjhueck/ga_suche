#!/usr/bin/env python3
import json
import re
from pathlib import Path

def normalize_text(text):
    if not text:
        return ""
    s = re.sub(r"<[^>]+>", " ", text)
    s = s.replace("\u00ad", "").replace("\u00a0", " ")
    s = s.lower().replace("ß", "ss")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

# Suchtext aus den ersten beiden Absätzen von GA153/1
search_text = "wer derjenigen form geisteswissenschaftlicher weltanschauung"

# Lade page-break-markers
with open('page-break-markers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

breaks = data.get('GA153', {}).get('breaks', [])
for b in breaks:
    page = b.get('page', 0)
    right = normalize_text(b.get('right') or '')
    if search_text[:50] in right:
        print(f"GEFUNDEN auf Seite {page}!")
        print(f"  Text: {right[:200]}...")
