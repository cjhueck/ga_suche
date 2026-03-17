import sqlite3, shutil, os, re
from collections import defaultdict

zotero_db = r'C:\Users\chuec\Zotero\zotero.sqlite'
tmp_db = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\zotero_neardup.sqlite'
shutil.copy2(zotero_db, tmp_db)
conn = sqlite3.connect(tmp_db)
cur = conn.cursor()

cur.execute("""
    SELECT i.itemID, i.key, idv.value as title
    FROM items i
    JOIN itemData id ON i.itemID = id.itemID
    JOIN itemDataValues idv ON id.valueID = idv.valueID
    JOIN fields f ON id.fieldID = f.fieldID
    WHERE f.fieldName = 'title'
    AND i.itemTypeID NOT IN (SELECT itemTypeID FROM itemTypes WHERE typeName IN ('attachment', 'note'))
    AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
""")
items = [(r[0], r[1], r[2]) for r in cur.fetchall()]

# Get authors and year for each item
item_meta = {}
for item_id, key, title in items:
    item_meta[item_id] = {"key": key, "title": title, "year": "", "authors": []}

cur.execute("""
    SELECT i.itemID, idv.value
    FROM items i
    JOIN itemData id ON i.itemID = id.itemID
    JOIN itemDataValues idv ON id.valueID = idv.valueID
    JOIN fields f ON id.fieldID = f.fieldID
    WHERE f.fieldName = 'date'
    AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
""")
for item_id, date_val in cur.fetchall():
    if item_id in item_meta:
        item_meta[item_id]["year"] = str(date_val or "")[:4]

cur.execute("""
    SELECT ic.itemID, c.lastName
    FROM itemCreators ic
    JOIN creators c ON ic.creatorID = c.creatorID
    WHERE ic.itemID NOT IN (SELECT itemID FROM deletedItems)
    ORDER BY ic.itemID, ic.orderIndex
""")
for item_id, last in cur.fetchall():
    if item_id in item_meta:
        item_meta[item_id]["authors"].append(last or "")

conn.close()
os.remove(tmp_db)

def norm_aggressive(s):
    s = (s or "").lower().strip()
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s)
    # Remove common articles
    for w in ['the ', 'a ', 'an ', 'der ', 'die ', 'das ', 'ein ', 'eine ', 'zur ', 'zum ']:
        if s.startswith(w):
            s = s[len(w):]
    return s

def first_n_words(s, n=5):
    words = norm_aggressive(s).split()
    return " ".join(words[:n])

# Strategy 1: Same first author + same year + similar first words
auth_year_groups = defaultdict(list)
for item_id, meta in item_meta.items():
    auth = (meta["authors"][0].lower().strip() if meta["authors"] else "")
    year = meta["year"]
    if auth and year:
        auth_year_groups[(auth, year)].append(item_id)

near_dupes = []
for (auth, year), group_ids in auth_year_groups.items():
    if len(group_ids) < 2:
        continue
    # Check if titles are similar
    group_items = [(gid, item_meta[gid]) for gid in group_ids]
    fw_groups = defaultdict(list)
    for gid, meta in group_items:
        fw = first_n_words(meta["title"], 3)
        if fw:
            fw_groups[fw].append((gid, meta))
    
    for fw, fw_items in fw_groups.items():
        if len(fw_items) >= 2:
            near_dupes.append(fw_items)

# Strategy 2: Same title first 6 words (regardless of author)
fw6_groups = defaultdict(list)
for item_id, meta in item_meta.items():
    fw = first_n_words(meta["title"], 6)
    if fw and len(fw) > 15:
        fw6_groups[fw].append((item_id, meta))

for fw, fw_items in fw6_groups.items():
    if len(fw_items) >= 2:
        # Check these aren't already found
        ids_set = frozenset(i[0] for i in fw_items)
        already = False
        for nd in near_dupes:
            if frozenset(i[0] for i in nd) == ids_set:
                already = True
                break
        if not already:
            near_dupes.append(fw_items)

# Deduplicate near_dupes groups
seen_pairs = set()
unique_groups = []
for group in near_dupes:
    pair = frozenset(g[0] for g in group)
    if pair not in seen_pairs:
        seen_pairs.add(pair)
        unique_groups.append(group)

print(f"Nah-Duplikate gefunden: {len(unique_groups)} Gruppen")
print(f"Betroffene Items: {sum(len(g) for g in unique_groups)}")

for i, group in enumerate(unique_groups[:30]):
    print(f"\nGruppe {i+1}:")
    for gid, meta in group:
        auth = meta['authors'][0] if meta['authors'] else '?'
        try:
            print(f"  ID={gid} [{auth} {meta['year']}] {meta['title'][:70]}")
        except UnicodeEncodeError:
            print(f"  ID={gid} [{auth} {meta['year']}] (encoding)")

print(f"\n=== GESAMT: {len(unique_groups)} Gruppen mit {sum(len(g) for g in unique_groups)} Items ===")
