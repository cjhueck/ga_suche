#!/usr/bin/env python3
"""
Überträgt Absatz-IDs (Obsidian Block-IDs) von einer alten Markdown-Datei in eine neue.

Verwendung:
    python transfer_paragraph_ids.py <alte_datei> <neue_datei> [--dry-run]

Beispiel:
    python transfer_paragraph_ids.py "GA228_alt.md" "GA228_neu.md"
    python transfer_paragraph_ids.py "GA228_alt.md" "GA228_neu.md" --dry-run

Optionen:
    --dry-run    Zeigt nur an, was übertragen würde, ohne die Datei zu ändern
"""

import re
import sys
import argparse
from pathlib import Path
from difflib import SequenceMatcher


def normalize_text(text):
    """Normalisiert Text für Vergleich."""
    # Entferne BOM-Zeichen
    text = text.replace('\ufeff', '')
    # Entferne Seitenmarker |123|
    text = re.sub(r'\|(\d+)\|', '', text)
    # Entferne Block-IDs
    text = re.sub(r'\s*\^[a-z0-9]+\s*$', '', text)
    # Normalisiere Rechtschreibung (alte -> neue)
    replacements = [
        ('daß', 'dass'), ('Daß', 'Dass'),
        ('muß', 'muss'), ('Muß', 'Muss'),
        ('läßt', 'lässt'), ('Läßt', 'Lässt'),
        ('faßt', 'fasst'), ('Faßt', 'Fasst'),
        ('haßt', 'hasst'), ('Haßt', 'Hasst'),
        ('paßt', 'passt'), ('Paßt', 'Passt'),
        ('wußt', 'wusst'), ('Wußt', 'Wusst'),
        ('bewußt', 'bewusst'), ('Bewußt', 'Bewusst'),
        ('unbewußt', 'unbewusst'), ('Unbewußt', 'Unbewusst'),
        ('gewiß', 'gewiss'), ('Gewiß', 'Gewiss'),
        ('miß', 'miss'), ('Miß', 'Miss'),
        ('Einfluß', 'Einfluss'), ('einfluß', 'einfluss'),
        ('Schluß', 'Schluss'), ('schluß', 'schluss'),
        ('Umriß', 'Umriss'), ('umriß', 'umriss'),
        ('Abriß', 'Abriss'), ('abriß', 'abriss'),
        ('Riß', 'Riss'), ('riß', 'riss'),
        ('Fluß', 'Fluss'), ('fluß', 'fluss'),
        ('Kuß', 'Kuss'), ('kuß', 'kuss'),
        ('Nuß', 'Nuss'), ('nuß', 'nuss'),
        ('Schuß', 'Schuss'), ('schuß', 'schuss'),
        ('Schloß', 'Schloss'), ('schloß', 'schloss'),
        ('groß', 'gross'), ('Groß', 'Gross'),  # Schweizer Schreibweise
    ]
    for old, new in replacements:
        text = text.replace(old, new)
        text = text.replace(new, old)  # Auch umgekehrt normalisieren
    
    # Entferne Zeichnungs-Referenzen
    text = re.sub(r'\[.*?Zeichnung.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(siehe Zeichnung.*?\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[.*?Tafel.*?\]', '', text, flags=re.IGNORECASE)
    
    # Normalisiere Whitespace
    text = ' '.join(text.split())
    text = text.strip()
    return text


def extract_paragraphs_with_ids(content):
    """Extrahiert Absätze mit IDs aus der alten Datei."""
    paragraphs = []
    
    # Teile nach Absätzen (doppelte Newlines)
    blocks = re.split(r'\n\n+', content)
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        # Suche nach Block-ID am Ende
        id_match = re.search(r'\^([a-z0-9]+)\s*$', block)
        if id_match:
            block_id = id_match.group(1)
            # Entferne ID vom Text für Vergleich
            text_without_id = re.sub(r'\s*\^[a-z0-9]+\s*$', '', block)
            normalized = normalize_text(text_without_id)
            
            if len(normalized) > 50:  # Nur substantielle Absätze
                paragraphs.append({
                    'id': block_id,
                    'original': block,
                    'normalized': normalized,
                    'first_words': ' '.join(normalized.split()[:10])
                })
    
    return paragraphs


def find_best_match(old_para, new_lines, used_indices):
    """Findet den besten passenden Absatz in der neuen Datei."""
    best_match = None
    best_ratio = 0
    best_idx = -1
    
    old_normalized = old_para['normalized']
    old_first_words = old_para['first_words']
    
    for idx, new_line in enumerate(new_lines):
        if idx in used_indices:
            continue
            
        new_normalized = normalize_text(new_line)
        
        if len(new_normalized) < 50:
            continue
        
        # Schnelle Prüfung: Erste Wörter vergleichen
        new_first_words = ' '.join(new_normalized.split()[:10])
        
        if old_first_words[:30].lower() in new_first_words[:50].lower() or \
           new_first_words[:30].lower() in old_first_words[:50].lower():
            # Detaillierter Vergleich
            ratio = SequenceMatcher(None, old_normalized[:500], new_normalized[:500]).ratio()
            
            if ratio > best_ratio and ratio > 0.7:
                best_ratio = ratio
                best_match = new_line
                best_idx = idx
    
    return best_idx, best_match, best_ratio


