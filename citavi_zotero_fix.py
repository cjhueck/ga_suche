import sqlite3
import os
import json
import shutil

db_path = r'C:\Users\chuec\OneDrive\Dokumente\Citavi 7\Projects\Organicism\Organicism.ctv6'
export_dir = r'C:\Users\chuec\OneDrive\Dokumente\Citavi 7\Projects\Organicism\ZoteroExport'
zotero_db = r'C:\Users\chuec\Zotero\zotero.sqlite'

# --- Step 1: Build Citavi ReferenceID -> PDF filename mapping ---
conn_c = sqlite3.connect(db_path)
cur_c = conn_c.cursor()

# Location table: ReferenceID -> Address (JSON with PDF info)
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

# Reference table: get title for each reference
cur_c.execute("SELECT ID, Title, Year, ShortTitle FROM Reference")
citavi_refs = {}
for row in cur_c.fetchall():
    citavi_refs[row[0]] = {"title": row[1], "year": row[2], "short_title": row[3]}

conn_c.close()

print(f"Citavi Referenzen mit PDF: {len(ref_to_pdf)}")
print(f"Citavi Referenzen gesamt: {len(citavi_refs)}")

# --- Step 2: Get Zotero items that DON'T have PDF attachments ---
tmp_db = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\zotero_copy2.sqlite'
shutil.copy2(zotero_db, tmp_db)
conn_z = sqlite3.connect(tmp_db)
cur_z = conn_z.cursor()

# Get all non-attachment items with their titles
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

# Get items that already have PDF attachments
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

print(f"\nZotero Items (Bücher/Artikel): {len(zotero_items)}")
print(f"Davon bereits mit PDF: {len(items_with_pdf)}")
print(f"Ohne PDF: {len(zotero_items) - len(items_with_pdf)}")

# --- Step 3: Match Citavi -> Zotero by title ---
# Normalize titles for matching
def normalize(s):
    if not s:
        return ""
    return s.lower().strip().replace("  ", " ")

# Build Zotero title index
z_title_index = {}
for item_id, info in zotero_items.items():
    norm = normalize(info["title"])
    if norm not in z_title_index:
        z_title_index[norm] = []
    z_title_index[norm].append(item_id)

matched = 0
unmatched = 0
already_has = 0
matches = []  # (zotero_item_id, zotero_key, pdf_filename)

for ref_id, pdf_name in ref_to_pdf.items():
    citavi_info = citavi_refs.get(ref_id, {})
    citavi_title = normalize(citavi_info.get("title", ""))
    
    if citavi_title and citavi_title in z_title_index:
        for z_item_id in z_title_index[citavi_title]:
            if z_item_id in items_with_pdf:
                already_has += 1
            else:
                z_key = zotero_items[z_item_id]["key"]
                pdf_path = os.path.join(export_dir, pdf_name)
                if os.path.exists(pdf_path):
                    matches.append((z_item_id, z_key, pdf_name, zotero_items[z_item_id]["title"]))
                    matched += 1
                else:
                    unmatched += 1
    else:
        unmatched += 1

print(f"\n=== MATCHING ===")
print(f"Zugeordnet (PDF vorhanden, noch nicht in Zotero): {matched}")
print(f"Bereits mit PDF in Zotero: {already_has}")
print(f"Nicht zugeordnet: {unmatched}")

# --- Step 4: Generate Zotero JavaScript to import PDFs ---
js_output = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\zotero_import.js'

# Zotero JS API to add file attachments
js_lines = []
js_lines.append(f'// Zotero Import Script - {len(matches)} PDFs')
js_lines.append(f'// Run in Zotero: Tools -> Developer -> Run JavaScript')
js_lines.append(f'var exportDir = {json.dumps(export_dir.replace(chr(92), "/"))};')
js_lines.append('')

# Process in batches
batch_size = 50
total_batches = (len(matches) + batch_size - 1) // batch_size

js_lines.append(f'var files = [')
for i, (z_id, z_key, pdf_name, title) in enumerate(matches):
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
js_lines.append('      Zotero.debug("Error for " + key + ": " + e);')
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
print(f"JavaScript-Datei erstellt: {js_output}")
print(f"Enthält {len(matches)} PDF-Zuordnungen")
print(f"{'='*60}")
print(f"\nAnleitung:")
print(f"  1. Zotero öffnen")
print(f"  2. Tools -> Developer -> Run JavaScript")
print(f"  3. Inhalt von {js_output} einfügen")
print(f"  4. 'Run' klicken")

# Show some examples
print(f"\nBeispiel-Zuordnungen:")
for _, z_key, pdf_name, title in matches[:5]:
    print(f"  {z_key}: '{title}' -> {pdf_name}")
