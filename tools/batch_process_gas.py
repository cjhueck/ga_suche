#!/usr/bin/env python3
"""
Batch-Verarbeitung von GA-Bänden für Seitenzahlen.

Verwendung:
  python tools/batch_process_gas.py 151 200
  python tools/batch_process_gas.py 151 200 --dry-run
"""
import subprocess
import sys
import io
import json
import shutil
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent.parent
PDF_DIR = SCRIPT_DIR / "Steiner_GA_pdf"
PAGEBREAK_DIR = SCRIPT_DIR / "pagebreak-books"


def find_pdf_for_ga(ga_num: int) -> bool:
    """Prüft ob ein PDF für die GA-Nummer existiert."""
    ga_str = str(ga_num).zfill(3)
    for pdf in PDF_DIR.glob("*.pdf"):
        name_lower = pdf.name.lower()
        if f"ga {ga_str}" in name_lower or f"ga{ga_str}" in name_lower:
            return True
        # Auch ohne führende Nullen
        if f"ga {ga_num}" in name_lower or f"ga {ga_num}," in name_lower:
            return True
    return False


def has_lectures_in_json(ga_num: int) -> bool:
    """Prüft ob Vorträge für die GA in den JSON-Dateien existieren."""
    ga_str = f"GA{str(ga_num).zfill(3)}"
    for json_file in SCRIPT_DIR.glob("steiner-full-lectures-*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for lec in data.get("lectures", []):
                if (lec.get("gaNumber") or "").upper() == ga_str:
                    return True
        except:
            pass
    return False


def run_command(cmd: list, description: str, timeout: int = 300) -> bool:
    """Führt einen Befehl aus und gibt Erfolg/Misserfolg zurück."""
    try:
        result = subprocess.run(
            cmd,
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        if result.returncode != 0:
            print(f"    ⚠️  {description} fehlgeschlagen")
            if result.stderr:
                print(f"       {result.stderr[:200]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"    ⚠️  {description} Timeout")
        return False
    except Exception as e:
        print(f"    ⚠️  {description} Fehler: {e}")
        return False


def process_ga(ga_num: int, dry_run: bool = False) -> dict:
    """Verarbeitet eine GA-Nummer."""
    ga_str = f"GA{str(ga_num).zfill(3)}"
    result = {"ga": ga_str, "status": "skipped", "reason": ""}
    
    # Prüfe ob PDF existiert
    if not find_pdf_for_ga(ga_num):
        result["reason"] = "Kein PDF"
        return result
    
    # Prüfe ob Vorträge in JSON existieren
    if not has_lectures_in_json(ga_num):
        result["reason"] = "Keine Vorträge in JSON"
        return result
    
    if dry_run:
        result["status"] = "would_process"
        return result
    
    print(f"  Verarbeite {ga_str}...")
    
    # 1. Seitenzahlen extrahieren
    if not run_command(
        [sys.executable, "export_page_markers_v4.py", ga_str],
        "Export",
        timeout=120
    ):
        result["status"] = "error"
        result["reason"] = "Export fehlgeschlagen"
        return result
    
    # 2. Mapping generieren
    if not run_command(
        [sys.executable, "generate_lecture_page_mapping.py", ga_str],
        "Mapping",
        timeout=180
    ):
        result["status"] = "error"
        result["reason"] = "Mapping fehlgeschlagen"
        return result
    
    # 3. Seitenzahlen anwenden
    if not run_command(
        [sys.executable, "apply_page_break_markers_v4.py", ga_str],
        "Apply",
        timeout=180
    ):
        result["status"] = "error"
        result["reason"] = "Apply fehlgeschlagen"
        return result
    
    # 4. Nach pagebreak-books kopieren
    output_file = SCRIPT_DIR / f"{ga_str}-with-pagebreaks.json"
    target_file = PAGEBREAK_DIR / f"{ga_str}.json"
    
    if output_file.exists():
        shutil.copy(output_file, target_file)
        result["status"] = "success"
    else:
        result["status"] = "error"
        result["reason"] = "Output-Datei nicht gefunden"
    
    return result


def main():
    if len(sys.argv) < 3:
        print("Verwendung: python tools/batch_process_gas.py START END [--dry-run]")
        print("Beispiel:   python tools/batch_process_gas.py 151 200")
        sys.exit(1)
    
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    dry_run = "--dry-run" in sys.argv
    
    print(f"\n{'='*60}")
    print(f"Batch-Verarbeitung GA{start:03d} bis GA{end:03d}")
    if dry_run:
        print("(Trockenlauf - keine Änderungen)")
    print(f"{'='*60}\n")
    
    results = {
        "success": [],
        "skipped": [],
        "error": []
    }
    
    for ga_num in range(start, end + 1):
        result = process_ga(ga_num, dry_run)
        
        if result["status"] == "success":
            results["success"].append(result["ga"])
            print(f"  ✓ {result['ga']}")
        elif result["status"] == "would_process":
            results["success"].append(result["ga"])
            print(f"  → {result['ga']} (würde verarbeitet)")
        elif result["status"] == "skipped":
            results["skipped"].append(f"{result['ga']}: {result['reason']}")
        else:
            results["error"].append(f"{result['ga']}: {result['reason']}")
            print(f"  ✗ {result['ga']}: {result['reason']}")
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print("Zusammenfassung")
    print(f"{'='*60}")
    print(f"  Erfolgreich: {len(results['success'])}")
    print(f"  Übersprungen: {len(results['skipped'])}")
    print(f"  Fehler: {len(results['error'])}")
    
    if results["error"]:
        print(f"\nFehler:")
        for e in results["error"]:
            print(f"  - {e}")
    
    # Server-Reload Hinweis
    if results["success"] and not dry_run:
        print(f"\n→ Server neu laden:")
        print(f"  Invoke-RestMethod -Uri 'http://localhost:3003/api/reload-books' -Method POST")


if __name__ == "__main__":
    main()

