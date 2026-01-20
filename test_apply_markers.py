#!/usr/bin/env python3
"""Test: Anwendung der ersten 10 Marker auf GA001"""
import fix_sm_from_online as f
from pathlib import Path

filepath = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA001-Goethes Naturwissenschaftliche Schriften\GA001 - Einleitungen zu Goethes Naturwissenschaftlichen Schriften (1884-1897).md")

print("Lade HTML von steiner.wiki/GA_1...")
html = f.fetch_online_html(1)
print(f"HTML geladen: {len(html)} Zeichen")

print("\nExtrahiere Seitenmarker...")
markers = f.extract_page_markers_from_html(html)
print(f"Marker gefunden: {len(markers)}")

# Nur erste 10 Marker für Test
test_markers = markers[:10]
print(f"\nTeste mit ersten {len(test_markers)} Markern...")

print("\nLade lokale Datei...")
content = filepath.read_text(encoding='utf-8')
print(f"Lokale Datei: {len(content)} Zeichen")

# Prüfe existierende Marker
existing = []
for m in test_markers:
    if f"|{m['page']}|" in content:
        existing.append(m['page'])
print(f"\nBereits vorhandene Marker: {existing if existing else 'keine'}")

print("\nVerarbeite Datei (dry-run)...")
num_corrections, details = f.process_ga_file(filepath, test_markers, dry_run=True, insert_missing=True)

print(f"\n{num_corrections} Änderung(en):")
for detail in details[:20]:
    print(f"  - {detail}")
