import zipfile

src = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\temp_work.docx'
out = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives_CORRECTED.docx'

with zipfile.ZipFile(src, 'r') as z:
    with z.open('word/document.xml') as f:
        content = f.read().decode('utf-8')

# Ersetzungen
old1 = 'XE "Kielmeyer:reproduction and sensibility"'
new1 = 'XE "Kielmeyer:reproduction, irritability, and sensibility"'
old2 = 'XE "Excitability:Humboldt and Brown"'
new2 = 'XE "Excitability:Brown, Humboldt, and Treviranus"'

count1 = content.count(old1)
count2 = content.count(old2)
count1new = content.count('XE "Kielmeyer:reproduction, irritability, and sensibility"')
count2new = content.count('XE "Excitability:Brown, Humboldt, and Treviranus"')

print(f'Alter Kielmeyer-Eintrag:      {count1}x')
print(f'Alter Excitability-Eintrag:   {count2}x')
print(f'Bereits korrigiert Kielmeyer: {count1new}x')
print(f'Bereits korrigiert Excitab.:  {count2new}x')

content_new = content.replace(old1, new1).replace(old2, new2)

with zipfile.ZipFile(src, 'r') as zin:
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == 'word/document.xml':
                zout.writestr(item, content_new.encode('utf-8'))
            else:
                zout.writestr(item, zin.read(item.filename))

print(f'\nFertig: {count1}x Kielmeyer und {count2}x Excitability ersetzt.')
print(f'Gespeichert als: ...CORRECTED.docx')
