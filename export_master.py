#!/usr/bin/env python3
"""
Master Export-Skript fuer Steiner GA-Suche
==========================================
Fuehrt den kompletten Export-Workflow automatisch aus:
1. Bildpfade in Obsidian korrigieren (optional)
   - Extrahiert Bilder aus PDF-Dateien (falls vorhanden) und speichert sie als PNG
   - Konvertiert JPEG-Bilder zu PNG im assets-Ordner
   - Korrigiert fehlerhafte Markdown/Wiki-Links
   - Vereinfacht GA-Ordner-Pfade zu assets/...
   - Backup-Dateien werden automatisch erstellt
2a. Bücher exportieren (GA001-GA050)
   - Exportiert Bücher als JSON mit Absätzen und Überschriften
   - Überschriften werden in summary-database.json gespeichert
2b. Lectures aus Obsidian exportieren (inkl. Bilder, GA051+)
   - Exportiert Vortraege als JSON (gesplittete part-Dateien)
   - Bilder werden direkt als gesplittete part-Dateien exportiert
   - Jede Datei < 10 MB (GitHub-kompatibel)
3. Server neu starten (optional)

Verwendung:
    python export_master.py                      # Kompletter Export (ALLE GA-Baende)
    python export_master.py GA112-GA117a         # Nur bestimmte GA-Baende
    python export_master.py --skip-path-fix      # Bildpfad-Korrektur ueberspringen
    python export_master.py --restart-server     # Server automatisch neu starten
    
Beispiele:
    python export_master.py                      # Alles mit Bildpfad-Korrektur
    python export_master.py GA089                # Nur GA089
    python export_master.py GA175-GA209 --restart-server
    python export_master.py --skip-path-fix
    
Hinweis:
    Bilder werden automatisch mit den Lectures exportiert und gesplittet.
    Es wird keine steiner-images.json mehr erstellt, nur part-Dateien.
"""

import subprocess
import sys
import os
import re
import time
import json
from datetime import datetime
from pathlib import Path

# Importiere Rechtschreibkorrekturen
try:
    from rechtschreibregeln import korrigiere_rechtschreibung
except ImportError:
    print("Warnung: rechtschreibregeln.py nicht gefunden")
    def korrigiere_rechtschreibung(text):
        return text

# Importiere PIL für Bildkonvertierung
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warnung: PIL/Pillow nicht verfügbar. JPEG-zu-PNG Konvertierung wird übersprungen.")

# Importiere PyMuPDF für PDF-Bild-Extraktion
try:
    import fitz  # PyMuPDF
    import io
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    print("Warnung: PyMuPDF (fitz) nicht verfügbar. PDF-Bild-Extraktion wird übersprungen.")


# ============================================================================
# BILDPFAD-KORREKTUR FUNKTIONEN (Integriert)
# ============================================================================

def extract_images_from_pdf(ga_folder_path):
    """
    Extrahiert Bilder aus PDF-Datei (falls vorhanden) und speichert sie als PNG im assets-Ordner.
    
    Args:
        ga_folder_path: Pfad zum GA-Ordner (z.B. "Steiner_GA/GA267-Seelenübungen I")
        
    Returns:
        Anzahl der extrahierten Bilder
    """
    if not FITZ_AVAILABLE or not PIL_AVAILABLE:
        return 0
    
    try:
        ga_folder = Path(ga_folder_path)
        ga_name = ga_folder.name
        
        # Prüfe ob assets-Ordner bereits Bilder enthält
        assets_dir = ga_folder / "assets"
        if assets_dir.exists():
            existing_images = list(assets_dir.glob("*.png")) + list(assets_dir.glob("*.jpg")) + list(assets_dir.glob("*.jpeg"))
            if len(existing_images) > 0:
                # Bilder bereits vorhanden, überspringe Extraktion
                return 0
        
        # Suche nach PDF-Datei im GA-Ordner
        pdf_files = list(ga_folder.glob("*.pdf"))
        if not pdf_files:
            return 0
        
        # Verwende die erste gefundene PDF-Datei
        pdf_path = pdf_files[0]
        
        # Erstelle assets-Ordner falls nicht vorhanden
        assets_dir.mkdir(exist_ok=True)
        
        print(f"    📄 PDF gefunden: {pdf_path.name}")
        
        doc = fitz.open(str(pdf_path))
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
                    
                except Exception as e:
                    print(f"    ⚠ Fehler bei Bild {pnum+1}/{img_idx+1}: {str(e)}")
                    continue
        
        doc.close()
        
        if image_count > 0:
            print(f"    ✅ {image_count} Bilder aus PDF extrahiert")
        
        return image_count
        
    except Exception as e:
        print(f"    ⚠ Fehler bei PDF-Extraktion in {ga_folder_path}: {e}")
        return 0


