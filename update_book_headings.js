#!/usr/bin/env node
/**
 * Aktualisiert die Überschriften-Indizes für Bücher GA001-GA013
 * Ruft für jedes Buch den /api/book/:gaNumber Endpoint auf,
 * der automatisch die Überschriften mit den richtigen Paragraph-Indizes aktualisiert
 */

const http = require('http');

const API_BASE = process.env.API_BASE || 'http://localhost:3000';
const BOOKS_TO_UPDATE = [
  'GA001', 'GA002', 'GA003', 'GA004', 'GA005', 'GA006', 'GA007',
  'GA008', 'GA009', 'GA010', 'GA011', 'GA012', 'GA013'
];

async function updateBookHeadings(gaNumber) {
  return new Promise((resolve, reject) => {
    const url = `${API_BASE}/api/book/${gaNumber}`;
    console.log(`[UPDATE] Lade ${gaNumber}...`);
    
    http.get(url, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const book = JSON.parse(data);
            console.log(`[UPDATE] ✓ ${gaNumber}: ${book.headings?.length || 0} Überschriften aktualisiert`);
            resolve({ success: true, gaNumber, headingsCount: book.headings?.length || 0 });
          } catch (e) {
            console.error(`[UPDATE] ✗ ${gaNumber}: JSON Parse Fehler:`, e.message);
            reject(e);
          }
        } else {
          console.error(`[UPDATE] ✗ ${gaNumber}: HTTP ${res.statusCode}`);
          reject(new Error(`HTTP ${res.statusCode}`));
        }
      });
    }).on('error', (err) => {
      console.error(`[UPDATE] ✗ ${gaNumber}: Fehler:`, err.message);
      reject(err);
    });
  });
}

async function updateAllBooks() {
  console.log('========================================');
  console.log('Aktualisiere Überschriften für Bücher GA001-GA013');
  console.log(`API Base: ${API_BASE}`);
  console.log('========================================\n');
  
  const results = [];
  
  for (const gaNumber of BOOKS_TO_UPDATE) {
    try {
      // Warte 500ms zwischen den Requests, um den Server nicht zu überlasten
      if (results.length > 0) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      const result = await updateBookHeadings(gaNumber);
      results.push(result);
    } catch (error) {
      results.push({ success: false, gaNumber, error: error.message });
    }
  }
  
  console.log('\n========================================');
  console.log('Zusammenfassung:');
  console.log('========================================');
  
  const successful = results.filter(r => r.success);
  const failed = results.filter(r => !r.success);
  
  console.log(`✓ Erfolgreich: ${successful.length}`);
  successful.forEach(r => {
    console.log(`  - ${r.gaNumber}: ${r.headingsCount} Überschriften`);
  });
  
  if (failed.length > 0) {
    console.log(`\n✗ Fehlgeschlagen: ${failed.length}`);
    failed.forEach(r => {
      console.log(`  - ${r.gaNumber}: ${r.error}`);
    });
  }
  
  console.log('\n========================================');
  console.log('Fertig!');
  console.log('========================================');
}

// Führe Update aus
updateAllBooks().catch(err => {
  console.error('Fataler Fehler:', err);
  process.exit(1);
});


