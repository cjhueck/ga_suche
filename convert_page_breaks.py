#!/usr/bin/env python3
"""
Konvertiert Seitentrennungen in GA 71a Markdown-Dateien:
- Ersetzt den Trennungsblock durch |XX|
- Reduziert Seitennummer um 2
- Behandelt Worttrennungen (marker ohne Abstände im Wort)
- Behält Absatzumbrüche bei
"""

import re
import sys
from pathlib import Path


def convert_page_breaks(text: str) -> str:
    """
    Konvertiert Seitentrennungen gemäß den Regeln:
    1. Ersetzt Trennungsblock durch |XX| (XX = Seitennummer - 2)
    2. Bei Worttrennung: Marker innerhalb des Wortes ohne Abstände
    3. Bei Absatzumbruch: Umbruch behalten, Marker am Beginn des neuen Absatzes
    """
    # Erfasst die letzte nicht-leere Zeile vor dem Block (nicht die oft leere Zeile direkt davor)
    pattern = re.compile(
        r'(.*?)([^\n]+)(?:\s*\n)+\s*RUDOLF\s+STEINER\s*\n\s*VERLAG(?:\s*\n)+\s*Seite\s+(\d+)\s*\n\s*---+\s*\n(?:\s*\n)*\s*([^\n]*)',
        re.MULTILINE | re.DOTALL
    )

    def replacer(match):
        prefix = match.group(1)
        before = match.group(2)  # letzte nicht-leere Zeile
        page_num = int(match.group(3))
        after = match.group(4)
        new_page = page_num - 2
        marker = f"|{new_page}|"
        before_stripped = before.rstrip()
        after_stripped = after.lstrip()
        is_hyphenation = (
            before_stripped.endswith('-') and
            after_stripped and
            after_stripped[0].islower()
        )
        if is_hyphenation:
            return f"{prefix}{before_stripped[:-1]}{marker}{after_stripped}"
        # Absatzumbruch nur wenn die letzte Zeile mit Satzende endet (. ! ? :)
        if before_stripped and before_stripped[-1] in '.!?:':
            return f"{prefix}\n\n{marker} {after_stripped}"
        # Innerhalb des Satzes
        return f"{prefix}{before_stripped} {marker} {after_stripped}"

    return pattern.sub(replacer, text)


def main():
    file_path = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA071a-Seelenunsterblichkeit, Schicksalskräfte und menschlicher Lebenslauf\GA 71a - Seelenunsterblichkeit, Schicksalskräfte und menschlicher Lebenslauf.md")
    
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"Datei nicht gefunden: {file_path}")
        sys.exit(1)
    
    content = file_path.read_text(encoding='utf-8')
    converted = convert_page_breaks(content)
    
    if converted != content:
        file_path.write_text(converted, encoding='utf-8')
        print(f"Konvertierung abgeschlossen: {file_path}")
    else:
        print("Keine Seitentrennungen zum Konvertieren gefunden.")


if __name__ == "__main__":
    main()
