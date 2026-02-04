# -*- coding: utf-8 -*-
import json
import glob

old_folder = 'C:/Users/chuec/OneDrive/Obsidian/ga_suche - Kopien/ga_suche'
jfiles = glob.glob(f'{old_folder}/steiner-full-lectures-*.json')

print(f"Gefundene alte JSON-Dateien: {len(jfiles)}")

if jfiles:
    with open(jfiles[0], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    lectures = data.get('lectures', [])
    print(f'Anzahl Vorträge: {len(lectures)}')
    
    if lectures:
        lec = lectures[0]
        print(f'Erster Vortrag ID: {lec.get("id")}')
        paras = lec.get('paragraphs', [])
        print(f'Absätze: {len(paras)}')
        
        if paras:
            para = paras[0]
            print(f'Keys: {list(para.keys())}')
            print(f'Index: {para.get("index")}')
            # Altes Format hat 'content' statt 'text'
            text = para.get('text', '') or para.get('content', '')
            print(f'Text (erste 200 Zeichen): {text[:200]}')
