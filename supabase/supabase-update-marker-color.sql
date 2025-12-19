-- ============================================
-- SQL Script: Ändere marker_color Constraint
-- ============================================
-- Führen Sie dieses Script im Supabase SQL Editor aus
-- Erlaubt: 'blue', 'red', 'yellow' (statt 'red', 'yellow', 'green')

-- 1. Entferne alte Constraint und füge neue hinzu für quotes
ALTER TABLE public.quotes DROP CONSTRAINT IF EXISTS quotes_marker_color_check;
ALTER TABLE public.quotes ADD CONSTRAINT quotes_marker_color_check 
  CHECK (marker_color IN ('blue', 'red', 'yellow') OR marker_color IS NULL);

-- 2. Entferne alte Constraint und füge neue hinzu für bookmarks
ALTER TABLE public.bookmarks DROP CONSTRAINT IF EXISTS bookmarks_marker_color_check;
ALTER TABLE public.bookmarks ADD CONSTRAINT bookmarks_marker_color_check 
  CHECK (marker_color IN ('blue', 'red', 'yellow') OR marker_color IS NULL);

-- 3. Konvertiere existierende 'green' Werte zu NULL (falls vorhanden)
UPDATE public.quotes SET marker_color = NULL WHERE marker_color = 'green';
UPDATE public.bookmarks SET marker_color = NULL WHERE marker_color = 'green';

-- 4. Prüfe Ergebnis
SELECT 'Constraints erfolgreich aktualisiert: blue, red, yellow sind jetzt erlaubt' as status;

