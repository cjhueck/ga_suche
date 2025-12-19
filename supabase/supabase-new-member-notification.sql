-- ============================================
-- Supabase: Benachrichtigung bei neuen Mitgliedern
-- ============================================
-- Dieses Script richtet eine E-Mail-Benachrichtigung ein,
-- die automatisch gesendet wird, wenn sich ein neues Mitglied registriert.
--
-- WICHTIG: Sie müssen zuerst die pg_net Extension aktivieren!
-- Gehen Sie zu: Database → Extensions → pg_net → Enable
-- ============================================

-- ============================================
-- Option 1: E-Mail-Benachrichtigung über HTTP Webhook
-- ============================================
-- Diese Funktion sendet eine HTTP-Anfrage an einen Webhook-Service
-- (z.B. EmailJS, Zapier, Make.com, oder Ihre eigene API)

CREATE OR REPLACE FUNCTION notify_admin_new_user()
RETURNS TRIGGER AS $$
DECLARE
  webhook_url TEXT := 'https://YOUR_WEBHOOK_URL_HERE'; -- Ersetzen Sie dies!
  admin_email TEXT := 'admin@ihre-domain.de'; -- Ihre E-Mail-Adresse
  payload JSONB;
BEGIN
  -- Erstelle Payload mit User-Daten
  payload := jsonb_build_object(
    'event', 'user.signup',
    'user_id', NEW.id,
    'email', NEW.email,
    'created_at', NEW.created_at,
    'email_confirmed', CASE WHEN NEW.confirmed_at IS NOT NULL THEN true ELSE false END,
    'to', admin_email,
    'subject', '🎉 Neues Mitglied registriert',
    'body', format(
      'Ein neues Mitglied hat sich registriert:%n%n' ||
      'E-Mail: %s%n' ||
      'User ID: %s%n' ||
      'Registriert am: %s%n' ||
      'E-Mail bestätigt: %s',
      NEW.email,
      NEW.id,
      to_char(NEW.created_at, 'DD.MM.YYYY HH24:MI:SS'),
      CASE WHEN NEW.confirmed_at IS NOT NULL THEN 'Ja' ELSE 'Nein' END
    )
  );
  
  -- Sende HTTP Request
  -- HINWEIS: Diese Funktion benötigt die pg_net Extension!
  PERFORM net.http_post(
    url := webhook_url,
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'User-Agent', 'Supabase-New-User-Notification'
    ),
    body := payload::text
  );
  
  RETURN NEW;
EXCEPTION
  WHEN OTHERS THEN
    -- Logge Fehler, aber verhindere nicht die User-Erstellung
    RAISE WARNING 'Fehler beim Senden der Benachrichtigung: %', SQLERRM;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger erstellen
DROP TRIGGER IF EXISTS on_new_user_notify_admin ON auth.users;
CREATE TRIGGER on_new_user_notify_admin
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION notify_admin_new_user();

-- ============================================
-- Option 2: Slack-Benachrichtigung
-- ============================================
-- Falls Sie Slack verwenden, können Sie diese Funktion nutzen:

CREATE OR REPLACE FUNCTION notify_slack_new_user()
RETURNS TRIGGER AS $$
DECLARE
  slack_webhook_url TEXT := 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK';
  slack_payload JSONB;
BEGIN
  slack_payload := jsonb_build_object(
    'text', '🎉 Neues Mitglied registriert!',
    'blocks', jsonb_build_array(
      jsonb_build_object(
        'type', 'section',
        'text', jsonb_build_object(
          'type', 'mrkdwn',
          'text', format(
            '*Neues Mitglied:*%n' ||
            'E-Mail: `%s`%n' ||
            'User ID: `%s`%n' ||
            'Registriert: %s',
            NEW.email,
            NEW.id,
            to_char(NEW.created_at, 'DD.MM.YYYY um HH24:MI Uhr')
          )
        )
      )
    )
  );
  
  PERFORM net.http_post(
    url := slack_webhook_url,
    headers := jsonb_build_object('Content-Type', 'application/json'),
    body := slack_payload::text
  );
  
  RETURN NEW;
EXCEPTION
  WHEN OTHERS THEN
    RAISE WARNING 'Fehler beim Senden der Slack-Benachrichtigung: %', SQLERRM;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger für Slack (optional - auskommentieren wenn nicht benötigt)
-- DROP TRIGGER IF EXISTS on_new_user_notify_slack ON auth.users;
-- CREATE TRIGGER on_new_user_notify_slack
--   AFTER INSERT ON auth.users
--   FOR EACH ROW
--   EXECUTE FUNCTION notify_slack_new_user();

-- ============================================
-- Option 3: Logging in eine eigene Tabelle
-- ============================================
-- Falls Sie die Benachrichtigungen auch lokal speichern möchten:

CREATE TABLE IF NOT EXISTS public.admin_notifications (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  notification_type VARCHAR(50) NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  user_email TEXT,
  notification_data JSONB,
  sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  success BOOLEAN DEFAULT true,
  error_message TEXT
);

-- Funktion zum Loggen
CREATE OR REPLACE FUNCTION log_admin_notification()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.admin_notifications (
    notification_type,
    user_id,
    user_email,
    notification_data
  ) VALUES (
    'user.signup',
    NEW.id,
    NEW.email,
    jsonb_build_object(
      'created_at', NEW.created_at,
      'confirmed_at', NEW.confirmed_at
    )
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger für Logging (optional)
-- DROP TRIGGER IF EXISTS on_new_user_log_notification ON auth.users;
-- CREATE TRIGGER on_new_user_log_notification
--   AFTER INSERT ON auth.users
--   FOR EACH ROW
--   EXECUTE FUNCTION log_admin_notification();

-- ============================================
-- Einrichtung
-- ============================================
-- 1. Aktivieren Sie die pg_net Extension:
--    Database → Extensions → pg_net → Enable
--
-- 2. Ersetzen Sie 'YOUR_WEBHOOK_URL_HERE' mit Ihrer tatsächlichen Webhook-URL
--    Beispiele:
--    - EmailJS: https://api.emailjs.com/api/v1.0/email/send
--    - Zapier: https://hooks.zapier.com/hooks/catch/YOUR_WEBHOOK_ID/
--    - Make.com: https://hook.eu1.make.com/YOUR_WEBHOOK_ID
--    - Eigene API: https://ihre-api.de/webhook/new-user
--
-- 3. Führen Sie dieses Script im Supabase SQL Editor aus
--
-- 4. Testen Sie die Einrichtung, indem Sie einen neuen Test-User erstellen
--
-- 5. Prüfen Sie die Logs in der admin_notifications Tabelle (falls aktiviert)

-- ============================================
-- Deaktivieren der Benachrichtigungen
-- ============================================
-- DROP TRIGGER IF EXISTS on_new_user_notify_admin ON auth.users;
-- DROP FUNCTION IF EXISTS notify_admin_new_user();

