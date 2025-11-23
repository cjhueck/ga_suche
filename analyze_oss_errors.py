#!/usr/bin/env python3
"""
Analysiere die gefundenen 'oß'/'Oß' Vorkommen und identifiziere echte Fehler
"""

import re
from collections import defaultdict

# Liste korrekter deutscher Wörter mit 'oß' (die NICHT geändert werden sollen)
CORRECT_WORDS = {
    'bloß', 'bloßen', 'bloße', 'bloßer', 'bloßes',
    'groß', 'großen', 'große', 'großer', 'großes', 'großem', 'großer', 'großte', 'größte',
    'oß',  # könnte auch korrekt sein in bestimmten Kontexten
    'oßen',  # "oben" - aber hier ist es falsch geschrieben!
    'Oktober',  # sollte "Oktober" sein, nicht "Oktoßer"
    'beobachten', 'beobachtet', 'beobachtung', 'Beobachtung',  # sollte "beobachten" sein
    'oberfläche', 'Oberfläche',  # sollte "Oberfläche" sein
    'obwohl',  # sollte "obwohl" sein
    'objektiv', 'objektive', 'Objektiv', 'Objektive',  # sollte "objektiv" sein
    'Problem', 'Probleme',  # sollte "Problem" sein
    'Jakob',  # sollte "Jakob" sein
}

def analyze_results():
    """Analysiere die gefundenen Fehler"""
    
    # Lese die Ergebnisse
    with open('oss_errors_found.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extrahiere alle gefundenen Wörter aus der detaillierten Liste
    word_pattern = re.compile(r"Wort: '([^']+)'")
    words = word_pattern.findall(content)
    
    # Kategorisiere die Wörter
    likely_errors = []
    correct_words = []
    uncertain = []
    
    for word in set(words):  # Eindeutige Wörter
        word_lower = word.lower()
        
        # Prüfe ob es ein bekannter Fehler ist
        if word_lower in ['oß', 'oßen', 'oktoßer', 'beoßachten', 'beoßachtet', 'beoßachtung',
                         'oßerfläche', 'oßwohl', 'oßjektiv', 'oßjektive', 'proßlem', 'jakoß']:
            likely_errors.append(word)
        elif any(correct in word_lower for correct in ['bloß', 'groß', 'größ']):
            correct_words.append(word)
        else:
            uncertain.append(word)
    
    # Ausgabe
    output_file = "oss_real_errors.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ANALYSE DER GEFUNDENEN 'oß'/'Oß' VORKOMMEN\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("WAHRSCHEINLICHE FEHLER (sollten 'ob'/'Ob' sein):\n")
        f.write("-" * 80 + "\n")
        for word in sorted(set(likely_errors)):
            f.write(f"  '{word}' → sollte wahrscheinlich '{word.replace('oß', 'ob').replace('Oß', 'Ob')}' sein\n")
        
        f.write(f"\n\nKORREKTE WÖRTER (mit 'oß'/'Oß'):\n")
        f.write("-" * 80 + "\n")
        for word in sorted(set(correct_words))[:50]:
            f.write(f"  '{word}'\n")
        
        f.write(f"\n\nUNSICHERE FÄLLE (müssen manuell geprüft werden):\n")
        f.write("-" * 80 + "\n")
        for word in sorted(set(uncertain))[:100]:
            f.write(f"  '{word}'\n")
    
    print(f"Analyse gespeichert in '{output_file}'")
    print(f"\nWahrscheinliche Fehler: {len(set(likely_errors))}")
    print(f"Korrekte Wörter: {len(set(correct_words))}")
    print(f"Unsichere Fälle: {len(set(uncertain))}")

if __name__ == "__main__":
    analyze_results()

