#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erstellt eine HTML-Galerie zur Überprüfung der hellen Bilder.
Bilder können angeklickt werden um sie zu bestätigen.
"""

from pathlib import Path
import json

PROJECT_DIR = Path(__file__).parent.parent
SOURCE_DIR = PROJECT_DIR / "Steiner_GA" / "chalkboards"
OUTPUT_HTML = PROJECT_DIR / "backups" / "review_bright_images.html"

# Liste der hellen Bilder (aus dem letzten Lauf)
BRIGHT_IMAGES = [
    "GA201/GA201-1920-04-17-T02.webp",
    "GA201/GA201-1920-04-18-T01.webp",
    "GA206/GA206-1921-08-20-T01.webp",
    "GA207/GA207-1921-09-24-T02.webp",
    "GA214/GA214-1922-08-05-T01.webp",
    "GA220/GA220-1923-01-27-T02.webp",
    "GA229/GA229-1923-10-06-T01.webp",
    "GA229/GA229-1923-10-06-T02.webp",
    "GA229/GA229-1923-10-12-T01.webp",
    "GA230/GA230-1923-10-19-T01.webp",
    "GA230/GA230-1923-10-20-T01.webp",
    "GA230/GA230-1923-10-26-T01.webp",
    "GA230/GA230-1923-10-26-T02.webp",
    "GA230/GA230-1923-11-02-T02.webp",
    "GA230/GA230-1923-11-04-T01.webp",
    "GA230/GA230-1923-11-04-T02.webp",
    "GA230/GA230-1923-11-09-T02.webp",
    "GA230/GA230-1923-11-10-T01.webp",
    "GA235/GA235-1924-02-16-T01.webp",
    "GA235/GA235-1924-02-16-T02.webp",
    "GA235/GA235-1924-02-17-T02.webp",
    "GA235/GA235-1924-03-02-T02.webp",
    "GA235/GA235-1924-03-08-T01.webp",
    "GA235/GA235-1924-03-08-T02.webp",
    "GA235/GA235-1924-03-08-T03.webp",
    "GA235/GA235-1924-03-22-T01.webp",
    "GA236/GA236-1924-05-09-T02.webp",
    "GA237/GA237-1924-07-04-T02.webp",
    "GA237/GA237-1924-07-11-T01.webp",
    "GA237/GA237-1924-08-01-T01.webp",
    "GA237/GA237-1924-08-08-T01.webp",
    "GA237/GA237-1924-08-08-T02.webp",
    "GA238/GA238-1924-09-10-T01.webp",
    "GA240/GA240-1924-08-24-T01.webp",
    "GA279/GA279-1924-07-11-T01.webp",
    "GA282/GA282-1924-09-13-T01.webp",
    "GA291/GA291-1921-05-07-T01.webp",
    "GA291/GA291-1921-05-07-T02.webp",
    "GA291/GA291-1921-05-08-T01.webp",
    "GA291/GA291-1921-05-08-T02.webp",
    "GA296/GA296-1919-08-10-T01.webp",
    "GA296/GA296-1919-08-15-T01.webp",
    "GA306/GA306-1923-04-16-T01.webp",
    "GA312/GA312-1920-03-21-T01.webp",
    "GA312/GA312-1920-03-21-T02.webp",
    "GA312/GA312-1920-03-22-T01.webp",
    "GA312/GA312-1920-03-23-T02.webp",
    "GA312/GA312-1920-03-25-T01.webp",
    "GA312/GA312-1920-03-25-T02.webp",
    "GA312/GA312-1920-03-26-T01.webp",
    "GA312/GA312-1920-03-26-T02.webp",
    "GA312/GA312-1920-03-27-T01.webp",
    "GA312/GA312-1920-03-27-T02.webp",
    "GA312/GA312-1920-03-28-T02.webp",
    "GA312/GA312-1920-03-29-T01.webp",
    "GA312/GA312-1920-03-30-T01.webp",
    "GA312/GA312-1920-03-30-T02.webp",
    "GA312/GA312-1920-03-31-T01.webp",
    "GA312/GA312-1920-04-01-T01.webp",
    "GA312/GA312-1920-04-01-T02.webp",
    "GA312/GA312-1920-04-02-T01.webp",
    "GA312/GA312-1920-04-03-T01.webp",
    "GA312/GA312-1920-04-03-T02.webp",
    "GA312/GA312-1920-04-07-T01.webp",
    "GA312/GA312-1920-04-07-T02.webp",
    "GA312/GA312-1920-04-09-T02.webp",
    "GA313/GA313-1921-04-11-T01.webp",
    "GA313/GA313-1921-04-11-T02.webp",
    "GA313/GA313-1921-04-13-T01.webp",
    "GA313/GA313-1921-04-14-T01.webp",
    "GA313/GA313-1921-04-16-T01.webp",
    "GA313/GA313-1921-04-17-T01.webp",
    "GA313/GA313-1921-04-18-T01.webp",
    "GA314/GA314-1920-10-09-T01.webp",
    "GA314/GA314-1920-10-09-T03.webp",
    "GA314/GA314-1924-04-22-T01.webp",
    "GA315/GA315-1921-04-12-T01.webp",
    "GA315/GA315-1921-04-13-T01.webp",
    "GA315/GA315-1921-04-14-T01.webp",
    "GA315/GA315-1921-04-17-T01.webp",
    "GA326/GA326-1923-01-03-T02.webp",
    "GA340/GA340-1922-07-24-T01.webp",
    "GA347/GA347-1922-09-20-T01.webp",
    "GA353/GA353-1924-03-01-T02.webp",
    "GA353/GA353-1924-03-08-T02.webp",
    "GA353/GA353-1924-06-04-T02.webp",
]

def main():
    print(f"Erstelle Galerie für {len(BRIGHT_IMAGES)} Bilder...")
    
    # Erstelle HTML
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Helle Bilder - Überprüfung</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: Arial, sans-serif; 
            background: #1a1a1a; 
            color: #fff; 
            padding: 20px;
            margin: 0;
        }
        h1 { color: #4a9eff; margin-bottom: 10px; }
        .info { 
            background: #2a2a2a; 
            padding: 15px; 
            border-radius: 8px; 
            margin-bottom: 20px;
        }
        .info p { margin: 5px 0; }
        .stats {
            position: fixed;
            top: 10px;
            right: 20px;
            background: #333;
            padding: 15px 20px;
            border-radius: 8px;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }
        .stats .confirmed { color: #4ade80; font-size: 1.2em; }
        .stats .pending { color: #fbbf24; font-size: 1.2em; }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .image-card {
            background: #2a2a2a;
            border-radius: 8px;
            overflow: hidden;
            cursor: pointer;
            transition: all 0.2s;
            border: 3px solid transparent;
        }
        .image-card:hover {
            transform: scale(1.02);
        }
        .image-card.confirmed {
            border-color: #4ade80;
            background: #1a3a1a;
        }
        .image-card img {
            width: 100%;
            height: auto;
            display: block;
        }
        .image-info {
            padding: 10px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .image-name {
            font-size: 0.9em;
            color: #aaa;
        }
        .status {
            font-size: 0.8em;
            padding: 4px 8px;
            border-radius: 4px;
        }
        .status.ok {
            background: #4ade80;
            color: #000;
        }
        .status.pending {
            background: #fbbf24;
            color: #000;
        }
        .export-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #4a9eff;
            color: #fff;
            border: none;
            padding: 15px 30px;
            font-size: 1.1em;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }
        .export-btn:hover {
            background: #3a8eef;
        }
        .lightbox {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.95);
            z-index: 2000;
            align-items: center;
            justify-content: center;
        }
        .lightbox.active {
            display: flex;
        }
        .lightbox img {
            max-width: 95%;
            max-height: 95%;
        }
        .lightbox-close {
            position: absolute;
            top: 20px;
            right: 30px;
            font-size: 2em;
            color: #fff;
            cursor: pointer;
        }
        .instructions {
            background: #3a3a3a;
            padding: 10px 15px;
            border-radius: 4px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <h1>🖼️ Helle Bilder - Überprüfung</h1>
    
    <div class="info">
        <p><strong>""" + str(len(BRIGHT_IMAGES)) + """ Bilder</strong> wurden als "hell" erkannt und nicht automatisch gecroppt.</p>
        <div class="instructions">
            <strong>Anleitung:</strong><br>
            👆 <strong>Klicke auf ein Bild</strong> um es zu bestätigen (= Bild ist OK, kein Cropping nötig)<br>
            🔍 <strong>Rechtsklick</strong> um das Bild vergrößert anzuzeigen<br>
            📋 <strong>"Export"</strong> zeigt die Liste der nicht-bestätigten Bilder (zum manuellen Bearbeiten)
        </div>
    </div>
    
    <div class="stats">
        <div>Bestätigt: <span class="confirmed" id="confirmedCount">0</span></div>
        <div>Ausstehend: <span class="pending" id="pendingCount">""" + str(len(BRIGHT_IMAGES)) + """</span></div>
    </div>
    
    <div class="gallery" id="gallery">
"""
    
    # Füge Bilder hinzu
    for img_path in BRIGHT_IMAGES:
        full_path = SOURCE_DIR / img_path.replace("/", "\\")
        # Relativer Pfad für HTML
        rel_path = f"../Steiner_GA/chalkboards/{img_path}"
        
        html += f"""
        <div class="image-card" data-path="{img_path}" onclick="toggleConfirm(this)" oncontextmenu="showLightbox('{rel_path}'); return false;">
            <img src="{rel_path}" alt="{img_path}" loading="lazy">
            <div class="image-info">
                <span class="image-name">{img_path}</span>
                <span class="status pending">Ausstehend</span>
            </div>
        </div>
"""
    
    html += """
    </div>
    
    <button class="export-btn" onclick="exportPending()">📋 Export nicht-bestätigte</button>
    
    <div class="lightbox" id="lightbox" onclick="closeLightbox()">
        <span class="lightbox-close">&times;</span>
        <img id="lightboxImg" src="">
    </div>
    
    <script>
        // Lade gespeicherten Status
        let confirmed = JSON.parse(localStorage.getItem('confirmedImages') || '[]');
        
        // Wende gespeicherten Status an
        document.querySelectorAll('.image-card').forEach(card => {
            if (confirmed.includes(card.dataset.path)) {
                card.classList.add('confirmed');
                card.querySelector('.status').className = 'status ok';
                card.querySelector('.status').textContent = '✓ OK';
            }
        });
        updateStats();
        
        function toggleConfirm(card) {
            const path = card.dataset.path;
            card.classList.toggle('confirmed');
            
            if (card.classList.contains('confirmed')) {
                card.querySelector('.status').className = 'status ok';
                card.querySelector('.status').textContent = '✓ OK';
                if (!confirmed.includes(path)) {
                    confirmed.push(path);
                }
            } else {
                card.querySelector('.status').className = 'status pending';
                card.querySelector('.status').textContent = 'Ausstehend';
                confirmed = confirmed.filter(p => p !== path);
            }
            
            localStorage.setItem('confirmedImages', JSON.stringify(confirmed));
            updateStats();
        }
        
        function updateStats() {
            const total = document.querySelectorAll('.image-card').length;
            const confirmedCount = document.querySelectorAll('.image-card.confirmed').length;
            document.getElementById('confirmedCount').textContent = confirmedCount;
            document.getElementById('pendingCount').textContent = total - confirmedCount;
        }
        
        function showLightbox(src) {
            document.getElementById('lightboxImg').src = src;
            document.getElementById('lightbox').classList.add('active');
        }
        
        function closeLightbox() {
            document.getElementById('lightbox').classList.remove('active');
        }
        
        function exportPending() {
            const pending = [];
            document.querySelectorAll('.image-card:not(.confirmed)').forEach(card => {
                pending.push(card.dataset.path);
            });
            
            if (pending.length === 0) {
                alert('Alle Bilder wurden bestätigt! 🎉');
                return;
            }
            
            const text = 'Nicht-bestätigte Bilder (zum manuellen Bearbeiten):\\n\\n' + pending.join('\\n');
            
            // Zeige in neuem Fenster
            const win = window.open('', '_blank');
            win.document.write('<pre style="font-family: monospace; padding: 20px;">' + text + '</pre>');
            win.document.title = 'Nicht-bestätigte Bilder';
        }
        
        // ESC schließt Lightbox
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') closeLightbox();
        });
    </script>
</body>
</html>
"""
    
    # Speichere HTML
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Galerie erstellt: {OUTPUT_HTML}")
    print(f"\nÖffne im Browser: file:///{OUTPUT_HTML.as_posix()}")


if __name__ == "__main__":
    main()

