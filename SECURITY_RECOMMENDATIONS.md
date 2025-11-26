# Sicherheits- und Wartbarkeits-Empfehlungen

## 1. Dateistruktur: Aufteilen vs. Beibehalten

### Aktuelle Situation
- **app.html**: ~1 MB, ~27.000 Zeilen, ~3.278 Funktionen/Variablen
- Monolithische Single-Page-Application
- Alle Funktionen in einer Datei

### Empfehlung: **GRADUELLE MODULARISIERUNG**

#### ✅ **NICHT komplett aufteilen** (warum):
1. **Aktuell funktioniert es** - "Never touch a running system"
2. **Komplexität der Migration** - Risiko von Breaking Changes
3. **Build-Prozess nötig** - Aktuell keine Build-Pipeline vorhanden
4. **Performance** - Eine Datei = weniger HTTP-Requests

#### ✅ **ABER: Strategische Modularisierung** (empfohlen):

### Phase 1: Externe Module auslagern (Niedriges Risiko)
```
app.html (Hauptdatei)
├── js/
│   ├── modules/
│   │   ├── search.js          (Suchfunktionen)
│   │   ├── display.js         (Anzeige-Funktionen)
│   │   ├── images.js          (Bild-Verarbeitung)
│   │   ├── highlighting.js    (Highlighting-Logik)
│   │   └── utils.js           (Hilfsfunktionen)
│   └── config.js              (Konfiguration)
└── css/
    └── components.css         (Komponenten-Styles)
```

**Vorteile:**
- Bessere Wartbarkeit
- Einfachere Code-Reviews
- Klarere Verantwortlichkeiten
- Keine Breaking Changes (schrittweise Migration)

**Nachteile:**
- Mehr HTTP-Requests (kann durch HTTP/2 minimiert werden)
- Module-Loading-Logik nötig

### Phase 2: Build-Prozess einführen (Mittelfristig)
- **Bundler**: Vite, Webpack oder Rollup
- **Vorteile**: 
  - Code-Splitting
  - Tree-Shaking
  - Minification
  - Source Maps für Debugging

---

## 2. Sicherheitsmaßnahmen

### 🔴 **KRITISCH - Sofort umsetzen:**

#### A. Content Security Policy (CSP)
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; 
               style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; 
               font-src 'self' https://fonts.gstatic.com; 
               img-src 'self' data: blob:; 
               connect-src 'self' http://localhost:3003;">
```

**Problem aktuell:** `'unsafe-inline'` erlaubt XSS-Angriffe
**Lösung:** Nonces oder Hashes für inline scripts/styles verwenden

#### B. XSS-Schutz bei innerHTML
```javascript
// ❌ GEFÄHRLICH:
viewer.innerHTML = userInput;

// ✅ SICHER:
function sanitizeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Oder: DOMPurify verwenden
import DOMPurify from 'dompurify';
viewer.innerHTML = DOMPurify.sanitize(userInput);
```

**Aktuell gefunden:** 9 Stellen mit `innerHTML` - alle prüfen!

#### C. Input-Validierung im Backend
```javascript
// backend.js - Input-Validierung hinzufügen
function validateLectureId(lectureId) {
  // Erlaubt nur: GA001-GA999, optional /1-999
  return /^GA\d{3}(\/\d{1,3})?$/.test(lectureId);
}

app.get('/api/steiner-images/:lectureId', async (req, res) => {
  const lectureId = req.params.lectureId;
  if (!validateLectureId(lectureId)) {
    return res.status(400).json({ error: 'Invalid lecture ID format' });
  }
  // ...
});
```

#### D. Rate Limiting
```javascript
// backend.js
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 Minuten
  max: 100 // max 100 Requests pro IP
});

app.use('/api/', limiter);
```

### 🟡 **WICHTIG - Mittelfristig:**

#### E. HTTPS erzwingen (für Production)
```javascript
// backend.js
if (process.env.NODE_ENV === 'production') {
  app.use((req, res, next) => {
    if (req.header('x-forwarded-proto') !== 'https') {
      res.redirect(`https://${req.header('host')}${req.url}`);
    } else {
      next();
    }
  });
}
```

#### F. Helmet.js für Security Headers
```javascript
const helmet = require('helmet');
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'", "https://unpkg.com"],
      // ...
    }
  }
}));
```

#### G. SQL Injection Schutz (falls Datenbank hinzugefügt wird)
- Prepared Statements verwenden
- ORM verwenden (z.B. Prisma, Sequelize)

#### H. Dependency Scanning
```bash
npm audit
# oder
npm install -g snyk
snyk test
```

### 🟢 **NICHT KRITISCH - Langfristig:**

#### I. Code-Obfuscation (für Production)
- Minification und Obfuscation für Client-Code
- Backend-Code sollte klar bleiben für Debugging

#### J. Logging & Monitoring
```javascript
// Strukturiertes Logging
const winston = require('winston');
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});
```

---

## 3. Code-Qualität & Wartbarkeit

### A. TypeScript Migration (Langfristig)
- Bessere Typsicherheit
- Bessere IDE-Unterstützung
- Weniger Runtime-Fehler

### B. Unit Tests
```javascript
// Beispiel mit Jest
describe('replaceImageSrcWithBase64', () => {
  it('should replace image src with base64', async () => {
    const html = '<img src="assets/test.png">';
    const result = await replaceImageSrcWithBase64(html, 'GA001/1');
    expect(result).toContain('data:image');
  });
});
```

### C. Code-Dokumentation
```javascript
/**
 * Ersetzt img src-Attribute durch Base64-Daten
 * @param {string} htmlContent - HTML-Content mit img-Tags
 * @param {string} lectureId - ID des Vortrags (z.B. "GA001/1")
 * @returns {Promise<string>} HTML mit Base64-Bildern
 */
async function replaceImageSrcWithBase64(htmlContent, lectureId) {
  // ...
}
```

### D. ESLint & Prettier
```json
// .eslintrc.json
{
  "extends": ["eslint:recommended"],
  "rules": {
    "no-eval": "error",
    "no-implied-eval": "error",
    "no-new-func": "error"
  }
}
```

---

## 4. Empfohlene Prioritäten

### Sofort (Diese Woche):
1. ✅ CSP Header hinzufügen
2. ✅ Input-Validierung im Backend
3. ✅ Rate Limiting implementieren
4. ✅ `innerHTML` Stellen prüfen und sanitizen

### Kurzfristig (Dieser Monat):
1. ✅ Helmet.js integrieren
2. ✅ Externe Module auslagern (search.js, display.js)
3. ✅ DOMPurify für HTML-Sanitization

### Mittelfristig (Nächste 3 Monate):
1. ✅ Build-Prozess einführen
2. ✅ Unit Tests für kritische Funktionen
3. ✅ TypeScript Migration planen

### Langfristig (6+ Monate):
1. ✅ Vollständige Modularisierung
2. ✅ Component-basierte Architektur
3. ✅ Framework-Migration (React/Vue) erwägen

---

## 5. Fazit

**Für diese Anwendung empfehle ich:**

1. **NICHT komplett aufteilen** - Risiko zu hoch, Nutzen zu gering
2. **GRADUELLE Modularisierung** - Schrittweise externe Module auslagern
3. **Sicherheit zuerst** - CSP, Input-Validierung, Rate Limiting
4. **Code-Qualität** - Tests, Dokumentation, Linting

Die aktuelle monolithische Struktur ist für eine Single-Page-Application dieser Größe **akzeptabel**, solange Sicherheitsmaßnahmen implementiert werden.

