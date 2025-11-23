#!/usr/bin/env python3
"""
Prüfe welche Varianten von "proß" noch vorhanden sind
"""

import re
from pathlib import Path
from collections import defaultdict

def check_pross_variants():
    """Suche nach allen Varianten von 'proß'"""
    steiner_ga_dir = Path("Steiner_GA")
    if not steiner_ga_dir.exists():
        print(f"Verzeichnis {steiner_ga_dir} nicht gefunden!")
        return
    
    # Suche nach allen Varianten
    pattern = re.compile(r'\b\w*[Pp]ro[ß]\w*\b')
    matches = defaultdict(int)
    examples = defaultdict(list)
    
    for md_file in steiner_ga_dir.rglob("*.md"):
        try:
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    with open(md_file, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            for match in pattern.finditer(content):
                word = match.group()
                matches[word] += 1
                if len(examples[word]) < 3:
                    # Hole Kontext
                    start = max(0, match.start() - 30)
                    end = min(len(content), match.end() + 30)
                    context = content[start:end].replace('\n', ' ')
                    examples[word].append({
                        'file': str(md_file.relative_to(steiner_ga_dir)),
                        'context': context
                    })
        except Exception as e:
            pass
    
    print(f"Gefunden: {sum(matches.values())} Vorkommen von 'proß' Varianten\n")
    print("=" * 80)
    print("VARIANTEN:")
    print("=" * 80)
    
    for word, count in sorted(matches.items(), key=lambda x: x[1], reverse=True):
        print(f"\n'{word}': {count}x")
        if examples[word]:
            print(f"  Beispiel aus: {examples[word][0]['file']}")
            print(f"  Kontext: ...{examples[word][0]['context'][:100]}...")

if __name__ == "__main__":
    check_pross_variants()

