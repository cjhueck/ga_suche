# Online-Deployment Plan: Steiner GA-Suche mit Mitgliederbereich

## Aktuelle Situation
- ✅ Backend: Node.js/Express bereits vorhanden
- ✅ Deployment: GitHub → Render.com (bereits konfiguriert)
- ✅ Daten: ~182 MB (75 MB Lectures + 107 MB Bilder)

---

## Empfohlene Architektur

### Backend: **Render.com** (bereits vorhanden)
- Bestehende Express-App bleibt fast unverändert
- Kosten: $7/Monat (Starter) oder $0 (Free Tier mit Sleep Mode)

### Benutzer-Datenbank: **Supabase**
- PostgreSQL für Mitgliederdaten
- Integrierte Authentifizierung (Email/OAuth)
- Row Level Security (Benutzer sehen nur eigene Daten)
- Kosten: $0 (Free Tier: 500 MB DB, 50.000 Users/Monat)

### Total Kosten: **$7/Monat** (oder $0 mit Einschränkungen)

---

## Funktionen im Mitgliederbereich

### 1. Leselisten-Tracking
```
Tabelle: reading_progress
- Welche Vorträge gelesen
- Lesefortschritt (%)
- Zuletzt gelesen Datum
- Notizen zum Vortrag
```

### 2. Bookmarks
```
Tabelle: bookmarks
- Gespeicherte Absätze
- Eigene Titel/Tags
- Notizen
- Quellenangaben automatisch
```

### 3. Gespeicherte Texte
```
Tabelle: saved_texts
- Kopierte Textabschnitte
- Quellenangaben (GA/Vortrag/Absatz)
- Tags/Kategorien
- Eigene Kommentare
```

### 4. Notizen/Schreibfunktion
```
Tabelle: user_notes
- Freie Notizen
- Verknüpfung zu Vorträgen
- Rich-Text Editor
- Versionierung (created/updated)
```

---

## Datenbank-Schema (Supabase)

```sql
-- Lesefortschritt
CREATE TABLE reading_progress (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  lecture_id TEXT NOT NULL,
  progress INTEGER DEFAULT 0,
  completed BOOLEAN DEFAULT false,
  read_at TIMESTAMP DEFAULT NOW(),
  notes TEXT,
  UNIQUE(user_id, lecture_id)
);

-- Bookmarks
CREATE TABLE bookmarks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  lecture_id TEXT NOT NULL,
  paragraph_index TEXT NOT NULL,
  text TEXT NOT NULL,
  title TEXT,
  tags TEXT[],
  note TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Gespeicherte Texte
CREATE TABLE saved_texts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  lecture_id TEXT NOT NULL,
  paragraph_index TEXT,
  text TEXT NOT NULL,
  source_reference TEXT NOT NULL,
  tags TEXT[],
  comment TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Notizen
CREATE TABLE user_notes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users NOT NULL,
  lecture_id TEXT,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Row Level Security aktivieren
ALTER TABLE reading_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_texts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_notes ENABLE ROW LEVEL SECURITY;

-- Policies: User sieht nur eigene Daten
CREATE POLICY "Users can view own reading_progress" ON reading_progress
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own reading_progress" ON reading_progress
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own reading_progress" ON reading_progress
  FOR UPDATE USING (auth.uid() = user_id);

-- (Analog für andere Tabellen)
```

---

## Code-Änderungen

### Backend (backend.js)

#### Neue Dependencies installieren:
```bash
npm install @supabase/supabase-js dotenv
```

#### Am Anfang von backend.js:
```javascript
require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
);

// Auth Middleware
async function requireAuth(req, res, next) {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');
    if (!token) return res.status(401).json({ error: 'Login erforderlich' });
    
    const { data: { user }, error } = await supabase.auth.getUser(token);
    if (error || !user) return res.status(401).json({ error: 'Unauthorized' });
    
    req.user = user;
    next();
  } catch (err) {
    res.status(401).json({ error: 'Auth fehlgeschlagen' });
  }
}
```

