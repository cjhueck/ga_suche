#!/usr/bin/env python3
"""Korrigiere GA074 Paragraphen - konvertiere Markdown-Bilder zu HTML."""

import json
import re
from pathlib import Path

base = Path(__file__).parent.parent
f = base / 'steiner-full-lectures' / 'steiner-full-lectures-074-074.json'

print(f"Lade {f.name}...")
data = json.load(open(f, 'r', encoding='utf-8'))

def convert_markdown_images_to_html(content):
    """Konvertiere ![alt](src) zu <img src="src" alt="alt" />"""
    # Pattern: ![alt](src)
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def replace_img(match):
        alt = match.group(1)
        src = match.group(2)
        return f'<img src="{src}" alt="{alt}" />'
    
    return re.sub(pattern, replace_img, content)

changes = 0
for lec in data['lectures']:
    for para in lec['paragraphs']:
        content = para.get('content', '')
        
        # Prüfe ob Content Markdown-Bilder hat
        if '![' in content and '](' in content:
            new_content = convert_markdown_images_to_html(content)
            if new_content != content:
                para['content'] = new_content
                changes += 1
                print(f"  {lec.get('ID')} {para.get('index')}: Bild konvertiert")
                print(f"    Vorher: {content[:80]}...")
                print(f"    Nachher: {new_content[:80]}...")

if changes > 0:
    print(f"\nSpeichere {changes} Änderungen...")
    with open(f, 'w', encoding='utf-8') as out:
        json.dump(data, out, ensure_ascii=False, indent=2)
    print("Fertig!")
else:
    print("Keine Änderungen nötig.")


