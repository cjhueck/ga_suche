-- ============================================
-- GA-Suche Mitgliederbereich - Schema Update
-- Fügt lecture_url Spalten zu bestehenden Tabellen hinzu
-- ============================================
-- Dieses SQL-Script in Supabase SQL Editor ausführen,
-- wenn die Tabellen bereits existieren

-- ============================================
-- 1. BOOKMARKS Tabelle: lecture_url Spalte hinzufügen
-- ============================================
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'bookmarks' 
    AND column_name = 'lecture_url'
  ) THEN
    ALTER TABLE public.bookmarks ADD COLUMN lecture_url TEXT;
    RAISE NOTICE 'Spalte lecture_url zu bookmarks Tabelle hinzugefügt';
  ELSE
    RAISE NOTICE 'Spalte lecture_url existiert bereits in bookmarks Tabelle';
  END IF;
END $$;


-- ============================================
-- 2. QUOTES Tabelle: lecture_url Spalte hinzufügen
-- ============================================
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'quotes' 
    AND column_name = 'lecture_url'
  ) THEN
    ALTER TABLE public.quotes ADD COLUMN lecture_url TEXT;
    RAISE NOTICE 'Spalte lecture_url zu quotes Tabelle hinzugefügt';
  ELSE
    RAISE NOTICE 'Spalte lecture_url existiert bereits in quotes Tabelle';
  END IF;
END $$;


-- ============================================
-- FERTIG! ✓
-- ============================================
-- Die lecture_url Spalten wurden erfolgreich hinzugefügt.
-- Bestehende Datensätze haben NULL als Wert für lecture_url.
-- Neue Bookmarks und Zitate werden automatisch mit der URL gespeichert.

