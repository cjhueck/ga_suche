import re
from pathlib import Path

folder = Path(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\Steiner_GA')
for d in folder.iterdir():
    if 'GA019' in d.name:
        ga_folder = d
        break

# Prüfe Hauptdatei
main_file = ga_folder / "GA019 (1.) GEDANKEN WÄHREND DER ZEIT DES KRIEGES. Für Deutsche und diejenigen, die nicht glauben sie hassen zu müssen (1915).md"
main_content = main_file.read_text(encoding='utf-8')

# Prüfe Backup
backup_file = ga_folder / "_backups" / "GA019 (1.) GEDANKEN WÄHREND DER ZEIT DES KRIEGES. Für Deutsche und diejenigen, die nicht glauben sie hassen zu müssen (1915)_backup.md"
backup_content = backup_file.read_text(encoding='utf-8')

print("=== HAUPTDATEI ===")
# Finde Beispiele
for m in re.finditer(r'.{20}\|\d+\|.{20}', main_content):
    print(m.group(0).replace('\n', ' '))
    if '|11|' in m.group(0):
        break

print("\n=== BACKUP ===")
for m in re.finditer(r'.{20}\|\d+\|.{20}', backup_content):
    print(m.group(0).replace('\n', ' '))
    if '|11|' in m.group(0):
        break

