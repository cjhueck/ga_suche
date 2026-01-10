#!/usr/bin/env python3
"""
Konvertiert Mistral OCR Seitenmarker in das Standard-Format |X|

Mistral OCR Format:
    ...Text...
    RUDOLF STEINER
    VERLAG
    Seite X
    ---
    ...nächster Text...

Standard Format:
    ...Text...|X|...nächster Text...

Verwendung:
    python tools/convert_mistral_pagemarks.py <input.md> [output.md]
"""

import re
import sys
from pathlib import Path

def convert_mistral_to_standard(content: str) -> str:
    """Konvertiert Mistral 'Seite X' Marker in |X| Format."""
    
    # Pattern für Mistral-Seitenmarker
    # Matches: RUDOLF STEINER\nVERLAG\nSeite X\n---
    # oder: RUDOLF STEINER\nVERLAG\n\nSeite X\n---
    pattern = r'\n*RUDOLF STEINER\s*\n\s*VERLAG\s*\n+Seite\s+(\d+)\s*\n+---\n*'
    
    def replace_marker(match):
        page_num = match.group(1)
        return f'|{page_num}|'
    
    # Ersetze alle Marker
    result = re.sub(pattern, replace_marker, content, flags=re.IGNORECASE)
    
    # Entferne auch alleinstehende "Seite X" am Zeilenanfang (falls vorhanden)
    result = re.sub(r'\nSeite\s+\d+\s*\n', '\n', result)
    
    # Entferne doppelte Leerzeilen
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result


def main():
    if len(sys.argv) < 2:
        print("Verwendung: python convert_mistral_pagemarks.py <input.md> [output.md]")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        # Standard: gleiches Verzeichnis, mit "_converted" Suffix
        output_path = input_path.parent / f"{input_path.stem}_converted{input_path.suffix}"
    
    print(f"Lese: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Zähle originale Marker
    original_count = len(re.findall(r'Seite\s+\d+', content, re.IGNORECASE))
    print(f"Gefundene 'Seite X' Marker: {original_count}")
    
    # Konvertiere
    converted = convert_mistral_to_standard(content)
    
    # Zähle neue Marker
    new_count = len(re.findall(r'\|\d+\|', converted))
    print(f"Konvertierte |X| Marker: {new_count}")
    
    # Speichere
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(converted)
    
    print(f"Gespeichert: {output_path}")
    
    # Zeige Beispiel
    print("\nBeispiel der ersten Marker:")
    matches = re.finditer(r'.{50}\|(\d+)\|.{50}', converted, re.DOTALL)
    for i, m in enumerate(matches):
        if i >= 3:
            break
        snippet = m.group(0).replace('\n', '\\n')
        print(f"  ...{snippet}...")


if __name__ == '__main__':
    main()

