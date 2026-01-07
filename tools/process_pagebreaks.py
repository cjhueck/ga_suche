#!/usr/bin/env python3
"""
Komplettes Verfahren für Seitenumbrüche und Seitenzahlen

Führt alle Schritte automatisch durch:
1. PDF aus Steiner_GA_pdf/ in Steiner_GA/GAXXX-Titel/ kopieren
2. Seitenmarker mit apply_pagebreaks_from_pdf.py einfügen
3. Alte Override-Dateien in pagebreaks/ inaktivieren (.old)

Verwendung:
  python tools/process_pagebreaks.py GA061
  python tools/process_pagebreaks.py 61 67          # Bereich
  python tools/process_pagebreaks.py GA061 --dry-run  # Nur anzeigen
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Windows-Konsole UTF-8 Unterstützung
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

SCRIPT_DIR = Path(__file__).parent.parent
PDF_SOURCE_DIR = SCRIPT_DIR / "Steiner_GA_pdf"
GA_TARGET_DIR = SCRIPT_DIR / "Steiner_GA"
PAGEBREAKS_DIR = SCRIPT_DIR / "pagebreaks"
LECTURES_DIR = SCRIPT_DIR / "steiner-full-lectures"

# Import des Hauptscripts
sys.path.insert(0, str(SCRIPT_DIR / "tools"))
try:
    from apply_pagebreaks_from_pdf import (
        normalize_ga,
        find_pdf_for_ga,
        process_ga as apply_pagebreaks
    )
except ImportError:
    print("FEHLER: apply_pagebreaks_from_pdf.py nicht gefunden!")
    sys.exit(1)


def find_source_pdf(ga_number: str) -> Path | None:
    """Findet die PDF-Datei in Steiner_GA_pdf/."""
    m = re.search(r"(\d+)([a-z]?)", ga_number, re.IGNORECASE)
    if not m:
        return None
    
    ga_num = m.group(1).zfill(3)
    ga_suffix = m.group(2).lower() if m.group(2) else ""
    
    patterns = [
        f"ga {ga_num}{ga_suffix}",
        f"ga{ga_num}{ga_suffix}",
        f"ga {ga_num} {ga_suffix}" if ga_suffix else f"ga {ga_num}",
    ]
    
    for pdf in PDF_SOURCE_DIR.glob("*.pdf"):
        name_lower = pdf.name.lower()
        if "steiner" not in name_lower:
            continue
        
        for pattern in patterns:
            if pattern in name_lower.replace(",", " ").replace("  ", " "):
                return pdf
    
    return None


def find_target_folder(ga_number: str) -> Path | None:
    """Findet den Zielordner in Steiner_GA/."""
    m = re.search(r"(\d+)([a-z]?)", ga_number, re.IGNORECASE)
    if not m:
        return None
    
    ga_num = m.group(1).zfill(3)
    ga_suffix = m.group(2).lower() if m.group(2) else ""
    
    # Suche nach passendem Ordner
    pattern = f"GA{ga_num}{ga_suffix}-*" if ga_suffix else f"GA{ga_num}-*"
    
    for folder in GA_TARGET_DIR.glob(pattern):
        if folder.is_dir():
            return folder
    
    # Fallback: ohne Suffix
    if not ga_suffix:
        for folder in GA_TARGET_DIR.glob(f"GA{ga_num}*"):
            if folder.is_dir() and not re.search(r"GA\d{3}[a-z]", folder.name, re.IGNORECASE):
                return folder
    
    return None


def has_lectures(ga_number: str) -> bool:
    """Prüft ob Vorträge für die GA existieren."""
    ga_upper = ga_number.upper()
    
    for path in LECTURES_DIR.glob("steiner-full-lectures-*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for lec in data.get("lectures", []):
                if (lec.get("gaNumber") or "").upper() == ga_upper:
                    return True
        except:
            pass
    
    return False


def copy_pdf_to_ga_folder(ga_number: str, dry_run: bool = False) -> bool:
    """
    Schritt 1: Kopiert PDF von Steiner_GA_pdf/ nach Steiner_GA/GAXXX-Titel/
    """
    source_pdf = find_source_pdf(ga_number)
    if not source_pdf:
        print(f"    ⚠️  Keine PDF gefunden in Steiner_GA_pdf/")
        return False
    
    target_folder = find_target_folder(ga_number)
    if not target_folder:
        print(f"    ⚠️  Kein Zielordner gefunden in Steiner_GA/")
        return False
    
    target_pdf = target_folder / source_pdf.name
    
    if target_pdf.exists():
        print(f"    ✓ PDF bereits vorhanden: {target_folder.name}/")
        return True
    
    if dry_run:
        print(f"    → Würde kopieren: {source_pdf.name}")
        print(f"      Nach: {target_folder.name}/")
        return True
    
    try:
        shutil.copy2(source_pdf, target_pdf)
        print(f"    ✓ PDF kopiert: {source_pdf.name}")
        print(f"      Nach: {target_folder.name}/")
        return True
    except Exception as e:
        print(f"    ✗ Fehler beim Kopieren: {e}")
        return False


def deactivate_old_overrides(ga_number: str, dry_run: bool = False) -> bool:
    """
    Schritt 3: Benennt alte Override-Dateien in pagebreaks/ um (.old)
    """
    ga_norm = normalize_ga(ga_number)
    if not ga_norm:
        return False
    
    override_file = PAGEBREAKS_DIR / f"{ga_norm}.json"
    
    if not override_file.exists():
        print(f"    ✓ Keine alte Override-Datei vorhanden")
        return True
    
    # Generiere eindeutigen Namen mit Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    old_name = f"{ga_norm}.json.old_{timestamp}"
    old_file = PAGEBREAKS_DIR / old_name
    
    if dry_run:
        print(f"    → Würde umbenennen: {ga_norm}.json → {old_name}")
        return True
    
    try:
        override_file.rename(old_file)
        print(f"    ✓ Override inaktiviert: {ga_norm}.json → {old_name}")
        return True
    except Exception as e:
        print(f"    ✗ Fehler beim Umbenennen: {e}")
        return False


def process_ga_complete(ga_number: str, dry_run: bool = False) -> dict:
    """
    Führt das komplette Verfahren für eine GA durch:
    1. PDF kopieren
    2. Seitenmarker einfügen
    3. Alte Override-Dateien inaktivieren
    """
    ga_norm = normalize_ga(ga_number)
    if not ga_norm:
        return {"ga": ga_number, "status": "error", "reason": "Ungültige GA-Nummer"}
    
    print(f"\n{'='*60}")
    print(f"Verarbeite {ga_norm}")
    print(f"{'='*60}")
    
    # Prüfe ob Vorträge existieren
    if not has_lectures(ga_norm):
        print(f"  ⚠️  Keine Vorträge in steiner-full-lectures/ gefunden")
        return {"ga": ga_norm, "status": "skipped", "reason": "Keine Vorträge"}
    
    # Schritt 1: PDF kopieren
    print(f"\n  [1/3] PDF kopieren...")
    pdf_ok = copy_pdf_to_ga_folder(ga_norm, dry_run)
    
    # Schritt 2: Seitenmarker einfügen
    print(f"\n  [2/3] Seitenmarker einfügen...")
    if dry_run:
        print(f"    → Würde Marker einfügen mit apply_pagebreaks_from_pdf.py")
        markers_inserted = 0
    else:
        try:
            result = apply_pagebreaks(ga_norm, update_source=True)
            markers_inserted = result.get("markers_inserted", 0)
            if "error" in result:
                print(f"    ⚠️  {result['error']}")
        except Exception as e:
            print(f"    ✗ Fehler: {e}")
            markers_inserted = 0
    
    # Schritt 3: Alte Overrides inaktivieren
    print(f"\n  [3/3] Alte Override-Dateien inaktivieren...")
    override_ok = deactivate_old_overrides(ga_norm, dry_run)
    
    # Zusammenfassung
    print(f"\n  Ergebnis für {ga_norm}:")
    print(f"    - PDF: {'✓' if pdf_ok else '✗'}")
    print(f"    - Marker: {markers_inserted if not dry_run else '(dry-run)'}")
    print(f"    - Override: {'✓' if override_ok else '✗'}")
    
    return {
        "ga": ga_norm,
        "status": "success" if (pdf_ok or markers_inserted > 0) else "error",
        "markers_inserted": markers_inserted,
        "pdf_copied": pdf_ok,
        "override_deactivated": override_ok
    }


def main():
    parser = argparse.ArgumentParser(
        description="Komplettes Verfahren für Seitenumbrüche und Seitenzahlen",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python tools/process_pagebreaks.py GA061
  python tools/process_pagebreaks.py 61 67
  python tools/process_pagebreaks.py GA061 --dry-run

Das Script führt automatisch durch:
  1. PDF aus Steiner_GA_pdf/ in Steiner_GA/GAXXX-Titel/ kopieren
  2. Seitenmarker mit apply_pagebreaks_from_pdf.py einfügen
  3. Alte Override-Dateien in pagebreaks/ inaktivieren

Nach Abschluss: Server neu starten (nb)
        """
    )
    parser.add_argument("ga", nargs="+", help="GA-Nummer(n) oder Bereich (z.B. 61 67)")
    parser.add_argument("--dry-run", action="store_true", 
                        help="Nur anzeigen, keine Änderungen")
    
    args = parser.parse_args()
    
    # Bestimme GA-Nummern
    ga_numbers = []
    
    if len(args.ga) == 2 and args.ga[0].isdigit() and args.ga[1].isdigit():
        # Bereich
        start = int(args.ga[0])
        end = int(args.ga[1])
        ga_numbers = [f"GA{i:03d}" for i in range(start, end + 1)]
    else:
        # Einzelne GAs
        for ga in args.ga:
            ga_norm = normalize_ga(ga)
            if ga_norm:
                ga_numbers.append(ga_norm)
    
    if not ga_numbers:
        print("Keine gültigen GA-Nummern angegeben")
        sys.exit(1)
    
    print(f"\n{'#'*60}")
    print(f"# SEITENUMBRÜCHE VERARBEITEN")
    print(f"# GAs: {', '.join(ga_numbers)}")
    if args.dry_run:
        print(f"# MODUS: Trockenlauf (keine Änderungen)")
    print(f"{'#'*60}")
    
    # Verarbeite alle GAs
    results = []
    for ga in ga_numbers:
        result = process_ga_complete(ga, dry_run=args.dry_run)
        results.append(result)
    
    # Gesamtzusammenfassung
    print(f"\n{'='*60}")
    print("GESAMTZUSAMMENFASSUNG")
    print(f"{'='*60}")
    
    success = [r for r in results if r["status"] == "success"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors = [r for r in results if r["status"] == "error"]
    
    print(f"  Erfolgreich: {len(success)}")
    print(f"  Übersprungen: {len(skipped)}")
    print(f"  Fehler: {len(errors)}")
    
    total_markers = sum(r.get("markers_inserted", 0) for r in results)
    print(f"\n  Gesamt Marker eingefügt: {total_markers}")
    
    if errors:
        print(f"\n  Fehler bei:")
        for r in errors:
            print(f"    - {r['ga']}: {r.get('reason', 'Unbekannt')}")
    
    if skipped:
        print(f"\n  Übersprungen:")
        for r in skipped:
            print(f"    - {r['ga']}: {r.get('reason', 'Unbekannt')}")
    
    if success and not args.dry_run:
        print(f"\n{'='*60}")
        print("WICHTIG: Server neu starten!")
        print(f"{'='*60}")
        print("  Im Server-Terminal: Ctrl+C, dann: nb")


if __name__ == "__main__":
    main()

