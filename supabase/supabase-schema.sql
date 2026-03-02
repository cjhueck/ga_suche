-- ============================================
-- GA-Suche Mitgliederbereich - Supabase Schema
-- ============================================
-- Dieses SQL-Script in Supabase SQL Editor ausführen

-- ============================================
-- 1. BOOKMARKS Tabelle
-- ============================================
CREATE TABLE IF NOT EXISTS public.bookmarks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  ga_number VARCHAR(50) NOT NULL,
  lecture_title TEXT,
  lecture_url TEXT,
  paragraph_id VARCHAR(100),
  paragraph_text TEXT,
  note TEXT,
  tags TEXT[] DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index für schnelle Abfragen (werden nur erstellt, falls nicht vorhanden)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'bookmarks' 
    AND indexname = 'idx_bookmarks_user'
  ) THEN
    CREATE INDEX idx_bookmarks_user ON public.bookmarks(user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'bookmarks' 
    AND indexname = 'idx_bookmarks_ga'
  ) THEN
    CREATE INDEX idx_bookmarks_ga ON public.bookmarks(ga_number);
  END IF;
END $$;

-- Row Level Security (RLS)
ALTER TABLE public.bookmarks ENABLE ROW LEVEL SECURITY;

-- Policies für Bookmarks (werden nur erstellt, falls nicht vorhanden)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'bookmarks' 
    AND policyname = 'Users can view own bookmarks'
  ) THEN
    CREATE POLICY "Users can view own bookmarks" 
      ON public.bookmarks FOR SELECT 
      USING ((select auth.uid()) = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'bookmarks' 
    AND policyname = 'Users can insert own bookmarks'
  ) THEN
    CREATE POLICY "Users can insert own bookmarks" 
      ON public.bookmarks FOR INSERT 
      WITH CHECK ((select auth.uid()) = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'bookmarks' 
    AND policyname = 'Users can update own bookmarks'
  ) THEN
    CREATE POLICY "Users can update own bookmarks" 
      ON public.bookmarks FOR UPDATE 
      USING ((select auth.uid()) = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'bookmarks' 
    AND policyname = 'Users can delete own bookmarks'
  ) THEN
    CREATE POLICY "Users can delete own bookmarks" 
      ON public.bookmarks FOR DELETE 
      USING ((select auth.uid()) = user_id);
  END IF;
END $$;


-- ============================================
-- 2. QUOTES (Zitate) Tabelle
-- ============================================
CREATE TABLE IF NOT EXISTS public.quotes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  quote_text TEXT NOT NULL,
  ga_reference VARCHAR(50) NOT NULL,
  lecture_title TEXT,
  lecture_url TEXT,
  paragraph_id VARCHAR(100),
  paragraph_text TEXT,
  context_before TEXT,
  context_after TEXT,
  text_start_offset INTEGER,  -- Position im Absatz wo das Zitat beginnt
  text_end_offset INTEGER,     -- Position im Absatz wo das Zitat endet
  personal_note TEXT,
  tags TEXT[] DEFAULT '{}',
  is_public BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indizes für Quotes (werden nur erstellt, falls nicht vorhanden)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'quotes' 
    AND indexname = 'idx_quotes_user'
  ) THEN
    CREATE INDEX idx_quotes_user ON public.quotes(user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'quotes' 
    AND indexname = 'idx_quotes_ga'
  ) THEN
    CREATE INDEX idx_quotes_ga ON public.quotes(ga_reference);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'quotes' 
    AND indexname = 'idx_quotes_tags'
  ) THEN
    CREATE INDEX idx_quotes_tags ON public.quotes USING GIN(tags);
  END IF;
END $$;

ALTER TABLE public.quotes ENABLE ROW LEVEL SECURITY;

