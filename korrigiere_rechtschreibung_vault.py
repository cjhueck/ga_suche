# -*- coding: utf-8 -*-
"""
Korrigiert alte Rechtschreibung zu neuer in allen Markdown-Dateien
Wendet die gleichen Korrekturen an wie ga_pdf_final.py
"""
import os
import sys
from pathlib import Path

STEINER_GA_DIR = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'

# Wörterliste - gleich wie in ga_pdf_final.py
REPLACEMENTS = {
    # Häufigste
    'daß': 'dass',
    'Daß': 'Dass',
    'muß': 'muss',
    'mußt': 'musst',
    'mußte': 'musste',
    'mußtest': 'musstest',
    'mußtet': 'musstet',
    'mußten': 'mussten',
    'wußte': 'wusste',
    'gewußt': 'gewusst',
    'Bewußtsein': 'Bewusstsein',
    'bewußt': 'bewusst',
    'Bewußtseins': 'Bewusstseins',
    'Bewußtseinszustand': 'Bewusstseinszustand',
    'Bewußtseinszustände': 'Bewusstseinszustände',
    'Unbewußtsein': 'Unbewusstsein',
    'unbewußt': 'unbewusst',
    'Selbstbewußtsein': 'Selbstbewusstsein',
    'selbstbewußt': 'selbstbewusst',
    # Weitere häufige
    'ißt': 'isst',
    'iß': 'iss',
    'frißt': 'frisst',
    'Kuß': 'Kuss',
    'Fluß': 'Fluss',
    'Schloß': 'Schloss',
    'Haß': 'Hass',
    'Nuß': 'Nuss',
    'Faß': 'Fass',
    'Preß': 'Press',
    'Miß': 'Miss',
    'miß': 'miss',
    'nuß': 'nuss',
    'fluß': 'fluss',
    'schloß': 'schloss',
    'kuß': 'kuss',
    'haß': 'hass',
    'faß': 'fass',
    'preß': 'press',
    'Anschluß': 'Anschluss',
    'schluß': 'schluss',
    'Schluß': 'Schluss',
    # Weitere Formen
    'biß': 'biss',
    'riß': 'riss',
    'floß': 'floss',
    'schoß': 'schoss',
    # Weitere Korrekturen
    'Entschluß': 'Entschluss',
    'entschluß': 'entschluss',
    'Entschlüsse': 'Entschlüsse',  # Plural bleibt gleich
    'entschlüsse': 'entschlüsse',  # Plural bleibt gleich
    'müßte': 'müsste',
    'müßtest': 'müsstest',
    'müßtet': 'müsstet',
    'müßten': 'müssten',
    # ss zu ß (nach langem Vokal/Diphthong)
    'reisst': 'reißt',
    'Eiweiss': 'Eiweiß',
    'eiweiss': 'eiweiß',
    # Weitere häufige Korrekturen
    'läßt': 'lässt',
    'heisst': 'heißt',
    'weiss': 'weiß',
    # Zusammengesetzte Wörter mit Bindestrich
    'ChristusWesenheit': 'Christus-Wesenheit',
    'JohannesEvangelium': 'Johannes-Evangelium',
    'SeelischGeistiges': 'Seelisch-Geistiges',
    'GeistigSeelisches': 'Geistig-Seelisches',
    'geistigseelisch': 'geistig-seelisch',
    'seelischgeistig': 'seelisch-geistig',
    'westund mitteleuropäisch': 'west- und mitteleuropäisch',
    'von daoder von dorther': 'von da- oder von dorther',
    'EntwederOder': 'Entweder-Oder',
    # Weitere Prozeß-Varianten
    'Prozeß': 'Prozess',
    '..prozeß': '..prozess',
    # ss statt ss
    'dreissig': 'dreißig',
    'dreiunddreissig': 'dreiunddreißig',
}


def korrigiere_datei(filepath, dry_run=False):
    """Korrigiert Rechtschreibung in einer Datei"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_count = 0
        
        # Wende alle Ersetzungen an
        for old, new in REPLACEMENTS.items():
            if old in content:
                count = content.count(old)
                content = content.replace(old, new)
                changes_count += count
        
        # Wenn Änderungen vorgenommen wurden
        if content != original_content:
            if not dry_run:
                # Speichere korrigierte Datei
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return changes_count
        
        return 0
        
    except Exception as e:
        print(f"  Fehler bei {filepath}: {e}")
        return 0


def main():
    # Parse Kommandozeilenargumente
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    
    print("=" * 80)
    print("RECHTSCHREIBKORREKTUR - ALTE => NEUE RECHTSCHREIBUNG")
    print("=" * 80)
    print(f"\nOrdner: {STEINER_GA_DIR}")
    print(f"Korrekturen: {len(REPLACEMENTS)} Ersetzungsregeln")
    
    if dry_run:
        print("\n*** DRY RUN MODUS - Keine Änderungen werden gespeichert ***")
    
    print()
    
    if not os.path.exists(STEINER_GA_DIR):
        print(f"FEHLER: Ordner nicht gefunden: {STEINER_GA_DIR}")
        return
    
    # Finde alle .md Dateien
    md_files = []
    for root, dirs, files in os.walk(STEINER_GA_DIR):
        for file in files:
            if file.endswith('.md') and not file.endswith('.backup'):
                md_files.append(os.path.join(root, file))
    
    print(f"Gefunden: {len(md_files)} Markdown-Dateien\n")
    
    if not dry_run:
        print("Möchten Sie fortfahren? (j/n): ", end='')
        response = input().lower()
        if response not in ['j', 'ja', 'y', 'yes']:
            print("\nAbgebrochen.")
            return
        print()
    
    print("Verarbeite Dateien...\n")
    
    files_changed = 0
    total_changes = 0
    
    for i, filepath in enumerate(md_files, 1):
        # Zeige Fortschritt alle 100 Dateien
        if i % 100 == 0:
            print(f"  Verarbeitet: {i}/{len(md_files)}... ({files_changed} Dateien geändert, {total_changes} Korrekturen)")
        
        changes = korrigiere_datei(filepath, dry_run=dry_run)
        if changes > 0:
            rel_path = os.path.relpath(filepath, STEINER_GA_DIR)
            # Zeige nur die ersten paar Dateien detailliert
            if files_changed < 20 or dry_run:
                print(f"  [OK] {rel_path}: {changes} Korrektur(en)")
            files_changed += 1
            total_changes += changes
    
    print("\n" + "=" * 80)
    print("FERTIG!")
    print("=" * 80)
    print(f"\nDateien verarbeitet: {len(md_files)}")
    print(f"Dateien geändert: {files_changed}")
    print(f"Dateien unverändert: {len(md_files) - files_changed}")
    print(f"Gesamt-Korrekturen: {total_changes}")
    
    if dry_run:
        print("\n*** DRY RUN - Keine Änderungen wurden gespeichert ***")
        print("Zum Anwenden der Änderungen: python korrigiere_rechtschreibung_vault.py")
    else:
        print("\n*** Änderungen wurden gespeichert ***")
    
    print("=" * 80 + "\n")


if __name__ == "__main__":
    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        print("\nVerwendung:")
        print("  python korrigiere_rechtschreibung_vault.py           # Führt Korrekturen aus")
        print("  python korrigiere_rechtschreibung_vault.py --dry-run # Zeigt nur was geändert würde")
        print("  python korrigiere_rechtschreibung_vault.py -d        # Kurz für --dry-run")
        sys.exit(0)
    
    main()

