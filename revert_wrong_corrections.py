#!/usr/bin/env python3
"""
Korrigiert falsche Ersetzungen zurück:
- "Stob" → "Stoß" (wenn es "Stoß" sein sollte)
- "Anstob" → "Anstoß"
- "abgestoben" → "abgestoßen"
- "gestoben" → "gestoßen"
- etc.
"""

import re
from pathlib import Path
from collections import defaultdict

# Falsche Ersetzungen die rückgängig gemacht werden müssen
REVERT_CORRECTIONS = {
    'Stob': 'Stoß',
    'stob': 'stoß',
    'Stobkraft': 'Stoßkraft',
    'Stoblaute': 'Stoßlaute',
    'Stoblaut': 'Stoßlaut',
    'stobe': 'stoße',
    'Stobes': 'Stoßes',
    'Stoblauten': 'Stoßlauten',
    'stobenden': 'stoßenden',
    'stobweise': 'stoßweise',
    'Stobkräfte': 'Stoßkräfte',
    'Stobe': 'Stoße',
    'Stobrichtung': 'Stoßrichtung',
    'stobest': 'stoßest',
    'stobende': 'stoßende',
    'stobend': 'stoßend',
    'Stobseufzer': 'Stoßseufzer',
    'Stobens': 'Stoßens',
    'Stobbewegung': 'Stoßbewegung',
    'stobige': 'stoßige',
    'Stoberei': 'Stoßerei',
    'Stobgeräusch': 'Stoßgeräusch',
    'Stobwirkungen': 'Stoßwirkungen',
    'stobweisem': 'stoßweisem',
    'Stobweise': 'Stoßweise',
    'Stobenden': 'Stoßenden',
    'stobkräftigen': 'stoßkräftigen',
    'Stobigem': 'Stoßigem',
    'Stoblautes': 'Stoßlautes',
    'Stobwellen': 'Stoßwellen',
    'Stobigkeit': 'Stoßigkeit',
    'Stobige': 'Stoßige',
    'Stobbock': 'Stoßbock',
    'stobender': 'stoßender',
    'Stobseufzern': 'Stoßseufzern',
    'Anstob': 'Anstoß',
    'abgestoben': 'abgestoßen',
    'gestoben': 'gestoßen',
    'schob': 'schoß',  # Vorsicht: "schob" kann auch korrekt sein (von "schieben")
    'schoben': 'schoßen',  # Vorsicht: "schoben" kann auch korrekt sein (von "schieben")
}

def revert_wrong_corrections():
    """Macht falsche Ersetzungen rückgängig"""
    steiner_ga_dir = Path("Steiner_GA")
    if not steiner_ga_dir.exists():
        print(f"Verzeichnis {steiner_ga_dir} nicht gefunden!")
        return
    
    stats = defaultdict(int)
    files_modified = []
    total_replacements = 0
    
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
            
            # Führe alle Rückgängigmachungen durch
            for wrong, correct in REVERT_CORRECTIONS.items():
                # Verwende einfache String-Ersetzung für bessere Trefferquote
                count = content.count(wrong)
                if count > 0:
                    content = content.replace(wrong, correct)
                    stats[wrong] += count
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
    print("RÜCKGÄNGIGMACHUNG ABGESCHLOSSEN")
    print("=" * 80)
    print(f"\nDateien geändert: {len(files_modified)}")
    print(f"Gesamt-Korrekturen: {total_replacements}")
    
    print("\nKorrekturen:")
    for wrong, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        correct = REVERT_CORRECTIONS[wrong]
        print(f"  '{wrong}' -> '{correct}': {count}x")

if __name__ == "__main__":
    print("Mache falsche Ersetzungen rückgängig...")
    print("=" * 80)
    revert_wrong_corrections()

