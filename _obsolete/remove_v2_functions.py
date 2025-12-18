#!/usr/bin/env python3
"""Entfernt V2 Seitenmarker-Funktionen aus app.html"""
import re

with open(r'c:\Users\chuec\OneDrive\GitHub\ga_suche\app.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Finde und entferne insertPageMarkersFromData und validateInsertedMarkers
# Pattern: Von "// Fügt Seitenmarker aus page-markers.json" bis zum Ende von validateInsertedMarkers

start_marker = "    // Fügt Seitenmarker aus page-markers.json in den Text ein"
end_marker = "    // GA-Bibliographie Popup Funktionen"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    # Entferne den Block
    new_content = content[:start_idx] + "\n" + content[end_idx:]
    
    with open(r'c:\Users\chuec\OneDrive\GitHub\ga_suche\app.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"V2-Funktionen entfernt!")
    print(f"  Start: Zeichen {start_idx}")
    print(f"  Ende: Zeichen {end_idx}")
    print(f"  Entfernte Zeichen: {end_idx - start_idx}")
else:
    print("Marker nicht gefunden!")
    print(f"  start_idx: {start_idx}")
    print(f"  end_idx: {end_idx}")

