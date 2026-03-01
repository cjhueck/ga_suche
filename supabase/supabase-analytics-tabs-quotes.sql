-- ============================================
-- GA-Suche Analytics - Tab-Aufrufe & Zitat der Woche
-- ============================================
-- Migration: Fügt Tab-Views und Quote-Views zu Supabase Analytics hinzu
-- Führe dieses Script im Supabase SQL Editor aus (nach supabase-analytics.sql)

-- ============================================
-- 1. Spalten zu analytics_daily hinzufügen
-- ============================================
ALTER TABLE public.analytics_daily 
  ADD COLUMN IF NOT EXISTS quote_views INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS tabs JSONB DEFAULT '{}'::jsonb;

-- ============================================
-- 2. Spalte zu analytics_totals hinzufügen
-- ============================================
ALTER TABLE public.analytics_totals 
  ADD COLUMN IF NOT EXISTS total_quote_views INTEGER DEFAULT 0;

-- ============================================
-- 3. FUNCTION: Tab-View oder Quote-View inkrementieren
-- ============================================
CREATE OR REPLACE FUNCTION public.increment_analytics_tab_quote(
  p_date DATE,
  p_type TEXT,  -- 'quote' oder 'tab'
  p_tab_name TEXT DEFAULT NULL  -- nur bei p_type='tab': z.B. 'texte', 'thematic'
)
RETURNS void AS $$
DECLARE
  v_current_val INTEGER;
  v_new_tabs JSONB;
BEGIN
  IF p_type = 'quote' THEN
    -- Quote-View: quote_views + 1
    INSERT INTO public.analytics_daily (date, quote_views, views, searches, lectures, updated_at)
    VALUES (p_date, 1, 0, 0, 0, NOW())
    ON CONFLICT (date) DO UPDATE SET
      quote_views = analytics_daily.quote_views + 1,
      updated_at = NOW();
    
    UPDATE public.analytics_totals SET
      total_quote_views = total_quote_views + 1,
      last_updated = NOW()
    WHERE id = 1;
    
  ELSIF p_type = 'tab' AND p_tab_name IS NOT NULL AND p_tab_name != '' THEN
    -- Tab-View: tabs->>p_tab_name + 1
    INSERT INTO public.analytics_daily (date, tabs, views, searches, lectures, updated_at)
    VALUES (p_date, jsonb_build_object(p_tab_name, 1), 0, 0, 0, NOW())
    ON CONFLICT (date) DO UPDATE SET
      tabs = jsonb_set(
        COALESCE(analytics_daily.tabs, '{}'::jsonb),
        ARRAY[p_tab_name],
        to_jsonb(COALESCE((analytics_daily.tabs->>p_tab_name)::int, 0) + 1)
      ),
      updated_at = NOW();
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 4. recalculate_analytics_totals erweitern
-- ============================================
CREATE OR REPLACE FUNCTION public.recalculate_analytics_totals()
RETURNS void AS $$
DECLARE
  v_views INTEGER;
  v_searches INTEGER;
  v_lectures INTEGER;
  v_unique_users INTEGER;
  v_quote_views INTEGER;
BEGIN
  SELECT 
    COALESCE(SUM(views), 0),
    COALESCE(SUM(searches), 0),
    COALESCE(SUM(lectures), 0),
    COALESCE(SUM(unique_users), 0),
    COALESCE(SUM(quote_views), 0)
  INTO v_views, v_searches, v_lectures, v_unique_users, v_quote_views
  FROM public.analytics_daily;
  
  UPDATE public.analytics_totals SET
    total_views = v_views,
    total_searches = v_searches,
    total_lectures = v_lectures,
    total_unique_users = v_unique_users,
    total_quote_views = COALESCE(v_quote_views, 0),
    last_updated = NOW()
  WHERE id = 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 5. GRANT für neue Funktion
-- ============================================
GRANT EXECUTE ON FUNCTION public.increment_analytics_tab_quote(DATE, TEXT, TEXT) TO anon, authenticated;
