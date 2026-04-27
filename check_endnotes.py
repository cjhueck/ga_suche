import zipfile, re, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\chuec\OneDrive\Texte\Nassar Bearbeitet und erledigt\Nassar Übersetzung\Romantischer Empirismus - Kapitel\Fertige Endversionen\0 Einleitung_fertig_DN_CH_2026.docx'

with zipfile.ZipFile(path) as z:
    namen = z.namelist()
    print('Relevante Dateien:', [n for n in namen if 'note' in n.lower() or 'Note' in n])

    for fname in ['word/endnotes.xml', 'word/footnotes.xml']:
        if fname not in namen:
            print(f'\n{fname}: NICHT VORHANDEN')
            continue
        xml = z.read(fname).decode('utf-8')
        tag = 'endnote' if 'end' in fname else 'footnote'
        pattern = r'<w:' + tag + r'\b[^>]*w:id="(\d+)"[^>]*>(.*?)</w:' + tag + r'>'
        matches = list(re.finditer(pattern, xml, re.DOTALL))
        print(f'\n=== {fname.upper()} ({len(matches)} Einträge) ===')
        for m in matches:
            nid = m.group(1)
            content = m.group(2)
            runs = re.findall(r'<w:t[^>]*>(.*?)</w:t>', content, re.DOTALL)
            text = ''.join(runs).strip()
            if text:
                print(f'\n--- Nr. {nid} ---')
                print(text[:600])
