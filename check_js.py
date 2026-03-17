with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\zotero_import.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Zeilen gesamt: {len(lines)}")
count = sum(1 for l in lines if l.strip().startswith('["'))
print(f"PDF-Eintraege: {count}")
print()
print("Erste 5 Zeilen:")
for l in lines[:5]:
    print(l.rstrip())
print("...")
print("Letzte 5 Zeilen:")
for l in lines[-5:]:
    print(l.rstrip())
