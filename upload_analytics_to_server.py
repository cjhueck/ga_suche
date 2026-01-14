# -*- coding: utf-8 -*-
"""
Skript zum Hochladen der wiederhergestellten Analytics-Daten auf den Render-Server

Dieses Skript:
1. Lädt die lokale analytics-data.json
2. Sendet sie an den Render-Server via API
"""

import json
import requests
from pathlib import Path

# Pfade
ANALYTICS_FILE = Path('analytics-data.json')
SERVER_URL = 'https://ga-suche.onrender.com'

def upload_analytics_data():
    """Lädt Analytics-Daten auf den Server hoch"""
    
    print("=" * 70)
    print("Analytics-Daten auf Server hochladen")
    print("=" * 70)
    print()
    
    # Lade lokale Datei
    if not ANALYTICS_FILE.exists():
        print(f"[FEHLER] Datei nicht gefunden: {ANALYTICS_FILE}")
        return False
    
    print(f"[INFO] Lade lokale Datei: {ANALYTICS_FILE}")
    try:
        with open(ANALYTICS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[FEHLER] Fehler beim Laden der Datei: {e}")
        return False
    
    # Validiere Datenstruktur
    if not data.get('dailyStats'):
        print("[FEHLER] Ungültige Datenstruktur: dailyStats fehlt")
        return False
    
    print(f"[OK] Datei geladen: {len(data.get('dailyStats', {}))} Tage mit Daten")
    print(f"     - Gesamt Views: {data.get('totalViews', 0)}")
    print(f"     - Gesamt Suchen: {data.get('totalSearches', 0)}")
    print(f"     - Gesamt Vortraege: {data.get('totalLectureViews', 0)}")
    print()
    
    # Upload-Endpunkt (muss erst im Backend erstellt werden)
    # Für jetzt verwenden wir den Restore-Endpunkt mit einem temporären Backup
    # ODER wir erstellen einen Upload-Endpunkt
    
    # Versuche Upload-Endpunkt (falls vorhanden)
    upload_url = f"{SERVER_URL}/api/analytics/upload"
    
    print(f"[INFO] Versuche Upload an: {upload_url}")
    try:
        response = requests.post(
            upload_url,
            json={'data': data},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] Upload erfolgreich!")
            print(f"     - {result.get('message', 'Erfolg')}")
            if 'stats' in result:
                stats = result['stats']
                print(f"     - Tage: {stats.get('days', 0)}")
                print(f"     - Views: {stats.get('totalViews', 0)}")
                print(f"     - Suchen: {stats.get('totalSearches', 0)}")
                print(f"     - Vortraege: {stats.get('totalLectures', 0)}")
            return True
        elif response.status_code == 404:
            print(f"[WARN] Upload-Endpunkt nicht gefunden (404)")
            print(f"       Der Endpunkt /api/analytics/upload muss erst im Backend erstellt werden.")
            print()
            print("Alternative: Verwenden Sie die Browser-Konsole:")
            print(f"  fetch('{SERVER_URL}/api/analytics/upload', {{")
            print(f"    method: 'POST',")
            print(f"    headers: {{ 'Content-Type': 'application/json' }},\n    body: JSON.stringify({{ data: <Ihre Daten> }})")
            print(f"  }})")
            return False
        else:
            print(f"[FEHLER] Upload fehlgeschlagen: {response.status_code}")
            print(f"         Antwort: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"[FEHLER] Netzwerkfehler: {e}")
        return False

if __name__ == '__main__':
    success = upload_analytics_data()
    if not success:
        print()
        print("=" * 70)
        print("Hinweis:")
        print("=" * 70)
        print("Falls der Upload-Endpunkt noch nicht existiert, können Sie:")
        print("1. Die Datei manuell auf den Server kopieren (via Git)")
        print("2. Oder den Upload-Endpunkt im Backend erstellen")
        print()
        print("Für manuellen Upload via Browser-Konsole:")
        print("1. Öffnen Sie die Browser-Konsole auf der Online-Version")
        print("2. Führen Sie aus:")
        print()
        print("""
fetch('https://ga-suche.onrender.com/api/analytics/upload', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    data: <Hier die Daten aus analytics-data.json einfügen>
  })
}).then(r => r.json()).then(console.log)
        """)
        print()

