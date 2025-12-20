#!/usr/bin/env python3
"""
Macht alle Wandtafelzeichnungen-Änderungen rückgängig:
1. Löscht alle WZ-Bilder mit Datum-Format (GA*-YYYY-MM-DD-T*.webp)
2. Entfernt "## Wandtafelzeichnungen" Abschnitte aus MD-Dateien

Verwendung:
    python revert_chalkboards.py --dry-run    # Nur anzeigen, was gelöscht würde
    python revert_chalkboards.py              # Tatsächlich löschen
"""

import os
import re
import sys
from pathlib import Path

def find_wz_images(steiner_ga_dir: Path) -> list[Path]:
    """Findet alle WZ-Bilder mit Datum-Format."""
    wz_images = []
    
    # Pattern: GA*-YYYY-MM-DD-T*.webp
    pattern = re.compile(r'^GA\d+[a-z]?-\d{4}-\d{2}-\d{2}-T\d+\.webp$')
    
    for ga_folder in steiner_ga_dir.iterdir():
        if not ga_folder.is_dir() or not ga_folder.name.startswith('GA'):
            continue
        
        assets_dir = ga_folder / 'assets'
        if not assets_dir.exists():
            continue
        
        for img_file in assets_dir.iterdir():
            if pattern.match(img_file.name):
                wz_images.append(img_file)
    
    return wz_images


def remove_wz_sections_from_md(md_file: Path, dry_run: bool = True) -> bool:
    """Entfernt ## Wandtafelzeichnungen Abschnitt aus MD-Datei."""
    try:
        content = md_file.read_text(encoding='utf-8')
        original_content = content
        
        # Pattern für Wandtafelzeichnungen-Abschnitt
        # Entfernt ## Wandtafelzeichnungen und alles danach bis zum Ende der Datei
        # oder bis zur nächsten H2-Überschrift
        pattern = r'\n## Wandtafelzeichnungen\n.*?(?=\n## |\Z)'
        
        new_content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        if new_content != original_content:
            if not dry_run:
                md_file.write_text(new_content, encoding='utf-8')
            return True
        
        return False
        
    except Exception as e:
        print(f"  [FEHLER] {md_file.name}: {e}")
        return False


def find_md_files_with_wz(steiner_ga_dir: Path) -> list[Path]:
    """Findet alle MD-Dateien mit Wandtafelzeichnungen-Abschnitt."""
    md_files = []
    
    for ga_folder in steiner_ga_dir.iterdir():
        if not ga_folder.is_dir() or not ga_folder.name.startswith('GA'):
            continue
        
        # Überspringe GA K 58 Ordner
        if 'GA K 58' in ga_folder.name:
            continue
        
        for md_file in ga_folder.glob('*.md'):
            # Nur Vortrags-Dateien (mit Nummer in Klammern)
            if not re.search(r'\(\d+\.\)', md_file.name):
                continue
            
            try:
                content = md_file.read_text(encoding='utf-8')
                if '## Wandtafelzeichnungen' in content:
                    md_files.append(md_file)
            except:
                pass
    
    return md_files


def main():
    dry_run = '--dry-run' in sys.argv
    
    # Finde Steiner_GA Ordner
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    steiner_ga_dir = project_root / 'Steiner_GA'
    
    if not steiner_ga_dir.exists():
        print(f"FEHLER: Steiner_GA nicht gefunden: {steiner_ga_dir}")
        sys.exit(1)
    
    print("=" * 70)
    print("  WANDTAFELZEICHNUNGEN RÜCKGÄNGIG MACHEN")
    print("=" * 70)
    
    if dry_run:
        print("\n[DRY-RUN] Keine Änderungen werden durchgeführt\n")
    
    # 1. Finde und lösche WZ-Bilder
    print("\n[1/2] Suche WZ-Bilder mit Datum-Format...")
    wz_images = find_wz_images(steiner_ga_dir)
    
    print(f"  Gefunden: {len(wz_images)} Bilder\n")
    
    # Gruppiere nach GA
    by_ga = {}
    for img in wz_images:
        ga_match = re.match(r'(GA\d+[a-z]?)', img.name)
        if ga_match:
            ga = ga_match.group(1)
            if ga not in by_ga:
                by_ga[ga] = []
            by_ga[ga].append(img)
    
    for ga in sorted(by_ga.keys()):
        imgs = by_ga[ga]
        print(f"  {ga}: {len(imgs)} Bilder")
        for img in sorted(imgs, key=lambda x: x.name):
            print(f"    - {img.name}")
            if not dry_run:
                img.unlink()
    
    # 2. Entferne WZ-Abschnitte aus MD-Dateien
    print("\n[2/2] Suche MD-Dateien mit Wandtafelzeichnungen-Abschnitt...")
    md_files = find_md_files_with_wz(steiner_ga_dir)
    
    print(f"  Gefunden: {len(md_files)} MD-Dateien\n")
    
    # Gruppiere nach GA
    md_by_ga = {}
    for md in md_files:
        ga_match = re.match(r'(GA\d+[a-z]?)', md.name)
        if ga_match:
            ga = ga_match.group(1)
            if ga not in md_by_ga:
                md_by_ga[ga] = []
            md_by_ga[ga].append(md)
    
    updated_count = 0
    for ga in sorted(md_by_ga.keys()):
        mds = md_by_ga[ga]
        print(f"  {ga}: {len(mds)} Dateien")
        for md in sorted(mds, key=lambda x: x.name):
            if remove_wz_sections_from_md(md, dry_run):
                updated_count += 1
                print(f"    [OK] {md.name}")
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("  ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"  WZ-Bilder: {len(wz_images)}")
    print(f"  MD-Dateien: {len(md_files)}")
    
    if dry_run:
        print("\n  [DRY-RUN] Keine Änderungen durchgeführt")
        print("  Zum Löschen: python revert_chalkboards.py")
    else:
        print(f"\n  [OK] {len(wz_images)} Bilder geloescht")
        print(f"  [OK] {updated_count} MD-Dateien bereinigt")
    
    print("=" * 70)


if __name__ == '__main__':
    main()
