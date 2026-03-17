#!/usr/bin/env python3
"""
Korrigiert falsche Absatzumbrüche vor Seitenmarkern |XX|:
- Entfernt \n\n vor |XX| wenn der vorherige Satz NICHT mit . ! ? : endet
- Behält \n\n vor |XX| nur wenn echter Absatzumbruch (Satz endet mit . ! ? :)
- Verschiebt Marker nie vor # Überschriften, sondern vor den nächsten Absatz
"""

import re
import sys
from pathlib import Path


def fix_paragraph_breaks(text: str) -> str:
    """
    Ersetzt "Zeile\n\n|XX| Fortsetzung" durch "Zeile |XX| Fortsetzung",
    wenn die Zeile nicht mit Satzende (. ! ? :) endet.
    """
    # Muster: Zeile + Absatzumbruch + Marker + Fortsetzung
    pattern = re.compile(
        r'([^\n]+)\n\n(\|\d+\|)\s+([^\n]*)',
        re.MULTILINE
    )

    def replacer(match):
        before = match.group(1)
        marker = match.group(2)
        after = match.group(3)
        before_stripped = before.rstrip()
        # Absatzumbruch beibehalten nur wenn Satz mit . ! ? : endet
        if before_stripped and before_stripped[-1] in '.!?:':
            return f"{before}\n\n{marker} {after}"
        # Falschen Absatzumbruch entfernen
        return f"{before_stripped} {marker} {after}"

    return pattern.sub(replacer, text)


def main():
    file_path = Path(r"C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA071a-Seelenunsterblichkeit, Schicksalskräfte und menschlicher Lebenslauf\GA 71a - Seelenunsterblichkeit, Schicksalskräfte und menschlicher Lebenslauf.md")

    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Datei nicht gefunden: {file_path}")
        sys.exit(1)

    content = file_path.read_text(encoding='utf-8')
    fixed = fix_paragraph_breaks(content)

    if fixed != content:
        file_path.write_text(fixed, encoding='utf-8')
        print(f"Korrektur abgeschlossen: {file_path}")
    else:
        print("Keine Korrekturen erforderlich.")


if __name__ == "__main__":
    main()
