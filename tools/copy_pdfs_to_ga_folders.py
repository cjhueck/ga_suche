#!/usr/bin/env python3
"""
PDF-Kopierskript für GA-Bände

Kopiert PDF-Dateien aus dem PDF-Verzeichnis in die entsprechenden GA-Ordner
in Obsidian, damit sie dort mit dem "Marker PDF to MD" Plugin konvertiert
werden können.

Die resultierenden MD-Dateien enthalten Copyright-Zeilen mit Seitenzahlen,
die als Seitenumbruch-Marker verwendet werden können:
  "Copyright Rudolf Steiner Nachlass-Verwaltung Buch: 94 Seite: 24"

Usage:
    python copy_pdfs_to_ga_folders.py [--dry-run] [--ga GA_NUMBER]
    
    --dry-run: Zeigt nur an, was kopiert würde (ohne tatsächlich zu kopieren)
    --ga: Nur bestimmte GA-Nummer(n) verarbeiten (z.B. --ga 093 oder --ga 093,094,095)
"""

import os
import re
import shutil
import argparse
from pathlib import Path
from typing import Optional, List, Tuple

# Pfade
PDF_DIR = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf')
GA_DIR = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA')


def extract_ga_number(pdf_name: str) -> Optional[str]:
    """
    Extrahiert GA-Nummer aus PDF-Dateiname.
    
    Beispiele:
        "Steiner, Rudolf GA 093, 1991 - Die Tempellegende.pdf" -> "093"
        "Steiner, Rudolf GA 093a, 1987 - Grundelemente.pdf" -> "093a"
    """
    match = re.search(r'GA\s*(\d+[a-z]?)', pdf_name, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None


def find_ga_folder(ga_num: str, ga_folders: List[str]) -> Optional[str]:
    """
    Findet den passenden GA-Ordner für eine GA-Nummer.
    
    Suffix-Varianten (z.B. 004a, 040a, 041b) haben eigene Ordner!
    Unterstützt verschiedene Ordner-Formate:
      - GA093-Titel
      - GA093 Titel (mit Leerzeichen)
    """
    ga_num_upper = ga_num.upper()
    
    for folder in ga_folders:
        folder_upper = folder.upper()
        # Format: GA093- oder GA093 (mit Bindestrich oder Leerzeichen)
        if folder_upper.startswith('GA' + ga_num_upper + '-'):
            return folder
        if folder_upper.startswith('GA' + ga_num_upper + ' '):
            return folder
    
    return None


def get_all_ga_folders() -> List[str]:
    """Lädt alle GA-Ordner aus dem Steiner_GA Verzeichnis."""
    return [d for d in os.listdir(GA_DIR) 
            if d.startswith('GA') and os.path.isdir(GA_DIR / d)]


def get_all_pdfs() -> List[str]:
    """Lädt alle PDF-Dateien aus dem PDF-Verzeichnis."""
    return sorted([f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')])


def check_existing_files(target_folder: Path, pdf_name: str) -> Tuple[bool, bool]:
    """
    Prüft ob PDF und/oder MD bereits im Zielordner existieren.
    
    Returns:
        (pdf_exists, md_exists)
    """
    pdf_exists = (target_folder / pdf_name).exists()
    md_name = pdf_name.replace('.pdf', '.md')
    md_exists = (target_folder / md_name).exists()
    return pdf_exists, md_exists


def copy_pdf(pdf_name: str, target_folder: Path, dry_run: bool = False) -> bool:
    """
    Kopiert eine PDF-Datei in den Zielordner.
    
    Returns:
        True wenn erfolgreich oder dry_run
    """
    source = PDF_DIR / pdf_name
    target = target_folder / pdf_name
    
    if dry_run:
        print(f"  [DRY-RUN] Würde kopieren: {pdf_name}")
        return True
    
    try:
        shutil.copy2(source, target)
        print(f"  [KOPIERT] {pdf_name}")
        return True
    except Exception as e:
        print(f"  [FEHLER] {pdf_name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Kopiert GA-PDFs in Obsidian-Ordner')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Zeigt nur an, was kopiert würde')
    parser.add_argument('--ga', type=str, 
                        help='Nur bestimmte GA-Nummer(n), z.B. 093 oder 093,094,095')
    parser.add_argument('--overwrite', action='store_true',
                        help='Überschreibt existierende PDFs')
    parser.add_argument('--skip-with-md', action='store_true',
                        help='Überspringt PDFs, für die bereits eine MD existiert')
    args = parser.parse_args()
    
    # Filter für bestimmte GA-Nummern
    filter_gas = None
    if args.ga:
        filter_gas = [g.strip().lower() for g in args.ga.split(',')]
    
    # Lade Daten
    ga_folders = get_all_ga_folders()
    pdfs = get_all_pdfs()
    
    print(f"PDF-Dateien gefunden: {len(pdfs)}")
    print(f"GA-Ordner gefunden: {len(ga_folders)}")
    print()
    
    if args.dry_run:
        print("*** DRY-RUN MODUS - Es wird nichts kopiert ***")
        print()
    
    # Statistik
    stats = {
        'kopiert': 0,
        'übersprungen_existiert': 0,
        'übersprungen_md_existiert': 0,
        'nicht_gefunden': 0,
        'fehler': 0
    }
    not_found = []
    
    for pdf in pdfs:
        ga_num = extract_ga_number(pdf)
        
        if not ga_num:
            print(f"[WARNUNG] Keine GA-Nummer gefunden in: {pdf}")
            stats['fehler'] += 1
            continue
        
        # Filter prüfen
        if filter_gas:
            # Prüfe ob ga_num oder die Basis (ohne Suffix) im Filter ist
            base_num = ga_num.rstrip('abcdefghij')
            if ga_num not in filter_gas and base_num not in filter_gas:
                continue
        
        folder_name = find_ga_folder(ga_num, ga_folders)
        
        if not folder_name:
            not_found.append((ga_num, pdf))
            stats['nicht_gefunden'] += 1
            continue
        
        target_folder = GA_DIR / folder_name
        pdf_exists, md_exists = check_existing_files(target_folder, pdf)
        
        # Skip-Logik
        if md_exists and args.skip_with_md:
            print(f"GA{ga_num}: [ÜBERSPRUNGEN] MD existiert bereits")
            stats['übersprungen_md_existiert'] += 1
            continue
        
        if pdf_exists and not args.overwrite:
            print(f"GA{ga_num}: [ÜBERSPRUNGEN] PDF existiert bereits")
            stats['übersprungen_existiert'] += 1
            continue
        
        # Kopieren
        print(f"GA{ga_num}: -> {folder_name[:60]}...")
        if copy_pdf(pdf, target_folder, args.dry_run):
            stats['kopiert'] += 1
        else:
            stats['fehler'] += 1
    
    # Zusammenfassung
    print()
    print("=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"Kopiert:                    {stats['kopiert']}")
    print(f"Übersprungen (PDF existiert): {stats['übersprungen_existiert']}")
    print(f"Übersprungen (MD existiert):  {stats['übersprungen_md_existiert']}")
    print(f"Kein GA-Ordner gefunden:    {stats['nicht_gefunden']}")
    print(f"Fehler:                     {stats['fehler']}")
    
    if not_found:
        print()
        print(f"PDFs ohne passenden GA-Ordner ({len(not_found)}):")
        for ga, pdf in not_found[:20]:
            print(f"  GA{ga}: {pdf[:60]}...")
        if len(not_found) > 20:
            print(f"  ... und {len(not_found) - 20} weitere")


if __name__ == '__main__':
    main()

