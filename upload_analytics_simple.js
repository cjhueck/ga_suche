// Einfaches Skript zum Hochladen der Analytics-Daten auf den Render-Server
// Führen Sie dies in der Browser-Konsole aus (auf der lokalen Version)

(async function() {
  try {
    console.log('[UPLOAD] Lade lokale Analytics-Daten...');
    
    // Lade vollständige lokale Daten
    const fullDataResponse = await fetch('http://localhost:3003/api/analytics/full');
    if (!fullDataResponse.ok) {
      throw new Error(`Fehler beim Laden lokaler Daten: ${fullDataResponse.status}`);
    }
    
    const uploadData = await fullDataResponse.json();
    
    console.log('[UPLOAD] Daten vorbereitet:', {
      days: Object.keys(uploadData.dailyStats).length,
      totalViews: uploadData.totalViews,
      totalSearches: uploadData.totalSearches
    });
    
    // Upload auf Server
    const uploadResponse = await fetch('https://ga-suche.onrender.com/api/analytics/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: uploadData })
    });
    
    if (!uploadResponse.ok) {
      const errorText = await uploadResponse.text();
      throw new Error(`Upload fehlgeschlagen: ${uploadResponse.status} - ${errorText}`);
    }
    
    const result = await uploadResponse.json();
    console.log('[UPLOAD] ✅ Erfolg!', result);
    alert(`Upload erfolgreich!\n\nTage: ${result.stats?.days || 0}\nViews: ${result.stats?.totalViews || 0}\nSuchen: ${result.stats?.totalSearches || 0}`);
    
  } catch (error) {
    console.error('[UPLOAD] ❌ Fehler:', error);
    alert(`Fehler beim Upload: ${error.message}`);
  }
})();

