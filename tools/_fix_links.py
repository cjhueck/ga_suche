import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Regex erweitern: ^pfr5w5 auch am Zeilenende erkennen (\s oder $)
old_regex = r"md = md.replace(/ \^([a-z0-9]+)(?=[ \[;])/g, ' <span class=\"blkref\" data-bid=\"$1\"></span>');"
new_regex = r"md = md.replace(/ \^([a-z0-9]+)(?=[ \[;\s]|$)/g, ' <span class=\"blkref\" data-bid=\"$1\"></span>');"

if old_regex in content:
    content = content.replace(old_regex, new_regex, 1)
    print('OK 1: Regex erweitert fuer Zeilenende')
else:
    print('FEHLER 1: Regex nicht gefunden')
    if 'blkref' in content:
        idx = content.find('blkref')
        print(repr(content[idx-80:idx+120]))

# 2. Link-Text mit Klammern: (GA307/5:pfr5w5)
old_text = "a.textContent = lid + ':' + captured;"
new_text = "a.textContent = '(' + lid + ':' + captured + ')';"

if old_text in content:
    content = content.replace(old_text, new_text, 1)
    print('OK 2: Link-Text mit Klammern')
else:
    # Evtl. anderes Format
    if "lid + ':' + captured" in content:
        content = content.replace("a.textContent = lid + ':' + captured;", new_text, 1)
        print('OK 2: Link-Text (Variante)')
    else:
        print('FEHLER 2: textContent Zeile nicht gefunden')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Gespeichert.')
