import sys, re, os
sys.stdout.reconfigure(encoding='utf-8')

def read_mar(path):
    with open(path, 'rb') as f:
        data = f.read()
    print(f'Datei: {os.path.basename(path)}')
    print(f'Größe: {len(data)} Bytes')
    # Alle druckbaren Strings extrahieren
    strings = re.findall(b'[\x20-\x7e\x80-\xfe]{6,}', data)
    print('Lesbare Strings:')
    for s in strings:
        try:
            decoded = s.decode('cp1252')
            print(f'  {decoded}')
        except:
            pass
    print()

# GOETHE.mar
goethe_mar = r'C:\Users\chuec\OneDrive\Dokumente\ViewLit-Projektdateien\Goethes Werk im Kontext (2005)\GOETHE.mar'
kant_mar = r'C:\Users\chuec\OneDrive\Dokumente\ViewLit-Projektdateien\Kant - Werke (2024)\KANT_J3.mar'
fichte_mar = r'C:\Users\chuec\OneDrive\Dokumente\ViewLit-Projektdateien\Fichte im Kontext II\FICHTE12.mar'

for path in [goethe_mar, kant_mar, fichte_mar]:
    try:
        read_mar(path)
    except Exception as e:
        print(f'Fehler bei {path}: {e}')

# Suche nach ViewLit-Datenbankdateien
print('='*60)
print('Suche nach Datenbankdateien auf dem System...')
search_dirs = [
    r'C:\Users\chuec\AppData',
    r'C:\Users\chuec\Documents',
    r'C:\Users\chuec\OneDrive\Dokumente',
    r'D:\\',
    r'E:\\',
]

extensions = ['.vlx', '.gwd', '.txd', '.vdb', '.idx', '.dat', '.lit']
for d in search_dirs:
    if not os.path.exists(d):
        continue
    try:
        for root, dirs, files in os.walk(d):
            # Skip too deep or unwanted dirs
            depth = root.replace(d, '').count(os.sep)
            if depth > 4:
                dirs.clear()
                continue
            for fname in files:
                if any(fname.lower().endswith(ext) for ext in extensions):
                    fpath = os.path.join(root, fname)
                    size = os.path.getsize(fpath)
                    print(f'  {fpath} ({size//1024} KB)')
    except PermissionError:
        pass
