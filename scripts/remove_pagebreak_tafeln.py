#!/usr/bin/env python3
"""
Entfernt redundante Wandtafel-Einträge am ENDE von Vorträgen in pagebreak-books.

WICHTIG: Nur Tafel-Einträge am ENDE eines Vortrags werden entfernt,
NICHT die Bilder, die im Text eingebettet sind!

Die Einträge am Ende haben typischerweise das Format:
- <img src="assets/GA191-1919-10-04-T02.webp" alt="Tafel 2" />
- <h2>Wandtafelzeichnungen</h2>\n<img src="..." />
- ![Tafel X](assets/GAXXX-TXX.webp)

Diese sind redundant, weil das Frontend die Wandtafelzeichnungen
bereits automatisch aus chalkboards.json lädt.
"""

import json
import re
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
PAGEBREAK_DIR = PROJECT_DIR / "pagebreak-books"

# Muster für Tafel-Einträge am Ende (verschiedene Formate)
TAFEL_PATTERNS = [
    # HTML-Format: <img src="assets/GA191-1919-10-04-T02.webp" alt="Tafel 2" />
    re.compile(r'^<img\s+src="assets/GA\d+-\d{4}-\d{2}-\d{2}-T\d+\.webp"\s+alt="Tafel\s+\d+"\s*/>$'),
    # Mit Überschrift: <h2>Wandtafelzeichnungen</h2>\n<img ...>
    re.compile(r'^<h2>Wandtafelzeichnungen</h2>\s*\n?\s*<img\s+src="assets/GA\d+-\d{4}-\d{2}-\d{2}-T\d+\.webp"\s+alt="Tafel\s+\d+"\s*/>$'),
    # Markdown ohne GA: ![Tafel X](assets/GAXXX-TXX.webp)
    re.compile(r'^!\[Tafel\s+\d+\]\(assets/GA\d+-T\d+\.webp\)$'),
    # Markdown mit Überschrift
    re.compile(r'^<h2>Wandtafelzeichnungen</h2>\s*\n?\s*!\[Tafel\s+\d+\]\(assets/GA\d+-T\d+\.webp\)$'),
    # Kurzes Format: ![211-T01](assets/211-T01.webp)
    re.compile(r'^!\[\d+-T\d+\]\(assets/\d+-T\d+\.webp\)$'),
]


def is_tafel_only_paragraph(content: str) -> bool:
    """
    Prüft ob ein Paragraph NUR ein Tafel-Eintrag ist (keine weiteren Inhalte).
    Wichtig: Gibt nur True zurück wenn der GESAMTE Inhalt ein Tafel-Bild ist.
    """
    content = content.strip()
    for pattern in TAFEL_PATTERNS:
        if pattern.match(content):
            return True
    return False


def find_trailing_tafel_entries(paragraphs: list) -> int:
    """
    Findet die Anzahl der Tafel-Einträge am ENDE der Paragraphen-Liste.
    Zählt von hinten, wie viele aufeinanderfolgende Tafel-Einträge es gibt.
    """
    count = 0
    for i in range(len(paragraphs) - 1, -1, -1):
        content = paragraphs[i].get('content', '')
        if is_tafel_only_paragraph(content):
            count += 1
        else:
            # Sobald ein Nicht-Tafel-Eintrag gefunden wird, aufhören
            break
    return count


def process_file(filepath: Path) -> tuple[int, int]:
    """
    Verarbeitet eine JSON-Datei und entfernt Tafel-Einträge am ENDE.
    
    Returns:
        (anzahl_entfernt, anzahl_vortraege_betroffen)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_removed = 0
    lectures_affected = 0
    
    lectures = data if isinstance(data, list) else data.get('lectures', [])
    
    for lecture in lectures:
        if 'paragraphs' not in lecture:
            continue
        
        # Finde Tafel-Einträge am ENDE
        trailing_count = find_trailing_tafel_entries(lecture['paragraphs'])
        
        if trailing_count > 0:
            # Entferne nur die letzten N Einträge
            lecture['paragraphs'] = lecture['paragraphs'][:-trailing_count]
            total_removed += trailing_count
            lectures_affected += 1
    
    if total_removed > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data if isinstance(data, dict) else lectures, f, ensure_ascii=False, indent=2)
    
    return total_removed, lectures_affected


def main():
    print("=" * 60)
    print("  ENTFERNE TAFEL-EINTRÄGE AM ENDE VON VORTRÄGEN")
    print("  (Bilder im Text werden NICHT entfernt!)")
    print("=" * 60)
    print()
    
    if not PAGEBREAK_DIR.exists():
        print(f"FEHLER: Verzeichnis nicht gefunden: {PAGEBREAK_DIR}")
        return
    
    json_files = sorted(PAGEBREAK_DIR.glob("GA*.json"))
    print(f"Gefundene Dateien: {len(json_files)}")
    print()
    
    total_removed = 0
    total_lectures = 0
    files_modified = 0
    
    for filepath in json_files:
        removed, lectures = process_file(filepath)
        if removed > 0:
            print(f"  {filepath.name}: {removed} Einträge entfernt ({lectures} Vorträge)")
            total_removed += removed
            total_lectures += lectures
            files_modified += 1
    
    print()
    print("=" * 60)
    print(f"  ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"  Dateien modifiziert: {files_modified}")
    print(f"  Vorträge betroffen: {total_lectures}")
    print(f"  Einträge entfernt: {total_removed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