-- Policies für Quotes (werden nur erstellt, falls nicht vorhanden)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'quotes' 
    AND policyname = 'Users can view own quotes'
  ) THEN
    CREATE POLICY "Users can view own quotes" 
      ON public.quotes FOR SELECT 
      USING (auth.uid() = user_id OR is_public = true);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'quotes' 
    AND policyname = 'Users can insert own quotes'
  ) THEN
    CREATE POLICY "Users can insert own quotes" 
      ON public.quotes FOR INSERT 
      WITH CHECK ((select auth.uid()) = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'quotes' 
    AND policyname = 'Users can update own quotes'
  ) THEN
    CREATE POLICY "Users can update own quotes" 
      ON public.quotes FOR UPDATE 
      USING ((select auth.uid()) = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'quotes' 
    AND policyname = 'Users can delete own quotes'
  ) THEN
    CREATE POLICY "Users can delete own quotes" 
      ON public.quotes FOR DELETE 
      USING ((select auth.uid()) = user_id);
  END IF;
END $$;


-- ============================================
-- 3. NOTES (Notizen) Tabelle - mit Obsidian-Features
-- ============================================
CREATE TABLE IF NOT EXISTS public.notes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  title VARCHAR(500),
  content TEXT NOT NULL,
  ga_references TEXT[] DEFAULT '{}',  -- ['GA110/5', 'GA107/3']
  wiki_links TEXT[] DEFAULT '{}',     -- Alle [[Links]] im Text
  tags TEXT[] DEFAULT '{}',           -- #Karma #Ätherleib
  is_public BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indizes für Notes (werden nur erstellt, falls nicht vorhanden)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'notes' 
    AND indexname = 'idx_notes_user'
  ) THEN
    CREATE INDEX idx_notes_user ON public.notes(user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'notes' 
    AND indexname = 'idx_notes_ga_refs'
  ) THEN
    CREATE INDEX idx_notes_ga_refs ON public.notes USING GIN(ga_references);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'notes' 
    AND indexname = 'idx_notes_wiki_links'
  ) THEN
    CREATE INDEX idx_notes_wiki_links ON public.notes USING GIN(wiki_links);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'notes' 
    AND indexname = 'idx_notes_tags'
  ) THEN
    CREATE INDEX idx_notes_tags ON public.notes USING GIN(tags);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'notes' 
    AND indexname = 'idx_notes_content_search'
  ) THEN
    CREATE INDEX idx_notes_content_search ON public.notes USING GIN(to_tsvector('german', content));
  END IF;
END $$;

ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;

-- Policies für Notes (werden nur erstellt, falls nicht vorhanden)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'notes' 
    AND policyname = 'Users can view own notes'
  ) THEN
    CREATE POLICY "Users can view own notes" 
      ON public.notes FOR SELECT 
      USING (auth.uid() = user_id OR is_public = true);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'notes' 
    AND policyname = 'Users can insert own notes'
  ) THEN
    CREATE POLICY "Users can insert own notes" 
      ON public.notes FOR INSERT 
      WITH CHECK ((select auth.uid()) = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'notes' 
    AND policyname = 'Users can update own notes'
  ) THEN
    CREATE POLICY "Users can update own notes" 
      ON public.notes FOR UPDATE 
      USING ((select auth.uid()) = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'notes' 
    AND policyname = 'Users can delete own notes'
  ) THEN
    CREATE POLICY "Users can delete own notes" 
      ON public.notes FOR DELETE 
      USING ((select auth.uid()) = user_id);
  END IF;
END $$;


-- ============================================
-- 4. BACKLINKS Tabelle - für Obsidian Graph
-- ============================================
CREATE TABLE IF NOT EXISTS public.backlinks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  source_type VARCHAR(20) NOT NULL,  -- 'note', 'quote', 'bookmark'
  source_id UUID NOT NULL,
  target_reference VARCHAR(200) NOT NULL,  -- 'GA110/5' oder Note-Titel
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indizes für Backlinks (werden nur erstellt, falls nicht vorhanden)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'backlinks' 
    AND indexname = 'idx_backlinks_user'
  ) THEN
    CREATE INDEX idx_backlinks_user ON public.backlinks(user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'backlinks' 
    AND indexname = 'idx_backlinks_target'
  ) THEN
    CREATE INDEX idx_backlinks_target ON public.backlinks(target_reference);
  END IF;
END $$;

ALTER TABLE public.backlinks ENABLE ROW LEVEL SECURITY;

