#!/usr/bin/env python3
"""Test-Skript für Online-Marker-Extraktion"""
import fix_sm_from_online as f

print("Lade HTML von steiner.wiki/GA_1...")
html = f.fetch_online_html(1)
print(f"HTML geladen: {len(html)} Zeichen")

print("\nExtrahiere Seitenmarker...")
markers = f.extract_page_markers_from_html(html)
print(f"Marker gefunden: {len(markers)}")

if markers:
    print("\nErste 10 Marker:")
    for m in markers[:10]:
        print(f"  Seite {m['page']:3d}: vor='...{m['context_before'][-40:]}' | nach='{m['context_after'][:40]}...'")
