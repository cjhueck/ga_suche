// TEMPORÄRE VERSION - Speichert OHNE lecture_url
// Nur für Testing wenn DB noch nicht aktualisiert wurde

// In members-context-menu.js ersetzen Sie diese Funktionen:

/**
 * Bookmark OHNE URL speichern (temporär)
 */
async function saveContextBookmark(text, gaNumber, lectureTitle, lectureUrl, paragraphId) {
  try {
    if (typeof supabaseClient === 'undefined' || !supabaseClient) {
      throw new Error('Supabase Client nicht initialisiert');
    }
    
    // OHNE lecture_url!
    const { data, error } = await supabaseClient
      .from('bookmarks')
      .insert({
        user_id: currentUser.id,
        ga_number: gaNumber,
        lecture_title: lectureTitle,
        // lecture_url: lectureUrl,  // AUSKOMMENTIERT!
        paragraph_id: paragraphId,
        paragraph_text: text,
        note: '',
        tags: []
      })
      .select();
    
    if (error) {
      console.error('Supabase Fehler:', error);
      throw new Error(error.message || 'Datenbankfehler');
    }
    
    console.log('✓ Bookmark gespeichert (ohne URL):', data);
    showContextNotification('✓ Bookmark gespeichert!', 'success');
    highlightContextSelection('#ccffcc');
    
    if (typeof membersPanelActive !== 'undefined' && membersPanelActive && currentMembersTab === 'bookmarks') {
      if (typeof loadMembersTab === 'function') {
        await loadMembersTab('bookmarks');
      }
    }
  } catch (error) {
    console.error('Fehler beim Speichern:', error);
    showContextNotification(`✗ Fehler: ${error.message}`, 'error');
  }
}

/**
 * Zitat OHNE URL speichern (temporär)
 */
async function saveContextQuote(text, gaNumber, lectureTitle, lectureUrl, contextBefore, contextAfter) {
  try {
    if (typeof supabaseClient === 'undefined' || !supabaseClient) {
      throw new Error('Supabase Client nicht initialisiert');
    }
    
    // OHNE lecture_url!
    const { data, error } = await supabaseClient
      .from('quotes')
      .insert({
        user_id: currentUser.id,
        quote_text: text,
        ga_reference: gaNumber,
        lecture_title: lectureTitle,
        // lecture_url: lectureUrl,  // AUSKOMMENTIERT!
        context_before: contextBefore,
        context_after: contextAfter,
        personal_note: '',
        tags: [],
        is_public: false
      })
      .select();
    
    if (error) {
      console.error('Supabase Fehler:', error);
      throw new Error(error.message || 'Datenbankfehler');
    }
    
    console.log('✓ Zitat gespeichert (ohne URL):', data);
    showContextNotification('✓ Zitat gespeichert!', 'success');
    highlightContextSelection('#ffffcc');
    
    if (typeof membersPanelActive !== 'undefined' && membersPanelActive && currentMembersTab === 'quotes') {
      if (typeof loadMembersTab === 'function') {
        await loadMembersTab('quotes');
      }
    }
  } catch (error) {
    console.error('Fehler beim Speichern:', error);
    showContextNotification(`✗ Fehler: ${error.message}`, 'error');
  }
}

