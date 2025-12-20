#!/usr/bin/env python3
"""
Skript zur Integration der Wandtafelzeichnungen aus GA K 58_1 in die entsprechenden GA-Vorträge.

Das Skript:
1. Liest JPEG-Bilder aus dem Wandtafelzeichnungen-Ordner
2. Dreht sie um 90° nach links (counterclockwise)
3. Konvertiert sie zu WebP (kleinere Dateigröße)
4. Speichert sie im assets-Ordner des jeweiligen GA-Bandes
5. Fügt Bildverweise am Ende der MD-Dateien ein
"""

import os
import shutil
from pathlib import Path
from PIL import Image

# Basispfad zum Steiner_GA Ordner
BASE_PATH = Path(__file__).parent.parent / "Steiner_GA"

# Quellordner für die Wandtafelzeichnungen
SOURCE_PATH = BASE_PATH / "GA K 58_1 - Wandtafelzeichnungen zum Vortragswerk 1 (U1-U4) (1)" / "assets"

# Zuordnungstabelle: (img-nummer, GA-Band, Datum-Pattern für Dateisuche, Tafelnummer)
MAPPINGS = [
    # GA 73A - 27. März 1920
    ("img-1", "GA073a", "27. März 1920", 1),
    ("img-2", "GA073a", "27. März 1920", 2),
    
    # GA 74 - 22.-24. Mai 1920
    ("img-3", "GA074", "22. Mai 1920", 1),
    ("img-4", "GA074", "23. Mai 1920", 2),
    ("img-5", "GA074", "23. Mai 1920", 3),
    ("img-6", "GA074", "24. Mai 1920", 4),
    ("img-7", "GA074", "24. Mai 1920", 5),
    
    # GA 76 - 5.-7. April 1921
    ("img-8", "GA076", "5. April 1921", 1),
    ("img-9", "GA076", "6. April 1921", 2),
    ("img-10", "GA076", "7. April 1921", 3),
    
    # GA 84 - 14.-22. April 1923
    ("img-11", "GA084", "14. April 1923", 1),
    ("img-12", "GA084", "14. April 1923", 2),
    ("img-13", "GA084", "15. April 1923", 3),
    ("img-14", "GA084", "15. April 1923", 4),
    ("img-15", "GA084", "20. April 1923", 5),
    ("img-16", "GA084", "20. April 1923", 6),
    ("img-17", "GA084", "21. April 1923", 7),
    ("img-18", "GA084", "21. April 1923", 8),
    ("img-19", "GA084", "22. April 1923", 9),
]

# GA-Ordnernamen (für die Suche nach dem richtigen Ordner)
GA_FOLDERS = {
    "GA073a": "GA073a-Fachwissenschaften und Anthroposophie",
    "GA074": "GA074-Die Philosophie des Thomas von Aquino",
    "GA076": "GA076-Die befruchtende Wirkung der Anthroposophie auf die Fachwissenschaften",
    "GA084": "GA084-Was wollte das Goetheanum und was soll die Anthroposophie",
}


def find_md_file(ga_folder_path: Path, date_pattern: str) -> Path | None:
    """Findet die MD-Datei, die das angegebene Datum im Namen enthält."""
    for md_file in ga_folder_path.glob("*.md"):
        if date_pattern in md_file.name and md_file.name.startswith(ga_folder_path.name.split("-")[0]):
            # Überspringe die Übersichtsdatei (die mit dem Bandtitel)
            if not md_file.name.endswith(").md"):
                return md_file
    return None


def process_image(source_file: Path, target_file: Path) -> bool:
    """
    Verarbeitet ein Bild: Dreht es 90° nach links und speichert als WebP.
    Returns True bei Erfolg, False bei Fehler.
    """
    try:
        with Image.open(source_file) as img:
            # 90° nach links drehen (counterclockwise)
            rotated = img.rotate(90, expand=True)
            # Als WebP speichern mit guter Qualität
            rotated.save(target_file, 'WEBP', quality=90)
            print(f"  [OK] Bild konvertiert: {target_file.name}")
            return True
    except Exception as e:
        print(f"  [FEHLER] bei {source_file.name}: {e}")
        return False


