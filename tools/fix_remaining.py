# -*- coding: utf-8 -*-
"""
Manuelle Fixes fuer die verbleibenden SM
"""
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

alt_folder = os.path.join(folder, 'alt')

# Fixes: (Vortrag, alte_text, neue_text)
fixes = [
    # Vortrag 1
    (1, 'fühlte sich in einer geistigen', 'fühlte sich in einer [|19|] geistigen'),
    
    # Vortrag 2
    (2, 'Einfluss aus auf', 'Ein[|34|]fluss aus auf'),
    (2, 'Entwickelungsstufen früherer', 'Entwickelungsstufen [|42|] früherer'),
    
    # Vortrag 3
    (3, 'von Aufstieg kommen könne', 'von Aufstieg kommen [|48|] könne'),
    (3, 'rücken - es ist aber wahrhaftig', 'rücken - es ist aber [|57|] wahrhaftig'),
    
    # Vortrag 4
    (4, 'dar eine tiefe Einsicht', 'dar eine tiefe Ein[|69|]sicht'),
    (4, 'in der äußeren Welt. Denn', 'in der äußeren [|77|] Welt. Denn'),
    
    # Vortrag 5
    (5, 'Wahrheit zwischen zwei', 'Wahrheit zwi[|90|]schen zwei'),
    (5, 'siehe Seite 321. als Materie', 'siehe Seite 321. [|91|] als Materie'),
    
    # Vortrag 7
    (7, 'denke, aus einer - wie', 'denke, aus einer [|120|] - wie'),
    
    # Vortrag 8
    (8, 'wiedergeboren werden. den, und', 'wiedergeboren werden. [|135|] den, und'),
    (8, 'lasen, so würden sie sehen, dass', 'lasen, so würden sie [|143|] sehen, dass'),
    
    # Vortrag 9
    (9, 'Christus-Mysterium', 'Christus-[|157|]Mysterium'),
    
    # Vortrag 10
    (10, 'europäischen Zivilisation: „Ja, die', 'europäischen Zivilisa[|163|]tion: „Ja, die'),
    (10, 'Petrus- eine Johanneseinsetzung', 'Petrus- eine [|174|] Johanneseinsetzung'),
    
    # Vortrag 11
    (11, 'theosophische', 'theosophisehe'),  # OCR-Korrektur in Ziel
    (11, 'Vater ein Telegramm', 'Vater ein Tele[|190|]gramm'),
    
    # Vortrag 12
    (12, 'möglich', 'möglieh'),  # OCR in Ziel
    (12, 'Menschen-leben ist', 'Menschen-[|205|]leben ist'),
    (12, 'Menschen', 'Mensehen'),  # OCR in Ziel
    
    # Vortrag 13
    (13, 'selbst in seinem Inneren das Licht', 'selbst in seinem [|230|] Inneren das Licht'),
    (13, 'gewisse Säfte, die man der Natur', 'gewisse Säfte, die [|243|] man der Natur'),
    
    # Vortrag 14
    (14, 'dann über das, was sie nicht wissen', 'dann über das, was [|250|] sie nicht wissen'),
    
    # Vortrag 15
    (15, 'Jahve-Religion muss man ja nicht', 'Jahve-Religion muss [|269|] man ja nicht'),
    
    # Vortrag 16
    (16, 'Kunst in ihrer großen Vollkommenheit', 'Kunst in ihrer großen [|281|] Vollkommenheit'),
    
    # Vortrag 18
    (18, '"Wenn dasjenige', '[|307|] "Wenn dasjenige'),
]

def get_file(num):
    for f in os.listdir(alt_folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            return os.path.join(alt_folder, f)
    return None

applied = 0
for num, old, new in fixes:
    path = get_file(num)
    if not path:
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Versuche mit flexiblem Whitespace
    pattern = re.escape(old).replace(r'\ ', r'\s+')
    if re.search(pattern, content):
        content = re.sub(pattern, new, content, count=1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Vortrag {num}: "{old[:30]}..." -> angewendet')
        applied += 1
    else:
        print(f'Vortrag {num}: "{old[:30]}..." -> NICHT GEFUNDEN')

print(f'\n{applied} Fixes angewendet')
