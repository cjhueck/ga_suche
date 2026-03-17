import sqlite3, shutil, os, json, re
from collections import defaultdict

db_path = r'C:\Users\chuec\OneDrive\Dokumente\Citavi 7\Projects\Organicism\Organicism.ctv6'
zotero_db = r'C:\Users\chuec\Zotero\zotero.sqlite'
export_dir = r'C:\Users\chuec\OneDrive\Dokumente\Citavi 7\Projects\Organicism\ZoteroExport'

def normalize(s):
    s = (s or "").lower().strip()
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s

# --- Citavi ---
conn_c = sqlite3.connect(db_path)
cur_c = conn_c.cursor()

cur_c.execute("SELECT ID, Title, Year, ShortTitle FROM Reference")
citavi_refs = {}
for row in cur_c.fetchall():
    citavi_refs[row[0]] = {"title": row[1] or "", "year": row[2] or "", "short_title": row[3] or ""}

cur_c.execute("""
    SELECT ra.ReferenceID, p.LastName, p.FirstName
    FROM ReferenceAuthor ra
    JOIN Person p ON ra.PersonID = p.ID
    ORDER BY ra.ReferenceID
""")
ref_authors = defaultdict(list)
for ref_id, last, first in cur_c.fetchall():
    ref_authors[ref_id].append({"last": last or "", "first": first or ""})

# Get PDF mappings
cur_c.execute("SELECT ReferenceID, Address FROM Location WHERE Address IS NOT NULL AND Address != ''")
ref_to_pdf = {}
for ref_id, addr in cur_c.fetchall():
    try:
        data = json.loads(addr)
    except json.JSONDecodeError:
        continue
    if data.get("LinkedResourceType") != 1:
        continue
    uri = data.get("UriString", "")
    if uri.lower().endswith(".pdf"):
        ref_to_pdf[ref_id] = uri

# Get reference type
cur_c.execute("SELECT ID, ReferenceType FROM Reference")
ref_types = {}
for row in cur_c.fetchall():
    ref_types[row[0]] = row[1]

conn_c.close()

print(f"Citavi Referenzen gesamt: {len(citavi_refs)}")

# --- Zotero ---
tmp_db = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\zotero_missing.sqlite'
shutil.copy2(zotero_db, tmp_db)
conn_z = sqlite3.connect(tmp_db)
cur_z = conn_z.cursor()

cur_z.execute("""
    SELECT i.itemID, idv.value as title
    FROM items i
    JOIN itemData id ON i.itemID = id.itemID
    JOIN itemDataValues idv ON id.valueID = idv.valueID
    JOIN fields f ON id.fieldID = f.fieldID
    WHERE f.fieldName = 'title'
    AND i.itemTypeID NOT IN (SELECT itemTypeID FROM itemTypes WHERE typeName IN ('attachment', 'note'))
    AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
""")
zotero_titles = set()
for row in cur_z.fetchall():
    zotero_titles.add(normalize(row[1]))

conn_z.close()
os.remove(tmp_db)

print(f"Zotero Eintraege: {len(zotero_titles)}")

# --- Find missing ---
missing = []
for ref_id, info in citavi_refs.items():
    c_norm = normalize(info["title"])
    if c_norm and c_norm not in zotero_titles:
        has_pdf = ref_id in ref_to_pdf
        authors = ref_authors.get(ref_id, [])
        auth_str = "; ".join([f"{a['last']}, {a['first']}" for a in authors[:3]])
        missing.append({
            "ref_id": ref_id,
            "title": info["title"],
            "year": info["year"],
            "authors": auth_str,
            "has_pdf": has_pdf,
            "pdf_name": ref_to_pdf.get(ref_id, ""),
            "type": ref_types.get(ref_id, "")
        })

print(f"\nFehlende Eintraege: {len(missing)}")

# Breakdown by type
type_counts = defaultdict(int)
for m in missing:
    type_counts[m["type"]] += 1
print("\nNach Typ:")
for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")

with_pdf = sum(1 for m in missing if m["has_pdf"])
print(f"\nDavon mit PDF: {with_pdf}")
print(f"Ohne PDF: {len(missing) - with_pdf}")

# Show first 20
print(f"\nBeispiele (erste 20):")
for m in missing[:20]:
    try:
        print(f"  [{m['year']}] {m['authors'][:30]}: {m['title'][:60]} {'[PDF]' if m['has_pdf'] else ''}")
    except UnicodeEncodeError:
        print(f"  [{m['year']}] (encoding) {'[PDF]' if m['has_pdf'] else ''}")

# Check: are there Citavi entries matching Zotero by substring?
found_by_sub = 0
truly_missing = []
for m in missing:
    c_norm = normalize(m["title"])
    found = False
    if len(c_norm) >= 15:
        for z_t in zotero_titles:
            if c_norm in z_t or z_t in c_norm:
                found = True
                found_by_sub += 1
                break
    if not found:
        truly_missing.append(m)

print(f"\nDavon per Substring in Zotero gefunden: {found_by_sub}")
print(f"Wirklich fehlend: {len(truly_missing)}")
