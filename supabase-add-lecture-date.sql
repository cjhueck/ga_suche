-- ============================================
-- Migration: lecture_date zu quotes und highlights hinzufügen
-- ============================================
-- Dieses SQL-Script in Supabase SQL Editor ausführen

-- Füge lecture_date Spalte zu quotes Tabelle hinzu, falls sie nicht existiert
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'quotes' 
    AND column_name = 'lecture_date'
  ) THEN
    ALTER TABLE public.quotes ADD COLUMN lecture_date VARCHAR(50);
    COMMENT ON COLUMN public.quotes.lecture_date IS 'Datum des Vortrags im Format YYYY-MM-DD oder deutsches Format';
  END IF;
END $$;

-- Füge lecture_date Spalte zu highlights Tabelle hinzu, falls sie nicht existiert
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'highlights' 
    AND column_name = 'lecture_date'
  ) THEN
    ALTER TABLE public.highlights ADD COLUMN lecture_date VARCHAR(50);
    COMMENT ON COLUMN public.highlights.lecture_date IS 'Datum des Vortrags im Format YYYY-MM-DD oder deutsches Format';
  END IF;
END $$;

-- Erstelle Index für lecture_date in quotes (optional, für bessere Performance bei Sortierung)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND table_name = 'quotes' 
    AND indexname = 'idx_quotes_lecture_date'
  ) THEN
    CREATE INDEX idx_quotes_lecture_date ON public.quotes(lecture_date);
  END IF;
END $$;

-- Erstelle Index für lecture_date in highlights (optional, für bessere Performance bei Sortierung)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND table_name = 'highlights' 
    AND indexname = 'idx_highlights_lecture_date'
  ) THEN
    CREATE INDEX idx_highlights_lecture_date ON public.highlights(lecture_date);
  END IF;
END $$;


