import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# In showMapsInViewer: font-size von p und li von 0.9rem auf 0.85rem
old = '''        p.style.setProperty('font-size', '0.9rem', 'important');
        p.style.setProperty('line-height', '1.5', 'important');
      });
      wrap.querySelectorAll('li').forEach(li => {
        li.style.setProperty('font-size', '0.9rem', 'important');'''

new = '''        p.style.setProperty('font-size', '0.85rem', 'important');
        p.style.setProperty('line-height', '1.5', 'important');
      });
      wrap.querySelectorAll('li').forEach(li => {
        li.style.setProperty('font-size', '0.85rem', 'important');'''

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: font-size 0.9rem -> 0.85rem')
else:
    print('FEHLER: Block nicht gefunden')
