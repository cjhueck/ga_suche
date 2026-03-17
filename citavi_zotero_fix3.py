import sqlite3
import os
import json
import shutil
import re
from collections import defaultdict

db_path = r'C:\Users\chuec\OneDrive\Dokumente\Citavi 7\Projects\Organicism\Organicism.ctv6'
export_dir = r'C:\Users\chuec\OneDrive\Dokumente\Citavi 7\Projects\Organicism\ZoteroExport'
zotero_db = r'C:\Users\chuec\Zotero\zotero.sqlite'

# --- Step 1: Citavi ---
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
        if ref_id not in ref_to_pdf:
            ref_to_pdf[ref_id] = uri

cur_c.execute("SELECT ID, Title, Year, ShortTitle FROM Reference")
citavi_refs = {}
for row in cur_c.fetchall():
    citavi_refs[row[0]] = {"title": row[1] or "", "year": row[2] or "", "short_title": row[3] or ""}

cur_c.execute("""
    SELECT ra.ReferenceID, p.LastName
    FROM ReferenceAuthor ra
    JOIN Person p ON ra.PersonID = p.ID
    ORDER BY ra.ReferenceID
""")
ref_authors = defaultdict(list)
for ref_id, last in cur_c.fetchall():
    ref_authors[ref_id].append(last or "")

conn_c.close()

# --- Step 2: Zotero ---
tmp_db = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\zotero_copy4.sqlite'
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
    zotero_items[item_id] = {"key": key, "title": title or ""}

cur_z.execute("""
    SELECT i.itemID, idv.value
    FROM items i
    JOIN itemData id ON i.itemID = id.itemID
    JOIN itemDataValues idv ON id.valueID = idv.valueID
    JOIN fields f ON id.fieldID = f.fieldID
    WHERE f.fieldName = 'date'
""")
for item_id, date_val in cur_z.fetchall():
    if item_id in zotero_items:
        zotero_items[item_id]["year"] = date_val or ""

