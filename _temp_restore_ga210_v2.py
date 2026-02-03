#!/usr/bin/env python3
"""
Versucht, die alten GA210-IDs durch Textsuche zu finden.

Strategie:
1. Extrahiere Textausschnitte aus den Concepts (Zitate vor/nach der ID-Referenz)
2. Suche diese Texte in den neuen Vorträgen
3. Finde die neue ID für den passenden Paragraphen
"""

import json
import re
from difflib import SequenceMatcher
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def text_similarity(a, b):
    """Berechnet Textähnlichkeit zwischen 0 und 1"""
    if not a or not b:
        return 0
    # Normalisiere
    a = re.sub(r'\s+', ' ', a.lower().strip())
    b = re.sub(r'\s+', ' ', b.lower().strip())
    return SequenceMatcher(None, a, b).ratio()

def extract_context_around_ref(text, ref_pattern):
    """Extrahiert den Kontext um eine Referenz herum"""
    # Finde die Referenz und extrahiere 100 Zeichen davor
    match = re.search(re.escape(ref_pattern), text)
    if match:
        start = max(0, match.start() - 150)
        context_before = text[start:match.start()]
        # Bereinige
        context_before = re.sub(r'\([^)]*\)', '', context_before)  # Entferne andere Referenzen
        context_before = re.sub(r'\s+', ' ', context_before).strip()
        # Nimm nur den letzten Teil
        if len(context_before) > 50:
            context_before = context_before[-100:]
        return context_before
    return None

def find_paragraph_by_text(search_text, paragraphs, min_similarity=0.5):
    """Findet den besten passenden Paragraphen"""
    if not search_text or len(search_text) < 20:
        return None
    
    best_match = None
    best_score = min_similarity
    
    for new_id, para_text, position in paragraphs:
        # Prüfe ob Suchtext im Paragraphen enthalten ist
        if search_text.lower() in para_text.lower():
            return (new_id, 1.0, 'exact-substring')
        
        # Berechne Ähnlichkeit für kürzere Texte
        # Vergleiche nur die ersten 200 Zeichen
        score = text_similarity(search_text[:200], para_text[:200])
        if score > best_score:
            best_score = score
            best_match = (new_id, score, 'similarity')
    
    return best_match

def extract_quotes_from_concepts(concepts_backup):
    """Extrahiert Zitate aus Concepts, die GA210-Referenzen haben"""
    ga210_ref_pattern = re.compile(r'\(GA210/(\d+):\^?([a-z0-9]+)\)')
    
    quotes = {}  # {(lecture_num, old_id): [quote_contexts]}
    
    for concept in concepts_backup:
        keyword = concept.get('keyword', '')
        
        # Prüfe alle Text-Felder
        for field in ['text', 'definitionText', 'functionText', 'interactionText', 'specialText']:
            # Hauptebene
            text = concept.get(field, '')
            if text:
                for match in ga210_ref_pattern.finditer(text):
                    lecture_num = match.group(1)
                    old_id = match.group(2)
                    key = (lecture_num, old_id)
                    
                    # Extrahiere Kontext vor der Referenz
                    context = extract_context_around_ref(text, match.group(0))
                    if context and len(context) > 20:
                        if key not in quotes:
                            quotes[key] = []
                        quotes[key].append({
                            'context': context,
                            'concept': keyword,
                            'field': field
                        })
            
            # Overview-Ebene
            overview = concept.get('overview', {})
            if isinstance(overview, dict):
                text = overview.get(field, '')
                if text:
                    for match in ga210_ref_pattern.finditer(text):
                        lecture_num = match.group(1)
                        old_id = match.group(2)
                        key = (lecture_num, old_id)
                        
                        context = extract_context_around_ref(text, match.group(0))
                        if context and len(context) > 20:
                            if key not in quotes:
                                quotes[key] = []
                            quotes[key].append({
                                'context': context,
                                'concept': keyword,
                                'field': f'overview.{field}'
                            })
    
    return quotes

