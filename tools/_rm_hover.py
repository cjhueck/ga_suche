import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Entferne den Hover-Block und auch die transition aus dem vorigen Block
old = '''      transition: opacity 0.15s;
    }
    #results .maps-sidepanel-content h4:hover,
    #results .maps-sidepanel-content h5:hover,
    #results .maps-sidepanel-content h6:hover {
      opacity: 0.7;
    }'''

new = '''    }'''

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: Hover-Effekt entfernt')
else:
    print('FEHLER: Block nicht gefunden')
    idx = content.find('transition: opacity')
    print(repr(content[max(0,idx-20):idx+200]))
