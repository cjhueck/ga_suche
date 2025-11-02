#!/usr/bin/env python3
"""
Integrierter Export von Steiner-Bildern
========================================
Führt alle Schritte automatisch aus:
1. Konvertiert JPEGs zu transparenten PNGs
2. Exportiert Bilder aus steiner-full-lectures*.json
3. Erstellt finale steiner-images.json

Verwendung:
    python export_steiner_images_integrated.py
    
Optional mit Parametern:
    python export_steiner_images_integrated.py --skip-conversion  # Überspringe JPEG-Konvertierung
    python export_steiner_images_integrated.py --threshold 250    # Eigener Transparenz-Schwellenwert
"""

import json
import os
import base64
import re
import sys
from pathlib import Path

# Prüfe Pillow-Installation
try:
    from PIL import Image
except ImportError:
    print("\n" + "=" * 60)
    print("FEHLER: Pillow ist nicht installiert!")
    print("=" * 60)
    print("Installieren Sie es mit:")
    print("  pip install Pillow")
    print("=" * 60 + "\n")
    sys.exit(1)


# ============================================================================
# SCHRITT 1: JPEG ZU PNG KONVERTIERUNG
# ============================================================================

def convert_jpeg_to_transparent_png(jpeg_path, png_path, threshold=240):
    """
    Konvertiert JPEG zu PNG mit transparentem Hintergrund.
    
    Args:
        jpeg_path: Pfad zur JPEG-Datei
        png_path: Pfad zur zu erstellenden PNG-Datei
        threshold: RGB-Schwellenwert für Transparenz (Standard: 240)
                   Pixel mit allen RGB-Werten > threshold werden transparent
    """
    try:
        # Öffne JPEG
        img = Image.open(jpeg_path)
        
        # Konvertiere zu RGBA (für Transparenz)
        img = img.convert("RGBA")
        
        # Lade Pixel-Daten
        datas = img.getdata()
        new_data = []
        
        # Mache weiße/helle Bereiche transparent
        for item in datas:
            # Wenn Pixel fast weiß ist (R, G, B alle > threshold)
            if item[0] > threshold and item[1] > threshold and item[2] > threshold:
                # Mache transparent (Alpha = 0)
                new_data.append((255, 255, 255, 0))
            else:
                # Behalte Pixel wie es ist
                new_data.append(item)
        
        # Setze neue Pixel-Daten
        img.putdata(new_data)
        
        # Speichere als PNG
        img.save(png_path, "PNG")
        return True
        
    except Exception as e:
        print(f"  X Fehler: {e}")
        return False


def convert_all_jpegs_in_ga_folders(steiner_ga_dir, threshold=240):
    """
    Durchläuft alle GA-Ordner und konvertiert JPEGs zu PNGs.
    
    Returns:
        tuple: (converted, skipped, errors, folders_processed)
    """
    print("\n" + "=" * 60)
    print("SCHRITT 1: JPEG zu PNG Konvertierung")
    print("=" * 60)
    print(f"Basis-Ordner: {steiner_ga_dir}")
    print(f"Schwellenwert: {threshold} (Pixel > {threshold} werden transparent)\n")
    
    if not os.path.exists(steiner_ga_dir):
        print(f"X Fehler: Ordner nicht gefunden: {steiner_ga_dir}")
        return 0, 0, 0, 0
    
    total_converted = 0
    total_skipped = 0
    total_errors = 0
    folders_processed = 0
    
    # Durchlaufe alle GA-Ordner
    ga_folders = []
    for folder_name in os.listdir(steiner_ga_dir):
        folder_path = os.path.join(steiner_ga_dir, folder_name)
        if os.path.isdir(folder_path) and folder_name.startswith('GA'):
            ga_folders.append((folder_name, folder_path))
    
    ga_folders.sort()
    
    for folder_name, folder_path in ga_folders:
        assets_path = os.path.join(folder_path, 'assets')
        
        if not os.path.exists(assets_path):
            continue
        
        # Finde alle JPEG-Dateien
        jpeg_files = []
        for file_name in os.listdir(assets_path):
            if file_name.lower().endswith(('.jpg', '.jpeg')):
                jpeg_files.append(file_name)
        
        if not jpeg_files:
            continue
        
        print(f"\n{folder_name}:")
        print(f"  Gefunden: {len(jpeg_files)} JPEG-Dateien")
        
        converted = 0
        skipped = 0
        errors = 0
        
        for file_name in jpeg_files:
            jpeg_path = os.path.join(assets_path, file_name)
            
            # Erstelle PNG-Dateiname
            png_name = file_name.rsplit('.', 1)[0] + '.png'
            png_path = os.path.join(assets_path, png_name)
            
            # Überspringe, wenn PNG bereits existiert
            if os.path.exists(png_path):
                skipped += 1
                continue
            
            # Konvertiere
            if convert_jpeg_to_transparent_png(jpeg_path, png_path, threshold):
                converted += 1
            else:
                errors += 1
        
        if converted > 0 or skipped > 0 or errors > 0:
            print(f"  > {converted} konvertiert, {skipped} uebersprungen, {errors} Fehler")
            folders_processed += 1
            total_converted += converted
            total_skipped += skipped
            total_errors += errors
    
    print(f"\n{'='*60}")
    print(f"SCHRITT 1 abgeschlossen:")
    print(f"  GA-Ordner verarbeitet: {folders_processed}")
    print(f"  Bilder konvertiert: {total_converted}")
    print(f"  Bilder uebersprungen (existieren bereits): {total_skipped}")
    print(f"  Fehler: {total_errors}")
    print(f"{'='*60}")
    
    return total_converted, total_skipped, total_errors, folders_processed


