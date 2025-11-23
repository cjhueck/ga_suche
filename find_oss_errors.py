#!/usr/bin/env python3
"""
Suche nach Wörtern mit "oß" oder "Oß", die wahrscheinlich "ob" oder "Ob" sein sollten
"""

import os
import re
from pathlib import Path

def find_oss_errors():
    """Suche nach falschen 'oß'/'Oß' Schreibweisen"""
    steiner_ga_dir = Path("Steiner_GA")
    if not steiner_ga_dir.exists():
        print(f"Verzeichnis {steiner_ga_dir} nicht gefunden!")
        return
    
    matches = []
    pattern = re.compile(r'\b\w*o[ß]\w*\b', re.IGNORECASE)
    
    for md_file in steiner_ga_dir.rglob("*.md"):
        try:
            # Versuche verschiedene Kodierungen
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    with open(md_file, 'r', encoding=encoding, errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if pattern.search(line):
                                # Finde alle Treffer in der Zeile
                                for match in pattern.finditer(line):
                                    word = match.group()
                                    context_start = max(0, match.start() - 30)
                                    context_end = min(len(line), match.end() + 30)
                                    context = line[context_start:context_end].strip()
                                    
                                    matches.append({
                                        'file': str(md_file.relative_to(steiner_ga_dir)),
                                        'line': line_num,
                                        'word': word,
                                        'context': context
                                    })
                    break  # Erfolgreich gelesen
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            print(f"Fehler beim Lesen von {md_file}: {e}")
    
    # Ausgabe in Datei (UTF-8)
    output_file = "oss_errors_found.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        if matches:
            f.write(f"Gefunden: {len(matches)} mögliche Fehler\n\n")
            f.write("=" * 80 + "\n\n")
            
            # Gruppiere nach Wort, um häufige Fehler zu identifizieren
            word_counts = {}
            for match in matches:
                word = match['word']
                word_counts[word] = word_counts.get(word, 0) + 1
            
            # Zeige zuerst die häufigsten Fehlerwörter
            f.write("HÄUFIGSTE FEHLERWÖRTER:\n")
            f.write("-" * 80 + "\n")
            for word, count in sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:50]:
                f.write(f"  '{word}': {count} Vorkommen\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("\nDETAILLIERTE LISTE (erste 500):\n")
            f.write("-" * 80 + "\n\n")
            
            for i, match in enumerate(matches[:500], 1):
                f.write(f"{i}. Datei: {match['file']}\n")
                f.write(f"   Zeile: {match['line']}\n")
                f.write(f"   Wort: '{match['word']}'\n")
                f.write(f"   Kontext: ...{match['context']}...\n\n")
        else:
            f.write("Keine Vorkommen von 'oß' oder 'Oß' gefunden.\n")
        
        # Statistik nach Dateien
        if matches:
            file_counts = {}
            for match in matches:
                file_counts[match['file']] = file_counts.get(match['file'], 0) + 1
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("\nSTATISTIK NACH DATEIEN (Top 50):\n")
            f.write("-" * 80 + "\n")
            for file, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:50]:
                f.write(f"  {file}: {count} Vorkommen\n")
    
    print(f"Ergebnisse wurden in '{output_file}' gespeichert.")
    print(f"Gefunden: {len(matches)} mögliche Fehler")
    
    # Zeige Zusammenfassung in Konsole
    if matches:
        word_counts = {}
        for match in matches:
            word = match['word']
            word_counts[word] = word_counts.get(word, 0) + 1
        
        print("\nTop 20 häufigste Fehlerwörter:")
        for word, count in sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"  '{word}': {count}x")

if __name__ == "__main__":
    find_oss_errors()

