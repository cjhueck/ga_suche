import re
from pathlib import Path

folder = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA')
for d in folder.iterdir():
    if 'GA019' in d.name:
        ga_folder = d
        break

print("=== Hauptdateien (sollten Marker haben) ===")
for f in sorted(ga_folder.glob("GA019 (*.md")):
    if f.parent == ga_folder:  # Nur Hauptordner
        content = f.read_text(encoding='utf-8')
        markers = len(re.findall(r'\|\d+\|', content))
        print(f"{f.name[:45]}... : {markers} Marker")

print("\n=== Backup-Dateien (ohne Marker) ===")
backup_folder = ga_folder / "_backups"
if backup_folder.exists():
    for f in sorted(backup_folder.glob("*.md")):
        content = f.read_text(encoding='utf-8')
        markers = len(re.findall(r'\|\d+\|', content))
        print(f"{f.name[:45]}... : {markers} Marker")

