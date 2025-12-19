-- ============================================
-- Migration: Multi-Absatz-Unterstützung für Markierungen
-- Fügt end_paragraph_id zu highlights, quotes und notes hinzu
-- ============================================

-- 1. HIGHLIGHTS: end_paragraph_id hinzufügen
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'highlights' 
    AND column_name = 'end_paragraph_id'
  ) THEN
    ALTER TABLE public.highlights ADD COLUMN end_paragraph_id VARCHAR(100);
    COMMENT ON COLUMN public.highlights.end_paragraph_id IS 'End-Absatz-ID bei Multi-Absatz-Markierungen (null wenn nur ein Absatz)';
  END IF;
END $$;

-- 2. QUOTES: end_paragraph_id hinzufügen
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'quotes' 
    AND column_name = 'end_paragraph_id'
  ) THEN
    ALTER TABLE public.quotes ADD COLUMN end_paragraph_id VARCHAR(100);
    COMMENT ON COLUMN public.quotes.end_paragraph_id IS 'End-Absatz-ID bei Multi-Absatz-Markierungen (null wenn nur ein Absatz)';
  END IF;
END $$;

-- 3. NOTES: end_paragraph_id hinzufügen
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'notes' 
    AND column_name = 'end_paragraph_id'
  ) THEN
    ALTER TABLE public.notes ADD COLUMN end_paragraph_id VARCHAR(100);
    COMMENT ON COLUMN public.notes.end_paragraph_id IS 'End-Absatz-ID bei Multi-Absatz-Markierungen (null wenn nur ein Absatz)';
  END IF;
END $$;

-- ============================================
-- FERTIG! 🎉
-- ============================================
-- Diese Migration fügt das end_paragraph_id Feld hinzu,
-- das bei Multi-Absatz-Markierungen verwendet wird.
-- Wenn die Markierung nur einen Absatz umfasst, bleibt dieses Feld NULL.

