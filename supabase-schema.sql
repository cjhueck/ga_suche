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
  paragraph_id VARCHAR(100),
  paragraph_text TEXT,
  note TEXT,
  tags TEXT[] DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index für schnelle Abfragen
CREATE INDEX idx_bookmarks_user ON public.bookmarks(user_id);
CREATE INDEX idx_bookmarks_ga ON public.bookmarks(ga_number);

-- Row Level Security (RLS)
ALTER TABLE public.bookmarks ENABLE ROW LEVEL SECURITY;

-- Policy: Nutzer sehen nur ihre eigenen Bookmarks
CREATE POLICY "Users can view own bookmarks" 
  ON public.bookmarks FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own bookmarks" 
  ON public.bookmarks FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own bookmarks" 
  ON public.bookmarks FOR UPDATE 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own bookmarks" 
  ON public.bookmarks FOR DELETE 
  USING (auth.uid() = user_id);


-- ============================================
-- 2. QUOTES (Zitate) Tabelle
-- ============================================
CREATE TABLE IF NOT EXISTS public.quotes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  quote_text TEXT NOT NULL,
  ga_reference VARCHAR(50) NOT NULL,
  lecture_title TEXT,
  context_before TEXT,
  context_after TEXT,
  personal_note TEXT,
  tags TEXT[] DEFAULT '{}',
  is_public BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_quotes_user ON public.quotes(user_id);
CREATE INDEX idx_quotes_ga ON public.quotes(ga_reference);
CREATE INDEX idx_quotes_tags ON public.quotes USING GIN(tags);

ALTER TABLE public.quotes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own quotes" 
  ON public.quotes FOR SELECT 
  USING (auth.uid() = user_id OR is_public = true);

CREATE POLICY "Users can insert own quotes" 
  ON public.quotes FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own quotes" 
  ON public.quotes FOR UPDATE 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own quotes" 
  ON public.quotes FOR DELETE 
  USING (auth.uid() = user_id);


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

CREATE INDEX idx_notes_user ON public.notes(user_id);
CREATE INDEX idx_notes_ga_refs ON public.notes USING GIN(ga_references);
CREATE INDEX idx_notes_wiki_links ON public.notes USING GIN(wiki_links);
CREATE INDEX idx_notes_tags ON public.notes USING GIN(tags);

-- Volltext-Suche in Notizen
CREATE INDEX idx_notes_content_search ON public.notes USING GIN(to_tsvector('german', content));

ALTER TABLE public.notes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own notes" 
  ON public.notes FOR SELECT 
  USING (auth.uid() = user_id OR is_public = true);

CREATE POLICY "Users can insert own notes" 
  ON public.notes FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own notes" 
  ON public.notes FOR UPDATE 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own notes" 
  ON public.notes FOR DELETE 
  USING (auth.uid() = user_id);


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

CREATE INDEX idx_backlinks_user ON public.backlinks(user_id);
CREATE INDEX idx_backlinks_target ON public.backlinks(target_reference);

ALTER TABLE public.backlinks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own backlinks" 
  ON public.backlinks FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own backlinks" 
  ON public.backlinks FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own backlinks" 
  ON public.backlinks FOR DELETE 
  USING (auth.uid() = user_id);


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

CREATE INDEX idx_chat_room ON public.chat_messages(room, created_at DESC);

ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Chat ist für alle angemeldeten Mitglieder sichtbar
CREATE POLICY "Members can view messages" 
  ON public.chat_messages FOR SELECT 
  USING (auth.role() = 'authenticated');

CREATE POLICY "Members can insert messages" 
  ON public.chat_messages FOR INSERT 
  WITH CHECK (auth.uid() = user_id);


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

CREATE POLICY "Users can view all profiles" 
  ON public.user_profiles FOR SELECT 
  USING (true);

CREATE POLICY "Users can update own profile" 
  ON public.user_profiles FOR UPDATE 
  USING (auth.uid() = id);


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

-- Trigger für alle Tabellen
CREATE TRIGGER update_bookmarks_updated_at BEFORE UPDATE ON public.bookmarks
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_quotes_updated_at BEFORE UPDATE ON public.quotes
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_notes_updated_at BEFORE UPDATE ON public.notes
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.user_profiles
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


-- ============================================
-- 8. REALTIME für Chat aktivieren
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

