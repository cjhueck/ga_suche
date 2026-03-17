import sqlite3
import os
import json
import shutil

db_path = r'C:\Users\chuec\OneDrive\Dokumente\Citavi 7\Projects\Organicism\Organicism.ctv6'
attach_dir = r'C:\Users\chuec\OneDrive\Dokumente\Citavi 7\Projects\Organicism\Citavi Attachments'
cache_base = r'C:\Users\chuec\AppData\Local\Swiss Academic Software\Citavi 7\ProjectCache'
export_dir = r'C:\Users\chuec\OneDrive\Dokumente\Citavi 7\Projects\Organicism\ZoteroExport'

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT Address FROM Location WHERE Address IS NOT NULL AND Address != ''")
rows = cur.fetchall()

# Build index of all files in ProjectCache
cache_index = {}
if os.path.exists(cache_base):
    for subdir in os.listdir(cache_base):
        sub_attach = os.path.join(cache_base, subdir, "Citavi Attachments")
        if os.path.exists(sub_attach):
            for f in os.listdir(sub_attach):
                cache_index[f] = os.path.join(sub_attach, f)

print(f"Dateien im ProjectCache: {len(cache_index)}")

# Parse DB entries
cached_entries = []   # (guid_filename, readable_name, full_cache_path)
direct_entries = []   # (readable_name) - files with readable names in attach_dir

for (addr,) in rows:
    try:
        data = json.loads(addr)
    except json.JSONDecodeError:
        continue

    if data.get("LinkedResourceType") != 1:
        continue

    uri = data.get("UriString", "")
    if not uri.lower().endswith(".pdf"):
        continue

    cache_path = data.get("CacheFilePath", "")
    if cache_path:
        guid_file = os.path.basename(cache_path)
        cached_entries.append((guid_file, uri))
    else:
        direct_entries.append(uri)

# Create export directory
os.makedirs(export_dir, exist_ok=True)

# Copy .ctv6 file
print(f"\n=== Kopiere .ctv6 Datei ===")
shutil.copy2(db_path, os.path.join(export_dir, "Organicism.ctv6"))
print(f"  OK: Organicism.ctv6")

# Copy PDFs with readable names from attach_dir
copied_direct = 0
missing_direct = 0
for name in direct_entries:
    src = os.path.join(attach_dir, name)
    dst = os.path.join(export_dir, name)
    if os.path.exists(src):
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
        copied_direct += 1
    else:
        missing_direct += 1

print(f"\n=== PDFs mit lesbarem Namen ===")
print(f"  Kopiert: {copied_direct}")
print(f"  Nicht gefunden: {missing_direct}")

# Copy cached PDFs from ProjectCache, renamed to readable names
copied_cache = 0
missing_cache = 0
missing_list = []
for guid_file, readable in cached_entries:
    dst = os.path.join(export_dir, readable)
    if guid_file in cache_index:
        src = cache_index[guid_file]
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
        copied_cache += 1
    else:
        # Also check attach_dir directly with readable name
        src_alt = os.path.join(attach_dir, readable)
        if os.path.exists(src_alt):
            if not os.path.exists(dst):
                shutil.copy2(src_alt, dst)
            copied_cache += 1
        else:
            missing_cache += 1
            missing_list.append((guid_file, readable))

print(f"\n=== PDFs aus ProjectCache (GUID -> lesbarer Name) ===")
print(f"  Kopiert und umbenannt: {copied_cache}")
print(f"  Nicht gefunden: {missing_cache}")

if missing_list:
    print(f"\n  Fehlende Dateien:")
    for g, r in missing_list[:20]:
        print(f"    {g} -> {r}")

# Final count
export_files = [f for f in os.listdir(export_dir) if f.lower().endswith('.pdf')]
print(f"\n{'='*60}")
print(f"ERGEBNIS")
print(f"{'='*60}")
print(f"PDFs im Export-Ordner: {len(export_files)}")
print(f"Export-Ordner: {export_dir}")
print(f"")
print(f"Nächster Schritt:")
print(f"  1. Zotero öffnen")
print(f"  2. Datei -> Importieren -> Aus einer Datei")
print(f"  3. '{export_dir}\\Organicism.ctv6' auswählen")
print(f"  4. 'Dateien in den Zotero-Speicherordner kopieren' aktivieren")

conn.close()
