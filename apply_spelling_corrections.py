#!/usr/bin/env python3
"""
Umfassende Rechtschreibkorrektur für Steiner_GA Dateien
- Anwendung der Regeln aus rechtschreibregeln.py
- Allgemeine Rechtschreibkorrekturen
- Korrektur fehlender Bindestriche vor "und" (z.B. "Sonnenund" => "Sonnen- und")
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Importiere Rechtschreibregeln
try:
    from rechtschreibregeln import korrigiere_rechtschreibung
except ImportError:
    print("Warnung: rechtschreibregeln.py nicht gefunden, verwende eingebettete Version")
    def korrigiere_rechtschreibung(text):
        return text

# Wörter, die NICHT geändert werden sollen (korrekte Wörter die auf "und" enden)
UND_EXCEPTIONS = {
    'rund', 'Rund', 'Hund', 'hund', 'Stund', 'stund', 'Bund', 'bund',
    'Grund', 'grund', 'Fund', 'fund', 'Pfund', 'pfund', 'Wund', 'wund',
    'Mund', 'mund', 'Sund', 'sund', 'Zund', 'zund', 'Kund', 'kund',
    'hundert', 'Hundert', 'tausend', 'Tausend',
    'gesund', 'Gesund', 'ungesund', 'Ungesund',
    'verwund', 'Verwund', 'verwunden', 'Verwunden',
    'gefunden', 'Gefunden', 'begründet', 'Begründet',
    'gegründet', 'Gegründet', 'abgerundet', 'Abgerundet',
    'aufgerundet', 'Aufgerundet', 'umrundet', 'Umrundet',
    'Ungrund', 'ungrund', 'Weltabgrund', 'weltabgrund', 'Abgrund', 'abgrund',
    'Freund', 'freund', 'Rätselfreund', 'rätselfreund',
    'gebunden', 'Gebunden', 'verbunden', 'Verbunden',
    'ungebunden', 'Ungebunden', 'unverbunden', 'Unverbunden',
    'gebunden', 'Gebunden', 'verbunden', 'Verbunden',
    'gebunden', 'Gebunden', 'verbunden', 'Verbunden',
}

def fix_missing_hyphen_before_und(text):
    """
    Korrigiert fehlende Bindestriche vor "und" in zusammengesetzten Wörtern.
    Beispiele: "Sonnenund" => "Sonnen- und", "Wachund" => "Wach- und"
    """
    # Pattern: Wort das mit "und" endet, gefolgt von Leerzeichen oder Satzzeichen
    # Suche nach Wörtern wie "Sonnenund", "Wachund", etc.
    
    def replace_und(match):
        full_word = match.group(0)  # Das gesamte Wort (z.B. "Sonnenund")
        
        # Überspringe Ausnahmen
        if full_word.lower() in UND_EXCEPTIONS:
            return full_word
        
        # Prüfe ob das Wort wirklich mit "und" endet
        if not full_word.lower().endswith('und'):
            return full_word
        
        # Extrahiere den Prefix (alles außer "und")
        prefix = full_word[:-3]
        
        # Prüfe ob Prefix sinnvoll ist (mindestens 2 Zeichen, endet mit Buchstabe)
        if len(prefix) < 2 or not prefix[-1].isalpha():
            return full_word
        
        # Ersetze: "Xund" => "X- und"
        # Behalte Groß-/Kleinschreibung des Prefix bei
        return f"{prefix}- und"
    
    # Pattern: Wort das mit "und" endet, gefolgt von Leerzeichen, Satzzeichen oder Zeilenende
    # \b(\w{2,})und\b(?=\s|$|[.,;:!?\)\]])
    pattern = r'\b(\w{2,})und\b(?=\s|$|[.,;:!?\)\]\n])'
    text = re.sub(pattern, replace_und, text)
    
    return text

def apply_general_spelling_corrections(text):
    """
    Allgemeine Rechtschreibkorrekturen zusätzlich zu rechtschreibregeln.py
    """
    # Zusätzliche allgemeine Korrekturen
    general_replacements = {
        # Häufige Tippfehler
        'ackurat': 'akkurat',
        'zurücckommen': 'zurückkommen',
        'zurücc': 'zurück',
        
        # Weitere häufige Fehler
        'paßt': 'passt',
        'läßt': 'lässt',
        'heisst': 'heißt',
        'weiss': 'weiß',
        'Fleiss': 'Fleiß',
        'fleiss': 'fleiß',
        'dreissig': 'dreißig',
        'dreiunddreissig': 'dreiunddreißig',
        
        # Zusammengesetzte Wörter mit fehlendem Bindestrich
        'römischkatholisch': 'römisch-katholisch',
        'DeutschÖsterreicher': 'Deutsch-Österreicher',
        'seelischgeistig': 'seelisch-geistig',
        'geistigseelisch': 'geistig-seelisch',
        
        # Weitere häufige Zusammensetzungen
        'westund mitteleuropäisch': 'west- und mitteleuropäisch',
        'von daoder von dorther': 'von da- oder von dorther',
    }
    
    for old, new in general_replacements.items():
        text = text.replace(old, new)
    
    return text

def correct_spelling_in_file(filepath):
    """
    Korrigiert Rechtschreibung in einer einzelnen Datei
    """
    try:
        # Versuche verschiedene Kodierungen
        content = None
        encoding_used = None
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
            try:
                with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read()
                encoding_used = encoding
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            return 0, []
        
        original_content = content
        changes = []
        
        # 1. Anwenden der Rechtschreibregeln aus rechtschreibregeln.py
        content = korrigiere_rechtschreibung(content)
        
        # 2. Allgemeine Rechtschreibkorrekturen
        content = apply_general_spelling_corrections(content)
        
        # 3. Fehlende Bindestriche vor "und" korrigieren
        content = fix_missing_hyphen_before_und(content)
        
        # Prüfe ob Änderungen vorgenommen wurden
        if content != original_content:
            # Speichere korrigierte Version
            with open(filepath, 'w', encoding=encoding_used or 'utf-8') as f:
                f.write(content)
            
            # Zähle Änderungen (vereinfacht)
            num_changes = len([c for c in range(len(original_content)) if original_content[c] != content[c]])
            # Grobe Schätzung der Anzahl der Ersetzungen
            changes_made = []
            if 'daß' in original_content and 'dass' in content:
                changes_made.append('daß→dass')
            if 'muß' in original_content and 'muss' in content:
                changes_made.append('muß→muss')
            if 'Bewußtsein' in original_content and 'Bewusstsein' in content:
                changes_made.append('Bewußtsein→Bewusstsein')
            if '- und' in content and '- und' not in original_content:
                changes_made.append('Bindestrich vor "und"')
            
            return 1, [f"{len(changes_made)} Korrekturtypen: {', '.join(changes_made)}"]
        
        return 0, []
        
    except Exception as e:
        print(f"  X Fehler bei {filepath}: {e}")
        return 0, []

def main():
    """Hauptfunktion"""
    steiner_ga_dir = Path("Steiner_GA")
    if not steiner_ga_dir.exists():
        print(f"Verzeichnis {steiner_ga_dir} nicht gefunden!")
        return
    
    print("Starte umfassende Rechtschreibkorrektur...")
    print("=" * 80)
    
    files_modified = []
    total_files = 0
    
    # Durchsuche alle Markdown-Dateien
    for md_file in steiner_ga_dir.rglob("*.md"):
        # Überspringe .trash Ordner
        if '.trash' in str(md_file):
            continue
        
        total_files += 1
        if total_files % 100 == 0:
            print(f"Verarbeitet: {total_files} Dateien...")
        
        modified, changes = correct_spelling_in_file(md_file)
        if modified:
            files_modified.append(str(md_file.relative_to(steiner_ga_dir)))
            if changes:
                print(f"[OK] {md_file.name}: {', '.join(changes)}")
    
    # Zusammenfassung
    print("\n" + "=" * 80)
    print("RECHTSCHREIBKORREKTUR ABGESCHLOSSEN")
    print("=" * 80)
    print(f"\nGesamt Dateien verarbeitet: {total_files}")
    print(f"Dateien geändert: {len(files_modified)}")
    
    # Speichere Liste der geänderten Dateien
    if files_modified:
        with open('spelling_corrections_log.txt', 'w', encoding='utf-8') as f:
            f.write("KORRIGIERTE DATEIEN\n")
            f.write("=" * 80 + "\n\n")
            for file in sorted(files_modified):
                f.write(f"{file}\n")
        print(f"\nListe der geänderten Dateien gespeichert in 'spelling_corrections_log.txt'")

if __name__ == "__main__":
    main()

