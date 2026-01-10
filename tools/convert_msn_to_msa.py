#!/usr/bin/env python3
"""
Konvertiert MsN (Mistral Neu) direkt zu MsA-Format mit Seitenmarkern.

MsN Format:
    ...Text...
    100
    RUDOLF STEINER
    VERLAG
    Seite 100
    ---
    ...nächster Text (Seite 101)...

Wird zu:
    ...Text...|101|...nächster Text...

Verwendung:
    python tools/convert_msn_to_msa.py GA019
"""

import re
import sys
from pathlib import Path


def convert_msn_pagebreaks(content: str) -> str:
    """
    Konvertiere MsN Seitenmarker zu |X| Format.
    
    "Seite X" steht am ENDE von Seite X, also ist der Text danach Seite X+1.
    """
    
    # Entferne die Seitenzahl-Zeile vor dem RUDOLF STEINER Header
    # Pattern: Zahl allein auf einer Zeile, gefolgt von RUDOLF STEINER VERLAG
    content = re.sub(
        r'\n(\d{1,3})\s*\n+RUDOLF STEINER\s*\n\s*VERLAG',
        r'\nRUDOLF STEINER\nVERLAG',
        content,
        flags=re.IGNORECASE
    )
    
    # Hauptkonvertierung: RUDOLF STEINER VERLAG Seite X --- → |X+1|
    def replace_pagebreak(match):
        page_num = int(match.group(1))
        next_page = page_num + 1
        return f'|{next_page}|'
    
    content = re.sub(
        r'\s*RUDOLF STEINER\s*\n\s*VERLAG\s*\n+Seite\s+(\d+)\s*\n+---\s*',
        replace_pagebreak,
        content,
        flags=re.IGNORECASE
    )
    
    # Entferne übrige "Seite X" Zeilen (die manchmal doppelt vorkommen)
    content = re.sub(r'\nSeite\s+\d+\s*\n', '\n', content, flags=re.IGNORECASE)
    
    # Konvertiere nackte Seitenzahlen mit --- (alternatives Format)
    # Pattern: \n\nXX\n\n---\n\n → |XX+1|
    def replace_naked_pagebreak(match):
        page_num = int(match.group(1))
        next_page = page_num + 1
        return f'|{next_page}|'
    
    content = re.sub(r'\n\n(\d{1,3})\n\n---\n+', replace_naked_pagebreak, content)
    
    # Entferne ALLE verbleibenden "RUDOLF STEINER\nVERLAG" Blöcke
    content = re.sub(r'\n*RUDOLF STEINER\s*\n\s*VERLAG\s*\n*', '\n', content, flags=re.IGNORECASE)
    
    # Entferne Überschriften (# ...) - diese kommen aus MsA, nicht aus MsN
    content = re.sub(r'^#+\s+.*$', '', content, flags=re.MULTILINE)
    
    # Füge Worttrennungen zusammen (Trennstrich am Zeilenende)
    # Pattern: Wort-\nrest → Wortrest
    content = re.sub(r'(\w)-\n(\w)', r'\1\2', content)
    
    # Bereinige mehrfache Leerzeilen
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Formatiere Marker nach den Regeln
    content = format_pagebreak_markers(content)
    
    return content


