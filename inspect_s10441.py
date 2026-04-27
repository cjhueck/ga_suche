import zipfile, shutil, re

src = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'
tmp = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\tmp_ins.docx'
shutil.copy2(src, tmp)

with zipfile.ZipFile(tmp, 'r') as z:
    doc = z.read('word/document.xml').decode('utf-8')
import os; os.remove(tmp)

# Finde die Position im XML
idx = doc.find('s10441-005-5350-')
if idx >= 0:
    # Zeige 500 Zeichen Kontext
    snippet = doc[max(0, idx-200):idx+300]
    print("XML um 's10441-005-5350-':")
    print(snippet)
    print()
    # Zeige was nach dem Bindestrich kommt
    after = doc[idx+len('s10441-005-5350-'):idx+len('s10441-005-5350-')+200]
    print("Nach dem Bindestrich:")
    print(repr(after[:200]))
else:
    print("NICHT GEFUNDEN")
