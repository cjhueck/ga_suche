"""
Skript zum Zusammenfügen von GA-Einzeldateien zu einer Gesamtdatei.
Dateinamen werden zu Überschriften umgewandelt.

Verwendung:
    python merge_ga.py 236
    python merge_ga.py 234
    python merge_ga.py 230
"""

import sys
import re
from pathlib import Path

def find_ga_folder(base_path: Path, ga_number: str) -> Path | None:
    """Findet den GA-Ordner anhand der Nummer."""
    # Suche nach Ordner, der mit "GA{nummer}" beginnt
    pattern = f"GA{ga_number}*"
    matches = list(base_path.glob(pattern))
    
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"Mehrere Ordner gefunden für GA{ga_number}:")
        for i, m in enumerate(matches):
            print(f"  {i+1}: {m.name}")
        choice = input("Bitte Nummer wählen: ")
        return matches[int(choice) - 1]
    else:
        return None

def merge_ga_files(ga_number: str):
    """Fügt alle Einzeldateien eines GA-Bandes zusammen."""
    
    # Basispfad
    base_path = Path(__file__).parent / "Steiner_GA"
    
    # GA-Ordner finden
    folder = find_ga_folder(base_path, ga_number)
    if not folder:
        print(f"Kein Ordner gefunden für GA{ga_number}")
        return
    
    print(f"Ordner: {folder.name}")
    
    # Alle Vortragsdateien finden (Muster: GA{nummer} (X.) ...)
    lecture_files = []
    # Pattern für Dateinamen wie "GA236 (1.) ERSTER VORTRAG..."
    # Unterstützt auch GA-Nummern mit Buchstaben wie "GA040a"
    pattern = re.compile(rf'^GA{re.escape(ga_number)}\s*\((\d+)\.\)')
    
    for file in folder.glob(f"GA{ga_number}*.md"):
        match = pattern.match(file.name)
        if match:
            num = int(match.group(1))
            lecture_files.append((num, file))
    
    if not lecture_files:
        print(f"Keine Einzeldateien gefunden mit Muster 'GA{ga_number} (X.) ...'")
        return
    
    # Nach Nummer sortieren
    lecture_files.sort(key=lambda x: x[0])
    
    print(f"Gefunden: {len(lecture_files)} Dateien")
    
    # Gesamtinhalt zusammenbauen
    merged_content = []
    
    for num, file in lecture_files:
        # Dateinamen zu Überschrift umwandeln
        # "GA236 (1.) ERSTER VORTRAG, Dornach, 6. April 1924.md" 
        # -> "# ERSTER VORTRAG, Dornach, 6. April 1924"
        title = file.stem  # Dateiname ohne .md
        # Entferne "GA{nummer} (X.) " vom Anfang
        title = re.sub(rf'^GA{re.escape(ga_number)}\s*\(\d+\.\)\s*', '', title)
        heading = f"# {title}"
        
        print(f"  {num}: {title}")
        
        # Dateiinhalt lesen
        content = file.read_text(encoding='utf-8')
        
        # Zusammenfügen
        merged_content.append(heading)
        merged_content.append("")  # Leerzeile nach Überschrift
        merged_content.append(content)
        merged_content.append("")  # Leerzeile zwischen Vorträgen
        merged_content.append("")  # Zusätzliche Leerzeile
    
    # In Ausgabedatei schreiben
    output_file = folder / f"GA{ga_number}-Gesamt.md"
    output_file.write_text('\n'.join(merged_content), encoding='utf-8')
    
    print(f"\nGesamtdatei erstellt: {output_file.name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python merge_ga.py <GA-Nummer>")
        print("Beispiel:   python merge_ga.py 236")
        sys.exit(1)
    
    ga_number = sys.argv[1]
    merge_ga_files(ga_number)
