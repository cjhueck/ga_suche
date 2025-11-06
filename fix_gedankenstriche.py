# -*- coding: utf-8 -*-
"""
Ersetzt lange Gedankenstriche (—) durch kurze (-) und kk durch ck in allen Steiner_GA Markdown-Dateien
"""
import os
import sys
import re
from pathlib import Path

# Setze UTF-8 für Console-Output
sys.stdout = sys.__stdout__
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

STEINER_GA_DIR = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA'

def fix_text_in_file(filepath):
    """Ersetzt lange Gedankenstriche und kk durch ck in einer Datei"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Zähle Gedankenstriche
        num_dashes = content.count('—')
        
        # Ersetze Gedankenstriche
        content = content.replace('—', '-')
        
        # Zähle kk-Vorkommen (nur in Wörtern, nicht in URLs oder Code)
        # Pattern: kk innerhalb von Wörtern (mit Buchstaben davor und danach)
        kk_pattern = r'\b(\w*?)kk(\w*?)\b'
        kk_matches = re.findall(kk_pattern, content, re.IGNORECASE)
        
        # Filtere nur deutsche Wörter (heuristisch: mindestens 5 Zeichen gesamt)
        kk_words_before = []
        for match in kk_matches:
            word = match[0] + 'kk' + match[1]
            if len(word) >= 5:  # Nur längere Wörter
                kk_words_before.append(word)
        
        num_kk = len(kk_words_before)
        
        # Ersetze kk durch ck (case-sensitive)
        # Nur in deutschen Wörtern, nicht in URLs, nicht am Wortanfang
        def replace_kk(match):
            before = match.group(1)
            after = match.group(2)
            word = before + 'kk' + after
            
            # Überspringe wenn:
            # - Zu kurz (< 5 Zeichen)
            # - Enthält Sonderzeichen (URL, etc.)
            # - kk am Anfang des Wortes
            if len(word) < 5 or not before or any(c in word for c in ['/', ':', '.', '@', '_']):
                return match.group(0)
            
            # Ersetze kk durch ck
            return before + 'ck' + after
        
        content = re.sub(kk_pattern, replace_kk, content)
        
        # Nur speichern wenn Änderungen vorgenommen wurden
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return num_dashes, num_kk
        
        return 0, 0
        
    except Exception as e:
        print(f"  [X] Fehler bei {filepath}: {e}")
        return 0, 0

def main():
    print("=" * 80)
    print("Ersetze Gedankenstriche (— -> -) und kk -> ck in Steiner_GA")
    print("=" * 80)
    print()
    
    if not os.path.exists(STEINER_GA_DIR):
        print(f"[X] Fehler: Steiner_GA-Ordner nicht gefunden: {STEINER_GA_DIR}")
        return
    
    total_files = 0
    total_dashes = 0
    total_kk = 0
    folders_processed = 0
    
    # Durchlaufe alle GA-Ordner
    for folder_name in sorted(os.listdir(STEINER_GA_DIR)):
        folder_path = os.path.join(STEINER_GA_DIR, folder_name)
        
        if not os.path.isdir(folder_path):
            continue
        
        # Finde alle Markdown-Dateien
        md_files = [f for f in os.listdir(folder_path) if f.endswith('.md')]
        
        if not md_files:
            continue
        
        folder_had_changes = False
        folder_dashes = 0
        folder_kk = 0
        folder_files = 0
        
        for md_file in md_files:
            md_path = os.path.join(folder_path, md_file)
            num_dashes, num_kk = fix_text_in_file(md_path)
            
            if num_dashes > 0 or num_kk > 0:
                if not folder_had_changes:
                    print(f"\n{folder_name}:")
                    folder_had_changes = True
                
                changes_str = []
                if num_dashes > 0:
                    changes_str.append(f"{num_dashes} Gedankenstrich(e)")
                if num_kk > 0:
                    changes_str.append(f"{num_kk} kk->ck")
                
                print(f"  [OK] {md_file}: {', '.join(changes_str)}")
                folder_dashes += num_dashes
                folder_kk += num_kk
                folder_files += 1
        
        if folder_had_changes:
            folders_processed += 1
            total_files += folder_files
            total_dashes += folder_dashes
            total_kk += folder_kk
    
    print()
    print("=" * 80)
    print(f"Zusammenfassung:")
    print(f"  Ordner verarbeitet: {folders_processed}")
    print(f"  Dateien geaendert: {total_files}")
    print(f"  Gedankenstriche ersetzt: {total_dashes}")
    print(f"  kk->ck ersetzt: {total_kk}")
    print("=" * 80)
    
    if total_dashes > 0 or total_kk > 0:
        print("\n[OK] Fertig! Alle Ersetzungen wurden durchgefuehrt.")
    else:
        print("\n[OK] Keine Ersetzungen notwendig.")

if __name__ == "__main__":
    main()

