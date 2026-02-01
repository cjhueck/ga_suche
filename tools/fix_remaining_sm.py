# -*- coding: utf-8 -*-
"""
Fuege die verbleibenden 9 SM ein basierend auf Quellkontext
"""
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
folder = None
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

alt = os.path.join(folder, 'alt')

def find_and_fix(num, page, searches, replacement_func):
    """Suche und ersetze in Zieldatei"""
    for f in os.listdir(alt):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            path = os.path.join(alt, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            for search in searches:
                if search in content:
                    new_content = replacement_func(content, search)
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8') as file:
                            file.write(new_content)
                        print(f'  Vortrag {num}, [|{page}|]: eingefuegt bei "{search[:40]}..."')
                        return True
            
            print(f'  Vortrag {num}, [|{page}|]: NICHT GEFUNDEN')
            return False
    return False

total = 0

# Vortrag 2, [|42|]: Entwicklungsstufen [|42|] früherer
if find_and_fix(2, 42, 
    ['Entwicklungsstufen früherer', 'Entwicklungsstufen frueherer'],
    lambda c, s: c.replace(s, s.replace('Entwicklungsstufen ', 'Entwicklungsstufen [|42|] '), 1)):
    total += 1

# Vortrag 5, [|91|]: Seite 321. [|91|] als
if find_and_fix(5, 91,
    ['321. als', 'Seite 321. als', '321 als'],
    lambda c, s: c.replace(s, s.replace('321', '321 [|91|]').replace('[|91|].', '[|91|]').replace('[|91|] ', '[|91|] '), 1)):
    total += 1

# Vortrag 8, [|135|]: werden. [|135|] den, (OCR-Fehler "Wer-den")
# Suche alternative Kontexte
if find_and_fix(8, 135,
    ['wiedergeboren werden. Den', 'wiedergeboren werden. den', 'werden. Den,', 'werden. den,'],
    lambda c, s: c.replace(s, s.replace('werden. ', 'werden. [|135|] '), 1)):
    total += 1

# Vortrag 9, [|149|]: nach Bild, vor "keit" - suche "Natuerlichkeit" oder aehnlich
# Der Kontext zeigt: nach einem Bild kommt "[|149|] keit der Natur"
# Suche Woerter die auf "keit" enden
if find_and_fix(9, 149,
    ['Natuerlichkeit der Natur', 'Natürlichkeit der Natur', 'lichkeit der Natur'],
    lambda c, s: c.replace(s, '[|149|] ' + s, 1)):
    total += 1

# Vortrag 9, [|157|]: Christus[|157|]Mysterium
if find_and_fix(9, 157,
    ['Christus-Mysterium', 'Christus–Mysterium', 'ChristusMysteri'],
    lambda c, s: c.replace(s, 'Christus[|157|]' + s[8:] if s.startswith('Christus') else s, 1)):
    total += 1

# Vortrag 10, [|167|]: aus. [|167|] Nun - asiatische Kritik Kontext
if find_and_fix(10, 167,
    ['aus. Nun, das ist', 'aus. Nun, das', 'aus.  Nun'],
    lambda c, s: c.replace(s, s.replace('aus. ', 'aus. [|167|] ').replace('aus.  ', 'aus. [|167|] '), 1)):
    total += 1

# Vortrag 14, [|257|]: zurück[|257|]Tafel - vor "Tafel 6"
if find_and_fix(14, 257,
    ['zurückTafel', 'zurück Tafel', 'zurueckTafel', 'zurueck Tafel'],
    lambda c, s: c.replace(s, s.replace('zurück', 'zurück[|257|]').replace('zurueck', 'zurueck[|257|]'), 1)):
    total += 1

# Vortrag 15, [|266|]: Tafel 7 [|266|] Nun
if find_and_fix(15, 266,
    ['Tafel 7 Nun', 'Tafel 7  Nun', '7 Nun ist'],
    lambda c, s: c.replace(s, s.replace('7 ', '7 [|266|] '), 1)):
    total += 1

# Vortrag 15, [|272|]: Jahve[|272|]Reiches
if find_and_fix(15, 272,
    ['Jahve-Reiches', 'Jahve–Reiches', 'JahveReiches', 'Jahve Reiches'],
    lambda c, s: c.replace(s, s[:5] + '[|272|]' + s[5:] if 'Jahve' in s else s, 1)):
    total += 1

print(f'\n{total} weitere SM eingefuegt')
