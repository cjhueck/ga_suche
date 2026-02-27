with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html', 'r', encoding='utf-8') as f:
    src = f.read()

old = """    #results .maps-sidepanel-content h4:hover,
    #results .maps-sidepanel-content h5:hover,
    #results .maps-sidepanel-content h6:hover {
      opacity: 0.7;
    }"""

new = """    #results .maps-sidepanel-content h4:hover,
    #results .maps-sidepanel-content h5:hover,
    #results .maps-sidepanel-content h6:hover {
      opacity: 0.7;
    }
    /* Block-ID Referenz-Spans unsichtbar */
    .blkref { display: none !important; }"""

if old not in src:
    print('FEHLER nicht gefunden')
    exit(1)
src = src.replace(old, new, 1)
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html', 'w', encoding='utf-8') as f:
    f.write(src)
print('OK: .blkref CSS hinzugefügt')
