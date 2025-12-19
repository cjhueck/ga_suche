#!/usr/bin/env python3
"""
Export Pagebreak-Marker zu HTML

Generiert eine HTML-Datei mit den Pagebreak-Markern und Seitenzahlen für einen GA-Band.
"""

import json
import sys
import io
from pathlib import Path

# Windows-Konsole UTF-8 Unterstützung
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent
MARKERS_FILE = SCRIPT_DIR / "page-break-markers.json"

def normalize_ga(ga_number: str) -> str:
    """Normalisiert GA-Nummer zu GA### Format"""
    import re
    ga_number = ga_number.upper().strip()
    if not ga_number.startswith("GA"):
        ga_number = "GA" + ga_number
    # Stelle sicher, dass es 3-stellig ist
    match = re.match(r"GA(\d+)", ga_number)
    if match:
        num = match.group(1)
        return f"GA{num.zfill(3)}"
    return ga_number

def export_to_html(ga_number: str) -> str:
    """Exportiert Pagebreak-Marker für einen GA-Band zu HTML"""
    
    # Lade Marker-Datenbank
    if not MARKERS_FILE.exists():
        print(f"FEHLER: {MARKERS_FILE} nicht gefunden")
        return None
    
    with open(MARKERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    ga_norm = ga_number.upper()
    if not ga_norm.startswith("GA"):
        ga_norm = "GA" + ga_norm
    
    # Stelle sicher, dass es 3-stellig ist
    import re
    match = re.match(r"GA(\d+)", ga_norm)
    if match:
        num = match.group(1)
        ga_norm = f"GA{num.zfill(3)}"
    
    ga_data = data.get(ga_norm)
    if not ga_data:
        print(f"FEHLER: Keine Daten für {ga_norm} gefunden")
        return None
    
    title = ga_data.get("title", ga_norm)
    pdf_source = ga_data.get("pdfSource", "")
    pdf_page_count = ga_data.get("pdfPageCount", 0)
    breaks = ga_data.get("breaks", [])
    content_range = ga_data.get("contentRange", [1, 10000])
    
    # HTML generieren
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pagebreak-Marker: {ga_norm} - {title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #467886;
            border-bottom: 2px solid #467886;
            padding-bottom: 10px;
        }}
        .info {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .info p {{
            margin: 5px 0;
        }}
        .break-item {{
            margin-bottom: 20px;
            padding: 15px;
            border-left: 4px solid #467886;
            background: #fafafa;
            border-radius: 3px;
        }}
        .break-header {{
            font-weight: bold;
            color: #467886;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .page-number {{
            display: inline-block;
            background: #467886;
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-weight: bold;
            margin-right: 10px;
        }}
        .text-preview {{
            font-family: 'Courier New', monospace;
            background: white;
            padding: 10px;
            border-radius: 3px;
            margin-top: 8px;
            font-size: 0.9em;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .left-text {{
            color: #666;
        }}
        .right-text {{
            color: #333;
        }}
        .confidence {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.85em;
            margin-left: 10px;
        }}
        .confidence.extracted {{
            background: #d4edda;
            color: #155724;
        }}
        .confidence.interpolated {{
            background: #fff3cd;
            color: #856404;
        }}
        .first-page {{
            background: #e7f3ff;
            border-left-color: #0066cc;
        }}
        .pdf-info {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>{ga_norm}: {title}</h1>
    
    <div class="info">
        <p><strong>PDF-Quelle:</strong> {pdf_source}</p>
        <p><strong>PDF-Seiten:</strong> {pdf_page_count}</p>
        <p><strong>Content-Bereich:</strong> Seite {content_range[0]} - {content_range[1]}</p>
        <p><strong>Anzahl Breaks:</strong> {len(breaks)}</p>
    </div>
    
    <h2>Pagebreak-Marker</h2>
"""
    
    for i, break_item in enumerate(breaks):
        page = break_item.get("page", "?")
        pdf_from = break_item.get("pdfFrom")
        pdf_to = break_item.get("pdfTo")
        left = break_item.get("left", "")
        right = break_item.get("right", "")
        hyphenated = break_item.get("hyphenated", False)
        confidence = break_item.get("printedPageConfidence", "unknown")
        is_first = break_item.get("isFirstPage", False)
        
        pdf_info = ""
        if pdf_from is not None and pdf_to is not None:
            pdf_info = f"PDF-Seiten: {pdf_from} → {pdf_to}"
        elif pdf_to is not None:
            pdf_info = f"PDF-Seite: {pdf_to}"
        
        confidence_class = "extracted" if confidence == "extracted" else "interpolated"
        first_class = " first-page" if is_first else ""
        
        html += f"""
    <div class="break-item{first_class}">
        <div class="break-header">
            <span class="page-number">Seite {page}</span>
            <span class="confidence {confidence_class}">{confidence}</span>
            {f'<span class="pdf-info">({pdf_info})</span>' if pdf_info else ''}
            {f'<span style="color: #d9534f;">[Erste Seite]</span>' if is_first else ''}
            {f'<span style="color: #856404;">[Getrenntes Wort]</span>' if hyphenated else ''}
        </div>
"""
        
        if left:
            html += f"""
        <div class="text-preview left-text">
            <strong>Vorher (left):</strong> {left[:300]}{'...' if len(left) > 300 else ''}
        </div>
"""
        
        if right:
            html += f"""
        <div class="text-preview right-text">
            <strong>Nachher (right):</strong> {right[:300]}{'...' if len(right) > 300 else ''}
        </div>
"""
        
        html += "    </div>\n"
    
    html += """
</body>
</html>
"""
    
    return html

def main():
    if len(sys.argv) < 2:
        print("Export Pagebreak-Marker zu HTML")
        print("Verwendung:")
        print("  python export_pagebreaks_to_html.py GA200")
        sys.exit(1)
    
    ga_number = sys.argv[1]
    html = export_to_html(ga_number)
    
    if html:
        output_file = SCRIPT_DIR / f"pagebreaks-{ga_number.upper()}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"OK: HTML exportiert: {output_file}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()




