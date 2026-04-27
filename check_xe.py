import zipfile

path = r'C:\Users\chuec\OneDrive\Obsidian\Obsidian Organik\CLC2025 Anthology final\Cognizing Life Historical, Epistemological, Idealistic, and Goethean Perspectives.docx'
try:
    with zipfile.ZipFile(path, 'r') as z:
        with z.open('word/document.xml') as f:
            content = f.read().decode('utf-8')
    count1 = content.count('XE "Kielmeyer:reproduction and sensibility"')
    count2 = content.count('XE "Excitability:Humboldt and Brown"')
    count1new = content.count('XE "Kielmeyer:reproduction, irritability, and sensibility"')
    count2new = content.count('XE "Excitability:Brown, Humboldt, and Treviranus"')
    print(f'Alter Kielmeyer-Eintrag: {count1}x')
    print(f'Alter Excitability-Eintrag: {count2}x')
    print(f'Neuer Kielmeyer-Eintrag (bereits geaendert): {count1new}x')
    print(f'Neuer Excitability-Eintrag (bereits geaendert): {count2new}x')
except Exception as e:
    print(f'Fehler: {e}')