def build_new_paragraph_index(lectures_json):
    """Baut einen Index der neuen Paragraphen"""
    new_paragraphs = {}
    
    for lecture in lectures_json.get('lectures', []):
        lecture_id = lecture.get('ID', '')
        match = re.match(r'GA210/(\d+)', lecture_id, re.IGNORECASE)
        if not match:
            continue
        
        lecture_num = match.group(1)
        paragraphs = lecture.get('paragraphs', [])
        
        new_paragraphs[lecture_num] = []
        for i, para in enumerate(paragraphs):
            new_id = para.get('index', '').lstrip('^')
            text = para.get('content', '')
            if new_id and text:
                new_paragraphs[lecture_num].append((new_id, text, i))
    
    return new_paragraphs

def main():
    print("=" * 70)
    print("  GA210 CONCEPT-IDs WIEDERHERSTELLEN (v2 - Textsuche)")
    print("=" * 70)
    
    # Lade Dateien
    print("\n[1/4] Lade Dateien...")
    concepts_backup = load_json(PROJECT_ROOT / '_backups/concepts-database_20260203_103725.json')
    new_lectures = load_json(PROJECT_ROOT / 'steiner-full-lectures/steiner-full-lectures-210-210.json')
    
    # Extrahiere Zitate
    print("\n[2/4] Extrahiere Zitate aus Concepts...")
    quotes = extract_quotes_from_concepts(concepts_backup)
    print(f"  Gefunden: {len(quotes)} IDs mit Zitat-Kontexten")
    
    # Baue Paragraph-Index
    print("\n[3/4] Baue Paragraph-Index...")
    new_paragraphs = build_new_paragraph_index(new_lectures)
    total_paras = sum(len(p) for p in new_paragraphs.values())
    print(f"  Neue Paragraphen: {total_paras}")
    
    # Suche Matches
    print("\n[4/4] Suche Matches durch Textvergleich...")
    mappings = {}
    no_match = []
    
    for (lecture_num, old_id), quote_list in quotes.items():
        if lecture_num not in new_paragraphs:
            no_match.append((lecture_num, old_id, "Vortrag nicht gefunden"))
            continue
        
        paras = new_paragraphs[lecture_num]
        best_overall = None
        
        for quote_info in quote_list:
            context = quote_info['context']
            result = find_paragraph_by_text(context, paras)
            
            if result:
                new_id, score, method = result
                if best_overall is None or score > best_overall[1]:
                    best_overall = (new_id, score, method, context[:50])
        
        if best_overall and best_overall[1] >= 0.5:
            mappings[(lecture_num, old_id)] = best_overall
            print(f"  GA210/{lecture_num}:^{old_id} -> ^{best_overall[0]} ({best_overall[2]}, {best_overall[1]:.0%})")
        else:
            no_match.append((lecture_num, old_id, quote_list[0]['context'][:40] if quote_list else ""))
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("  ERGEBNIS")
    print("=" * 70)
    print(f"\n  IDs mit Zitaten: {len(quotes)}")
    print(f"  Erfolgreich gemappt: {len(mappings)}")
    print(f"  Nicht gefunden: {len(no_match)}")
    
    if mappings:
        print(f"\n  Match-Rate: {len(mappings)/len(quotes)*100:.1f}%")
        print("\n  Alle Mappings:")
        for (lecture_num, old_id), (new_id, score, method, ctx) in sorted(mappings.items()):
            print(f"    GA210/{lecture_num}: ^{old_id} -> ^{new_id} ({score:.0%})")
    
    if no_match:
        print(f"\n  Nicht gefundene IDs ({len(no_match)}):")
        for lecture_num, old_id, reason in no_match[:5]:
            print(f"    GA210/{lecture_num}:^{old_id}")
            print(f"      Kontext: {reason[:60]}...")
    
    return mappings, no_match

if __name__ == '__main__':
    main()
