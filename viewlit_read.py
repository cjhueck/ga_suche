"""Lese ViewLit V60-Textdatenbank und extrahiere Goethe/Kant-Texte."""
import sys, re, os
sys.stdout.reconfigure(encoding='utf-8')

def read_v60_sample(path, max_bytes=500000):
    """Liest die ersten Bytes der V60-Datei und extrahiert lesbaren Text."""
    with open(path, 'rb') as f:
        data = f.read(max_bytes)
    
    print(f'Datei: {os.path.basename(path)}')
    print(f'Gelesen: {len(data)} Bytes')
    
    # Header
    header = data[:200]
    print(f'\nHeader (Latin-1): {header.decode("latin-1", errors="replace")[:200]}')
    
    # Suche nach lesbaren Textblöcken (min. 20 Zeichen)
    # V60 speichert Text wahrscheinlich in Blöcken mit Steuerzeichen
    strings = re.findall(b'[\x20-\x7e\x80-\xfe\t\r\n]{20,}', data)
    
    print(f'\nAnzahl lesbarer Textblöcke: {len(strings)}')
    print('\nErste 20 Textblöcke:')
    for i, s in enumerate(strings[:20]):
        try:
            decoded = s.decode('cp1252').strip()
            if decoded:
                print(f'  [{i:3d}] {decoded[:150]}')
        except:
            pass

goethe_v60 = r'C:\Program Files (x86)\Common Files\Literatur im Kontext\Goethes Werk im Kontext\GOETHE.V60'
kant_v60 = r'C:\Program Files (x86)\Common Files\Literatur im Kontext\Kant Werke (Sonderausgabe)\KANT_J3.V60'

print('='*60)
read_v60_sample(goethe_v60, max_bytes=200000)
print()
print('='*60)
read_v60_sample(kant_v60, max_bytes=100000)
