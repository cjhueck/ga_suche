-- ============================================
-- GA-Suche – Timeline-Schlagwort-Cache (global)
-- ============================================
-- In Supabase: SQL Editor → New query → gesamtes Script ausführen
--
-- Zweck: Schlagwort-spezifische Timeline-Suchergebnisse persistent speichern
-- (über Deploys und Nutzer hinweg; nicht nutzer-spezifisch).
--
-- Backend-Zugriff wie bei Analytics: anon key + SECURITY DEFINER RPCs
-- (kein neuer API-Key nötig, sofern SUPABASE_URL/ANON_KEY schon auf Render gesetzt sind).

-- ============================================
-- 1. Tabelle
-- ============================================
CREATE TABLE IF NOT EXISTS public.timeline_search_cache (
  keyword TEXT PRIMARY KEY,              -- normalisiert: lowercase, getrimmt
  keyword_display TEXT NOT NULL,       -- Anzeige-Form (Original-Schreibweise)
  results JSONB NOT NULL DEFAULT '[]', -- kombinierte Treffer (Keyword-DB + Volltext)
  result_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_timeline_search_cache_updated
  ON public.timeline_search_cache(updated_at DESC);

ALTER TABLE public.timeline_search_cache ENABLE ROW LEVEL SECURITY;

-- Direkter Tabellenzugriff nur lesend (optional, für Debugging im Dashboard)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = 'timeline_search_cache'
      AND policyname = 'Allow anonymous read timeline cache'
  ) THEN
    CREATE POLICY "Allow anonymous read timeline cache"
      ON public.timeline_search_cache FOR SELECT
      USING (true);
  END IF;
END $$;

-- Schreiben nur über RPC-Funktionen (SECURITY DEFINER)

-- ============================================
-- 2. Lesen: ein Schlagwort
-- ============================================
CREATE OR REPLACE FUNCTION public.get_timeline_search_cache(p_keyword TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_key TEXT := lower(trim(p_keyword));
  v_row public.timeline_search_cache%ROWTYPE;
BEGIN
  IF v_key IS NULL OR v_key = '' THEN
    RETURN NULL;
  END IF;

  SELECT * INTO v_row
  FROM public.timeline_search_cache
  WHERE keyword = v_key;

  IF NOT FOUND THEN
    RETURN NULL;
  END IF;

  RETURN jsonb_build_object(
    'keyword', v_row.keyword_display,
    'results', v_row.results,
    'resultCount', v_row.result_count,
    'timestamp', v_row.updated_at,
    'fromCache', true
  );
END;
$$;

-- ============================================
-- 3. Schreiben / Aktualisieren
-- ============================================
CREATE OR REPLACE FUNCTION public.upsert_timeline_search_cache(
  p_keyword TEXT,
  p_keyword_display TEXT,
  p_results JSONB,
  p_result_count INTEGER
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_key TEXT := lower(trim(p_keyword));
BEGIN
  IF v_key IS NULL OR v_key = '' THEN
    RAISE EXCEPTION 'keyword required';
  END IF;

  INSERT INTO public.timeline_search_cache (
    keyword,
    keyword_display,
    results,
    result_count,
    created_at,
    updated_at
  )
  VALUES (
    v_key,
    COALESCE(NULLIF(trim(p_keyword_display), ''), p_keyword),
    COALESCE(p_results, '[]'::jsonb),
    COALESCE(p_result_count, 0),
    NOW(),
    NOW()
  )
  ON CONFLICT (keyword) DO UPDATE SET
    keyword_display = EXCLUDED.keyword_display,
    results = EXCLUDED.results,
    result_count = EXCLUDED.result_count,
    updated_at = NOW();
END;
$$;

-- ============================================
-- 4. Cache leeren (bei Daten-Reload / Invalidierung)
-- ============================================
CREATE OR REPLACE FUNCTION public.clear_timeline_search_cache()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  TRUNCATE public.timeline_search_cache;
END;
$$;

-- ============================================
-- 5. RPC für anon/authenticated freigeben
-- ============================================
GRANT EXECUTE ON FUNCTION public.get_timeline_search_cache(TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.upsert_timeline_search_cache(TEXT, TEXT, JSONB, INTEGER) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.clear_timeline_search_cache() TO anon, authenticated;

-- ============================================
-- Fertig
-- ============================================
-- Prüfen: SELECT * FROM public.timeline_search_cache LIMIT 5;
-- Nach Backend-Anbindung: erste Timeline-Suche sollte hier Einträge erzeugen.
