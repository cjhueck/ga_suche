// Einmaliges Setup für den Vectorize-Index der GA-Suche.
// - Legt den Index an (768 Dim, cosine), idempotent: existierender Index → Skip.
// - Aktiviert Metadata-Filtering für gaBand und typ.
// - Smoke-Test: 3 Probe-Vektoren upserten, Query, Aufräumen.
//
// Ausführen:
//   node _setup_vectorize.js
//
// Voraussetzung in .env:
//   CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, VECTORIZE_INDEX_NAME

require('dotenv').config();
const v = require('./vectorize-client');

(async () => {
  if (!v.isConfigured()) {
    console.error('FEHLER: Vectorize nicht konfiguriert. Prüfe CLOUDFLARE_ACCOUNT_ID und CLOUDFLARE_API_TOKEN in .env.');
    process.exit(1);
  }
  const indexName = v.getIndexName();
  console.log(`[SETUP] Index-Name: ${indexName}`);

  // 1. Index anlegen (oder existierenden erkennen)
  console.log('\n[1/4] Lege Index an (768 Dim, cosine)…');
  try {
    const created = await v.createIndex({
      dimensions: 768,
      metric: 'cosine',
      description: 'GA-Suche: Absatz-Embeddings aus Steiner-Werk (Gemini embedding-001, 768d)'
    });
    console.log('  ✓ Index angelegt:', created?.result?.name || indexName);
  } catch (e) {
    if (/already exists|duplicate_name|\b3002\b/i.test(e.message) || e.status === 409) {
      console.log('  ✓ Index existiert bereits (idempotent, kein Fehler)');
    } else {
      console.error('  ✗ Fehler beim Anlegen:', e.message);
      throw e;
    }
  }

  // 2. Index-Info abrufen
  console.log('\n[2/4] Index-Info abrufen…');
  try {
    const info = await v.getIndexInfo();
    console.log('  ✓ Info:', JSON.stringify(info?.result || info, null, 2).substring(0, 500));
  } catch (e) {
    console.warn('  (Info nicht abrufbar, harmlos):', e.message);
  }

  // 3. Metadata-Indexe für gaBand und typ aktivieren
  console.log('\n[3/4] Metadata-Indexe aktivieren (gaBand, typ)…');
  for (const prop of ['gaBand', 'typ']) {
    try {
      const r = await v.createMetadataIndex(prop, 'string');
      console.log(`  ✓ Metadata-Index gestartet für "${prop}" (mutationId: ${r?.result?.mutationId || '–'})`);
    } catch (e) {
      if (/already/i.test(e.message)) {
        console.log(`  ✓ Metadata-Index für "${prop}" existiert bereits`);
      } else {
        console.warn(`  ! Konnte Metadata-Index "${prop}" nicht anlegen: ${e.message}`);
      }
    }
  }

  // 4. Smoke-Test: 3 Test-Vektoren mit Dummy-Werten upserten, einen Query absetzen,
  //    die Test-Vektoren wieder löschen. Die echten GA001-Embeddings kommen erst
  //    in einem separaten Migrationsschritt rein.
  console.log('\n[4/4] Smoke-Test: 3 Dummy-Vektoren upsert/query/delete…');
  function rand768() {
    const a = new Array(768);
    for (let i = 0; i < 768; i++) a[i] = (Math.random() - 0.5) * 0.1;
    return a;
  }
  const testIds = ['__smoke_test_a', '__smoke_test_b', '__smoke_test_c'];
  const testVectors = [
    { id: testIds[0], values: rand768(), metadata: { gaBand: 'TEST', typ: 'lecture' } },
    { id: testIds[1], values: rand768(), metadata: { gaBand: 'TEST', typ: 'book' } },
    { id: testIds[2], values: rand768(), metadata: { gaBand: 'TEST', typ: 'lecture' } }
  ];
  // Den ersten Vektor wollen wir gleich als Query verwenden — er sollte mit Score 1.0 (oder
  // sehr nahe daran) als Top-1 wiederkommen. Wir kopieren seine values explizit.
  const queryVec = [...testVectors[0].values];

  try {
    const t0 = Date.now();
    const upRes = await v.upsertVectors(testVectors);
    console.log(`  ✓ Upsert: ${upRes.upserted} Vektoren in ${Date.now() - t0} ms`);
    console.log('  ⏳ Warte 8 s, bis Vectorize indexiert hat…');
    await new Promise(r => setTimeout(r, 8000));

    const t1 = Date.now();
    const matches = await v.queryNearest(queryVec, { topK: 3, filter: { gaBand: 'TEST' }, returnMetadata: 'indexed' });
    const dt = Date.now() - t1;
    console.log(`  ✓ Query (topK=3, filter gaBand=TEST): ${matches.count} Treffer in ${dt} ms`);
    (matches.matches || []).forEach((m, i) => {
      console.log(`    ${i + 1}. id=${m.id}  score=${(m.score || 0).toFixed(4)}  meta=${JSON.stringify(m.metadata || {})}`);
    });
    if (!matches.matches || matches.matches.length === 0) {
      console.warn('  ! Kein Treffer — ggf. Indexierung noch nicht durch. Versuche es erneut in 30 s.');
    } else if (matches.matches[0].id !== testIds[0]) {
      console.warn(`  ! Erwarteter Top-Hit ${testIds[0]}, bekam ${matches.matches[0].id} (Indexierung noch nicht final)`);
    }
  } finally {
    console.log('  Aufräumen: lösche Smoke-Test-Vektoren…');
    try {
      const del = await v.deleteByIds(testIds);
      console.log(`  ✓ Delete: mutationId=${del?.result?.mutationId || '–'}`);
    } catch (e) {
      console.warn(`  ! Aufräumen fehlgeschlagen (harmlos, Vektoren laufen mit gaBand=TEST):`, e.message);
    }
  }

  console.log('\n=== SETUP FERTIG ===');
  console.log(`Index "${indexName}" ist einsatzbereit. Nächster Schritt: GA001-Embeddings hochspielen.`);
})().catch(e => {
  console.error('\n[SETUP] FATAL:', e.message);
  if (e.body) console.error('  Body:', JSON.stringify(e.body, null, 2).substring(0, 1000));
  process.exit(1);
});
