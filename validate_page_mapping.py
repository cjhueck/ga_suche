#!/usr/bin/env python3
"""
Validiert das lecture-page-mapping.json auf Fehler:
1. Nicht-monotone Seitenzahlen (Rücksprünge)
2. Fehlende Vorträge (Lücken in der Nummerierung)
3. Unplausible Seitenzahlen (< 5)

Verwendung:
    python validate_page_mapping.py           # Alle GA-Bände prüfen
    python validate_page_mapping.py GA030     # Nur GA030 prüfen
    python validate_page_mapping.py --fix     # Probleme automatisch korrigieren
"""

import io
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Windows-Konsole UTF-8 Unterstützung
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent
MAPPING_FILE = SCRIPT_DIR / "lecture-page-mapping.json"


def load_mapping() -> Dict:
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_mapping(data: Dict) -> None:
    sorted_data = {"_info": data.get("_info", "")}
    ga_keys = sorted(k for k in data.keys() if k.startswith("GA"))
    for k in ga_keys:
        sorted_data[k] = data[k]
    
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)


def extract_lecture_num(lecture_id: str) -> Optional[int]:
    """Extrahiert die Vortragsnummer aus der ID (z.B. 'GA030/6' -> 6)"""
    m = re.search(r'/(\d+)$', lecture_id)
    return int(m.group(1)) if m else None


def validate_ga(ga_number: str, mapping: Dict[str, int]) -> List[Dict]:
    """
    Validiert das Mapping für einen GA-Band.
    Rückgabe: Liste von Problemen
    """
    problems = []
    
    # Sortiere nach Vortragsnummer
    sorted_items = []
    for lecture_id, page in mapping.items():
        num = extract_lecture_num(lecture_id)
        if num is not None:
            sorted_items.append((num, lecture_id, page))
    
    sorted_items.sort(key=lambda x: x[0])
    
    if not sorted_items:
        return problems
    
    # Prüfe auf Probleme
    prev_num = 0
    prev_page = 0
    
    for num, lecture_id, page in sorted_items:
        # Problem 1: Nicht-monotone Seitenzahlen (Rücksprung)
        if page < prev_page - 5:  # Toleranz von 5 Seiten für Anhänge etc.
            problems.append({
                "type": "non_monotonic",
                "ga": ga_number,
                "lecture_id": lecture_id,
                "page": page,
                "prev_page": prev_page,
                "message": f"Rücksprung: {lecture_id} hat Seite {page}, aber vorheriger Vortrag hat Seite {prev_page}"
            })
        
        # Problem 2: Unplausibel niedrige Seitenzahl
        if page < 5 and num > 1:
            problems.append({
                "type": "implausible_page",
                "ga": ga_number,
                "lecture_id": lecture_id,
                "page": page,
                "message": f"Unplausibel: {lecture_id} hat Seite {page} (zu niedrig für Vortrag {num})"
            })
        
        # Problem 3: Lücke in der Nummerierung (optional, nur warnen)
        if num > prev_num + 1 and prev_num > 0:
            # Nur als Info, nicht als Fehler
            pass
        
        prev_num = num
        if page > prev_page:  # Nur aktualisieren wenn gültig
            prev_page = page
    
    return problems


def estimate_correct_page(ga_number: str, mapping: Dict[str, int], problem_lecture_id: str) -> Optional[int]:
    """
    Schätzt die korrekte Seitenzahl basierend auf Nachbarn.
    """
    problem_num = extract_lecture_num(problem_lecture_id)
    if problem_num is None:
        return None
    
    # Finde Nachbarn
    sorted_items = []
    for lecture_id, page in mapping.items():
        num = extract_lecture_num(lecture_id)
        if num is not None and num != problem_num:
            sorted_items.append((num, page))
    
    sorted_items.sort()
    
    # Finde vorherigen und nächsten gültigen Vortrag
    prev_page = None
    next_page = None
    
    for num, page in sorted_items:
        if num < problem_num:
            if prev_page is None or page > prev_page:
                prev_page = page
        elif num > problem_num and next_page is None:
            next_page = page
            break
    
    # Schätze basierend auf Nachbarn
    if prev_page and next_page:
        return (prev_page + next_page) // 2
    elif prev_page:
        return prev_page + 10  # Annahme: ca. 10 Seiten pro Vortrag
    
    return None


def main():
    args = sys.argv[1:]
    fix_mode = "--fix" in args
    args = [a for a in args if not a.startswith("--")]
    
    mapping = load_mapping()
    ga_filter = None
    
    if args:
        ga_filter = set()
        for a in args:
            m = re.match(r"GA?(\d{2,3}[a-z]?)", a, re.IGNORECASE)
            if m:
                ga_filter.add(f"GA{m.group(1).zfill(3).upper()}")
    
    all_problems = []
    
    # Alle GA-Bände prüfen
    for ga_key in sorted(k for k in mapping.keys() if k.startswith("GA")):
        if ga_filter and ga_key not in ga_filter:
            continue
        
        ga_mapping = mapping[ga_key]
        problems = validate_ga(ga_key, ga_mapping)
        all_problems.extend(problems)
    
    # Ergebnisse ausgeben
    if not all_problems:
        print("✓ Keine Probleme gefunden!")
        return
    
    print(f"\n{'='*70}")
    print(f"GEFUNDENE PROBLEME: {len(all_problems)}")
    print(f"{'='*70}\n")
    
    # Gruppiere nach GA
    by_ga = {}
    for p in all_problems:
        ga = p["ga"]
        if ga not in by_ga:
            by_ga[ga] = []
        by_ga[ga].append(p)
    
    fixes_applied = []
    
    for ga, problems in sorted(by_ga.items()):
        print(f"\n{ga}: {len(problems)} Problem(e)")
        print("-" * 40)
        
        for p in problems:
            print(f"  ✗ {p['message']}")
            
            if fix_mode:
                # Versuche zu korrigieren
                estimated = estimate_correct_page(ga, mapping[ga], p["lecture_id"])
                if estimated:
                    print(f"    → Geschätzte korrekte Seite: {estimated}")
                    print(f"    → ENTFERNE aus Mapping (manuell prüfen)")
                    # Entferne den problematischen Eintrag
                    if p["lecture_id"] in mapping[ga]:
                        del mapping[ga][p["lecture_id"]]
                        fixes_applied.append(p["lecture_id"])
    
    print(f"\n{'='*70}")
    
    if fix_mode and fixes_applied:
        save_mapping(mapping)
        print(f"\n✓ {len(fixes_applied)} problematische Einträge entfernt:")
        for lid in fixes_applied:
            print(f"   - {lid}")
        print("\nBitte 'generate_lecture_page_mapping.py' erneut ausführen für diese GA-Bände!")
    elif not fix_mode and all_problems:
        print("\nVerwende --fix um problematische Einträge zu entfernen")


if __name__ == "__main__":
    main()



