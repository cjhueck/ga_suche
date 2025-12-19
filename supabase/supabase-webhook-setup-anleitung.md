# Schritt-für-Schritt Anleitung: Database Webhook für neue Mitglieder

Diese Anleitung zeigt Ihnen, wie Sie einen Database Webhook in Supabase einrichten, um bei jeder neuen Mitgliederanmeldung benachrichtigt zu werden.

## Voraussetzungen

- Supabase-Projekt mit aktivierter Authentication
- Zugriff auf das Supabase Dashboard
- Eine Webhook-URL (siehe Optionen unten)

---

## Schritt 1: Webhook-URL erstellen

Wählen Sie einen der folgenden Services:

### Option A: EmailJS (Kostenlos bis 200 E-Mails/Monat)

1. **Registrieren Sie sich bei EmailJS:** https://www.emailjs.com/
2. **Erstellen Sie einen Email Service:**
   - Gehen Sie zu "Email Services"
   - Wählen Sie Ihren E-Mail-Provider (Gmail, Outlook, etc.)
   - Folgen Sie der Anleitung zur Einrichtung
3. **Erstellen Sie eine Email Template:**
   - Gehen Sie zu "Email Templates"
   - Erstellen Sie ein neues Template mit folgendem Inhalt:
   ```
   Betreff: 🎉 Neues Mitglied registriert
   
   Ein neues Mitglied hat sich registriert:
   
   E-Mail: {{email}}
   User ID: {{user_id}}
   Registriert am: {{created_at}}
   ```
4. **Kopieren Sie die Service ID und Template ID**
5. **Ihre Webhook-URL wird sein:**
   ```
   https://api.emailjs.com/api/v1.0/email/send
   ```

### Option B: Zapier (No-Code Lösung)

1. **Registrieren Sie sich bei Zapier:** https://zapier.com/
2. **Erstellen Sie einen neuen Zap:**
   - Trigger: "Webhooks by Zapier" → "Catch Hook"
   - Kopieren Sie die Webhook-URL (z.B. `https://hooks.zapier.com/hooks/catch/123456/abcdef`)
3. **Fügen Sie eine Aktion hinzu:**
   - "Email by Zapier" → "Send Outbound Email"
   - Konfigurieren Sie die E-Mail-Vorlage
4. **Aktivieren Sie den Zap**

### Option C: Make.com (früher Integromat)

1. **Registrieren Sie sich bei Make.com:** https://www.make.com/
2. **Erstellen Sie ein neues Scenario:**
   - Trigger: "Webhooks" → "Custom webhook"
   - Kopieren Sie die Webhook-URL
3. **Fügen Sie ein Modul hinzu:**
   - "Email" → "Send an Email"
   - Konfigurieren Sie die E-Mail

### Option D: Eigene API-Endpoint

Falls Sie einen eigenen Server haben, können Sie einen einfachen Endpoint erstellen:

```javascript
// Beispiel: Express.js Endpoint
app.post('/webhook/new-user', async (req, res) => {
  const { email, user_id, created_at } = req.body;
  
  // Sende E-Mail
  await sendEmail({
    to: 'admin@ihre-domain.de',
    subject: 'Neues Mitglied registriert',
    body: `E-Mail: ${email}\nUser ID: ${user_id}\nRegistriert: ${created_at}`
  });
  
  res.json({ success: true });
});
```

---

## Schritt 2: Webhook im Supabase Dashboard einrichten

1. **Öffnen Sie das Supabase Dashboard:**
   - Gehen Sie zu: https://app.supabase.com/
   - Wählen Sie Ihr Projekt aus

2. **Navigieren Sie zu Database → Webhooks:**
   - Im linken Menü: "Database" → "Webhooks"

3. **Klicken Sie auf "Create a new webhook"**

