# -*- coding: utf-8 -*-
"""
Batch-Analyse von GA-Bänden - Vergleicht MD mit PDF und gibt Statistiken aus.
Verwendung: python batch_analyze.py GA051 GA052 GA053 ...
            python batch_analyze.py GA051-GA060  (Bereich)
            python batch_analyze.py --all  (alle verfügbaren)
            
Ausgabe wird in batch_analyze_results.txt gespeichert.
"""
import sys
import re
import io
from pathlib import Path
from datetime import datetime

# Importiere das Rekonstruktions-Tool
sys.path.insert(0, str(Path(__file__).parent))
from reconstruct_md_from_pdf import process_ga

# Unterdrücke detaillierte Ausgabe vom Rekonstruktions-Tool
class QuietMode:
    def __init__(self):
        self.original_stdout = sys.stdout
        self.captured = io.StringIO()
        
    def __enter__(self):
        sys.stdout = self.captured
        return self
        
    def __exit__(self, *args):
        sys.stdout = self.original_stdout
        
    def getvalue(self):
        return self.captured.getvalue()

def parse_ga_range(arg: str) -> list:
    """Parse GA-Bereich wie 'GA051-GA060' oder einzelne wie 'GA051'"""
    if '-' in arg and arg.count('-') == 1:
        # Bereich: GA051-GA060
        parts = arg.split('-')
        start = int(re.search(r'\d+', parts[0]).group())
        end = int(re.search(r'\d+', parts[1]).group())
        return [f"GA{i:03d}" for i in range(start, end + 1)]
    else:
        # Einzelner GA-Band
        return [arg.upper()]

def main():
    if len(sys.argv) < 2:
        print("Verwendung: python batch_analyze.py GA051 GA052 ...")
        print("            python batch_analyze.py GA051-GA060")
        sys.exit(1)
    
    # Parse Argumente
    ga_list = []
    quiet = '--quiet' in sys.argv or '-q' in sys.argv
    for arg in sys.argv[1:]:
        if arg.startswith('--') or arg == '-q':
            continue
        ga_list.extend(parse_ga_range(arg))
    
    # Entferne Duplikate und sortiere
    ga_list = sorted(set(ga_list), key=lambda x: int(re.search(r'\d+', x).group()))
    
    output_lines = []
    def log(msg):
        print(msg)
        output_lines.append(msg)
    
    log(f"Batch-Analyse gestartet: {datetime.now().strftime('%H:%M:%S')}")
    log(f"GA-Bände: {', '.join(ga_list)}")
    log("=" * 70)
    
    results = []
    
    for i, ga in enumerate(ga_list):
        log(f"\n[{i+1}/{len(ga_list)}] Verarbeite {ga}...")
        try:
            # Unterdrücke Detail-Ausgabe
            with QuietMode() as qm:
                result = process_ga(ga.replace('GA', '').lstrip('0') or '0', dry_run=True)
            
            if result and 'total_stats' in result:
                ts = result['total_stats']
                old_ids = ts.get('old_block_ids', 0)
                kept_ids = ts.get('matched_ids', 0)
                new_ids = ts.get('new_ids', 0)
                files = result.get('files_processed', 0)
                pct = (kept_ids / old_ids * 100) if old_ids > 0 else 0
                
                results.append({
                    'ga': ga,
                    'files': files,
                    'old_ids': old_ids,
                    'kept_ids': kept_ids,
                    'new_ids': new_ids,
                    'pct': pct
                })
                log(f"  ✓ {files} Dateien, Block-IDs: {kept_ids}/{old_ids} ({pct:.1f}%)")
            elif result and 'error' in result:
                log(f"  ✗ {result['error']}")
                results.append({'ga': ga, 'error': result['error']})
            else:
                log(f"  ✗ Keine Daten")
                results.append({'ga': ga, 'error': 'Keine Daten'})
        except Exception as e:
            log(f"  ✗ Fehler: {e}")
            results.append({'ga': ga, 'error': str(e)})
    
    # Zusammenfassung
    log("\n" + "=" * 70)
    log("ZUSAMMENFASSUNG")
    log("=" * 70)
    log(f"{'GA':<8} {'Dateien':>8} {'Alt':>8} {'Übern.':>8} {'Neu':>8} {'Match %':>10}")
    log("-" * 70)
    
    total_old = 0
    total_kept = 0
    total_new = 0
    total_files = 0
    
    for r in results:
        if 'error' in r:
            log(f"{r['ga']:<8} {'FEHLER':>8}")
        else:
            log(f"{r['ga']:<8} {r['files']:>8} {r['old_ids']:>8} {r['kept_ids']:>8} {r['new_ids']:>8} {r['pct']:>9.1f}%")
            total_old += r['old_ids']
            total_kept += r['kept_ids']
            total_new += r['new_ids']
            total_files += r['files']
    
    log("-" * 70)
    total_pct = (total_kept / total_old * 100) if total_old > 0 else 0
    log(f"{'GESAMT':<8} {total_files:>8} {total_old:>8} {total_kept:>8} {total_new:>8} {total_pct:>9.1f}%")
    log("=" * 70)
    log(f"Fertig: {datetime.now().strftime('%H:%M:%S')}")
    
    # Speichere Ergebnisse in Datei
    output_file = Path(__file__).parent.parent / "batch_analyze_results.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    print(f"\nErgebnisse gespeichert in: {output_file}")

if __name__ == "__main__":
    main()

