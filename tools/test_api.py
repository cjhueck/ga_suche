import urllib.request
import json

try:
    with urllib.request.urlopen('http://localhost:3003/api/book/GA009') as response:
        data = json.loads(response.read().decode())
        
        print(f"ID: {data.get('ID', '?')}")
        print(f"Titel: {data.get('Titel', data.get('title', '?'))}")
        
        paragraphs = data.get('paragraphs', [])
        print(f"Paragraphen: {len(paragraphs)}")
        
        # Zähle Marker
        markers = 0
        for p in paragraphs:
            content = p.get('content', '')
            if '|' in content and any(c.isdigit() for c in content):
                markers += 1
        print(f"Mit |X| Markern: {markers}")
        
        # Zeige ersten Paragraphen
        if paragraphs:
            print(f"\nErster Paragraph:")
            print(paragraphs[0].get('content', '')[:200])
            
except Exception as e:
    print(f"Fehler: {e}")

