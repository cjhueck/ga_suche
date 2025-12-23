-- ============================================
-- SQL Script: Füge 'gray' als erlaubte Farbe hinzu
-- ============================================
-- Führen Sie dieses Script im Supabase SQL Editor aus
-- (Settings → Database → SQL Editor → New Query)
--
-- Graue Markierungen werden in der Datenbank gespeichert,
-- aber nicht im Members Panel angezeigt.

-- 1. Aktualisiere Constraint für quotes Tabelle
ALTER TABLE public.quotes DROP CONSTRAINT IF EXISTS quotes_marker_color_check;
ALTER TABLE public.quotes ADD CONSTRAINT quotes_marker_color_check 
  CHECK (marker_color IN ('blue', 'red', 'yellow', 'gray') OR marker_color IS NULL);

-- 2. Aktualisiere Constraint für bookmarks Tabelle
ALTER TABLE public.bookmarks DROP CONSTRAINT IF EXISTS bookmarks_marker_color_check;
ALTER TABLE public.bookmarks ADD CONSTRAINT bookmarks_marker_color_check 
  CHECK (marker_color IN ('blue', 'red', 'yellow', 'gray') OR marker_color IS NULL);

-- 3. Aktualisiere Constraint für highlights Tabelle (falls vorhanden)
-- Highlights verwendet 'color' statt 'marker_color'
DO $$
BEGIN
  -- Prüfe ob Constraint existiert
  IF EXISTS (
    SELECT 1 FROM information_schema.table_constraints 
    WHERE constraint_name = 'highlights_color_check' 
    AND table_name = 'highlights'
  ) THEN
    ALTER TABLE public.highlights DROP CONSTRAINT highlights_color_check;
    ALTER TABLE public.highlights ADD CONSTRAINT highlights_color_check 
      CHECK (color IN ('blue', 'red', 'yellow', 'gray') OR color IS NULL);
    RAISE NOTICE '✓ Constraint highlights_color_check aktualisiert';
  ELSE
    RAISE NOTICE 'ℹ Kein color Constraint für highlights gefunden (kein Update nötig)';
  END IF;
END
$$;

-- 4. Prüfe Ergebnis
SELECT 'Constraints erfolgreich aktualisiert: gray ist jetzt erlaubt' as status;

-- Zeige aktuelle Constraints
SELECT 
  tc.table_name,
  tc.constraint_name,
  cc.check_clause
FROM information_schema.table_constraints tc
JOIN information_schema.check_constraints cc 
  ON tc.constraint_name = cc.constraint_name
WHERE tc.table_name IN ('quotes', 'bookmarks', 'highlights')
  AND tc.constraint_type = 'CHECK'
  AND (cc.check_clause LIKE '%color%' OR cc.check_clause LIKE '%marker_color%');

