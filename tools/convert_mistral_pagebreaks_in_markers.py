#!/usr/bin/env python3
"""
Konvertiert Mistral-Seitentrennungen (RUDOLF STEINER / VERLAG / Seite XX) in Markdown-Seitenmarker |XX|.

Verarbeitung:
1. Ersetzt Seitentrennungsblöcke durch |XX| (Seitennummer - 2)
2. Worttrennungen: Marker innerhalb des Wortes ohne Abstände (Silbe|XX|ben)
3. Absatzumbrüche: Behält \n\n nur wenn Satz mit . ! ? : endet
4. Überschriften: Marker nie vor # Text, sondern vor dem nächsten Absatz

Verwendung:
    python convert_mistral_pagebreaks_in_markers.py <datei.md>
"""

import re
import sys
from pathlib import Path


def _is_heading(line: str) -> bool:
    """Prüft ob eine Zeile eine Markdown-Überschrift ist."""
    stripped = line.strip()
    return stripped.startswith('#') and len(stripped) > 1


def convert_page_breaks(text: str) -> str:
    """
    Konvertiert RUDOLF STEINER/VERLAG/Seite XX-Blöcke in |XX| Marker.
    Reduziert Seitennummer um 2.
    """
    pattern = re.compile(
        r'(.*?)([^\n]+)(?:\s*\n)+\s*RUDOLF\s+STEINER\s*\n\s*VERLAG(?:\s*\n)+\s*Seite\s+(\d+)\s*\n\s*---+\s*\n(?:\s*\n)*\s*([^\n]*)',
        re.MULTILINE | re.DOTALL
    )

    def replacer(match):
        prefix = match.group(1)
        before = match.group(2)
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
        if before_stripped and before_stripped[-1] in '.!?:':
            return f"{prefix}\n\n{marker} {after_stripped}"
        return f"{prefix}{before_stripped} {marker} {after_stripped}"

    return pattern.sub(replacer, text)


def fix_paragraph_breaks(text: str) -> str:
    """
    Entfernt falsche Absatzumbrüche vor |XX| wenn der Satz nicht mit . ! ? : endet.
    """
    pattern = re.compile(
        r'([^\n]+)\n\n(\|\d+\|)\s+([^\n]*)',
        re.MULTILINE
    )

    def replacer(match):
        before = match.group(1)
        marker = match.group(2)
        after = match.group(3)
        before_stripped = before.rstrip()
        if before_stripped and before_stripped[-1] in '.!?:':
            return f"{before}\n\n{marker} {after}"
        return f"{before_stripped} {marker} {after}"

    return pattern.sub(replacer, text)


def fix_markers_before_headings(text: str) -> str:
    """
    Verschiebt Marker von vor # Überschriften an den Anfang des nächsten Absatzes.
    """
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        # Marker am Anfang einer Zeile, gefolgt von # Überschrift
        match = re.match(r'^(\s*)(\|(\d+)\|)\s*(#+\s+.*)$', line)
        if match:
            indent = match.group(1)
            marker = match.group(2)
            heading = match.group(4)
            lines[i] = indent + heading
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if next_line.strip() and not _is_heading(next_line):
                    lines[j] = marker + ' ' + next_line.lstrip()
                    break
                j += 1
        i += 1
    return '\n'.join(lines)


def process(text: str) -> str:
    """Vollständige Verarbeitung: Konvertierung + Korrekturen."""
    result = convert_page_breaks(text)
    result = fix_paragraph_breaks(result)
    result = fix_markers_before_headings(result)
    return result


def main():
    if len(sys.argv) < 2:
        print("Verwendung: python convert_mistral_pagebreaks_in_markers.py <datei.md>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Datei nicht gefunden: {file_path}")
        sys.exit(1)

    content = file_path.read_text(encoding='utf-8')
    result = process(content)

    if result != content:
        file_path.write_text(result, encoding='utf-8')
        print(f"Konvertierung abgeschlossen: {file_path}")
    else:
        print("Keine Änderungen vorgenommen (keine Mistral-Seitentrennungen gefunden).")


if __name__ == "__main__":
    main()
