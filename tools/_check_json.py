import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

base = r'C:\Users\chuec\OneDrive\GitHub\ga_suche'

# Finde eine JSON-Datei mit GA307
for f in os.listdir(base):
    if '307' in f and f.endswith('.json') and 'lectures' in f.lower():
        path = os.path.join(base, f)
        print(f'Gefunden: {f}')
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        # Zeige Struktur des ersten Eintrags
        if isinstance(data, list):
            item = data[0]
        elif isinstance(data, dict):
            item = data
        print('Keys:', list(item.keys())[:10] if isinstance(item, dict) else type(item))
        # Suche nach blockId / id / ^
        if isinstance(item, dict):
            for k, v in item.items():
                print(f'  {k}: {str(v)[:60]}')
        break
else:
    # Liste alle JSON-Dateien
    jsons = [f for f in os.listdir(base) if f.endswith('.json')]
    print('JSON-Dateien:', jsons[:10])
