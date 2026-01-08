#!/usr/bin/env python3
"""
Komplettes Verfahren für Seitenumbrüche und Seitenzahlen

Führt alle Schritte automatisch durch:
1. PDF aus Steiner_GA_pdf/ in Steiner_GA/GAXXX-Titel/ kopieren
2. Seitenmarker in JSON einfügen (apply_pagebreaks_from_pdf.py)
3. Alte Override-Dateien in pagebreaks/ inaktivieren (.old)
4. Seitenmarker in MD-Dateien einfügen (apply_pagebreaks_to_md.py)

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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Tuple

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

try:
    from apply_pagebreaks_to_md import process_ga_md as apply_pagebreaks_md
except ImportError:
    apply_pagebreaks_md = None
    print("WARNUNG: apply_pagebreaks_to_md.py nicht gefunden - MD wird nicht aktualisiert")


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


BOOKS_DIR = SCRIPT_DIR / "steiner-books"


def has_books(ga_number: str) -> bool:
    """Prüft ob ein Buch für die GA existiert."""
    ga_upper = ga_number.upper()
    
    for path in BOOKS_DIR.glob("steiner-books-*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for book in data.get("books", []):
                if (book.get("gaNumber") or "").upper() == ga_upper:
                    return True
        except:
            pass
    
    return False


def has_content(ga_number: str) -> Tuple[bool, str]:
    """
    Prüft ob Inhalte (Vorträge oder Bücher) für die GA existieren.
    Rückgabe: (exists, type) wobei type 'lectures', 'book' oder '' ist.
    """
    if has_lectures(ga_number):
        return True, "lectures"
    if has_books(ga_number):
        return True, "book"
    return False, ""


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
    2. Seitenmarker in JSON einfügen
    3. Alte Override-Dateien inaktivieren
    4. Seitenmarker in MD-Dateien einfügen
    """
    ga_norm = normalize_ga(ga_number)
    if not ga_norm:
        return {"ga": ga_number, "status": "error", "reason": "Ungültige GA-Nummer"}
    
    print(f"\n{'='*60}")
    print(f"Verarbeite {ga_norm}")
    print(f"{'='*60}")
    
    # Prüfe ob Vorträge oder Bücher existieren
    content_exists, content_type = has_content(ga_norm)
    if not content_exists:
        print(f"  ⚠️  Keine Vorträge/Bücher gefunden")
        return {"ga": ga_norm, "status": "skipped", "reason": "Keine Inhalte"}
    
    print(f"  Typ: {content_type}")
    
    # Schritt 1: PDF kopieren
    print(f"\n  [1/4] PDF kopieren...")
    pdf_ok = copy_pdf_to_ga_folder(ga_norm, dry_run)
    
    # Schritt 2: Seitenmarker in JSON einfügen
    print(f"\n  [2/4] Seitenmarker in JSON einfügen...")
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
    print(f"\n  [3/4] Alte Override-Dateien inaktivieren...")
    override_ok = deactivate_old_overrides(ga_norm, dry_run)
    
    # Schritt 4: Seitenmarker in MD-Dateien einfügen
    print(f"\n  [4/4] Seitenmarker in MD-Dateien einfügen...")
    md_markers_inserted = 0
    if apply_pagebreaks_md is None:
        print(f"    ⚠️  apply_pagebreaks_to_md.py nicht verfügbar")
        md_ok = False
    elif dry_run:
        print(f"    → Würde Marker in MD-Dateien einfügen")
        md_ok = True
    else:
        try:
            md_result = apply_pagebreaks_md(ga_norm, dry_run=False)
            md_markers_inserted = md_result.get("markers_inserted", 0)
            if "error" in md_result:
                print(f"    ⚠️  {md_result['error']}")
                md_ok = False
            else:
                md_ok = True
        except Exception as e:
            print(f"    ✗ Fehler: {e}")
            md_ok = False
    
    # Zusammenfassung
    print(f"\n  Ergebnis für {ga_norm}:")
    print(f"    - PDF: {'✓' if pdf_ok else '✗'}")
    print(f"    - JSON-Marker: {markers_inserted if not dry_run else '(dry-run)'}")
    print(f"    - Override: {'✓' if override_ok else '✗'}")
    print(f"    - MD-Marker: {md_markers_inserted if not dry_run else '(dry-run)'}")
    
    return {
        "ga": ga_norm,
        "status": "success" if (pdf_ok or markers_inserted > 0 or md_markers_inserted > 0) else "error",
        "markers_inserted": markers_inserted,
        "md_markers_inserted": md_markers_inserted,
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
  2. Seitenmarker in JSON einfügen (apply_pagebreaks_from_pdf.py)
  3. Alte Override-Dateien in pagebreaks/ inaktivieren
  4. Seitenmarker in MD-Dateien einfügen (apply_pagebreaks_to_md.py)

Nach Abschluss: Server neu starten (nb)
        """
    )
    parser.add_argument("ga", nargs="+", help="GA-Nummer(n) oder Bereich (z.B. 61 67)")
    parser.add_argument("--dry-run", action="store_true", 
                        help="Nur anzeigen, keine Änderungen")
    parser.add_argument("--workers", "-w", type=int, default=4,
                        help="Anzahl paralleler Prozesse (Standard: 4)")
    parser.add_argument("--sequential", "-s", action="store_true",
                        help="Sequentielle Verarbeitung (kein Parallelismus)")
    
    args = parser.parse_args()
    
    # Bestimme GA-Nummern
    ga_numbers = []
    
    i = 0
    while i < len(args.ga):
        # Prüfe auf Bereich: zwei aufeinanderfolgende Zahlen
        if (i + 1 < len(args.ga) and 
            args.ga[i].isdigit() and 
            args.ga[i+1].isdigit() and
            int(args.ga[i]) < int(args.ga[i+1])):
            # Bereich erkannt
            start = int(args.ga[i])
            end = int(args.ga[i+1])
            for n in range(start, end + 1):
                ga_numbers.append(f"GA{n:03d}")
            i += 2
        else:
            # Einzelne GA
            ga_norm = normalize_ga(args.ga[i])
            if ga_norm:
                ga_numbers.append(ga_norm)
            i += 1
    
    # Duplikate entfernen, Reihenfolge beibehalten
    seen = set()
    ga_numbers = [x for x in ga_numbers if not (x in seen or seen.add(x))]
    
    if not ga_numbers:
        print("Keine gültigen GA-Nummern angegeben")
        sys.exit(1)
    
    print(f"\n{'#'*60}")
    print(f"# SEITENUMBRÜCHE VERARBEITEN")
    print(f"# GAs: {', '.join(ga_numbers)}")
    if args.dry_run:
        print(f"# MODUS: Trockenlauf (keine Änderungen)")
    if not args.sequential:
        print(f"# PARALLEL: {args.workers} Worker")
    print(f"{'#'*60}")
    
    # Verarbeite alle GAs
    results = []
    
    if args.sequential or len(ga_numbers) == 1:
        # Sequentielle Verarbeitung
        for ga in ga_numbers:
            result = process_ga_complete(ga, dry_run=args.dry_run)
            results.append(result)
    else:
        # Parallele Verarbeitung (Threads statt Prozesse für Windows-Kompatibilität)
        print(f"\nStarte parallele Verarbeitung mit {args.workers} Threads...")
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(process_ga_complete, ga, args.dry_run): ga 
                for ga in ga_numbers
            }
            for future in as_completed(futures):
                ga = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    status = result.get("status", "?")
                    markers = result.get("markers_inserted", 0) + result.get("md_markers_inserted", 0)
                    print(f"  ✓ {ga}: {status} ({markers} Marker)")
                except Exception as e:
                    print(f"  ✗ {ga}: Fehler - {e}")
                    results.append({"ga": ga, "status": "error", "reason": str(e)})
    
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
    total_md_markers = sum(r.get("md_markers_inserted", 0) for r in results)
    print(f"\n  Gesamt JSON-Marker eingefügt: {total_markers}")
    print(f"  Gesamt MD-Marker eingefügt: {total_md_markers}")
    
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

