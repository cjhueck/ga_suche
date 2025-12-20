#!/usr/bin/env python3
"""
Fuegt die Wandtafelzeichnungen-Paragraphen zu den bestehenden Vortraegen 
in steiner-full-lectures hinzu, ohne einen kompletten Neuexport.
"""

import json
import re
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent
LECTURES_PATH = BASE_PATH / "steiner-full-lectures"
STEINER_GA_PATH = BASE_PATH / "Steiner_GA"

# Mapping: GA-Nummer -> (Ordnername, {Datum -> Vortragsnummer})
GA_CONFIG = {
    "GA073a": {
        "folder": "GA073a-Fachwissenschaften und Anthroposophie",
        "lectures": {"27. März 1920": 2}
    },
    "GA074": {
        "folder": "GA074-Die Philosophie des Thomas von Aquino",
        "lectures": {"22. Mai 1920": 1, "23. Mai 1920": 2, "24. Mai 1920": 3}
    },
    "GA076": {
        "folder": "GA076-Die befruchtende Wirkung der Anthroposophie auf die Fachwissenschaften",
        "lectures": {"5. April 1921": 3, "6. April 1921": 4, "7. April 1921": 5}
    },
    "GA084": {
        "folder": "GA084-Was wollte das Goetheanum und was soll die Anthroposophie",
        "lectures": {"14. April 1923": 2, "15. April 1923": 3, "20. April 1923": 4, "21. April 1923": 5, "22. April 1923": 6}
    },
}


def extract_chalkboard_paragraphs(md_file: Path) -> list:
    """Extrahiert die Wandtafelzeichnungen-Paragraphen aus einer MD-Datei."""
    content = md_file.read_text(encoding='utf-8')
    
    paragraphs = []
    
    # Finde den Wandtafelzeichnungen-Abschnitt
    match = re.search(r'## Wandtafelzeichnungen\s*\n(.*)', content, re.DOTALL)
    if not match:
        return []
    
    section = match.group(1)
    
    # Finde alle Bilder mit Block-IDs
    # Pattern: ![Tafel X](assets/GAXXX-TYY.webp) ^blockid
    pattern = r'!\[([^\]]+)\]\(([^)]+)\)\s*\^(\w+)'
    
    for img_match in re.finditer(pattern, section):
        alt_text = img_match.group(1)  # z.B. "Tafel 1"
        img_path = img_match.group(2)  # z.B. "assets/GA074-T01.webp"
        block_id = img_match.group(3)  # z.B. "ga074t01"
        
        # Erstelle Paragraph im gleichen Format wie export-lectures.js
        paragraph = {
            "index": f"^{block_id}",
            "content": f"![{alt_text}]({img_path})"
        }
        paragraphs.append(paragraph)
    
    return paragraphs


def find_lecture_in_json(lectures_data: list, ga_number: str, lecture_num: int) -> dict | None:
    """Findet einen Vortrag in der Lectures-Liste."""
    lecture_id = f"{ga_number}/{lecture_num}"
    
    for lecture in lectures_data:
        # Verschiedene ID-Formate pruefen
        if lecture.get('ID') == lecture_id:
            return lecture
        if lecture.get('gaNumber') == ga_number and lecture.get('lectureNumber') == lecture_num:
            return lecture
    
    return None


def main():
    print("=" * 60)
    print("Wandtafelzeichnungen-Paragraphen hinzufuegen")
    print("=" * 60)
    
    # Sammle alle Aenderungen nach Part-Datei
    changes_by_file = {}
    
    for ga_num, config in GA_CONFIG.items():
        folder_path = STEINER_GA_PATH / config["folder"]
        
        if not folder_path.exists():
            print(f"WARNUNG: Ordner nicht gefunden: {folder_path}")
            continue
        
        print(f"\n{ga_num}:")
        
        for date_pattern, lecture_num in config["lectures"].items():
            # Finde die MD-Datei
            md_file = None
            for md in folder_path.glob("*.md"):
                if date_pattern in md.name and f"({lecture_num}.)" in md.name:
                    md_file = md
                    break
            
            if not md_file:
                print(f"  WARNUNG: MD-Datei nicht gefunden fuer {date_pattern}")
                continue
            
            # Extrahiere Paragraphen
            new_paragraphs = extract_chalkboard_paragraphs(md_file)
            if not new_paragraphs:
                print(f"  WARNUNG: Keine Wandtafelzeichnungen in {md_file.name}")
                continue
            
            print(f"  {lecture_num}. Vortrag ({date_pattern}): {len(new_paragraphs)} Tafel(n)")
            
            # Speichere fuer spaetere Verarbeitung
            lecture_id = f"{ga_num}/{lecture_num}"
            if lecture_id not in changes_by_file:
                changes_by_file[lecture_id] = {
                    "ga_number": ga_num,
                    "lecture_num": lecture_num,
                    "paragraphs": new_paragraphs
                }
    
    if not changes_by_file:
        print("\nKeine Aenderungen gefunden!")
        return
    
    # Finde und aktualisiere die Part-Dateien
    print("\n" + "=" * 60)
    print("Aktualisiere steiner-full-lectures...")
    print("=" * 60)
    
    updated_files = set()
    
    for part_file in sorted(LECTURES_PATH.glob("steiner-full-lectures-*.json")):
        try:
            with open(part_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            lectures = data.get('lectures', [])
            file_modified = False
            
            for lecture in lectures:
                ga_number = lecture.get('gaNumber', '')
                lecture_num = lecture.get('lectureNumber', 0)
                lecture_id = f"{ga_number}/{lecture_num}"
                
                if lecture_id in changes_by_file:
                    change = changes_by_file[lecture_id]
                    new_paragraphs = change["paragraphs"]
                    
                    # Pruefe ob bereits vorhanden
                    existing_indices = {p.get('index', '') for p in lecture.get('paragraphs', [])}
                    paragraphs_to_add = [p for p in new_paragraphs if p['index'] not in existing_indices]
                    
                    if paragraphs_to_add:
                        if 'paragraphs' not in lecture:
                            lecture['paragraphs'] = []
                        lecture['paragraphs'].extend(paragraphs_to_add)
                        file_modified = True
                        print(f"  + {lecture_id}: {len(paragraphs_to_add)} Paragraph(en) hinzugefuegt")
                    else:
                        print(f"  = {lecture_id}: Bereits vorhanden")
            
            if file_modified:
                with open(part_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                updated_files.add(part_file.name)
        
        except Exception as e:
            print(f"  FEHLER bei {part_file.name}: {e}")
    
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"Aktualisierte Dateien: {len(updated_files)}")
    for f in sorted(updated_files):
        print(f"  - {f}")
    print("\nFertig! Server neu starten um Aenderungen zu sehen.")


if __name__ == "__main__":
    main()





