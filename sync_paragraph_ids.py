#!/usr/bin/env python3
"""
Synchronisiert Paragraph-IDs zwischen exportierten JSON-Dateien und Keyword/Concept-Datenbanken.

WORKFLOW:
=========
1. Laufe NACH dem Export von Obsidian-MD zu steiner-full-lectures-*.json
2. Das Skript vergleicht die aktuellen IDs in den JSON-Dateien mit den Referenzen in:
   - keywords-database.json
   - concepts-database.json
3. Erstellt ein Mapping (alte_ID → neue_ID) über Textvergleich
4. Aktualisiert die Datenbanken mit den neuen IDs

VERWENDUNG:
===========
    python sync_paragraph_ids.py                    # Alle GA-Bände synchronisieren
    python sync_paragraph_ids.py GA210              # Nur GA210 synchronisieren
    python sync_paragraph_ids.py GA210-GA215        # Bereich synchronisieren
    python sync_paragraph_ids.py --dry-run          # Nur anzeigen, nicht ändern
    python sync_paragraph_ids.py --verbose          # Detaillierte Ausgabe

HINWEIS:
========
Das Skript verwendet Textvergleich (fuzzy matching), um alte und neue IDs zu mappen.
Bei starken Textänderungen kann manuelles Eingreifen nötig sein.
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict

# Projekt-Root
PROJECT_ROOT = Path(__file__).parent
LECTURES_DIR = PROJECT_ROOT / "steiner-full-lectures"
KEYWORDS_DB = PROJECT_ROOT / "keywords-database.json"
CONCEPTS_DB = PROJECT_ROOT / "concepts-database.json"


def normalize_text(text: str) -> str:
    """Normalisiert Text für Vergleich (entfernt Whitespace, HTML, etc.)"""
    if not text:
        return ""
    # Entferne HTML-Tags
    text = re.sub(r'<[^>]+>', '', text)
    # Entferne Seitenmarker |XXX|
    text = re.sub(r'\|\d+\|', '', text)
    # Normalisiere Whitespace
    text = ' '.join(text.split())
    # Kleinbuchstaben für Vergleich
    return text.lower().strip()


def text_similarity(text1: str, text2: str) -> float:
    """Berechnet Ähnlichkeit zwischen zwei Texten (0.0 - 1.0)"""
    t1 = normalize_text(text1)
    t2 = normalize_text(text2)
    if not t1 or not t2:
        return 0.0
    return SequenceMatcher(None, t1, t2).ratio()


def load_lectures_json() -> dict:
    """
    Lädt alle Paragraphen aus steiner-full-lectures-*.json.
    Returns: { lecture_id: { index: content, ... }, ... }
    """
    paragraphs_by_lecture = {}
    
    # Prüfe beide mögliche Orte
    search_dirs = [PROJECT_ROOT, LECTURES_DIR]
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        for json_file in search_dir.glob("steiner-full-lectures-*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                lectures = data.get('lectures', [])
                for lecture in lectures:
                    lecture_id = lecture.get('ID', '')
                    if not lecture_id:
                        continue
                    
                    paragraphs = lecture.get('paragraphs', [])
                    para_dict = {}
                    for para in paragraphs:
                        idx = para.get('index', '')
                        content = para.get('content', '')
                        if idx and content:
                            # Normalisiere Index (mit oder ohne ^)
                            idx_clean = idx if idx.startswith('^') else f'^{idx}'
                            para_dict[idx_clean] = content
                    
                    if para_dict:
                        paragraphs_by_lecture[lecture_id] = para_dict
                        
            except Exception as e:
                print(f"  ⚠️  Fehler beim Laden von {json_file.name}: {e}")
    
    return paragraphs_by_lecture


def load_keywords_database() -> dict:
    """Lädt keywords-database.json"""
    if not KEYWORDS_DB.exists():
        print(f"  ⚠️  keywords-database.json nicht gefunden")
        return {}
    
    try:
        with open(KEYWORDS_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ⚠️  Fehler beim Laden von keywords-database.json: {e}")
        return {}


def load_concepts_database() -> list:
    """Lädt concepts-database.json"""
    if not CONCEPTS_DB.exists():
        print(f"  ⚠️  concepts-database.json nicht gefunden")
        return []
    
    try:
        with open(CONCEPTS_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ⚠️  Fehler beim Laden von concepts-database.json: {e}")
        return []


def extract_ga_from_lecture_id(lecture_id: str) -> str:
    """Extrahiert GA-Nummer aus Lecture-ID (z.B. 'GA210/5' -> 'GA210')"""
    match = re.match(r'(GA\d{2,3}[a-z]?)', lecture_id, re.IGNORECASE)
    return match.group(1).upper() if match else ''


def find_best_match(old_index: str, old_content: str, new_paragraphs: dict, 
                    threshold: float = 0.8) -> tuple:
    """
    Findet den besten Match für einen alten Absatz in den neuen Paragraphen.
    Returns: (new_index, similarity) oder (None, 0.0)
    """
    best_match = None
    best_similarity = 0.0
    
    for new_idx, new_content in new_paragraphs.items():
        sim = text_similarity(old_content, new_content)
        if sim > best_similarity and sim >= threshold:
            best_similarity = sim
            best_match = new_idx
    
    return best_match, best_similarity


def build_id_mapping(keywords_db: dict, lectures_data: dict, 
                     ga_filter: set = None, verbose: bool = False) -> dict:
    """
    Baut ein Mapping von alten IDs zu neuen IDs.
    Returns: { 'GA210/5': { '^old_id': '^new_id', ... }, ... }
    """
    mapping = defaultdict(dict)
    stats = {'matched': 0, 'not_found': 0, 'unchanged': 0}
    
    for lecture_id, kw_data in keywords_db.items():
        ga_num = extract_ga_from_lecture_id(lecture_id)
        
        # GA-Filter anwenden
        if ga_filter and ga_num not in ga_filter:
            continue
        
        # Hole die Keywords mit ihren Indizes
        keywords = kw_data.get('keywords', [])
        if not keywords:
            continue
        
        # Hole die neuen Paragraphen für diesen Vortrag
        new_paragraphs = lectures_data.get(lecture_id, {})
        if not new_paragraphs:
            if verbose:
                print(f"  INFO {lecture_id}: Keine Paragraphen in JSON gefunden")
            continue
        
        for kw in keywords:
            old_idx = kw.get('index', '')
            if not old_idx:
                continue
            
            # Normalisiere Index
            old_idx_clean = old_idx if old_idx.startswith('^') else f'^{old_idx}'
            
            # Prüfe ob die ID noch existiert
            if old_idx_clean in new_paragraphs:
                stats['unchanged'] += 1
                continue
            
            # ID existiert nicht mehr - versuche über Heading zu matchen
            heading = kw.get('heading', '')
            if not heading:
                stats['not_found'] += 1
                if verbose:
                    print(f"  ? {lecture_id}: ID {old_idx} nicht gefunden (kein Heading)")
                continue
            
            # Suche nach bestem Match über Text-Ähnlichkeit
            # Verwende das Heading als Anhaltspunkt
            best_match = None
            best_sim = 0.0
            
            for new_idx, new_content in new_paragraphs.items():
                # Prüfe ob das Heading im neuen Content vorkommt
                if heading.lower() in new_content.lower():
                    best_match = new_idx
                    best_sim = 1.0
                    break
                
                # Fallback: Text-Ähnlichkeit
                sim = text_similarity(heading, new_content[:200])  # Nur Anfang
                if sim > best_sim:
                    best_sim = sim
                    best_match = new_idx
            
            if best_match and best_sim >= 0.5:
                mapping[lecture_id][old_idx_clean] = best_match
                stats['matched'] += 1
                if verbose:
                    print(f"  OK {lecture_id}: {old_idx} -> {best_match} (sim={best_sim:.2f})")
            else:
                stats['not_found'] += 1
                if verbose:
                    print(f"  X {lecture_id}: ID {old_idx} konnte nicht gemappt werden")
    
    return mapping, stats


def update_keywords_database(keywords_db: dict, mapping: dict, 
                             dry_run: bool = False) -> int:
    """
    Aktualisiert die Keywords-Datenbank mit neuen IDs.
    Returns: Anzahl der Änderungen
    """
    changes = 0
    
    for lecture_id, id_map in mapping.items():
        if lecture_id not in keywords_db:
            continue
        
        keywords = keywords_db[lecture_id].get('keywords', [])
        for kw in keywords:
            old_idx = kw.get('index', '')
            old_idx_clean = old_idx if old_idx.startswith('^') else f'^{old_idx}'
            
            if old_idx_clean in id_map:
                new_idx = id_map[old_idx_clean]
                if not dry_run:
                    kw['index'] = new_idx
                changes += 1
    
    return changes


def update_concepts_database(concepts_db: list, mapping: dict, 
                             dry_run: bool = False) -> int:
    """
    Aktualisiert die Concepts-Datenbank mit neuen IDs.
    Returns: Anzahl der Änderungen
    """
    changes = 0
    
    # Erstelle flaches Mapping: alle IDs zusammen
    flat_mapping = {}
    for lecture_id, id_map in mapping.items():
        ga_num = extract_ga_from_lecture_id(lecture_id)
        lecture_num = lecture_id.split('/')[-1] if '/' in lecture_id else ''
        
        for old_idx, new_idx in id_map.items():
            # Entferne ^ für Pattern-Matching
            old_clean = old_idx.lstrip('^')
            new_clean = new_idx.lstrip('^')
            flat_mapping[old_clean] = new_clean
    
    if not flat_mapping:
        return 0
    
    # Pattern für ID-Referenzen in Texten: (GA115/4:^ka5rsv) oder (GA115/4:ka5rsv)
    id_pattern = re.compile(r'(\(GA\d{2,3}[a-z]?/\d+:\^?)([a-z0-9]+)(\))')
    
    for concept in concepts_db:
        # Durchsuche alle Text-Felder
        for field in ['text', 'definitionText', 'functionText', 'interactionText', 'specialText']:
            text = concept.get(field, '')
            if not text:
                # Prüfe auch in overview
                overview = concept.get('overview', {})
                if isinstance(overview, dict):
                    text = overview.get(field, '')
            
            if not text:
                continue
            
            def replace_id(match):
                prefix = match.group(1)
                old_id = match.group(2)
                suffix = match.group(3)
                
                if old_id in flat_mapping:
                    nonlocal changes
                    changes += 1
                    return f'{prefix}{flat_mapping[old_id]}{suffix}'
                return match.group(0)
            
            new_text = id_pattern.sub(replace_id, text)
            
            if new_text != text and not dry_run:
                if field in concept:
                    concept[field] = new_text
                else:
                    overview = concept.get('overview', {})
                    if isinstance(overview, dict) and field in overview:
                        overview[field] = new_text
        
        # Aktualisiere auch sources
        sources = concept.get('sources', [])
        for source in sources:
            old_idx = source.get('index', '')
            if not old_idx:
                continue
            old_clean = old_idx.lstrip('^')
            
            if old_clean in flat_mapping:
                if not dry_run:
                    source['index'] = f'^{flat_mapping[old_clean]}'
                changes += 1
    
    return changes


def parse_ga_range(ga_arg: str) -> set:
    """
    Parst GA-Argument zu einer Menge von GA-Nummern.
    Beispiele: 'GA210' -> {'GA210'}, 'GA210-GA215' -> {'GA210', 'GA211', ...}
    """
    ga_set = set()
    
    # Bereich: GA210-GA215
    range_match = re.match(r'GA(\d{2,3})([a-z])?-GA(\d{2,3})([a-z])?', ga_arg, re.IGNORECASE)
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(3))
        for num in range(start, end + 1):
            ga_set.add(f'GA{num:03d}'.upper())
        return ga_set
    
    # Einzelne GA: GA210
    single_match = re.match(r'GA(\d{2,3})([a-z])?', ga_arg, re.IGNORECASE)
    if single_match:
        num = int(single_match.group(1))
        suffix = (single_match.group(2) or '').upper()
        ga_set.add(f'GA{num:03d}{suffix}')
        return ga_set
    
    return ga_set


def main():
    parser = argparse.ArgumentParser(
        description='Synchronisiert Paragraph-IDs zwischen JSON und Datenbanken'
    )
    parser.add_argument('ga_bands', nargs='*', 
                        help='GA-Bände zu synchronisieren (z.B. GA210 oder GA210-GA215)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Nur anzeigen, keine Änderungen speichern')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Detaillierte Ausgabe')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("  PARAGRAPH-ID SYNCHRONISATION")
    print("=" * 70)
    
    # GA-Filter erstellen
    ga_filter = set()
    if args.ga_bands:
        for ga_arg in args.ga_bands:
            ga_filter.update(parse_ga_range(ga_arg))
        print(f"\n  Filter: {', '.join(sorted(ga_filter))}")
    else:
        print("\n  Filter: ALLE GA-Bände")
    
    if args.dry_run:
        print("  Modus: DRY-RUN (keine Änderungen)")
    
    # 1. Lade aktuelle JSON-Daten
    print("\n[1/4] Lade exportierte JSON-Dateien...")
    lectures_data = load_lectures_json()
    print(f"      {len(lectures_data)} Vorträge geladen")
    
    # 2. Lade Keywords-Datenbank
    print("\n[2/4] Lade Keywords-Datenbank...")
    keywords_db = load_keywords_database()
    print(f"      {len(keywords_db)} Einträge geladen")
    
    # 3. Erstelle ID-Mapping
    print("\n[3/4] Erstelle ID-Mapping...")
    mapping, stats = build_id_mapping(keywords_db, lectures_data, 
                                       ga_filter if ga_filter else None,
                                       verbose=args.verbose)
    
    print(f"      Unverändert: {stats['unchanged']}")
    print(f"      Gemappt:     {stats['matched']}")
    print(f"      Nicht gefunden: {stats['not_found']}")
    
    if not mapping:
        print("\n  ✓ Keine IDs müssen aktualisiert werden!")
        return
    
    # 4. Aktualisiere Datenbanken
    print("\n[4/4] Aktualisiere Datenbanken...")
    
    # Keywords
    kw_changes = update_keywords_database(keywords_db, mapping, dry_run=args.dry_run)
    print(f"      Keywords: {kw_changes} Änderungen")
    
    # Concepts
    concepts_db = load_concepts_database()
    concept_changes = update_concepts_database(concepts_db, mapping, dry_run=args.dry_run)
    print(f"      Concepts: {concept_changes} Änderungen")
    
    # Speichern
    if not args.dry_run and (kw_changes > 0 or concept_changes > 0):
        print("\n  Speichere Änderungen...")
        
        if kw_changes > 0:
            with open(KEYWORDS_DB, 'w', encoding='utf-8') as f:
                json.dump(keywords_db, f, ensure_ascii=False, indent=2)
            print(f"      OK keywords-database.json gespeichert")
        
        if concept_changes > 0:
            with open(CONCEPTS_DB, 'w', encoding='utf-8') as f:
                json.dump(concepts_db, f, ensure_ascii=False, indent=2)
            print(f"      OK concepts-database.json gespeichert")
    
    print("\n" + "=" * 70)
    if args.dry_run:
        print("  DRY-RUN abgeschlossen - keine Änderungen gespeichert")
    else:
        print("  Synchronisation abgeschlossen!")
    print("=" * 70)


if __name__ == '__main__':
    main()
