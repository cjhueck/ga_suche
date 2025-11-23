#!/usr/bin/env python3
"""
Korrigiert verbleibende Rechtschreibfehler die noch nicht korrigiert wurden
"""

import re
from pathlib import Path
from collections import defaultdict

def fix_remaining_spelling():
    """Korrigiert verbleibende Rechtschreibfehler"""
    steiner_ga_dir = Path("Steiner_GA")
    if not steiner_ga_dir.exists():
        print(f"Verzeichnis {steiner_ga_dir} nicht gefunden!")
        return
    
    # Zusätzliche Ersetzungen die möglicherweise fehlen
    replacements = {
        'muß': 'muss',
        'Muß': 'Muss',
        'MÜß': 'MUSS',
        'mußt': 'musst',
        'Mußt': 'Musst',
        'mußte': 'musste',
        'Mußte': 'Musste',
        'mußtest': 'musstest',
        'Mußtest': 'Musstest',
        'mußtet': 'musstet',
        'Mußtet': 'Musstet',
        'mußten': 'mussten',
        'Mußten': 'Mussten',
        'wußte': 'wusste',
        'Wußte': 'Wusste',
        'gewußt': 'gewusst',
        'Gewußt': 'Gewusst',
        'Prozeß': 'Prozess',
        'prozeß': 'prozess',
        'PROZEß': 'PROZESS',
    }
    
    stats = defaultdict(int)
    files_modified = []
    total_replacements = 0
    
    print("Starte Korrektur verbleibender Rechtschreibfehler...")
    print("=" * 80)
    
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
        with open('remaining_spelling_corrections_log.txt', 'w', encoding='utf-8') as f:
            f.write("KORRIGIERTE DATEIEN\n")
            f.write("=" * 80 + "\n\n")
            for file in sorted(files_modified):
                f.write(f"{file}\n")
        print(f"\nListe der geänderten Dateien gespeichert in 'remaining_spelling_corrections_log.txt'")

if __name__ == "__main__":
    fix_remaining_spelling()

