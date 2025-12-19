#!/usr/bin/env python3
"""
Exportiert nur die Wandtafelzeichnungen direkt in steiner-images.
Kein kompletter GA-Band-Export nötig.
"""

import json
import base64
import re
from pathlib import Path

BASE_PATH = Path(__file__).parent.parent / "Steiner_GA"
IMAGES_PATH = Path(__file__).parent.parent / "steiner-images"

# GA-Ordner und ihre Lecture-Nummern-Mappings
GA_CONFIG = {
    "GA073a": {
        "folder": "GA073a-Fachwissenschaften und Anthroposophie",
        "lectures": {
            "27. März 1920": 2,  # GA073a (2.)
        }
    },
    "GA074": {
        "folder": "GA074-Die Philosophie des Thomas von Aquino",
        "lectures": {
            "22. Mai 1920": 1,  # GA074 (1.)
            "23. Mai 1920": 2,  # GA074 (2.)
            "24. Mai 1920": 3,  # GA074 (3.)
        }
    },
    "GA076": {
        "folder": "GA076-Die befruchtende Wirkung der Anthroposophie auf die Fachwissenschaften",
        "lectures": {
            "5. April 1921": 3,   # GA076 (3.)
            "6. April 1921": 4,   # GA076 (4.)
            "7. April 1921": 5,   # GA076 (5.)
        }
    },
    "GA084": {
        "folder": "GA084-Was wollte das Goetheanum und was soll die Anthroposophie",
        "lectures": {
            "14. April 1923": 2,  # GA084 (2.)
            "15. April 1923": 3,  # GA084 (3.)
            "20. April 1923": 4,  # GA084 (4.)
            "21. April 1923": 5,  # GA084 (5.)
            "22. April 1923": 6,  # GA084 (6.)
        }
    },
}

def find_block_id_for_image(md_file: Path, image_filename: str) -> str | None:
    """Findet die Block-ID für ein Bild in einer MD-Datei."""
    content = md_file.read_text(encoding='utf-8')
    # Pattern: ![...](assets/GA074-T01.webp) ^ga074t01
    pattern = rf'\!\[.*?\]\(assets/{re.escape(image_filename)}\)\s*\^(\w+)'
    match = re.search(pattern, content)
    return match.group(1) if match else None


def get_lecture_number_from_filename(md_filename: str) -> int | None:
    """Extrahiert die Vortragsnummer aus dem Dateinamen."""
    # Pattern: GA074 (2.) ... -> 2
    match = re.search(r'GA\d+[a-z]?\s*\((\d+)\.\)', md_filename)
    return int(match.group(1)) if match else None


def main():
    print("=" * 60)
    print("Wandtafelzeichnungen -> steiner-images Export")
    print("=" * 60)
    
    new_images = []
    
    for ga_num, config in GA_CONFIG.items():
        folder_path = BASE_PATH / config["folder"]
        assets_path = folder_path / "assets"
        
        if not assets_path.exists():
            print(f"WARNUNG: Assets-Ordner nicht gefunden: {assets_path}")
            continue
        
        print(f"\n{ga_num}:")
        
        # Finde alle Wandtafel-WebP-Bilder
        for webp_file in sorted(assets_path.glob(f"{ga_num}-T*.webp")):
            print(f"  Verarbeite: {webp_file.name}")
            
            # Extrahiere Tafelnummer aus Dateiname (GA074-T02.webp -> 02)
            tafel_match = re.search(r'-T(\d+)\.webp$', webp_file.name)
            if not tafel_match:
                continue
            tafel_nr = int(tafel_match.group(1))
            
            # Finde die zugehörige MD-Datei mit diesem Bild
            md_file = None
            block_id = None
            lecture_num = None
            
            for md in folder_path.glob("*.md"):
                bid = find_block_id_for_image(md, webp_file.name)
                if bid:
                    block_id = bid
                    md_file = md
                    lecture_num = get_lecture_number_from_filename(md.name)
                    break
            
            if not block_id or not lecture_num:
                print(f"    WARNUNG: Block-ID oder Lecture-Nummer nicht gefunden")
                continue
            
            # Bild in Base64 konvertieren
            with open(webp_file, 'rb') as f:
                image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            # Erstelle Image-Eintrag
            lecture_id = f"{ga_num}/{lecture_num}"
            image_entry = {
                "lectureId": lecture_id,
                "index": f"^{block_id}",
                "altText": f"Tafel {tafel_nr}",
                "path": f"assets/{webp_file.name}",
                "markdownRef": f"![Tafel {tafel_nr}](assets/{webp_file.name})",
                "base64": f"data:image/webp;base64,{base64_data}"
            }
            
            new_images.append(image_entry)
            print(f"    -> {lecture_id} ^{block_id}")
    
    if not new_images:
        print("\nKeine Bilder zum Exportieren gefunden!")
        return
    
    # Speichere in neue steiner-images Datei
    # Finde die nächste verfügbare Part-Nummer
    existing_parts = list(IMAGES_PATH.glob("steiner-images-part*.json"))
    max_part = 0
    for p in existing_parts:
        match = re.search(r'part(\d+)\.json$', p.name)
        if match:
            max_part = max(max_part, int(match.group(1)))
    
    new_part_num = max_part + 1
    output_file = IMAGES_PATH / f"steiner-images-part{new_part_num:02d}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_images, f, ensure_ascii=False, indent=2)
    
    # Berechne Dateigröße
    file_size_kb = output_file.stat().st_size / 1024
    
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"Exportierte Bilder: {len(new_images)}")
    print(f"Ausgabedatei: {output_file.name}")
    print(f"Dateigröße: {file_size_kb:.1f} KB")
    print("\nFertig!")


if __name__ == "__main__":
    main()
