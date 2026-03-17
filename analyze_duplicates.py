import sqlite3, shutil, os
from collections import defaultdict

zotero_db = r'C:\Users\chuec\Zotero\zotero.sqlite'
tmp_db = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\zotero_dup.sqlite'
shutil.copy2(zotero_db, tmp_db)
conn = sqlite3.connect(tmp_db)
cur = conn.cursor()

# Current state
cur.execute("""SELECT it.typeName, COUNT(*) FROM items i 
    JOIN itemTypes it ON i.itemTypeID = it.itemTypeID 
    WHERE i.itemID NOT IN (SELECT itemID FROM deletedItems)
    GROUP BY it.typeName ORDER BY COUNT(*) DESC""")
print("=== Aktuelle Items ===")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Get all regular items with titles
cur.execute("""
    SELECT i.itemID, i.key, idv.value as title, it.typeName
    FROM items i
    JOIN itemData id ON i.itemID = id.itemID
    JOIN itemDataValues idv ON id.valueID = idv.valueID
    JOIN fields f ON id.fieldID = f.fieldID
    JOIN itemTypes it ON i.itemTypeID = it.itemTypeID
    WHERE f.fieldName = 'title'
    AND it.typeName NOT IN ('attachment', 'note')
    AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
""")
items = []
for row in cur.fetchall():
    items.append({"id": row[0], "key": row[1], "title": row[2], "type": row[3]})

print(f"\nRegulaere Items mit Titel: {len(items)}")

# Find duplicates by normalized title
def normalize(s):
    import re
    s = s.lower().strip()
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s

title_groups = defaultdict(list)
for item in items:
    norm = normalize(item["title"])
    title_groups[norm].append(item)

duplicates = {k: v for k, v in title_groups.items() if len(v) > 1}
unique = {k: v for k, v in title_groups.items() if len(v) == 1}

print(f"Einzigartige Titel: {len(unique)}")
print(f"Doppelte Titel: {len(duplicates)} (betrifft {sum(len(v) for v in duplicates.values())} Items)")

# Analyze duplicate groups
dup_2 = sum(1 for v in duplicates.values() if len(v) == 2)
dup_3 = sum(1 for v in duplicates.values() if len(v) == 3)
dup_4plus = sum(1 for v in duplicates.values() if len(v) >= 4)
print(f"  2-fach: {dup_2}")
print(f"  3-fach: {dup_3}")
print(f"  4+ fach: {dup_4plus}")

# Check which items have PDF attachments
cur.execute("""
    SELECT ia.parentItemID, COUNT(*) as pdf_count
    FROM itemAttachments ia
    WHERE ia.contentType = 'application/pdf'
    AND ia.linkMode = 0
    AND ia.parentItemID IS NOT NULL
    AND ia.itemID NOT IN (SELECT itemID FROM deletedItems)
    GROUP BY ia.parentItemID
""")
items_with_pdfs = dict(cur.fetchall())

# Check which items have notes
cur.execute("""
    SELECT in2.parentItemID, COUNT(*) as note_count
    FROM itemNotes in2
    JOIN items i ON in2.itemID = i.itemID
    WHERE in2.parentItemID IS NOT NULL
    AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
    GROUP BY in2.parentItemID
""")
items_with_notes = dict(cur.fetchall())

# Analyze duplicates: which has PDFs, notes, etc.
print(f"\n=== Duplikat-Analyse ===")
both_have_pdf = 0
one_has_pdf = 0
none_has_pdf = 0
has_notes_data = 0

for norm_title, group in duplicates.items():
    pdf_items = [item for item in group if item["id"] in items_with_pdfs]
    note_items = [item for item in group if item["id"] in items_with_notes]
    
    if len(pdf_items) >= 2:
        both_have_pdf += 1
    elif len(pdf_items) == 1:
        one_has_pdf += 1
    else:
        none_has_pdf += 1
    
    if note_items:
        has_notes_data += 1

print(f"  Beide/alle haben PDFs: {both_have_pdf}")
print(f"  Nur einer hat PDF: {one_has_pdf}")
print(f"  Keiner hat PDF: {none_has_pdf}")
print(f"  Mindestens einer hat Notizen: {has_notes_data}")

# Show examples
print(f"\n=== Beispiele (erste 10) ===")
for norm_title, group in list(duplicates.items())[:10]:
    title = group[0]["title"][:60]
    pdfs = [f"ID={item['id']}({items_with_pdfs.get(item['id'], 0)}PDF)" for item in group]
    notes = [f"{items_with_notes.get(item['id'], 0)}N" for item in group]
    try:
        print(f"  '{title}' -> {' vs '.join(pdfs)}")
    except UnicodeEncodeError:
        print(f"  (encoding issue) -> {' vs '.join(pdfs)}")

# Strategy summary
print(f"\n=== MERGE-STRATEGIE ===")
print(f"Fuer jede Duplikat-Gruppe:")
print(f"  1. Behalte Item mit meisten PDFs/Notizen als 'Master'")
print(f"  2. Verschiebe PDFs/Notizen von Duplikaten zum Master")
print(f"  3. Loesche die Duplikate")
print(f"  Betroffene Gruppen: {len(duplicates)}")
print(f"  Items die geloescht werden: {sum(len(v) - 1 for v in duplicates.values())}")

conn.close()
os.remove(tmp_db)
