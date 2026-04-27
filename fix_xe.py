import zipfile
import os
import shutil

path = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\temp_copy.docx'
out_path = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\temp_fixed.docx'

with zipfile.ZipFile(path, 'r') as z:
    with z.open('word/document.xml') as f:
        content = f.read().decode('utf-8')

# Ersetzungen
old1 = 'XE "Kielmeyer:reproduction and sensibility"'
new1 = 'XE "Kielmeyer:reproduction, irritability, and sensibility"'

old2 = 'XE "Excitability:Humboldt and Brown"'
new2 = 'XE "Excitability:Brown, Humboldt, and Treviranus"'

count1 = content.count(old1)
count2 = content.count(old2)
print(f"Gefunden '{old1}': {count1}x")
print(f"Gefunden '{old2}': {count2}x")

content_new = content.replace(old1, new1).replace(old2, new2)

# Schreibe neues Docx
with zipfile.ZipFile(path, 'r') as zin:
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == 'word/document.xml':
                zout.writestr(item, content_new.encode('utf-8'))
            else:
                zout.writestr(item, zin.read(item.filename))

print(f"\nFertig! Gespeichert als: {out_path}")
print(f"Ersetzt: {count1}x Kielmeyer, {count2}x Excitability")
