"""
Kontext-Analyse Tool: Extrahiert typische Kontextwörter für Suchbegriffe
Verwendung: python build_context_index.py <suchbegriff> [kontextlänge]
"""

import json
import glob
import sys
import os
import re
from collections import Counter

def extract_words_around_term(text, term, context_words=50):
    """
    Extrahiert Wörter in der Umgebung eines Suchbegriffs
    
    Args:
        text: Volltext
        term: Suchbegriff
        context_words: Anzahl Wörter vor und nach dem Begriff
    
    Returns:
        Liste von Kontextwörtern
    """
    words = text.split()
    term_lower = term.lower()
    context_words_list = []
    
    for i, word in enumerate(words):
        if term_lower in word.lower():
            # Extrahiere Kontext
            start = max(0, i - context_words)
            end = min(len(words), i + context_words + 1)
            
            context = words[start:i] + words[i+1:end]
            context_words_list.extend(context)
    
    return context_words_list

def is_substantive(word):
    """
    Heuristik: Ist das Wort ein Substantiv?
    - Beginnt mit Großbuchstaben
    - Nicht am Satzanfang (schwer zu erkennen, ignorieren wir)
    - Mindestens 3 Zeichen
    """
    # Bereinige Satzzeichen
    cleaned = re.sub(r'[^\w]', '', word)
    
    if len(cleaned) < 3:
        return False
    
    # Beginnt mit Großbuchstaben
    if not cleaned[0].isupper():
        return False
    
    # Filtere bekannte Nicht-Substantive
    stopwords = {'Der', 'Die', 'Das', 'Dem', 'Den', 'Des', 'Ein', 'Eine', 'Einer', 
                 'Eines', 'Einem', 'Einen', 'Und', 'Oder', 'Aber', 'Wenn', 'Dann',
                 'Wie', 'Was', 'Wer', 'Wo', 'Warum', 'Wann', 'Auch', 'Nur', 'Noch',
                 'Schon', 'Sehr', 'Mehr', 'Alle', 'Jede', 'Jeder', 'Jedes', 'Manche',
                 'Einige', 'Viele', 'Wenige', 'Andere', 'Solche', 'Welche'}
    
    if cleaned in stopwords:
        return False
    
    return True

def build_context_index(query, context_words=50, min_occurrences=3):
    """
    Baut einen Kontext-Index fuer einen Suchbegriff
    
    Args:
        query: Suchbegriff
        context_words: Anzahl Woerter im Kontext (+/-)
        min_occurrences: Minimale Haeufigkeit fuer Aufnahme in Index
    
    Returns:
        Dictionary mit typischen Kontextwoertern und Haeufigkeiten
    """
    print(f"Baue Kontext-Index fuer '{query}' (+/-{context_words} Woerter)...")
    print("="*80)
    
    all_context_words = []
    total_occurrences = 0
    lectures_with_term = 0
    
    # Durchsuche alle JSON-Dateien
    for file_path in glob.glob("steiner-full-lectures-*.json"):
        print(f"Analysiere {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                lectures = data.get('lectures', [])
                
                for lecture in lectures:
                    # Erstelle Volltext
                    paragraphs = lecture.get('paragraphs', [])
                    full_text = ' '.join([p.get('content', '') or p.get('text', '') 
                                         for p in paragraphs])
                    
                    # Prüfe ob Suchbegriff vorkommt
                    occurrences = full_text.lower().count(query.lower())
                    if occurrences > 0:
                        total_occurrences += occurrences
                        lectures_with_term += 1
                        
                        # Extrahiere Kontextwörter
                        context = extract_words_around_term(full_text, query, context_words)
                        all_context_words.extend(context)
        
        except Exception as e:
            print(f"Fehler bei {file_path}: {e}")
    
    print(f"\nGefunden: {total_occurrences} Vorkommen in {lectures_with_term} Vorträgen")
    print(f"Gesammelte Kontextwörter: {len(all_context_words)}")
    
    # Filtere nur Substantive
    substantives = [word for word in all_context_words if is_substantive(word)]
    print(f"Substantive gefunden: {len(substantives)}")
    
    # Zähle Häufigkeiten
    word_counts = Counter(substantives)
    
    # Filtere nach Mindesthäufigkeit
    filtered_words = {word: count for word, count in word_counts.items() 
                     if count >= min_occurrences}
    
    # Sortiere nach Häufigkeit
    sorted_words = dict(sorted(filtered_words.items(), 
                               key=lambda x: x[1], 
                               reverse=True))
    
    print(f"Typische Kontextwoerter (>={min_occurrences}x): {len(sorted_words)}")
    
    # Zähle Gesamtanzahl aller Vorträge
    total_lectures = 0
    for file_path in glob.glob("steiner-full-lectures-*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_lectures += len(data.get('lectures', []))
        except:
            pass
    
    # Ergebnis
    result = {
        'query': query,
        'context_words': context_words,
        'total_occurrences': total_occurrences,
        'lectures_with_term': lectures_with_term,
        'lectures_count': total_lectures,  # Gesamtanzahl aller Vorträge
        'context_terms': sorted_words,
        'top_20': dict(list(sorted_words.items())[:20])
    }
    
    return result

def main():
    if len(sys.argv) < 2:
        print("Verwendung: python build_context_index.py <suchbegriff> [kontextlänge]")
        print("Beispiel: python build_context_index.py Goetheanismus 100")
        sys.exit(1)
    
    query = sys.argv[1]
    context_words = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    # Baue Index
    result = build_context_index(query, context_words)
    
    # Zeige Top 20
    print("\n" + "="*80)
    print("TOP 20 KONTEXTWÖRTER:")
    print("="*80)
    for i, (word, count) in enumerate(result['top_20'].items(), 1):
        print(f"{i:2d}. {word:30s} {count:4d}x")
    
    # Speichere in zentrale Indizes-Datei
    indices_file = "context-indices.json"
    
    # Lade bestehende Indizes
    all_indices = {}
    if os.path.exists(indices_file):
        try:
            with open(indices_file, 'r', encoding='utf-8') as f:
                all_indices = json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden bestehender Indizes: {e}")
    
    # Füge neuen Index hinzu
    all_indices[query.lower()] = result
    
    # Speichere zurück
    with open(indices_file, 'w', encoding='utf-8') as f:
        json.dump(all_indices, f, ensure_ascii=False, indent=2)
    
    print(f"\nOK Kontext-Index gespeichert in: {indices_file}")
    print(f"  Begriff: {query}")
    print(f"  Enthaelt {len(result['context_terms'])} typische Kontextwoerter")
    print(f"  Gesamt {len(all_indices)} Begriffe in Datenbank")

if __name__ == '__main__':
    main()

