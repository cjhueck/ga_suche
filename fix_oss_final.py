#!/usr/bin/env python3
"""
Finale umfassende Korrektur: Ersetzt alle falschen "oß"/"Oß" zu "ob"/"Ob" 
mit besserem Schutz für korrekte Wörter
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Liste korrekter Wörter mit "oß" die NICHT geändert werden sollen
CORRECT_WORDS = {
    'bloß', 'bloßen', 'bloße', 'bloßer', 'bloßes', 'bloßem',
    'groß', 'großen', 'große', 'großer', 'großes', 'großem', 'größte', 'größer', 'größten', 'größten',
    'Großbritannien', 'Großgrundbesitzerin', 'großartig', 'Großes', 'Großen', 'Große',
    'stoßen', 'Anstoß', 'abgestoßen', 'gestoßen', 'verschoßen',  # verschoßen sollte eigentlich "verschoben" sein, aber das ist ein anderer Fehler
    'Stoß', 'Stoßkraft', 'Stoßlaute', 'Stoßlaut', 'stoße', 'Stoßes', 'Stoßlauten', 
    'stoßenden', 'stoßweise', 'Stoßkräfte', 'Stoße', 'Stoßrichtung', 'stoßest', 
    'stoßende', 'stoßend', 'Stoßseufzer', 'Stoßens', 'Stoßbewegung', 'stoßige',
    'Stoßerei', 'Stoßgeräusch', 'Stoßwirkungen', 'stoßweisem', 'Stoßweise', 
    'Stoßenden', 'stoßkräftigen', 'Stoßigem', 'Stoßlautes', 'Stoßwellen', 
    'Stoßigkeit', 'Stoßige', 'Stoßbock', 'stoßender', 'Stoßseufzern',
    'schoß', 'schoßen',  # Schoß, schoßen
    'sproß', 'sproßte', 'entsproß', 'hervorsproß', 'hervorsproßte', 'heraussproß', 'aufgesproßt', 
    'gesproßt', 'absproßt', 'hervorgesproßt', 'herausgesproßt', 'Sproßknolle', 'Menschensproß', 'Göttersproß', 'Königssproß',
    'Schoße', 'Schoß',
    # "gewoßen", "verwoßen" etc. sollten eigentlich "gewoben", "verwoben" sein - aber das sind andere Fehler
    # Lass sie erstmal unverändert, da sie nicht "ob" enthalten sollten
}

def is_correct_word(word):
    """Prüft ob ein Wort korrekt ist und nicht geändert werden soll"""
    word_lower = word.lower()
    
    # Exakte Übereinstimmung
    if word in CORRECT_WORDS or word_lower in CORRECT_WORDS:
        return True
    
    # Pattern-basierte Prüfung
    if re.match(r'^blo[ß]\w*$', word, re.IGNORECASE):
        return True
    if re.match(r'^gro[ß]\w*$', word, re.IGNORECASE):
        return True
    if re.match(r'^grö[ß]\w*$', word, re.IGNORECASE):
        return True
    if re.match(r'^spro[ß]\w*$', word, re.IGNORECASE):
        return True
    if re.match(r'^Ansto[ß]$', word, re.IGNORECASE):
        return True
    if re.match(r'^abgesto[ß]\w*$', word, re.IGNORECASE):
        return True
    if re.match(r'^gesto[ß]\w*$', word, re.IGNORECASE):
        return True
    if re.match(r'^Sto[ß]\w*$', word):  # Stoß, Stoßkraft, etc.
        return True
    if re.match(r'^sto[ß]\w*$', word):  # stoße, stoßend, etc.
        return True
    if re.match(r'^Scho[ß]\w*$', word):  # Schoß
        return True
    if re.match(r'^scho[ß]\w*$', word, re.IGNORECASE):  # schoß, schoßen
        return True
    
    return False

def fix_oss_final():
    """Finale umfassende Korrektur"""
    steiner_ga_dir = Path("Steiner_GA")
    if not steiner_ga_dir.exists():
        print(f"Verzeichnis {steiner_ga_dir} nicht gefunden!")
        return
    
    stats = defaultdict(int)
    files_modified = []
    total_replacements = 0
    
    # Pattern: Finde alle Wörter mit "oß" oder "Oß"
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
                
                # Überspringe korrekte Wörter
                if is_correct_word(word):
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
    
    print("\nTop 50 häufigste Korrekturen:")
    for wrong, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)[:50]:
        corrected = wrong.replace('oß', 'ob').replace('Oß', 'Ob')
        print(f"  '{wrong}' -> '{corrected}': {count}x")
    
    # Speichere Liste der geänderten Dateien
    if files_modified:
        with open('oss_corrections_final_log.txt', 'w', encoding='utf-8') as f:
            f.write("KORRIGIERTE DATEIEN\n")
            f.write("=" * 80 + "\n\n")
            for file in sorted(files_modified):
                f.write(f"{file}\n")
        print(f"\nListe der geänderten Dateien gespeichert in 'oss_corrections_final_log.txt'")

if __name__ == "__main__":
    print("Starte finale umfassende Korrektur der 'oß'/'Oß' Fehler...")
    print("=" * 80)
    fix_oss_final()

