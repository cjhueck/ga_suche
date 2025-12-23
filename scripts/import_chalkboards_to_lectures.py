#!/usr/bin/env python3
"""
Importiert Wandtafelzeichnungen aus chalkboards.json in steiner-full-lectures.

Matching: GA-Nummer + Datum aus chalkboards.json → Vortrag in steiner-full-lectures

Die Tafeln werden am Ende des Vortrags eingefügt:
- Waagerechte Linie (---)
- Überschrift "Wandtafelzeichnungen"
- Bild(er) der Tafel(n)

WICHTIG: Bei jedem Durchlauf werden bestehende Tafel-Paragraphen ENTFERNT und
neu eingefügt. So verschwinden gelöschte Tafeln automatisch aus den Vorträgen.
"""

import json
from pathlib import Path
from collections import defaultdict

PROJECT_DIR = Path(__file__).parent.parent
CHALKBOARDS_FILE = PROJECT_DIR / "chalkboards.json"
LECTURES_DIR = PROJECT_DIR / "steiner-full-lectures"


def load_chalkboards() -> dict:
    """
    Lädt chalkboards.json und gruppiert nach GA + Datum + optionalem Suffix.
    
    Returns: {("076", "1921-04-05", None): [tafel1, tafel2, ...], 
              ("316", "1924-04-24", "a"): [tafel1, tafel2, ...], ...}
    
    Das Suffix (z.B. "a") wird verwendet bei mehreren Vorträgen am selben Tag:
    - Bilder ohne Suffix → erster Vortrag des Tages
    - Bilder mit "a" → zweiter Vortrag des Tages (z.B. Abendzusammenkunft)
    """
    with open(CHALKBOARDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    grouped = defaultdict(list)
    for cb in data.get('chalkboards', []):
        # Key enthält jetzt auch dateSuffix (kann None sein)
        date_suffix = cb.get('dateSuffix', None)
        key = (cb['ga'], cb['date'], date_suffix)
        grouped[key].append(cb)
    
    # Sortiere Tafeln nach Nummer
    for key in grouped:
        grouped[key].sort(key=lambda x: x.get('tafel', 0))
    
    return dict(grouped)


def ga_number_to_key(ga_number: str) -> str:
    """
    Konvertiert GA-Nummer aus Vortrag (z.B. "GA076") zu chalkboards-Key (z.B. "076").
    """
    if ga_number.startswith("GA"):
        return ga_number[2:]
    return ga_number


def extract_date_suffix(lecture: dict) -> str | None:
    """
    Extrahiert das Datums-Suffix (a, b, c...) aus einem Vortrag.
    
    Erkennt mehrere Vorträge am selben Tag anhand:
    1. Suffix direkt am Jahr: "24. April 1924a" → "a"
    2. Suffix in Klammern: "24. April 1924(a)" → "a"
    3. Schlüsselwörter wie "Abendzusammenkunft", "abends", "nachmittags"
    
    Returns: "a", "b", etc. oder None
    """
    import re
    
    fileName = lecture.get('fileName', '')
    title = lecture.get('title', '')
    
    # Pattern 1: Suffix direkt am Jahr (OHNE Klammern)
    # z.B. "24. April 1924a" oder "1924a"
    # WICHTIG: Das "a" muss am Ende stehen oder von Komma/Leerzeichen gefolgt werden
    pattern_direct = r'\b(\d{4})([a-z])(?:\b|[,\s]|$)'
    
    for text in [fileName, title]:
        match = re.search(pattern_direct, text)
        if match:
            return match.group(2).lower()
    
    # Pattern 2: Suffix in Klammern (a), (b), (c) nach dem Jahr
    # z.B. "24. April 1924(a)"
    pattern_parens = r'\d{4}\s*\(([a-z])\)'
    
    for text in [fileName, title]:
        match = re.search(pattern_parens, text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    
    # Pattern 3: Schlüsselwörter für zweiten Vortrag des Tages (Fallback)
    combined = f"{fileName} {title}".lower()
    
    # "a" für Abendzusammenkunft, abends, Abend-Vortrag
    if any(kw in combined for kw in ['abendzusammenkunft', 'abends', 'abend-', 'abendvortrag']):
        return 'a'
    
    return None


def is_chalkboard_paragraph(paragraph: dict) -> bool:
    """
    Prüft ob ein Paragraph zu den Wandtafelzeichnungen gehört.
    
    Erkennungsmerkmale:
    - Index beginnt mit "^cb" (chalkboard)
    - Content ist "---\n\n## Wandtafelzeichnungen"
    - Content ist ein Tafel-Bild: "![Tafel X](...)"
    """
    index = paragraph.get('index', '')
    content = paragraph.get('content', '')
    
    # Index-basierte Erkennung (primär)
    if index.startswith('^cb'):
        return True
    
    # Content-basierte Erkennung (Fallback für alte Daten)
    if content.startswith('---\n\n## Wandtafelzeichnungen'):
        return True
    if content.startswith('![Tafel '):
        return True
    
    return False


def remove_chalkboard_paragraphs(paragraphs: list) -> tuple[list, int]:
    """
    Entfernt alle Wandtafel-Paragraphen aus einer Paragraph-Liste.
    
    Returns:
        (bereinigte_paragraphen, anzahl_entfernt)
    """
    original_count = len(paragraphs)
    cleaned = [p for p in paragraphs if not is_chalkboard_paragraph(p)]
    removed_count = original_count - len(cleaned)
    return cleaned, removed_count


def create_chalkboard_paragraphs(tafeln: list) -> list:
    """
    Erstellt die Paragraphen für die Wandtafelzeichnungen.
    """
    paragraphs = []
    
    # Waagerechte Linie + Überschrift als erster Paragraph
    first_tafel = tafeln[0]
    first_index = f"^cb{first_tafel['ga']}{first_tafel['date'].replace('-', '')}"
    
    paragraphs.append({
        "index": first_index,
        "content": "---\n\n## Wandtafelzeichnungen"
    })
    
    # Jede Tafel als eigener Paragraph
    for tafel in tafeln:
        tafel_index = f"^cb{tafel['ga']}{tafel['date'].replace('-', '')}t{tafel['tafel']:02d}"
        # Pfad zur Tafel-Datei (relativ zum chalkboards-Ordner)
        img_path = tafel['path']
        alt_text = f"Tafel {tafel['tafel']}"
        
        paragraphs.append({
            "index": tafel_index,
            "content": f"![{alt_text}]({img_path})"
        })
    
    return paragraphs


def process_lectures_file(filepath: Path, chalkboards: dict, ga_filter: set) -> tuple[int, int, int]:
    """
    Verarbeitet eine steiner-full-lectures JSON-Datei.
    
    Bei jedem Durchlauf werden bestehende Tafel-Paragraphen ENTFERNT und
    neu eingefügt. So verschwinden gelöschte Tafeln automatisch.
    
    Returns:
        (anzahl_tafeln_eingefügt, anzahl_vorträge_mit_neuen_tafeln, anzahl_vorträge_bereinigt)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Struktur kann {"lectures": [...]} oder [...] sein
    if isinstance(data, dict) and 'lectures' in data:
        lectures = data['lectures']
        is_wrapped = True
    else:
        lectures = data
        is_wrapped = False
    
    total_tafeln = 0
    lectures_with_new_tafeln = 0
    lectures_cleaned = 0
    modified = False
    
    for lecture in lectures:
        ga_number = lecture.get('gaNumber', '')
        ga_key = ga_number_to_key(ga_number)
        date = lecture.get('date', '')
        lecture_id = lecture.get('ID', '')
        
        # Prüfe GA-Filter
        if ga_filter and ga_key not in ga_filter:
            continue
        
        paragraphs = lecture.get('paragraphs', [])
        
        # SCHRITT 1: Entferne alle bestehenden Tafel-Paragraphen
        cleaned_paragraphs, removed_count = remove_chalkboard_paragraphs(paragraphs)
        
        if removed_count > 0:
            lecture['paragraphs'] = cleaned_paragraphs
            paragraphs = cleaned_paragraphs
            lectures_cleaned += 1
            modified = True
        
        # SCHRITT 2: Prüfe ob neue Tafeln eingefügt werden sollen
        # Extrahiere Datums-Suffix für mehrere Vorträge am selben Tag
        date_suffix = extract_date_suffix(lecture)
        
        # Suche passende Tafeln (mit Suffix)
        key = (ga_key, date, date_suffix)
        tafeln = None
        
        if key in chalkboards:
            tafeln = chalkboards[key]
        elif date_suffix is not None:
            # Fallback: Versuche ohne Suffix (für Abwärtskompatibilität)
            key_no_suffix = (ga_key, date, None)
            if key_no_suffix in chalkboards:
                tafeln = chalkboards[key_no_suffix]
        
        # SCHRITT 3: Füge neue Tafeln ein (falls vorhanden)
        if tafeln:
            tafel_paragraphs = create_chalkboard_paragraphs(tafeln)
            lecture['paragraphs'].extend(tafel_paragraphs)
            
            total_tafeln += len(tafeln)
            lectures_with_new_tafeln += 1
            modified = True
            
            if removed_count > 0:
                print(f"    ~ {lecture_id}: {removed_count} alte entfernt, {len(tafeln)} neue Tafel(n)")
            else:
                print(f"    + {lecture_id}: {len(tafeln)} Tafel(n) eingefuegt")
        elif removed_count > 0:
            # Tafeln wurden entfernt, aber keine neuen eingefügt
            print(f"    - {lecture_id}: {removed_count} Tafel(n) entfernt (keine neuen)")
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            if is_wrapped:
                data['lectures'] = lectures
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                json.dump(lectures, f, ensure_ascii=False, indent=2)
    
    return total_tafeln, lectures_with_new_tafeln, lectures_cleaned


def main(ga_filter: set = None):
    print("=" * 60)
    print("  IMPORTIERE WANDTAFELZEICHNUNGEN IN STEINER-FULL-LECTURES")
    print("=" * 60)
    print()
    print("  HINWEIS: Bestehende Tafeln werden entfernt und neu eingefuegt.")
    print("           Geloeschte Tafeln verschwinden automatisch.")
    print()
    
    if ga_filter:
        print(f"GA-Filter: {', '.join(sorted(ga_filter))}")
        print()
    
    # Lade chalkboards
    print("Lade chalkboards.json...")
    chalkboards = load_chalkboards()
    print(f"  {len(chalkboards)} GA/Datum-Kombinationen gefunden")
    print()
    
    # Verarbeite alle steiner-full-lectures Dateien
    json_files = sorted(LECTURES_DIR.glob("steiner-full-lectures-*.json"))
    print(f"Verarbeite {len(json_files)} Dateien...")
    print()
    
    total_tafeln = 0
    total_lectures_new = 0
    total_lectures_cleaned = 0
    files_modified = 0
    
    for filepath in json_files:
        tafeln, lectures_new, lectures_cleaned = process_lectures_file(filepath, chalkboards, ga_filter)
        if tafeln > 0 or lectures_cleaned > 0:
            files_modified += 1
            total_tafeln += tafeln
            total_lectures_new += lectures_new
            total_lectures_cleaned += lectures_cleaned
    
    print()
    print("=" * 60)
    print(f"  ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"  Dateien modifiziert:     {files_modified}")
    print(f"  Vortraege mit Tafeln:    {total_lectures_new}")
    print(f"  Vortraege bereinigt:     {total_lectures_cleaned}")
    print(f"  Tafeln eingefuegt:       {total_tafeln}")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    # GA-Filter aus Kommandozeile
    ga_filter = None
    if len(sys.argv) > 1:
        ga_filter = set()
        for arg in sys.argv[1:]:
            # Normalisiere: "GA076" -> "076", "ga191" -> "191"
            ga = arg.upper().replace("GA", "")
            ga_filter.add(ga)
    
    main(ga_filter)