# ============================================================================
# SCHRITT 2: EXPORT ZU STEINER-IMAGES.JSON
# ============================================================================

def encode_image_to_base64(image_path):
    """Liest ein Bild und encodiert es als Base64-String."""
    with open(image_path, 'rb') as img_file:
        img_data = img_file.read()
        base64_data = base64.b64encode(img_data).decode('utf-8')
        
        # Bestimme MIME-Type basierend auf Dateiendung
        if image_path.lower().endswith('.png'):
            mime_type = 'image/png'
        elif image_path.lower().endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
        elif image_path.lower().endswith('.webp'):
            mime_type = 'image/webp'
        else:
            mime_type = 'image/png'  # Default
        
        return f"data:{mime_type};base64,{base64_data}", len(img_data)


def extract_images_from_lectures(lectures_files, steiner_ga_dir):
    """
    Durchsucht alle Lecture-Dateien nach Bildreferenzen und erstellt steiner-images.json
    """
    print("\n" + "=" * 60)
    print("SCHRITT 2: Export zu steiner-images.json")
    print("=" * 60)
    
    images_data = {}
    total_found = 0
    total_encoded = 0
    total_not_found = 0
    
    for lecture_file in lectures_files:
        print(f"\n{'='*60}")
        print(f"Verarbeite: {os.path.basename(lecture_file)}")
        print(f"{'='*60}")
        
        with open(lecture_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both formats: direct list or {"lectures": [...]}
        lectures = data.get('lectures', data) if isinstance(data, dict) else data
        
        for lecture in lectures:
            lecture_id = lecture.get('ID')
            if not lecture_id:
                continue
            
            paragraphs = lecture.get('paragraphs', [])
            
            for para in paragraphs:
                content = para.get('content', '')
                para_index = para.get('index', '')
                
                # Sammle alle Bildmarkierungen (beide Formate)
                all_matches = []
                
                # Pattern 1: Standard Markdown ![alt](path)
                markdown_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
                markdown_matches = re.findall(markdown_pattern, content)
                for alt_text, img_path in markdown_matches:
                    # Bereinige doppelte Ordnernamen auch hier
                    # GA118-.../GA118-.../assets/... → assets/...
                    cleaned_img_path = img_path
                    if re.match(r'GA\d{3}[a-z]?-', cleaned_img_path):
                        # Extrahiere nur den Teil nach dem LETZTEN "assets/"
                        assets_match = re.search(r'assets/(.+)$', cleaned_img_path)
                        if assets_match:
                            cleaned_img_path = f'assets/{assets_match.group(1)}'
                    
                    # Speichere auch das Original-Format (Markdown)
                    all_matches.append((alt_text, cleaned_img_path, f'![{alt_text}]({img_path})'))
                
                # Pattern 2: Obsidian Wiki-Links ![[filename]]
                wiki_pattern = r'!\[\[([^\]]+)\]\]'
                wiki_matches = re.findall(wiki_pattern, content)
                for filename in wiki_matches:
                    # Bereinige Pfad - entferne GA-Ordner-Präfix falls vorhanden
                    # ![[GA223-.../assets/223-T01.webp]] → assets/223-T01.webp
                    # ![[GA118-.../GA118-.../assets/...]] → assets/... (doppelte Ordner entfernen)
                    cleaned_path = filename
                    
                    # Entferne GA-Ordner-Präfix (auch doppelte!)
                    # Pattern: GA118-.../GA118-.../assets/... oder GA118-.../assets/...
                    if re.match(r'GA\d{3}[a-z]?-', cleaned_path):
                        # Extrahiere nur den Teil nach dem LETZTEN "assets/"
                        # Dies behandelt sowohl einfache als auch doppelte Ordnernamen
                        assets_match = re.search(r'assets/(.+)$', cleaned_path)
                        if assets_match:
                            cleaned_path = f'assets/{assets_match.group(1)}'
                    
                    # Konvertiere zu assets/filename Format
                    img_path = cleaned_path if cleaned_path.startswith('assets/') else f'assets/{cleaned_path}'
                    
                    # Bereinige Dateinamen: Entferne Leerzeichen und Zahlen-Suffix
                    # "213-T01 3.webp" → "213-T01.webp"
                    img_path = re.sub(r'(\d{3}-T\d{2})\s+\d+\.webp', r'\1.webp', img_path)
                    
                    # Ersetze Unterstrich durch Bindestrich
                    # "221_T01.webp" → "221-T01.webp"
                    img_path = re.sub(r'(\d{3})_T(\d{2})\.webp', r'\1-T\2.webp', img_path)
                    
                    # Alt-Text aus bereinigtem Pfad
                    alt_text = os.path.basename(img_path).replace('.webp', '').replace('.png', '').replace('.jpeg', '').replace('.jpg', '')
                    
                    # Speichere auch das Original-Format (Wiki-Link)
                    all_matches.append((alt_text, img_path, f'![[{filename}]]'))
                
                if all_matches:
                    for match_tuple in all_matches:
                        # Entpacke Match (entweder 2 oder 3 Elemente)
                        if len(match_tuple) == 3:
                            alt_text, img_path, original_ref = match_tuple
                        else:
                            alt_text, img_path = match_tuple
                            original_ref = f'![{alt_text}]({img_path})'
                        
                        total_found += 1
                        
                        # Dekodiere URL-encoding
                        img_path_decoded = img_path.replace('%20', ' ')
                        
                        # Versuche PNG-Version zu finden, falls WebP, dann WebP behalten
                        if img_path_decoded.lower().endswith('.webp'):
                            final_path = img_path_decoded  # WebP bleibt WebP
                        else:
                            final_path = re.sub(r'\.(jpe?g)$', '.png', img_path_decoded, flags=re.IGNORECASE)
                        
                        # Extrahiere GA-Nummer und finde tatsächlichen Ordnernamen
                        ga_number = lecture_id.split('/')[0]
                        
                        # Suche nach dem tatsächlichen Ordner im Steiner_GA-Verzeichnis
                        ga_folder = None
                        for folder_name in os.listdir(steiner_ga_dir):
                            if folder_name.startswith(ga_number + '-'):
                                ga_folder = folder_name
                                break
                        
                        if not ga_folder:
                            # Fallback: verwende gaTitle
                            ga_title = lecture.get('gaTitle', '').split('(')[0].strip()
                            ga_folder = f"{ga_number}-{ga_title}"
                        
                        # Entferne "assets/" aus final_path, falls vorhanden
                        final_filename = final_path.replace('assets/', '')
                        
                        # Konstruiere vollständigen Pfad: Steiner_GA/GA089-Bewusstsein Leben Form/assets/...
                        full_image_path = os.path.join(
                            steiner_ga_dir,
                            ga_folder,
                            'assets',
                            final_filename
                        )
                        
                        # Falls PNG nicht existiert, versuche Alternativen (WebP, JPEG)
                        if not os.path.exists(full_image_path):
                            # Versuche WebP-Version (Tafelzeichnungen)
                            webp_path = re.sub(r'\.(png|jpe?g)$', '.webp', final_path, flags=re.IGNORECASE)
                            webp_filename = webp_path.replace('assets/', '')
                            full_webp_path = os.path.join(
                                steiner_ga_dir,
                                ga_folder,
                                'assets',
                                webp_filename
                            )
                            if os.path.exists(full_webp_path):
                                full_image_path = full_webp_path
                                final_path = webp_path
                            else:
                                # Versuche JPEG-Version (falls noch nicht konvertiert)
                                jpeg_path = re.sub(r'\.png$', '.jpeg', final_path, flags=re.IGNORECASE)
                                jpeg_filename = jpeg_path.replace('assets/', '')
                                full_jpeg_path = os.path.join(
                                    steiner_ga_dir,
                                    ga_folder,
                                    'assets',
                                    jpeg_filename
                                )
                                if os.path.exists(full_jpeg_path):
                                    full_image_path = full_jpeg_path
                                    final_path = jpeg_path
                                else:
                                    # Versuche JPG-Version (alternatives Format)
                                    jpg_path = re.sub(r'\.png$', '.jpg', final_path, flags=re.IGNORECASE)
                                    jpg_filename = jpg_path.replace('assets/', '')
                                    full_jpg_path = os.path.join(
                                        steiner_ga_dir,
                                        ga_folder,
                                        'assets',
                                        jpg_filename
                                    )
                                    if os.path.exists(full_jpg_path):
                                        full_image_path = full_jpg_path
                                        final_path = jpg_path
                        
                        if os.path.exists(full_image_path):
                            print(f"  OK {lecture_id} - {alt_text}")
                            
                            try:
                                # Encodiere Bild
                                base64_str, file_size = encode_image_to_base64(full_image_path)
                                
                                # Erstelle Eintrag
                                # WICHTIG: altText und markdownRef behalten ORIGINAL (aus Text)
                                # path enthält den finalen Pfad (PNG oder WebP)
                                image_entry = {
                                    'index': para_index,
                                    'altText': alt_text,  # Original aus Text
                                    'path': final_path,  # Finaler Pfad (PNG oder WebP)
                                    'markdownRef': original_ref,  # Original-Referenz aus Text (Markdown oder Wiki-Link)!
                                    'base64': base64_str,
                                    'size': file_size
                                }
                                
                                # Füge zu images_data hinzu
                                if lecture_id not in images_data:
                                    images_data[lecture_id] = []
                                
                                images_data[lecture_id].append(image_entry)
                                total_encoded += 1
                                
                            except Exception as e:
                                print(f"  X Fehler beim Encodieren: {e}")
                                total_not_found += 1
                        else:
                            print(f"  X Bild nicht gefunden: {lecture_id} - {final_path}")
                            total_not_found += 1
    
    return images_data, total_found, total_encoded, total_not_found


# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

def main():
    """Hauptfunktion für integrierten Export"""
    
    # Parse Kommandozeilenargumente
    skip_conversion = '--skip-conversion' in sys.argv
    threshold = 240
    
    if '--threshold' in sys.argv:
        try:
            idx = sys.argv.index('--threshold')
            threshold = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Fehler: --threshold benötigt einen numerischen Wert")
            sys.exit(1)
    
    # Pfade
    project_root = os.path.dirname(os.path.abspath(__file__))
    steiner_ga_dir = r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA"
    output_file = os.path.join(project_root, 'steiner-images.json')
    
    # Finde alle lecture-Dateien
    lecture_files = [
        os.path.join(project_root, f'steiner-full-lectures-051-311-part0{i}.json')
        for i in range(1, 8)
    ]
    lecture_files = [f for f in lecture_files if os.path.exists(f)]
    
    print("\n" + "=" * 60)
    print("INTEGRIERTER STEINER IMAGES EXPORT")
    print("=" * 60)
    print(f"Projekt-Ordner: {project_root}")
    print(f"Steiner GA-Ordner: {steiner_ga_dir}")
    print(f"Output: {output_file}")
    print(f"Lecture-Dateien: {len(lecture_files)}")
    print("=" * 60)
    
    # SCHRITT 1: Konvertierung (optional überspringen)
    if not skip_conversion:
        converted, skipped, errors, folders = convert_all_jpegs_in_ga_folders(
            steiner_ga_dir, 
            threshold
        )
        
        if errors > 0:
            print(f"\nWarnung: {errors} Fehler bei der Konvertierung")
            response = input("Möchten Sie trotzdem fortfahren? (j/n): ")
            if response.lower() not in ['j', 'ja', 'y', 'yes']:
                print("Abgebrochen.")
                sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("SCHRITT 1: ÜBERSPRUNGEN (--skip-conversion)")
        print("=" * 60)
    
    # SCHRITT 2: Export
    images_data, total_found, total_encoded, total_not_found = extract_images_from_lectures(
        lecture_files, 
        steiner_ga_dir
    )
    
    # SCHRITT 3: Speichere Ergebnis mit automatischem Splitting
    if images_data:
        from datetime import datetime
        
        # Prüfe Größe der JSON
        test_json = json.dumps(images_data, ensure_ascii=False, indent=2)
        total_size_mb = len(test_json.encode('utf-8')) / (1024 * 1024)
        
        print(f"\nGesamtgroesse: {total_size_mb:.2f} MB")
        
        # Entscheide: Einzeldatei oder Chunks
        MAX_CHUNK_SIZE_MB = 10
        
        if total_size_mb > MAX_CHUNK_SIZE_MB:
            print(f"Datei zu gross (>{MAX_CHUNK_SIZE_MB} MB) - teile in Chunks auf...\n")
            
            # Sortiere Vorträge
            sorted_lectures = sorted(images_data.keys())
            
            # Teile in Chunks
            chunks = []
            current_chunk = {}
            
            for lecture_id in sorted_lectures:
                images = images_data[lecture_id]
                
                # Test ob hinzufügen noch passt
                test_chunk = {**current_chunk, lecture_id: images}
                test_size_mb = len(json.dumps(test_chunk, ensure_ascii=False).encode('utf-8')) / (1024 * 1024)
                
                if test_size_mb > MAX_CHUNK_SIZE_MB and current_chunk:
                    # Chunk ist voll
                    chunks.append(current_chunk)
                    current_chunk = {lecture_id: images}
                else:
                    current_chunk[lecture_id] = images
            
            # Letzten Chunk speichern
            if current_chunk:
                chunks.append(current_chunk)
            
            print(f"Erstelle {len(chunks)} Chunks:")
            
            # Speichere Chunks
            for i, chunk in enumerate(chunks):
                chunk_file = os.path.join(project_root, f'steiner-images-part{i+1:02d}.json')
                
                with open(chunk_file, 'w', encoding='utf-8') as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=2)
                
                chunk_size = len(json.dumps(chunk, ensure_ascii=False).encode('utf-8')) / (1024 * 1024)
                chunk_images = sum(len(imgs) for imgs in chunk.values())
                
                print(f"  + steiner-images-part{i+1:02d}.json ({chunk_size:.2f} MB, {len(chunk)} Vortraege, {chunk_images} Bilder)")
            
            # Lösche alte einzelne Datei (falls vorhanden)
            if os.path.exists(output_file):
                backup_file = output_file.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                os.rename(output_file, backup_file)
                print(f"\nAlte steiner-images.json umbenannt zu: {os.path.basename(backup_file)}")
        
        else:
            # Datei klein genug - als Einzeldatei speichern
            print(f"Datei klein genug (<={MAX_CHUNK_SIZE_MB} MB) - speichere als Einzeldatei\n")
            
            # Erstelle Backup
            if os.path.exists(output_file):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = output_file.replace('.json', f'_backup_{timestamp}.json')
                print(f"Erstelle Backup: {backup_file}")
                
                with open(output_file, 'r', encoding='utf-8') as original:
                    with open(backup_file, 'w', encoding='utf-8') as backup:
                        backup.write(original.read())
            
            # Speichere neue steiner-images.json
            print(f"Speichere: {output_file}")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(images_data, f, ensure_ascii=False, indent=2)
        
        # Finale Statistik
        print(f"\n" + "=" * 60)
        print("EXPORT ERFOLGREICH ABGESCHLOSSEN!")
        print("=" * 60)
        print(f"  Bildreferenzen gefunden: {total_found}")
        print(f"  Erfolgreich encodiert: {total_encoded}")
        print(f"  Nicht gefunden: {total_not_found}")
        print(f"  Vortraege mit Bildern: {len(images_data)}")
        print("=" * 60)
        
        if total_not_found > 0:
            print(f"\nHinweis: {total_not_found} Bilder wurden nicht gefunden.")
            print("Mögliche Gründe:")
            print("  - Bilder wurden noch nicht konvertiert (JPEG -> PNG)")
            print("  - Dateipfade stimmen nicht überein")
            print("  - Bilder existieren nicht im Steiner_GA Ordner")
        
        print(f"\nNächste Schritte:")
        print(f"  1. Server neu starten: node backend.js")
        print(f"  2. Browser neu laden (F5 oder Strg+F5)")
        print("=" * 60 + "\n")
    else:
        print("\n" + "=" * 60)
        print("FEHLER: Keine Bilder gefunden!")
        print("=" * 60)
        print("Mögliche Gründe:")
        print("  - Keine steiner-full-lectures*.json Dateien gefunden")
        print("  - Keine Bildreferenzen in den Lecture-Dateien")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

