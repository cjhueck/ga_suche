# -*- coding: utf-8 -*-
"""Finale Fixes fuer alle verbleibenden SM"""
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

alt_folder = os.path.join(folder, 'alt')

# Format: (Vortrag, Suchmuster, Ersetzung)
# Suchmuster als Regex fuer flexibles Matching
fixes = [
    # Vortrag 3
    (3, r'es ist aber\s+wahrhaftig nicht trivial', 'es ist aber [|57|] wahrhaftig nicht trivial'),
    
    # Vortrag 5
    (5, r'siehe Seite 321\.\s+als Materie', 'siehe Seite 321. [|91|] als Materie'),
    
    # Vortrag 7
    (7, r'denke,\s+aus einer\s+-\s+wie er', 'denke, aus einer [|120|] - wie er'),
    
    # Vortrag 8
    (8, r'wiedergeboren werden\.\s+den,\s+und die luziferischen', 'wiedergeboren werden. [|135|] den, und die luziferischen'),
    (8, r'so würden sie\s+sehen,\s+dass die Zeit', 'so würden sie [|143|] sehen, dass die Zeit'),
    
    # Vortrag 9 - Bilder entfernt, Rest bleibt
    (9, r'Gesetzlichkeit der Natur enthält', 'Gesetzlich[|149|]keit der Natur enthält'),
    (9, r'\)\s+Das ist die Zwiespältigkeit', ') [|151|] Das ist die Zwiespältigkeit'),
    (9, r'lernt man erkennen,\s+dass\s+das Geistige eingreift', 'lernt man erkennen, dass [|152|] das Geistige eingreift'),
    (9, r'Christus-Mysterium', 'Christus-[|157|]Mysterium'),
    
    # Vortrag 10
    (10, r'europäischen Zivilisation:\s+„Ja,\s+die modern', 'europäischen Zivilisa[|163|]tion: „Ja, die modern'),
    (10, r'Nun,\s+das ist,\s+möchte ich sagen,\s+asiatischer', '[|167|] Nun, das ist, möchte ich sagen, asiatischer'),
    (10, r'neben der Petrus-\s+eine\s+Johanneseinsetzung', 'neben der Petrus- eine [|174|] Johanneseinsetzung'),
    
    # Vortrag 11
    (11, r'als theosophische\s+Lehre aufgetreten', 'als theosophi[|182|]sche Lehre aufgetreten'),
    (11, r'ein Telegramm\s+in der vereinbarten', 'ein Tele[|190|]gramm in der vereinbarten'),
    
    # Vortrag 12 - viele OCR-Probleme
    (12, r'dass es möglich\s+sei,\s+einen solchen', 'dass es mög[|201|]lich sei, einen solchen'),
    (12, r'die mit\s+allen Lebenskräften', 'die mit [|202|] allen Lebenskräften'),
    (12, r'überhaupt Menschenleben\s+ist\.\s+Daher ist', 'überhaupt Menschen[|205|]leben ist. Daher ist'),
    (12, r'dass solche Menschen\s+wie Frohnmeyer', 'dass solche Men[|210|]schen wie Frohnmeyer'),
    (12, r'„Tat"-Heft\.\s+Sehen Sie,\s+man sollte', '„Tat"-Heft. [|212|] Sehen Sie, man sollte'),
    (12, r'heranzuziehen\."\s+Ich wollte', 'heranzuziehen." [|214|] Ich wollte'),
    (12, r'Sumpfblumen\.\s+Es interessiert', 'Sumpfblumen. [|220|] Es interessiert'),
    
    # Vortrag 13
    (13, r'selbst in seinem\s+Inneren das Licht', 'selbst in seinem [|230|] Inneren das Licht'),
    
    # Vortrag 14
    (14, r'Dagegen die zurück', 'Dagegen die zurück[|257|]'),
    
    # Vortrag 15
    (15, r'Tafel 7\s+Nun ist das Eigentümliche', 'Tafel 7 [|266|] Nun ist das Eigentümliche'),
    (15, r'Jahve bildete den Menschen\s+aus dem Staub', 'Jahve bildete den Men[|267|]schen aus dem Staub'),
    (15, r'dem Umstände,\s+dass\s+sich in ihm Salze', 'dem Umstände, dass [|268|] sich in ihm Salze'),
    (15, r'Jahve-Religion muss\s+man ja nicht bloß', 'Jahve-Religion muss [|269|] man ja nicht bloß'),
    (15, r'innerhalb des Jahve-Reiches', 'innerhalb des Jahve-[|272|]Reiches'),
    
    # Vortrag 16
    (16, r'durch und durch egoistischen\s+Weise', 'durch und durch egoisti[|282|]schen Weise'),
    
    # Vortrag 18
    (18, r'^"Wenn dasjenige', '[|307|] "Wenn dasjenige'),
    (18, r'welches die Aufgabe\s+ernst gemeinter', 'welches die Auf[|320|]gabe ernst gemeinter'),
]

def get_file(num):
    for f in os.listdir(alt_folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            return os.path.join(alt_folder, f)
    return None

applied = 0
not_applied = []

for num, pattern, replacement in fixes:
    path = get_file(num)
    if not path:
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Suche mit Regex
    if re.search(pattern, content, re.MULTILINE):
        content = re.sub(pattern, replacement, content, count=1, flags=re.MULTILINE)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'V{num}: angewendet')
        applied += 1
    else:
        not_applied.append((num, pattern[:40]))
        print(f'V{num}: NICHT GEFUNDEN - {pattern[:40]}...')

print(f'\n{applied} Fixes angewendet, {len(not_applied)} nicht gefunden')
