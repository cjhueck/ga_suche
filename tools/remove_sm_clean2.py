# -*- coding: utf-8 -*-
"""Entferne SM ohne Leerzeichen vor Absatzanfaengen zu hinterlassen"""
import re

path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA203-Die Verantwortung des Menschen für die Weltentwickelung durch seinen geistigen Zusammenhang mit dem Erdplaneten und der St\alt\GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f'Vorher: {len(content)} Zeichen')

# Zeige erste SM
matches = re.findall(r'\|\d+\|', content)
print(f'SM im Format |XX| gefunden: {len(matches)}')
if matches:
    print(f'  Beispiele: {matches[:5]}')

# Entferne |XX| Format (ohne Klammern) - direkt im Wort oder mit Leerzeichen
content = re.sub(r'\|\d+\|', '', content)

# Bereinige: doppelte Leerzeichen
content = re.sub(r'  +', ' ', content)

# Bereinige: Leerzeichen am Zeilenanfang
content = re.sub(r'\n +', '\n', content)

# Bereinige: Leerzeichen vor Zeilenumbruch
content = re.sub(r' +\n', '\n', content)

print(f'Nachher: {len(content)} Zeichen')

# Pruefe ob noch SM vorhanden
remaining = re.findall(r'\|\d+\|', content)
print(f'Verbleibende SM: {len(remaining)}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fertig.')
