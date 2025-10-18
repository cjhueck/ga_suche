"""
Test der Kontext-basierten Relevanz-Bewertung
Vergleicht automatische Scores mit Nutzer-Bewertungen
"""

import json
import glob

# Bewertungen vom Nutzer
ratings = {
    "GA073/3": "hoch",
    "GA072/5": "hoch",
    "GA073a/2": "hoch",
    "GA074/3": "hoch",
    "GA220/3": "hoch",
    "GA080b/11": "hoch",
    "GA300a/17": "mittel",
    "GA065/2": "mittel",
    "GA072/2": "mittel",
    "GA077b/10": "mittel",
    "GA080b/1": "mittel",
    "GA076/7": "mittel",
}

# Lade Kontext-Index
with open('context-index-goetheanismus.json', 'r', encoding='utf-8') as f:
    context_index = json.load(f)

top_context_terms = dict(list(context_index['context_terms'].items())[:50])
print(f"Geladen: {len(top_context_terms)} Top-Kontextwörter")

# Analysiere Vorträge
results = []

for file_path in glob.glob("steiner-full-lectures-*.json"):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        lectures = data.get('lectures', [])
        
        for lecture in lectures:
            lecture_id = lecture.get('ID', '')
            
            if lecture_id in ratings:
                paragraphs = lecture.get('paragraphs', [])
                full_text = ' '.join([p.get('content', '') or p.get('text', '') 
                                     for p in paragraphs])
                full_text_lower = full_text.lower()
                
                # Zähle Goetheanismus-Vorkommen
                goetheanismus_count = full_text_lower.count('goetheanismus')
                
                # Zähle Kontextwort-Matches
                context_matches = 0
                for term in top_context_terms.keys():
                    if term.lower() in full_text_lower:
                        context_matches += 1
                
                context_ratio = context_matches / len(top_context_terms)
                
                results.append({
                    'id': lecture_id,
                    'rating': ratings[lecture_id],
                    'goetheanismus': goetheanismus_count,
                    'context_matches': context_matches,
                    'context_ratio': context_ratio
                })

# Sortiere nach Bewertung
results.sort(key=lambda x: (
    {'hoch': 0, 'mittel': 1, 'niedrig': 2}[x['rating']], 
    -x['context_ratio']
))

print("\n" + "="*80)
print("KONTEXT-RELEVANZ TEST")
print("="*80)

for rating in ['hoch', 'mittel']:
    rated = [r for r in results if r['rating'] == rating]
    if rated:
        print(f"\n{rating.upper()}:")
        print("-"*80)
        for r in rated:
            print(f"{r['id']:15s} | Goethe.: {r['goetheanismus']:2d} | "
                  f"Context: {r['context_matches']:2d}/{len(top_context_terms)} ({r['context_ratio']:.1%})")

print("\n" + "="*80)
print("STATISTIK:")
print("="*80)

for rating in ['hoch', 'mittel']:
    rated = [r for r in results if r['rating'] == rating]
    if rated:
        avg_matches = sum(r['context_matches'] for r in rated) / len(rated)
        avg_ratio = sum(r['context_ratio'] for r in rated) / len(rated)
        print(f"{rating:10s}: Ø {avg_matches:.1f} Matches ({avg_ratio:.1%} der Top-50)")

print("\n" + "="*80)
print("EMPFEHLUNG:")
print("="*80)

hoch_avg = sum(r['context_ratio'] for r in results if r['rating'] == 'hoch') / len([r for r in results if r['rating'] == 'hoch'])
mittel_avg = sum(r['context_ratio'] for r in results if r['rating'] == 'mittel') / len([r for r in results if r['rating'] == 'mittel'])

threshold_high = (hoch_avg + mittel_avg) / 2

print(f"Durchschnitt 'hoch':   {hoch_avg:.1%}")
print(f"Durchschnitt 'mittel': {mittel_avg:.1%}")
print(f"Empfohlene Schwelle für 'hoch': {threshold_high:.1%} Context-Match-Ratio")

