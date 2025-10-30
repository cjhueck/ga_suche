#!/usr/bin/env python3
"""
Konvertiert JPEG-Bilder zu PNG mit transparentem Hintergrund.
Optimal für schwarz-weiß Zeichnungen/Diagramme.
"""

import os
from PIL import Image
import numpy as np

def remove_white_background(image_path, output_path, threshold=240):
    """
    Entfernt weißen Hintergrund und macht ihn transparent.
    
    Args:
        image_path: Pfad zum Eingabebild (JPEG)
        output_path: Pfad zum Ausgabebild (PNG)
        threshold: Helligkeitsschwelle (0-255). Pixel heller als dieser Wert werden transparent.
                   Standard: 240 (fast weiß)
    """
    print(f"Verarbeite: {os.path.basename(image_path)}")
    
    # Lade Bild
    img = Image.open(image_path)
    
    # Konvertiere zu RGBA (mit Alpha-Kanal für Transparenz)
    img = img.convert("RGBA")
    
    # Konvertiere zu NumPy Array für einfache Manipulation
    data = np.array(img)
    
    # RGB-Kanäle
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    
    # Finde weiße/helle Pixel (alle RGB-Werte über threshold)
    white_areas = (r > threshold) & (g > threshold) & (b > threshold)
    
    # Setze Alpha-Kanal auf 0 (transparent) für weiße Bereiche
    data[white_areas, 3] = 0
    
    # Erstelle neues Bild aus modifizierten Daten
    result = Image.fromarray(data)
    
    # Speichere als PNG
    result.save(output_path, 'PNG')
    print(f"  -> Gespeichert als: {os.path.basename(output_path)}")


def convert_directory(input_dir, threshold=240):
    """
    Konvertiert alle JPEG-Dateien in einem Verzeichnis.
    """
    # Erstelle Backup-Ordner für Originale
    backup_dir = os.path.join(input_dir, "_backup_jpegs")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Finde alle JPEG-Dateien
    jpeg_files = [f for f in os.listdir(input_dir) 
                  if f.lower().endswith(('.jpg', '.jpeg'))]
    
    if not jpeg_files:
        print("Keine JPEG-Dateien gefunden!")
        return
    
    print(f"\nGefunden: {len(jpeg_files)} JPEG-Dateien")
    print(f"Backup-Ordner: {backup_dir}")
    print(f"Helligkeits-Schwelle: {threshold} (Pixel heller als {threshold} werden transparent)\n")
    
    for jpeg_file in jpeg_files:
        input_path = os.path.join(input_dir, jpeg_file)
        
        # Erstelle PNG-Dateinamen (ersetze .jpg/.jpeg mit .png)
        base_name = os.path.splitext(jpeg_file)[0]
        output_path = os.path.join(input_dir, base_name + '.png')
        
        try:
            # Konvertiere zu PNG mit Transparenz
            remove_white_background(input_path, output_path, threshold)
            
            # Verschiebe Original ins Backup
            backup_path = os.path.join(backup_dir, jpeg_file)
            os.rename(input_path, backup_path)
            print(f"  -> Original nach Backup verschoben\n")
            
        except Exception as e:
            print(f"  X Fehler bei {jpeg_file}: {e}\n")
    
    print(f"\nFertig! {len(jpeg_files)} Bilder konvertiert.")
    print(f"Originale gesichert in: {backup_dir}")


if __name__ == "__main__":
    # Zielverzeichnis
    target_dir = r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA\GA089-Bewusstsein Leben Form\assets"
    
    print("=" * 60)
    print("JPEG zu PNG Konverter mit Transparenz")
    print("=" * 60)
    print(f"Verzeichnis: {target_dir}\n")
    
    # Ueberpruefe ob Verzeichnis existiert
    if not os.path.exists(target_dir):
        print(f"X Fehler: Verzeichnis nicht gefunden!")
        print(f"  {target_dir}")
        exit(1)
    
    print("Starte Konvertierung...\n")
    
    # Konvertiere mit threshold=240 (sehr helles Weiss wird transparent)
    # Bei Bedarf anpassen: niedrigerer Wert = mehr wird transparent
    convert_directory(target_dir, threshold=240)
    
    print("\nHinweis: Falls zu viel oder zu wenig transparent ist,")
    print("können Sie das Script mit einem anderen 'threshold'-Wert erneut ausführen:")
    print("  - Höherer Wert (z.B. 250): Nur sehr reines Weiß wird transparent")
    print("  - Niedrigerer Wert (z.B. 220): Auch hellgraue Bereiche werden transparent")

