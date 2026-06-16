// Spezifischer Test des User-Beispiels:
// LLM-Zitat: "Das Richtige ist, dass der Goethe'schen Denkweise eine wesentlich
// andere Philosophie als die Kantische immanent war. So kam es, dass Goethe die
// Kant'schen Feststellungen stets missverstand [...]. Nicht die Dichtungsgabe
// und nicht der gesunde Menschenverstand hinderten ihn, sondern nur das, dass
// seine Weltansicht gerade der entgegengesetzte Pol der Kantischen ist."

(async () => {
  // Echte Backend-Snippet-Generierung simulieren
  const ESSAY_BRACKET_RE = /\[\s*(?:\.\s*){2,}\.?\s*\]|\[\s*…\s*\]|\(\s*(?:\.\s*){2,}\.?\s*\)|\(\s*…\s*\)|\[[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß. ]{0,28}\]/g;
  const stripBoundaryPunct = (s) => s
    .replace(/^[\s,;.:!?„"""'\u2018\u2019\u201A\u201B\u201C\u201D\u201E\u201F«»\-–—]+/, '')
    .replace(/[\s,;.:!?„"""'\u2018\u2019\u201A\u201B\u201C\u201D\u201E\u201F«»\-–—]+$/, '')
    .trim();

  const userQuote = "Das Richtige ist, dass der Goethe'schen Denkweise eine wesentlich andere Philosophie als die Kantische immanent war. So kam es, dass Goethe die Kant'schen Feststellungen stets missverstand [...]. Nicht die Dichtungsgabe und nicht der gesunde Menschenverstand hinderten ihn, sondern nur das, dass seine Weltansicht gerade der entgegengesetzte Pol der Kantischen ist.";

  let cleaned = userQuote.replace(/\s+/g, ' ').trim();
  const backendFragments = cleaned.split(ESSAY_BRACKET_RE).map(s => stripBoundaryPunct(s.trim())).filter(s => s.length >= 6);
  console.log('=== Backend-Fragmente ===');
  backendFragments.forEach((f, i) => console.log(`F${i+1} (${f.length}ch): "${f}"`));

  // Echten Absatz aus GA046/11 holen
  const r = await fetch('http://localhost:3003/api/full-lecture/GA046/11');
  const data = await r.json();
  const paragraphs = (data.lecture && data.lecture.paragraphs) || [];
  const hit = paragraphs.find(p => /Das Richtige ist/.test(p.content || ''));
  console.log('\n=== Absatz raw ===');
  console.log(hit.content);

  // Frontend-Match-Simulation (incl. Fallback auf Komma-Split)
  function convertPageMarkers(html) {
    return html.replace(/\|(\d{1,4})\|/g, (m, n) =>
      '<span class="page-break-container" title="Seite ' + n + '"><span class="page-break-num">' + n + '</span><span class="page-break-bar">|</span></span>'
    );
  }
  const paraHTML = convertPageMarkers(hit.content);

  const PB_SENTINEL = '\u0002P\u0002';
  const PB_RE_FRAG = '\\u0002P\\u0002';
  const TAG_SENTINEL = '\u0001T\u0001';
  const TAG_RE_FRAG = '\\u0001T\\u0001';
  const NOISE_RE_FRAG = '[\u00B2\u00B3\u00B9\u2070-\u2079\u2080-\u2089]';
  const SENTINEL_OPT = `(?:${PB_RE_FRAG}|${TAG_RE_FRAG}|${NOISE_RE_FRAG})*`;
  const PB_FULL_RE = /<span\s+class="page-break-container"[^>]*>\s*<span\s+class="page-break-num"[^>]*>[^<]*<\/span>\s*<span\s+class="page-break-bar"[^>]*>[^<]*<\/span>\s*<\/span>/g;
  const QUOTE_CHARS_RE = /[\u0022\u0027\u00AB\u00BB\u00B4\u2018\u2019\u201A\u201B\u201C\u201D\u201E\u201F\u2032\u2033\u2039\u203A]/;
  const QUOTE_FLEX_CLASS = '[\u0022\u0027\u00AB\u00BB\u00B4\u2018\u2019\u201A\u201B\u201C\u201D\u201E\u201F\u2032\u2033\u2039\u203A]?';
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

  const tryMatch = (subTerm, label) => {
    if (!subTerm || subTerm.length < 5) return false;
    const re = new RegExp('(' + buildFlexRegex(subTerm) + ')', 'gi');
    const before = workingHTML;
    workingHTML = workingHTML.replace(re, m => '<mark>' + m + '</mark>');
    const matched = workingHTML !== before;
    console.log(`  ${label}: ${matched ? '✓' : '✗'} "${subTerm.substring(0, 100)}${subTerm.length > 100 ? '…' : ''}"`);
    return matched;
  };

  console.log('\n=== Frontend-Matching mit Fallback ===');
  backendFragments.forEach((frag, idx) => {
    console.log(`\n→ F${idx+1}:`);
    if (tryMatch(frag, 'WHOLE')) return;
    console.log('  Fallback: Komma/Punkt-Split');
    const subParts = frag.split(/[.,;:]+\s+/)
      .map(s => s.trim().replace(/^[\s,;.:!?„"""'\u2018\u2019\u201C\u201D\u201E«»\-–—]+|[\s,;.:!?„"""'\u2018\u2019\u201C\u201D\u201E«»\-–—]+$/g, ''))
      .filter(s => s.length >= 12);
    subParts.forEach((p, i) => tryMatch(p, '  Sub' + (i + 1)));
  });
})();
