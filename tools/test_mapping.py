#!/usr/bin/env python3
"""Test-Script für PDF -> GA-Ordner Mapping"""

import os
import re

pdf_dir = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA_pdf'
ga_dir = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'

def extract_ga_number(pdf_name):
    """Extrahiert GA-Nummer aus PDF-Dateiname"""
    match = re.search(r'GA\s*(\d+[a-z]?)', pdf_name, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None

def find_ga_folder(ga_num, ga_folders):
    """Findet passenden GA-Ordner für eine GA-Nummer"""
    ga_num_upper = ga_num.upper()
    for folder in ga_folders:
        # Pattern: GA093- oder GA093a-
        if folder.upper().startswith('GA' + ga_num_upper + '-'):
            return folder
    return None

def main():
    ga_folders = [d for d in os.listdir(ga_dir) 
                  if d.startswith('GA') and os.path.isdir(os.path.join(ga_dir, d))]
    pdfs = sorted([f for f in os.listdir(pdf_dir) if f.endswith('.pdf')])
    
    print(f'PDFs gefunden: {len(pdfs)}')
    print(f'GA-Ordner gefunden: {len(ga_folders)}')
    print()
    print('Mapping-Test (erste 30):')
    print('=' * 100)
    
    found = 0
    not_found = []
    
    for pdf in pdfs[:30]:
        ga_num = extract_ga_number(pdf)
        folder = find_ga_folder(ga_num, ga_folders) if ga_num else None
        
        if folder:
            found += 1
            status = 'OK'
        else:
            status = 'NICHT GEFUNDEN'
            not_found.append((ga_num, pdf))
        
        ga_str = ga_num if ga_num else '???'
        folder_str = folder[:55] + '...' if folder and len(folder) > 55 else (folder if folder else '---')
        print(f'{ga_str:6s} -> {folder_str:60s} [{status}]')
    
    print()
    print(f'Gefunden: {found}/30')
    
    if not_found:
        print(f'\nNicht gefunden ({len(not_found)}):')
        for ga, pdf in not_found:
            print(f'  GA{ga}: {pdf[:60]}...')

if __name__ == '__main__':
    main()

