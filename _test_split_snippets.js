// Unit-Test des Backend-Snippet-Splittings (repliziert die Logik in addSnippet).

const cases = [
  {
    name: "Methode + […] + [hat]",
    input: "Für die organische Wissenschaft ist aber die Intuition die richtige Methode. […] Goethes Geist [hat] gerade deshalb, weil er auf Intuition angelegt war, im Organischen den rechten Weg gefunden.",
    expectedMin: 3,
    mustContain: ["Für die organische Wissenschaft ist aber die Intuition die richtige Methode", "Goethes Geist", "gerade deshalb, weil er auf Intuition angelegt war, im Organischen den rechten Weg gefunden"]
  },
  {
    name: "Typus [ist] mit Auslassungen",
    input: "Der Typus [ist] keine abgeschlossene eingefrorene Begriffsform […], sondern […] er ist flüssig […], er [kann] die mannigfaltigsten Gestaltungen annehmen. Die Zahl dieser Gestaltungen ist eine unendliche.",
    expectedMin: 3,
    mustContain: ["keine abgeschlossene eingefrorene Begriffsform", "er ist flüssig", "die mannigfaltigsten Gestaltungen annehmen"]
  },
  {
    name: "ASCII-Auslassung [...]",
    input: "Ich habe [...] Goethe den Kopernikus und Kepler der Wissenschaft vom Organischen genannt.",
    expectedMin: 1,
    mustContain: ["Goethe den Kopernikus und Kepler der Wissenschaft vom Organischen genannt"]
  },
  {
    name: "Ohne Klammern (1 bleiben)",
    input: "Die Schöpfung der Welt ist immer ein Werk des Geistes.",
    expectedMin: 1,
    mustContain: ["Die Schöpfung der Welt"]
  },
  {
    name: "Mit [Anm. d. Hrsg.]",
    input: "Das Wesentliche [Anm. d. Hrsg.] ist hier zu betonen.",
    expectedMin: 2,
    mustContain: ["Das Wesentliche", "ist hier zu betonen"]
  },
];

const ESSAY_BRACKET_RE = /\[\s*(?:\.\s*){2,}\.?\s*\]|\[\s*…\s*\]|\(\s*(?:\.\s*){2,}\.?\s*\)|\(\s*…\s*\)|\[[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß. ]{0,28}\]/g;

const stripBoundaryPunct = (s) => s
  .replace(/^[\s,;.:!?„"""'\u2018\u2019\u201A\u201B\u201C\u201D\u201E\u201F«»\-–—]+/, '')
  .replace(/[\s,;.:!?„"""'\u2018\u2019\u201A\u201B\u201C\u201D\u201E\u201F«»\-–—]+$/, '')
  .trim();

function addSnippetMockup(raw) {
  if (!raw) return [];
  let cleaned = raw
    .replace(/^\s*[\*_]+|[\*_]+\s*$/g, '')
    .replace(/^\s*[„"]+|[""]+\s*$/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  if (cleaned.length < 5) return [];

  const fragments = cleaned.split(ESSAY_BRACKET_RE)
    .map(s => stripBoundaryPunct(s.trim()))
    .filter(s => s.length >= 6);
  const cleanedTrim = stripBoundaryPunct(cleaned);
  const toAdd = fragments.length > 1
    ? fragments
    : (cleanedTrim.length >= 5 ? [cleanedTrim] : []);
  return toAdd.filter(f => f.length >= 5);
}

let allOk = true;
cases.forEach(c => {
  const out = addSnippetMockup(c.input);
  const meetsCount = out.length >= c.expectedMin;
  const meetsContain = c.mustContain.every(needle => out.some(f => f.includes(needle)));
  const ok = meetsCount && meetsContain;
  if (!ok) allOk = false;
  console.log((ok ? '✓' : '✗') + ` "${c.name}" — ${out.length} Fragmente (≥${c.expectedMin}? ${meetsCount}, mustContain? ${meetsContain})`);
  out.forEach((f, i) => console.log(`    ${i+1}. [${f.length}ch] "${f.substring(0, 100)}${f.length > 100 ? '…' : ''}"`));
  console.log();
});

console.log(allOk ? '\nAlle Tests grün.' : '\nFehler — siehe oben.');
process.exit(allOk ? 0 : 1);
