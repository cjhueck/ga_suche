import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Sichtbare Anzeige: (307/5) statt GA307/5:pfr5w5
# lectureId ist z.B. "GA307/5" -> Anzeige "(307/5)"
old_text = "a.textContent = lid + ':' + captured;"
new_text = "a.textContent = '(' + (lid || '').replace(/^GA/i, '') + ')';"

if old_text in content:
    content = content.replace(old_text, new_text, 1)
    print('OK: Anzeige (307/5)')
elif "lid + ':' + captured" in content:
    content = content.replace("a.textContent = lid + ':' + captured;", new_text, 1)
    print('OK: Anzeige (307/5) Variante')
elif "a.textContent = '(' + lid" in content:
    # Bereits Klammern, aber falscher Inhalt
    old2 = "a.textContent = '(' + lid + ':' + captured + ')';"
    if old2 in content:
        content = content.replace(old2, new_text, 1)
        print('OK: Anzeige (307/5) ersetzt')
    else:
        print('Andere Variante - prufe')
else:
    idx = content.find('a.textContent')
    if idx >= 0:
        print('Gefunden bei', idx, ':', repr(content[idx:idx+80]))
    else:
        print('textContent nicht gefunden')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
