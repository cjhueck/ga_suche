#!/usr/bin/env python3
"""
Korrigiert alle Varianten von "müß" zu "müss" in Steiner_GA Dateien
"""

import re
from pathlib import Path
from collections import defaultdict

def fix_muess_variants():
    """Korrigiert müßte, müßtest, müßtet, müßten zu müsste, müsstest, müsstet, müssten"""
    steiner_ga_dir = Path("Steiner_GA")
    if not steiner_ga_dir.exists():
        print(f"Verzeichnis {steiner_ga_dir} nicht gefunden!")
        return
    
    # Alle Varianten die korrigiert werden müssen
    replacements = {
        'müßte': 'müsste',
        'Müßte': 'Müsste',
        'MÜßTE': 'MÜSSTE',
        'müßtest': 'müsstest',
        'Müßtest': 'Müsstest',
        'müßtet': 'müsstet',
        'Müßtet': 'Müsstet',
        'müßten': 'müssten',
        'Müßten': 'Müssten',
    }
    
    stats = defaultdict(int)
    files_modified = []
    total_replacements = 0
    
    for md_file in steiner_ga_dir.rglob("*.md"):
        # Überspringe .trash Ordner
        if '.trash' in str(md_file):
            continue
        
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
            file_replacements = 0
            
            # Führe alle Ersetzungen durch
            for old, new in replacements.items():
                count = content.count(old)
                if count > 0:
                    content = content.replace(old, new)
                    stats[old] += count
                    file_replacements += count
            
            # Speichere nur wenn Änderungen vorgenommen wurden
            if content != original_content:
                with open(md_file, 'w', encoding=encoding_used or 'utf-8') as f:
                    f.write(content)
                
                files_modified.append(str(md_file.relative_to(steiner_ga_dir)))
                total_replacements += file_replacements
                if file_replacements > 0:
                    print(f"[OK] {md_file.name}: {file_replacements} Korrekturen")
                
        except Exception as e:
            print(f"Fehler bei {md_file}: {e}")
    
    # Zusammenfassung
    print("\n" + "=" * 80)
    print("KORREKTUR ABGESCHLOSSEN")
    print("=" * 80)
    print(f"\nDateien geändert: {len(files_modified)}")
    print(f"Gesamt-Korrekturen: {total_replacements}")
    
    print("\nKorrekturen nach Variante:")
    for wrong, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        correct = replacements[wrong]
        print(f"  '{wrong}' -> '{correct}': {count}x")
    
    # Speichere Liste der geänderten Dateien
    if files_modified:
        with open('muess_corrections_log.txt', 'w', encoding='utf-8') as f:
            f.write("KORRIGIERTE DATEIEN\n")
            f.write("=" * 80 + "\n\n")
            for file in sorted(files_modified):
                f.write(f"{file}\n")
        print(f"\nListe der geänderten Dateien gespeichert in 'muess_corrections_log.txt'")

if __name__ == "__main__":
    print("Starte Korrektur der 'müß' Varianten...")
    print("=" * 80)
    fix_muess_variants()

