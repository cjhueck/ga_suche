#!/usr/bin/env python3
"""
Löscht JPEG-Dateien in Steiner_GA/assets die bereits zu PNG konvertiert wurden
================================================================================
Prüft für jede .jpg/.jpeg Datei ob eine .png Version mit gleichem Namen existiert.
Nur dann wird die JPEG gelöscht.

Verwendung:
    python cleanup_converted_jpegs.py           # Dry-Run (nur anzeigen)
    python cleanup_converted_jpegs.py --delete  # Tatsächlich löschen
"""

import os
import sys

def cleanup_converted_jpegs(steiner_ga_dir, actually_delete=False):
    """
    Löscht JPEG-Dateien die bereits zu PNG konvertiert wurden
    """
    print("=" * 70)
    print("CLEANUP: Konvertierte JPEG-Dateien")
    print("=" * 70)
    print(f"Verzeichnis: {steiner_ga_dir}")
    print(f"Modus: {'LÖSCHEN' if actually_delete else 'DRY-RUN (nur anzeigen)'}")
    print("=" * 70 + "\n")
    
    if not os.path.exists(steiner_ga_dir):
        print(f"Fehler: Ordner nicht gefunden: {steiner_ga_dir}")
        return
    
    total_jpegs_found = 0
    total_jpegs_with_png = 0
    total_jpegs_deleted = 0
    total_size_freed = 0
    
    # Durchsuche alle GA-Ordner
    for ga_folder_name in sorted(os.listdir(steiner_ga_dir)):
        ga_folder_path = os.path.join(steiner_ga_dir, ga_folder_name)
        
        if not os.path.isdir(ga_folder_path):
            continue
        
        if not ga_folder_name.startswith('GA'):
            continue
        
        # Prüfe assets-Ordner
        assets_path = os.path.join(ga_folder_path, 'assets')
        
        if not os.path.exists(assets_path):
            continue
        
        # Finde alle JPEG-Dateien
        jpegs_in_folder = []
        
        for filename in os.listdir(assets_path):
            if filename.lower().endswith(('.jpg', '.jpeg')):
                jpegs_in_folder.append(filename)
        
        if not jpegs_in_folder:
            continue
        
        # Prüfe jede JPEG-Datei
        jpegs_to_delete = []
        
        for jpeg_filename in jpegs_in_folder:
            total_jpegs_found += 1
            
            jpeg_path = os.path.join(assets_path, jpeg_filename)
            
            # Erstelle PNG-Dateiname
            base_name = os.path.splitext(jpeg_filename)[0]
            png_filename = base_name + '.png'
            png_path = os.path.join(assets_path, png_filename)
            
            # Prüfe ob PNG existiert
            if os.path.exists(png_path):
                total_jpegs_with_png += 1
                jpeg_size = os.path.getsize(jpeg_path)
                jpegs_to_delete.append((jpeg_filename, jpeg_size))
        
        # Zeige Ergebnisse für diesen Ordner
        if jpegs_to_delete:
            print(f"\n{ga_folder_name}:")
            print(f"  JPEG-Dateien: {len(jpegs_in_folder)}")
            print(f"  Davon konvertiert (PNG vorhanden): {len(jpegs_to_delete)}")
            
            if actually_delete:
                # Lösche JPEGs
                for jpeg_filename, jpeg_size in jpegs_to_delete:
                    jpeg_path = os.path.join(assets_path, jpeg_filename)
                    try:
                        os.remove(jpeg_path)
                        total_jpegs_deleted += 1
                        total_size_freed += jpeg_size
                        print(f"    ✓ Gelöscht: {jpeg_filename} ({jpeg_size/1024:.1f} KB)")
                    except Exception as e:
                        print(f"    ✗ Fehler bei {jpeg_filename}: {e}")
            else:
                # Nur anzeigen
                folder_size = sum(size for _, size in jpegs_to_delete)
                print(f"  Würde löschen: {len(jpegs_to_delete)} Dateien ({folder_size/1024/1024:.2f} MB)")
                for jpeg_filename, jpeg_size in jpegs_to_delete[:3]:  # Zeige nur erste 3
                    print(f"    - {jpeg_filename} ({jpeg_size/1024:.1f} KB)")
                if len(jpegs_to_delete) > 3:
                    print(f"    ... und {len(jpegs_to_delete) - 3} weitere")
    
    # Zusammenfassung
    print(f"\n{'='*70}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*70}")
    print(f"  JPEG-Dateien gefunden: {total_jpegs_found}")
    print(f"  Davon mit PNG-Version: {total_jpegs_with_png}")
    
    if actually_delete:
        print(f"  Gelöscht: {total_jpegs_deleted}")
        print(f"  Speicherplatz freigegeben: {total_size_freed/1024/1024:.2f} MB")
    else:
        estimated_size = sum(size for _, size in 
                           [(f, os.path.getsize(os.path.join(steiner_ga_dir, ga, 'assets', f))) 
                            for ga in os.listdir(steiner_ga_dir) 
                            if os.path.isdir(os.path.join(steiner_ga_dir, ga)) and ga.startswith('GA')
                            for assets in [os.path.join(steiner_ga_dir, ga, 'assets')]
                            if os.path.exists(assets)
                            for f in os.listdir(assets)
                            if f.lower().endswith(('.jpg', '.jpeg')) and 
                               os.path.exists(os.path.join(assets, os.path.splitext(f)[0] + '.png'))]) if total_jpegs_with_png > 0 else 0
        
        print(f"  Kann gelöscht werden: ~{total_jpegs_with_png} Dateien")
        print(f"\n  Führen Sie mit --delete aus, um zu löschen:")
        print(f"    python cleanup_converted_jpegs.py --delete")
    
    print(f"{'='*70}\n")

if __name__ == "__main__":
    steiner_ga_dir = r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA"
    
    actually_delete = '--delete' in sys.argv or '-d' in sys.argv
    
    cleanup_converted_jpegs(steiner_ga_dir, actually_delete)

