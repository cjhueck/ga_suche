#!/usr/bin/env python3
"""
Exportiert Bilder aus den steiner-full-lectures JSON-Dateien nach steiner-images.json.
Liest die Bildreferenzen aus den Vorträgen und encodiert die tatsächlichen PNG-Dateien.
"""

import json
import os
import base64
import re
from pathlib import Path

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
        else:
            mime_type = 'image/png'  # Default
        
        return f"data:{mime_type};base64,{base64_data}", len(img_data)


def extract_images_from_lectures(lectures_files, assets_base_dir):
    """
    Durchsucht alle Lecture-Dateien nach Bildreferenzen und erstellt steiner-images.json
    """
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
                
                # Suche nach Bildmarkierungen: ![alt](path)
                image_pattern = r'!\[([^\]]+)\]\(([^)]+)\)'
                matches = re.findall(image_pattern, content)
                
                if matches:
                    for alt_text, img_path in matches:
                        total_found += 1
                        
                        # Dekodiere URL-encoding
                        img_path_decoded = img_path.replace('%20', ' ')
                        
                        # Versuche PNG-Version zu finden
                        png_path = re.sub(r'\.(jpe?g)$', '.png', img_path_decoded, flags=re.IGNORECASE)
                        
                        # Extrahiere GA-Nummer und finde tatsächlichen Ordnernamen
                        ga_number = lecture_id.split('/')[0]
                        
                        # Suche nach dem tatsächlichen Ordner im Steiner_GA-Verzeichnis
                        ga_folder = None
                        for folder_name in os.listdir(assets_base_dir):
                            if folder_name.startswith(ga_number + '-'):
                                ga_folder = folder_name
                                break
                        
                        if not ga_folder:
                            # Fallback: verwende gaTitle
                            ga_title = lecture.get('gaTitle', '').split('(')[0].strip()
                            ga_folder = f"{ga_number}-{ga_title}"
                        
                        # Entferne "assets/" aus png_path, falls vorhanden
                        png_filename = png_path.replace('assets/', '')
                        
                        # Konstruiere vollständigen Pfad: Steiner_GA/GA089-Bewusstsein Leben Form/assets/...
                        full_png_path = os.path.join(
                            assets_base_dir,  # Das ist jetzt steiner_ga_dir
                            ga_folder,
                            'assets',  # Füge assets-Ordner hinzu
                            png_filename
                        )
                        
                        # DEBUG: Zeige konstruierten Pfad für GA089
                        if 'GA089' in lecture_id and 'img-0' in png_path:
                            print(f"\n  === DEBUG für GA089/img-0 ===")
                            print(f"  img_path (original): {img_path}")
                            print(f"  png_path: {png_path}")
                            print(f"  png_filename: {png_filename}")
                            print(f"  ga_folder: {ga_folder}")
                            print(f"  assets_base_dir: {assets_base_dir}")
                            print(f"  full_png_path: {full_png_path}")
                            print(f"  exists: {os.path.exists(full_png_path)}")
                            print(f"  ===========================\n")
                        
                        if os.path.exists(full_png_path):
                            print(f"  OK {lecture_id} - {alt_text}")
                            
                            try:
                                # Encodiere Bild
                                base64_str, file_size = encode_image_to_base64(full_png_path)
                                
                                # Erstelle Eintrag
                                # WICHTIG: altText und markdownRef behalten ORIGINAL (aus Text, mit .jpeg)
                                # path enthält .png (für tatsächliche Datei)
                                image_entry = {
                                    'index': para_index,
                                    'altText': alt_text,  # Original aus Text
                                    'path': png_path,  # PNG-Pfad für die Datei
                                    'markdownRef': f"![{alt_text}]({img_path})",  # Original-Referenz aus Text!
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
                            print(f"  X PNG nicht gefunden: {lecture_id} - {png_path}")
                            total_not_found += 1
    
    return images_data, total_found, total_encoded, total_not_found


if __name__ == "__main__":
    # Pfade
    project_root = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(project_root, 'steiner-images.json')
    
    # Finde alle lecture-Dateien
    lecture_files = [
        os.path.join(project_root, f'steiner-full-lectures-051-311-part0{i}.json')
        for i in range(1, 8)
    ]
    lecture_files = [f for f in lecture_files if os.path.exists(f)]
    
    # Assets-Verzeichnisse
    assets_dir = os.path.join(project_root, 'assets')
    steiner_ga_dir = r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA"
    
    print("=" * 60)
    print("Steiner Images Exporter")
    print("=" * 60)
    print(f"Lecture-Dateien: {len(lecture_files)}")
    print(f"Assets-Ordner: {assets_dir}")
    print(f"Steiner GA-Ordner: {steiner_ga_dir}\n")
    
    # Extrahiere Bilder (verwende Steiner_GA als Basis-Ordner)
    images_data, total_found, total_encoded, total_not_found = extract_images_from_lectures(
        lecture_files, 
        steiner_ga_dir
    )
    
    if images_data:
        # Erstelle Backup
        if os.path.exists(output_file):
            backup_file = output_file + '.backup'
            print(f"\nErstelle Backup: {backup_file}")
            with open(backup_file, 'w', encoding='utf-8') as f:
                with open(output_file, 'r', encoding='utf-8') as original:
                    f.write(original.read())
        
        # Speichere neue steiner-images.json
        print(f"Speichere: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(images_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"OK Fertig!")
        print(f"  Bildreferenzen gefunden: {total_found}")
        print(f"  Erfolgreich encodiert: {total_encoded}")
        print(f"  Nicht gefunden: {total_not_found}")
        print(f"  Vorträge mit Bildern: {len(images_data)}")
        print(f"{'='*60}")
    else:
        print("\nKeine Bilder gefunden.")

