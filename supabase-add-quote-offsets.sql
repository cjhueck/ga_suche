-- ============================================
-- Migration: Neue Spalten für exakte Zitat-Positionierung
-- Entfernt Abhängigkeit von context_before/context_after
-- ============================================
-- Dieses SQL-Script in Supabase SQL Editor ausführen
-- (Settings → Database → SQL Editor → New Query)
--
-- Diese Migration:
-- 1. Fügt paragraph_text, text_start_offset, text_end_offset hinzu (für exakte Positionierung)
-- 2. Macht context_before und context_after optional (werden nicht mehr benötigt)

-- Füge paragraph_text Spalte zu quotes Tabelle hinzu, falls sie nicht existiert
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'quotes' 
    AND column_name = 'paragraph_text'
  ) THEN
    ALTER TABLE public.quotes ADD COLUMN paragraph_text TEXT;
    COMMENT ON COLUMN public.quotes.paragraph_text IS 'Vollständiger Text des Absatzes, aus dem das Zitat stammt';
    RAISE NOTICE '✓ Spalte paragraph_text zur Tabelle quotes hinzugefügt';
  ELSE
    RAISE NOTICE 'ℹ Spalte paragraph_text existiert bereits in quotes';
  END IF;
END $$;

-- Füge text_start_offset Spalte zu quotes Tabelle hinzu, falls sie nicht existiert
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'quotes' 
    AND column_name = 'text_start_offset'
  ) THEN
    ALTER TABLE public.quotes ADD COLUMN text_start_offset INTEGER;
    COMMENT ON COLUMN public.quotes.text_start_offset IS 'Position im Absatz wo das Zitat beginnt (Character-Offset)';
    RAISE NOTICE '✓ Spalte text_start_offset zur Tabelle quotes hinzugefügt';
  ELSE
    RAISE NOTICE 'ℹ Spalte text_start_offset existiert bereits in quotes';
  END IF;
END $$;

-- Füge text_end_offset Spalte zu quotes Tabelle hinzu, falls sie nicht existiert
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'quotes' 
    AND column_name = 'text_end_offset'
  ) THEN
    ALTER TABLE public.quotes ADD COLUMN text_end_offset INTEGER;
    COMMENT ON COLUMN public.quotes.text_end_offset IS 'Position im Absatz wo das Zitat endet (Character-Offset)';
    RAISE NOTICE '✓ Spalte text_end_offset zur Tabelle quotes hinzugefügt';
  ELSE
    RAISE NOTICE 'ℹ Spalte text_end_offset existiert bereits in quotes';
  END IF;
END $$;

-- Prüfe Ergebnis
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'quotes'
AND column_name IN ('paragraph_text', 'text_start_offset', 'text_end_offset')
ORDER BY column_name;

-- ============================================
-- 4. HINWEIS: context_before und context_after sind jetzt deprecated
-- ============================================
-- Diese Spalten werden NICHT gelöscht (für Rückwärtskompatibilität),
-- aber neue Zitate verwenden sie nicht mehr.
-- 
-- Falls Sie die Spalten komplett entfernen möchten (optional):
-- ALTER TABLE public.quotes DROP COLUMN IF EXISTS context_before;
-- ALTER TABLE public.quotes DROP COLUMN IF EXISTS context_after;

-- ============================================
-- FERTIG! ✓
-- ============================================
-- Die neuen Spalten paragraph_text, text_start_offset und text_end_offset wurden erfolgreich hinzugefügt.
-- 
-- WICHTIG:
-- - Neue Zitate verwenden die neuen Spalten für exakte Positionierung
-- - Bestehende Zitate haben NULL als Wert (funktionieren weiterhin, aber ohne exakte Markierung)
-- - context_before und context_after sind deprecated, werden aber nicht gelöscht (für Rückwärtskompatibilität)