def convert_jpeg_to_png_files(md_file_path):
    """
    Konvertiert alle JPEG-Bilder in PNG im assets-Ordner des GA-Bandes.
    Sucht alle .jpeg/.jpg Dateien im assets-Ordner und konvertiert sie zu .png.
    
    Args:
        md_file_path: Pfad zur Markdown-Datei
        
    Returns:
        Anzahl der konvertierten Dateien
    """
    if not PIL_AVAILABLE:
        return 0
    
    try:
        md_dir = os.path.dirname(md_file_path)
        
        # Finde assets-Ordner relativ zur Markdown-Datei
        assets_dir = os.path.join(md_dir, 'assets')
        
        if not os.path.exists(assets_dir):
            return 0
        
        converted_count = 0
        
        # Finde alle JPEG-Dateien im assets-Ordner
        for filename in os.listdir(assets_dir):
            if filename.lower().endswith('.jpeg') or filename.lower().endswith('.jpg'):
                jpeg_path = os.path.join(assets_dir, filename)
                
                # Erstelle PNG-Pfad
                png_filename = re.sub(r'\.jpe?g$', '.png', filename, flags=re.IGNORECASE)
                png_path = os.path.join(assets_dir, png_filename)
                
                # Überspringe wenn PNG bereits existiert
                if os.path.exists(png_path):
                    continue
                
                try:
                    # Konvertiere JPEG zu PNG
                    img = Image.open(jpeg_path)
                    img.save(png_path, 'PNG')
                    converted_count += 1
                except Exception as e:
                    print(f"    ⚠ Konvertierung fehlgeschlagen: {jpeg_path} → {e}")
        
        return converted_count
        
    except Exception as e:
        print(f"    ⚠ Fehler beim Konvertieren der Bilder in {md_file_path}: {e}")
        return 0


