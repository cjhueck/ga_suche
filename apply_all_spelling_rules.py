#!/usr/bin/env python3
"""
Umfassende Rechtschreibkorrektur für Steiner_GA Dateien
Wendet ALLE Regeln aus rechtschreibregeln.py direkt an
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Importiere Rechtschreibregeln
from rechtschreibregeln import korrigiere_rechtschreibung, get_replacements_dict

def apply_all_spelling_rules():
    """Wendet alle Rechtschreibregeln auf alle Dateien an"""
    steiner_ga_dir = Path("Steiner_GA")
    if not steiner_ga_dir.exists():
        print(f"Verzeichnis {steiner_ga_dir} nicht gefunden!")
        return
    
    print("Starte umfassende Rechtschreibkorrektur...")
    print("=" * 80)
    
    # Hole alle Ersetzungen
    replacements = get_replacements_dict()
    
    files_modified = []
    total_files = 0
    stats = defaultdict(int)
    
    # Durchsuche alle Markdown-Dateien
    for md_file in steiner_ga_dir.rglob("*.md"):
        # Überspringe .trash Ordner
        if '.trash' in str(md_file):
            continue
        
        total_files += 1
        if total_files % 500 == 0:
            print(f"Verarbeitet: {total_files} Dateien...")
        
        try:
            # Versuche verschiedene Kodierungen
            content = None
            encoding_used = None
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    with open(md_file, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                continue
            
            original_content = content
            
            # Wende Rechtschreibkorrekturen an
            content = korrigiere_rechtschreibung(content)
            
            # Zusätzliche direkte Ersetzungen für häufige Fälle
            # (falls sie nicht in korrigiere_rechtschreibung enthalten sind)
            for old, new in replacements.items():
                if old in content:
                    count = content.count(old)
                    content = content.replace(old, new)
                    stats[old] += count
            
            # Prüfe ob Änderungen vorgenommen wurden
            if content != original_content:
                # Speichere korrigierte Version
                with open(md_file, 'w', encoding=encoding_used or 'utf-8') as f:
                    f.write(content)
                
                files_modified.append(str(md_file.relative_to(steiner_ga_dir)))
                
                # Zähle grob die Anzahl der Änderungen
                changes = sum(1 for i in range(len(original_content)) 
                            if i < len(content) and original_content[i] != content[i])
                
                if changes > 0:
                    print(f"[OK] {md_file.name}: ~{changes} Zeichen geändert")
                
        except Exception as e:
            print(f"  X Fehler bei {md_file}: {e}")
    
    # Zusammenfassung
    print("\n" + "=" * 80)
    print("RECHTSCHREIBKORREKTUR ABGESCHLOSSEN")
    print("=" * 80)
    print(f"\nGesamt Dateien verarbeitet: {total_files}")
    print(f"Dateien geändert: {len(files_modified)}")
    
    print("\nTop 30 häufigste Korrekturen:")
    for old, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)[:30]:
        new = replacements.get(old, '?')
        print(f"  '{old}' -> '{new}': {count}x")
    
    # Speichere Liste der geänderten Dateien
    if files_modified:
        with open('all_spelling_corrections_log.txt', 'w', encoding='utf-8') as f:
            f.write("KORRIGIERTE DATEIEN\n")
            f.write("=" * 80 + "\n\n")
            for file in sorted(files_modified):
                f.write(f"{file}\n")
        print(f"\nListe der geänderten Dateien gespeichert in 'all_spelling_corrections_log.txt'")

if __name__ == "__main__":
    apply_all_spelling_rules()

