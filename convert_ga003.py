#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konvertiert GA003.pdf zu Markdown:
1. Liest PDF mit PyMuPDF
2. Löscht Seitenumbrüche
3. Fügt an Seitenumbrüchen getrennte Wörter zusammen
4. Löscht Seitenzahlen
5. Löscht Seiten-Headers (über Linien)
6. Konvertiert Fußnoten zu klickbaren Markdown-Links
"""

import re
import fitz  # PyMuPDF
from pathlib import Path


def extrahiere_text_aus_pdf(pdf_path):
    """Extrahiert Text aus PDF"""
    doc = fitz.open(pdf_path)
    text_pages = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        text_pages.append(text)
    
    doc.close()
    return text_pages


def loesche_seitenzahlen(text):
    """Löscht Seitenzahlen (z.B. "Seite 1", "1", römische Zahlen, etc.)"""
    lines = text.split('\n')
    result = []
    
    for line in lines:
        line_stripped = line.strip()
        # Überspringe Zeilen die nur Zahlen sind (wahrscheinlich Seitenzahlen)
        if line_stripped.isdigit() and len(line_stripped) <= 3:
            continue
        # Überspringe "Seite X" Zeilen
        if re.match(r'^Seite\s+\d+$', line_stripped, re.IGNORECASE):
            continue
        # Überspringe römische Zahlen (I, II, III, IV, V, VI, VII, VIII, IX, X, etc.)
        # Prüfe ob die Zeile nur aus römischen Zahlen besteht
        if re.match(r'^[IVXLCDM]+$', line_stripped) and len(line_stripped) <= 10:
            # Überspringe nur wenn es alleinstehend ist (nicht Teil eines Textes)
            continue
        result.append(line)
    
    return '\n'.join(result)


def loesche_seiten_headers(text):
    """Löscht Seiten-Headers die über Linien stehen"""
    lines = text.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        line_stripped = line.strip()
        
        # Prüfe ob dies ein Header sein könnte (z.B. "WAHRHEIT UND WISSENSCHAFT")
        # Headers sind typischerweise:
        # 1. Eine Zeile mit Text (z.B. "WAHRHEIT UND WISSENSCHAFT")
        # 2. Eine weitere Zeile mit Text (z.B. "Vorrede")
        # 3. Eine Zeile mit vielen Unterstrichen oder Bindestrichen
        
        if i + 2 < len(lines):
            line1 = line_stripped
            line2 = lines[i+1].strip()
            line3 = lines[i+2].strip()
            
            # Prüfe ob line3 eine Linie ist (viele Unterstriche/Bindestriche)
            if re.match(r'^[-_]{10,}$', line3):
                # Prüfe ob line1 und line2 Text sind (nicht leer, nicht nur Zahlen)
                if line1 and not line1.isdigit() and line2 and not line2.isdigit():
                    # Überspringe diese drei Zeilen
                    i += 3
                    continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)


def entferne_seitenumbrueche_und_fuege_woerter_zusammen(text):
    """Entfernt Seitenumbrüche und fügt getrennte Wörter zusammen"""
    lines = text.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        line_stripped = line.strip()
        
        # Überspringe leere Zeilen die Seitenumbrüche markieren könnten
        if not line_stripped:
            # Prüfe ob die nächste Zeile mit Kleinbuchstaben beginnt (Fortsetzung eines Wortes)
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line and next_line[0].islower():
                    # Prüfe ob die vorherige Zeile mit Bindestrich endet
                    if result and result[-1].rstrip().endswith('-') and not result[-1].rstrip().endswith('--'):
                        # Entferne Bindestrich und füge zusammen
                        last_line = result[-1].rstrip()
                        result[-1] = result[-1][:len(result[-1]) - len(last_line)] + last_line[:-1] + next_line
                        i += 2
                        continue
            
            result.append(line)
            i += 1
            continue
        
        # Prüfe ob die Zeile mit Bindestrich endet (getrenntes Wort)
        # Z.B. "Wis-" sollte mit "senschaft" zusammengefügt werden
        if line_stripped.endswith('-') and not line_stripped.endswith('--'):
            # Suche die nächste nicht-leere Zeile
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            
            if j < len(lines):
                next_line = lines[j].strip()
                # Wenn die nächste Zeile mit Kleinbuchstaben beginnt, füge sie zusammen
                if next_line and next_line[0].islower():
                    # Entferne Bindestrich und füge zusammen
                    result.append(line_stripped[:-1] + next_line)
                    i = j + 1
                    continue
                # Auch wenn die nächste Zeile mit Großbuchstaben beginnt, könnte es ein zusammengehöriges Wort sein
                # wenn die vorherige Zeile kurz ist (z.B. "Wis-" + "senschaft")
                elif next_line and len(line_stripped) < 15 and next_line[0].isupper():
                    # Prüfe ob es wirklich ein zusammengehöriges Wort ist
                    # (z.B. wenn die nächste Zeile mit demselben Buchstaben beginnt wie die vorherige endet)
                    if len(line_stripped) >= 2 and line_stripped[-2].lower() == next_line[0].lower():
                        # Füge zusammen, aber konvertiere ersten Buchstaben der nächsten Zeile zu Kleinbuchstaben
                        result.append(line_stripped[:-1] + next_line[0].lower() + next_line[1:])
                        i = j + 1
                        continue
                # Wenn die nächste Zeile mit Großbuchstaben beginnt und die vorherige Zeile sehr kurz ist
                # könnte es auch ein zusammengehöriges Wort sein (z.B. "Wis-" + "senschaft")
                elif next_line and len(line_stripped) <= 5 and next_line[0].isupper():
                    # Füge zusammen, konvertiere ersten Buchstaben zu Kleinbuchstaben
                    result.append(line_stripped[:-1] + next_line[0].lower() + next_line[1:])
                    i = j + 1
                    continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)


def konvertiere_fussnoten(text):
    """Konvertiert Fußnoten zu klickbaren Markdown-Links"""
    lines = text.split('\n')
    result = []
    fussnoten_defs = {}  # Mapping von Nummer zu Text
    
    # Erste Durchlauf: Sammle alle Fußnoten-Definitionen
    i = 0
    while i < len(lines):
        line = lines[i]
        line_stripped = line.strip()
        
        # Erkenne Fußnoten-Definitionen: [^0]: ${ }^{n}$ ... oder ähnliche Formate
        if line_stripped.startswith('[^0]:'):
            rest_match = re.search(r'\[\^0\]:\s+(.+)$', line_stripped)
            if rest_match:
                rest = rest_match.group(1)
                # Prüfe ob Rest mit ${ }^{ beginnt
                if rest.startswith('${ }^{'):
                    num_match = re.search(r'\d+', rest)
                    if num_match:
                        after_num = rest[num_match.end():]
                        if after_num.startswith('}$'):
                            fn_num = num_match.group(0)
                            fn_text = after_num[2:].strip()
                            fussnoten_defs[fn_num] = fn_text
                            # Überspringe diese Zeile
                            i += 1
                            continue
        
        result.append(line)
        i += 1
    
    # Zweiter Durchlauf: Ersetze Fußnoten-Referenzen im Text
    text_result = '\n'.join(result)
    
    # Ersetze ${ }^{n}$ → [^n]
    def replace_fussnote_in_text(text):
        result_chars = []
        i = 0
        while i < len(text):
            if i < len(text) - 6 and text[i:i+6] == '${ }^{':
                j = i + 6
                num_start = j
                while j < len(text) and text[j].isdigit():
                    j += 1
                if j < len(text) - 2 and text[j:j+2] == '}$':
                    fn_num = text[num_start:j]
                    result_chars.append(f' [^{fn_num}]')
                    i = j + 2
                    continue
            result_chars.append(text[i])
            i += 1
        return ''.join(result_chars)
    
    text_result = replace_fussnote_in_text(text_result)
    
    # Ersetze Unicode-Fußnoten-Zeichen (¹, ², ³, etc.)
    unicode_to_num = {
        '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5',
        '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁰': '0'
    }
    for unicode_char, num in unicode_to_num.items():
        # Ersetze Unicode-Zeichen direkt im Text
        text_result = text_result.replace(unicode_char, f' [^{num}]')
    
    # Füge Fußnoten-Definitionen am Ende hinzu
    if fussnoten_defs:
        text_result += '\n\n---\n\n## Fußnoten\n\n'
        # Sortiere nach Nummer
        sorted_fns = sorted(fussnoten_defs.items(), key=lambda x: int(x[0]) if x[0].isdigit() else float('inf'))
        for fn_num, fn_text in sorted_fns:
            text_result += f'[^{fn_num}]: {fn_text}\n'
    
    return text_result


def konvertiere_pdf_zu_md(pdf_path, output_path):
    """Hauptfunktion: Konvertiert PDF zu Markdown"""
    print(f'Lese PDF: {pdf_path}')
    
    # Extrahiere Text aus PDF
    text_pages = extrahiere_text_aus_pdf(pdf_path)
    text = '\n'.join(text_pages)
    
    print('Bereinige Text...')
    
    # 1. Lösche Seitenzahlen
    text = loesche_seitenzahlen(text)
    
    # 2. Lösche Seiten-Headers
    text = loesche_seiten_headers(text)
    
    # 3. Entferne Seitenumbrüche und füge Wörter zusammen
    text = entferne_seitenumbrueche_und_fuege_woerter_zusammen(text)
    
    # 4. Konvertiere Fußnoten
    text = konvertiere_fussnoten(text)
    
    # Speichere Ergebnis
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f'Gespeichert: {output_path}')


if __name__ == '__main__':
    pdf_path = Path('Steiner_GA/GA003-Wahrheit und Wissenschaft/003.pdf')
    output_path = Path('Steiner_GA/GA003-Wahrheit und Wissenschaft/003_konvertiert.md')
    
    konvertiere_pdf_zu_md(pdf_path, output_path)
    print('Fertig!')