def transfer_ids(old_file: Path, new_file: Path, dry_run: bool = False):
    """Überträgt IDs von alter zu neuer Datei."""
    print("=" * 60)
    print("Absatz-ID Transfer")
    print("=" * 60)
    print(f"Alte Datei: {old_file.name}")
    print(f"Neue Datei: {new_file.name}")
    if dry_run:
        print("[DRY RUN - keine Aenderungen werden gespeichert]")
    print()
    
    # Prüfe ob Dateien existieren
    if not old_file.exists():
        print(f"FEHLER: Alte Datei nicht gefunden: {old_file}")
        return False
    if not new_file.exists():
        print(f"FEHLER: Neue Datei nicht gefunden: {new_file}")
        return False
    
    # Lese Dateien
    old_content = old_file.read_text(encoding='utf-8')
    new_content = new_file.read_text(encoding='utf-8')
    
    # Extrahiere Absätze mit IDs aus alter Datei
    old_paragraphs = extract_paragraphs_with_ids(old_content)
    print(f"Gefunden: {len(old_paragraphs)} Absaetze mit IDs in alter Datei")
    
    if len(old_paragraphs) == 0:
        print("FEHLER: Keine Absaetze mit IDs in alter Datei gefunden!")
        return False
    
    # Teile neue Datei in Zeilen
    new_lines = new_content.split('\n')
    
    # Prüfe ob neue Datei bereits IDs hat
    existing_ids = len(re.findall(r'\^[a-z0-9]+\s*$', new_content, re.MULTILINE))
    if existing_ids > 0:
        print(f"Hinweis: Neue Datei hat bereits {existing_ids} IDs")
    
    # Tracking
    matches = []
    used_indices = set()
    
    # Finde Matches
    print("\nSuche Matches...")
    for i, old_para in enumerate(old_paragraphs):
        idx, match, ratio = find_best_match(old_para, new_lines, used_indices)
        
        if idx >= 0:
            matches.append({
                'old_para': old_para,
                'new_idx': idx,
                'ratio': ratio
            })
            used_indices.add(idx)
            
            if (i + 1) % 50 == 0:
                print(f"  Verarbeitet: {i + 1}/{len(old_paragraphs)}")
    
    print(f"\nGefunden: {len(matches)} Matches ({len(matches)*100//len(old_paragraphs)}%)")
    
    # Zeige einige Beispiele
    if matches:
        print("\nBeispiel-Matches:")
        for m in matches[:3]:
            print(f"  ID: ^{m['old_para']['id']} (Ratio: {m['ratio']:.2f})")
            print(f"    Text: {m['old_para']['first_words'][:60]}...")
            print()
    
    if dry_run:
        print("[DRY RUN] Wuerde diese IDs uebertragen - keine Aenderungen gespeichert")
    else:
        # Füge IDs in neue Datei ein
        print("Fuege IDs ein...")
        
        # Sortiere nach Index (rückwärts, um Indizes nicht zu verschieben)
        matches_sorted = sorted(matches, key=lambda x: x['new_idx'], reverse=True)
        
        ids_added = 0
        for m in matches_sorted:
            idx = m['new_idx']
            block_id = m['old_para']['id']
            
            line = new_lines[idx]
            
            # Prüfe ob bereits eine ID vorhanden ist
            if re.search(r'\^[a-z0-9]+\s*$', line):
                continue
            
            # Füge ID am Ende der Zeile hinzu
            new_lines[idx] = line.rstrip() + f" ^{block_id}"
            ids_added += 1
        
        # Schreibe neue Datei
        new_content_with_ids = '\n'.join(new_lines)
        new_file.write_text(new_content_with_ids, encoding='utf-8')
        
        print(f"\n[OK] {ids_added} IDs uebertragen")
        print(f"[OK] Datei gespeichert: {new_file}")
    
    # Zeige nicht gefundene
    not_found = len(old_paragraphs) - len(matches)
    if not_found > 0:
        print(f"\n[!] {not_found} Absaetze ohne Match:")
        count = 0
        for old_para in old_paragraphs:
            if old_para['id'] not in [m['old_para']['id'] for m in matches]:
                print(f"  ^{old_para['id']}: {old_para['first_words'][:60]}...")
                count += 1
                if count >= 20:
                    remaining = not_found - count
                    if remaining > 0:
                        print(f"  ... und {remaining} weitere")
                    break
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Uebertraegt Absatz-IDs von einer alten Markdown-Datei in eine neue.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Beispiele:
  python transfer_paragraph_ids.py "GA228_alt.md" "GA228_neu.md"
  python transfer_paragraph_ids.py "alte_datei.md" "neue_datei.md" --dry-run
        '''
    )
    parser.add_argument('old_file', type=str, help='Pfad zur alten Datei (mit IDs)')
    parser.add_argument('new_file', type=str, help='Pfad zur neuen Datei (ohne IDs)')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Zeigt nur an, was uebertragen wuerde, ohne zu speichern')
    
    args = parser.parse_args()
    
    old_path = Path(args.old_file)
    new_path = Path(args.new_file)
    
    success = transfer_ids(old_path, new_path, args.dry_run)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
