import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Ab "resultsDiv.querySelectorAll" nach dem blkref-Bereich
pos = content.find("resultsDiv.innerHTML = '<div id=\"maps-obsidian-content\"")
pos2 = content.find("const hash = (window.location.hash || '')", pos)
print('Block von maps-obsidian bis hash:')
print(repr(content[pos:pos2]))
