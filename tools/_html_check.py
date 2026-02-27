import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html','r',encoding='utf-8') as f:
    content = f.read()
idx = content.find('app.js')
print('Kontext um app.js:', repr(content[max(0,idx-80):idx+80]))

# Suche showLectureFromAdvancedSearch in app.html
count = content.count('showLectureFromAdvancedSearch')
print(f'\nshowLectureFromAdvancedSearch in app.html: {count}x')

# Suche blkref in app.html
count2 = content.count('blkref')
print(f'blkref in app.html: {count2}x')

# Gibt es ein window.showLectureFromAdvancedSearch in app.html?
if 'window.showLectureFromAdvancedSearch' in content:
    idx2 = content.find('window.showLectureFromAdvancedSearch')
    print(f'window.showLectureFromAdvancedSearch gefunden bei Index {idx2}')
    print(repr(content[max(0,idx2-20):idx2+80]))
else:
    print('window.showLectureFromAdvancedSearch NICHT in app.html')
