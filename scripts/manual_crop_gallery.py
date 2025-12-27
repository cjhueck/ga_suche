"""
Interaktive Galerie zum manuellen Croppen von Wandtafelzeichnungen.
Zeigt jedes Bild mit Slider für links/rechts/oben/unten Crop.
"""

from pathlib import Path
import base64
import json

# Pfade
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CHALKBOARDS_DIR = PROJECT_DIR / "chalkboards"
OUTPUT_FILE = PROJECT_DIR / "backups" / "manual_crop_gallery.html"

# Liste der zu bearbeitenden Bilder
IMAGES_TO_PROCESS = """
GA201/GA201-1920-04-17-T02.webp
GA206/GA206-1921-08-20-T01.webp
GA207/GA207-1921-09-24-T02.webp
GA214/GA214-1922-08-05-T01.webp
GA220/GA220-1923-01-27-T02.webp
GA229/GA229-1923-10-06-T01.webp
GA229/GA229-1923-10-06-T02.webp
GA230/GA230-1923-10-19-T01.webp
GA230/GA230-1923-10-26-T01.webp
GA230/GA230-1923-10-26-T02.webp
GA230/GA230-1923-11-02-T02.webp
GA230/GA230-1923-11-04-T01.webp
GA230/GA230-1923-11-10-T01.webp
GA235/GA235-1924-02-16-T01.webp
GA235/GA235-1924-02-16-T02.webp
GA235/GA235-1924-03-02-T02.webp
GA235/GA235-1924-03-08-T01.webp
GA235/GA235-1924-03-08-T03.webp
GA235/GA235-1924-03-22-T01.webp
GA237/GA237-1924-07-11-T01.webp
GA237/GA237-1924-08-01-T01.webp
GA237/GA237-1924-08-08-T01.webp
GA238/GA238-1924-09-10-T01.webp
GA279/GA279-1924-07-11-T01.webp
GA282/GA282-1924-09-13-T01.webp
GA291/GA291-1921-05-07-T01.webp
GA291/GA291-1921-05-07-T02.webp
GA291/GA291-1921-05-08-T01.webp
GA296/GA296-1919-08-10-T01.webp
GA296/GA296-1919-08-15-T01.webp
GA312/GA312-1920-03-21-T01.webp
GA312/GA312-1920-03-22-T01.webp
GA312/GA312-1920-03-23-T02.webp
GA312/GA312-1920-03-25-T01.webp
GA312/GA312-1920-03-25-T02.webp
GA312/GA312-1920-03-26-T01.webp
GA312/GA312-1920-03-27-T01.webp
GA312/GA312-1920-03-27-T02.webp
GA312/GA312-1920-03-28-T02.webp
GA312/GA312-1920-03-29-T01.webp
GA312/GA312-1920-03-30-T01.webp
GA312/GA312-1920-03-30-T02.webp
GA312/GA312-1920-03-31-T01.webp
GA312/GA312-1920-04-01-T01.webp
GA312/GA312-1920-04-01-T02.webp
GA312/GA312-1920-04-03-T01.webp
GA312/GA312-1920-04-03-T02.webp
GA312/GA312-1920-04-07-T01.webp
GA312/GA312-1920-04-07-T02.webp
GA312/GA312-1920-04-09-T02.webp
GA313/GA313-1921-04-11-T01.webp
GA313/GA313-1921-04-11-T02.webp
GA313/GA313-1921-04-13-T01.webp
GA313/GA313-1921-04-16-T01.webp
GA313/GA313-1921-04-17-T01.webp
GA313/GA313-1921-04-18-T01.webp
GA314/GA314-1920-10-09-T01.webp
GA314/GA314-1920-10-09-T03.webp
GA314/GA314-1924-04-22-T01.webp
GA315/GA315-1921-04-12-T01.webp
GA315/GA315-1921-04-14-T01.webp
GA315/GA315-1921-04-17-T01.webp
GA326/GA326-1923-01-03-T02.webp
GA340/GA340-1922-07-24-T01.webp
GA347/GA347-1922-09-20-T01.webp
GA353/GA353-1924-03-08-T02.webp
GA353/GA353-1924-06-04-T02.webp
""".strip().split('\n')


