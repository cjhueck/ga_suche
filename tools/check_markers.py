#!/usr/bin/env python3
"""Schnelle Überprüfung ob Marker in MD-Dateien vorhanden sind."""
import re
from pathlib import Path

gas = ['051', '063', '084', '092', '110', '152', '181', '200']
pattern = r'\|\d+\|'

print("Überprüfe Marker in ausgewählten GAs:\n")

for ga in gas:
    md_files = list(Path('Steiner_GA').glob(f'GA{ga}*/*1*.md'))
    if md_files:
        content = md_files[0].read_text(encoding='utf-8')
        markers = re.findall(pattern, content)
        print(f"  GA{ga}/1: {len(markers)} Marker - {md_files[0].name}")
    else:
        print(f"  GA{ga}/1: NICHT GEFUNDEN")

