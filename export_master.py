#!/usr/bin/env python3
"""
Master Export-Skript fuer Steiner GA-Suche
==========================================
Fuehrt den kompletten Export-Workflow automatisch aus:
1. Bildpfade in Obsidian korrigieren (optional)
   - Korrigiert fehlerhafte Markdown/Wiki-Links
   - Vereinfacht GA-Ordner-Pfade zu assets/...
   - Backup-Dateien werden automatisch erstellt
2. Lectures aus Obsidian exportieren (inkl. Bilder)
   - Exportiert Vortraege als JSON
   - Bilder werden in steiner-images.json exportiert
3. steiner-images.json splitten
   - Teilt grosse steiner-images.json in kleinere part-Dateien
   - Jede Datei < 10 MB (GitHub-kompatibel)
4. Server neu starten (optional)

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
    Bilder werden automatisch mit den Lectures exportiert.
    Separater Bilder-Export ist nicht mehr notwendig.
"""

import subprocess
import sys
import os
import re
import time
import json
from datetime import datetime
from pathlib import Path


# ============================================================================
# BILDPFAD-KORREKTUR FUNKTIONEN (Integriert)
# ============================================================================

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
        # ![text](assets/GA223-.../assets/223-T01.webp) → ![text](assets/223-T01.webp)
        pattern4 = r'(!\[[^\]]*\]\()assets/GA\d{3}[a-z]?-[^/]+/assets/([^)]+)\)'
        
        def replace4(match):
            prefix = match.group(1)
            filename = match.group(2)
            new_ref = f'{prefix}assets/{filename})'
            changes.append(f"  - Markdown-Pfad bereinigt: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern4, replace4, content)
        
        # Fix 5: Markdown-Links mit GA-Ordner am Anfang (Pattern 2: GA...)
        # ![text](GA145-Welche Bedeutung.../assets/img-0.jpeg) → ![text](assets/img-0.jpeg)
        # ![text](GA151-Der menschliche.../assets/img-2.jpeg) → ![text](assets/img-2.jpeg)
        pattern5 = r'(!\[[^\]]*\]\()GA\d{3}[a-z]?-[^/]+/assets/([^)]+)\)'
        
        def replace5(match):
            prefix = match.group(1)
            filename = match.group(2)
            new_ref = f'{prefix}assets/{filename})'
            changes.append(f"  - Markdown-Pfad vereinfacht: {match.group(0)} -> {new_ref}")
            return new_ref
        
        content = re.sub(pattern5, replace5, content)
        
        # Wende Änderungen an
        if changes and apply_changes:
            # Backup
            backup_path = filepath + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
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
        print(f"\n{'#' * 70}")
        print(f"  SCHRITT {step_num}/{total_steps}: {title}")
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
    
    def step1_fix_image_paths(self, skip=False):
        """Schritt 1: Bildpfade in Obsidian korrigieren"""
        if skip:
            print("\nSCHRITT 1 UEBERSPRUNGEN (--skip-path-fix)")
            return True
        
        self.print_step(1, 5, "Bildpfade in Obsidian korrigieren")
        
        try:
            total_files = 0
            total_fixes = 0
            
            # Durchlaufe alle GA-Ordner
            for folder_name in sorted(os.listdir(self.steiner_ga_dir)):
                folder_path = os.path.join(self.steiner_ga_dir, folder_name)
                
                if not os.path.isdir(folder_path) or not folder_name.startswith('GA'):
                    continue
                
                # Finde Markdown-Dateien
                md_files = [f for f in os.listdir(folder_path) 
                           if f.endswith('.md') and '(' in f and ')' in f]
                
                if not md_files:
                    continue
                
                folder_had_changes = False
                
                for md_file in md_files:
                    md_path = os.path.join(folder_path, md_file)
                    num_fixes, changes = fix_image_refs_in_file(md_path, apply_changes=True)
                    
                    if num_fixes > 0:
                        if not folder_had_changes:
                            print(f"\n{folder_name}:")
                            folder_had_changes = True
                        
                        print(f"  {md_file}: {num_fixes} Korrektur(en)")
                        total_fixes += num_fixes
                        total_files += 1
            
            print(f"\n{'='*70}")
            print(f"Dateien mit Korrekturen: {total_files}")
            print(f"Gesamt-Korrekturen: {total_fixes}")
            
            if total_fixes > 0:
                print(f"Backups erstellt: *.backup")
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
    
    def step2_export_lectures(self, ga_bands=None):
        """Schritt 2: Lectures aus Obsidian exportieren (mit Bildern)"""
        self.print_step(2, 4, "Lectures exportieren (inkl. Bilder)")
        
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
        self.print_step(3, 4, "Splitte steiner-images.json")
        
        try:
            images_file = os.path.join(self.project_root, 'steiner-images.json')
            
            if not os.path.exists(images_file):
                print("  steiner-images.json nicht gefunden, überspringe Split...")
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
        """Schritt 4: Server neu starten (optional)"""
        if not restart:
            print("\nSCHRITT 4 UEBERSPRUNGEN")
            print("   Server-Neustart mit --restart-server")
            return True
        
        self.print_step(4, 4, "Server neu starten")
        
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
        
        # Schritt 1: Bildpfade korrigieren
        if not self.step1_fix_image_paths(skip=skip_path_fix):
            print("\nWarnung: Bildpfad-Korrektur fehlgeschlagen")
            print("   Moechten Sie trotzdem fortfahren? (j/n): ", end='')
            response = input().lower()
            if response not in ['j', 'ja', 'y', 'yes']:
                print("\nExport abgebrochen.")
                return False
        
        # Schritt 2: Lectures exportieren (enthält Bilder-Export)
        if not self.step2_export_lectures(ga_bands):
            print("\nKRITISCHER FEHLER: Lecture-Export fehlgeschlagen!")
            print("   Export wird abgebrochen.")
            self.print_summary(start_time, ga_bands)
            return False
        
        # Schritt 3: steiner-images.json splitten
        if not self.step3_split_images():
            print("\nWarnung: Bilder-Split fehlgeschlagen")
            print("   Export wird fortgesetzt...")
        
        # Schritt 4: Server neu starten (optional)
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

