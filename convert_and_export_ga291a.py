#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konvertiert JPEG-Bilder in GA291a zu PNG und aktualisiert die Bildpfade in MD-Dateien.
Dann wird GA291a exportiert.
"""

import os
import sys
import re
import subprocess
from pathlib import Path

# Setze UTF-8 Encoding für Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Importiere PIL für Bildkonvertierung
try:
    from PIL import Image
except ImportError:
    print("❌ PIL (Pillow) nicht installiert. Installiere mit: pip install Pillow")
    sys.exit(1)


def convert_jpeg_to_png(ga_folder_path):
    """
    Konvertiert alle JPEG-Dateien (jpg, jpeg) in einem GA-Ordner zu PNG.
    
    Args:
        ga_folder_path: Pfad zum GA-Ordner
        
    Returns:
        (converted_count, errors_count, converted_files)
    """
    ga_path = Path(ga_folder_path)
    
    if not ga_path.exists():
        print(f"❌ Ordner nicht gefunden: {ga_folder_path}")
        return 0, 0, []
    
    # Finde alle JPEG-Dateien rekursiv
    jpeg_files = []
    for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
        jpeg_files.extend(ga_path.rglob(ext))
    
    if not jpeg_files:
        print(f"ℹ️  Keine JPEG-Dateien gefunden in: {ga_folder_path}")
        return 0, 0, []
    
    converted = 0
    errors = 0
    converted_files = []
    
    print(f"\n📁 Verarbeite: {ga_folder_path}")
    print(f"   Gefundene JPEG-Dateien: {len(jpeg_files)}")
    
    for jpeg_file in jpeg_files:
        try:
            # Erstelle PNG-Dateinamen (ersetze Extension)
            png_file = jpeg_file.with_suffix('.png')
            
            # Wenn PNG bereits existiert, lösche es zuerst (wird überschrieben)
            if png_file.exists():
                print(f"   🔄 Überschreibe vorhandene PNG: {png_file.name}")
                png_file.unlink()
            
            # Öffne und konvertiere Bild
            print(f"   🔄 Konvertiere: {jpeg_file.name} → {png_file.name}")
            with Image.open(jpeg_file) as img:
                # Konvertiere zu RGB falls notwendig
                if img.mode in ('RGBA', 'LA', 'P'):
                    img.save(png_file, 'PNG', optimize=True)
                else:
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        rgb_img.paste(img, mask=img.split()[3])
                    else:
                        rgb_img.paste(img)
                    rgb_img.save(png_file, 'PNG', optimize=True)
            
            converted += 1
            converted_files.append({
                'old': jpeg_file.name,
                'new': png_file.name
            })
            
            # Lösche die ursprüngliche JPEG-Datei nach erfolgreicher Konvertierung
            jpeg_file.unlink()
            print(f"   ✅ Konvertiert und JPEG gelöscht: {jpeg_file.name}")
            
        except Exception as e:
            print(f"   ❌ Fehler bei {jpeg_file.name}: {str(e)}")
            errors += 1
    
    return converted, errors, converted_files


def update_image_paths_in_md_files(ga_folder_path, converted_files):
    """
    Aktualisiert die Bildpfade in allen MD-Dateien des GA-Ordners.
    Ersetzt .jpeg/.jpg durch .png in Bildverweisen.
    
    Args:
        ga_folder_path: Pfad zum GA-Ordner
        converted_files: Liste der konvertierten Dateien [{'old': 'name.jpeg', 'new': 'name.png'}, ...]
    
    Returns:
        Anzahl der geänderten MD-Dateien
    """
    ga_path = Path(ga_folder_path)
    md_files = list(ga_path.glob('*.md'))
    
    if not md_files:
        print(f"ℹ️  Keine MD-Dateien gefunden in: {ga_folder_path}")
        return 0
    
    print(f"\n📝 Aktualisiere Bildpfade in {len(md_files)} MD-Dateien...")
    
    changed_files = 0
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Ersetze alle .jpeg/.jpg Verweise durch .png in Bildlinks
            # Pattern: ![alt](path.jpeg) oder ![alt](path.jpg)
            content = re.sub(r'(\!\[[^\]]*\]\([^)]*\.)jpe?g(\))', r'\1png\2', content, flags=re.IGNORECASE)
            
            # Ersetze auch in Alt-Texten
            # Pattern: ![name.jpeg](path) -> ![name.png](path)
            content = re.sub(r'(\!\[)([^\]]*?)\.jpe?g(\])', r'\1\2.png\3', content, flags=re.IGNORECASE)
            
            if content != original_content:
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   ✅ Aktualisiert: {md_file.name}")
                changed_files += 1
        
        except Exception as e:
            print(f"   ❌ Fehler bei {md_file.name}: {str(e)}")
    
    return changed_files


def export_ga(ga_number):
    """
    Exportiert einen GA-Band über den Backend-Server.
    
    Args:
        ga_number: GA-Nummer (z.B. "GA291a")
    """
    print(f"\n🚀 Starte Export für {ga_number}...")
    
    # Verwende Node.js um den Export-Befehl auszuführen
    # Der Export läuft über das Backend
    try:
        # Prüfe ob der Server läuft
        import urllib.request
        import json
        
        base_url = "http://localhost:3003"
        
        # Teste Verbindung
        try:
            urllib.request.urlopen(f"{base_url}/api/ga-list", timeout=5)
        except Exception as e:
            print(f"❌ Server nicht erreichbar unter {base_url}")
            print(f"   Bitte starte den Server mit: node backend.js")
            return False
        
        # Starte Export
        export_url = f"{base_url}/api/export-ga"
        data = json.dumps({"gaNumber": ga_number}).encode('utf-8')
        req = urllib.request.Request(
            export_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   📤 Sende Export-Anfrage für {ga_number}...")
        response = urllib.request.urlopen(req, timeout=300)  # 5 Minuten Timeout
        result = json.loads(response.read().decode('utf-8'))
        
        if result.get('success'):
            print(f"   ✅ Export erfolgreich!")
            if result.get('exportedFiles'):
                print(f"   📁 Exportierte Dateien: {result['exportedFiles']}")
            return True
        else:
            print(f"   ❌ Export fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Export: {str(e)}")
        return False


def main():
    """Hauptfunktion"""
    base_dir = Path(__file__).parent
    steiner_ga_dir = base_dir / "Steiner_GA"
    
    # GA291a Ordner
    ga_folder = steiner_ga_dir / "GA291a-Farbenerkenntnis"
    
    print("=" * 70)
    print("JPEG zu PNG Konvertierung und Export für GA291a")
    print("=" * 70)
    
    # Schritt 1: JPEG zu PNG konvertieren
    print("\n" + "=" * 70)
    print("SCHRITT 1: JPEG-Dateien zu PNG konvertieren")
    print("=" * 70)
    
    converted, errors, converted_files = convert_jpeg_to_png(ga_folder)
    
    if converted > 0:
        print(f"\n✅ {converted} Dateien konvertiert")
        if errors > 0:
            print(f"⚠️  {errors} Fehler")
    elif errors == 0:
        print("\nℹ️  Keine JPEG-Dateien zum Konvertieren gefunden (bereits PNG?)")
    
    # Schritt 2: Bildpfade in MD-Dateien aktualisieren
    print("\n" + "=" * 70)
    print("SCHRITT 2: Bildpfade in MD-Dateien aktualisieren")
    print("=" * 70)
    
    changed_md_files = update_image_paths_in_md_files(ga_folder, converted_files)
    print(f"\n✅ {changed_md_files} MD-Dateien aktualisiert")
    
    # Schritt 3: GA291a exportieren
    print("\n" + "=" * 70)
    print("SCHRITT 3: GA291a exportieren")
    print("=" * 70)
    
    export_success = export_ga("GA291a")
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"  Bilder konvertiert: {converted}")
    print(f"  MD-Dateien aktualisiert: {changed_md_files}")
    print(f"  Export erfolgreich: {'Ja' if export_success else 'Nein'}")
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


