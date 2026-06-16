// End-to-End-Diagnose: simuliert das Frontend-Matching für ein konkretes
// Zitat gegen den echten GA002-Quelltext. Findet, ob das Splitting +
// Sentinel-Strip + Flex-Regex das Zitat in der Quelle korrekt findet.

(async () => {
  // 1. Lade das Buch GA002
  const r = await fetch('http://localhost:3003/api/book/GA002');
  const book = await r.json();
  let raw = book.content;

  // 2. Replicate die Frontend-Render-Pipeline: marked.parse + convertPageMarkers
  // Der einfachen Halber: mache nur convertPageMarkers (markdown ist primär Text)
  // und schau, ob Block-IDs ` ^xyz` im Text vorkommen.
  function convertPageMarkers(html) {
    return html.replace(/\|(\d{1,4})\|/g, (m, n) =>
      '<span class="page-break-container" title="Seite ' + n + '"><span class="page-break-num">' + n + '</span><span class="page-break-bar">|</span></span>'
    );
  }

  // Suche den Absatz, der "Prinzipes erkannt" enthält
  // Steiner-Bücher haben ` ^xyz`-Block-IDs am Ende der Absätze
  const lines = raw.split('\n');
  let paraIdx = -1;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('Prinzipes erkannt')) { paraIdx = i; break; }
  }
  if (paraIdx < 0) { console.log('Stelle nicht gefunden'); return; }

  // Zeige Kontext: 5 Zeilen
  console.log('=== Kontext um "Prinzipes erkannt" (raw markdown) ===');
  for (let i = Math.max(0, paraIdx - 2); i < Math.min(lines.length, paraIdx + 3); i++) {
    console.log(`L${i}: ${lines[i].substring(0, 200)}${lines[i].length > 200 ? '…' : ''}`);
  }
  console.log();

  // 3. Simuliere die Backend-Snippet-Splitting-Logik
  const originalQuote = "Eine im Sinne der Goetheschen Weltanschauung begründete Erkenntniswissenschaft legt das Hauptgewicht darauf, dass sie dem Prinzip der Erfahrung durchaus treu bleibt. Niemand hat so wie Goethe die ausschließliche Geltung dieses Prinzipes erkannt. [...] Alle höheren Ansichten über die Natur durften ihm als nichts denn als Erfahrung erscheinen. Sie sollten 'höhere Natur innerhalb der Natur' sein.";

  const ESSAY_BRACKET_RE = /\[\s*(?:\.\s*){2,}\.?\s*\]|\[\s*…\s*\]|\(\s*(?:\.\s*){2,}\.?\s*\)|\(\s*…\s*\)|\[[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß. ]{0,28}\]/g;
  const stripBoundaryPunct = (s) => s
    .replace(/^[\s,;.:!?„"""'\u2018\u2019\u201A\u201B\u201C\u201D\u201E\u201F«»\-–—]+/, '')
    .replace(/[\s,;.:!?„"""'\u2018\u2019\u201A\u201B\u201C\u201D\u201E\u201F«»\-–—]+$/, '')
    .trim();
  let cleaned = originalQuote
    .replace(/^\s*[\*_]+|[\*_]+\s*$/g, '')
    .replace(/^\s*[„"]+|[""]+\s*$/g, '')
    .replace(/\s+/g, ' ').trim();
  const fragments = cleaned.split(ESSAY_BRACKET_RE).map(s => stripBoundaryPunct(s.trim())).filter(s => s.length >= 6);
  console.log('=== Backend-Fragmente ===');
  fragments.forEach((f, i) => console.log(`F${i+1} (${f.length}ch): "${f}"`));
  console.log();

  // 4. Simuliere die Side-Panel-DOM-Erstellung für den relevanten Absatz
  // Vereinfacht: wir nehmen den ganzen book.content (markdown), rendern Page-Markers,
  // dann simulieren wir, dass jeder Absatz der Markdown-Datei zu einem
  // paragraphElement wird.
  const paraStart = lines.lastIndexOf('', paraIdx);
  // Raw-Absatz extrahieren: vom nächsten leeren bis zum nächsten leeren
  let pStart = paraIdx; while (pStart > 0 && lines[pStart - 1].trim() !== '') pStart--;
  let pEnd = paraIdx; while (pEnd < lines.length - 1 && lines[pEnd + 1].trim() !== '') pEnd++;
  const paraRaw = lines.slice(pStart, pEnd + 1).join('\n');
  console.log('=== Absatz-Roh-Markdown (vor Render) ===');
  console.log(paraRaw);
  console.log();

  // 5. Page-Markers anwenden
  const paraHTML = convertPageMarkers(paraRaw);
  console.log('=== Absatz-HTML nach convertPageMarkers ===');
  console.log(paraHTML.substring(0, 600) + (paraHTML.length > 600 ? '…' : ''));
  console.log();

  // 6. Sentinel-Replace + Tag-Strip + Frontend-Matching
  const PB_SENTINEL = '\u0002P\u0002';
  const PB_RE_FRAG = '\\u0002P\\u0002';
  const TAG_SENTINEL = '\u0001T\u0001';
  const TAG_RE_FRAG = '\\u0001T\\u0001';
  const PB_FULL_RE = /<span\s+class="page-break-container"[^>]*>\s*<span\s+class="page-break-num"[^>]*>[^<]*<\/span>\s*<span\s+class="page-break-bar"[^>]*>[^<]*<\/span>\s*<\/span>/g;

  const QUOTE_CHARS_RE = /[\u0022\u0027\u00AB\u00BB\u00B4\u2018\u2019\u201A\u201B\u201C\u201D\u201E\u201F\u2032\u2033\u2039\u203A]/;
  const QUOTE_FLEX_CLASS = '[\u0022\u0027\u00AB\u00BB\u00B4\u2018\u2019\u201A\u201B\u201C\u201D\u201E\u201F\u2032\u2033\u2039\u203A]?';
  const NOISE_RE_FRAG = '[\u00B2\u00B3\u00B9\u2070-\u2079\u2080-\u2089]';
  const SENTINEL_OPT = `(?:${PB_RE_FRAG}|${TAG_RE_FRAG}|${NOISE_RE_FRAG})*`;
  const buildFlexRegex = (term) => {
    let out = '';
    for (let i = 0; i < term.length; i++) {
      const ch = term[i];
      if (QUOTE_CHARS_RE.test(ch)) out += QUOTE_FLEX_CLASS;
      else if (/\s/.test(ch)) {
        while (i + 1 < term.length && /\s/.test(term[i + 1])) i++;
        out += `(?:\\s|${PB_RE_FRAG}|${TAG_RE_FRAG}|${NOISE_RE_FRAG})+`;
      } else out += ch.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      if (i < term.length - 1) out += SENTINEL_OPT;
    }
    return out;
  };

  let workingHTML = paraHTML.replace(PB_FULL_RE, () => PB_SENTINEL);
  workingHTML = workingHTML.replace(/<[^>]+>/g, () => TAG_SENTINEL);

  console.log('=== Frontend-Matching ===');
  fragments.forEach((f, i) => {
    const pattern = buildFlexRegex(f);
    try {
      const re = new RegExp('(' + pattern + ')', 'gi');
      const matches = workingHTML.match(re);
      console.log(`F${i+1} match: ${matches ? matches.length + ' Treffer' : '0 Treffer'}`);
      if (matches && matches.length > 0) console.log(`  → "${matches[0].substring(0, 200).replace(/\u0001T\u0001/g, '[T]').replace(/\u0002P\u0002/g, '[PB]')}…"`);
    } catch (e) {
      console.log(`F${i+1} regex-Fehler: ${e.message}`);
    }
  });
})();
