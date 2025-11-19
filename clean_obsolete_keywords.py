#!/usr/bin/env python3
"""
Bereinigt veraltete Schlagworte aus summary-database.json

Entfernt lectureKeywords, die nicht mehr in keywords-database.json vorhanden sind.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def normalize_keyword(term):
    """Normalisiert Keyword für Vergleich (lowercase, strip)"""
    return term.lower().strip()


def load_databases():
    """Lädt beide Datenbanken"""
    project_root = Path(__file__).parent
    
    summary_db_path = project_root / "summary-database.json"
    keywords_db_path = project_root / "keywords-database.json"
    
    if not summary_db_path.exists():
        print(f"[FEHLER] summary-database.json nicht gefunden: {summary_db_path}")
        sys.exit(1)
    
    if not keywords_db_path.exists():
        print(f"[FEHLER] keywords-database.json nicht gefunden: {keywords_db_path}")
        sys.exit(1)
    
    print(f"[INFO] Lade summary-database.json...")
    with open(summary_db_path, 'r', encoding='utf-8') as f:
        summary_db = json.load(f)
    
    print(f"[INFO] Lade keywords-database.json...")
    with open(keywords_db_path, 'r', encoding='utf-8') as f:
        keywords_db = json.load(f)
    
    return summary_db, keywords_db, summary_db_path


def create_backup(filepath):
    """Erstellt ein Backup der Datei"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.parent / f"{filepath.stem}_backup_{timestamp}{filepath.suffix}"
    
    print(f"[BACKUP] Erstelle Backup: {backup_path.name}")
    with open(filepath, 'r', encoding='utf-8') as src:
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    
    return backup_path


def clean_obsolete_keywords(summary_db, keywords_db):
    """Bereinigt veraltete Keywords aus summary-database.json"""
    
    stats = {
        'total_lectures': 0,
        'lectures_with_keywords': 0,
        'lectures_cleaned': 0,
        'total_keywords_before': 0,
        'total_keywords_after': 0,
        'keywords_removed': 0,
        'lectures_without_keywords_db': 0
    }
    
    # Erstelle Mapping: lectureId -> Set der aktuellen Keywords (normalisiert)
    keywords_lookup = {}
    for lecture_id, data in keywords_db.items():
        if 'keywords' in data and isinstance(data['keywords'], list):
            # Erstelle Set der normalisierten Keyword-Terms
            current_keywords = set()
            for kw in data['keywords']:
                if isinstance(kw, dict) and 'term' in kw:
                    normalized = normalize_keyword(kw['term'])
                    current_keywords.add(normalized)
            keywords_lookup[lecture_id] = current_keywords
    
    print(f"[INFO] {len(keywords_lookup)} Vorträge mit Keywords in keywords-database.json gefunden")
    
    # Bereinige jeden Vortrag in summary-database.json
    for lecture_id, data in summary_db.items():
        stats['total_lectures'] += 1
        
        # Prüfe ob lectureKeywords vorhanden sind
        if 'lectureKeywords' not in data or not isinstance(data['lectureKeywords'], list):
            continue
        
        stats['lectures_with_keywords'] += 1
        lecture_keywords = data['lectureKeywords']
        stats['total_keywords_before'] += len(lecture_keywords)
        
        # Hole aktuelle Keywords aus keywords-database.json
        current_keywords_set = keywords_lookup.get(lecture_id, set())
        
        if not current_keywords_set:
            stats['lectures_without_keywords_db'] += 1
            # Wenn keine Keywords in keywords-db vorhanden, behalte alle (könnte neu sein)
            # Oder entferne alle - hier: behalten für Sicherheit
            continue
        
        # Filtere lectureKeywords: Behalte nur die, die auch in keywords-db existieren
        cleaned_keywords = []
        removed_count = 0
        
        for kw in lecture_keywords:
            if isinstance(kw, dict) and 'term' in kw:
                normalized_term = normalize_keyword(kw['term'])
                if normalized_term in current_keywords_set:
                    cleaned_keywords.append(kw)
                else:
                    removed_count += 1
        
        # Aktualisiere lectureKeywords
        if removed_count > 0:
            stats['lectures_cleaned'] += 1
            stats['keywords_removed'] += removed_count
            
            if cleaned_keywords:
                data['lectureKeywords'] = cleaned_keywords
            else:
                # Wenn alle Keywords entfernt wurden, setze leeres Array
                data['lectureKeywords'] = []
        
        stats['total_keywords_after'] += len(data.get('lectureKeywords', []))
    
    return stats


def main():
    """Hauptfunktion"""
    print("\n" + "=" * 70)
    print("  BEREINIGUNG VERALTETER SCHLAGWORTE")
    print("=" * 70 + "\n")
    
    # Lade Datenbanken
    summary_db, keywords_db, summary_db_path = load_databases()
    
    print(f"[INFO] summary-database.json: {len(summary_db)} Vorträge")
    print(f"[INFO] keywords-database.json: {len(keywords_db)} Vorträge\n")
    
    # Erstelle Backup
    backup_path = create_backup(summary_db_path)
    print()
    
    # Bereinige Keywords
    print("[INFO] Bereinige veraltete Keywords...\n")
    stats = clean_obsolete_keywords(summary_db, keywords_db)
    
    # Speichere bereinigte Datei
    print(f"[INFO] Speichere bereinigte summary-database.json...")
    with open(summary_db_path, 'w', encoding='utf-8') as f:
        json.dump(summary_db, f, ensure_ascii=False, indent=2)
    
    # Zeige Statistik
    print("\n" + "=" * 70)
    print("  STATISTIK")
    print("=" * 70)
    print(f"Gesamt Vorträge:                    {stats['total_lectures']}")
    print(f"Vorträge mit lectureKeywords:       {stats['lectures_with_keywords']}")
    print(f"Vorträge bereinigt:                 {stats['lectures_cleaned']}")
    print(f"Vorträge ohne keywords-db Eintrag: {stats['lectures_without_keywords_db']}")
    print()
    print(f"Keywords vorher:                    {stats['total_keywords_before']}")
    print(f"Keywords nachher:                   {stats['total_keywords_after']}")
    print(f"Keywords entfernt:                  {stats['keywords_removed']}")
    print()
    print(f"Backup erstellt:                    {backup_path.name}")
    print("=" * 70 + "\n")
    
    if stats['keywords_removed'] > 0:
        print(f"[OK] {stats['keywords_removed']} veraltete Keywords wurden entfernt!")
    else:
        print("[INFO] Keine veralteten Keywords gefunden.")
    
    print()


if __name__ == "__main__":
    main()

