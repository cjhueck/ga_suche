"""Kürzt GA002 MsAN auf MsA-Länge."""
from pathlib import Path
import re

folder = Path('Steiner_GA/GA002-Grundlinien einer Erkenntnistheorie der Goetheschen Weltanschauung')

msa = (folder / 'GA002 - Grundlinien einer Erkenntnistheorie der Goetheschen Weltanschauung (1886).md').read_text(encoding='utf-8')
msan_path = folder / 'GA002 - Grundlinien einer Erkenntnistheorie der Goetheschen Weltanschauung (1886)_new.md'
msan = msan_path.read_text(encoding='utf-8')

print(f"MsA: {len(msa)} Zeichen")
print(f"MsAN: {len(msan)} Zeichen")

# Finde den letzten inhaltlichen Absatz aus MsA in MsAN
search_text = 'Dieser Sinn ist'
pos = msan.find(search_text)
print(f"Gefunden bei Position {pos}")

if pos > 0:
    # Finde Ende dieses Absatzes
    end_para = msan.find('\n\n', pos)
    print(f"Absatz endet bei {end_para}")
    
    # Zeige den Kontext
    if end_para > 0:
        print(f"\n=== Kontext um Schnittpunkt ===")
        print(msan[pos:end_para+100])
        
        # Suche die Fußnote danach
        rest = msan[end_para:end_para+1000]
        fn_match = re.search(r'\[\^13\].*?(?=\n\n|\Z)', rest, re.DOTALL)
        if fn_match:
            print(f"\nFußnote gefunden: {fn_match.group()[:100]}...")
            # Schneide nach der Fußnote ab
            fn_end = end_para + fn_match.end()
            msan_cut = msan[:fn_end].strip()
        else:
            msan_cut = msan[:end_para].strip()
        
        # Wörter zählen
        def count_words(text):
            text = re.sub(r'\^[a-z0-9]+', '', text)
            text = re.sub(r'\|\d+\|', '', text)
            return len(re.findall(r'\b\w+\b', text))
        
        msa_words = count_words(msa)
        msan_words = count_words(msan_cut)
        diff = abs(msan_words - msa_words) / msa_words * 100
        
        print(f"\nWortanzahl: MsA={msa_words}, MsAN={msan_words}")
        print(f"Differenz: {diff:.1f}%")
        
        # Speichere
        msan_path.write_text(msan_cut, encoding='utf-8')
        print(f"\nGespeichert! ({len(msan_cut)} Zeichen)")