cur_z.execute("""
    SELECT ic.itemID, c.lastName
    FROM itemCreators ic
    JOIN creators c ON ic.creatorID = c.creatorID
    ORDER BY ic.itemID, ic.orderIndex
""")
z_authors = defaultdict(list)
for item_id, last in cur_z.fetchall():
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
def strip_punct(s):
    s = re.sub(r'[^\w\s]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def norm(s):
    return strip_punct((s or "").lower())

def first_words(s, n=4):
    words = norm(s).split()
    return " ".join(words[:n]) if len(words) >= n else " ".join(words)

# Build Zotero indexes
z_by_norm = defaultdict(list)
z_by_fw_year = defaultdict(list)  # first words + year
z_all = []  # for substring matching

for z_id, info in zotero_items.items():
    t = norm(info["title"])
    year = str(info.get("year", ""))[:4]
    authors = z_authors.get(z_id, [])
    first_auth = norm(authors[0]) if authors else ""
    
    z_by_norm[t].append(z_id)
    
    fw = first_words(info["title"], 4)
    if year and fw:
        z_by_fw_year[(fw, year)].append(z_id)
    
    z_all.append((z_id, t, year, first_auth))

# Match
matches = {}
used_citavi = set()

def try_match(ref_id, z_id, strategy, pdf_name):
    if z_id in items_with_pdf:
        return False
    if z_id in matches:
        return False
    matches[z_id] = (zotero_items[z_id]["key"], pdf_name, strategy)
    used_citavi.add(ref_id)
    return True

# Pass 1: Exact normalized title
for ref_id, pdf_name in ref_to_pdf.items():
    if ref_id in used_citavi:
        continue
    pdf_path = os.path.join(export_dir, pdf_name)
    if not os.path.exists(pdf_path):
        continue
    
    c_title = norm(citavi_refs[ref_id]["title"])
    if not c_title:
        continue
    
    for z_id in z_by_norm.get(c_title, []):
        if try_match(ref_id, z_id, "exact_norm", pdf_name):
            break

print(f"Nach Pass 1 (exact_norm): {len(matches)}")

# Pass 2: First 4 words + year
for ref_id, pdf_name in ref_to_pdf.items():
    if ref_id in used_citavi:
        continue
    pdf_path = os.path.join(export_dir, pdf_name)
    if not os.path.exists(pdf_path):
        continue
    
    info = citavi_refs[ref_id]
    fw = first_words(info["title"], 4)
    year = str(info.get("year", ""))[:4]
    
    if fw and year:
        candidates = z_by_fw_year.get((fw, year), [])
        if len(candidates) == 1:
            try_match(ref_id, candidates[0], "first_words_year", pdf_name)

print(f"Nach Pass 2 (first_words+year): {len(matches)}")

# Pass 3: Substring matching (one title contains the other)
remaining_citavi = []
for ref_id, pdf_name in ref_to_pdf.items():
    if ref_id in used_citavi:
        continue
    pdf_path = os.path.join(export_dir, pdf_name)
    if not os.path.exists(pdf_path):
        continue
    info = citavi_refs[ref_id]
    c_title = norm(info["title"])
    c_year = str(info.get("year", ""))[:4]
    c_auth = norm(ref_authors.get(ref_id, [""])[0]) if ref_authors.get(ref_id) else ""
    if len(c_title) >= 10:
        remaining_citavi.append((ref_id, c_title, c_year, c_auth, pdf_name))

for ref_id, c_title, c_year, c_auth, pdf_name in remaining_citavi:
    best_z_id = None
    best_score = 0
    
    for z_id, z_title, z_year, z_auth in z_all:
        if z_id in matches or z_id in items_with_pdf:
            continue
        if not z_title or len(z_title) < 8:
            continue
        
        # Year must match if both have year
        if c_year and z_year and c_year != z_year:
            continue
        
        # Check substring
        is_sub = c_title in z_title or z_title in c_title
        if not is_sub:
            continue
        
        # Prefer matches where author also matches
        score = min(len(c_title), len(z_title))
        if c_auth and z_auth and c_auth == z_auth:
            score += 1000
        
        if score > best_score:
            best_score = score
            best_z_id = z_id
    
    if best_z_id and best_score >= 15:
        try_match(ref_id, best_z_id, "substring", pdf_name)

print(f"Nach Pass 3 (substring): {len(matches)}")

# Pass 4: Author + Year (unique match)
z_by_auth_year = defaultdict(list)
for z_id, z_title, z_year, z_auth in z_all:
    if z_id in matches and z_id not in items_with_pdf:
        continue
    if z_auth and z_year:
        z_by_auth_year[(z_auth, z_year)].append(z_id)

for ref_id, pdf_name in ref_to_pdf.items():
    if ref_id in used_citavi:
        continue
    pdf_path = os.path.join(export_dir, pdf_name)
    if not os.path.exists(pdf_path):
        continue
    
    info = citavi_refs[ref_id]
    c_year = str(info.get("year", ""))[:4]
    authors = ref_authors.get(ref_id, [])
    c_auth = norm(authors[0]) if authors else ""
    
    if c_auth and c_year:
        candidates = [z for z in z_by_auth_year.get((c_auth, c_year), []) if z not in matches and z not in items_with_pdf]
        if len(candidates) == 1:
            try_match(ref_id, candidates[0], "author_year_unique", pdf_name)

print(f"Nach Pass 4 (author+year unique): {len(matches)}")

# Stats
strategy_counts = defaultdict(int)
for z_id, (_, _, strat) in matches.items():
    strategy_counts[strat] += 1

unmatched = [(ref_id, citavi_refs[ref_id]["title"], pdf) for ref_id, pdf in ref_to_pdf.items() 
             if ref_id not in used_citavi and os.path.exists(os.path.join(export_dir, pdf))]

print(f"\n{'='*60}")
print(f"ENDERGEBNIS")
print(f"{'='*60}")
print(f"Zugeordnete PDFs: {len(matches)}")
for strat, count in sorted(strategy_counts.items()):
    print(f"  {strat}: {count}")
print(f"Bereits mit PDF in Zotero: {len(items_with_pdf)}")
print(f"Nicht zugeordnet (PDF vorhanden, kein Match): {len(unmatched)}")
print(f"Zotero Items gesamt: {len(zotero_items)}")

if unmatched:
    print(f"\nNicht zugeordnet (erste 20):")
    for ref_id, title, pdf in unmatched[:20]:
        year = citavi_refs[ref_id].get("year", "")
        auth = ref_authors.get(ref_id, ["?"])[0]
        try:
            print(f"  [{auth} {year}] '{title}'")
        except UnicodeEncodeError:
            print(f"  [{auth} {year}] '{title.encode('ascii', 'replace').decode()}'")


# --- Step 4: Generate JavaScript ---
js_output = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\zotero_import.js'
export_dir_js = export_dir.replace('\\', '/')

js_lines = []
js_lines.append(f'// Zotero Import Script - {len(matches)} PDFs')
js_lines.append('// Run in Zotero: Tools -> Developer -> Run JavaScript')
js_lines.append(f'var exportDir = {json.dumps(export_dir_js)};')
js_lines.append('')
js_lines.append('var files = [')
items_list = list(matches.items())
for i, (z_id, (z_key, pdf_name, _)) in enumerate(items_list):
    comma = "," if i < len(items_list) - 1 else ""
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
js_lines.append('      if (count % 50 === 0) {')
js_lines.append('        Zotero.debug("Imported " + count + "/" + files.length + " PDFs...");')
js_lines.append('      }')
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
print(f"Bereit zum Import: {len(matches)} PDFs")
print(f"{'='*60}")
