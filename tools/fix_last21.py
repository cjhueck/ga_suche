# -*- coding: utf-8 -*-
"""Finale 21 Fixes basierend auf tatsaechlichen Ziel-Texten"""
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

alt_folder = os.path.join(folder, 'alt')

def get_file(num):
    for f in os.listdir(alt_folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            return os.path.join(alt_folder, f)
    return None

def apply_fix(num, old, new):
    path = get_file(num)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if old in content:
        content = content.replace(old, new, 1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

applied = 0

# V7 SM 120
if apply_fix(7, 'denke, aus einer – wie er natürlich meinte – abstrakten',
                'denke, aus einer [|120|] – wie er natürlich meinte – abstrakten'):
    print('V7 SM 120: OK')
    applied += 1

# V8 SM 135
if apply_fix(8, 'Wir können wiedergeboren werden, und die luziferischen',
                'Wir können wiedergeboren werden. [|135|] den, und die luziferischen'):
    print('V8 SM 135: OK')
    applied += 1
else:
    # Alternativer Text
    if apply_fix(8, 'können wiedergeboren werden, und',
                    'können wiedergeboren werden. [|135|] den, und'):
        print('V8 SM 135 (alt): OK')
        applied += 1

# V9 SM 151 - nach Bild
if apply_fix(9, ']] Das ist die Zwiespältigkeit',
                ']] [|151|] Das ist die Zwiespältigkeit'):
    print('V9 SM 151: OK')
    applied += 1

# V9 SM 152
if apply_fix(9, 'Dann lernt man erkennen, dass das Geistige',
                'Dann lernt man erkennen, dass [|152|] das Geistige'):
    print('V9 SM 152: OK')
    applied += 1

# V9 SM 157 - Christus-Mysterium mit langem Strich
if apply_fix(9, 'das Christus–Mysterium wirklich begreift',
                'das Christus–[|157|]Mysterium wirklich begreift'):
    print('V9 SM 157: OK')
    applied += 1

# V10 SM 167
if apply_fix(10, 'Nun, das ist, möchte ich sagen, asiatischer',
                 '[|167|] Nun, das ist, möchte ich sagen, asiatischer'):
    print('V10 SM 167: OK')
    applied += 1

# V10 SM 174 - Petrus mit langem Strich
if apply_fix(10, 'neben der Petrus– eine Johanneseinsetzung',
                 'neben der Petrus– eine [|174|] Johanneseinsetzung'):
    print('V10 SM 174: OK')
    applied += 1

# V11 SM 182 - theosophische
if apply_fix(11, 'als theosophische Lehre aufgetreten',
                 'als theosophi[|182|]sche Lehre aufgetreten'):
    print('V11 SM 182: OK')
    applied += 1
else:
    if apply_fix(11, 'Die theosophische Bewegung',
                     'Die theosophi[|182|]sche Bewegung'):
        print('V11 SM 182 (alt): OK')
        applied += 1

# V12 SM 205 - Menschenleben
if apply_fix(12, 'das Menschenleben und das Weltleben',
                 'das Menschen[|205|]leben und das Weltleben'):
    print('V12 SM 205: OK')
    applied += 1

# V12 SM 212 - Tat-Heft
if apply_fix(12, '„Tat"–Heft. Sehen Sie, man sollte',
                 '„Tat"–Heft. [|212|] Sehen Sie, man sollte'):
    print('V12 SM 212: OK')
    applied += 1

# V12 SM 214
if apply_fix(12, 'heranzuziehen.» Ich wollte',
                 'heranzuziehen.» [|214|] Ich wollte'):
    print('V12 SM 214: OK')
    applied += 1

# V13 SM 230
if apply_fix(13, 'selber in seinem Inneren das Licht fortgeleitet',
                 'selber in seinem [|230|] Inneren das Licht fortgeleitet'):
    print('V13 SM 230: OK')
    applied += 1

# V15 SM 272 - Jahve-Reiches mit langem Strich
if apply_fix(15, 'innerhalb des Jahve–Reiches die luziferischen',
                 'innerhalb des Jahve–[|272|]Reiches die luziferischen'):
    print('V15 SM 272: OK')
    applied += 1

# V18 SM 307 - Am Anfang
path = get_file(18)
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Suche nach BOM oder Anfang
if content.startswith('"Wenn dasjenige'):
    content = '[|307|] ' + content
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('V18 SM 307: OK')
    applied += 1
elif '\ufeff"Wenn' in content:
    content = content.replace('\ufeff"Wenn', '\ufeff[|307|] "Wenn')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('V18 SM 307 (BOM): OK')
    applied += 1

print(f'\n{applied} Fixes angewendet')
