# -*- coding: utf-8 -*-
with open('Steiner_GA/GA001-Goethes Naturwissenschaftliche Schriften/GA001/GA001.md', 'r', encoding='utf-8') as f:
    line = f.readlines()[99]

pos = line.find('[WA')
if pos >= 0:
    snippet = line[pos:pos+20]
    print('Snippet:', repr(snippet))
    print('Characters:')
    for i, c in enumerate(snippet):
        print(f'  {i}: {repr(c)} (ord={ord(c)})')
    
    # Prüfe ob ¹ direkt nach ] kommt
    pos_close = snippet.find(']')
    if pos_close >= 0:
        print(f'\nFound ] at position {pos_close}')
        if pos_close + 1 < len(snippet):
            next_char = snippet[pos_close + 1]
            print(f'Next char after ]: {repr(next_char)} (ord={ord(next_char)})')
            print(f'Is ¹: {next_char == "¹"}')