#### Neue API-Endpoints:
```javascript
// Lesefortschritt speichern
app.post('/api/user/reading-progress', requireAuth, async (req, res) => {
  const { lectureId, progress, completed, notes } = req.body;
  
  const { data, error } = await supabase
    .from('reading_progress')
    .upsert({
      user_id: req.user.id,
      lecture_id: lectureId,
      progress: progress || 0,
      completed: completed || false,
      notes: notes || null,
      read_at: new Date().toISOString()
    }, { onConflict: 'user_id,lecture_id' });
  
  if (error) return res.status(400).json({ error: error.message });
  res.json({ success: true, data });
});

// Lesefortschritt abrufen
app.get('/api/user/reading-progress', requireAuth, async (req, res) => {
  const { data, error } = await supabase
    .from('reading_progress')
    .select('*')
    .eq('user_id', req.user.id);
  
  if (error) return res.status(400).json({ error: error.message });
  res.json(data);
});

// Bookmark speichern
app.post('/api/user/bookmark', requireAuth, async (req, res) => {
  const { lectureId, paragraphIndex, text, title, tags, note } = req.body;
  
  const { data, error } = await supabase
    .from('bookmarks')
    .insert({
      user_id: req.user.id,
      lecture_id: lectureId,
      paragraph_index: paragraphIndex,
      text: text,
      title: title,
      tags: tags || [],
      note: note
    });
  
  if (error) return res.status(400).json({ error: error.message });
  res.json({ success: true, data });
});

// Alle Bookmarks abrufen
app.get('/api/user/bookmarks', requireAuth, async (req, res) => {
  const { data, error } = await supabase
    .from('bookmarks')
    .select('*')
    .eq('user_id', req.user.id)
    .order('created_at', { ascending: false });
  
  if (error) return res.status(400).json({ error: error.message });
  res.json(data);
});

// Text speichern
app.post('/api/user/save-text', requireAuth, async (req, res) => {
  const { lectureId, paragraphIndex, text, sourceReference, tags, comment } = req.body;
  
  const { data, error } = await supabase
    .from('saved_texts')
    .insert({
      user_id: req.user.id,
      lecture_id: lectureId,
      paragraph_index: paragraphIndex,
      text: text,
      source_reference: sourceReference,
      tags: tags || [],
      comment: comment
    });
  
  if (error) return res.status(400).json({ error: error.message });
  res.json({ success: true, data });
});

// Notiz speichern
app.post('/api/user/note', requireAuth, async (req, res) => {
  const { lectureId, title, content, noteId } = req.body;
  
  if (noteId) {
    // Update bestehende Notiz
    const { data, error } = await supabase
      .from('user_notes')
      .update({ 
        title, 
        content,
        updated_at: new Date().toISOString()
      })
      .eq('id', noteId)
      .eq('user_id', req.user.id); // Sicherheit: nur eigene Notizen
    
    if (error) return res.status(400).json({ error: error.message });
    res.json({ success: true, data });
  } else {
    // Neue Notiz
    const { data, error } = await supabase
      .from('user_notes')
      .insert({
        user_id: req.user.id,
        lecture_id: lectureId,
        title: title,
        content: content
      });
    
    if (error) return res.status(400).json({ error: error.message });
    res.json({ success: true, data });
  }
});

// Alle Notizen abrufen
app.get('/api/user/notes', requireAuth, async (req, res) => {
  const { data, error } = await supabase
    .from('user_notes')
    .select('*')
    .eq('user_id', req.user.id)
    .order('updated_at', { ascending: false });
  
  if (error) return res.status(400).json({ error: error.message });
  res.json(data);
});
```

---

## Frontend-Änderungen

### 1. Login-Seite (login.html)
```html
<div id="login-container">
  <h2>Mitgliederbereich</h2>
  <form id="login-form">
    <input type="email" placeholder="Email" required>
    <input type="password" placeholder="Passwort" required>
    <button type="submit">Anmelden</button>
  </form>
  <p>Noch kein Konto? <a href="#" onclick="showRegister()">Registrieren</a></p>
</div>

<script>
// Login
document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = e.target[0].value;
  const password = e.target[1].value;
  
  const { data, error } = await supabase.auth.signInWithPassword({
    email, password
  });
  
  if (error) {
    alert('Login fehlgeschlagen: ' + error.message);
    return;
  }
  
  localStorage.setItem('supabase_token', data.session.access_token);
  window.location.href = '/';
});
</script>
```

### 2. Mitglieder-Funktionen in index.html

**Bookmark-Button bei jedem Absatz:**
```javascript
// Bei Alt+Click auf Absatz
paragraph.addEventListener('click', async (e) => {
  if (e.altKey) {
    const text = paragraph.textContent;
    const lectureId = currentLectureId;
    const paragraphIndex = paragraph.dataset.index;
    
    // Öffne Dialog
    const note = prompt('Notiz zu diesem Bookmark (optional):');
    
    // Speichere Bookmark
    await fetch('/api/user/bookmark', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('supabase_token')}`
      },
      body: JSON.stringify({
        lectureId,
        paragraphIndex,
        text,
        note
      })
    });
    
    alert('✓ Bookmark gespeichert!');
  }
});
```

**Lesefortschritt automatisch tracken:**
```javascript
// Beim Scrollen im Vortrag
let lastScrollPosition = 0;
window.addEventListener('scroll', debounce(() => {
  const progress = (window.scrollY / document.body.scrollHeight) * 100;
  
  if (progress > lastScrollPosition + 10) {
    // Alle 10% Fortschritt speichern
    saveReadingProgress(currentLectureId, Math.floor(progress));
    lastScrollPosition = progress;
  }
}, 2000));
```

---

## Render.com Konfiguration

### Environment Variables hinzufügen:
```
Dashboard → Environment
→ Add Environment Variable

SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NODE_ENV=production
```

### Deploy-Einstellungen:
```yaml
# render.yaml (optional)
services:
  - type: web
    name: steiner-ga-suche
    env: node
    buildCommand: npm install
    startCommand: node backend.js
    envVars:
      - key: NODE_ENV
        value: production
```

---

## Zugriffs-Struktur

### Öffentlicher Bereich (OHNE Login):
- Suche (Stichwort, Semantisch, Thematisch)
- Vorträge lesen
- Timeline
- GA-Übersichten

### Mitglieder-Bereich (MIT Login):
- **Leselisten:** "Was habe ich gelesen?"
- **Bookmarks:** Wichtige Stellen markieren
- **Texte speichern:** Mit Quellenangaben
- **Notizen:** Eigene Gedanken zu Vorträgen
- **Export:** Eigene Sammlung als PDF

---

## Implementierungs-Reihenfolge

### Phase 1: Supabase Setup (1 Stunde)
1. Supabase Projekt erstellen
2. SQL-Schema ausführen
3. API-Keys kopieren
4. In Render Environment Variables eintragen

### Phase 2: Backend erweitern (2-3 Stunden)
1. `npm install @supabase/supabase-js`
2. Auth-Middleware hinzufügen
3. Neue API-Endpoints implementieren
4. Testen lokal

### Phase 3: Frontend erweitern (4-6 Stunden)
1. Login/Register Seite
2. Mitglieder-Dashboard
3. Bookmark-Icons bei Absätzen
4. Lesefortschritt-Anzeige
5. Notizen-Editor

### Phase 4: Deployment (30 Minuten)
1. Git commit & push
2. Render deployed automatisch
3. Testen online

### Phase 5: Optional (1-2 Stunden)
1. Email-Verifikation
2. Passwort-Reset
3. Profil-Verwaltung
4. Export-Funktion (PDF/JSON)

---

## Kosten-Übersicht

### Development (Kostenlos):
- Supabase Free Tier: $0
- Render Free Tier: $0 (mit Sleep Mode)

### Production (Klein):
- Render Starter: $7/Monat
- Supabase Free: $0/Monat
- Domain: ~$1/Monat
- **Total: ~$8/Monat**

### Production (Mittel, 5000+ Users):
- Render Standard: $25/Monat
- Supabase Pro: $25/Monat
- **Total: ~$50/Monat**

---

## Sicherheit & DSGVO

### Supabase (EU-Server):
- ✅ Server in Frankfurt verfügbar
- ✅ DSGVO-konform
- ✅ Row Level Security
- ✅ Verschlüsselte Verbindungen

### Benötigt:
- Datenschutzerklärung
- Impressum
- Cookie-Consent (falls Analytics)
- AGB für Mitglieder

---

## Alternative: Nur Mitgliederbereich

Falls die **gesamte App** nur für Mitglieder sein soll:

**Vorteile:**
- Einfacher zu implementieren (nur eine Auth-Check)
- Kein öffentlicher Traffic
- Bessere Kontrolle

**Code:**
```javascript
// Middleware für ALLE Routes
app.use((req, res, next) => {
  // Ausnahme: Login-Seite
  if (req.path === '/login' || req.path.startsWith('/auth')) {
    return next();
  }
  
  // Sonst: Auth prüfen
  requireAuth(req, res, next);
});
```

---

## Nächste Schritte

1. **Entscheidung:** Öffentlich + Mitglieder ODER nur Mitglieder?
2. **Supabase Setup:** SQL-Schema ausführen
3. **Backend:** Dependencies installieren & Auth-Code hinzufügen
4. **Frontend:** Login-UI & Mitglieder-Funktionen
5. **Deploy:** Git push → Render deployed automatisch

---

## Quick Start (wenn bereit):

```bash
# 1. Dependencies
npm install @supabase/supabase-js dotenv

# 2. .env Datei erstellen (lokal)
echo "SUPABASE_URL=https://xxxxx.supabase.co" > .env
echo "SUPABASE_ANON_KEY=eyJhbG..." >> .env

# 3. Render Environment Variables setzen (online)
# → Render Dashboard

# 4. Code anpassen
# → backend.js erweitern
# → index.html Login hinzufügen

# 5. Deploy
git add .
git commit -m "Add member area with Supabase"
git push
# → Render deployed automatisch
```

---

**Vorbereitet von:** AI Assistant  
**Datum:** November 2025  
**Für:** Steiner GA-Suche Online-Deployment  
**Stack:** Render.com + Supabase + Express + Vanilla JS

