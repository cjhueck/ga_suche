#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Listet Wandtafelzeichnungen nach GA-Band und GA K 58 Band."""

import json
from collections import defaultdict

# GA K 58 Zuordnung basierend auf dem Report
GA_K_58_MAPPING = {
    1: ['073A', '074', '076', '084'],
    2: ['191', '194'],
    3: ['196', '198'],
    4: ['199', '189'],
    5: ['200', '201'],
    6: ['202', '203', '204'],
    7: ['205', '206'],
    8: ['207', '208'],
    9: ['209', '210', '211', '212'],
    10: ['213', '214'],
    11: ['215', '216', '217', '218', '219', '220'],
    12: ['221', '222', '223', '224', '225'],
    13: ['227', '228', '229', '230'],
    14: ['232', '233'],
    15: ['233A', '234', '243'],
    16: ['235', '236', '237', '238', '240'],
    17: ['257', '258', '260', '260A'],
    18: ['271', '276', '288', '291'],
    19: ['278', '279'],
    20: ['281', '282', '283'],
    21: ['296', '303', '304', '306', '308'],
    22: ['311', '312', '313', '314', '315'],
    23: ['316', '317', '318'],
    24: ['322', '324A', '326', '327', '336', '340'],
    25: ['337B', '339', '342', '347', '348'],
    26: ['349', '350'],
    27: ['351', '352'],
    28: ['353', '354', '383'],
    29: ['343', '344', '346'],
    30: ['255B', '158', '180'],
}

# Umkehrung: GA -> GA K 58
GA_TO_K58 = {}
for k58, gas in GA_K_58_MAPPING.items():
    for ga in gas:
        GA_TO_K58[ga] = k58

# Lade chalkboards.json
with open('chalkboards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Zähle Tafeln pro GA-Band
ga_counts = defaultdict(int)
for cb in data['chalkboards']:
    ga_counts[cb['ga']] += 1

# LISTE 1: GA-Bände mit Anzahl Tafeln und GA K 58 Band
print('=' * 70)
print('LISTE 1: GA-Bände / Anzahl Tafeln / GA K 58 Band')
print('=' * 70)
print(f"{'GA-Band':<12} {'Tafeln':>8}    {'GA K 58 Band':<15}")
print('-' * 70)

sorted_gas = sorted(ga_counts.items(), key=lambda x: (len(x[0]), x[0]))
total = 0
for ga, count in sorted_gas:
    k58 = GA_TO_K58.get(ga, '?')
    k58_str = f'GA K 58_{k58}' if k58 != '?' else 'unbekannt'
    print(f"GA{ga:<10} {count:>8}    {k58_str:<15}")
    total += count
print('-' * 70)
print(f"{'GESAMT':<12} {total:>8}")

# LISTE 2: GA K 58 Band mit Anzahl Tafeln und GA-Bänden
print()
print('=' * 70)
print('LISTE 2: GA K 58 Band / Anzahl Tafeln / GA-Bände')
print('=' * 70)

k58_stats = defaultdict(lambda: {'count': 0, 'gas': set()})
for cb in data['chalkboards']:
    ga = cb['ga']
    k58 = GA_TO_K58.get(ga, 0)
    k58_stats[k58]['count'] += 1
    k58_stats[k58]['gas'].add(ga)

print(f"{'GA K 58 Band':<15} {'Tafeln':>8}    {'GA-Bände'}")
print('-' * 70)
total2 = 0
for k58 in sorted(k58_stats.keys()):
    if k58 == 0:
        continue
    stats = k58_stats[k58]
    gas_sorted = sorted(stats['gas'], key=lambda x: (len(x), x))
    gas_str = ', '.join([f'GA{g}' for g in gas_sorted])
    print(f"GA K 58_{k58:<6} {stats['count']:>8}    {gas_str}")
    total2 += stats['count']

# Unbekannte
if 0 in k58_stats:
    stats = k58_stats[0]
    gas_sorted = sorted(stats['gas'], key=lambda x: (len(x), x))
    gas_str = ', '.join([f'GA{g}' for g in gas_sorted])
    print(f"{'unbekannt':<15} {stats['count']:>8}    {gas_str}")
    total2 += stats['count']

print('-' * 70)
print(f"{'GESAMT':<15} {total2:>8}")

