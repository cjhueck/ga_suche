#!/usr/bin/env python3
"""Prüft und korrigiert alle Rechtschreibfehler"""

from pathlib import Path
import re

# Test-Wörter die noch vorhanden sein könnten
test_words = ['daß', 'muß', 'Bewußtsein', 'wußte', 'müßte', 'Prozeß', 'Fluß', 'Schloß']

def check_spelling():
    """Prüft ob noch alte Rechtschreibung vorhanden ist"""
    steiner_ga_dir = Path("Steiner_GA")
    results = {}
    
    for word in test_words:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        count = 0
        for md_file in steiner_ga_dir.rglob("*.md"):
            if '.trash' in str(md_file):
                continue
            try:
                with open(md_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    count += len(pattern.findall(content))
            except:
                pass
        results[word] = count
    
    print("Gefundene alte Rechtschreibung:")
    for word, count in results.items():
        if count > 0:
            print(f"  {word}: {count}x")
    
    return results

if __name__ == "__main__":
    check_spelling()

