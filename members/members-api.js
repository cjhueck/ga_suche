// ============================================
// GA-Suche Mitgliederbereich - API Functions
// ============================================

import { supabase, getCurrentUser } from './members-auth.js';


// ============================================
// BOOKMARKS
// ============================================

/**
 * Bookmark erstellen
 */
export async function createBookmark(gaNumber, lectureTitle, paragraphId, paragraphText, note = '', tags = [], lectureUrl = '') {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    const { data, error } = await supabase
      .from('bookmarks')
      .insert({
        user_id: user.id,
        ga_number: gaNumber,
        paragraph_id: paragraphId,
        paragraph_text: paragraphText,
        note: note,
        tags: tags
      })
      .select()
      .single();

    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Erstellen des Bookmarks:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Alle Bookmarks des Users abrufen
 */
export async function getBookmarks(gaNumber = null) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    let query = supabase
      .from('bookmarks')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    if (gaNumber) {
      query = query.eq('ga_number', gaNumber);
    }

    const { data, error } = await query;
    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Abrufen der Bookmarks:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Bookmark löschen
 */
export async function deleteBookmark(bookmarkId) {
  try {
    const { error } = await supabase
      .from('bookmarks')
      .delete()
      .eq('id', bookmarkId);

    if (error) throw error;

    return { success: true };
  } catch (error) {
    console.error('Fehler beim Löschen des Bookmarks:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Bookmark aktualisieren
 */
export async function updateBookmark(bookmarkId, updates) {
  try {
    // Ensure marker_color is valid or null (blue/red/yellow erlaubt)
    if (updates.marker_color !== undefined) {
      if (updates.marker_color !== null && 
          updates.marker_color !== 'blue' && 
          updates.marker_color !== 'red' && 
          updates.marker_color !== 'yellow') {
        updates.marker_color = null;
      }
    }
    
    const { data, error } = await supabase
      .from('bookmarks')
      .update(updates)
      .eq('id', bookmarkId)
      .select()
      .single();

    if (error) {
      console.error('Supabase Fehler beim Aktualisieren des Bookmarks:', error);
      // Check if marker_color column is missing
      if (error.message && error.message.includes('marker_color')) {
        throw new Error('Die marker_color Spalte fehlt in der Datenbank. Bitte führen Sie das SQL-Script supabase-add-marker-color.sql im Supabase SQL Editor aus.');
      }
      throw error;
    }

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Aktualisieren des Bookmarks:', error);
    return { success: false, error: error.message || 'Unbekannter Fehler' };
  }
}


// ============================================
// QUOTES (Zitate)
// ============================================

/**
 * Ermittelt das Datum eines Vortrags aus der lectureId
 * Diese Funktion kann optional verwendet werden, wenn currentLectureData verfügbar ist
 */
function getLectureDateFromId(lectureId) {
  if (!lectureId) return null;
  
  // Versuche aus currentLectureData zu holen (falls verfügbar)
  if (typeof currentLectureData !== 'undefined' && currentLectureData && currentLectureData.ID === lectureId) {
    let date = currentLectureData.date || currentLectureData.dateString || '';
    
    if (date) {
      // Wenn bereits im ISO-Format (YYYY-MM-DD), direkt zurückgeben
      if (date.match(/^\d{4}-\d{2}-\d{2}$/)) {
        return date;
      }
      
      // Versuche aus deutschem Format zu konvertieren (z.B. "21. Oktober 1908")
      const dateMatch = date.match(/(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*(\d{4})/i);
      if (dateMatch) {
        const day = dateMatch[1].padStart(2, '0');
        const monthNames = {
          'januar': '01', 'februar': '02', 'märz': '03', 'april': '04',
          'mai': '05', 'juni': '06', 'juli': '07', 'august': '08',
          'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12'
        };
        const month = monthNames[dateMatch[2].toLowerCase()];
        const year = dateMatch[3];
        if (month) {
          return `${year}-${month}-${day}`;
        }
      }
    }
    
    // Fallback: Versuche aus fileName oder location zu extrahieren
    if (!date && (currentLectureData.fileName || currentLectureData.location)) {
      const locationMatch = (currentLectureData.location || currentLectureData.fileName || '').match(/(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*(\d{4})/i);
      if (locationMatch) {
        const day = locationMatch[1].padStart(2, '0');
        const monthNames = {
          'januar': '01', 'februar': '02', 'märz': '03', 'april': '04',
          'mai': '05', 'juni': '06', 'juli': '07', 'august': '08',
          'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12'
        };
        const month = monthNames[locationMatch[2].toLowerCase()];
        const year = locationMatch[3];
        if (month) {
          return `${year}-${month}-${day}`;
        }
      }
    }
  }
  
  return null;
}

/**
 * Zitat erstellen
 */
export async function createQuote(quoteText, gaReference, lectureTitle, contextBefore = '', contextAfter = '', personalNote = '', tags = [], isPublic = false, lectureUrl = '', markerColor = null) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    // Ermittle das Datum des Vortrags
    const lectureDate = getLectureDateFromId(gaReference);

    const insertData = {
        user_id: user.id,
        quote_text: quoteText,
        ga_reference: gaReference,
        personal_note: personalNote,
        tags: tags,
        is_public: isPublic
    };
    
    // Füge marker_color hinzu, falls angegeben (blue/red/yellow erlaubt)
    if (markerColor && (markerColor === 'blue' || markerColor === 'red' || markerColor === 'yellow')) {
      insertData.marker_color = markerColor;
    }
    
    // Füge lecture_date hinzu, falls verfügbar
    if (lectureDate) {
      insertData.lecture_date = lectureDate;
    }

    const { data, error } = await supabase
      .from('quotes')
      .insert(insertData)
      .select()
      .single();

    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Erstellen des Zitats:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Zitate abrufen
 */
export async function getQuotes(filters = {}) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    let query = supabase
      .from('quotes')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    if (filters.gaReference) {
      query = query.eq('ga_reference', filters.gaReference);
    }

    if (filters.tags && filters.tags.length > 0) {
      query = query.contains('tags', filters.tags);
    }

    const { data, error } = await query;
    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Abrufen der Zitate:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Öffentliche Zitate abrufen
 */
export async function getPublicQuotes(gaReference = null) {
  try {
    let query = supabase
      .from('quotes')
      .select('*, user_profiles(display_name)')
      .eq('is_public', true)
      .order('created_at', { ascending: false });

    if (gaReference) {
      query = query.eq('ga_reference', gaReference);
    }

    const { data, error } = await query;
    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Abrufen öffentlicher Zitate:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Zitat löschen
 */
export async function deleteQuote(quoteId) {
  try {
    const { error } = await supabase
      .from('quotes')
      .delete()
      .eq('id', quoteId);

    if (error) throw error;

    return { success: true };
  } catch (error) {
    console.error('Fehler beim Löschen des Zitats:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Zitat aktualisieren
 */
export async function updateQuote(quoteId, updates) {
  try {
    // Ensure marker_color is valid or null (blue/red/yellow erlaubt)
    if (updates.marker_color !== undefined) {
      if (updates.marker_color !== null && 
          updates.marker_color !== 'blue' && 
          updates.marker_color !== 'red' && 
          updates.marker_color !== 'yellow') {
        updates.marker_color = null;
      }
    }
    
    const { data, error } = await supabase
      .from('quotes')
      .update(updates)
      .eq('id', quoteId)
      .select()
      .single();

    if (error) {
      console.error('Supabase Fehler beim Aktualisieren des Zitats:', error);
      // Check if marker_color column is missing
      if (error.message && error.message.includes('marker_color')) {
        throw new Error('Die marker_color Spalte fehlt in der Datenbank. Bitte führen Sie das SQL-Script supabase-add-marker-color.sql im Supabase SQL Editor aus.');
      }
      throw error;
    }

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Aktualisieren des Zitats:', error);
    return { success: false, error: error.message || 'Unbekannter Fehler' };
  }
}


// ============================================
// NOTES (Notizen) mit Obsidian-Features
// ============================================

/**
 * Wiki-Links aus Text extrahieren [[Link]]
 */
export function extractWikiLinks(text) {
  const regex = /\[\[(.*?)\]\]/g;
  const matches = [];
  let match;
  
  while ((match = regex.exec(text)) !== null) {
    matches.push(match[1]);
  }
  
  return [...new Set(matches)]; // Duplikate entfernen
}


/**
 * Tags aus Text extrahieren #tag
 */
export function extractTags(text) {
  const regex = /#(\w+)/g;
  const matches = [];
  let match;
  
  while ((match = regex.exec(text)) !== null) {
    matches.push(match[1]);
  }
  
  return [...new Set(matches)]; // Duplikate entfernen
}


/**
 * GA-Referenzen aus Text extrahieren (GA110/5, GA107/3, etc.)
 */
export function extractGAReferences(text) {
  // Unterstützt auch GA-Nummern mit Buchstaben-Suffix wie GA266a/9
  const regex = /GA\s?(\d{1,3}[a-z]?)\/(\d{1,3})|GA\s?(\d{1,3}[a-z]?)/gi;
  const matches = [];
  let match;
  
  while ((match = regex.exec(text)) !== null) {
    if (match[1] && match[2]) {
      matches.push(`GA${match[1]}/${match[2]}`);
    } else if (match[3]) {
      matches.push(`GA${match[3]}`);
    }
  }
  
  return [...new Set(matches)]; // Duplikate entfernen
}


/**
 * Notiz erstellen mit automatischer Link-Extraktion
 */
export async function createNote(title, content, isPublic = false, paragraphId = null, paragraphText = null, textStartOffset = null, textEndOffset = null, lectureDate = null, manualTags = null, markerColor = null, manualGroups = null, endParagraphId = null) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    // Automatisch Links und Tags extrahieren
    const wikiLinks = extractWikiLinks(content);
    // Wenn manuelle Tags übergeben wurden, diese verwenden, sonst aus Content extrahieren
    const tags = manualTags !== null ? manualTags : extractTags(content);
    const gaReferences = extractGAReferences(content);

    // Alle Daten für die Notiz
    const insertData = {
        user_id: user.id,
        title: title,
        content: content,
        ga_references: gaReferences,
        wiki_links: wikiLinks,
        tags: tags,
        groups: manualGroups || [],
        is_public: isPublic,
        paragraph_id: paragraphId,
        paragraph_text: paragraphText,
        text_start_offset: textStartOffset,
        text_end_offset: textEndOffset,
        lecture_date: lectureDate,
        marker_color: markerColor || 'blue'
    };
    
    // Füge end_paragraph_id hinzu bei Multi-Absatz-Notizen
    if (endParagraphId) {
      insertData.end_paragraph_id = endParagraphId;
      console.log('[NOTE-CREATE] Multi-Absatz: end_paragraph_id =', endParagraphId);
    }

    const result = await supabase
      .from('notes')
      .insert(insertData)
      .select()
      .single();

    if (result.error) throw result.error;

    // Backlinks erstellen
    await updateBacklinks(result.data.id, 'note', [...wikiLinks, ...gaReferences]);

    return { success: true, data: result.data };
  } catch (error) {
    console.error('Fehler beim Erstellen der Notiz:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Notiz aktualisieren
 */
/**
 * Ändert nur die Farbe einer Notiz
 */
export async function updateNoteColor(noteId, color) {
  try {
    const { data, error } = await supabase
      .from('notes')
      .update({ marker_color: color })
      .eq('id', noteId)
      .select()
      .single();

    if (error) throw error;
    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Ändern der Notiz-Farbe:', error);
    return { success: false, error: error.message };
  }
}

export async function updateNote(noteId, title, content, isPublic = false, manualTags = null, markerColor = null, manualGroups = null) {
  try {
    // Links und Tags neu extrahieren
    const wikiLinks = extractWikiLinks(content);
    // Wenn manuelle Tags übergeben wurden, diese verwenden, sonst aus Content extrahieren
    const tags = manualTags !== null ? manualTags : extractTags(content);
    const gaReferences = extractGAReferences(content);

    // Update-Objekt erstellen
    const updateData = {
      title: title,
      content: content,
      ga_references: gaReferences,
      wiki_links: wikiLinks,
      tags: tags,
      is_public: isPublic
    };
    
    // Gruppen nur hinzufügen wenn angegeben
    if (manualGroups !== null) {
      updateData.groups = manualGroups;
    }
    
    // Farbe nur hinzufügen wenn angegeben
    if (markerColor !== null) {
      updateData.marker_color = markerColor;
    }

    const { data, error } = await supabase
      .from('notes')
      .update(updateData)
      .eq('id', noteId)
      .select()
      .single();

    if (error) throw error;

    // Backlinks aktualisieren
    await deleteBacklinks(noteId);
    await updateBacklinks(noteId, 'note', [...wikiLinks, ...gaReferences]);

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Aktualisieren der Notiz:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Notizen abrufen
 */
export async function getNotes(filters = {}) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    let query = supabase
      .from('notes')
      .select('*')
      .eq('user_id', user.id)
      .order('updated_at', { ascending: false });

    if (filters.tag) {
      query = query.contains('tags', [filters.tag]);
    }

    if (filters.gaReference) {
      query = query.contains('ga_references', [filters.gaReference]);
    }

    const { data, error } = await query;
    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Abrufen der Notizen:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Einzelne Notiz abrufen
 */
export async function getNote(noteId) {
  try {
    const { data, error } = await supabase
      .from('notes')
      .select('*')
      .eq('id', noteId)
      .single();

    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Abrufen der Notiz:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Notiz löschen
 */
export async function deleteNote(noteId) {
  try {
    // Erst Backlinks löschen
    await deleteBacklinks(noteId);

    // Dann Notiz löschen
    const { error } = await supabase
      .from('notes')
      .delete()
      .eq('id', noteId);

    if (error) throw error;

    return { success: true };
  } catch (error) {
    console.error('Fehler beim Löschen der Notiz:', error);
    return { success: false, error: error.message };
  }
}


/**
 * In Notizen suchen (Volltext)
 */
export async function searchNotes(searchTerm) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    const { data, error } = await supabase
      .from('notes')
      .select('*')
      .eq('user_id', user.id)
      .textSearch('content', searchTerm, {
        type: 'websearch',
        config: 'german'
      });

    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Durchsuchen der Notizen:', error);
    return { success: false, error: error.message };
  }
}


// ============================================
// BACKLINKS (für Obsidian-Features)
// ============================================

/**
 * Backlinks erstellen/aktualisieren
 */
async function updateBacklinks(sourceId, sourceType, targetReferences) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    const backlinks = targetReferences.map(ref => ({
      user_id: user.id,
      source_type: sourceType,
      source_id: sourceId,
      target_reference: ref
    }));

    if (backlinks.length === 0) return;

    const { error } = await supabase
      .from('backlinks')
      .insert(backlinks);

    if (error) throw error;
  } catch (error) {
    console.error('Fehler beim Erstellen der Backlinks:', error);
  }
}


/**
 * Backlinks löschen
 */
async function deleteBacklinks(sourceId) {
  try {
    const { error } = await supabase
      .from('backlinks')
      .delete()
      .eq('source_id', sourceId);

    if (error) throw error;
  } catch (error) {
    console.error('Fehler beim Löschen der Backlinks:', error);
  }
}


/**
 * Backlinks zu einer Referenz abrufen
 */
export async function getBacklinks(targetReference) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    const { data, error } = await supabase
      .from('backlinks')
      .select('*')
      .eq('user_id', user.id)
      .eq('target_reference', targetReference);

    if (error) throw error;

    // Detaillierte Infos zu den verlinkenden Items abrufen
    const detailedBacklinks = [];

    for (const backlink of data) {
      let itemData = null;
      
      if (backlink.source_type === 'note') {
        const result = await getNote(backlink.source_id);
        itemData = result.success ? result.data : null;
      }
      // Weitere Types können hier hinzugefügt werden

      if (itemData) {
        detailedBacklinks.push({
          ...backlink,
          item: itemData
        });
      }
    }

    return { success: true, data: detailedBacklinks };
  } catch (error) {
    console.error('Fehler beim Abrufen der Backlinks:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Graph-Daten für Visualisierung generieren
 */
export async function generateGraphData() {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    // Alle Notizen abrufen
    const notesResult = await getNotes();
    if (!notesResult.success) throw new Error('Fehler beim Abrufen der Notizen');

    const notes = notesResult.data;
    const nodes = [];
    const links = [];
    const nodeMap = new Map();

    // Notizen als Nodes hinzufügen
    notes.forEach(note => {
      const nodeId = note.id;
      nodes.push({
        id: nodeId,
        label: note.title || 'Unbenannte Notiz',
        type: 'note',
        data: note
      });
      nodeMap.set(nodeId, true);

      // GA-Referenzen als Nodes
      note.ga_references?.forEach(ref => {
        if (!nodeMap.has(ref)) {
          nodes.push({
            id: ref,
            label: ref,
            type: 'ga_reference'
          });
          nodeMap.set(ref, true);
        }
        
        links.push({
          source: nodeId,
          target: ref
        });
      });

      // Wiki-Links als Nodes
      note.wiki_links?.forEach(link => {
        if (!nodeMap.has(link)) {
          nodes.push({
            id: link,
            label: link,
            type: 'wiki_link'
          });
          nodeMap.set(link, true);
        }
        
        links.push({
          source: nodeId,
          target: link
        });
      });
    });

    return {
      success: true,
      data: { nodes, links }
    };
  } catch (error) {
    console.error('Fehler beim Generieren der Graph-Daten:', error);
    return { success: false, error: error.message };
  }
}


// ============================================
// CHAT
// ============================================

/**
 * Chat-Nachricht senden
 */
export async function sendChatMessage(message, room = 'general') {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    // User-Profil für Anzeigename abrufen
    const profile = await getUserProfile(user.id);
    const userName = profile?.display_name || user.email;

    const { data, error } = await supabase
      .from('chat_messages')
      .insert({
        user_id: user.id,
        user_name: userName,
        message: message,
        room: room
      })
      .select()
      .single();

    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Senden der Nachricht:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Chat-Nachrichten abrufen
 */
export async function getChatMessages(room = 'general', limit = 50) {
  try {
    const { data, error } = await supabase
      .from('chat_messages')
      .select('*')
      .eq('room', room)
      .order('created_at', { ascending: false })
      .limit(limit);

    if (error) throw error;

    return { success: true, data: data.reverse() }; // Älteste zuerst
  } catch (error) {
    console.error('Fehler beim Abrufen der Nachrichten:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Realtime-Listener für neue Chat-Nachrichten
 */
export function subscribeToChatMessages(room, callback) {
  const channel = supabase
    .channel(`chat:${room}`)
    .on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: 'chat_messages',
        filter: `room=eq.${room}`
      },
      (payload) => {
        callback(payload.new);
      }
    )
    .subscribe();

  return channel;
}


/**
 * Realtime-Listener beenden
 */
export function unsubscribeFromChat(channel) {
  supabase.removeChannel(channel);
}


// ============================================
// HIGHLIGHTS (Unterstreichungen)
// ============================================

/**
 * Unterstreichung erstellen
 */
export async function createHighlight(gaNumber, lectureTitle, paragraphId, paragraphText, textStartOffset, textEndOffset, lectureUrl = '', color = 'blue') {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    // Ermittle das Datum des Vortrags
    const lectureDate = getLectureDateFromId(gaNumber);

    const insertData = {
        user_id: user.id,
        ga_number: gaNumber,
        paragraph_id: paragraphId,
        paragraph_text: paragraphText,
        text_start_offset: textStartOffset,
        text_end_offset: textEndOffset,
        color: color
    };
    
    // Füge lecture_date hinzu, falls verfügbar
    if (lectureDate) {
      insertData.lecture_date = lectureDate;
    }

    const { data, error } = await supabase
      .from('highlights')
      .insert(insertData)
      .select()
      .single();

    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Erstellen der Unterstreichung:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Alle Unterstreichungen des Users abrufen
 */
export async function getHighlights(gaNumber = null) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    let query = supabase
      .from('highlights')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    if (gaNumber) {
      query = query.eq('ga_number', gaNumber);
    }

    const { data, error } = await query;
    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Abrufen der Unterstreichungen:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Unterstreichung löschen
 */
export async function deleteHighlight(highlightId) {
  try {
    const { error } = await supabase
      .from('highlights')
      .delete()
      .eq('id', highlightId);

    if (error) throw error;

    return { success: true };
  } catch (error) {
    console.error('Fehler beim Löschen der Unterstreichung:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Unterstreichung aktualisieren
 */
export async function updateHighlight(highlightId, updates) {
  try {
    const { data, error } = await supabase
      .from('highlights')
      .update(updates)
      .eq('id', highlightId)
      .select()
      .single();

    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Aktualisieren der Unterstreichung:', error);
    return { success: false, error: error.message };
  }
}


// Helper: User-Profil abrufen (aus members-auth.js importiert, aber hier nochmal für einfache Nutzung)
async function getUserProfile(userId) {
  const { data } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('id', userId)
    .single();
  
  return data;
}


// ============================================
// SAVED THEMATIC SEARCHES (Gespeicherte Themenabfragen)
// ============================================

/**
 * Themenabfrage speichern
 */
export async function saveThematicSearch(query, content, sources = [], options = {}) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    const {
      title = null,
      searchMethod = 'hybrid-thematic-unified',
      totalMatches = 0,
      gaFilter = null,
      limitUsed = 100,
      tags = [],
      notes = null
    } = options;

    // ga_filter-Spalte ist VARCHAR(50) – längere Filter gehoeren in notes (gaFilterFull)
    const gaFilterDb = gaFilter ? String(gaFilter).slice(0, 50) : null;

    const { data, error } = await supabase
      .from('saved_thematic_searches')
      .insert({
        user_id: user.id,
        query: query,
        title: title || query.substring(0, 100), // Fallback: Erste 100 Zeichen der Query
        content: content,
        sources: sources,
        search_method: searchMethod,
        total_matches: totalMatches,
        ga_filter: gaFilterDb,
        limit_used: limitUsed,
        tags: tags,
        notes: notes
      })
      .select()
      .single();

    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Speichern der Themenabfrage:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Alle gespeicherten Themenabfragen des Users abrufen
 */
export async function getSavedThematicSearches(filters = {}) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    let query = supabase
      .from('saved_thematic_searches')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    // Optional: Nach Tags filtern
    if (filters.tags && filters.tags.length > 0) {
      query = query.contains('tags', filters.tags);
    }

    // Optional: Limit
    if (filters.limit) {
      query = query.limit(filters.limit);
    }

    const { data, error } = await query;
    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Abrufen der gespeicherten Themenabfragen:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Einzelne gespeicherte Themenabfrage abrufen
 */
export async function getSavedThematicSearch(searchId) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    const { data, error } = await supabase
      .from('saved_thematic_searches')
      .select('*')
      .eq('id', searchId)
      .eq('user_id', user.id)
      .single();

    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Abrufen der Themenabfrage:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Gespeicherte Themenabfrage aktualisieren
 */
export async function updateSavedThematicSearch(searchId, updates) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    const { data, error } = await supabase
      .from('saved_thematic_searches')
      .update(updates)
      .eq('id', searchId)
      .eq('user_id', user.id)
      .select()
      .single();

    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Aktualisieren der Themenabfrage:', error);
    return { success: false, error: error.message };
  }
}


/**
 * Gespeicherte Themenabfrage löschen
 */
export async function deleteSavedThematicSearch(searchId) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    const { error } = await supabase
      .from('saved_thematic_searches')
      .delete()
      .eq('id', searchId)
      .eq('user_id', user.id);

    if (error) throw error;

    return { success: true };
  } catch (error) {
    console.error('Fehler beim Löschen der Themenabfrage:', error);
    return { success: false, error: error.message };
  }
}


/**
 * In gespeicherten Themenabfragen suchen (Volltext)
 */
export async function searchSavedThematicSearches(searchTerm) {
  try {
    const user = await getCurrentUser();
    if (!user) throw new Error('Nicht angemeldet');

    const { data, error } = await supabase
      .from('saved_thematic_searches')
      .select('*')
      .eq('user_id', user.id)
      .or(`query.ilike.%${searchTerm}%,title.ilike.%${searchTerm}%,content.ilike.%${searchTerm}%`)
      .order('created_at', { ascending: false });

    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Fehler beim Durchsuchen der Themenabfragen:', error);
    return { success: false, error: error.message };
  }
}

