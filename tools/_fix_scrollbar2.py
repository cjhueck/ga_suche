import io, sys
path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Wenn PDF-Panel sichtbar, Summary-Panel nicht scrollen lassen (vermeidet Doppel-Scrollbar)
# body:has() wird von modernen Browsern unterstuetzt
insert_after = """    body.dark-mode .pdf-canvas-container {
      background: var(--dark-background-color);
    }"""

new_rule = """
    /* Keine Doppel-Scrollbar: wenn PDF-Panel offen, nur PDF-Container scrollt */
    body:has(#pdf-viewer-panel.visible) #summary-panel {
      overflow-y: hidden !important;
    }"""

if insert_after in c and new_rule not in c:
    c = c.replace(insert_after, insert_after + new_rule, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('OK: Summary-Panel Scrollbar versteckt wenn PDF offen')
else:
    print('Einzufuegen nach:', insert_after[:50] if insert_after in c else 'Nicht gefunden')
    print('Bereits vorhanden:', new_rule[:30] in c)
