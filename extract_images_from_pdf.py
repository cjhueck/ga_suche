#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrahiert Bilder aus PDF-Dateien für GA-Bände.
Kann von Node.js export-lectures.js aufgerufen werden.
"""

import sys
import os
from pathlib import Path

# Setze UTF-8 Encoding für Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Importiere PyMuPDF für PDF-Bild-Extraktion
try:
    import fitz  # PyMuPDF
    import io
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    print("ERROR: PyMuPDF (fitz) nicht verfügbar. Installiere mit: pip install PyMuPDF")
    sys.exit(1)

# Importiere PIL für Bildkonvertierung
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("ERROR: PIL/Pillow nicht verfügbar. Installiere mit: pip install Pillow")
    sys.exit(1)


def extract_images_from_pdf(ga_folder_path, image_index_map=None):
    """
    Extrahiert Bilder aus PDF-Datei und speichert sie als PNG im assets-Ordner.
    
    Args:
        ga_folder_path: Pfad zum GA-Ordner (z.B. "Steiner_GA/GA266a-Band I...")
        image_index_map: Optional dict mit Mapping von Bildnummern zu Dateinamen
                        z.B. {0: "img-0.png", 1: "img-1.png"}
    
    Returns:
        dict: {'success': bool, 'count': int, 'images': list}
    """
    if not FITZ_AVAILABLE or not PIL_AVAILABLE:
        return {'success': False, 'count': 0, 'images': [], 'error': 'Dependencies nicht verfügbar'}
    
    try:
        ga_folder = Path(ga_folder_path)
        ga_name = ga_folder.name
        
        # Suche nach PDF-Datei im GA-Ordner
        pdf_files = list(ga_folder.glob("*.pdf"))
        if not pdf_files:
            return {'success': False, 'count': 0, 'images': [], 'error': 'Keine PDF-Datei gefunden'}
        
        # Verwende die erste gefundene PDF-Datei
        pdf_path = pdf_files[0]
        
        # Erstelle assets-Ordner falls nicht vorhanden
        assets_dir = ga_folder / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        print(f"    📄 PDF gefunden: {pdf_path.name}")
        
        doc = fitz.open(str(pdf_path))
        image_count = 0
        image_index = 0
        extracted_images = []
        
        for pnum in range(len(doc)):
            page = doc[pnum]
            image_list = page.get_images()
            
            for img_idx, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Bestimme Dateinamen
                    if image_index_map and image_index in image_index_map:
                        image_filename = image_index_map[image_index]
                    else:
                        # Standard-Format: GA266a-Band I..._img-0.png
                        image_filename = f"{ga_name}_img-{image_index}.png"
                    
                    image_path = assets_dir / image_filename
                    
                    # Überspringe wenn bereits vorhanden
                    if image_path.exists():
                        image_index += 1
                        continue
                    
                    # Konvertiere zu PNG mit PIL
                    img_pil = Image.open(io.BytesIO(image_bytes))
                    
                    # Behalte Transparenz bei wenn vorhanden
                    if img_pil.mode in ('RGBA', 'LA', 'P'):
                        # Behalte Transparenz bei
                        img_pil.save(image_path, 'PNG', optimize=True)
                    else:
                        # Konvertiere zu RGB für maximale Kompatibilität
                        rgb_img = Image.new('RGB', img_pil.size, (255, 255, 255))
                        if img_pil.mode == 'RGBA':
                            rgb_img.paste(img_pil, mask=img_pil.split()[3])  # Alpha-Kanal als Maske
                        else:
                            rgb_img.paste(img_pil)
                        rgb_img.save(image_path, 'PNG', optimize=True)
                    
                    extracted_images.append(str(image_path))
                    image_count += 1
                    image_index += 1
                    
                except Exception as e:
                    print(f"    ⚠ Fehler bei Bild {pnum+1}/{img_idx+1}: {str(e)}")
                    continue
        
        doc.close()
        
        if image_count > 0:
            print(f"    ✅ {image_count} Bilder aus PDF extrahiert")
        
        return {
            'success': True,
            'count': image_count,
            'images': extracted_images,
            'pdf_path': str(pdf_path)
        }
        
    except Exception as e:
        return {
            'success': False,
            'count': 0,
            'images': [],
            'error': str(e)
        }


def main():
    """Hauptfunktion für Kommandozeilen-Aufruf"""
    if len(sys.argv) < 2:
        print("Verwendung: python extract_images_from_pdf.py <GA-Ordner-Pfad>")
        print("Beispiel: python extract_images_from_pdf.py 'Steiner_GA/GA266a-Band I 1904-1909 Gedächtnisaufzeichnungen von Teilnehmern'")
        sys.exit(1)
    
    ga_folder_path = sys.argv[1]
    
    if not os.path.exists(ga_folder_path):
        print(f"Fehler: Ordner nicht gefunden: {ga_folder_path}")
        sys.exit(1)
    
    result = extract_images_from_pdf(ga_folder_path)
    
    if result['success']:
        print(f"\n✅ Erfolgreich: {result['count']} Bilder extrahiert")
        sys.exit(0)
    else:
        print(f"\n❌ Fehler: {result.get('error', 'Unbekannter Fehler')}")
        sys.exit(1)


if __name__ == "__main__":
    main()

