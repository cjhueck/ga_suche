#!/usr/bin/env python3
"""
Erhöht Seitenmarker |XX| in einem Bereich um 1.

Verwendung:
    python renumber_page_markers.py <datei.md> <start> [ende]
    z.B. python renumber_page_markers.py ga71a.md 188         (ab 188 bis Ende)
    z.B. python renumber_page_markers.py ga71a.md 30 187    (von 30 bis 187 inkl.)

Alle |N| mit start <= N <= ende (oder N >= start wenn ende fehlt) werden zu |N+1|.
Verarbeitung von hoch nach niedrig, damit keine doppelte Ersetzung entsteht.
"""

import re
import sys
from pathlib import Path


def renumber_markers(text: str, from_num: int, to_num: int | None = None) -> str:
    """
    Erhöht alle |N| mit from_num <= N <= to_num (bzw. N >= from_num wenn to_num=None) um 1.
    """
    numbers = set(map(int, re.findall(r'\|(\d+)\|', text)))
    if to_num is not None:
        to_rename = sorted([n for n in numbers if from_num <= n <= to_num], reverse=True)
    else:
        to_rename = sorted([n for n in numbers if n >= from_num], reverse=True)

    for n in to_rename:
        text = text.replace(f"|{n}|", f"|{n + 1}|")

    return text


def main():
    if len(sys.argv) < 3:
        print("Verwendung: python renumber_page_markers.py <datei.md> <start> [ende]")
        print("Beispiel: python renumber_page_markers.py ga71a.md 30 187")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    try:
        from_num = int(sys.argv[2])
        to_num = int(sys.argv[3]) if len(sys.argv) > 3 else None
    except ValueError:
        print("Start- und Endnummer müssen ganze Zahlen sein.")
        sys.exit(1)

    if not file_path.exists():
        print(f"Datei nicht gefunden: {file_path}")
        sys.exit(1)

    content = file_path.read_text(encoding='utf-8')
    result = renumber_markers(content, from_num, to_num)

    if result != content:
        file_path.write_text(result, encoding='utf-8')
        range_str = f"|{from_num}| bis |{to_num}|" if to_num else f"ab |{from_num}|"
        print(f"Neunummerierung {range_str} abgeschlossen: {file_path}")
    else:
        print("Keine Marker zur Änderung gefunden.")


if __name__ == "__main__":
    main()
