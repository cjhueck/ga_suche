#!/usr/bin/env python3
"""
Master Export-Skript fuer Steiner GA-Suche
==========================================
Fuehrt den kompletten Export-Workflow automatisch aus:
1. Bildpfade in Obsidian korrigieren (optional)
2. JPEG zu PNG Konvertierung (optional)
3. Lectures aus Obsidian exportieren
4. Bilder in steiner-images.json exportieren
5. Server neu starten (optional)

Verwendung:
    python export_master.py                      # Kompletter Export (ALLE GA-Baende)
    python export_master.py GA112-GA117a         # Nur bestimmte GA-Baende
    python export_master.py --skip-path-fix      # Bildpfad-Korrektur ueberspringen
    python export_master.py --skip-conversion    # JPEG-Konvertierung ueberspringen
    python export_master.py --restart-server     # Server automatisch neu starten
    
Beispiele:
    python export_master.py GA089                # Nur GA089
    python export_master.py GA112-GA117a --restart-server
    python export_master.py --skip-path-fix --skip-conversion
"""

import subprocess
import sys
import os
import time
from datetime import datetime
from pathlib import Path

class ExportMaster:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.steiner_ga_dir = r"C:\Users\chuec\OneDrive\GitHub\Steiner_GA"
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
        
        command = [sys.executable, "fix_obsidian_image_paths.py", "--apply"]
        return self.run_command(command, "Bildpfad-Korrektur")
    
    def step2_convert_jpegs(self, skip=False):
        """Schritt 2: JPEGs zu PNGs konvertieren"""
        if skip:
            print("\nSCHRITT 2 UEBERSPRUNGEN (--skip-conversion)")
            return True
        
        self.print_step(2, 5, "JPEG zu PNG Konvertierung")
        
        # Verwende das integrierte Skript, aber mit subprocess für JPEG-Konvertierung
        # Alternativ: rufe convert_all_jpegs_to_png.py direkt auf
        command = [sys.executable, "convert_all_jpegs_to_png.py"]
        return self.run_command(command, "JPEG-Konvertierung")
    
    def step3_export_lectures(self, ga_bands=None):
        """Schritt 3: Lectures aus Obsidian exportieren"""
        self.print_step(3, 5, "Lectures exportieren")
        
        if ga_bands:
            command = ["node", "export-lectures.js"] + ga_bands
            print(f"Exportiere GA-Baende: {', '.join(ga_bands)}\n")
        else:
            # Kompletter Export (ohne GA-Parameter = ALLE)
            command = ["node", "export-lectures.js"]
            print("Exportiere ALLE GA-Baende\n")
        
        return self.run_command(command, "Lecture-Export", shell=True)
    
    def step4_export_images(self):
        """Schritt 4: Bilder in steiner-images.json exportieren"""
        self.print_step(4, 5, "Bilder exportieren")
        
        # Verwende das Python-Skript nur für den Export (ohne Konvertierung)
        command = [sys.executable, "export_steiner_images_integrated.py", "--skip-conversion"]
        return self.run_command(command, "Bilder-Export")
    
    def step5_restart_server(self, restart=False):
        """Schritt 5: Server neu starten (optional)"""
        if not restart:
            print("\nSCHRITT 5 UEBERSPRUNGEN")
            print("   Server-Neustart mit --restart-server")
            return True
        
        self.print_step(5, 5, "Server neu starten")
        
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
        skip_conversion = options.get('skip_conversion', False)
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
        print(f"  JPEG-Konvertierung: {'NEIN' if skip_conversion else 'JA'}")
        print(f"  Server-Neustart: {'JA' if restart_server else 'NEIN'}")
        
        # Schritt 1: Bildpfade korrigieren
        if not self.step1_fix_image_paths(skip=skip_path_fix):
            print("\nWarnung: Bildpfad-Korrektur fehlgeschlagen")
            print("   Moechten Sie trotzdem fortfahren? (j/n): ", end='')
            response = input().lower()
            if response not in ['j', 'ja', 'y', 'yes']:
                print("\nExport abgebrochen.")
                return False
        
        # Schritt 2: JPEG-Konvertierung
        if not self.step2_convert_jpegs(skip=skip_conversion):
            print("\nWarnung: JPEG-Konvertierung fehlgeschlagen")
            print("   Moechten Sie trotzdem fortfahren? (j/n): ", end='')
            response = input().lower()
            if response not in ['j', 'ja', 'y', 'yes']:
                print("\nExport abgebrochen.")
                return False
        
        # Schritt 3: Lectures exportieren
        if not self.step3_export_lectures(ga_bands):
            print("\nKRITISCHER FEHLER: Lecture-Export fehlgeschlagen!")
            print("   Export wird abgebrochen.")
            self.print_summary(start_time, ga_bands)
            return False
        
        # Schritt 4: Bilder exportieren
        if not self.step4_export_images():
            print("\nKRITISCHER FEHLER: Bilder-Export fehlgeschlagen!")
            print("   Export wird abgebrochen.")
            self.print_summary(start_time, ga_bands)
            return False
        
        # Schritt 5: Server neu starten (optional)
        self.step5_restart_server(restart=restart_server)
        
        # Finale Zusammenfassung
        self.print_summary(start_time, ga_bands)
        
        return len(self.steps_failed) == 0


def parse_arguments():
    """Parse Kommandozeilenargumente"""
    args = sys.argv[1:]
    
    ga_bands = []
    options = {
        'skip_path_fix': False,
        'skip_conversion': False,
        'restart_server': False
    }
    
    for arg in args:
        if arg.startswith('--'):
            # Optionen
            if arg == '--skip-path-fix':
                options['skip_path_fix'] = True
            elif arg == '--skip-conversion':
                options['skip_conversion'] = True
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

