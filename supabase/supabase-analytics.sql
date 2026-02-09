-- ============================================
-- GA-Suche Analytics - Supabase Schema
-- ============================================
-- Dieses SQL-Script in Supabase SQL Editor ausführen
-- Speichert Nutzungsstatistiken PERSISTENT in der Datenbank

-- ============================================
-- 1. ANALYTICS_DAILY Tabelle - Tägliche Statistiken
-- ============================================
CREATE TABLE IF NOT EXISTS public.analytics_daily (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  date DATE NOT NULL UNIQUE,  -- Eindeutiges Datum (ein Eintrag pro Tag)
  views INTEGER DEFAULT 0,
  searches INTEGER DEFAULT 0,
  lectures INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index für schnelle Datum-Abfragen
CREATE INDEX IF NOT EXISTS idx_analytics_daily_date ON public.analytics_daily(date DESC);

-- RLS DEAKTIVIEREN für anonymen Zugriff (Backend schreibt ohne Auth)
ALTER TABLE public.analytics_daily DISABLE ROW LEVEL SECURITY;

-- Alternativ: Policy für anonymen Zugriff (falls RLS aktiviert bleiben soll)
-- CREATE POLICY "Allow anonymous read" ON public.analytics_daily FOR SELECT USING (true);
-- CREATE POLICY "Allow anonymous insert" ON public.analytics_daily FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Allow anonymous update" ON public.analytics_daily FOR UPDATE USING (true);


-- ============================================
-- 2. ANALYTICS_TOTALS Tabelle - Kumulative Gesamtwerte
-- ============================================
-- Diese Tabelle speichert die berechneten Gesamtwerte für schnellen Zugriff
CREATE TABLE IF NOT EXISTS public.analytics_totals (
  id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),  -- Nur ein Eintrag erlaubt
  total_views INTEGER DEFAULT 0,
  total_searches INTEGER DEFAULT 0,
  total_lectures INTEGER DEFAULT 0,
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Initialer Eintrag
INSERT INTO public.analytics_totals (id, total_views, total_searches, total_lectures)
VALUES (1, 0, 0, 0)
ON CONFLICT (id) DO NOTHING;

-- RLS deaktivieren
ALTER TABLE public.analytics_totals DISABLE ROW LEVEL SECURITY;


-- ============================================
-- 3. FUNCTION: Inkrementiere Tagesstatistik
-- ============================================
-- Diese Funktion wird vom Backend aufgerufen
CREATE OR REPLACE FUNCTION public.increment_analytics(
  p_date DATE,
  p_views INTEGER DEFAULT 0,
  p_searches INTEGER DEFAULT 0,
  p_lectures INTEGER DEFAULT 0
)
RETURNS void AS $$
BEGIN
  -- Upsert: Erstelle oder aktualisiere Tagesstatistik
  INSERT INTO public.analytics_daily (date, views, searches, lectures, updated_at)
  VALUES (p_date, p_views, p_searches, p_lectures, NOW())
  ON CONFLICT (date) DO UPDATE SET
    views = analytics_daily.views + EXCLUDED.views,
    searches = analytics_daily.searches + EXCLUDED.searches,
    lectures = analytics_daily.lectures + EXCLUDED.lectures,
    updated_at = NOW();
  
  -- Aktualisiere Gesamtwerte
  UPDATE public.analytics_totals SET
    total_views = total_views + p_views,
    total_searches = total_searches + p_searches,
    total_lectures = total_lectures + p_lectures,
    last_updated = NOW()
  WHERE id = 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- ============================================
-- 4. FUNCTION: Berechne Gesamtwerte neu
-- ============================================
-- Falls die Totals-Tabelle aus dem Sync geraten ist
CREATE OR REPLACE FUNCTION public.recalculate_analytics_totals()
RETURNS void AS $$
DECLARE
  v_views INTEGER;
  v_searches INTEGER;
  v_lectures INTEGER;
BEGIN
  SELECT 
    COALESCE(SUM(views), 0),
    COALESCE(SUM(searches), 0),
    COALESCE(SUM(lectures), 0)
  INTO v_views, v_searches, v_lectures
  FROM public.analytics_daily;
  
  UPDATE public.analytics_totals SET
    total_views = v_views,
    total_searches = v_searches,
    total_lectures = v_lectures,
    last_updated = NOW()
  WHERE id = 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- ============================================
-- 5. Trigger für updated_at
-- ============================================
CREATE OR REPLACE FUNCTION public.update_analytics_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_analytics_daily_updated_at ON public.analytics_daily;
CREATE TRIGGER update_analytics_daily_updated_at 
  BEFORE UPDATE ON public.analytics_daily
  FOR EACH ROW EXECUTE FUNCTION public.update_analytics_updated_at();


-- ============================================
-- 6. UNIQUE VISITORS Tracking
-- ============================================
-- Tabelle für eindeutige Besucher pro Tag (visitor_id aus localStorage)
CREATE TABLE IF NOT EXISTS public.analytics_visitors (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  date DATE NOT NULL,
  visitor_id TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(date, visitor_id)  -- Ein Besucher wird pro Tag nur einmal gezählt
);

-- Index für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_analytics_visitors_date ON public.analytics_visitors(date DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_visitors_visitor ON public.analytics_visitors(visitor_id);

-- RLS deaktivieren
ALTER TABLE public.analytics_visitors DISABLE ROW LEVEL SECURITY;

-- Spalte unique_users zu analytics_daily hinzufügen (falls noch nicht vorhanden)
ALTER TABLE public.analytics_daily ADD COLUMN IF NOT EXISTS unique_users INTEGER DEFAULT 0;

-- Spalte total_unique_users zu analytics_totals hinzufügen
ALTER TABLE public.analytics_totals ADD COLUMN IF NOT EXISTS total_unique_users INTEGER DEFAULT 0;


-- ============================================
-- 7. FUNCTION: Unique Visitor tracken
-- ============================================
-- Gibt TRUE zurück wenn der Besucher neu ist (für diesen Tag), FALSE wenn bereits gezählt
CREATE OR REPLACE FUNCTION public.track_unique_visitor(
  p_date DATE,
  p_visitor_id TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
  v_row_count INTEGER;
BEGIN
  -- Versuche den Besucher einzufügen
  INSERT INTO public.analytics_visitors (date, visitor_id)
  VALUES (p_date, p_visitor_id)
  ON CONFLICT (date, visitor_id) DO NOTHING;
  
  -- Prüfe ob der INSERT erfolgreich war (neuer Besucher)
  -- ROW_COUNT gibt INTEGER zurück: 1 = neuer Eintrag, 0 = bereits vorhanden
  GET DIAGNOSTICS v_row_count = ROW_COUNT;
  
  IF v_row_count > 0 THEN
    -- Neuer Besucher: Inkrementiere unique_users in analytics_daily
    UPDATE public.analytics_daily 
    SET unique_users = unique_users + 1, updated_at = NOW()
    WHERE date = p_date;
    
    -- Falls kein Eintrag für diesen Tag existiert, erstelle einen
    IF NOT FOUND THEN
      INSERT INTO public.analytics_daily (date, unique_users, views, searches, lectures, updated_at)
      VALUES (p_date, 1, 0, 0, 0, NOW())
      ON CONFLICT (date) DO UPDATE SET
        unique_users = analytics_daily.unique_users + 1,
        updated_at = NOW();
    END IF;
    
    -- Aktualisiere Gesamtwerte
    UPDATE public.analytics_totals SET
      total_unique_users = total_unique_users + 1,
      last_updated = NOW()
    WHERE id = 1;
  END IF;
  
  RETURN v_row_count > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- ============================================
-- 8. FUNCTION: Gesamtwerte neu berechnen (aktualisiert)
-- ============================================
-- Überschreibt die alte Version mit unique_users Support
CREATE OR REPLACE FUNCTION public.recalculate_analytics_totals()
RETURNS void AS $$
DECLARE
  v_views INTEGER;
  v_searches INTEGER;
  v_lectures INTEGER;
  v_unique_users INTEGER;
BEGIN
  SELECT 
    COALESCE(SUM(views), 0),
    COALESCE(SUM(searches), 0),
    COALESCE(SUM(lectures), 0),
    COALESCE(SUM(unique_users), 0)
  INTO v_views, v_searches, v_lectures, v_unique_users
  FROM public.analytics_daily;
  
  UPDATE public.analytics_totals SET
    total_views = v_views,
    total_searches = v_searches,
    total_lectures = v_lectures,
    total_unique_users = v_unique_users,
    last_updated = NOW()
  WHERE id = 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- ============================================
-- FERTIG! 
-- ============================================
-- Nach Ausführung dieses Scripts:
-- 1. Die analytics_daily Tabelle speichert tägliche Statistiken
-- 2. Die analytics_totals Tabelle speichert kumulative Werte
-- 3. Die increment_analytics() Funktion wird vom Backend aufgerufen
-- 4. Alle Daten bleiben PERSISTENT - auch nach Render-Neustarts!
-- 5. Die analytics_visitors Tabelle trackt eindeutige Besucher pro Tag
-- 6. Die track_unique_visitor() Funktion zählt neue Besucher