4. **Füllen Sie das Formular aus:**

   **Basic Settings:**
   - **Name:** `new-user-signup` (oder ein anderer Name Ihrer Wahl)
   - **Table:** `auth.users`
   - **Events:** Wählen Sie `INSERT` aus
   
   **HTTP Request:**
   - **URL:** Ihre Webhook-URL (z.B. von EmailJS, Zapier, etc.)
   - **Method:** `POST`
   - **HTTP Headers:** 
     ```json
     {
       "Content-Type": "application/json"
     }
     ```
     Falls Sie einen Authorization-Header benötigen:
     ```json
     {
       "Content-Type": "application/json",
       "Authorization": "Bearer YOUR_SECRET_TOKEN"
     }
     ```
   
   **HTTP Request Body:**
   
   Für EmailJS:
   ```json
   {
     "service_id": "YOUR_SERVICE_ID",
     "template_id": "YOUR_TEMPLATE_ID",
     "user_id": "YOUR_USER_ID",
     "template_params": {
       "email": "{{ $body.email }}",
       "user_id": "{{ $body.id }}",
       "created_at": "{{ $body.created_at }}"
     }
   }
   ```
   
   Für Zapier/Make.com (einfache Variante):
   ```json
   {
     "event": "user.signup",
     "email": "{{ $body.email }}",
     "user_id": "{{ $body.id }}",
     "created_at": "{{ $body.created_at }}",
     "email_confirmed": "{{ $body.confirmed_at }}"
   }
   ```
   
   Für eigene API:
   ```json
   {
     "email": "{{ $body.email }}",
     "user_id": "{{ $body.id }}",
     "created_at": "{{ $body.created_at }}",
     "confirmed_at": "{{ $body.confirmed_at }}"
   }
   ```

5. **Klicken Sie auf "Save"**

---

## Schritt 3: Webhook testen

1. **Erstellen Sie einen Test-User:**
   - Gehen Sie zu Authentication → Users
   - Klicken Sie auf "Add user"
   - Geben Sie eine Test-E-Mail ein
   - Erstellen Sie den User

2. **Prüfen Sie die Webhook-Logs:**
   - Gehen Sie zurück zu Database → Webhooks
   - Klicken Sie auf Ihren Webhook
   - Prüfen Sie die "Recent deliveries" Sektion
   - Sie sollten einen erfolgreichen Request sehen (Status 200)

3. **Prüfen Sie Ihre E-Mail/Service:**
   - Sie sollten eine Benachrichtigung erhalten haben

---

## Schritt 4: Webhook-Logs überwachen

Supabase speichert alle Webhook-Aufrufe:

- **Erfolgreiche Requests:** Status 200
- **Fehlgeschlagene Requests:** Status 4xx/5xx
- **Request Body:** Was wurde gesendet
- **Response:** Was der Service zurückgegeben hat

**Tipp:** Prüfen Sie regelmäßig die Logs, um sicherzustellen, dass alles funktioniert.

---

## Fehlerbehebung

### Webhook wird nicht ausgelöst

1. **Prüfen Sie die Table:** Muss `auth.users` sein
2. **Prüfen Sie das Event:** Muss `INSERT` sein
3. **Prüfen Sie die Logs:** Gibt es Fehler?

### Webhook wird ausgelöst, aber keine E-Mail

1. **Prüfen Sie die Webhook-Logs:** Was ist die Response?
2. **Prüfen Sie die Webhook-URL:** Ist sie korrekt?
3. **Prüfen Sie die Request Body:** Sind die Variablen korrekt formatiert?
4. **Prüfen Sie Ihren E-Mail-Service:** Funktioniert er unabhängig?

### Häufige Fehler

- **404 Not Found:** Webhook-URL ist falsch
- **401 Unauthorized:** Authorization-Header fehlt oder ist falsch
- **400 Bad Request:** Request Body Format ist falsch
- **500 Internal Server Error:** Problem beim E-Mail-Service

---

## Erweiterte Konfiguration

### Nur bei bestätigten E-Mails benachrichtigen

Falls Sie nur bei bestätigten E-Mails benachrichtigt werden möchten, können Sie einen Filter hinzufügen:

1. Gehen Sie zu Database → Webhooks
2. Bearbeiten Sie Ihren Webhook
3. Fügen Sie einen Filter hinzu:
   ```sql
   confirmed_at IS NOT NULL
   ```

### Mehrere Benachrichtigungen

Sie können mehrere Webhooks erstellen:
- E-Mail an Admin
- Slack-Benachrichtigung
- Discord-Benachrichtigung
- etc.

Jeder Webhook wird unabhängig ausgelöst.

---

## Alternative: SQL-Trigger (für fortgeschrittene Nutzer)

Falls Sie mehr Kontrolle benötigen, können Sie auch einen SQL-Trigger verwenden:

Siehe: `supabase-new-member-notification.sql`

---

## Zusammenfassung

✅ **Was Sie jetzt haben:**
- Automatische Benachrichtigung bei jeder neuen Mitgliederanmeldung
- Webhook-Logs zur Überwachung
- Einfache Konfiguration über das Dashboard

**Nächste Schritte:**
- Testen Sie die Einrichtung mit einem Test-User
- Überwachen Sie die Logs regelmäßig
- Passen Sie die E-Mail-Vorlage nach Bedarf an

