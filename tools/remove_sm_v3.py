# -*- coding: utf-8 -*-
import re

path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA\GA203-Die Verantwortung des Menschen für die Weltentwickelung durch seinen geistigen Zusammenhang mit dem Erdplaneten und der St\alt\GA203 (1.) ERSTER VORTRAG, Stuttgart, 1. Januar 1921.md'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Zeige erste Zeile
print('Erste Zeile vorher:')
print(content[:200])

# Entferne |XX| (Pipe-Zahl-Pipe) - escaped pipes
content = re.sub(r'\|(\d+)\|', '', content)

# Doppelte Leerzeichen bereinigen
content = re.sub(r'  +', ' ', content)

# Leerzeichen am Zeilenanfang
content = re.sub(r'\n ', '\n', content)

print('\nErste Zeile nachher:')
print(content[:200])

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('\nGespeichert.')
