#!/usr/bin/env python3
"""
Konvertiert GA002 MsN zu MsA mit Seitenmarkern.
Speziell für GA002 angepasst (einzelnes Buch, anderer Dateiname).
"""

import re
import sys
from pathlib import Path
from difflib import SequenceMatcher

# Import convert_msn_to_msa Funktionen
sys.path.insert(0, str(Path(__file__).parent))
from convert_msn_to_msa import convert_msn_pagebreaks, format_pagebreak_markers


def normalize(text: str) -> str:
    """Normalisiere Text für Vergleich."""
    text = text.lower()
    text = text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    text = re.sub(r'[^a-z0-9]', '', text)
    return text


def count_words(text: str) -> int:
    """Zähle Wörter im Text."""
    text = re.sub(r'\^[a-z0-9]+', '', text)
    text = re.sub(r'\|\d+\|', '', text)
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def transfer_block_ids(new_content: str, old_content: str) -> str:
    """Übertrage Block-IDs von altem zu neuem Content."""
    # Extrahiere alle Block-IDs aus altem Content
    old_ids = re.findall(r'\^[a-z0-9]+', old_content)
    
    if not old_ids:
        print("  Keine Block-IDs in MsA gefunden!")
        return new_content
    
    print(f"  {len(old_ids)} Block-IDs in MsA")
    
    # Teile beide Texte in Absätze
    new_paragraphs = re.split(r'\n\n+', new_content)
    old_paragraphs = re.split(r'\n\n+', old_content)
    
    # Erstelle Mapping: alter Absatz -> ID
    old_para_to_id = {}
    for old_para in old_paragraphs:
        old_para = old_para.strip()
        if not old_para:
            continue
        id_match = re.search(r'(\^[a-z0-9]+)\s*$', old_para)
        if id_match:
            block_id = id_match.group(1)
            old_text = old_para[:id_match.start()].strip()
            old_norm = normalize(old_text[:200])  # Nur Anfang vergleichen
            old_para_to_id[old_norm] = block_id
    
    result_paragraphs = []
    used_ids = set()
    matched_count = 0
    
    for new_para in new_paragraphs:
        new_para = new_para.strip()
        if not new_para:
            continue
        
        # Hat der Absatz schon eine ID?
        if re.search(r'\^[a-z0-9]+\s*$', new_para):
            result_paragraphs.append(new_para)
            continue
        
        new_norm = normalize(new_para[:200])
        
        # Finde besten Match
        best_match = None
        best_ratio = 0.6
        
        for old_norm, block_id in old_para_to_id.items():
            if block_id in used_ids:
                continue
            
            ratio = SequenceMatcher(None, new_norm[:100], old_norm[:100]).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = block_id
        
        if best_match:
            new_para = new_para + ' ' + best_match
            used_ids.add(best_match)
            matched_count += 1
        
        result_paragraphs.append(new_para)
    
    print(f"  {matched_count} Block-IDs übertragen")
    
    return '\n\n'.join(result_paragraphs)


def main():
    # Pfade
    base = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA')
    ga_folder = base / 'GA002-Grundlinien einer Erkenntnistheorie der Goetheschen Weltanschauung'
    
    msn_path = ga_folder / 'GA 2 - Grundlinien einer Erkenntnistheorie der Goetheschen Weltanschauung.md'
    msa_path = ga_folder / 'GA002 - Grundlinien einer Erkenntnistheorie der Goetheschen Weltanschauung (1886).md'
    
    print(f"MsN: {msn_path.name}")
    print(f"MsA: {msa_path.name}")
    
    if not msn_path.exists():
        print("MsN-Datei nicht gefunden!")
        sys.exit(1)
    
    if not msa_path.exists():
        print("MsA-Datei nicht gefunden!")
        sys.exit(1)
    
    # Lade Dateien
    msn_content = msn_path.read_text(encoding='utf-8')
    msa_content = msa_path.read_text(encoding='utf-8')
    
    print(f"\nMsN: {len(msn_content)} Zeichen")
    print(f"MsA: {len(msa_content)} Zeichen")
    
    # Konvertiere MsN (Seite X → |X|)
    print("\nKonvertiere Seitenmarker...")
    converted = convert_msn_pagebreaks(msn_content)
    
    # Zähle Marker
    markers = re.findall(r'\|(\d+)\|', converted)
    if markers:
        pages = sorted(set(int(m) for m in markers))
        print(f"  {len(markers)} Marker erstellt")
        print(f"  Seiten: {min(pages)} - {max(pages)}")
    
    # Übertrage Block-IDs
    print("\nÜbertrage Block-IDs...")
    converted = transfer_block_ids(converted, msa_content)
    
    # Wortanzahl-Validierung
    msa_words = count_words(msa_content)
    msn_words = count_words(converted)
    diff_pct = abs(msn_words - msa_words) / msa_words * 100 if msa_words > 0 else 0
    
    print(f"\nWortanzahl:")
    print(f"  MsA: {msa_words}")
    print(f"  MsAN: {msn_words}")
    print(f"  Differenz: {diff_pct:.1f}%")
    
    if diff_pct > 15:
        print(f"\n[!] WARNUNG: Große Differenz! Bitte manuell prüfen.")
    else:
        print(f"\n[OK] Wortanzahl validiert")
    
    # Speichere konvertierte Datei
    output_path = ga_folder / (msa_path.stem + '_new.md')
    output_path.write_text(converted, encoding='utf-8')
    print(f"\nGespeichert: {output_path.name}")
    
    # Zeige Beispiele
    print(f"\nBeispiel (erste 3 Marker):")
    for m in markers[:3]:
        pattern = rf'.{{30}}\|{m}\|.{{30}}'
        match = re.search(pattern, converted)
        if match:
            print(f"  |{m}|: ...{match.group()}...")
    
    print(f"\nNächste Schritte:")
    print(f"1. Prüfe die neue Datei: {output_path.name}")
    print(f"2. Wenn OK, ersetze MsA durch MsAN:")
    print(f"   Remove-Item '{msa_path}'")
    print(f"   Rename-Item '{output_path}' '{msa_path.name}'")
    print(f"3. Exportiere: python export_master.py GA002 --skip-path-fix")


if __name__ == '__main__':
    main()

