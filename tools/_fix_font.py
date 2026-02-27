path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()
c2 = c.replace("p.style.setProperty('font-size', '0.9rem', 'important');",
               "p.style.setProperty('font-size', '0.85rem', 'important');", 1)
c2 = c2.replace("li.style.setProperty('font-size', '0.9rem', 'important');",
                "li.style.setProperty('font-size', '0.85rem', 'important');", 1)
with open(path, 'w', encoding='utf-8') as f:
    f.write(c2)
print('OK' if c2 != c else 'bereits 0.85rem')
