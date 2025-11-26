# Supabase Dashboard Setup-Anleitung

## 1. Rate Limiting

### ⚠️ WICHTIG: Rate Limiting ist NICHT im Dashboard verfügbar!

Supabase bietet **kein direktes Rate Limiting** für die Data API im Dashboard. Es gibt jedoch mehrere Schutzebenen:

### A. ✅ Bereits implementiert: Backend Rate Limiting

**Status:** ✅ **BEREITS AKTIV** in `backend.js`

Dein Backend hat bereits Rate Limiting implementiert:
- 500 Requests pro IP pro 15 Minuten
- Verhindert DDoS-Angriffe auf dein Backend
- Schützt deine Supabase-Kosten

### B. Supabase Standard-Limits (automatisch aktiv)

Supabase hat **automatische Limits** basierend auf deinem Plan:

**Free Plan:**
- API Requests: ~50.000/Monat
- Database Size: 500 MB
- Bandwidth: 5 GB/Monat

**Pro Plan:**
- API Requests: ~2 Millionen/Monat
- Database Size: 8 GB
- Bandwidth: 250 GB/Monat

Diese Limits werden automatisch durchgesetzt - keine Konfiguration nötig!

### C. Auth Rate Limits (optional, über Management API)

Für **Auth-Endpoints** (Login, Signup, etc.) kannst du Rate Limits über die Management API setzen:

1. **Access Token erstellen:**
   - Gehe zu: https://supabase.com/dashboard/account/tokens
   - Erstelle einen Personal Access Token

2. **Rate Limits setzen:**
   ```bash
   curl -X PATCH "https://api.supabase.com/v1/projects/qygirjbfvzyhpgwhllzs/config/auth" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "rate_limit_email_sent": 10,
       "rate_limit_verify": 10
     }'
   ```

**Empfehlung:** Nicht nötig, da dein Backend bereits Rate Limiting hat!

---

## 2. Backups konfigurieren

### Schritt-für-Schritt:

1. **Settings → Database:**
   - Scrolle zu "Backups"

2. **Backup-Strategie:**
   ```
   ✅ Point-in-Time Recovery (PITR) aktivieren
   ✅ Retention: 7 Tage (für kostenlosen Plan)
   ✅ Backup Schedule: Täglich um 2:00 Uhr
   ```

3. **Für Production (bezahlter Plan):**
   ```
   Retention: 30 Tage
   Backup Schedule: Stündlich
   ```

4. **Test-Backup erstellen:**
   - Klicke auf "Create Backup Now"
   - Warte auf Bestätigung

**Warum wichtig:**
- Datenverlust vermeiden
- Bei Fehlern wiederherstellbar
- Compliance-Anforderungen

---

## 3. Email-Bestätigung prüfen

### Im Dashboard prüfen:

1. **Authentication → Settings:**
   - Scrolle zu "Email Auth"

2. **Prüfe folgende Einstellungen:**
   ```
   ✅ Enable email confirmations: AN
   ✅ Secure email change: AN
   ✅ Double confirm email changes: AN (empfohlen)
   ```

3. **Email Templates prüfen:**
   - Authentication → Email Templates
   - "Confirm signup" Template sollte aktiviert sein

### Im Code prüfen:

**members-auth.js** sollte folgendes haben:
```javascript
const { data, error } = await supabase.auth.signUp({
  email: email,
  password: password,
  options: {
    emailRedirectTo: `${window.location.origin}/auth/callback`,
    data: {
      display_name: displayName
    }
  }
});
```

**Wenn `emailRedirectTo` vorhanden ist:** ✅ Email-Bestätigung ist aktiviert

---

## 4. Weitere wichtige Sicherheitseinstellungen

### A. Password Policy

**Settings → Authentication → Password:**
```
✅ Minimum password length: 8 Zeichen
✅ Require uppercase: Optional (empfohlen)
✅ Require lowercase: Optional (empfohlen)
✅ Require numbers: Optional (empfohlen)
```

### B. Session Management

**Settings → Authentication → Sessions:**
```
✅ JWT expiry: 3600 Sekunden (1 Stunde)
✅ Refresh token rotation: Aktiviert
✅ Refresh token expiry: 30 Tage
```

### C. OAuth Providers (falls verwendet)

**Settings → Authentication → Providers:**
- Nur aktivieren, was benötigt wird
- Google/GitHub/etc. nur wenn nötig

### D. Network Restrictions (für Production)

**Settings → Database → Network Restrictions:**
```
✅ IP Whitelist: Nur bekannte IPs (optional)
✅ SSL Mode: Require (empfohlen)
```

---

## 5. Monitoring & Alerts

### A. Logs überwachen

**Logs → API Logs:**
- Prüfe regelmäßig auf verdächtige Anfragen
- Suche nach:
  - Viele fehlgeschlagene Login-Versuche
  - Ungewöhnliche IP-Adressen
  - Hohe Request-Raten

### B. Database Monitoring

**Database → Reports:**
- Prüfe Database-Größe
- Prüfe Query-Performance
- Prüfe Connection-Pool

### C. Alerts einrichten (für bezahlten Plan)

**Settings → Alerts:**
```
✅ Database size > 80%: Email-Benachrichtigung
✅ High error rate: Email-Benachrichtigung
✅ Backup failed: Email-Benachrichtigung
```

---

## 6. Checkliste

### Sofort prüfen:
- [x] Rate Limiting aktiviert? ✅ (bereits im Backend implementiert)
- [ ] Backups konfiguriert?
- [x] Email-Bestätigung aktiviert? ✅ (bereits im Code konfiguriert)
- [ ] Password Policy konfiguriert?

### Diese Woche:
- [ ] Logs überprüft?
- [ ] Session-Einstellungen optimiert?
- [ ] Test-Backup erstellt?

### Dieser Monat:
- [ ] Monitoring eingerichtet?
- [ ] Alerts konfiguriert?
- [ ] Security Audit durchgeführt?

---

## 7. Troubleshooting

### Problem: Email-Bestätigung funktioniert nicht

**Lösung:**
1. Prüfe SMTP-Einstellungen (Settings → Auth → SMTP)
2. Prüfe Email-Templates
3. Prüfe Spam-Ordner
4. Teste mit verschiedenen Email-Providern

### Problem: Rate Limiting blockiert legitime Nutzer

**Lösung:**
1. Erhöhe Rate Limits im Backend (`backend.js` Zeile 20: `RATE_LIMIT_MAX`)
2. Implementiere IP-Whitelist für bekannte IPs
3. Nutze Authenticated Rate Limits (höher für eingeloggte Nutzer)

### Problem: Backups fehlgeschlagen

**Lösung:**
1. Prüfe Database-Größe (kostenloser Plan: max 500 MB)
2. Prüfe Storage-Quota
3. Kontaktiere Supabase Support

---

## 8. Nützliche Links

- [Supabase Rate Limiting Docs](https://supabase.com/docs/guides/api/rest/security)
- [Supabase Backups Docs](https://supabase.com/docs/guides/database/backups)
- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)

