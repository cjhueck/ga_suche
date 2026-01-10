#!/usr/bin/env python3
"""Debug-Skript für GA019/5 Matching"""

import re
from pathlib import Path

def normalize(text):
    text = text.lower()
    text = text.replace('ä', 'a').replace('ö', 'o').replace('ü', 'u').replace('ß', 'ss')
    text = re.sub(r'[^a-z]', '', text)
    return text

# Lade MsA für GA019/5
base = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA')
for d in base.iterdir():
    if 'GA019' in d.name:
        for f in d.iterdir():
            if '(5.)' in f.name and f.suffix == '.md':
                msa = f.read_text(encoding='utf-8')
                msa_norm = normalize(msa)
                
                print(f"MsA Datei: {f.name}")
                print(f"MsA Länge: {len(msa)} Zeichen")
                print(f"MsA norm (100 chars): {msa_norm[:100]}")
                print()
                
                # Suche nach Text, der auf verschiedenen Seiten steht
                test_texts = [
                    'Stimmen vernehmen',
                    'dieser Krieg doch die Lehre',
                    'Man könnte auch',
                    'kein Volk darf gezwungen werden',
                    'So umschreibt Herr Wilson',
                ]
                
                for t in test_texts:
                    t_norm = normalize(t)
                    pos = msa_norm.find(t_norm)
                    if pos >= 0:
                        print(f"GEFUNDEN: '{t}' bei Position {pos}")
                    else:
                        print(f"NICHT GEFUNDEN: '{t}'")

