import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html', 'r', encoding='utf-8') as f:
    c = f.read()

# HTML Struktur pdf-popup
idx = c.find('id="pdf-popup-modal"')
print('HTML:', repr(c[idx:idx+600]))
