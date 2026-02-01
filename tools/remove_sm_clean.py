# -*- coding: utf-8 -*-
"""Entferne SM ohne Leerzeichen vor Absatzanfaengen zu hinterlassen"""
import re

path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA203-Die Verantwortung des Menschen für die Weltentwickelung durch seinen geistigen Zusammenhang mit dem Erdplaneten und der St\alt\GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f'Vorher: {len(content)} Zeichen')

# Zaehle SM vor dem Loeschen
sm_count = len(re.findall(r'\[\|\d+\|\]', content)) + len(re.findall(r'\|\d+\|', content))
print(f'SM gefunden: {sm_count}')

# Entferne [|XX|] Format (mit umgebenden Leerzeichen)
content = re.sub(r'\s*\[\|\d+\|\]\s*', ' ', content)

# Entferne |XX| Format (mit umgebenden Leerzeichen)
content = re.sub(r'\s*\|\d+\|\s*', ' ', content)

# Bereinige: keine Leerzeichen am Zeilenanfang
content = re.sub(r'\n +', '\n', content)

# Bereinige: keine doppelten Leerzeichen
content = re.sub(r'  +', ' ', content)

# Bereinige: kein Leerzeichen vor Zeilenumbruch
content = re.sub(r' +\n', '\n', content)

print(f'Nachher: {len(content)} Zeichen')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fertig.')
