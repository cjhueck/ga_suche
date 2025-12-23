#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erstellt Listen der Wandtafeln nach GA und K-Band."""

import json
import re
from collections import defaultdict
from pathlib import Path

# GA K Band Zuordnungen (Rudolf Steiner Gesamtausgabe Kunstmappen)
GA_K_MAPPING = {
    'K20': (73, 84),      # Philosophie
    'K26': (157, 163),
    'K27': (166, 178),
    'K28': (180, 195),
    'K29': (196, 199),
    'K30': (200, 202),
    'K31': (203, 210),
    'K32': (211, 219),
    'K33': (220, 223),
    'K34': (224, 227),
    'K35': (228, 230),
    'K36': (231, 233),    # inkl. 233a
    'K37': (234, 234),
    'K38': (235, 235),
    'K39': (236, 236),
    'K40': (237, 237),
    'K41': (238, 243),
    'K42': (254, 258),
    'K43': (260, 270),
    'K44': (271, 291),    # Kunst
    'K53': (293, 311),    # Pädagogik
    'K54': (312, 319),    # Medizin
    'K55': (320, 327),    # Naturwissenschaft
    'K56': (328, 341),    # Soziales
    'K57': (342, 354),    # Arbeitervorträge
}

def get_ga_num(ga_str):
    """Extrahiere numerischen Teil (z.B. '233A' -> 233)"""
    match = re.match(r'(\d+)', ga_str)
    return int(match.group(1)) if match else 0

def find_k_band(ga_str):
    """Finde den zugehörigen K-Band für eine GA-Nummer."""
    num = get_ga_num(ga_str)
    for k, (start, end) in GA_K_MAPPING.items():
        if start <= num <= end:
            return k
    return None

def main():
    project_dir = Path(__file__).parent.parent
    
    with open(project_dir / 'chalkboards.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Zähle Tafeln pro GA
    ga_counts = defaultdict(int)
    for c in data['chalkboards']:
        ga_counts[c['ga']] += 1

    # Sortiere nach GA-Nummer
    sorted_gas = sorted(ga_counts.keys(), key=lambda x: (get_ga_num(x), x))

    # Liste 1
    print('=' * 40)
    print('LISTE 1: GA Nummer | Anzahl Tafeln | K-Band')
    print('=' * 40)
    print(f"{'GA':<10} {'Tafeln':>8}   {'K-Band':<8}")
    print('-' * 40)
    
    total = 0
    for ga in sorted_gas:
        k = find_k_band(ga) or '-'
        print(f"GA{ga:<7} {ga_counts[ga]:>8}   {k:<8}")
        total += ga_counts[ga]
    
    print('-' * 40)
    print(f"{'GESAMT':<10} {total:>8}")
    print(f"\nAnzahl GA-Bände: {len(sorted_gas)}")

    # Liste 2: K-Band gruppiert
    print('\n')
    print('=' * 70)
    print('LISTE 2: K-Band | Anzahl Tafeln | GA Nummern')
    print('=' * 70)
    print(f"{'K-Band':<10} {'Tafeln':>8}   GA Nummern")
    print('-' * 70)

    k_data = defaultdict(lambda: {'count': 0, 'gas': []})
    no_k = {'count': 0, 'gas': []}

    for ga in sorted_gas:
        k = find_k_band(ga)
        if k:
            k_data[k]['count'] += ga_counts[ga]
            k_data[k]['gas'].append(f"GA{ga}({ga_counts[ga]})")
        else:
            no_k['count'] += ga_counts[ga]
            no_k['gas'].append(f"GA{ga}({ga_counts[ga]})")

    total_k = 0
    for k in sorted(k_data.keys(), key=lambda x: int(x[1:])):
        gas_str = ', '.join(k_data[k]['gas'])
        print(f"{k:<10} {k_data[k]['count']:>8}   {gas_str}")
        total_k += k_data[k]['count']

    if no_k['count'] > 0:
        print(f"{'(kein K)':<10} {no_k['count']:>8}   {', '.join(no_k['gas'])}")

    print('-' * 70)
    print(f"{'GESAMT':<10} {total:>8}")
    print(f"\nAnzahl K-Bände: {len(k_data)}")

if __name__ == "__main__":
    main()

