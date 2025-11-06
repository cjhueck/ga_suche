# -*- coding: utf-8 -*-
"""
Verarbeite GA-Bände in einem Bereich (z.B. GA224 bis GA292)
"""
import sys
from ga_pdf_final import process_ga_pdf

def process_range(start, end, indizes=False):
    """Verarbeite GA-Bände von start bis end"""
    erfolg = []
    fehler = []
    
    for ga_num in range(start, end + 1):
        ga_str = str(ga_num)
        print(f"\n\n{'='*80}")
        print(f"Verarbeite GA {ga_str} ({ga_num - start + 1}/{end - start + 1})")
        print(f"{'='*80}\n")
        
        try:
            files = process_ga_pdf(ga_str, indizes_hinzufuegen=indizes)
            if files:
                erfolg.append(ga_str)
                print(f"\n✓ GA {ga_str} erfolgreich verarbeitet")
            else:
                fehler.append((ga_str, "Keine Dateien erstellt"))
                print(f"\n✗ GA {ga_str} fehlgeschlagen (keine Dateien erstellt)")
        except Exception as e:
            fehler.append((ga_str, str(e)))
            print(f"\n✗ GA {ga_str} fehlgeschlagen: {e}")
    
    # Zusammenfassung
    print("\n\n" + "="*80)
    print("ZUSAMMENFASSUNG")
    print("="*80)
    print(f"\nErfolgreich verarbeitet: {len(erfolg)}")
    for ga in erfolg:
        print(f"  ✓ GA {ga}")
    
    if fehler:
        print(f"\nFehler: {len(fehler)}")
        for ga, err in fehler:
            print(f"  ✗ GA {ga}: {err}")
    
    print("\n" + "="*80)
    return erfolg, fehler


def main():
    if len(sys.argv) < 3:
        print("Verwendung: python process_ga_range.py <Start-GA> <End-GA> [--indizes]")
        print("Beispiel: python process_ga_range.py 224 292")
        print("  --indizes: Füge Obsidian-Indizes zu Absätzen hinzu")
        return
    
    try:
        start = int(sys.argv[1])
        end = int(sys.argv[2])
        indizes = '--indizes' in sys.argv or '-i' in sys.argv
        
        if start > end:
            print("Fehler: Start-GA muss kleiner oder gleich End-GA sein")
            return
        
        print(f"\nVerarbeite GA {start} bis GA {end}")
        if indizes:
            print("Mit Obsidian-Indizes")
        print("\n")
        
        process_range(start, end, indizes)
        
    except ValueError:
        print("Fehler: Start und End müssen Zahlen sein")


if __name__ == "__main__":
    main()

