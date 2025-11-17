import re

line = '[^0]:    ${ }^{1}$ [Alle Stellen aus von Goethe verfaßten Briefen sind zitiert nach der sog. Weimarer Ausgabe (= WA) oder Sophien-Ausgabe von Goethes Werken, Abteilung IV: Briefe, 50 Bde., Weimar 1887-1912; die beiden Ziffern beziehen sich auf Band und Seitenzahl dieser Abteilung. - Hinzufügungen des Herausgebers sind in eckige Klammern gesetzt.]'

print('Line:', repr(line))
print('Stripped:', repr(line.strip()))

# Test verschiedene Patterns
patterns = [
    r'^\[\^0\]:\s+\$\{\s*\}^{\s*\{(\d+)\}\s*\}\$\s+(.+)$',
    r'\[\^0\]:\s+\$\{\s*\}^{\s*\{(\d+)\}\s*\}\$\s+(.+)$',
    r'\[\^0\]:\s+\$\{\s*\}^{\s*\{(\d+)\}\s*\}\$\s+(.+)$',
]

for i, pattern in enumerate(patterns):
    print(f'\nPattern {i+1}: {pattern}')
    match = re.search(pattern, line.strip())
    if match:
        print(f'  Match found! Groups: {match.groups()}')
    else:
        print('  No match')

# Test mit einfacherem Pattern
simple_pattern = r'\[\^0\]:.*?\$\{\s*\}^{\s*\{(\d+)\}\s*\}\$\s+(.+)$'
print(f'\nSimple pattern: {simple_pattern}')
match = re.search(simple_pattern, line.strip())
if match:
    print(f'  Match found! Groups: {match.groups()}')
else:
    print('  No match')