def format_pagebreak_markers(content: str) -> str:
    """
    Formatiere Pagebreak-Marker nach den Regeln:
    1. Leerzeichen vor und nach Marker (Standard)
    2. Bei Worttrennungen: Trennstrich entfernen, kein Leerzeichen (Wort-|XX|rest → Wort|XX|rest)
    3. Satzzeichen vor dem Marker (nicht danach)
    """
    
    # Regel 2: Worttrennung - Trennstrich VOR Marker entfernen
    # Pattern 1: Wort-\n|XX|\nrest → Wort|XX|rest (mit Zeilenumbrüchen)
    content = re.sub(r'(\w)-\s*\n?\s*\|(\d+)\|\s*\n?\s*(\w)', r'\1§§|\2|§§\3', content)
    
    # Pattern 2: Wort- |XX| rest → Wort|XX|rest (mit Leerzeichen)
    content = re.sub(r'(\w)-\s+\|(\d+)\|\s+(\w)', r'\1§§|\2|§§\3', content)
    
    # Pattern 3: Wort-|XX|rest → Wort|XX|rest (direkt)
    content = re.sub(r'(\w)-\|(\d+)\|(\w)', r'\1§§|\2|§§\3', content)
    
    # Regel 3: Satzzeichen nach Marker vor den Marker verschieben
    # Pattern: |XX|? → ? |XX| (für ?, !, ., ,, ;, :, », «, ")
    content = re.sub(r'\|(\d+)\|\s*([?!.,;:»«"])', r'\2 |\1|', content)
    
    # Regel 1: Füge Leerzeichen vor und nach Marker hinzu
    # ABER nicht wenn §§ Markierung vorhanden (Worttrennung)
    
    # Leerzeichen nach Marker (wenn kein §§ folgt und kein Whitespace)
    content = re.sub(r'\|(\d+)\|([^§\s|])', r'|\1| \2', content)
    
    # Leerzeichen vor Marker (wenn kein §§ davor und kein Whitespace)
    content = re.sub(r'([^§\s|])\|(\d+)\|', r'\1 |\2|', content)
    
    # Entferne die §§ Markierungen
    content = content.replace('§§', '')
    
    # Bereinige doppelte Leerzeichen
    content = re.sub(r'  +', ' ', content)
    
    # Bereinige Leerzeichen am Zeilenende
    content = re.sub(r' +\n', '\n', content)
    
    # Bereinige Leerzeichen am Zeilenanfang
    content = re.sub(r'\n +', '\n', content)
    
    # Bereinige Marker am Zeilenanfang mit Leerzeichen danach
    content = re.sub(r'^\|(\d+)\|\s+', r'|\1| ', content, flags=re.MULTILINE)
    
    return content


def extract_absatz_ids(msa_content: str) -> list:
    """Extrahiere Absatz-IDs (^xxxxx) aus MsA."""
    return re.findall(r'\^[a-z0-9]{5,6}', msa_content)


def add_absatz_ids(content: str, ids: list) -> str:
    """Füge Absatz-IDs am Ende jedes Absatzes hinzu."""
    # Teile in Absätze (doppelte Newlines)
    paragraphs = re.split(r'\n\n+', content)
    
    result = []
    id_index = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Prüfe ob Absatz bereits eine ID hat
        if re.search(r'\^[a-z0-9]{5,6}$', para):
            result.append(para)
        else:
            # Füge ID hinzu wenn verfügbar
            if id_index < len(ids):
                para = f"{para} {ids[id_index]}"
                id_index += 1
            result.append(para)
    
    return '\n\n'.join(result)


def main():
    if len(sys.argv) < 2:
        print("Verwendung: python convert_msn_to_msa.py GA019")
        sys.exit(1)
    
    ga_num = sys.argv[1].upper()
    if not ga_num.startswith('GA'):
        ga_num = f'GA{ga_num}'
    
    # Finde GA-Ordner
    base = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA')
    ga_folder = None
    
    for d in base.iterdir():
        if d.is_dir() and ga_num in d.name:
            ga_folder = d
            break
    
    if not ga_folder:
        print(f"GA-Ordner nicht gefunden: {ga_num}")
        sys.exit(1)
    
    print(f"GA-Ordner: {ga_folder.name}")
    
    # Finde MsN Datei
    msn_path = None
    for f in ga_folder.iterdir():
        if f.suffix == '.md' and 'Steiner, Rudolf' in f.name and '_converted' not in f.name:
            msn_path = f
            break
    
    if not msn_path:
        print("MsN-Datei nicht gefunden!")
        sys.exit(1)
    
    print(f"MsN: {msn_path.name}")
    
    # Lade und konvertiere MsN
    msn_content = msn_path.read_text(encoding='utf-8')
    converted = convert_msn_pagebreaks(msn_content)
    
    # Zähle Marker
    markers = re.findall(r'\|(\d+)\|', converted)
    print(f"Marker erstellt: {len(markers)}")
    if markers:
        pages = [int(m) for m in markers]
        print(f"  Seiten: {min(pages)} - {max(pages)}")
    
    # Speichere konvertierte Version
    output_path = msn_path.parent / f"{msn_path.stem}_converted.md"
    output_path.write_text(converted, encoding='utf-8')
    print(f"\nKonvertiert gespeichert: {output_path.name}")
    
    # Zeige Beispiel
    print("\nBeispiel (erste 3 Marker):")
    for m in re.finditer(r'.{40}\|(\d+)\|.{40}', converted):
        page = m.group(1)
        snippet = m.group(0).replace('\n', '\\n')[:90]
        print(f"  |{page}|: ...{snippet}...")
        if int(page) > 12:
            break


if __name__ == '__main__':
    main()

