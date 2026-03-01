# Tab-Aufrufe und Zitat der Woche über Supabase

## 1. Supabase-Migration ausführen

Öffne den **Supabase SQL Editor** und führe das Script `supabase-analytics-tabs-quotes.sql` aus.
Es fügt die Spalten `quote_views` und `tabs` hinzu und erstellt die RPC-Funktion `increment_analytics_tab_quote`.

## 2. Backend-Änderungen (backend.js)

### 2a) Neue Funktion einfügen (nach Zeile ~24382, nach dem catch-Block von incrementSupabaseAnalytics)

```javascript
// Tab-View oder Quote-View in Supabase speichern (persistent, wie Nutzerstatistik)
async function incrementSupabaseTabQuote(type, tabName = null) {
  if (!supabaseClient) {
    console.warn('[ANALYTICS-SUPABASE] Kein Supabase-Client für tab/quote');
    return false;
  }
  const today = getDateKey();
  try {
    const { error } = await supabaseClient.rpc('increment_analytics_tab_quote', {
      p_date: today,
      p_type: type === 'quote_view' ? 'quote' : 'tab',
      p_tab_name: type === 'tab_view' ? tabName : null
    });
    if (error) {
      console.error('[ANALYTICS-SUPABASE] Tab/Quote RPC Fehler:', error.message);
      return false;
    }
    console.log(`[ANALYTICS-SUPABASE] ✓ ${type}${tabName ? ' ' + tabName : ''} getrackt`);
    return true;
  } catch (error) {
    console.error('[ANALYTICS-SUPABASE] Tab/Quote Fehler:', error.message);
    return false;
  }
}
```

### 2b) Tab/Quote-Block ersetzen (Zeilen ~24599–24620)

**Entfernen:**
```javascript
    // Tab-View / Quote-View: Lokal zählen (kein Supabase-Schema nötig)
    if (type === 'quote_view') {
      const data = await loadAnalyticsData();
      ...
      return res.json({ ok: true, storage: 'local-quote' });
    }
    if (type === 'tab_view' && value) {
      const data = await loadAnalyticsData();
      ...
      return res.json({ ok: true, storage: 'local-tab' });
    }
```

**Ersetzen durch:**
```javascript
    // Tab-View / Quote-View: Supabase (persistent, wie Nutzerstatistik)
    if (type === 'quote_view') {
      const success = await incrementSupabaseTabQuote('quote_view');
      return res.json({ ok: true, storage: success ? 'supabase' : 'fallback' });
    }
    if (type === 'tab_view' && value) {
      const success = await incrementSupabaseTabQuote('tab_view', value);
      return res.json({ ok: true, storage: success ? 'supabase' : 'fallback' });
    }
```

### 2c) loadAnalyticsFromSupabase – dailyStats erweitern (Zeilen ~24447–24454)

**Alt:**
```javascript
        dailyStats[row.date] = {
          views: row.views || 0,
          searches: row.searches || 0,
          lectures: row.lectures || 0,
          unique_users: row.unique_users || 0
        };
```

**Neu:**
```javascript
        dailyStats[row.date] = {
          views: row.views || 0,
          searches: row.searches || 0,
          lectures: row.lectures || 0,
          unique_users: row.unique_users || 0,
          quote_views: row.quote_views || 0,
          tabs: row.tabs || {}
        };
```

## 3. app.js: Zitat-der-Woche-Tracking (falls noch nicht ergänzt)

In `openQuotesPopup()` am Anfang hinzufügen:

```javascript
  if (typeof analyticsTrack === 'function') {
    analyticsTrack('quote_view').catch(function() {});
  } else {
    const api = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? 'http://localhost:3003' : 'https://ga-suche.onrender.com';
    fetch(api + '/api/analytics/track', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'quote_view' }) }).catch(function() {});
  }
```

## 4. Reihenfolge

1. SQL in Supabase ausführen  
2. backend.js anpassen  
3. Optional: app.js anpassen (falls Zitat-Klicks fehlen)  
4. Deploy
