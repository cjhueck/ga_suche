#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrahiert Bilder aus GA267 und GA268 PDFs und konvertiert sie zu PNG.
"""

import sys
import os
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io

# Setze UTF-8 Encoding für Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def extract_and_convert_images(pdf_path, output_dir, ga_name):
    """
    Extrahiert Bilder aus PDF und konvertiert sie zu PNG.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
        output_dir: Ausgabe-Verzeichnis (GA-Ordner)
        ga_name: Name des GA-Bandes (z.B. "GA267-Seelenübungen I")
    """
    assets_dir = Path(output_dir) / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    print(f"\n📁 Verarbeite: {ga_name}")
    print(f"   PDF: {Path(pdf_path).name}")
    
    doc = fitz.open(pdf_path)
    print(f"   Seiten: {len(doc)}")
    
    image_count = 0
    image_index = 0
    
    for pnum in range(len(doc)):
        page = doc[pnum]
        image_list = page.get_images()
        
        for img_idx, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"].lower()
                
                # Erstelle Dateiname im Format: GA267-Seelenübungen I_img-0.png
                image_filename = f"{ga_name}_img-{image_index}.png"
                image_path = assets_dir / image_filename
                
                # Konvertiere zu PNG mit PIL
                img_pil = Image.open(io.BytesIO(image_bytes))
                
                # Konvertiere zu RGB falls notwendig
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
                
                image_count += 1
                image_index += 1
                
                if image_count % 5 == 0:
                    print(f"   ✅ {image_count} Bilder extrahiert...")
                    
            except Exception as e:
                print(f"   ⚠️  Fehler bei Bild {pnum+1}/{img_idx+1}: {str(e)}")
                continue
    
    doc.close()
    print(f"   ✅ Gesamt: {image_count} Bilder extrahiert und als PNG gespeichert")
    
    return image_count

def main():
    """Hauptfunktion"""
    base_dir = Path(__file__).parent
    steiner_ga_dir = base_dir / "Steiner_GA"
    
    # GA267 und GA268
    ga_configs = [
        {
            'folder': steiner_ga_dir / "GA267-Seelenübungen I",
            'pdf_name': "GA267-Seelenübungen I.pdf",
            'ga_name': "GA267-Seelenübungen I"
        },
        {
            'folder': steiner_ga_dir / "GA268-Mantrische Sprüche Seelenübungen II",
            'pdf_name': "GA268-Mantrische Sprüche Seelenübungen II.pdf",
            'ga_name': "GA268-Mantrische Sprüche Seelenübungen II"
        }
    ]
    
    print("=" * 70)
    print("Bild-Extraktion und PNG-Konvertierung für GA267 und GA268")
    print("=" * 70)
    
    total_images = 0
    
    for config in ga_configs:
        pdf_path = config['folder'] / config['pdf_name']
        
        if not pdf_path.exists():
            print(f"\n❌ PDF nicht gefunden: {pdf_path}")
            continue
        
        count = extract_and_convert_images(
            pdf_path,
            config['folder'],
            config['ga_name']
        )
        total_images += count
    
    print("\n" + "=" * 70)
    print(f"✅ Extraktion abgeschlossen!")
    print(f"   Gesamt: {total_images} Bilder extrahiert")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unerwarteter Fehler: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

