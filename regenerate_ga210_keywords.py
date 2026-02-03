#!/usr/bin/env python3
"""
Regeneriert Keywords und Concept-Links für GA210.

SICHERHEIT:
- Entfernt NUR GA210-Einträge aus keywords-database.json
- Entfernt NUR GA210-Referenzen aus concepts-database.json
- Erstellt Backups vor jeder Änderung
- Alle anderen GA-Bände bleiben UNVERÄNDERT

WORKFLOW:
1. Backup der Datenbanken erstellen
2. GA210-Einträge aus keywords-database.json entfernen
3. GA210-Referenzen aus concepts-database.json entfernen
4. Zusammenfassung anzeigen

HINWEIS:
Nach Ausführung dieses Skripts müssen die Keywords über das Backend
neu generiert werden (z.B. über die Web-App mit "Neu generieren").
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
KEYWORDS_DB = PROJECT_ROOT / "keywords-database.json"
CONCEPTS_DB = PROJECT_ROOT / "concepts-database.json"
BACKUP_DIR = PROJECT_ROOT / "_backups"


def create_backup(file_path: Path) -> Path:
    """Erstellt ein Backup einer Datei."""
    if not file_path.exists():
        return None
    
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = BACKUP_DIR / backup_name
    
    shutil.copy2(file_path, backup_path)
    return backup_path


def clean_keywords_database() -> dict:
    """
    Entfernt alle GA210-Einträge aus keywords-database.json.
    Returns: Statistiken über entfernte Einträge
    """
    if not KEYWORDS_DB.exists():
        print("  keywords-database.json nicht gefunden!")
        return {'removed': 0, 'total': 0}
    
    with open(KEYWORDS_DB, 'r', encoding='utf-8') as f:
        kw_db = json.load(f)
    
    original_count = len(kw_db)
    
    # Finde GA210-Einträge
    ga210_keys = [k for k in kw_db.keys() if k.upper().startswith('GA210')]
    
    # Zähle Keywords vor dem Entfernen
    removed_keywords = 0
    for key in ga210_keys:
        keywords = kw_db[key].get('keywords', [])
        removed_keywords += len(keywords)
        del kw_db[key]
    
    # Speichern
    with open(KEYWORDS_DB, 'w', encoding='utf-8') as f:
        json.dump(kw_db, f, ensure_ascii=False, indent=2)
    
    return {
        'removed_lectures': len(ga210_keys),
        'removed_keywords': removed_keywords,
        'remaining_lectures': len(kw_db)
    }


def clean_concepts_database() -> dict:
    """
    Entfernt alle GA210-Referenzen aus concepts-database.json.
    Returns: Statistiken über entfernte Referenzen
    """
    if not CONCEPTS_DB.exists():
        print("  concepts-database.json nicht gefunden!")
        return {'modified': 0, 'removed_refs': 0}
    
    with open(CONCEPTS_DB, 'r', encoding='utf-8') as f:
        concepts_db = json.load(f)
    
    # Pattern für GA210-Referenzen: (GA210/X:^abc123) oder GA210/X:abc123
    ga210_pattern = re.compile(r'\(GA210/\d+:\^?[a-z0-9]+\)')
    ga210_source_pattern = re.compile(r'^GA210/', re.IGNORECASE)
    
    modified_concepts = 0
    removed_text_refs = 0
    removed_sources = 0
    
    for concept in concepts_db:
        concept_modified = False
        
        # Entferne GA210-Referenzen aus Textfeldern
        for field in ['text', 'definitionText', 'functionText', 'interactionText', 'specialText']:
            # Prüfe Hauptebene
            if field in concept and concept[field]:
                new_text = ga210_pattern.sub('', concept[field])
                if new_text != concept[field]:
                    # Bereinige doppelte Leerzeichen und Kommas
                    new_text = re.sub(r',\s*,', ',', new_text)
                    new_text = re.sub(r'\s+', ' ', new_text)
                    new_text = re.sub(r',\s*\.', '.', new_text)
                    concept[field] = new_text.strip()
                    removed_text_refs += 1
                    concept_modified = True
            
            # Prüfe overview-Ebene
            overview = concept.get('overview', {})
            if isinstance(overview, dict) and field in overview and overview[field]:
                new_text = ga210_pattern.sub('', overview[field])
                if new_text != overview[field]:
                    new_text = re.sub(r',\s*,', ',', new_text)
                    new_text = re.sub(r'\s+', ' ', new_text)
                    new_text = re.sub(r',\s*\.', '.', new_text)
                    overview[field] = new_text.strip()
                    removed_text_refs += 1
                    concept_modified = True
        
        # Entferne GA210-Sources
        sources = concept.get('sources', [])
        original_sources_count = len(sources)
        concept['sources'] = [
            s for s in sources 
            if not ga210_source_pattern.match(s.get('id', ''))
        ]
        removed = original_sources_count - len(concept['sources'])
        if removed > 0:
            removed_sources += removed
            concept_modified = True
        
        if concept_modified:
            modified_concepts += 1
    
    # Speichern
    with open(CONCEPTS_DB, 'w', encoding='utf-8') as f:
        json.dump(concepts_db, f, ensure_ascii=False, indent=2)
    
    return {
        'modified_concepts': modified_concepts,
        'removed_text_refs': removed_text_refs,
        'removed_sources': removed_sources,
        'total_concepts': len(concepts_db)
    }


def main():
    print("=" * 70)
    print("  GA210 KEYWORDS & CONCEPTS BEREINIGUNG")
    print("=" * 70)
    print("\nDieses Skript entfernt NUR GA210-Daten.")
    print("Alle anderen GA-Baende bleiben UNVERAENDERT.\n")
    
    # 1. Backups erstellen
    print("[1/3] Erstelle Backups...")
    
    kw_backup = create_backup(KEYWORDS_DB)
    if kw_backup:
        print(f"      keywords-database.json -> {kw_backup.name}")
    
    concepts_backup = create_backup(CONCEPTS_DB)
    if concepts_backup:
        print(f"      concepts-database.json -> {concepts_backup.name}")
    
    # 2. Keywords-Database bereinigen
    print("\n[2/3] Bereinige keywords-database.json...")
    kw_stats = clean_keywords_database()
    print(f"      Entfernte Vortraege: {kw_stats.get('removed_lectures', 0)}")
    print(f"      Entfernte Keywords:  {kw_stats.get('removed_keywords', 0)}")
    print(f"      Verbleibende Vortraege: {kw_stats.get('remaining_lectures', 0)}")
    
    # 3. Concepts-Database bereinigen
    print("\n[3/3] Bereinige concepts-database.json...")
    concept_stats = clean_concepts_database()
    print(f"      Modifizierte Concepts: {concept_stats['modified_concepts']}")
    print(f"      Entfernte Text-Referenzen: {concept_stats['removed_text_refs']}")
    print(f"      Entfernte Sources: {concept_stats['removed_sources']}")
    print(f"      Concepts gesamt: {concept_stats['total_concepts']}")
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("  ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"""
  Keywords-Database:
    - {kw_stats.get('removed_lectures', 0)} GA210-Vortraege entfernt
    - {kw_stats.get('removed_keywords', 0)} Keywords entfernt
    
  Concepts-Database:
    - {concept_stats['modified_concepts']} Concepts modifiziert
    - {concept_stats['removed_text_refs']} Text-Referenzen entfernt
    - {concept_stats['removed_sources']} Source-Eintraege entfernt
    
  Backups erstellt in: {BACKUP_DIR}
""")
    
    print("  NAECHSTE SCHRITTE:")
    print("  1. Server neu starten (falls lokal)")
    print("  2. In der Web-App: GA210 Vortraege oeffnen")
    print("  3. 'Neu generieren' klicken fuer jeden Vortrag")
    print("     ODER: Batch-Regeneration ueber API nutzen")
    print("=" * 70)


if __name__ == '__main__':
    main()
