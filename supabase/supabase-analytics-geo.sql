-- ============================================
-- GA-Suche Analytics - Geo-Tracking (Länder & Städte)
-- ============================================
-- Migration: Fügt Geo-Statistiken zu Supabase Analytics hinzu
-- Führe dieses Script im Supabase SQL Editor aus (nach supabase-analytics.sql)
-- DSGVO-konform: Es werden nur Ländercodes, Ländernamen, Städte und Regionen
-- gespeichert – keine IP-Adressen.

-- ============================================
-- 1. Tabelle analytics_geo erstellen
-- ============================================
CREATE TABLE IF NOT EXISTS public.analytics_geo (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  date DATE NOT NULL,
  country_code TEXT NOT NULL,
  country_name TEXT NOT NULL,
  city TEXT,
  region TEXT,
  count INTEGER DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(date, country_code, city)
);

-- Index für schnelle Abfragen nach Datum
CREATE INDEX IF NOT EXISTS idx_analytics_geo_date ON public.analytics_geo(date);

-- ============================================
-- 2. RPC-Funktion: Geo-Eintrag inkrementieren
-- ============================================
CREATE OR REPLACE FUNCTION public.increment_analytics_geo(
  p_date DATE,
  p_country_code TEXT,
  p_country_name TEXT,
  p_city TEXT DEFAULT NULL,
  p_region TEXT DEFAULT NULL
)
RETURNS void AS $$
BEGIN
  INSERT INTO public.analytics_geo (date, country_code, country_name, city, region, count, updated_at)
  VALUES (p_date, p_country_code, p_country_name, p_city, p_region, 1, NOW())
  ON CONFLICT (date, country_code, city) DO UPDATE SET
    count = analytics_geo.count + 1,
    country_name = COALESCE(EXCLUDED.country_name, analytics_geo.country_name),
    region = COALESCE(EXCLUDED.region, analytics_geo.region),
    updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 3. RPC-Funktion: Geo-Statistiken laden
-- ============================================
CREATE OR REPLACE FUNCTION public.get_analytics_geo_stats()
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_agg(row_to_json(t)) INTO result
  FROM (
    SELECT
      country_code,
      country_name,
      SUM(count) AS total_count,
      json_agg(
        json_build_object('city', city, 'region', region, 'count', count)
        ORDER BY count DESC
      ) AS cities
    FROM public.analytics_geo
    GROUP BY country_code, country_name
    ORDER BY SUM(count) DESC
  ) t;
  RETURN COALESCE(result, '[]'::json);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 4. GRANTs
-- ============================================
GRANT SELECT, INSERT, UPDATE ON public.analytics_geo TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.increment_analytics_geo(DATE, TEXT, TEXT, TEXT, TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.get_analytics_geo_stats() TO anon, authenticated;

-- ============================================
-- 5. RLS (Row Level Security)
-- ============================================
ALTER TABLE public.analytics_geo ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anon read analytics_geo"
  ON public.analytics_geo FOR SELECT TO anon
  USING (true);

CREATE POLICY "Allow anon insert analytics_geo"
  ON public.analytics_geo FOR INSERT TO anon
  WITH CHECK (true);

CREATE POLICY "Allow anon update analytics_geo"
  ON public.analytics_geo FOR UPDATE TO anon
  USING (true);
