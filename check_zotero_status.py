import sqlite3, shutil, os

zotero_db = r'C:\Users\chuec\Zotero\zotero.sqlite'
tmp_db = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\zotero_tmp.sqlite'
shutil.copy2(zotero_db, tmp_db)
conn = sqlite3.connect(tmp_db)
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM items')
print(f'Items gesamt: {cur.fetchone()[0]}')

cur.execute("""SELECT it.typeName, COUNT(*) FROM items i 
    JOIN itemTypes it ON i.itemTypeID = it.itemTypeID 
    GROUP BY it.typeName ORDER BY COUNT(*) DESC""")
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

cur.execute("SELECT COUNT(*) FROM itemAttachments WHERE contentType = 'application/pdf' AND linkMode = 0")
print(f'\nPDF-Dateien (imported_file): {cur.fetchone()[0]}')

cur.execute("SELECT COUNT(*) FROM itemAttachments WHERE linkMode = 3")
print(f'URL-Links: {cur.fetchone()[0]}')

cur.execute("SELECT COUNT(*) FROM collections")
print(f'Sammlungen: {cur.fetchone()[0]}')

cur.execute("SELECT collectionName FROM collections LIMIT 10")
print('Sammlungsnamen:')
for r in cur.fetchall():
    print(f'  {r[0]}')

conn.close()
os.remove(tmp_db)