def create_gallery():
    """Erstellt eine interaktive HTML-Galerie zum manuellen Croppen."""
    
    images_data = []
    
    for rel_path in IMAGES_TO_PROCESS:
        rel_path = rel_path.strip()
        if not rel_path:
            continue
            
        img_path = CHALKBOARDS_DIR / rel_path
        if not img_path.exists():
            print(f"WARNUNG: Bild nicht gefunden: {img_path}")
            continue
        
        # Bild als Base64 einbetten
        with open(img_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')
        
        images_data.append({
            'path': rel_path,
            'data': f'data:image/webp;base64,{img_data}'
        })
    
    print(f"Verarbeite {len(images_data)} Bilder...")
    
    # HTML generieren
    html = f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Manuelles Cropping - Wandtafelzeichnungen</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            padding: 20px;
            background: #16213e;
            border-radius: 12px;
            margin-bottom: 20px;
        }}
        h1 {{ color: #e94560; margin-bottom: 10px; }}
        .progress {{
            font-size: 1.2em;
            color: #0f3460;
            background: #e94560;
            padding: 8px 20px;
            border-radius: 20px;
            display: inline-block;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .image-editor {{
            background: #16213e;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .image-title {{
            font-size: 1.1em;
            color: #e94560;
            margin-bottom: 15px;
        }}
        .editor-content {{
            display: flex;
            gap: 30px;
            align-items: flex-start;
        }}
        .image-preview {{
            flex: 1;
            position: relative;
            background: #333;
            border-radius: 8px;
            overflow: hidden;
        }}
        .image-preview img {{
            width: 100%;
            display: block;
        }}
        .crop-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
        }}
        .crop-left, .crop-right, .crop-top, .crop-bottom {{
            position: absolute;
            background: rgba(233, 69, 96, 0.5);
        }}
        .crop-left {{ left: 0; top: 0; bottom: 0; }}
        .crop-right {{ right: 0; top: 0; bottom: 0; }}
        .crop-top {{ top: 0; left: 0; right: 0; }}
        .crop-bottom {{ bottom: 0; left: 0; right: 0; }}
        .controls {{
            width: 300px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        .control-group {{
            background: #0f3460;
            padding: 12px;
            border-radius: 8px;
        }}
        .control-group label {{
            display: block;
            margin-bottom: 8px;
            color: #aaa;
        }}
        .control-group input[type="range"] {{
            width: 100%;
            cursor: pointer;
        }}
        .control-value {{
            text-align: right;
            color: #e94560;
            font-weight: bold;
        }}
        .buttons {{
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }}
        .btn {{
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.2s;
        }}
        .btn-skip {{
            background: #333;
            color: #888;
        }}
        .btn-skip:hover {{ background: #444; color: #aaa; }}
        .btn-apply {{
            background: #e94560;
            color: white;
        }}
        .btn-apply:hover {{ background: #ff6b6b; }}
        .btn-export {{
            background: #4CAF50;
            color: white;
            padding: 15px 30px;
            font-size: 1.2em;
        }}
        .btn-export:hover {{ background: #66BB6A; }}
        .export-section {{
            text-align: center;
            padding: 30px;
            background: #16213e;
            border-radius: 12px;
            margin-top: 20px;
        }}
        .hidden {{ display: none !important; }}
        .done {{
            opacity: 0.3;
            pointer-events: none;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 15px;
        }}
        .stat {{
            background: #0f3460;
            padding: 10px 20px;
            border-radius: 8px;
        }}
        .stat-value {{ color: #e94560; font-weight: bold; }}
        #cropData {{
            background: #0a0a15;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            font-family: monospace;
            font-size: 0.9em;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖼️ Manuelles Cropping</h1>
            <p>Stelle für jedes Bild den Crop-Bereich ein. Rot markierte Bereiche werden abgeschnitten.</p>
            <div class="progress">
                <span id="currentIndex">1</span> / <span id="totalImages">{len(images_data)}</span>
            </div>
            <div class="stats">
                <div class="stat">Bearbeitet: <span class="stat-value" id="processedCount">0</span></div>
                <div class="stat">Übersprungen: <span class="stat-value" id="skippedCount">0</span></div>
            </div>
        </div>
        
        <div id="editors"></div>
        
        <div class="export-section">
            <button class="btn btn-export" onclick="exportCropData()">📋 Crop-Daten exportieren</button>
            <div id="cropData" class="hidden"></div>
        </div>
    </div>
    
    <script>
        const images = {json.dumps(images_data)};
        let cropSettings = {{}};
        let processedCount = 0;
        let skippedCount = 0;
        
        function createEditor(img, index) {{
            const div = document.createElement('div');
            div.className = 'image-editor';
            div.id = `editor-${{index}}`;
            div.innerHTML = `
                <div class="image-title">${{index + 1}}. ${{img.path}}</div>
                <div class="editor-content">
                    <div class="image-preview" id="preview-${{index}}">
                        <img src="${{img.data}}" alt="${{img.path}}" onload="initOverlay(${{index}})">
                        <div class="crop-overlay" id="overlay-${{index}}">
                            <div class="crop-left" id="crop-left-${{index}}"></div>
                            <div class="crop-right" id="crop-right-${{index}}"></div>
                            <div class="crop-top" id="crop-top-${{index}}"></div>
                            <div class="crop-bottom" id="crop-bottom-${{index}}"></div>
                        </div>
                    </div>
                    <div class="controls">
                        <div class="control-group">
                            <label>Links abschneiden: <span class="control-value" id="val-left-${{index}}">0</span>px</label>
                            <input type="range" min="0" max="100" value="0" id="range-left-${{index}}" oninput="updateCrop(${{index}})">
                        </div>
                        <div class="control-group">
                            <label>Rechts abschneiden: <span class="control-value" id="val-right-${{index}}">0</span>px</label>
                            <input type="range" min="0" max="100" value="0" id="range-right-${{index}}" oninput="updateCrop(${{index}})">
                        </div>
                        <div class="control-group">
                            <label>Oben abschneiden: <span class="control-value" id="val-top-${{index}}">0</span>px</label>
                            <input type="range" min="0" max="100" value="0" id="range-top-${{index}}" oninput="updateCrop(${{index}})">
                        </div>
                        <div class="control-group">
                            <label>Unten abschneiden: <span class="control-value" id="val-bottom-${{index}}">0</span>px</label>
                            <input type="range" min="0" max="100" value="0" id="range-bottom-${{index}}" oninput="updateCrop(${{index}})">
                        </div>
                        <div class="buttons">
                            <button class="btn btn-skip" onclick="skipImage(${{index}})">⏭️ Überspringen</button>
                            <button class="btn btn-apply" onclick="applyImage(${{index}})">✅ Anwenden</button>
                        </div>
                    </div>
                </div>
            `;
            return div;
        }}
        
        function initOverlay(index) {{
            updateCrop(index);
        }}
        
        function updateCrop(index) {{
            const left = parseInt(document.getElementById(`range-left-${{index}}`).value);
            const right = parseInt(document.getElementById(`range-right-${{index}}`).value);
            const top = parseInt(document.getElementById(`range-top-${{index}}`).value);
            const bottom = parseInt(document.getElementById(`range-bottom-${{index}}`).value);
            
            document.getElementById(`val-left-${{index}}`).textContent = left;
            document.getElementById(`val-right-${{index}}`).textContent = right;
            document.getElementById(`val-top-${{index}}`).textContent = top;
            document.getElementById(`val-bottom-${{index}}`).textContent = bottom;
            
            const preview = document.getElementById(`preview-${{index}}`);
            const w = preview.offsetWidth;
            const h = preview.offsetHeight;
            
            document.getElementById(`crop-left-${{index}}`).style.width = `${{(left/100) * w}}px`;
            document.getElementById(`crop-right-${{index}}`).style.width = `${{(right/100) * w}}px`;
            document.getElementById(`crop-top-${{index}}`).style.height = `${{(top/100) * h}}px`;
            document.getElementById(`crop-bottom-${{index}}`).style.height = `${{(bottom/100) * h}}px`;
        }}
        
        function skipImage(index) {{
            document.getElementById(`editor-${{index}}`).classList.add('done');
            skippedCount++;
            document.getElementById('skippedCount').textContent = skippedCount;
            updateProgress(index);
        }}
        
        function applyImage(index) {{
            const left = parseInt(document.getElementById(`range-left-${{index}}`).value);
            const right = parseInt(document.getElementById(`range-right-${{index}}`).value);
            const top = parseInt(document.getElementById(`range-top-${{index}}`).value);
            const bottom = parseInt(document.getElementById(`range-bottom-${{index}}`).value);
            
            if (left > 0 || right > 0 || top > 0 || bottom > 0) {{
                cropSettings[images[index].path] = {{ left, right, top, bottom }};
            }}
            
            document.getElementById(`editor-${{index}}`).classList.add('done');
            processedCount++;
            document.getElementById('processedCount').textContent = processedCount;
            updateProgress(index);
        }}
        
        function updateProgress(index) {{
            document.getElementById('currentIndex').textContent = Math.min(index + 2, images.length);
        }}
        
        function exportCropData() {{
            const dataDiv = document.getElementById('cropData');
            dataDiv.classList.remove('hidden');
            
            const cropList = Object.entries(cropSettings).map(([path, crop]) => 
                `${{path}}: L=${{crop.left}}%, R=${{crop.right}}%, T=${{crop.top}}%, B=${{crop.bottom}}%`
            ).join('\\n');
            
            dataDiv.textContent = `Crop-Einstellungen (${{Object.keys(cropSettings).length}} Bilder):\\n\\n${{cropList || '(Keine Änderungen)'}}`
                + `\\n\\n--- JSON für Script ---\\n${{JSON.stringify(cropSettings, null, 2)}}`;
        }}
        
        // Editoren erstellen
        const container = document.getElementById('editors');
        images.forEach((img, i) => {{
            container.appendChild(createEditor(img, i));
        }});
        document.getElementById('totalImages').textContent = images.length;
    </script>
</body>
</html>'''
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\nGalerie erstellt: {OUTPUT_FILE}")
    print(f"{len(images_data)} Bilder zum manuellen Croppen")


if __name__ == '__main__':
    create_gallery()

