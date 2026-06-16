// Test: LLM korrigiert stillschweigend einen Steiner-Druckfehler ("dein"→"dem"),
// das ganze Zitat matcht dadurch nicht mehr. Frontend-Fallback splittet auf
// Satz-/Komma-Grenzen und matcht die Teilstücke einzeln.

(async () => {
  const r = await fetch('http://localhost:3003/api/book/GA002');
  const book = await r.json();
  const raw = book.content;

  // Vortrag GA030/45 mit Absätzen holen
  const r2 = await fetch('http://localhost:3003/api/full-lecture/GA030/45');
  const lecData = await r2.json();
  const paragraphs = (lecData.lecture && lecData.lecture.paragraphs) || [];
  const hit = paragraphs.find(p => /Beobachter sich verh/.test(p.content || ''));
  if (!hit) { console.log('Absatz mit Stelle nicht gefunden'); return; }
  console.log('Absatz-Index:', hit.index);
  const paraRaw = hit.content;
  console.log('\n=== Absatz raw ===');
  console.log(paraRaw);

  function convertPageMarkers(html) {
    return html.replace(/\|(\d{1,4})\|/g, (m, n) =>
      '<span class="page-break-container" title="Seite ' + n + '"><span class="page-break-num">' + n + '</span><span class="page-break-bar">|</span></span>'
    );
  }
  const paraHTML = convertPageMarkers(paraRaw);

  // Frontend match logic
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

  // Das ganze Zitat (LLM-Version mit "dem")
  const wholeQuote = "Goethe verhält sich zu dem modernen Naturforscher wie der Astronom, der durch zusammenfassende kosmische Gesetze die Erscheinungen am Himmel erklärt, zu dem Beobachter sich verhält, der durch das Fernrohr die verschiedenen Stellungen der Sterne erfahrungsgemäß feststellt";

  // Versuch 1: ganzes Fragment
  const tryMatch = (subTerm) => {
    if (!subTerm || subTerm.length < 5) return 0;
    const re = new RegExp('(' + buildFlexRegex(subTerm) + ')', 'gi');
    const before = workingHTML;
    workingHTML = workingHTML.replace(re, (m) => '<mark>' + m + '</mark>');
    if (workingHTML === before) return 0;
    return (workingHTML.match(/<mark>/g) || []).length - (before.match(/<mark>/g) || []).length;
  };

  console.log('\n=== Match-Versuch ganzes Fragment ===');
  let m = tryMatch(wholeQuote);
  console.log('Whole match:', m, 'Treffer');

  if (m === 0) {
    console.log('\n=== Fallback: Splitten auf Satz-/Komma-Grenzen ===');
    const subParts = wholeQuote.split(/[.,;:]+\s+/)
      .map(s => s.trim().replace(/^[\s,;.:!?„"""'\u2018\u2019\u201C\u201D\u201E«»\-–—]+|[\s,;.:!?„"""'\u2018\u2019\u201C\u201D\u201E«»\-–—]+$/g, ''))
      .filter(s => s.length >= 12);
    subParts.forEach((p, i) => {
      const c = tryMatch(p);
      console.log(`Sub${i+1} (${p.length}ch): ${c} Treffer — "${p.substring(0, 100)}${p.length > 100 ? '…' : ''}"`);
    });
  }
})();
