# -*- coding: utf-8 -*-
"""Analysiere fehlende SM - zeige Kontext in Quelle und Ziel"""
import re
import os

base = r'c:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'
for item in os.listdir(base):
    if 'GA203' in item and os.path.isdir(os.path.join(base, item)):
        folder = os.path.join(base, item)
        break

alt_folder = os.path.join(folder, 'alt')

missing = [
    (3, 57), (5, 91), (7, 120), (8, 135), (8, 143),
    (9, 149), (9, 151), (9, 152), (9, 157),
    (10, 163), (10, 167), (10, 174),
    (11, 182), (11, 190),
    (12, 201), (12, 202), (12, 205), (12, 210), (12, 212), (12, 214), (12, 220),
    (13, 230), (14, 257),
    (15, 266), (15, 267), (15, 268), (15, 269), (15, 272),
    (16, 282), (18, 307), (18, 320)
]

def get_source(num):
    for f in os.listdir(folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            return os.path.join(folder, f)
    return None

def get_target(num):
    for f in os.listdir(alt_folder):
        if f.startswith(f'GA203 ({num}.)') and f.endswith('.md'):
            return os.path.join(alt_folder, f)
    return None

for num, page in missing:
    src_path = get_source(num)
    tgt_path = get_target(num)
    
    if not src_path or not tgt_path:
        continue
    
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    with open(tgt_path, 'r', encoding='utf-8') as f:
        tgt = f.read()
    
    sm = f'[|{page}|]'
    match = re.search(re.escape(sm), src)
    if match:
        pos = match.start()
        before = src[max(0,pos-40):pos]
        after = src[match.end():match.end()+40]
        
        # Bereinige
        before = re.sub(r'\[\|\d+\|\]', '', before)
        after = re.sub(r'\[\|\d+\|\]', '', after)
        
        print(f'\n=== Vortrag {num}, SM {page} ===')
        print(f'QUELLE: ...{before}{sm}{after}...')
        
        # Suche aehnlichen Text in Ziel
        search = before[-20:].strip() + after[:20].strip()
        search_clean = re.sub(r'\s+', ' ', search)
        if search_clean in tgt:
            print(f'ZIEL: Text gefunden!')
        else:
            print(f'ZIEL: Text NICHT gefunden')
            print(f'  Suchtext: "{search_clean}"')
