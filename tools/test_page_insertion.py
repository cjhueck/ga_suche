#!/usr/bin/env python3
"""
Test-Skript für die automatische Seitenzahlen-Einfügung.

Dieses Skript kann verwendet werden, um die Funktionalität zu testen,
ohne sofort die vollständige Verarbeitung durchzuführen.
"""

import os
import sys
from auto_insert_page_numbers import PageNumberInserter

def test_extraction():
    """Testet die Extraktion von Seitenzahlen aus OCR-Datei."""
    print("=== Test: Seitenzahlen-Extraktion ===")
    
    ocr_file = "GA008-Das Christentum als mystische Tatsache und die Mysterien des Altertums/Steiner, Rudolf GA 008, 1989 - Das Christentum als mystische Tatsache.md"
    
    if not os.path.exists(ocr_file):
        print(f"Datei nicht gefunden: {ocr_file}")
        return
    
    inserter = PageNumberInserter(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    page_markers = inserter.extract_page_numbers_from_ocr(ocr_file)
    print(f"\nGefundene Seitenmarker: {len(page_markers)}")
    
    # Zeige erste 10 Marker
    print("\nErste 10 Marker:")
    for line_idx, page_num in page_markers[:10]:
        print(f"  Zeile {line_idx}: Seite {page_num}")
    
    # Teste Extrapolation
    with open(ocr_file, 'r', encoding='utf-8') as f:
        total_lines = len(f.readlines())
    
    page_map = inserter.extrapolate_missing_pages(page_markers, total_lines)
    print(f"\nExtrapolierte Seitenzahlen: {len(page_map)}")
    
    # Zeige einige extrapolierte Seitenzahlen
    print("\nBeispiel extrapolierte Seitenzahlen:")
    sorted_pages = sorted(set(page_map.values()))[:10]
    for page_num in sorted_pages:
        lines_with_page = [line_idx for line_idx, p in page_map.items() if p == page_num]
        print(f"  Seite {page_num}: {len(lines_with_page)} Zeilen")


def test_with_sample():
    """Testet die Verarbeitung mit einer begrenzten Anzahl von Seiten."""
    print("\n=== Test: Verarbeitung mit Sample ===")
    
    ocr_file = "GA008-Das Christentum als mystische Tatsache und die Mysterien des Altertums/Steiner, Rudolf GA 008, 1989 - Das Christentum als mystische Tatsache.md"
    target_file = "GA008-Das Christentum als mystische Tatsache und die Mysterien des Altertums/GA008 - Das Christentum als mystische Tatsache und die Mysterien des Altertums (1902).md"
    output_file = "GA008-Das Christentum als mystische Tatsache und die Mysterien des Altertums/GA008_TEST_OUTPUT.md"
    
    if not os.path.exists(ocr_file):
        print(f"OCR-Datei nicht gefunden: {ocr_file}")
        return
    
    if not os.path.exists(target_file):
        print(f"Ziel-Datei nicht gefunden: {target_file}")
        return
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Fehler: ANTHROPIC_API_KEY nicht gesetzt!")
        print("Bitte setzen Sie die Umgebungsvariable oder übergeben Sie den API-Key.")
        return
    
    try:
        inserter = PageNumberInserter(api_key=api_key)
        
        # Teste mit nur 3 Seiten
        print("Verarbeite mit max. 3 Seiten (Test)...")
        inserter.process_files(
            ocr_file,
            target_file,
            output_file,
            max_pages=3
        )
        
        print(f"\nTest erfolgreich! Ausgabe gespeichert in: {output_file}")
        print("Bitte überprüfen Sie die Ausgabedatei, um zu sehen, ob die Seitenzahlen korrekt eingefügt wurden.")
        
    except Exception as e:
        print(f"Fehler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "full":
        test_with_sample()
    else:
        test_extraction()
        print("\n" + "="*50)
        print("Hinweis: Um die vollständige Verarbeitung zu testen, führen Sie aus:")
        print("  python test_page_insertion.py full")
        print("\nStellen Sie sicher, dass ANTHROPIC_API_KEY gesetzt ist!")

