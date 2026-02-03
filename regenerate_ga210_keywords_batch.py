#!/usr/bin/env python3
"""
Batch-Regeneration der Keywords für GA210 über das Backend-API.

VORAUSSETZUNG:
- Backend muss laufen (lokal: http://localhost:3003 oder Render)
- regenerate_ga210_keywords.py wurde bereits ausgeführt

VERWENDUNG:
    python regenerate_ga210_keywords_batch.py              # Lokal
    python regenerate_ga210_keywords_batch.py --render     # Render-Server
    python regenerate_ga210_keywords_batch.py --dry-run    # Nur anzeigen
"""

import argparse
import json
import time
import urllib.request
import urllib.error

# API URLs
LOCAL_API = "http://localhost:3003"
RENDER_API = "https://ga-suche.onrender.com"

# GA210 Vorträge
GA210_LECTURES = [f"GA210/{i}" for i in range(1, 15)]  # GA210/1 bis GA210/14


def check_server(base_url: str) -> bool:
    """Prüft ob der Server erreichbar ist."""
    # Versuche verschiedene Endpoints
    endpoints = [
        f"{base_url}/api/ga-volumes",
        f"{base_url}/",
    ]
    
    for endpoint in endpoints:
        try:
            req = urllib.request.Request(endpoint, method='GET')
            req.add_header('User-Agent', 'Mozilla/5.0')
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    return True
        except:
            continue
    
    return False


def regenerate_summary(base_url: str, lecture_id: str) -> dict:
    """
    Regeneriert Summary + Keywords für einen Vortrag.
    Verwendet forceRegenerate=true um Keywords neu zu generieren.
    """
    url = f"{base_url}/api/summarize-lecture"
    
    data = json.dumps({
        "lectureId": lecture_id,
        "forceRegenerate": True  # Wichtig: Erzwingt Keyword-Neugenerierung
    }).encode('utf-8')
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
            return {
                'success': True,
                'lectureId': lecture_id,
                'keywords_count': len(result.get('lectureKeywords', [])),
                'headings_count': len(result.get('headings', [])),
                'from_cache': result.get('fromCache', False)
            }
    except urllib.error.HTTPError as e:
        return {
            'success': False,
            'lectureId': lecture_id,
            'error': f"HTTP {e.code}: {e.reason}"
        }
    except urllib.error.URLError as e:
        return {
            'success': False,
            'lectureId': lecture_id,
            'error': str(e.reason)
        }
    except Exception as e:
        return {
            'success': False,
            'lectureId': lecture_id,
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(description='Regeneriert GA210 Keywords über Backend-API')
    parser.add_argument('--render', action='store_true', help='Verwende Render-Server statt localhost')
    parser.add_argument('--dry-run', action='store_true', help='Nur anzeigen, nicht ausfuehren')
    parser.add_argument('--delay', type=float, default=2.0, help='Sekunden zwischen Anfragen (default: 2)')
    
    args = parser.parse_args()
    
    base_url = RENDER_API if args.render else LOCAL_API
    
    print("=" * 70)
    print("  GA210 KEYWORDS BATCH-REGENERATION")
    print("=" * 70)
    print(f"\n  Server: {base_url}")
    print(f"  Vortraege: {len(GA210_LECTURES)}")
    print(f"  Delay: {args.delay}s zwischen Anfragen")
    
    if args.dry_run:
        print("\n  MODUS: DRY-RUN (keine Anfragen)")
        print("\n  Wuerde folgende Vortraege regenerieren:")
        for lid in GA210_LECTURES:
            print(f"    - {lid}")
        return
    
    # Server-Check
    print("\n[1/2] Pruefe Server-Verbindung...")
    if not check_server(base_url):
        print(f"  FEHLER: Server nicht erreichbar: {base_url}")
        print("  Bitte stelle sicher, dass das Backend laeuft.")
        return
    print("  OK - Server erreichbar")
    
    # Regeneration
    print(f"\n[2/2] Regeneriere Keywords fuer {len(GA210_LECTURES)} Vortraege...")
    print("-" * 70)
    
    success_count = 0
    error_count = 0
    total_keywords = 0
    
    for i, lecture_id in enumerate(GA210_LECTURES, 1):
        print(f"  [{i:2}/{len(GA210_LECTURES)}] {lecture_id}...", end=" ", flush=True)
        
        result = regenerate_summary(base_url, lecture_id)
        
        if result['success']:
            kw_count = result.get('keywords_count', 0)
            total_keywords += kw_count
            cached = " (cached)" if result.get('from_cache') else ""
            print(f"OK - {kw_count} Keywords{cached}")
            success_count += 1
        else:
            print(f"FEHLER: {result.get('error', 'Unbekannt')}")
            error_count += 1
        
        # Delay zwischen Anfragen (API-Rate-Limiting)
        if i < len(GA210_LECTURES):
            time.sleep(args.delay)
    
    # Zusammenfassung
    print("-" * 70)
    print(f"\n  ERGEBNIS:")
    print(f"    Erfolgreich: {success_count}/{len(GA210_LECTURES)}")
    print(f"    Fehler:      {error_count}")
    print(f"    Keywords:    {total_keywords} generiert")
    
    if error_count > 0:
        print("\n  HINWEIS: Bei Fehlern das Skript erneut ausfuehren")
        print("           oder manuell in der Web-App regenerieren.")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
