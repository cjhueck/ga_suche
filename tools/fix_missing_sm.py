# -*- coding: utf-8 -*-
"""
Fuege die 24 fehlenden SM manuell ein
"""
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
folder = None
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

alt_folder = os.path.join(folder, 'alt')

# Mapping: Vortrag -> Liste von (SM, korrektes_Wort, Ersetzung)
# Format: Das korrekte Wort in der Zieldatei wird durch Wort mit SM ersetzt
fixes = {
    2: [
        # [|42|]: Entwicklungsstufen | früherer -> suche "Entwicklungsstufen früherer"
        ('Entwicklungsstufen früherer', 'Entwicklungsstufen [|42|] früherer'),
    ],
    3: [
        # [|59|]: Gita, | muß -> suche "Gita, muß" oder "Gita, muss"
        ('Gita, muss', 'Gita, [|59|] muss'),
        ('Gita, muß', 'Gita, [|59|] muß'),
    ],
    4: [
        # [|69|]: Ein | sieht -> "Einsieht" oder "Ein sieht"
        ('Einsicht', 'Ein[|69|]sicht'),
    ],
    5: [
        # [|90|]: zwi | sehen -> "zwischen"
        ('zwischen', 'zwi[|90|]schen'),
        # [|91|]: 321. | als -> suche Kontext
        ('321. als', '321. [|91|] als'),
        ('321 als', '321 [|91|] als'),
    ],
    6: [
        # [|108|]: faßt | das, -> "fasst das" oder "faßt das"
        ('fasst das,', 'fasst [|108|] das,'),
        ('faßt das,', 'faßt [|108|] das,'),
    ],
    7: [
        # [|120|]: einer | - -> suche "einer -"
        ('einer -', 'einer [|120|] -'),
        ('einer –', 'einer [|120|] –'),
    ],
    8: [
        # [|135|]: werden. | den, -> OCR Fehler, suche Kontext
        ('werden. den,', 'werden. [|135|] den,'),
        ('werden. Den,', 'werden. [|135|] Den,'),
    ],
    9: [
        # [|149|]: | keit -> Teil eines Wortes, schwierig
        # [|152|]: daß | das -> "dass das" oder "daß das"  
        ('dass das', 'dass [|152|] das'),
        ('daß das', 'daß [|152|] das'),
        # [|157|]: Christus | Mysterium -> "ChristusMysteri" -> "Christus-Mysterium"
        ('Christus-Mysterium', 'Christus[|157|]-Mysterium'),
        ('ChristusMysteri', 'Christus[|157|]Mysteri'),
    ],
    10: [
        # [|167|]: aus.="" | Nun, -> HTML/Sonderzeichen, suche "aus. Nun"
        ('aus. Nun', 'aus. [|167|] Nun'),
    ],
    11: [
        # [|182|]: theosophi | sehe -> "theosophische"
        ('theosophische', 'theosophi[|182|]sche'),
        # [|196|]: Bewußtsein | hineingehen -> "Bewusstsein hineingehen"
        ('Bewusstsein hineingehen', 'Bewusstsein [|196|] hineingehen'),
        ('Bewußtsein hineingehen', 'Bewußtsein [|196|] hineingehen'),
    ],
    12: [
        # [|201|]: mög | lieh -> "möglich"
        ('möglich', 'mög[|201|]lich'),
        # [|210|]: Men | sehen -> "Menschen"
        ('Menschen', 'Men[|210|]schen'),
        # [|222|]: werden | muß -> "werden muss"
        ('werden muss', 'werden [|222|] muss'),
        ('werden muß', 'werden [|222|] muß'),
    ],
    14: [
        # [|257|]: zurück | Tafel -> "zurück Tafel" oder zusammen
        ('zurückTafel', 'zurück[|257|]Tafel'),
        ('zurück Tafel', 'zurück [|257|] Tafel'),
    ],
    15: [
        # [|266|]: 7 | Nun -> "7 Nun" oder Fussnote
        ('7 Nun', '7 [|266|] Nun'),
        # [|267|]: Men | sehen -> "Menschen"
        ('Menschen', 'Men[|267|]schen'),
        # [|269|]: muß | man -> "muss man"
        ('muss man', 'muss [|269|] man'),
        ('muß man', 'muß [|269|] man'),
        # [|272|]: Jahve | Reiches -> "Jahve-Reiches" oder "JahveReiches"
        ('Jahve-Reiches', 'Jahve[|272|]-Reiches'),
        ('JahveReiches', 'Jahve[|272|]Reiches'),
        ('Jahve Reiches', 'Jahve [|272|] Reiches'),
    ],
    16: [
        # [|281|]: großen | kommenheit -> "Vollkommenheit" (Teil davon)
        ('Vollkommenheit', 'Voll[|281|]kommenheit'),
        # [|282|]: egoisti | sehen -> "egoistischen"
        ('egoistischen', 'egoisti[|282|]schen'),
    ],
}

def find_target_file(num):
    """Finde Zieldatei fuer Vortrag"""
    for f in os.listdir(alt_folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md') and 'alt' not in f:
            return os.path.join(alt_folder, f)
    return None

def apply_fixes(num, fix_list):
    """Wende Fixes auf Vortrag an"""
    target_file = find_target_file(num)
    if not target_file:
        print(f'  Vortrag {num}: Datei nicht gefunden')
        return 0
    
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    applied = 0
    for old, new in fix_list:
        if old in content and new not in content:
            content = content.replace(old, new, 1)
            applied += 1
            print(f'  Vortrag {num}: {old[:30]}... -> eingefuegt')
    
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return applied

# Hauptprogramm
print('Fuege fehlende SM ein...\n')
total = 0

for num, fix_list in fixes.items():
    applied = apply_fixes(num, fix_list)
    total += applied

print(f'\n{total} SM eingefuegt')