-- Policies für Backlinks (werden nur erstellt, falls nicht vorhanden)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'backlinks' 
    AND policyname = 'Users can view own backlinks'
  ) THEN
    CREATE POLICY "Users can view own backlinks" 
      ON public.backlinks FOR SELECT 
      USING ((select auth.uid()) = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'backlinks' 
    AND policyname = 'Users can insert own backlinks'
  ) THEN
    CREATE POLICY "Users can insert own backlinks" 
      ON public.backlinks FOR INSERT 
      WITH CHECK ((select auth.uid()) = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'backlinks' 
    AND policyname = 'Users can delete own backlinks'
  ) THEN
    CREATE POLICY "Users can delete own backlinks" 
      ON public.backlinks FOR DELETE 
      USING ((select auth.uid()) = user_id);
  END IF;
END $$;


-- ============================================
-- 5. CHAT_MESSAGES Tabelle
-- ============================================
CREATE TABLE IF NOT EXISTS public.chat_messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  user_name VARCHAR(100),
  message TEXT NOT NULL,
  room VARCHAR(100) DEFAULT 'general',  -- 'general', 'GA110', etc.
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index für Chat (wird nur erstellt, falls nicht vorhanden)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'chat_messages' 
    AND indexname = 'idx_chat_room'
  ) THEN
    CREATE INDEX idx_chat_room ON public.chat_messages(room, created_at DESC);
  END IF;
END $$;

ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Policies für Chat (werden nur erstellt, falls nicht vorhanden)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'chat_messages' 
    AND policyname = 'Members can view messages'
  ) THEN
    CREATE POLICY "Members can view messages" 
      ON public.chat_messages FOR SELECT 
      USING ((select auth.role()) = 'authenticated');
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'chat_messages' 
    AND policyname = 'Members can insert messages'
  ) THEN
    CREATE POLICY "Members can insert messages" 
      ON public.chat_messages FOR INSERT 
      WITH CHECK ((select auth.uid()) = user_id);
  END IF;
END $$;


-- ============================================
-- 6. USER_PROFILES Tabelle - Erweiterte Nutzer-Info
-- ============================================
CREATE TABLE IF NOT EXISTS public.user_profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  display_name VARCHAR(100),
  bio TEXT,
  avatar_url TEXT,
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Policies für User Profiles (werden nur erstellt, falls nicht vorhanden)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'user_profiles' 
    AND policyname = 'Users can view all profiles'
  ) THEN
    CREATE POLICY "Users can view all profiles" 
      ON public.user_profiles FOR SELECT 
      USING (true);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'user_profiles' 
    AND policyname = 'Users can update own profile'
  ) THEN
    CREATE POLICY "Users can update own profile" 
      ON public.user_profiles FOR UPDATE 
      USING ((select auth.uid()) = id);
  END IF;
END $$;


-- ============================================
-- 7. FUNCTIONS - Helper Functions
-- ============================================

-- Automatisch Profil erstellen bei Registrierung
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_profiles (id, display_name)
  VALUES (NEW.id, NEW.email);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger für neue Nutzer
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- Automatisch updated_at aktualisieren
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger für alle Tabellen (werden nur erstellt, falls nicht vorhanden)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger 
    WHERE tgname = 'update_bookmarks_updated_at'
  ) THEN
    CREATE TRIGGER update_bookmarks_updated_at BEFORE UPDATE ON public.bookmarks
      FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger 
    WHERE tgname = 'update_quotes_updated_at'
  ) THEN
    CREATE TRIGGER update_quotes_updated_at BEFORE UPDATE ON public.quotes
      FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger 
    WHERE tgname = 'update_notes_updated_at'
  ) THEN
    CREATE TRIGGER update_notes_updated_at BEFORE UPDATE ON public.notes
      FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger 
    WHERE tgname = 'update_profiles_updated_at'
  ) THEN
    CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.user_profiles
      FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
  END IF;
END $$;