def add_image_to_md(md_file: Path, image_filename: str, tafel_nummer: int, is_first: bool) -> bool:
    """
    Fügt einen Bildverweis am Ende der MD-Datei ein.
    Bei der ersten Tafel wird auch die Überschrift hinzugefügt.
    """
    try:
        content = md_file.read_text(encoding='utf-8')
        
        # Prüfen ob bereits Wandtafelzeichnungen-Abschnitt existiert
        if "## Wandtafelzeichnungen" in content:
            # Nur das Bild hinzufügen
            new_content = content.rstrip() + f"\n\n![Tafel {tafel_nummer}](assets/{image_filename})"
        elif is_first:
            # Ersten Abschnitt mit Überschrift hinzufügen
            new_content = content.rstrip() + f"\n\n---\n\n## Wandtafelzeichnungen\n\n![Tafel {tafel_nummer}](assets/{image_filename})"
        else:
            # Sollte nicht vorkommen, aber falls doch
            new_content = content.rstrip() + f"\n\n![Tafel {tafel_nummer}](assets/{image_filename})"
        
        md_file.write_text(new_content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"  [FEHLER] beim Aktualisieren von {md_file.name}: {e}")
        return False


def main():
    print("=" * 60)
    print("Wandtafelzeichnungen Integration")
    print("=" * 60)
    
    # Prüfen ob Quellordner existiert
    if not SOURCE_PATH.exists():
        print(f"FEHLER: Quellordner nicht gefunden: {SOURCE_PATH}")
        return
    
    # Statistik
    images_processed = 0
    md_files_updated = set()
    errors = []
    
    # Gruppiere nach MD-Datei für korrekte "is_first" Logik
    md_first_image = {}  # Track welche MD-Datei schon ein Bild bekommen hat
    
    for img_name, ga_band, date_pattern, tafel_nr in MAPPINGS:
        print(f"\nVerarbeite: {img_name} -> {ga_band} Tafel {tafel_nr}")
        
        # Quellbild finden
        source_file = SOURCE_PATH / f"GA K 58_1 - Wandtafelzeichnungen zum Vortragswerk 1 (U1-U4) (1)_{img_name}.jpeg"
        if not source_file.exists():
            errors.append(f"Quellbild nicht gefunden: {source_file.name}")
            print(f"  [FEHLER] Quellbild nicht gefunden: {source_file.name}")
            continue
        
        # GA-Ordner finden
        ga_folder_name = GA_FOLDERS.get(ga_band)
        if not ga_folder_name:
            errors.append(f"GA-Ordner nicht konfiguriert: {ga_band}")
            continue
        
        ga_folder = BASE_PATH / ga_folder_name
        if not ga_folder.exists():
            errors.append(f"GA-Ordner nicht gefunden: {ga_folder}")
            continue
        
        # MD-Datei finden
        md_file = find_md_file(ga_folder, date_pattern)
        if not md_file:
            errors.append(f"MD-Datei nicht gefunden für {ga_band}, {date_pattern}")
            print(f"  [FEHLER] MD-Datei nicht gefunden fuer Datum: {date_pattern}")
            continue
        
        print(f"  -> MD-Datei: {md_file.name}")
        
        # Assets-Ordner erstellen falls nötig
        assets_folder = ga_folder / "assets"
        assets_folder.mkdir(exist_ok=True)
        
        # Zieldateiname
        target_filename = f"{ga_band}-T{tafel_nr:02d}.webp"
        target_file = assets_folder / target_filename
        
        # Bild verarbeiten
        if process_image(source_file, target_file):
            images_processed += 1
            
            # MD-Datei aktualisieren
            md_key = str(md_file)
            is_first = md_key not in md_first_image
            md_first_image[md_key] = True
            
            if add_image_to_md(md_file, target_filename, tafel_nr, is_first):
                md_files_updated.add(md_file.name)
                print(f"  [OK] MD-Datei aktualisiert")
    
    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"Bilder verarbeitet: {images_processed}/{len(MAPPINGS)}")
    print(f"MD-Dateien aktualisiert: {len(md_files_updated)}")
    
    if md_files_updated:
        print("\nAktualisierte MD-Dateien:")
        for name in sorted(md_files_updated):
            print(f"  - {name}")
    
    if errors:
        print(f"\nFehler ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    
    print("\nFertig!")


if __name__ == "__main__":
    main()


