-- ============================================
-- Supabase: Registrierte Mitglieder zählen
-- ============================================
-- Diese Funktion gibt die Anzahl der registrierten
-- Mitglieder zurück (aus auth.users).
-- SECURITY DEFINER erlaubt Zugriff auf auth.users
-- auch mit dem anon-Key.
-- ============================================

CREATE OR REPLACE FUNCTION get_registered_members_count()
RETURNS INTEGER AS $$
BEGIN
  RETURN (SELECT COUNT(*) FROM auth.users);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
