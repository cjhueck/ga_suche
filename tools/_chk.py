import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'r', encoding='utf-8') as f:
    content = f.read()

print('window.showLectureFromAdvancedSearch:', content.count('window.showLectureFromAdvancedSearch'))
print('GA-Links nach Zitat:', content.count('GA-Links nach Zitat'))
print('openMapLecture:', content.count('openMapLecture'))

# Wird app.js vom Server eingebunden?
with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html', 'r', encoding='utf-8') as f:
    html = f.read()
import re
idx = html.find('app.js')
print()
print('app.js in app.html:', idx >= 0)
print('Kontext:', repr(html[max(0,idx-40):idx+60]))
