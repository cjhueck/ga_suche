-- ============================================
-- GA-Suche Mitgliederbereich - Gespeicherte Themenabfragen
-- ============================================
-- Dieses SQL-Script in Supabase SQL Editor ausführen

-- ============================================
-- SAVED_THEMATIC_SEARCHES Tabelle
-- ============================================
CREATE TABLE IF NOT EXISTS public.saved_thematic_searches (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  query TEXT NOT NULL,                          -- Die Suchanfrage
  title VARCHAR(500),                           -- Optionaler benutzerdefinierter Titel
  content TEXT NOT NULL,                        -- Die KI-generierte Antwort
  sources JSONB DEFAULT '[]',                   -- Array mit Quellen [{ID, index, title, score, ...}]
  search_method VARCHAR(100),                   -- z.B. 'hybrid-thematic-unified'
  total_matches INTEGER DEFAULT 0,              -- Anzahl der gefundenen Treffer
  ga_filter VARCHAR(50),                        -- Optional: GA-Filter der bei der Suche verwendet wurde
  limit_used INTEGER DEFAULT 100,               -- Limit das bei der Suche verwendet wurde
  tags TEXT[] DEFAULT '{}',                     -- Benutzerdefinierte Tags
  notes TEXT,                                   -- Persönliche Notizen zur Abfrage
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indizes für schnelle Abfragen
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'saved_thematic_searches' 
    AND indexname = 'idx_saved_thematic_searches_user'
  ) THEN
    CREATE INDEX idx_saved_thematic_searches_user ON public.saved_thematic_searches(user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'saved_thematic_searches' 
    AND indexname = 'idx_saved_thematic_searches_tags'
  ) THEN
    CREATE INDEX idx_saved_thematic_searches_tags ON public.saved_thematic_searches USING GIN(tags);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'saved_thematic_searches' 
    AND indexname = 'idx_saved_thematic_searches_query'
  ) THEN
    CREATE INDEX idx_saved_thematic_searches_query ON public.saved_thematic_searches USING GIN(to_tsvector('german', query));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'saved_thematic_searches' 
    AND indexname = 'idx_saved_thematic_searches_created'
  ) THEN
    CREATE INDEX idx_saved_thematic_searches_created ON public.saved_thematic_searches(created_at DESC);
  END IF;
END $$;

-- Row Level Security (RLS)
ALTER TABLE public.saved_thematic_searches ENABLE ROW LEVEL SECURITY;

-- Policies für saved_thematic_searches (nur eigene Abfragen sichtbar)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'saved_thematic_searches' 
    AND policyname = 'Users can view own saved searches'
  ) THEN
    CREATE POLICY "Users can view own saved searches" 
      ON public.saved_thematic_searches FOR SELECT 
      USING (auth.uid() = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'saved_thematic_searches' 
    AND policyname = 'Users can insert own saved searches'
  ) THEN
    CREATE POLICY "Users can insert own saved searches" 
      ON public.saved_thematic_searches FOR INSERT 
      WITH CHECK (auth.uid() = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'saved_thematic_searches' 
    AND policyname = 'Users can update own saved searches'
  ) THEN
    CREATE POLICY "Users can update own saved searches" 
      ON public.saved_thematic_searches FOR UPDATE 
      USING (auth.uid() = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'saved_thematic_searches' 
    AND policyname = 'Users can delete own saved searches'
  ) THEN
    CREATE POLICY "Users can delete own saved searches" 
      ON public.saved_thematic_searches FOR DELETE 
      USING (auth.uid() = user_id);
  END IF;
END $$;

-- Trigger für updated_at
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger 
    WHERE tgname = 'update_saved_thematic_searches_updated_at'
  ) THEN
    CREATE TRIGGER update_saved_thematic_searches_updated_at 
      BEFORE UPDATE ON public.saved_thematic_searches
      FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
  END IF;
END $$;

-- ============================================
-- FERTIG! 🎉
-- ============================================
-- Die Tabelle ist jetzt bereit für gespeicherte Themenabfragen.
-- Jede Abfrage ist nur für den jeweiligen Benutzer sichtbar (RLS).

