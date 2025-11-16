-- ============================================
-- SQL Script: Füge marker_color Spalte hinzu
-- ============================================
-- Führen Sie dieses Script im Supabase SQL Editor aus
-- (Settings → Database → SQL Editor → New Query)

-- 1. Füge marker_color zur bookmarks Tabelle hinzu
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema='public' 
        AND table_name='bookmarks' 
        AND column_name='marker_color'
    ) THEN
        ALTER TABLE public.bookmarks 
        ADD COLUMN marker_color VARCHAR(10) CHECK (marker_color IN ('red', 'yellow', 'green') OR marker_color IS NULL);
        
        RAISE NOTICE '✓ Spalte marker_color zur Tabelle bookmarks hinzugefügt';
    ELSE
        RAISE NOTICE 'ℹ Spalte marker_color existiert bereits in bookmarks';
    END IF;
END
$$;

-- 2. Füge marker_color zur quotes Tabelle hinzu
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema='public' 
        AND table_name='quotes' 
        AND column_name='marker_color'
    ) THEN
        ALTER TABLE public.quotes 
        ADD COLUMN marker_color VARCHAR(10) CHECK (marker_color IN ('red', 'yellow', 'green') OR marker_color IS NULL);
        
        RAISE NOTICE '✓ Spalte marker_color zur Tabelle quotes hinzugefügt';
    ELSE
        RAISE NOTICE 'ℹ Spalte marker_color existiert bereits in quotes';
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
AND column_name = 'marker_color'

UNION ALL

SELECT 
    'quotes' as tabelle,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'quotes'
AND column_name = 'marker_color';

