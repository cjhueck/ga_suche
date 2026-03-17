import sqlite3
import os
import json
import shutil
import re
from collections import defaultdict

db_path = r'C:\Users\chuec\OneDrive\Dokumente\Citavi 7\Projects\Organicism\Organicism.ctv6'
export_dir = r'C:\Users\chuec\OneDrive\Dokumente\Citavi 7\Projects\Organicism\ZoteroExport'
zotero_db = r'C:\Users\chuec\Zotero\zotero.sqlite'

# --- Step 1: Build Citavi ReferenceID -> PDF + metadata ---
conn_c = sqlite3.connect(db_path)
cur_c = conn_c.cursor()

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

cur_c.execute("SELECT ID, Title, Year, ShortTitle FROM Reference")
citavi_refs = {}
for row in cur_c.fetchall():
    citavi_refs[row[0]] = {"title": row[1], "year": row[2], "short_title": row[3]}

# Also get authors from Citavi
cur_c.execute("""
    SELECT ra.ReferenceID, p.LastName, p.FirstName 
    FROM ReferenceAuthor ra 
    JOIN Person p ON ra.PersonID = p.ID
    ORDER BY ra.ReferenceID
""")
ref_authors = defaultdict(list)
for ref_id, last, first in cur_c.fetchall():
    ref_authors[ref_id].append(last or "")

conn_c.close()

# --- Step 2: Zotero items ---
tmp_db = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\zotero_copy3.sqlite'
shutil.copy2(zotero_db, tmp_db)
conn_z = sqlite3.connect(tmp_db)
cur_z = conn_z.cursor()

cur_z.execute("""
    SELECT i.itemID, i.key, idv.value as title
    FROM items i
    JOIN itemData id ON i.itemID = id.itemID
    JOIN itemDataValues idv ON id.valueID = idv.valueID
    JOIN fields f ON id.fieldID = f.fieldID
    WHERE f.fieldName = 'title'
    AND i.itemTypeID NOT IN (SELECT itemTypeID FROM itemTypes WHERE typeName IN ('attachment', 'note'))
""")
zotero_items = {}
for item_id, key, title in cur_z.fetchall():
    zotero_items[item_id] = {"key": key, "title": title}

# Also get year for Zotero items
cur_z.execute("""
    SELECT i.itemID, idv.value
    FROM items i
    JOIN itemData id ON i.itemID = id.itemID
    JOIN itemDataValues idv ON id.valueID = idv.valueID
    JOIN fields f ON id.fieldID = f.fieldID
    WHERE f.fieldName = 'date'
    AND i.itemTypeID NOT IN (SELECT itemTypeID FROM itemTypes WHERE typeName IN ('attachment', 'note'))
""")
for item_id, date_val in cur_z.fetchall():
    if item_id in zotero_items:
        zotero_items[item_id]["year"] = date_val

# Get Zotero authors
cur_z.execute("""
    SELECT ic.itemID, c.lastName, c.firstName
    FROM itemCreators ic
    JOIN creators c ON ic.creatorID = c.creatorID
    ORDER BY ic.itemID, ic.orderIndex
""")
z_authors = defaultdict(list)
for item_id, last, first in cur_z.fetchall():
    z_authors[item_id].append(last or "")

cur_z.execute("""
    SELECT ia.parentItemID 
    FROM itemAttachments ia 
    WHERE ia.contentType = 'application/pdf' 
    AND ia.linkMode = 0
    AND ia.parentItemID IS NOT NULL
""")
items_with_pdf = set(r[0] for r in cur_z.fetchall())

conn_z.close()
os.remove(tmp_db)

# --- Step 3: Multi-strategy matching ---
def normalize(s):
    if not s:
        return ""
    s = s.lower().strip()
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s

def normalize_light(s):
    if not s:
        return ""
    return s.lower().strip().replace("  ", " ")

# Build multiple indexes for Zotero items
z_by_exact_title = defaultdict(list)
z_by_norm_title = defaultdict(list)
z_by_title_year = defaultdict(list)
z_by_author_year = defaultdict(list)

for item_id, info in zotero_items.items():
    t_exact = normalize_light(info["title"])
    t_norm = normalize(info["title"])
    year = info.get("year", "")
    authors = z_authors.get(item_id, [])
    first_author = normalize(authors[0]) if authors else ""
    
    z_by_exact_title[t_exact].append(item_id)
    z_by_norm_title[t_norm].append(item_id)
    
    if year:
        year_str = str(year)[:4]
        z_by_title_year[(t_norm, year_str)].append(item_id)
        if first_author:
            z_by_author_year[(first_author, year_str)].append(item_id)

# Match with multiple strategies
matches = {}  # zotero_item_id -> (z_key, pdf_name, strategy)
unmatched_refs = []

