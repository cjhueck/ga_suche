-- ============================================
-- SQL Script: Füge lecture_url Spalte hinzu
-- ============================================
-- Führen Sie dieses Script im Supabase SQL Editor aus
-- (Settings → Database → SQL Editor → New Query)

-- 1. Füge lecture_url zur bookmarks Tabelle hinzu
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema='public' 
        AND table_name='bookmarks' 
        AND column_name='lecture_url'
    ) THEN
        ALTER TABLE public.bookmarks 
        ADD COLUMN lecture_url TEXT;
        
        RAISE NOTICE '✓ Spalte lecture_url zur Tabelle bookmarks hinzugefügt';
    ELSE
        RAISE NOTICE 'ℹ Spalte lecture_url existiert bereits in bookmarks';
    END IF;
END
$$;

-- 2. Füge lecture_url zur quotes Tabelle hinzu
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema='public' 
        AND table_name='quotes' 
        AND column_name='lecture_url'
    ) THEN
        ALTER TABLE public.quotes 
        ADD COLUMN lecture_url TEXT;
        
        RAISE NOTICE '✓ Spalte lecture_url zur Tabelle quotes hinzugefügt';
    ELSE
        RAISE NOTICE 'ℹ Spalte lecture_url existiert bereits in quotes';
    END IF;
END
$$;

-- 3. Prüfe Ergebnis
SELECT 
    'bookmarks' as tabelle,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'bookmarks'
AND column_name = 'lecture_url'

UNION ALL

SELECT 
    'quotes' as tabelle,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'quotes'
AND column_name = 'lecture_url';

