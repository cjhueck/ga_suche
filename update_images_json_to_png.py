#!/usr/bin/env python3
"""
Aktualisiert steiner-images.json: Ersetzt JPEG-Referenzen durch PNG-Referenzen
und aktualisiert die Base64-encodierten Bilddaten.
"""

import json
import os
import base64
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


def update_images_json(json_path, assets_dir):
    """
    Aktualisiert die steiner-images.json:
    - Ersetzt .jpeg Referenzen durch .png
    - Aktualisiert Base64-Daten
    - Aktualisiert Dateigrößen
    """
    print(f"Lade JSON: {json_path}")
    
    # Lade bestehende JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        images_data = json.load(f)
    
    total_updated = 0
    total_not_found = 0
    
    # Durchlaufe alle Lectures
    for lecture_id, images in images_data.items():
        if not images:  # Leeres Array
            continue
        
        for img_obj in images:
            # Prüfe ob es eine JPEG-Referenz ist
            if '.jpeg' in img_obj.get('path', '').lower() or '.jpg' in img_obj.get('path', '').lower():
                old_path = img_obj['path']
                
                # Erstelle neuen PNG-Pfad (ersetze .jpeg/.jpg mit .png)
                new_path = old_path.replace('.jpeg', '.png').replace('.jpg', '.png').replace('.JPEG', '.png').replace('.JPG', '.png')
                
                # Dekodiere URL-encoding für Dateisystem-Zugriff
                filesystem_path = new_path.replace('%20', ' ')
                full_path = os.path.join(os.path.dirname(json_path), filesystem_path)
                
                # Prüfe ob PNG-Datei existiert
                if os.path.exists(full_path):
                    print(f"\nAktualisiere: {lecture_id}")
                    print(f"  Alt: {old_path}")
                    print(f"  Neu: {new_path}")
                    
                    try:
                        # Generiere neue Base64-Daten
                        base64_str, file_size = encode_image_to_base64(full_path)
                        
                        # Aktualisiere Objekt - NUR path, base64 und size!
                        img_obj['path'] = new_path
                        # altText und markdownRef NICHT ändern - müssen .jpeg bleiben!
                        img_obj['base64'] = base64_str
                        img_obj['size'] = file_size
                        
                        print(f"  Groesse: {file_size} bytes")
                        total_updated += 1
                        
                    except Exception as e:
                        print(f"  X Fehler beim Encodieren: {e}")
                        total_not_found += 1
                else:
                    print(f"\nWarnung: PNG nicht gefunden: {full_path}")
                    total_not_found += 1
    
    if total_updated > 0:
        # Erstelle Backup der originalen JSON
        backup_path = json_path + '.backup'
        print(f"\n\nErstelle Backup: {backup_path}")
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(images_data, f, ensure_ascii=False, indent=2)
        
        # Speichere aktualisierte JSON
        print(f"Speichere aktualisierte JSON: {json_path}")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(images_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"Fertig!")
        print(f"  Aktualisiert: {total_updated} Bilder")
        print(f"  Nicht gefunden: {total_not_found} Bilder")
        print(f"  Backup gespeichert: {backup_path}")
        print(f"{'='*60}")
    else:
        print("\nKeine Bilder zum Aktualisieren gefunden.")


if __name__ == "__main__":
    # Pfade
    project_root = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(project_root, 'steiner-images.json')
    assets_dir = r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA\GA089-Bewusstsein Leben Form\assets"
    
    print("=" * 60)
    print("steiner-images.json Updater: JPEG -> PNG")
    print("=" * 60)
    print(f"JSON-Datei: {json_path}")
    print(f"Assets-Ordner: {assets_dir}\n")
    
    if not os.path.exists(json_path):
        print(f"X Fehler: JSON-Datei nicht gefunden!")
        exit(1)
    
    update_images_json(json_path, assets_dir)







