-- ============================================
-- GA-Suche: Supabase-Warnungen beheben
-- ============================================
-- 1. Mutable search_path bei update_analytics_updated_at
-- 2. RLS-Performance: auth.uid()/auth.role() → (select auth.uid())/(select auth.role())
-- Dieses Script im Supabase SQL Editor ausführen.

-- ============================================
-- 1. Fix: update_analytics_updated_at – search_path setzen
-- ============================================
CREATE OR REPLACE FUNCTION public.update_analytics_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql
SET search_path = '';

-- ============================================
-- 2. Fix: RLS Policies – (select auth.uid()) statt auth.uid()
-- ============================================

-- === bookmarks ===
DROP POLICY IF EXISTS "Users can view own bookmarks" ON public.bookmarks;
CREATE POLICY "Users can view own bookmarks"
  ON public.bookmarks FOR SELECT
  USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can insert own bookmarks" ON public.bookmarks;
CREATE POLICY "Users can insert own bookmarks"
  ON public.bookmarks FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can update own bookmarks" ON public.bookmarks;
CREATE POLICY "Users can update own bookmarks"
  ON public.bookmarks FOR UPDATE
  USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can delete own bookmarks" ON public.bookmarks;
CREATE POLICY "Users can delete own bookmarks"
  ON public.bookmarks FOR DELETE
  USING ((select auth.uid()) = user_id);

-- === quotes ===
DROP POLICY IF EXISTS "Users can view own quotes" ON public.quotes;
CREATE POLICY "Users can view own quotes"
  ON public.quotes FOR SELECT
  USING ((select auth.uid()) = user_id OR is_public = true);

DROP POLICY IF EXISTS "Users can insert own quotes" ON public.quotes;
CREATE POLICY "Users can insert own quotes"
  ON public.quotes FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can update own quotes" ON public.quotes;
CREATE POLICY "Users can update own quotes"
  ON public.quotes FOR UPDATE
  USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can delete own quotes" ON public.quotes;
CREATE POLICY "Users can delete own quotes"
  ON public.quotes FOR DELETE
  USING ((select auth.uid()) = user_id);

-- === notes ===
DROP POLICY IF EXISTS "Users can view own notes" ON public.notes;
CREATE POLICY "Users can view own notes"
  ON public.notes FOR SELECT
  USING ((select auth.uid()) = user_id OR is_public = true);

DROP POLICY IF EXISTS "Users can insert own notes" ON public.notes;
CREATE POLICY "Users can insert own notes"
  ON public.notes FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can update own notes" ON public.notes;
CREATE POLICY "Users can update own notes"
  ON public.notes FOR UPDATE
  USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can delete own notes" ON public.notes;
CREATE POLICY "Users can delete own notes"
  ON public.notes FOR DELETE
  USING ((select auth.uid()) = user_id);

-- === backlinks ===
DROP POLICY IF EXISTS "Users can view own backlinks" ON public.backlinks;
CREATE POLICY "Users can view own backlinks"
  ON public.backlinks FOR SELECT
  USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can insert own backlinks" ON public.backlinks;
CREATE POLICY "Users can insert own backlinks"
  ON public.backlinks FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can delete own backlinks" ON public.backlinks;
CREATE POLICY "Users can delete own backlinks"
  ON public.backlinks FOR DELETE
  USING ((select auth.uid()) = user_id);

-- === chat_messages ===
DROP POLICY IF EXISTS "Members can view messages" ON public.chat_messages;
CREATE POLICY "Members can view messages"
  ON public.chat_messages FOR SELECT
  USING ((select auth.role()) = 'authenticated');

DROP POLICY IF EXISTS "Members can insert messages" ON public.chat_messages;
CREATE POLICY "Members can insert messages"
  ON public.chat_messages FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

-- === user_profiles ===
DROP POLICY IF EXISTS "Users can update own profile" ON public.user_profiles;
CREATE POLICY "Users can update own profile"
  ON public.user_profiles FOR UPDATE
  USING ((select auth.uid()) = id);

-- === highlights ===
DROP POLICY IF EXISTS "Users can view own highlights" ON public.highlights;
CREATE POLICY "Users can view own highlights"
  ON public.highlights FOR SELECT
  USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can insert own highlights" ON public.highlights;
CREATE POLICY "Users can insert own highlights"
  ON public.highlights FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can update own highlights" ON public.highlights;
CREATE POLICY "Users can update own highlights"
  ON public.highlights FOR UPDATE
  USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can delete own highlights" ON public.highlights;
CREATE POLICY "Users can delete own highlights"
  ON public.highlights FOR DELETE
  USING ((select auth.uid()) = user_id);

-- === saved_thematic_searches ===
DROP POLICY IF EXISTS "Users can view own saved searches" ON public.saved_thematic_searches;
CREATE POLICY "Users can view own saved searches"
  ON public.saved_thematic_searches FOR SELECT
  USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can insert own saved searches" ON public.saved_thematic_searches;
CREATE POLICY "Users can insert own saved searches"
  ON public.saved_thematic_searches FOR INSERT
  WITH CHECK ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can update own saved searches" ON public.saved_thematic_searches;
CREATE POLICY "Users can update own saved searches"
  ON public.saved_thematic_searches FOR UPDATE
  USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can delete own saved searches" ON public.saved_thematic_searches;
CREATE POLICY "Users can delete own saved searches"
  ON public.saved_thematic_searches FOR DELETE
  USING ((select auth.uid()) = user_id);
