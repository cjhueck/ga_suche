#!/usr/bin/env python3
"""
Umfassende Korrektur: Ersetzt alle falschen "oß"/"Oß" zu "ob"/"Ob" 
ABER schützt korrekte Wörter wie "bloß", "groß", "sproß", etc.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Wörter, die NICHT geändert werden sollen (korrekte deutsche Wörter mit "oß")
PROTECTED_PATTERNS = [
    r'\bblo[ß]\w*',  # bloß, bloßen, bloße, etc.
    r'\bgro[ß]\w*',  # groß, großen, große, etc.
    r'\bgrö[ß]\w*',  # größte, größer, etc.
    r'\bsto[ß]\w*',  # stoßen, Anstoß, etc.
    r'\bAnsto[ß]',  # Anstoß
    r'\babgesto[ß]\w*',  # abgestoßen
    r'\bgesto[ß]\w*',  # gestoßen
    r'\bverscho[ß]\w*',  # verschoßen (aber das sollte eigentlich "verschoben" sein - ist das ein anderer Fehler?)
    r'\bspro[ß]\w*',  # sproß, sproßte, entsproß, etc.
    r'\bScho[ß]\w*',  # Schoße
    r'\bGroßbritannien',
    r'\bGroßgrundbesitzerin',
    r'\bgroßartig',
    r'\bgewo[ß]\w*',  # gewoßen sollte eigentlich "gewoben" sein, aber das ist ein anderer Fehler
    r'\bverwo[ß]\w*',  # verwoßen sollte eigentlich "verwoben" sein
    r'\beinverwo[ß]\w*',  # einverwoßen sollte eigentlich "einverwoben" sein
    r'\bhineinverwo[ß]\w*',  # hineinverwoßen sollte eigentlich "hineinverwoben" sein
]

def is_protected(word):
    """Prüft ob ein Wort geschützt werden soll"""
    for pattern in PROTECTED_PATTERNS:
        if re.search(pattern, word, re.IGNORECASE):
            return True
    return False

def fix_oss_comprehensive():
    """Umfassende Korrektur aller 'oß'/'Oß' zu 'ob'/'Ob'"""
    steiner_ga_dir = Path("Steiner_GA")
    if not steiner_ga_dir.exists():
        print(f"Verzeichnis {steiner_ga_dir} nicht gefunden!")
        return
    
    stats = defaultdict(int)
    files_modified = []
    total_replacements = 0
    
    # Pattern: Finde alle Wörter mit "oß" oder "Oß"
    # Aber nicht am Wortanfang (um "oß" allein zu erfassen)
    pattern = re.compile(r'\b\w*[oO][ß]\w*\b')
    
    for md_file in steiner_ga_dir.rglob("*.md"):
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
            
            # Finde alle Vorkommen von "oß"/"Oß"
            matches = list(pattern.finditer(content))
            
            # Ersetze von hinten nach vorne, um Positionsverschiebungen zu vermeiden
            for match in reversed(matches):
                word = match.group()
                
                # Überspringe geschützte Wörter
                if is_protected(word):
                    continue
                
                # Ersetze "oß" → "ob" und "Oß" → "Ob"
                if 'oß' in word:
                    corrected = word.replace('oß', 'ob')
                elif 'Oß' in word:
                    # Behalte Großschreibung bei
                    corrected = word.replace('Oß', 'Ob')
                else:
                    continue
                
                # Führe Ersetzung durch
                start, end = match.span()
                content = content[:start] + corrected + content[end:]
                
                stats[word] += 1
                file_replacements += 1
            
            # Speichere nur wenn Änderungen vorgenommen wurden
            if content != original_content:
                # Schreibe korrigierte Version
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
    
    print("\nTop 30 häufigste Korrekturen:")
    for wrong, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)[:30]:
        corrected = wrong.replace('oß', 'ob').replace('Oß', 'Ob')
        print(f"  '{wrong}' -> '{corrected}': {count}x")
    
    # Speichere Liste der geänderten Dateien
    if files_modified:
        with open('oss_corrections_log.txt', 'w', encoding='utf-8') as f:
            f.write("KORRIGIERTE DATEIEN\n")
            f.write("=" * 80 + "\n\n")
            for file in sorted(files_modified):
                f.write(f"{file}\n")
        print(f"\nListe der geänderten Dateien gespeichert in 'oss_corrections_log.txt'")

if __name__ == "__main__":
    print("Starte umfassende Korrektur der 'oß'/'Oß' Fehler...")
    print("=" * 80)
    fix_oss_comprehensive()