def fix_image_refs_in_file(filepath, apply_changes=False):
    """Korrigiert Bildreferenzen in einer Markdown-Datei"""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # Fix 1: Wiki-Links mit vollem Pfad vereinfachen
        # ![[GA223-Der Jahreskreislauf.../assets/223-T01.webp]] → ![[223-T01.webp]]
        pattern1 = r'!\[\[GA\d{3}[a-z]?-[^/]+/assets/([^\]]+)\]\]'
        
        def replace1(match):
            filename = match.group(1)
            new_ref = f'![[{filename}]]'
            changes.append(f"  - Wiki-Link vereinfacht: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern1, replace1, content)
        
        # Fix 2: Falsche Dateinamen mit Leerzeichen korrigieren
        # ![[213-T01 3.webp]] → ![[213-T01.webp]]
        pattern2 = r'!\[\[(\d{3})-T(\d{2})\s+\d+\.webp\]\]'
        
        def replace2(match):
            num1 = match.group(1)
            num2 = match.group(2)
            new_ref = f'![[{num1}-T{num2}.webp]]'
            changes.append(f"  - Leerzeichen entfernt: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern2, replace2, content)
        
        # Fix 3: Unterstrich zu Bindestrich
        # ![[221_T01.webp]] → ![[221-T01.webp]]
        pattern3 = r'!\[\[(\d{3})_T(\d{2})\.webp\]\]'
        
        def replace3(match):
            num1 = match.group(1)
            num2 = match.group(2)
            new_ref = f'![[{num1}-T{num2}.webp]]'
            changes.append(f"  - Unterstrich zu Bindestrich: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern3, replace3, content)
        
        # Fix 4: Markdown-Links mit vollem Pfad (Pattern 1: assets/GA...)
        # ![text](assets/GA223-.../assets/223-T01.webp) → ![text](<assets/223-T01.webp>)
        pattern4 = r'(!\[[^\]]*\]\()assets/GA\d{3}[a-z]?-[^/]+/assets/([^)]+)\)'
        
        def replace4(match):
            prefix = match.group(1)
            filename = match.group(2)
            # Wenn Pfad Leerzeichen enthält, in <> einschließen (Markdown-Standard)
            path = f'assets/{filename}'
            if ' ' in path:
                path = f'<{path}>'
            new_ref = f'{prefix}{path})'
            changes.append(f"  - Markdown-Pfad bereinigt: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern4, replace4, content)
        
        # Fix 5: Markdown-Links mit GA-Ordner am Anfang (Pattern 2: GA...)
        # ![text](GA145-Welche Bedeutung.../assets/img-0.jpeg) → ![text](<assets/img-0.jpeg>)
        # ![text](GA151-Der menschliche.../assets/img-2.jpeg) → ![text](<assets/img-2.jpeg>)
        pattern5 = r'(!\[[^\]]*\]\()GA\d{3}[a-z]?-[^/]+/assets/([^)]+)\)'
        
        def replace5(match):
            prefix = match.group(1)
            filename = match.group(2)
            # Wenn Pfad Leerzeichen enthält, in <> einschließen (Markdown-Standard)
            path = f'assets/{filename}'
            if ' ' in path:
                path = f'<{path}>'
            new_ref = f'{prefix}{path})'
            changes.append(f"  - Markdown-Pfad vereinfacht: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern5, replace5, content)
        
        # Fix 6: Lange Gedankenstriche durch kurze ersetzen
        # — (em dash) → - (hyphen)
        original_before_dash_fix = content
        content = content.replace('—', '-')
        
        # Zähle wie viele Gedankenstriche ersetzt wurden
        num_dashes_replaced = original_before_dash_fix.count('—')
        if num_dashes_replaced > 0:
            changes.append(f"  - Gedankenstriche ersetzt: {num_dashes_replaced}× (— → -)")
        
        # Fix 7: kk durch ck in deutschen Wörtern ersetzen
        # Entwikklung → Entwicklung, strikken → stricken, etc.
        original_before_kk_fix = content
        
        # Pattern: kk innerhalb von Wörtern (mit Buchstaben davor und danach)
        kk_pattern = r'\b(\w+?)kk(\w+?)\b'
        
        def replace_kk(match):
            before = match.group(1)
            after = match.group(2)
            word = before + 'kk' + after
            
            # Überspringe wenn:
            # - Zu kurz (< 5 Zeichen)
            # - Enthält Sonderzeichen (URL, etc.)
            # - kk am Anfang des Wortes
            # - Wort ist "okkult" oder beginnt mit "okkult" (z.B. Okkultismus)
            if (len(word) < 5 or not before or 
                any(c in word for c in ['/', ':', '.', '@', '_']) or
                word.lower().startswith('okkult')):
                return match.group(0)
            
            # Ersetze kk durch ck
            return before + 'ck' + after
        
        content = re.sub(kk_pattern, replace_kk, content)
        
        # Zähle wie viele kk ersetzt wurden (ungefähr)
        num_kk_before = len(re.findall(kk_pattern, original_before_kk_fix))
        num_kk_after = len(re.findall(kk_pattern, content))
        num_kk_replaced = num_kk_before - num_kk_after
        
        if num_kk_replaced > 0:
            changes.append(f"  - kk→ck ersetzt: {num_kk_replaced}× (Entwikklung → Entwicklung)")
        
        # Fix 8: URL-codierte Bildpfade decodieren
        # ![alt](assets/GA091-Kosmologie%20und%20menschliche%20Evolution_img-19.png) 
        # → ![alt](<assets/GA091-Kosmologie und menschliche Evolution_img-19.png>)
        from urllib.parse import unquote
        
        original_before_image_fix = content
        
        # Pattern für Markdown-Bilder mit URL-codierten Pfaden (enthält %)
        image_pattern = r'!\[([^\]]*)\]\(([^)]*%[^)]*)\)'
        
        def decode_image_path(match):
            alt_text = match.group(1)
            encoded_path = match.group(2)
            decoded_path = unquote(encoded_path)
            # Wenn Pfad Leerzeichen enthält, in <> einschließen (Markdown-Standard)
            if ' ' in decoded_path:
                decoded_path = f'<{decoded_path}>'
            return f'![{alt_text}]({decoded_path})'
        
        content = re.sub(image_pattern, decode_image_path, content)
        
        # Zähle wie viele Bildpfade decodiert wurden
        num_images_decoded = len(re.findall(image_pattern, original_before_image_fix))
        
        if num_images_decoded > 0:
            changes.append(f"  - Bildpfade decodiert: {num_images_decoded}× (URL-Codierung entfernt)")
        
        # Fix 9: Bildpfade mit Leerzeichen in <> einschließen (für Markdown-Parser)
        # ![alt](assets/path with spaces.jpg) → ![alt](<assets/path with spaces.jpg>)
        original_before_space_fix = content
        
        # Pattern für Markdown-Bilder mit Leerzeichen im Pfad (aber noch nicht in <> eingeschlossen)
        # Wichtig: Match nur, wenn Leerzeichen im Pfad sind UND noch keine <> vorhanden sind
        space_image_pattern = r'!\[([^\]]*)\]\((?!<)([^)<\s][^)<]*\s[^)<]*?)(?<!>)\)'
        
        def wrap_spaced_path(match):
            alt_text = match.group(1)
            path = match.group(2)
            # Nur einschließen, wenn tatsächlich Leerzeichen vorhanden sind
            if ' ' in path:
                return f'![{alt_text}](<{path}>)'
            return match.group(0)
        
        content = re.sub(space_image_pattern, wrap_spaced_path, content)
        
        # Zähle wie viele Bildpfade mit <> versehen wurden
        num_spaces_wrapped = content.count('(<assets/') - original_before_space_fix.count('(<assets/')
        
        if num_spaces_wrapped > 0:
            changes.append(f"  - Bildpfade mit <> versehen: {num_spaces_wrapped}× (Leerzeichen im Pfad)")
        
        # Fix 10: JPEG zu PNG Konvertierung in Bildreferenzen
        # ![alt](assets/img-0.jpeg) → ![alt](assets/img-0.png)
        # ![alt](<'assets/img-0.jpeg'>) → ![alt](<'assets/img-0.png'>)
        # ![alt]('assets/img-0.jpeg') → ![alt]('assets/img-0.png')
        original_before_jpeg_fix = content
        
        # Pattern für Markdown-Bilder mit .jpeg oder .jpg Endung
        # Erfasst alle Varianten: mit/ohne < >, mit/ohne Anführungszeichen
        jpeg_pattern = r'!\[([^\]]*)\]\(([^)]*\.jpe?g)([^)]*)\)'
        
        def convert_jpeg_to_png(match):
            alt_text = match.group(1)
            path_before_ext = match.group(2)  # Alles vor .jpeg/.jpg
            path_after_ext = match.group(3)   # Alles nach .jpeg/.jpg (kann ' oder > enthalten)
            
            # Konvertiere auch Alt-Text von .jpeg/.jpg zu .png
            alt_text_converted = re.sub(r'\.jpe?g$', '.png', alt_text, flags=re.IGNORECASE)
            
            # Entferne .jpeg oder .jpg und füge .png hinzu
            # path_before_ext endet mit .jpeg oder .jpg, also entfernen wir das
            path_without_ext = re.sub(r'\.jpe?g$', '', path_before_ext, flags=re.IGNORECASE)
            png_path_full = path_without_ext + '.png' + path_after_ext
            
            return f'![{alt_text_converted}]({png_path_full})'
        
        content = re.sub(jpeg_pattern, convert_jpeg_to_png, content)
        
        # Zusätzlicher Fix: Konvertiere Alt-Texte mit .jpeg/.jpg auch wenn Pfad bereits .png ist
        # ![img-3.jpeg](<'assets/...img-3.png'>) → ![img-3.png](<'assets/...img-3.png'>)
        alt_jpeg_pattern = r'!\[([^\]]*\.jpe?g)\](\([^)]*\.png[^)]*\))'
        
        def convert_alt_jpeg_to_png(match):
            alt_text = match.group(1)
            path_part = match.group(2)
            alt_text_converted = re.sub(r'\.jpe?g$', '.png', alt_text, flags=re.IGNORECASE)
            return f'![{alt_text_converted}]{path_part}'
        
        content = re.sub(alt_jpeg_pattern, convert_alt_jpeg_to_png, content)
        
        # Zähle wie viele JPEG-Referenzen konvertiert wurden
        num_jpegs_before = len(re.findall(jpeg_pattern, original_before_jpeg_fix))
        num_jpegs_after = len(re.findall(jpeg_pattern, content))
        num_jpegs_converted = num_jpegs_before - num_jpegs_after
        
        # Zähle auch Alt-Text-Konvertierungen
        num_alt_jpegs_before = len(re.findall(alt_jpeg_pattern, original_before_jpeg_fix))
        num_alt_jpegs_after = len(re.findall(alt_jpeg_pattern, content))
        num_alt_jpegs_converted = num_alt_jpegs_before - num_alt_jpegs_after
        
        total_converted = num_jpegs_converted + num_alt_jpegs_converted
        if total_converted > 0:
            changes.append(f"  - JPEG zu PNG konvertiert: {total_converted}× (.jpeg/.jpg → .png)")
        
        # Fix 11: Deutsche Rechtschreibkorrekturen
        original_before_spelling_fix = content
        
        # Verwende zuerst die umfassende Rechtschreibkorrektur aus rechtschreibregeln.py
        content = korrigiere_rechtschreibung(content)
        
        # Zusätzliche spezifische Korrekturen
        spelling_replacements = [
            ('Fleiss', 'Fleiß'),
            ('fleiss', 'fleiß'),
            ('vergeßlich', 'vergesslich'),
            ('heiss', 'heiß'),
            ('zurücckommen', 'zurückkommen'),
            ('ackurat', 'akkurat'),
            ('paßt', 'passt'),
            ('römischkatholisch', 'römisch-katholisch'),
            ('seelischgeistig', 'seelisch-geistig'),
            ('DeutschÖsterreicher', 'Deutsch-Österreicher')
        ]
        
        num_spelling_fixes = 0
        for old_spelling, new_spelling in spelling_replacements:
            count = content.count(old_spelling)
            if count > 0:
                content = content.replace(old_spelling, new_spelling)
                num_spelling_fixes += count
        
        if num_spelling_fixes > 0:
            changes.append(f"  - Rechtschreibung korrigiert: {num_spelling_fixes}× (DeutschÖsterreicher→Deutsch-Österreicher, paßt→passt, römischkatholisch→römisch-katholisch, etc.)")
        
        # Wende Änderungen an
        if changes and apply_changes:
            # KEIN Backup mehr - Backups werden nicht mehr erstellt
            # Backup-Erstellung entfernt, um .md.backup Dateien zu vermeiden
            
            # Speichere
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return len(changes), changes
        
    except Exception as e:
        print(f"  X Fehler bei {filepath}: {e}")
        return 0, []


# ============================================================================
# EXPORT MASTER CLASS
# ============================================================================

class ExportMaster:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.steiner_ga_dir = os.path.join(self.project_root, "Steiner_GA")
        self.steps_completed = []
        self.steps_failed = []
        
    def print_header(self, title):
        """Druckt formatierten Header"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
    
    def print_step(self, step_num, total_steps, title):
        """Druckt Schritt-Header"""
        # Unterstützt auch Unter-Schritte (z.B. "2a", "2b")
        step_display = str(step_num) if isinstance(step_num, int) else step_num
        print(f"\n{'#' * 70}")
        print(f"  SCHRITT {step_display}/{total_steps}: {title}")
        print(f"{'#' * 70}\n")
    
    def run_command(self, command, step_name, shell=False):
        """
        Führt einen Befehl aus und gibt Erfolg/Fehler zurück
        """
        try:
            if isinstance(command, str):
                # Für Windows PowerShell
                result = subprocess.run(
                    command,
                    shell=True,
                    check=True,
                    capture_output=False,
                    text=True,
                    cwd=self.project_root
                )
            else:
                result = subprocess.run(
                    command,
                    check=True,
                    capture_output=False,
                    text=True,
                    cwd=self.project_root,
                    shell=shell
                )
            
            self.steps_completed.append(step_name)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\nFEHLER bei {step_name}!")
            print(f"   Exit Code: {e.returncode}")
            self.steps_failed.append(step_name)
            return False
        except Exception as e:
            print(f"\nFEHLER bei {step_name}: {e}")
            self.steps_failed.append(step_name)
            return False
    
    def step1_fix_image_paths(self, skip=False, ga_bands=None):
        """Schritt 1: Bildpfade in Obsidian korrigieren"""
        if skip:
            print("\nSCHRITT 1 UEBERSPRUNGEN (--skip-path-fix)")
            return True
        
        self.print_step(1, 3, "Bildpfade in Obsidian korrigieren")
        
        try:
            total_files = 0
            total_fixes = 0
            
            # Erstelle Set von GA-Nummern für schnellen Lookup (z.B. "266a" aus "GA266a")
            ga_filter = None
            if ga_bands:
                ga_filter = set()
                for ga in ga_bands:
                    ga_match = re.match(r'GA(\d{2,3}[a-z]?)', ga.upper())
                    if ga_match:
                        ga_filter.add(ga_match.group(1).upper())
                print(f"Bildpfadkorrektur nur für: {', '.join(sorted(ga_filter))}\n")
            
            # Durchlaufe alle GA-Ordner
            for folder_name in sorted(os.listdir(self.steiner_ga_dir)):
                folder_path = os.path.join(self.steiner_ga_dir, folder_name)
                
                if not os.path.isdir(folder_path) or not folder_name.startswith('GA'):
                    continue
                
                # Wenn Filter aktiv, prüfe ob dieser GA-Ordner verarbeitet werden soll
                if ga_filter:
                    folder_ga_match = re.match(r'GA(\d{2,3}[a-z]?)', folder_name.upper())
                    if folder_ga_match:
                        folder_ga_num = folder_ga_match.group(1).upper()
                        if folder_ga_num not in ga_filter:
                            continue  # Überspringe diesen GA-Ordner
                
                folder_had_changes = False
                
                # Schritt 1: Extrahiere Bilder aus PDF (falls vorhanden)
                extracted_images = extract_images_from_pdf(folder_path)
                if extracted_images > 0:
                    if not folder_had_changes:
                        print(f"\n{folder_name}:")
                        folder_had_changes = True
                    print(f"  PDF-Extraktion: {extracted_images} Bild(er) extrahiert")
                
                # Finde Markdown-Dateien
                md_files = [f for f in os.listdir(folder_path) 
                           if f.endswith('.md') and '(' in f and ')' in f]
                
                if not md_files:
                    continue
                
                for md_file in md_files:
                    md_path = os.path.join(folder_path, md_file)
                    
                    # Konvertiere JPEG-Bilder zu PNG
                    converted_images = convert_jpeg_to_png_files(md_path)
                    
                    # Korrigiere Bildreferenzen in Markdown
                    num_fixes, changes = fix_image_refs_in_file(md_path, apply_changes=True)
                    
                    if num_fixes > 0 or converted_images > 0:
                        if not folder_had_changes:
                            print(f"\n{folder_name}:")
                            folder_had_changes = True
                        
                        msg_parts = []
                        if converted_images > 0:
                            msg_parts.append(f"{converted_images} Bild(er) konvertiert")
                        if num_fixes > 0:
                            msg_parts.append(f"{num_fixes} Korrektur(en)")
                        
                        print(f"  {md_file}: {', '.join(msg_parts)}")
                        total_fixes += num_fixes
                        total_files += 1
            
            print(f"\n{'='*70}")
            print(f"Dateien mit Korrekturen: {total_files}")
            print(f"Gesamt-Korrekturen: {total_fixes}")
            
            if total_fixes > 0:
                print("Änderungen wurden angewendet!")
            else:
                print("Keine Korrekturen notwendig.")
            print(f"{'='*70}")
            
            self.steps_completed.append("Bildpfad-Korrektur")
            return True
            
        except Exception as e:
            print(f"\nFEHLER bei Bildpfad-Korrektur: {e}")
            self.steps_failed.append("Bildpfad-Korrektur")
            return False
    
    def step2_export_books(self, ga_numbers=None):
        """Schritt 2a: Bücher (GA001-GA050) exportieren"""
        # Prüfe ob Bücher exportiert werden sollen
        if ga_numbers:
            # Prüfe ob GA001-GA050 dabei sind (inklusive Varianten mit Suffix wie GA040a, GA041a)
            book_gas = []
            for ga in ga_numbers:
                # Unterstütze auch Suffixe wie "a", "b" etc.
                ga_match = re.match(r'GA(\d{2,3})([a-z])?', ga.upper())
                if ga_match:
                    ga_num = int(ga_match.group(1))
                    if 1 <= ga_num <= 50:
                        # Behalte Suffix falls vorhanden
                        ga_suffix = ga_match.group(2) or ''
                        ga_full = f"GA{ga_num:03d}{ga_suffix.lower()}"
                        book_gas.append(ga_full)
            
            if not book_gas:
                print("\nSCHRITT 2a ÜBERSPRUNGEN")
                print("   Keine Bücher (GA001-GA050) zum Exportieren")
                return True
        else:
            # Alle Bücher exportieren
            book_gas = None
        
        self.print_step(2, 4, "Bücher exportieren (GA001-GA050)")
        
        # Importiere BooksExporter aus export_books_master.py
        try:
            # Dynamischer Import um Zirkelimporte zu vermeiden
            import importlib.util
            books_exporter_path = os.path.join(self.project_root, 'export_books_master.py')
            spec = importlib.util.spec_from_file_location("export_books_master", books_exporter_path)
            books_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(books_module)
            
            exporter = books_module.BooksExporter()
            success = exporter.export_books(book_gas)
            
            if success:
                self.steps_completed.append("Bücher-Export")
            else:
                self.steps_failed.append("Bücher-Export")
            
            return success
            
        except Exception as e:
            print(f"\nFEHLER beim Bücher-Export: {e}")
            self.steps_failed.append("Bücher-Export")
            return False
    
    def step2_export_lectures(self, ga_bands=None):
        """Schritt 2b: Lectures (GA051+) aus Obsidian exportieren (mit Bildern)"""
        # Prüfe ob Vorträge exportiert werden sollen
        if ga_bands:
            # Prüfe ob GA051+ dabei sind
            lecture_gas = []
            for ga in ga_bands:
                ga_match = re.match(r'GA(\d{2,3})', ga.upper())
                if ga_match:
                    ga_num = int(ga_match.group(1))
                    if ga_num >= 51:
                        lecture_gas.append(ga)
            
            if not lecture_gas:
                print("\nSCHRITT 2b ÜBERSPRUNGEN")
                print("   Keine Vorträge (GA051+) zum Exportieren")
                return True
            
            ga_bands = lecture_gas
        # else: Alle Vorträge exportieren
        
        self.print_step(2, 4, "Lectures und Bilder exportieren (gesplittet)")
        
        if ga_bands:
            command = ["node", "export-lectures.js"] + ga_bands
            print(f"Exportiere GA-Baende: {', '.join(ga_bands)}\n")
        else:
            # Kompletter Export (ohne GA-Parameter = ALLE)
            command = ["node", "export-lectures.js"]
            print("Exportiere ALLE GA-Baende\n")
        
        return self.run_command(command, "Lecture-Export", shell=True)
    
    def step3_split_images(self):
        """Schritt 3: steiner-images.json in kleinere Dateien splitten"""
        # HINWEIS: Dieser Schritt ist nicht mehr notwendig, da export-lectures.js
        # bereits direkt gesplittete part-Dateien erstellt
        print("\nSCHRITT 3 ÜBERSPRUNGEN")
        print("   Bilder werden bereits von export-lectures.js gesplittet")
        self.steps_completed.append("Bilder-Split (automatisch)")
        return True
        
        # Legacy-Code (falls steiner-images.json manuell existiert)
        try:
            images_file = os.path.join(self.project_root, 'steiner-images.json')
            
            if not os.path.exists(images_file):
                return True
            
            # Lade Bilder
            with open(images_file, 'r', encoding='utf-8') as f:
                all_images_data = json.load(f)
            
            # Konvertiere zu Liste falls es ein Objekt ist
            if isinstance(all_images_data, dict):
                all_images = list(all_images_data.values())
            else:
                all_images = all_images_data
            
            total_size_mb = os.path.getsize(images_file) / (1024 * 1024)
            print(f"  Gesamt: {len(all_images)} Bilder ({total_size_mb:.2f} MB)")
            
            # Dynamisches Splitting
            MAX_SIZE_MB = 9.5
            chunks = []
            current_chunk = []
            
            for idx, img in enumerate(all_images):
                current_chunk.append(img)
                
                # Prüfe alle 5 Bilder die Größe
                if len(current_chunk) % 5 == 0 or idx == len(all_images) - 1:
                    test_json = json.dumps(current_chunk, ensure_ascii=False, indent=2)
                    size_mb = len(test_json.encode('utf-8')) / (1024 * 1024)
                    
                    # Wenn zu groß und mehr als 1 Bild, splitte
                    if size_mb > MAX_SIZE_MB and len(current_chunk) > 1:
                        last_img = current_chunk.pop()
                        chunks.append(current_chunk)
                        current_chunk = [last_img]
            
            # Letzten Chunk hinzufügen
            if current_chunk:
                chunks.append(current_chunk)
            
            # Speichere chunks
            print(f"  Erstelle {len(chunks)} part-Dateien...\n")
            
            for i, chunk in enumerate(chunks, 1):
                filename = f'steiner-images-part{i:02d}.json'
                filepath = os.path.join(self.project_root, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(chunk, f, ensure_ascii=False, indent=2)
                
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                print(f"  [{i:2d}] {filename}: {len(chunk)} Bilder ({size_mb:.2f} MB)")
            
            print(f"\n  [OK] {len(chunks)} part-Dateien erstellt")
            self.steps_completed.append("Bilder-Split")
            return True
            
        except Exception as e:
            print(f"\nFEHLER beim Bilder-Split: {e}")
            self.steps_failed.append("Bilder-Split")
            return False
    
    def step4_restart_server(self, restart=False):
        """Schritt 3: Server neu starten (optional)"""
        if not restart:
            print("\nSCHRITT 3 UEBERSPRUNGEN")
            print("   Server-Neustart mit --restart-server")
            return True
        
        self.print_step(3, 4, "Server neu starten")
        
        print("Stoppe laufenden Server (falls aktiv)...")
        
        # Versuche, laufende Node-Prozesse zu stoppen
        try:
            # Windows: Finde node.exe Prozesse die backend.js ausführen
            subprocess.run(
                'taskkill /F /FI "IMAGENAME eq node.exe" /FI "WINDOWTITLE eq backend.js*" 2>nul',
                shell=True,
                capture_output=True
            )
            time.sleep(1)
        except:
            pass
        
        print("Starte Server im Hintergrund...")
        
        # Starte Server im Hintergrund
        try:
            # Windows: Start in neuem Fenster
            subprocess.Popen(
                ["node", "backend.js"],
                cwd=self.project_root,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            
            print("Server gestartet!")
            print("   URL: http://localhost:3000")
            self.steps_completed.append("Server-Neustart")
            return True
            
        except Exception as e:
            print(f"Fehler beim Server-Start: {e}")
            print("   Bitte starten Sie den Server manuell: node backend.js")
            self.steps_failed.append("Server-Neustart")
            return False
    
    def print_summary(self, start_time, ga_bands=None):
        """Druckt finale Zusammenfassung"""
        duration = time.time() - start_time
        
        self.print_header("EXPORT ABGESCHLOSSEN")
        
        print(f"\nGesamtdauer: {duration:.1f} Sekunden\n")
        
        if ga_bands:
            print(f"Exportierte GA-Baende: {', '.join(ga_bands)}")
        else:
            print(f"Exportierte GA-Baende: ALLE")
        
        if self.steps_completed:
            print(f"\nErfolgreiche Schritte ({len(self.steps_completed)}):")
            for step in self.steps_completed:
                print(f"   + {step}")
        
        if self.steps_failed:
            print(f"\nFehlgeschlagene Schritte ({len(self.steps_failed)}):")
            for step in self.steps_failed:
                print(f"   - {step}")
        
        print("\n" + "=" * 70)
        
        if not self.steps_failed:
            print("\nALLES ERFOLGREICH!")
            print("\nNaechste Schritte:")
            print("   1. Browser oeffnen: http://localhost:3000")
            print("   2. Seite neu laden: F5 oder Strg+F5")
        else:
            print("\nEINIGE SCHRITTE SIND FEHLGESCHLAGEN")
            print("   Bitte pruefen Sie die Fehler oben.")
        
        print("=" * 70 + "\n")
    
    def export(self, ga_bands=None, options=None):
        """Hauptfunktion: Führt den kompletten Export aus"""
        options = options or {}
        
        skip_path_fix = options.get('skip_path_fix', False)
        restart_server = options.get('restart_server', False)
        
        # Start
        start_time = time.time()
        
        self.print_header("MASTER EXPORT - STEINER GA-SUCHE")
        
        print(f"\nProjekt: {self.project_root}")
        print(f"Steiner GA: {self.steiner_ga_dir}")
        
        if ga_bands:
            print(f"GA-Bände: {', '.join(ga_bands)}")
        else:
            print(f"GA-Bände: ALLE")
        
        print(f"\nOptionen:")
        print(f"  Bildpfad-Korrektur: {'NEIN' if skip_path_fix else 'JA'}")
        print(f"  Server-Neustart: {'JA' if restart_server else 'NEIN'}")
        
        # Schritt 1: Bildpfade korrigieren (nur für angegebene GA-Bände)
        if not self.step1_fix_image_paths(skip=skip_path_fix, ga_bands=ga_bands):
            print("\nWarnung: Bildpfad-Korrektur fehlgeschlagen")
            print("   Moechten Sie trotzdem fortfahren? (j/n): ", end='')
            response = input().lower()
            if response not in ['j', 'ja', 'y', 'yes']:
                print("\nExport abgebrochen.")
                return False
        
        # Schritt 2a: Bücher exportieren (GA001-GA050)
        if not self.step2_export_books(ga_bands):
            print("\nWarnung: Bücher-Export fehlgeschlagen!")
            print("   Export wird fortgesetzt...")
        
        # Schritt 2b: Lectures und Bilder exportieren (bereits gesplittet)
        if not self.step2_export_lectures(ga_bands):
            print("\nKRITISCHER FEHLER: Lecture-Export fehlgeschlagen!")
            print("   Export wird abgebrochen.")
            self.print_summary(start_time, ga_bands)
            return False
        
        # Schritt 3 (Legacy): Übersprungen - Bilder werden bereits von export-lectures.js gesplittet
        if not self.step3_split_images():
            print("\nWarnung: Bilder-Split fehlgeschlagen")
            print("   Export wird fortgesetzt...")
        
        # Schritt 3: Server neu starten (optional)
        self.step4_restart_server(restart=restart_server)
        
        # Finale Zusammenfassung
        self.print_summary(start_time, ga_bands)
        
        return len(self.steps_failed) == 0


def parse_arguments():
    """Parse Kommandozeilenargumente"""
    args = sys.argv[1:]
    
    ga_bands = []
    options = {
        'skip_path_fix': False,
        'restart_server': False
    }
    
    for arg in args:
        if arg.startswith('--'):
            # Optionen
            if arg == '--skip-path-fix':
                options['skip_path_fix'] = True
            elif arg == '--restart-server':
                options['restart_server'] = True
            elif arg == '--help' or arg == '-h':
                print(__doc__)
                sys.exit(0)
        else:
            # GA-Bände
            ga_bands.append(arg)
    
    return ga_bands if ga_bands else None, options


def main():
    """Hauptfunktion"""
    ga_bands, options = parse_arguments()
    
    master = ExportMaster()
    
    # Pruefe, ob Steiner_GA Ordner existiert
    if not os.path.exists(master.steiner_ga_dir):
        print("\n" + "=" * 70)
        print("FEHLER: Steiner_GA Ordner nicht gefunden!")
        print("=" * 70)
        print(f"Erwartet: {master.steiner_ga_dir}")
        print("\nBitte passen Sie den Pfad im Skript an (Zeile 42)")
        print("=" * 70 + "\n")
        sys.exit(1)
    
    # Führe Export aus
    success = master.export(ga_bands, options)
    
    # Exit Code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

