import urllib.request
import json

try:
    r = urllib.request.urlopen('http://localhost:3003/api/keywords/broken')
    d = json.load(r)
    print(f'API Status: OK')
    print(f'Gültige IDs: {d.get("totalValid", "N/A")}')
    print(f'Gebrochene Keywords: {d.get("brokenCount", "N/A")}')
except urllib.error.HTTPError as e:
    print(f'HTTP Fehler: {e.code} {e.reason}')
    # Versuche Fehlermeldung zu lesen
    try:
        error_body = e.read().decode('utf-8')
        print(f'Fehlermeldung: {error_body}')
    except:
        pass
except urllib.error.URLError as e:
    print(f'Verbindungsfehler: {e.reason}')
except Exception as e:
    print(f'Fehler: {e}')
