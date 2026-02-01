# -*- coding: utf-8 -*-
import re

target_path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA203-Die Verantwortung des Menschen für die Weltentwickelung durch seinen geistigen Zusammenhang mit dem Erdplaneten und der St\alt\GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md'

with open(target_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Zaehle vorhandene SM
before = len(re.findall(r'\[?\|?\d+\|?\]?', content))
print(f'SM-artige Muster vorher: {before}')

# Entferne alle SM-Formate:
# [|XX|] - korrektes Format
# |XX| - defektes Format  
# |XX|X - defektes Format vor Buchstabe
result = re.sub(r'\[\|\d+\|\]', '', content)  # [|XX|]
result = re.sub(r'\|\d+\|', '', result)        # |XX|
result = re.sub(r'  +', ' ', result)           # Doppelte Leerzeichen

# Zaehle nach
after = len(re.findall(r'\[\|\d+\|\]', result))
print(f'SM nachher: {after}')

with open(target_path, 'w', encoding='utf-8') as f:
    f.write(result)

print('Fertig.')
