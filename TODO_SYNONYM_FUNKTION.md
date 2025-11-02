# TODO: Synonym-Funktion im Keyword-Manager

## Anforderung
Im keyword-manager.html eine neue Funktion "Synonym hinzufügen" erstellen.

## Beispiel
- Keyword: "Budhi"
- Synonym: "Buddhi"
→ Beide werden gleich behandelt in der Suche

## Implementierung

### 1. UI in keyword-manager.html
```html
<div class="synonym-section">
  <h4>Synonym hinzufügen</h4>
  <input id="baseKeyword" placeholder="Haupt-Keyword (z.B. Buddhi)">
  <input id="synonymKeyword" placeholder="Synonym (z.B. Budhi)">
  <button onclick="addSynonym()">Synonym hinzufügen</button>
</div>
```

### 2. Backend-Endpoint
```javascript
app.post('/api/synonyms/add', async (req, res) => {
  const { baseKeyword, synonym } = req.body;
  
  // Lade synonyms.json
  const synonyms = JSON.parse(fs.readFileSync('synonyms.json'));
  
  // Füge hinzu oder aktualisiere
  if (!synonyms[baseKeyword.toLowerCase()]) {
    synonyms[baseKeyword.toLowerCase()] = [baseKeyword.toLowerCase()];
  }
  
  synonyms[baseKeyword.toLowerCase()].push(synonym.toLowerCase());
  
  // Speichere
  fs.writeFileSync('synonyms.json', JSON.stringify(synonyms, null, 2));
  
  res.json({ success: true });
});
```

### 3. Frontend-Funktion
```javascript
async function addSynonym() {
  const base = document.getElementById('baseKeyword').value;
  const synonym = document.getElementById('synonymKeyword').value;
  
  if (!base || !synonym) {
    alert('Bitte beide Felder ausfüllen');
    return;
  }
  
  const response = await fetch('/api/synonyms/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ baseKeyword: base, synonym: synonym })
  });
  
  if (response.ok) {
    alert('Synonym hinzugefügt!');
    // Felder leeren
  }
}
```

## Bestehende Struktur

**synonyms.json Format:**
```json
{
  "kant": ["kant", "kants", "kantisch", "immanuel kant"],
  "bewusstsein": ["bewusstsein", "bewußtsein", "seelenleben"],
  "budhi": ["budhi", "buddhi"]  ← NEU
}
```

**Backend unterstützt bereits:**
- Laden von synonyms.json
- Expansion bei Suche
- ~90 Stellen im Code

## Status
- [x] Backend-Synonym-Support vorhanden
- [x] synonyms.json existiert
- [ ] UI im keyword-manager.html fehlt
- [ ] API-Endpoint zum Hinzufügen fehlt

**Priorität:** Mittel  
**Aufwand:** 30-60 Minuten

