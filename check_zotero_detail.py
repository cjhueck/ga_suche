import sqlite3, shutil, os

zotero_db = r'C:\Users\chuec\Zotero\zotero.sqlite'
tmp_db = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\zotero_tmp2.sqlite'
shutil.copy2(zotero_db, tmp_db)
conn = sqlite3.connect(tmp_db)
cur = conn.cursor()

# Total items by type
cur.execute("""SELECT it.typeName, COUNT(*) FROM items i 
    JOIN itemTypes it ON i.itemTypeID = it.itemTypeID 
    WHERE i.itemID NOT IN (SELECT itemID FROM deletedItems)
    GROUP BY it.typeName ORDER BY COUNT(*) DESC""")
print("Items (nicht geloescht):")
total = 0
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")
    total += r[1]
print(f"  GESAMT: {total}")

# Check deleted items
cur.execute("SELECT COUNT(*) FROM deletedItems")
print(f"\nGeloeschte Items: {cur.fetchone()[0]}")

# Check collections
cur.execute("SELECT collectionID, collectionName, parentCollectionID FROM collections")
colls = cur.fetchall()
print(f"\nSammlungen: {len(colls)}")
for c in colls:
    print(f"  ID={c[0]}: '{c[1]}' (parent={c[2]})")

# Items in collections
cur.execute("""SELECT c.collectionName, COUNT(*) 
    FROM collectionItems ci 
    JOIN collections c ON ci.collectionID = c.collectionID
    GROUP BY c.collectionName""")
print("\nItems pro Sammlung:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Items NOT in any collection (top-level "Meine Bibliothek")
cur.execute("""SELECT COUNT(*) FROM items i
    WHERE i.itemID NOT IN (SELECT itemID FROM collectionItems)
    AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
    AND i.itemTypeID NOT IN (SELECT itemTypeID FROM itemTypes WHERE typeName IN ('attachment', 'note'))""")
print(f"\nItems OHNE Sammlung (direkt in 'Meine Bibliothek'): {cur.fetchone()[0]}")

# Items that are regular items (not attachment/note)
cur.execute("""SELECT COUNT(*) FROM items i
    WHERE i.itemID NOT IN (SELECT itemID FROM deletedItems)
    AND i.itemTypeID NOT IN (SELECT itemTypeID FROM itemTypes WHERE typeName IN ('attachment', 'note'))""")
print(f"Regulaere Items gesamt: {cur.fetchone()[0]}")

# PDF attachments
cur.execute("""SELECT COUNT(*) FROM itemAttachments 
    WHERE contentType = 'application/pdf' AND linkMode = 0""")
print(f"\nPDF-Dateien (imported): {cur.fetchone()[0]}")

conn.close()
os.remove(tmp_db)
