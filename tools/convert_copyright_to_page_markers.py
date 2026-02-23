# -*- coding: utf-8 -*-
"""
Standalone-Skript zur Umwandlung von Copyright-Zeilen in Seitenmarker.

Eingabe-Format:
    ...Text...

    Copyright Rudolf Steiner Nachlass-Verwaltung Buch: 262 Seite: 19

    ---

    Die Folge waren scharfe Entgegnungen...

Ausgabe-Format:
    ...Text...

    |19| Die Folge waren scharfe Entgegnungen...

Verwendung:
    python convert_copyright_to_page_markers.py < eingabe.md
    python convert_copyright_to_page_markers.py eingabe.md
    python convert_copyright_to_page_markers.py eingabe.md ausgabe.md
"""

import re
import sys
from pathlib import Path


def convert_copyright_to_page_markers(text: str) -> str:
    """
    Entfernt Copyright-Zeilen und ---, fügt |Seite| am Anfang des
    folgenden Absatzes ein.
    """
    lines = text.split('\n')
    result_lines = []
    pending_page = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # Copyright-Zeile mit Seitenzahl?
        if 'Copyright' in line and 'Steiner' in line:
            page_match = re.search(r'Seite:\s*(\d[\d\s]*\d|\d)', line)
            if page_match:
                page_num = page_match.group(1).replace(' ', '')
                pending_page = int(page_num)
            i += 1
            continue

        # Trennlinie --- entfernen
        if line.strip() == '---':
            i += 1
            continue

        # Text mit pending Seitenmarker?
        if line.strip() and 'Copyright' not in line:
            if pending_page:
                line = f'|{pending_page}| {line.strip()}'
                pending_page = None
            result_lines.append(line)
        elif not line.strip():
            result_lines.append(line)

        i += 1

    result = '\n'.join(result_lines)
    return re.sub(r'\n{3,}', '\n\n', result).strip()


def main():
    if len(sys.argv) >= 2:
        input_path = Path(sys.argv[1])
        if not input_path.exists():
            print(f'Fehler: Datei nicht gefunden: {input_path}', file=sys.stderr)
            sys.exit(1)
        content = input_path.read_text(encoding='utf-8')
        output_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else input_path
    else:
        content = sys.stdin.read()
        output_path = None

    result = convert_copyright_to_page_markers(content)

    if output_path:
        output_path.write_text(result, encoding='utf-8')
        print(f'Gespeichert: {output_path}')
    else:
        print(result)


if __name__ == '__main__':
    main()