-- ============================================
-- 8. HIGHLIGHTS (Unterstreichungen) Tabelle
-- ============================================
CREATE TABLE IF NOT EXISTS public.highlights (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  ga_number VARCHAR(50) NOT NULL,
  lecture_title TEXT,
  lecture_url TEXT,
  paragraph_id VARCHAR(100),
  paragraph_text TEXT,
  text_start_offset INTEGER,  -- Position im Absatz wo die Unterstreichung beginnt
  text_end_offset INTEGER,     -- Position im Absatz wo die Unterstreichung endet
  personal_note TEXT,
  tags TEXT[] DEFAULT '{}',
  color VARCHAR(20) DEFAULT 'blue',  -- 'blue', 'red', 'yellow'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index für schnelle Abfragen (werden in Migration erstellt, falls nicht vorhanden)

-- Row Level Security (RLS)
ALTER TABLE public.highlights ENABLE ROW LEVEL SECURITY;

-- Policies werden im Migrationsskript erstellt, falls nicht vorhanden

-- Trigger für updated_at (wird im Migrationsskript erstellt, falls nicht vorhanden)


-- ============================================
-- MIGRATION: Tags und Notizen für Highlights hinzufügen
-- ============================================
-- Falls die Tabelle bereits existiert, füge die fehlenden Spalten, Indizes, Policies und Trigger hinzu
DO $$ 
BEGIN
  -- Füge personal_note Spalte hinzu, falls sie nicht existiert
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'highlights' 
    AND column_name = 'personal_note'
  ) THEN
    ALTER TABLE public.highlights ADD COLUMN personal_note TEXT;
  END IF;

  -- Füge tags Spalte hinzu, falls sie nicht existiert
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'highlights' 
    AND column_name = 'tags'
  ) THEN
    ALTER TABLE public.highlights ADD COLUMN tags TEXT[] DEFAULT '{}';
  END IF;

  -- Füge color Spalte hinzu, falls sie nicht existiert
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'highlights' 
    AND column_name = 'color'
  ) THEN
    ALTER TABLE public.highlights ADD COLUMN color VARCHAR(20) DEFAULT 'blue';
  END IF;

  -- Erstelle Indizes, falls sie nicht existieren
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'highlights' 
    AND indexname = 'idx_highlights_user'
  ) THEN
    CREATE INDEX idx_highlights_user ON public.highlights(user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'highlights' 
    AND indexname = 'idx_highlights_ga'
  ) THEN
    CREATE INDEX idx_highlights_ga ON public.highlights(ga_number);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'highlights' 
    AND indexname = 'idx_highlights_paragraph'
  ) THEN
    CREATE INDEX idx_highlights_paragraph ON public.highlights(ga_number, paragraph_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename = 'highlights' 
    AND indexname = 'idx_highlights_tags'
  ) THEN
    CREATE INDEX idx_highlights_tags ON public.highlights USING GIN(tags);
  END IF;

  -- Erstelle Policies, falls sie nicht existieren
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'highlights' 
    AND policyname = 'Users can view own highlights'
  ) THEN
    CREATE POLICY "Users can view own highlights" 
      ON public.highlights FOR SELECT 
      USING ((select auth.uid()) = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'highlights' 
    AND policyname = 'Users can insert own highlights'
  ) THEN
    CREATE POLICY "Users can insert own highlights" 
      ON public.highlights FOR INSERT 
      WITH CHECK ((select auth.uid()) = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'highlights' 
    AND policyname = 'Users can update own highlights'
  ) THEN
    CREATE POLICY "Users can update own highlights" 
      ON public.highlights FOR UPDATE 
      USING ((select auth.uid()) = user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'highlights' 
    AND policyname = 'Users can delete own highlights'
  ) THEN
    CREATE POLICY "Users can delete own highlights" 
      ON public.highlights FOR DELETE 
      USING (auth.uid() = user_id);
  END IF;

  -- Erstelle Trigger, falls er nicht existiert
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger 
    WHERE tgname = 'update_highlights_updated_at'
  ) THEN
    CREATE TRIGGER update_highlights_updated_at BEFORE UPDATE ON public.highlights
      FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
  END IF;
END $$;


-- ============================================
-- 9. REALTIME für Chat aktivieren
-- ============================================
-- In Supabase Dashboard: Realtime für chat_messages aktivieren


-- ============================================
-- FERTIG! 🎉
-- ============================================
-- Nächste Schritte:
-- 1. In Supabase Dashboard einloggen
-- 2. Neues Projekt erstellen (Frankfurt Region wählen!)
-- 3. SQL Editor öffnen
-- 4. Dieses Script ausführen
-- 5. Email Auth aktivieren in Authentication Settings
-- 6. API Keys kopieren für Frontend

