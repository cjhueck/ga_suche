#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bereinigt GA001.md:
1. Entfernt Absatzumbrüche (---) und fügt getrennte Wörter zusammen
2. Konvertiert Fußnoten zu klickbaren Links
"""

import re
from pathlib import Path


def entferne_absatzumbrueche_und_fuege_woerter_zusammen(text):
    """Entfernt --- Zeilen und fügt getrennte Wörter zusammen"""
    lines = text.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        line_stripped = line.strip()
        
        # Überspringe --- Zeilen komplett
        if line_stripped == '---':
            # Prüfe ob das vorherige Wort mit Bindestrich endet
            if result and result[-1].rstrip().endswith('-') and not result[-1].rstrip().endswith('--'):
                # Entferne den Bindestrich vom Ende der letzten Zeile
                last_line = result[-1].rstrip()
                result[-1] = result[-1][:len(result[-1]) - len(last_line)] + last_line[:-1]
                
                # Suche die nächste nicht-leere Zeile nach ---
                j = i + 1
                while j < len(lines) and (lines[j].strip() == '' or lines[j].strip() == '---'):
                    j += 1
                
                if j < len(lines):
                    next_line = lines[j].strip()
                    # Wenn die nächste Zeile mit Kleinbuchstaben beginnt, füge sie zusammen
                    if next_line and next_line[0].islower():
                        # Füge das Wort zusammen (ohne Leerzeichen)
                        result[-1] = result[-1].rstrip() + next_line
                        i = j + 1
                        continue
            
            i += 1
            continue
        
        # Prüfe ob die Zeile mit Bindestrich endet (aber nicht mit --)
        if line_stripped.endswith('-') and not line_stripped.endswith('--'):
            # Suche die nächste nicht-leere Zeile
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            
            # Wenn die nächste Zeile --- ist, überspringe sie und suche weiter
            if j < len(lines) and lines[j].strip() == '---':
                j += 1
                while j < len(lines) and (lines[j].strip() == '' or lines[j].strip() == '---'):
                    j += 1
            
            if j < len(lines):
                next_line = lines[j].strip()
                # Wenn die nächste Zeile mit Kleinbuchstaben beginnt, füge sie zusammen
                if next_line and next_line[0].islower():
                    # Entferne Bindestrich und füge zusammen
                    line_without_hyphen = line.rstrip()[:-1]
                    result.append(line_without_hyphen + next_line)
                    i = j + 1
                    continue
        
        # Normale Zeile hinzufügen
        result.append(line)
        i += 1
    
    return '\n'.join(result)


def konvertiere_fussnoten(text):
    """Konvertiert Fußnoten zu klickbaren Markdown-Links"""
    lines = text.split('\n')
    result = []
    fussnoten_defs = {}  # Mapping von Nummer zu Text
    
    # Erste Durchlauf: Sammle alle Fußnoten-Definitionen und entferne sie
    i = 0
    while i < len(lines):
        line = lines[i]
        line_stripped = line.strip()
        
        # Erkenne Fußnoten-Definitionen: [^0]:    ${ }^{n}$ ...
        # Zwei-Schritt-Ansatz: Erst [^0]: finden, dann ${ }^{n}$ im Rest
        if line_stripped.startswith('[^0]:'):
            # Extrahiere den Rest nach [^0]:
            rest_match = re.search(r'\[\^0\]:\s+(.+)$', line_stripped)
            if rest_match:
                rest = rest_match.group(1)
                # Suche nach ${ }^{n}$ im Rest - manueller Ansatz
                # Prüfe ob Rest mit ${ }^{ beginnt
                if rest.startswith('${ }^{'):
                    # Finde die Zahl nach ^{
                    num_match = re.search(r'\d+', rest)
                    if num_match:
                        # Prüfe ob nach der Zahl }$ kommt
                        after_num = rest[num_match.end():]
                        if after_num.startswith('}$'):
                            fn_num = num_match.group(0)  # Nummer
                            fn_text = after_num[2:].strip()  # Text nach }$
                            match = True  # Flag für später
                        else:
                            match = None
                    else:
                        match = None
                else:
                    match = None
            else:
                match = None
        else:
            match = None
        
        if match:
            
            # Speichere Definition
            fussnoten_defs[fn_num] = fn_text
            
            # Überspringe die [^0] Zeile davor (falls vorhanden)
            if result and result[-1].strip() == '[^0]':
                result.pop()  # Entferne die [^0] Zeile
            
            # Überspringe diese Definition-Zeile
            i += 1
            continue
        
        # Überspringe alleinstehende [^0] Zeilen (werden später entfernt)
        if line_stripped == '[^0]':
            i += 1
            continue
        
        result.append(line)
        i += 1
    
    # Zweiter Durchlauf: Ersetze Fußnoten-Referenzen im Text
    text_result = '\n'.join(result)
    
    # Ersetze verschiedene Fußnoten-Formate:
    # 1. [WA 8, 250¹] → [WA 8, 250] [^1] (mit Unicode-Ziffern)
    unicode_to_num = {
        '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5',
        '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁰': '0'
    }
    for unicode_char, num in unicode_to_num.items():
        # Suche nach [WA ...] gefolgt von Unicode-Ziffer
        # Manueller Ansatz: Finde alle [WA ...] und prüfe ob direkt danach Unicode-Ziffer kommt
        result_chars = []
        i = 0
        while i < len(text_result):
            # Suche nach [WA
            if i < len(text_result) - 3 and text_result[i:i+3] == '[WA':
                # Finde das Ende von [WA Zahl, Zahl]
                j = i + 3
                # Überspringe Leerzeichen
                while j < len(text_result) and text_result[j].isspace():
                    j += 1
                # Finde erste Zahl
                num_start = j
                while j < len(text_result) and text_result[j].isdigit():
                    j += 1
                # Prüfe ob Komma und zweite Zahl folgen
                if j < len(text_result) and text_result[j] == ',':
                    j += 1
                    while j < len(text_result) and text_result[j].isspace():
                        j += 1
                    num2_start = j
                    while j < len(text_result) and text_result[j].isdigit():
                        j += 1
                    # Prüfe ob ] folgt
                    if j < len(text_result) and text_result[j] == ']':
                        j += 1
                        # Prüfe ob direkt danach Unicode-Ziffer kommt (mit oder ohne Leerzeichen)
                        # Überspringe Leerzeichen nach ]
                        k = j
                        while k < len(text_result) and text_result[k].isspace():
                            k += 1
                        if k < len(text_result) and text_result[k] == unicode_char:
                            # Ersetze: [WA ...] + Leerzeichen? + Unicode → [WA ...] [^n]
                            result_chars.append(text_result[i:j])
                            result_chars.append(f' [^{num}]')
                            i = k + 1
                            continue
                        elif j < len(text_result) and text_result[j] == unicode_char:
                            # Unicode direkt nach ]
                            result_chars.append(text_result[i:j])
                            result_chars.append(f' [^{num}]')
                            i = j + 1
                            continue
            
            result_chars.append(text_result[i])
            i += 1
        
        text_result = ''.join(result_chars)
    
    # 2. ${ }^{n}$ → [^n]
    # Verwende manuellen Ansatz, da Regex nicht matched
    # Finde alle Vorkommen von ${ }^{n}$ und ersetze sie
    def replace_fussnote_in_text(text):
        result = []
        i = 0
        while i < len(text):
            # Suche nach ${ }^{
            if i < len(text) - 6 and text[i:i+6] == '${ }^{':
                # Finde die Zahl nach ^{
                j = i + 6
                num_start = j
                while j < len(text) and text[j].isdigit():
                    j += 1
                if j < len(text) - 2 and text[j:j+2] == '}$':
                    # Gefunden! Extrahiere Nummer
                    fn_num = text[num_start:j]
                    # Ersetze durch [^n]
                    result.append(f' [^{fn_num}]')
                    i = j + 2
                    continue
            result.append(text[i])
            i += 1
        return ''.join(result)
    
    text_result = replace_fussnote_in_text(text_result)
    
    # Entferne doppelte Leerzeilen
    text_result = re.sub(r'\n\n\n+', '\n\n', text_result)
    
    # Füge Fußnoten-Definitionen am Ende hinzu
    if fussnoten_defs:
        text_result += '\n\n---\n\n## Fußnoten\n\n'
        # Sortiere nach Nummer
        sorted_fns = sorted(fussnoten_defs.items(), key=lambda x: int(x[0]))
        for fn_num, fn_text in sorted_fns:
            text_result += f"[^{fn_num}]: {fn_text}\n"
    
    return text_result


def bereinige_datei(input_path, output_path):
    """Bereinigt die GA001.md Datei"""
    print(f"Lese Datei: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print("Entferne Absatzumbrüche und füge Wörter zusammen...")
    text = entferne_absatzumbrueche_und_fuege_woerter_zusammen(text)
    
    print("Konvertiere Fußnoten...")
    text = konvertiere_fussnoten(text)
    
    print(f"Speichere bereinigte Datei: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print("Fertig!")


if __name__ == '__main__':
    input_file = Path('Steiner_GA/GA001-Goethes Naturwissenschaftliche Schriften/GA001/GA001.md')
    output_file = Path('Steiner_GA/GA001-Goethes Naturwissenschaftliche Schriften/GA001/GA001_bereinigt.md')
    
    bereinige_datei(input_file, output_file)

