// Diagnose-Test für das GA046/11-Zitat: "Das Richtige ist, dass der Goethe'schen…"

(async () => {
  const r = await fetch('http://localhost:3003/api/full-lecture/GA046/11');
  const data = await r.json();
  const paragraphs = (data.lecture && data.lecture.paragraphs) || [];
  const hit = paragraphs.find(p => /Das Richtige ist/.test(p.content || ''));
  if (!hit) { console.log('Nicht gefunden'); return; }
  console.log('Absatz-Index:', hit.index);
  console.log('\n=== Absatz raw ===');
  console.log(hit.content);
  console.log('\n=== Hex der Stelle "Goethe?schen" und "Kant?schen" ===');
  for (const word of ['Goethe', 'Kant']) {
    const re = new RegExp(word + '.\\w+', 'g');
    let m;
    while ((m = re.exec(hit.content)) !== null) {
      const found = m[0];
      let hex = '';
      for (let i = 0; i < found.length; i++) {
        const c = found.charCodeAt(i);
        hex += c >= 32 && c <= 126 ? found[i] : `<U+${c.toString(16).toUpperCase().padStart(4, '0')}>`;
      }
      console.log(`  "${found}" → ${hex}`);
    }
  }

  // Frontend-Match-Simulation
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

  const tryMatch = (subTerm) => {
    if (!subTerm || subTerm.length < 5) return 0;
    const re = new RegExp('(' + buildFlexRegex(subTerm) + ')', 'gi');
    const before = workingHTML;
    workingHTML = workingHTML.replace(re, m => '<mark>' + m + '</mark>');
    if (workingHTML === before) return 0;
    return (workingHTML.match(/<mark>/g) || []).length - (before.match(/<mark>/g) || []).length;
  };

  // LLM Fragment 1 (vor dem [...])
  const f1 = "Das Richtige ist, dass der Goethe'schen Denkweise eine wesentlich andere Philosophie als die Kantische immanent war. So kam es, dass Goethe die Kant'schen Feststellungen stets missverstand";
  console.log('\n=== Fragment 1 ===');
  console.log(`F1 ganz (${f1.length}ch): ${tryMatch(f1)} Treffer`);
  if (workingHTML.indexOf('<mark>') < 0 || true) {
    // Fallback split
    const subs = f1.split(/[.,;:]+\s+/)
      .map(s => s.trim().replace(/^[\s,;.:!?„"""'\u2018\u2019\u201C\u201D\u201E«»\-–—]+|[\s,;.:!?„"""'\u2018\u2019\u201C\u201D\u201E«»\-–—]+$/g, ''))
      .filter(s => s.length >= 12);
    subs.forEach((s, i) => {
      const c = tryMatch(s);
      console.log(`  Sub${i+1} (${s.length}ch): ${c} Treffer — "${s}"`);
    });
  }
})();
