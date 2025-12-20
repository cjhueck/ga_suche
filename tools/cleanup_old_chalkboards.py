#!/usr/bin/env python3
"""
Cleanup-Skript für alte Wandtafelzeichnungen.

Entfernt alte WZ-Dateien (Format: XXX-TYY.webp) und deren Markdown-Referenzen
aus den Vortrags-MD-Dateien.

Usage:
    python cleanup_old_chalkboards.py [--dry-run]
"""

import os
import re
import sys
from pathlib import Path

# Pfade
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
STEINER_GA_DIR = PROJECT_DIR / "Steiner_GA"

def find_old_wz_files(steiner_ga_dir: Path) -> list[tuple[Path, str]]:
    """Findet alle alten WZ-Dateien (Format: XXX-TYY.webp)."""
    old_wz = []
    
    for ga_dir in steiner_ga_dir.iterdir():
        if not ga_dir.is_dir() or not ga_dir.name.startswith("GA"):
            continue
        
        # Suche in assets-Ordnern
        for assets_dir in ga_dir.rglob("assets"):
            if not assets_dir.is_dir():
                continue
            
            for wz_file in assets_dir.glob("*.webp"):
                # Altes Format: XXX-TYY.webp (z.B. 211-T01.webp)
                if re.match(r'^\d+-T\d+\.webp$', wz_file.name):
                    ga_match = re.match(r'^GA(\d+)', ga_dir.name)
                    if ga_match:
                        old_wz.append((wz_file, f"GA{ga_match.group(1)}"))
    
    return old_wz


def find_md_files_with_old_refs(steiner_ga_dir: Path, ga_number: str) -> list[tuple[Path, list[str]]]:
    """Findet MD-Dateien mit Referenzen zu alten WZ."""
    md_files_with_refs = []
    
    # Extrahiere numerischen Teil (z.B. "211" aus "GA211")
    num = re.match(r'GA(\d+)', ga_number).group(1)
    
    # Pattern für alte WZ-Referenzen: ![...](assets/XXX-TYY.webp) oder ![...](XXX-TYY.webp)
    pattern = rf'!\[[^\]]*\]\([^)]*{num}-T\d+\.webp[^)]*\)'
    
    for ga_dir in steiner_ga_dir.iterdir():
        if not ga_dir.is_dir() or not ga_dir.name.startswith(ga_number):
            continue
        
        for md_file in ga_dir.glob("*.md"):
            content = md_file.read_text(encoding='utf-8')
            matches = re.findall(pattern, content)
            if matches:
                md_files_with_refs.append((md_file, matches))
        
        # Auch in Unterordnern suchen
        for md_file in ga_dir.rglob("*.md"):
            if md_file.parent == ga_dir:
                continue  # Bereits oben behandelt
            content = md_file.read_text(encoding='utf-8')
            matches = re.findall(pattern, content)
            if matches:
                md_files_with_refs.append((md_file, matches))
    
    return md_files_with_refs


def remove_old_wz_section(content: str, ga_number: str) -> str:
    """Entfernt den alten Wandtafelzeichnungen-Abschnitt aus dem Content."""
    num = re.match(r'GA(\d+)', ga_number).group(1)
    
    # Pattern für den gesamten WZ-Abschnitt am Ende der Datei
    # Matches: ## Wandtafelzeichnungen\n![...](assets/XXX-TYY.webp)...\n bis zum Ende
    pattern = rf'\n## Wandtafelzeichnungen\n(!\[[^\]]*\]\([^)]*{num}-T\d+\.webp[^)]*\)[^\n]*\n?)+'
    
    content = re.sub(pattern, '', content)
    
    # Auch einzelne WZ-Referenzen entfernen (falls nicht im Abschnitt)
    pattern2 = rf'!\[[^\]]*\]\([^)]*{num}-T\d+\.webp[^)]*\)\s*\^?\w*\n?'
    content = re.sub(pattern2, '', content)
    
    return content


def cleanup_old_chalkboards(dry_run: bool = True):
    """Hauptfunktion: Entfernt alte WZ-Dateien und Referenzen."""
    
    print("=" * 70)
    print("  CLEANUP ALTE WANDTAFELZEICHNUNGEN")
    print("=" * 70)
    
    if dry_run:
        print("[DRY-RUN] Keine Änderungen werden durchgeführt\n")
    
    # Finde alle alten WZ-Dateien
    old_wz = find_old_wz_files(STEINER_GA_DIR)
    
    if not old_wz:
        print("Keine alten WZ-Dateien gefunden.")
        return
    
    # Gruppiere nach GA-Nummer
    by_ga = {}
    for wz_file, ga_num in old_wz:
        if ga_num not in by_ga:
            by_ga[ga_num] = []
        by_ga[ga_num].append(wz_file)
    
    print(f"Gefunden: {len(old_wz)} alte WZ-Dateien in {len(by_ga)} GA-Bänden\n")
    
    total_files_deleted = 0
    total_refs_removed = 0
    
    for ga_num in sorted(by_ga.keys()):
        wz_files = by_ga[ga_num]
        print(f"\n{ga_num}:")
        print(f"  {len(wz_files)} WZ-Dateien zum Löschen")
        
        # Lösche Dateien
        for wz_file in wz_files:
            if dry_run:
                print(f"    [würde löschen] {wz_file.name}")
            else:
                try:
                    wz_file.unlink()
                    print(f"    [gelöscht] {wz_file.name}")
                    total_files_deleted += 1
                except Exception as e:
                    print(f"    [FEHLER] {wz_file.name}: {e}")
        
        # Finde und bereinige MD-Dateien
        md_files = find_md_files_with_old_refs(STEINER_GA_DIR, ga_num)
        
        if md_files:
            print(f"  {len(md_files)} MD-Dateien mit Referenzen")
            
            for md_file, refs in md_files:
                if dry_run:
                    print(f"    [würde bereinigen] {md_file.name} ({len(refs)} Refs)")
                else:
                    try:
                        content = md_file.read_text(encoding='utf-8')
                        new_content = remove_old_wz_section(content, ga_num)
                        
                        if new_content != content:
                            md_file.write_text(new_content, encoding='utf-8')
                            total_refs_removed += len(refs)
                            print(f"    [bereinigt] {md_file.name} ({len(refs)} Refs entfernt)")
                    except Exception as e:
                        print(f"    [FEHLER] {md_file.name}: {e}")
    
    print("\n" + "=" * 70)
    print("  ZUSAMMENFASSUNG")
    print("=" * 70)
    
    if dry_run:
        print(f"  [DRY-RUN] Würde {len(old_wz)} Dateien löschen")
        print(f"  [DRY-RUN] Keine Änderungen durchgeführt")
        print(f"\n  Zum Ausführen: python cleanup_old_chalkboards.py")
    else:
        print(f"  Dateien gelöscht: {total_files_deleted}")
        print(f"  Referenzen entfernt: {total_refs_removed}")
    
    print("=" * 70)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    execute = "--execute" in sys.argv or "-x" in sys.argv
    
    if not dry_run and not execute:
        print("Usage: python cleanup_old_chalkboards.py [--dry-run | --execute]")
        print("  --dry-run  : Zeige was gelöscht würde (Standard)")
        print("  --execute  : Führe Löschung durch")
        sys.exit(1)
    
    cleanup_old_chalkboards(dry_run=not execute)


