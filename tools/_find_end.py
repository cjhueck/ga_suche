import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Finde Ende von showLectureFromAdvancedSearch: naechstes } bei indent 4 nach Zeile 12163
# Muss die Klammern zaehlen um das wirkliche Ende zu finden
depth = 0
start = 12162  # 0-indexiert = Zeile 12163
for i in range(start, min(start + 2000, len(lines))):
    l = lines[i]
    for ch in l:
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                print(f'Funktionsende bei Zeile {i+1}')
                for j in range(i+1, min(i+6, len(lines))):
                    print(f'  Danach {j+1}: {repr(lines[j][:60])}')
                break
    else:
        continue
    break
