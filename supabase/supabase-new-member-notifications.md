# Benachrichtigungen über neue Mitgliederanmeldungen

Supabase bietet mehrere Möglichkeiten, um über neue Mitgliederanmeldungen benachrichtigt zu werden:

## Option 1: Database Webhook (Empfohlen) ⭐

**📖 Detaillierte Schritt-für-Schritt-Anleitung:** Siehe `supabase-webhook-setup-anleitung.md`

### Schnellstart:

1. **Gehen Sie zu:** Database → Webhooks im Supabase Dashboard
2. **Klicken Sie auf:** "Create a new webhook"
3. **Konfiguration:**
   - **Name:** `new-user-signup`
   - **Table:** `auth.users`
   - **Events:** `INSERT`
   - **HTTP Request:**
     - **URL:** Ihre Webhook-URL (z.B. Zapier, Make.com, EmailJS, oder eigene API)
     - **Method:** POST
     - **Headers:** 
       ```json
       {
         "Content-Type": "application/json",
         "Authorization": "Bearer YOUR_SECRET_TOKEN"
       }
       ```
     - **Body:** 
       ```json
       {
         "event": "user.signup",
         "user_id": "{{ $body.id }}",
         "email": "{{ $body.email }}",
         "created_at": "{{ $body.created_at }}"
       }
       ```

### Empfohlene Services für Webhook-URLs:

- **EmailJS** (kostenlos bis 200 E-Mails/Monat) - Einfachste E-Mail-Lösung
- **Zapier** (kostenlos bis 100 Tasks/Monat) - No-Code Automation
- **Make.com** (kostenlos bis 1.000 Operations/Monat) - No-Code Automation
- **Eigene API** - Maximale Kontrolle

### Alternative: E-Mail-Benachrichtigung über pg_net

Sie können auch direkt eine E-Mail senden, indem Sie die `pg_net` Extension verwenden:

```sql
-- Aktivieren Sie pg_net Extension (falls noch nicht aktiviert)
CREATE EXTENSION IF NOT EXISTS pg_net;

-- Funktion zum Senden von E-Mail-Benachrichtigungen
CREATE OR REPLACE FUNCTION notify_new_user_signup()
RETURNS TRIGGER AS $$
DECLARE
  webhook_url TEXT := 'https://api.emailjs.com/api/v1.0/email/send'; -- Oder Ihre eigene API
  payload JSONB;
BEGIN
  -- Erstelle Payload mit User-Daten
  payload := jsonb_build_object(
    'user_id', NEW.id,
    'email', NEW.email,
    'created_at', NEW.created_at,
    'confirmed_at', NEW.confirmed_at
  );
  
  -- Sende HTTP Request (z.B. an EmailJS, SendGrid, etc.)
  PERFORM net.http_post(
    url := webhook_url,
    headers := jsonb_build_object(
      'Content-Type', 'application/json'
    ),
    body := payload::text
  );
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger erstellen
DROP TRIGGER IF EXISTS on_new_user_signup ON auth.users;
CREATE TRIGGER on_new_user_signup
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION notify_new_user_signup();
```

## Option 2: Supabase Edge Function

Erstellen Sie eine Edge Function, die bei Auth-Events ausgelöst wird:

1. **Erstellen Sie eine neue Edge Function:**
   ```bash
   supabase functions new notify-new-user
   ```

2. **Code für `supabase/functions/notify-new-user/index.ts`:**
   ```typescript
   import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
   import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

   serve(async (req) => {
     try {
       const { record } = await req.json()
       
       // Sende E-Mail-Benachrichtigung
       const emailBody = `
         Neues Mitglied registriert:
         
         E-Mail: ${record.email}
         User ID: ${record.id}
         Registriert am: ${new Date(record.created_at).toLocaleString('de-DE')}
       `
       
       // Verwenden Sie einen E-Mail-Service (z.B. Resend, SendGrid)
       // Hier ein Beispiel mit einem Webhook:
       await fetch('YOUR_WEBHOOK_URL', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({
           to: 'admin@ihre-domain.de',
           subject: 'Neues Mitglied registriert',
           body: emailBody
         })
       })
       
       return new Response(JSON.stringify({ success: true }), {
         headers: { 'Content-Type': 'application/json' },
         status: 200
       })
     } catch (error) {
       return new Response(JSON.stringify({ error: error.message }), {
         headers: { 'Content-Type': 'application/json' },
         status: 500
       })
     }
   })
   ```

3. **Deployen Sie die Function:**
   ```bash
   supabase functions deploy notify-new-user
   ```

4. **Richten Sie einen Database Webhook ein**, der die Function aufruft:
   - Table: `auth.users`
   - Event: `INSERT`
   - URL: `https://YOUR_PROJECT.supabase.co/functions/v1/notify-new-user`

## Option 3: Einfache E-Mail über Database Trigger (mit pg_net)

Die einfachste Lösung ist ein Database Trigger, der direkt eine E-Mail sendet:

```sql
-- Siehe supabase-new-member-notification.sql
```

## Option 4: Integration mit externen Services

### Zapier / Make.com (n8n)

1. Erstellen Sie einen Zap/Scenario
2. Wählen Sie "Supabase" als Trigger
3. Event: "New Row" in `auth.users`
4. Aktion: E-Mail senden oder Slack-Benachrichtigung

### Slack-Benachrichtigung

```sql
CREATE OR REPLACE FUNCTION notify_slack_new_user()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM net.http_post(
    url := 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
    headers := jsonb_build_object('Content-Type', 'application/json'),
    body := jsonb_build_object(
      'text', '🎉 Neues Mitglied registriert!',
      'blocks', jsonb_build_array(
        jsonb_build_object(
          'type', 'section',
          'text', jsonb_build_object(
            'type', 'mrkdwn',
            'text', format('*E-Mail:* %s\n*Registriert am:* %s', NEW.email, NEW.created_at)
          )
        )
      )
    )::text
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Empfohlene Lösung

Für die einfachste Einrichtung empfehle ich **Option 1 (Database Webhook)** mit einem Service wie:
- **EmailJS** (kostenlos für bis zu 200 E-Mails/Monat)
- **SendGrid** (kostenlos für bis zu 100 E-Mails/Tag)
- **Resend** (kostenlos für bis zu 3.000 E-Mails/Monat)

Oder verwenden Sie **Zapier/Make.com** für eine no-code Lösung.

