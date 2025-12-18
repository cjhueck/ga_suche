#!/usr/bin/env python3
"""Teste API-Response für GA035/5"""
import urllib.request
import json
import re

url = "http://localhost:3003/api/full-lecture/GA035/5"
with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode('utf-8'))

lecture = data.get('lecture', data)
paras = lecture.get('paragraphs', [])
print(f'Anzahl Paragraphen: {len(paras)}')
print()

for i, p in enumerate(paras[:5]):
    content = p.get('content', '')
    # Suche nach problematischen Mustern
    double_pipes = re.findall(r'\|\|', content)
    single_pipes = re.findall(r'\|[^|0-9]', content)
    normal_pages = re.findall(r'\|\d+\|', content)
    
    print(f'=== Para {i} ===')
    print(f'Content: {content[:120]}...')
    if double_pipes:
        print(f'  PROBLEM: Doppelte Pipes: {double_pipes}')
    if single_pipes:
        print(f'  PROBLEM: Einzelne Pipes: {single_pipes}')
    if normal_pages:
        print(f'  OK: Seitenmarker: {normal_pages}')
    print()

