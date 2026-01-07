#!/usr/bin/env python3
"""Archiviert alte pagebreaks/*.json für bereits verarbeitete GAs."""
import os
import shutil
from pathlib import Path

# GAs die bereits Marker in JSON haben
processed_gas = ['GA061', 'GA062', 'GA063', 'GA064', 'GA065', 'GA066', 'GA067', 'GA069a', 'GA069b', 'GA072', 'GA073']

# Erstelle archive Ordner
archive_dir = Path('pagebreaks/archive')
archive_dir.mkdir(exist_ok=True)

# Verschiebe nur die entsprechenden JSON-Dateien
moved = []
for ga in processed_gas:
    json_file = Path(f'pagebreaks/{ga}.json')
    if json_file.exists():
        dest = archive_dir / json_file.name
        shutil.move(str(json_file), str(dest))
        moved.append(ga)
        print(f'  Archiviert: {ga}.json')

print(f'\nGesamt archiviert: {len(moved)} Dateien')

# Zähle verbleibende
remaining = len([f for f in Path('pagebreaks').glob('*.json') if 'report' not in f.name])
print(f'Verbleibend in pagebreaks/: {remaining} Dateien')

