import json
import glob
import os

combined = {}
error_files = []
skipped = []

# Get all keyword database files
files = sorted(glob.glob('keywords-database-GA*.json'))

# Exclude the combined file itself
files = [f for f in files if 'combined' not in f]

print(f"Found {len(files)} files to process...\n")

for filepath in files:
    filename = os.path.basename(filepath)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            combined.update(data)
        print(f"✓ {filename:40} ({len(data):4} entries)")
    except json.JSONDecodeError as e:
        print(f"✗ {filename:40} JSON Error: line {e.lineno}")
        error_files.append(filename)
    except Exception as e:
        print(f"✗ {filename:40} Error: {str(e)[:50]}")
        error_files.append(filename)

print(f"\n{'='*70}")
print(f"Successfully merged: {len(files) - len(error_files)} files")
print(f"Total entries: {len(combined)}")

if error_files:
    print(f"\nFiles with errors ({len(error_files)}):")
    for f in error_files:
        print(f"  - {f}")

# Write combined file
print(f"\nWriting combined file...")
with open('keywords-database-combined.json', 'w', encoding='utf-8') as f:
    json.dump(combined, f, ensure_ascii=False, indent=2)
print(f"✓ Created: keywords-database-combined.json")

