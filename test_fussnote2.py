import re

line = '[^0]:    ${ }^{1}$ [Alle Stellen aus von Goethe verfaßten Briefen sind zitiert nach der sog. Weimarer Ausgabe (= WA) oder Sophien-Ausgabe von Goethes Werken, Abteilung IV: Briefe, 50 Bde., Weimar 1887-1912; die beiden Ziffern beziehen sich auf Band und Seitenzahl dieser Abteilung. - Hinzufügungen des Herausgebers sind in eckige Klammern gesetzt.]'

print('Line:', repr(line))
print('Stripped:', repr(line.strip()))

# Test mit noch einfacherem Pattern - nur die Nummer
simple_pattern2 = r'\$\{\s*\}^{\s*\{(\d+)\}\s*\}\$'
print(f'\nVery simple pattern (just number): {simple_pattern2}')
match3 = re.search(simple_pattern2, line)
if match3:
    print(f'  Match found! Number: {match3.group(1)}')
    # Finde Position
    pos = match3.end()
    print(f'  Position after $: {pos}')
    print(f'  Text after: {line[pos:pos+50]}')
else:
    print('  No match')

# Test mit Pattern das nach [^0]: sucht und dann alles nimmt
pattern3 = r'\[\^0\]:\s+(.+)$'
match4 = re.search(pattern3, line.strip())
if match4:
    print(f'\nPattern [^0]: ... found!')
    rest = match4.group(1)
    print(f'  Rest: {rest[:100]}')
    # Jetzt suche nach ${ }^{n}$ in rest
    match5 = re.search(r'\$\{\s*\}^{\s*\{(\d+)\}\s*\}\$\s+(.+)$', rest)
    if match5:
        print(f'  Found number: {match5.group(1)}')
        print(f'  Found text: {match5.group(2)[:50]}')