for ref_id, pdf_name in ref_to_pdf.items():
    citavi_info = citavi_refs.get(ref_id, {})
    c_title_exact = normalize_light(citavi_info.get("title", ""))
    c_title_norm = normalize(citavi_info.get("title", ""))
    c_year = str(citavi_info.get("year", ""))[:4] if citavi_info.get("year") else ""
    c_authors = ref_authors.get(ref_id, [])
    c_first_author = normalize(c_authors[0]) if c_authors else ""
    
    pdf_path = os.path.join(export_dir, pdf_name)
    if not os.path.exists(pdf_path):
        continue
    
    found = False
    
    # Strategy 1: Exact title match
    for z_id in z_by_exact_title.get(c_title_exact, []):
        if z_id not in items_with_pdf and z_id not in matches:
            matches[z_id] = (zotero_items[z_id]["key"], pdf_name, "exact_title")
            found = True
            break
    
    if found:
        continue
    
    # Strategy 2: Normalized title match
    for z_id in z_by_norm_title.get(c_title_norm, []):
        if z_id not in items_with_pdf and z_id not in matches:
            matches[z_id] = (zotero_items[z_id]["key"], pdf_name, "norm_title")
            found = True
            break
    
    if found:
        continue
    
    # Strategy 3: Title + Year
    if c_year:
        for z_id in z_by_title_year.get((c_title_norm, c_year), []):
            if z_id not in items_with_pdf and z_id not in matches:
                matches[z_id] = (zotero_items[z_id]["key"], pdf_name, "title_year")
                found = True
                break
    
    if found:
        continue
    
    # Strategy 4: First author + Year
    if c_first_author and c_year:
        candidates = z_by_author_year.get((c_first_author, c_year), [])
        if len(candidates) == 1:
            z_id = candidates[0]
            if z_id not in items_with_pdf and z_id not in matches:
                matches[z_id] = (zotero_items[z_id]["key"], pdf_name, "author_year")
                found = True
    
    if not found:
        unmatched_refs.append((ref_id, citavi_info.get("title", "?"), pdf_name))

# Count by strategy
strategy_counts = defaultdict(int)
for z_id, (z_key, pdf, strat) in matches.items():
    strategy_counts[strat] += 1

print(f"=== MATCHING ERGEBNIS ===")
print(f"Zugeordnete PDFs: {len(matches)}")
for strat, count in sorted(strategy_counts.items()):
    print(f"  {strat}: {count}")
print(f"Bereits mit PDF: {len(items_with_pdf)}")
print(f"Nicht zugeordnet: {len(unmatched_refs)}")

if unmatched_refs:
    print(f"\nNicht zugeordnet (erste 15):")
    for ref_id, title, pdf in unmatched_refs[:15]:
        print(f"  '{title}' -> {pdf}")

# --- Step 4: Generate JavaScript ---
js_output = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\zotero_import.js'
export_dir_js = export_dir.replace('\\', '/')

js_lines = []
js_lines.append(f'// Zotero Import Script - {len(matches)} PDFs')
js_lines.append(f'// Run in Zotero: Tools -> Developer -> Run JavaScript')
js_lines.append(f'var exportDir = {json.dumps(export_dir_js)};')
js_lines.append('')
js_lines.append('var files = [')
for i, (z_id, (z_key, pdf_name, _)) in enumerate(matches.items()):
    comma = "," if i < len(matches) - 1 else ""
    js_lines.append(f'  [{json.dumps(z_key)}, {json.dumps(pdf_name)}]{comma}')
js_lines.append('];')
js_lines.append('')
js_lines.append('async function importPDFs() {')
js_lines.append('  var count = 0;')
js_lines.append('  var errors = 0;')
js_lines.append('  for (let [key, filename] of files) {')
js_lines.append('    try {')
js_lines.append('      var item = await Zotero.Items.getByLibraryAndKeyAsync(1, key);')
js_lines.append('      if (!item) { errors++; continue; }')
js_lines.append('      var filePath = exportDir + "/" + filename;')
js_lines.append('      await Zotero.Attachments.importFromFile({')
js_lines.append('        file: filePath,')
js_lines.append('        parentItemID: item.id')
js_lines.append('      });')
js_lines.append('      count++;')
js_lines.append('      if (count % 50 === 0) Zotero.debug("Imported " + count + " PDFs...");')
js_lines.append('    } catch(e) {')
js_lines.append('      Zotero.debug("Error for " + key + " (" + filename + "): " + e);')
js_lines.append('      errors++;')
js_lines.append('    }')
js_lines.append('  }')
js_lines.append('  return "Done! Imported: " + count + ", Errors: " + errors;')
js_lines.append('}')
js_lines.append('')
js_lines.append('await importPDFs();')

with open(js_output, 'w', encoding='utf-8') as f:
    f.write('\n'.join(js_lines))

print(f"\n{'='*60}")
print(f"JavaScript-Datei: {js_output}")
print(f"PDFs zum Importieren: {len(matches)}")
print(f"{'='*60}")
print(f"\nAnleitung:")
print(f"  1. Zotero öffnen")
print(f"  2. Extras -> Entwickler -> Run JavaScript")
print(f"  3. Inhalt der JS-Datei einfügen")
print(f"  4. 'Run' klicken und warten")
