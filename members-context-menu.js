// ============================================
// GA-Suche - Rechtsklick Kontextmenü für Mitglieder
// Bookmark, Zitat, Notiz per Rechtsklick
// ============================================

let contextMenu = null;
let selectedTextForContext = '';
let selectionRangeForContext = null;

/**
 * Initialisiert das Rechtsklick-Kontextmenü
 */
function initMembersContextMenu() {
  // Context-Menü erstellen
  createContextMenu();
  
  // Rechtsklick-Event auf gesamtes Dokument (nicht nur Viewer)
  // So funktioniert es auch wenn Viewer später geladen wird
  document.addEventListener('contextmenu', handleContextMenu);
  
  // Klick außerhalb schließt Menü
  document.addEventListener('click', hideContextMenu);
}

/**
 * Context-Menü HTML erstellen
 */
function createContextMenu() {
  if (contextMenu) return;
  
  contextMenu = document.createElement('div');
  contextMenu.id = 'members-context-menu';
  contextMenu.className = 'members-context-menu';
  contextMenu.innerHTML = `
    <div class="context-menu-item highlight-menu-item" onmouseenter="showHighlightColorMenu()" onmouseleave="hideHighlightColorMenu()">
      <span class="context-menu-text">Unterstreichen</span>
      <span class="context-menu-arrow">▶</span>
      <div id="highlight-color-menu" class="context-submenu highlight-submenu-hidden" onmouseenter="showHighlightColorMenu()" onmouseleave="hideHighlightColorMenu()">
        <div class="context-menu-item" onclick="contextMenuAction('highlight', 'blue')" style="border-left: 3px solid #467886;">
          <span class="context-menu-text">Blau</span>
        </div>
        <div class="context-menu-item" onclick="contextMenuAction('highlight', 'red')" style="border-left: 3px solid #c62828;">
          <span class="context-menu-text">Rot</span>
        </div>
        <div class="context-menu-item" onclick="contextMenuAction('highlight', 'yellow')" style="border-left: 3px solid #ffc107;">
          <span class="context-menu-text">Gelb</span>
        </div>
      </div>
    </div>
    <div class="context-menu-item quote-menu-item" onmouseenter="showQuoteColorMenu()" onmouseleave="hideQuoteColorMenu()">
      <span class="context-menu-text">Zitat speichern</span>
      <span class="context-menu-arrow">▶</span>
      <div id="quote-color-menu" class="context-submenu quote-submenu-hidden" onmouseenter="showQuoteColorMenu()" onmouseleave="hideQuoteColorMenu()">
        <div class="context-menu-item" onclick="contextMenuAction('quote', 'blue')" style="border-left: 3px solid #467886;">
          <span class="context-menu-text">Blau</span>
        </div>
        <div class="context-menu-item" onclick="contextMenuAction('quote', 'red')" style="border-left: 3px solid #c62828;">
          <span class="context-menu-text">Rot</span>
        </div>
        <div class="context-menu-item" onclick="contextMenuAction('quote', 'yellow')" style="border-left: 3px solid #ffc107;">
          <span class="context-menu-text">Gelb</span>
        </div>
      </div>
    </div>
    <div class="context-menu-item" onclick="contextMenuAction('note')">
      <span class="context-menu-text">Notiz erstellen</span>
    </div>
  `;
  
  document.body.appendChild(contextMenu);
  addContextMenuStyles();
}

/**
 * Rechtsklick Handler
 */
function handleContextMenu(e) {
  const selection = window.getSelection();
  const selectedText = selection.toString().trim();
  
  // Nur anzeigen wenn Text markiert ist UND im Viewer oder Main
  const viewer = document.getElementById('viewer');
  const main = document.getElementById('main');
  const target = e.target;
  
  // Prüfe ob Klick im relevanten Bereich
  const isInViewer = viewer && (viewer.contains(target) || viewer === target);
  const isInMain = main && (main.contains(target) || main === target);
  
  if (selectedText.length < 3 || (!isInViewer && !isInMain)) {
    hideContextMenu();
    return;
  }
  
  e.preventDefault();
  e.stopPropagation();
  
  // Text und Range speichern
  selectedTextForContext = selectedText;
  try {
    selectionRangeForContext = selection.getRangeAt(0).cloneRange();
  } catch (err) {
    selectionRangeForContext = null;
  }
  
  // Menü positionieren
  showContextMenu(e.clientX, e.clientY);
}

/**
 * Context-Menü anzeigen
 */
function showContextMenu(x, y) {
  if (!contextMenu) return;
  
  contextMenu.style.display = 'block';
  contextMenu.style.left = x + 'px';
  contextMenu.style.top = y + 'px';
  
  // Viewport-Grenzen prüfen
  const menuRect = contextMenu.getBoundingClientRect();
  
  // Rechts aus dem Viewport?
  if (menuRect.right > window.innerWidth) {
    contextMenu.style.left = (window.innerWidth - menuRect.width - 10) + 'px';
  }
  
  // Unten aus dem Viewport?
  if (menuRect.bottom > window.innerHeight) {
    contextMenu.style.top = (window.innerHeight - menuRect.height - 10) + 'px';
  }
}

/**
 * Context-Menü verbergen
 */
function hideContextMenu() {
  if (contextMenu) {
    contextMenu.style.display = 'none';
  }
}

/**
 * Context-Menü Aktion
 */
async function contextMenuAction(action, extraData = null) {
  hideContextMenu();
  
  if (!selectedTextForContext) {
    showContextNotification('⚠️ Kein Text markiert', 'info');
    return;
  }
  
  // Prüfe ob Supabase verfügbar ist
  if (typeof initSupabase !== 'function') {
    showContextNotification('✗ Mitglieder-System nicht geladen', 'error');
    console.error('initSupabase ist nicht definiert - members-integration-standalone.js fehlt?');
    return;
  }
  
  // Prüfe ob angemeldet
  try {
    await initSupabase();
  } catch (err) {
    showContextNotification('✗ Verbindungsfehler', 'error');
    console.error('Fehler bei initSupabase:', err);
    return;
  }
  
  if (!currentUser) {
    showContextNotification('⚠️ Bitte zuerst anmelden', 'info');
    // Öffne MB nach kurzer Verzögerung
    setTimeout(() => {
      if (typeof openMembersPanel === 'function') {
        openMembersPanel();
      }
    }, 1000);
    return;
  }
  
  // Context-Informationen sammeln
  const contextBefore = getContextBefore(selectedTextForContext, 100);
  const contextAfter = getContextAfter(selectedTextForContext, 100);
  
  // Absatz-Index ermitteln (Format: "1a", "42", etc.)
  const paragraphIndex = findParagraphId(selectionRangeForContext);
  
  // Hole vollständige Lecture-ID (GA058/01) statt nur GA-Nummer
  const lectureId = (typeof currentLectureData !== 'undefined' && currentLectureData?.ID) 
    ? currentLectureData.ID 
    : extractGAFromURL();
  const gaNumber = lectureId ? lectureId.split('/')[0] : 'Unbekannt';
  const lectureTitle = currentContext?.lectureTitle || '';
  
  switch(action) {
    case 'quote':
      const quoteColor = extraData || 'blue'; // Standard: blau
      await saveContextQuote(selectedTextForContext, lectureId, lectureTitle, paragraphIndex, contextBefore, contextAfter, quoteColor);
      break;
    case 'highlight':
      const color = extraData || 'blue'; // Standard: blau
      await saveContextHighlight(selectedTextForContext, lectureId, lectureTitle, paragraphIndex, color);
      break;
    case 'note':
      openContextNote(selectedTextForContext, lectureId, lectureTitle);
      break;
  }
}

/**
 * Bookmark aus Context-Menü speichern
 */
async function saveContextBookmark(text, lectureId, lectureTitle, paragraphIndex) {
  try {
    if (typeof supabaseClient === 'undefined' || !supabaseClient) {
      throw new Error('Supabase Client nicht initialisiert');
    }
    
    // Zeige Keyword-Eingabe-Dialog (mit Notizen-Feld)
    const result = await showKeywordDialog('Bookmark', text);
    if (result === null) {
      // Benutzer hat abgebrochen
      return;
    }
    
    const { keywords, note } = result;
    
    const insertData = {
      user_id: currentUser.id,
      ga_number: lectureId,
      lecture_title: lectureTitle,
      paragraph_id: paragraphIndex,
      paragraph_text: text,
      note: note || '',
      tags: keywords
    };
    
    const { data, error } = await supabaseClient
      .from('bookmarks')
      .insert(insertData)
      .select();
    
    if (error) {
      console.error('Supabase Fehler:', error);
      throw new Error(error.message || 'Datenbankfehler');
    }
    
    showContextNotification('✓ Bookmark gespeichert!', 'success');
    highlightContextSelection('#ccffcc');
    
    // MB aktualisieren falls offen
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
 * Ermittelt das Datum des aktuellen Vortrags
 * Gibt das Datum im Format YYYY-MM-DD zurück oder null wenn nicht verfügbar
 */
function getCurrentLectureDate(lectureId) {
  if (!lectureId) {
    console.warn('[LECTURE-DATE] Keine lectureId übergeben');
    return null;
  }
  
  // Versuche aus currentLectureData zu holen (nur wenn ID übereinstimmt)
  if (typeof currentLectureData !== 'undefined' && currentLectureData) {
    // Prüfe ob die ID übereinstimmt
    const currentId = currentLectureData.ID || currentLectureData.id || '';
    if (currentId && currentId === lectureId) {
      let date = currentLectureData.date || currentLectureData.dateString || '';
      
      if (date) {
        // Wenn bereits im ISO-Format (YYYY-MM-DD), direkt zurückgeben
        if (date.match(/^\d{4}-\d{2}-\d{2}$/)) {
          console.log('[LECTURE-DATE] Datum gefunden (ISO):', date);
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
            const isoDate = `${year}-${month}-${day}`;
            console.log('[LECTURE-DATE] Datum konvertiert:', date, '->', isoDate);
            return isoDate;
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
            const isoDate = `${year}-${month}-${day}`;
            console.log('[LECTURE-DATE] Datum aus location/fileName extrahiert:', isoDate);
            return isoDate;
          }
        }
      }
    } else {
      console.warn('[LECTURE-DATE] currentLectureData.ID stimmt nicht überein:', currentId, 'vs', lectureId);
    }
  } else {
    console.warn('[LECTURE-DATE] currentLectureData nicht verfügbar für lectureId:', lectureId);
  }
  
  return null;
}

/**
 * Zitat aus Context-Menü speichern
 */
async function saveContextQuote(text, lectureId, lectureTitle, paragraphIndex, contextBefore, contextAfter, color = 'blue') {
  try {
    if (typeof supabaseClient === 'undefined' || !supabaseClient) {
      throw new Error('Supabase Client nicht initialisiert');
    }
    
    if (!selectionRangeForContext) {
      throw new Error('Keine Textauswahl vorhanden');
    }
    
    // Finde den Absatz-Container, der den markierten Text enthält
    let paragraphNode = selectionRangeForContext.commonAncestorContainer;
    while (paragraphNode && paragraphNode.nodeType !== Node.ELEMENT_NODE) {
      paragraphNode = paragraphNode.parentNode;
    }
    
    console.log('[QUOTE-SAVE] Starte Absatz-Suche, initial node:', paragraphNode?.tagName, paragraphNode?.id);
    
    // Für Bücher: Suche zuerst nach para- ID oder data-index
    let foundParaId = false;
    let tempNode = paragraphNode;
    while (tempNode && tempNode !== document.body) {
      if (tempNode.nodeType === 1) { // Element node
        // Prüfe ob para- ID vorhanden (für Vorträge und Bücher)
        if (tempNode.id && tempNode.id.startsWith('para-')) {
          console.log('[QUOTE-SAVE] para- ID gefunden:', tempNode.id);
          paragraphNode = tempNode;
          foundParaId = true;
          break;
        }
        // Prüfe ob data-index vorhanden (für Bücher)
        if (tempNode.dataset && tempNode.dataset.index) {
          console.log('[QUOTE-SAVE] data-index gefunden:', tempNode.dataset.index);
          // Finde das Parent-Element, das den Text enthält
          let parent = tempNode.parentElement;
          while (parent && parent !== document.body) {
            const tagName = parent.tagName.toLowerCase();
            if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
              console.log('[QUOTE-SAVE] Parent-Element mit Text gefunden:', tagName);
              paragraphNode = parent;
              foundParaId = true;
              break;
            }
            parent = parent.parentElement;
          }
          if (foundParaId) break;
        }
      }
      tempNode = tempNode.parentNode;
    }
    
    // Falls keine para- ID gefunden, suche nach dem Absatz-Element (p, div, etc.)
    if (!foundParaId) {
      console.log('[QUOTE-SAVE] Keine para- ID gefunden, suche nach Block-Element');
      tempNode = paragraphNode;
      while (tempNode && tempNode !== document.body) {
        const tagName = tempNode.tagName ? tempNode.tagName.toLowerCase() : '';
        if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
          // Prüfe ob dieser Absatz den markierten Text enthält
          const nodeText = tempNode.textContent || '';
          console.log('[QUOTE-SAVE] Block-Element gefunden:', tagName, 'Text-Länge:', nodeText.length, 'Enthält Text?', nodeText.includes(text));
          if (nodeText && nodeText.includes(text)) {
            paragraphNode = tempNode;
            foundParaId = true;
            break;
          }
        }
        tempNode = tempNode.parentNode;
      }
    }
    
    // Letzter Fallback: Verwende einfach das Element, das den Text enthält (auch wenn es kein Block-Element ist)
    if (!foundParaId && paragraphNode) {
      console.log('[QUOTE-SAVE] Fallback: Verwende aktuelles Element');
      // Prüfe ob das Element selbst Text enthält
      const nodeText = paragraphNode.textContent || '';
      if (!nodeText || !nodeText.includes(text)) {
        // Suche nach einem Parent, der den Text enthält
        tempNode = paragraphNode.parentNode;
        while (tempNode && tempNode !== document.body) {
          const nodeText2 = tempNode.textContent || '';
          if (nodeText2 && nodeText2.includes(text)) {
            paragraphNode = tempNode;
            foundParaId = true;
            console.log('[QUOTE-SAVE] Fallback: Parent mit Text gefunden:', tempNode.tagName);
            break;
          }
          tempNode = tempNode.parentNode;
        }
      } else {
        foundParaId = true;
      }
    }
    
    if (!paragraphNode || paragraphNode === document.body || !foundParaId) {
      console.error('[QUOTE-SAVE] Absatz nicht gefunden. paragraphNode:', paragraphNode, 'foundParaId:', foundParaId);
      throw new Error('Absatz nicht gefunden');
    }
    
    console.log('[QUOTE-SAVE] Absatz gefunden:', paragraphNode.tagName, paragraphNode.id || paragraphNode.dataset?.index || 'keine ID');
    
    // Hole den vollständigen Text des Absatzes
    // Verwende textContent für konsistente Berechnung (ignoriert HTML-Tags)
    const paragraphText = paragraphNode.textContent || paragraphNode.innerText || '';
    
    console.log('[QUOTE-SAVE] Paragraph Text Länge:', paragraphText.length);
    console.log('[QUOTE-SAVE] Selected Text:', text.substring(0, 50) + '...');
    console.log('[QUOTE-SAVE] Paragraph Index:', paragraphIndex);
    
    // Finde die Position des markierten Textes im Absatz
    // Verwende die Range-Informationen für präzisere Berechnung
    let textStartOffset = -1;
    let textEndOffset = -1;
    
    // Versuche zuerst mit der Range die exakte Position zu finden
    try {
      const range = selectionRangeForContext.cloneRange();
      const paraRange = document.createRange();
      paraRange.selectNodeContents(paragraphNode);
      
      // Berechne Offset relativ zum Absatz
      const startContainer = range.startContainer;
      const startOffset = range.startOffset;
      
      // Erstelle einen TreeWalker um die Position zu berechnen
      const walker = document.createTreeWalker(
        paragraphNode,
        NodeFilter.SHOW_TEXT,
        null,
        false
      );
      
      let currentOffset = 0;
      let node;
      let foundStart = false;
      
      while (node = walker.nextNode()) {
        if (node === startContainer || node.parentNode === startContainer) {
          if (node === startContainer) {
            textStartOffset = currentOffset + startOffset;
            foundStart = true;
          } else if (node.parentNode === startContainer) {
            // Text-Node ist Kind des Start-Containers
            let siblingOffset = 0;
            let sibling = node.previousSibling;
            while (sibling) {
              siblingOffset += (sibling.textContent || '').length;
              sibling = sibling.previousSibling;
            }
            textStartOffset = currentOffset + siblingOffset + startOffset;
            foundStart = true;
          }
          break;
        }
        currentOffset += node.textContent.length;
      }
      
      if (foundStart) {
        textEndOffset = textStartOffset + text.length;
        console.log('[QUOTE-SAVE] Offsets aus Range berechnet:', textStartOffset, textEndOffset);
      } else {
        // Fallback: Verwende indexOf
        textStartOffset = paragraphText.indexOf(text);
        textEndOffset = textStartOffset + text.length;
        console.log('[QUOTE-SAVE] Offsets mit indexOf berechnet:', textStartOffset, textEndOffset);
      }
    } catch (e) {
      console.warn('[QUOTE-SAVE] Fehler bei Range-Berechnung, verwende indexOf:', e);
      textStartOffset = paragraphText.indexOf(text);
      textEndOffset = textStartOffset + text.length;
    }
    
    if (textStartOffset === -1) {
      // Fallback: Versuche mit normalisiertem Text
      const normalizedParagraph = paragraphText.replace(/\s+/g, ' ').trim();
      const normalizedText = text.replace(/\s+/g, ' ').trim();
      const normalizedStart = normalizedParagraph.indexOf(normalizedText);
      
      if (normalizedStart === -1) {
        console.warn('[QUOTE-SAVE] Textposition im Absatz nicht gefunden, speichere ohne Offsets');
        textStartOffset = null;
        textEndOffset = null;
      } else {
        // Verwende die normalisierte Position als Näherung
        textStartOffset = normalizedStart;
        textEndOffset = normalizedStart + normalizedText.length;
        console.log('[QUOTE-SAVE] Offsets mit normalisiertem Text berechnet:', textStartOffset, textEndOffset);
      }
    }
    
    // Zeige Keyword-Eingabe-Dialog (mit Notizen-Feld)
    const result = await showKeywordDialog('Zitat', text);
    if (result === null) {
      // Benutzer hat abgebrochen
      return;
    }
    
    const { keywords, note } = result;
    
    // Ermittle das Datum des Vortrags
    const lectureDate = getCurrentLectureDate(lectureId);
    console.log('[QUOTE-SAVE] LectureId:', lectureId, 'LectureDate:', lectureDate);
    
    const insertData = {
      user_id: currentUser.id,
      quote_text: text,
      ga_reference: lectureId,
      lecture_title: lectureTitle,
      paragraph_id: paragraphIndex,
      personal_note: note || '',
      tags: keywords,
      is_public: false,
      marker_color: color
    };
    
    // WICHTIG: Verwende die neuen Spalten für exakte Textmarkierung
    // paragraph_text, text_start_offset, text_end_offset sind die primären Spalten
    if (paragraphText) {
      insertData.paragraph_text = paragraphText;
    }
    if (textStartOffset !== -1 && textStartOffset !== null) {
      insertData.text_start_offset = textStartOffset;
    }
    if (textEndOffset !== -1 && textEndOffset !== null) {
      insertData.text_end_offset = textEndOffset;
    }
    
    // context_before und context_after werden nicht mehr benötigt (deprecated)
    // Sie werden nur noch für Rückwärtskompatibilität gespeichert, falls die Spalten noch existieren
    
    // Füge lecture_date hinzu, falls verfügbar
    if (lectureDate) {
      insertData.lecture_date = lectureDate;
      console.log('[QUOTE-SAVE] Füge lecture_date hinzu:', lectureDate);
    } else {
      console.warn('[QUOTE-SAVE] Kein lecture_date verfügbar für:', lectureId);
    }
    
    const { data, error } = await supabaseClient
      .from('quotes')
      .insert(insertData)
      .select();
    
    if (error) {
      console.error('Supabase Fehler:', error);
      
      // Prüfe ob Fehler wegen fehlender Spalten ist
      if (error.message && (error.message.includes('paragraph_text') || 
          error.message.includes('text_start_offset') ||
          error.message.includes('text_end_offset'))) {
        console.warn('[QUOTE-SAVE] Neue Spalten fehlen in der Datenbank. Versuche ohne diese Spalten zu speichern...');
        
        // Entferne die neuen Spalten und versuche es erneut
        const fallbackData = { ...insertData };
        delete fallbackData.paragraph_text;
        delete fallbackData.text_start_offset;
        delete fallbackData.text_end_offset;
        
        const { data: retryData, error: retryError } = await supabaseClient
          .from('quotes')
          .insert(fallbackData)
          .select();
        
        if (retryError) {
          throw new Error(retryError.message || 'Datenbankfehler');
        }
        
        // Warnung anzeigen, dass Migration benötigt wird
        console.warn('[QUOTE-SAVE] Zitat ohne Offsets gespeichert. Bitte führen Sie das Migrationsskript supabase-add-quote-offsets.sql aus.');
        showContextNotification('✓ Zitat gespeichert (ohne exakte Position). Bitte Migration ausführen für exakte Textmarkierung!', 'warning');
        
        // MB aktualisieren falls offen
        if (typeof membersPanelActive !== 'undefined' && membersPanelActive) {
          if (typeof invalidateMembersCache === 'function') {
            invalidateMembersCache('quotes');
          }
          if (typeof updateMembersPanelIfOpen === 'function') {
            await updateMembersPanelIfOpen('quotes', true);
          } else if (typeof loadMembersTab === 'function' && currentMembersTab === 'quotes') {
            await loadMembersTab('quotes');
          }
        }
        return;
      }
      
      throw new Error(error.message || 'Datenbankfehler');
    }
    
    showContextNotification('✓ Zitat gespeichert!', 'success');
    
    // Zitat visuell markieren und klickbar machen
    if (data && data.length > 0) {
      const savedQuote = data[0];
      applyQuoteToSelection(selectionRangeForContext, savedQuote.id, lectureId, paragraphIndex);
    } else {
      highlightContextSelection('#ffffcc');
    }
    
    // MB aktualisieren falls offen (invalidiert Cache und lädt Quotes-Tab neu)
    if (typeof membersPanelActive !== 'undefined' && membersPanelActive) {
      // Invalidiere Cache für Quotes
      if (typeof invalidateMembersCache === 'function') {
        invalidateMembersCache('quotes');
      }
      // Aktualisiere Panel falls offen - aktualisiere auch wenn Tab nicht aktiv ist
      if (typeof updateMembersPanelIfOpen === 'function') {
        await updateMembersPanelIfOpen('quotes', true);
      } else if (typeof loadMembersTab === 'function' && currentMembersTab === 'quotes') {
        // Fallback: Nur aktualisieren wenn Quotes-Tab aktiv ist
        await loadMembersTab('quotes');
      }
    }
  } catch (error) {
    console.error('[QUOTE-SAVE] Fehler:', error);
    console.error('[QUOTE-SAVE] Daten:', { lectureId, paragraphIndex, text_length: text?.length });
    showContextNotification(`✗ Zitat Fehler: ${error.message}`, 'error');
  }
}

/**
 * Unterstreichung aus Context-Menü speichern
 */
async function saveContextHighlight(text, lectureId, lectureTitle, paragraphIndex, color = 'blue') {
  try {
    if (typeof supabaseClient === 'undefined' || !supabaseClient) {
      throw new Error('Supabase Client nicht initialisiert');
    }
    
    if (!selectionRangeForContext) {
      throw new Error('Keine Textauswahl vorhanden');
    }
    
    // Finde den Absatz-Container, der den markierten Text enthält
    let paragraphNode = selectionRangeForContext.commonAncestorContainer;
    while (paragraphNode && paragraphNode.nodeType !== Node.ELEMENT_NODE) {
      paragraphNode = paragraphNode.parentNode;
    }
    
    console.log('[HIGHLIGHT-SAVE] Starte Absatz-Suche, initial node:', paragraphNode?.tagName, paragraphNode?.id);
    
    // Für Bücher: Suche zuerst nach para- ID oder data-index
    let foundParaId = false;
    let tempNode = paragraphNode;
    while (tempNode && tempNode !== document.body) {
      if (tempNode.nodeType === 1) { // Element node
        // Prüfe ob para- ID vorhanden (für Vorträge und Bücher)
        if (tempNode.id && tempNode.id.startsWith('para-')) {
          console.log('[HIGHLIGHT-SAVE] para- ID gefunden:', tempNode.id);
          paragraphNode = tempNode;
          foundParaId = true;
          break;
        }
        // Prüfe ob data-index vorhanden (für Bücher)
        if (tempNode.dataset && tempNode.dataset.index) {
          console.log('[HIGHLIGHT-SAVE] data-index gefunden:', tempNode.dataset.index);
          // Finde das Parent-Element, das den Text enthält
          let parent = tempNode.parentElement;
          while (parent && parent !== document.body) {
            const tagName = parent.tagName.toLowerCase();
            if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
              console.log('[HIGHLIGHT-SAVE] Parent-Element mit Text gefunden:', tagName);
              paragraphNode = parent;
              foundParaId = true;
              break;
            }
            parent = parent.parentElement;
          }
          if (foundParaId) break;
        }
      }
      tempNode = tempNode.parentNode;
    }
    
    // Falls keine para- ID gefunden, suche nach dem Absatz-Element (p, div, etc.)
    if (!foundParaId) {
      console.log('[HIGHLIGHT-SAVE] Keine para- ID gefunden, suche nach Block-Element');
      tempNode = paragraphNode;
      while (tempNode && tempNode !== document.body) {
        const tagName = tempNode.tagName ? tempNode.tagName.toLowerCase() : '';
        if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
          // Prüfe ob dieser Absatz den markierten Text enthält
          const nodeText = tempNode.textContent || '';
          console.log('[HIGHLIGHT-SAVE] Block-Element gefunden:', tagName, 'Text-Länge:', nodeText.length, 'Enthält Text?', nodeText.includes(text));
          if (nodeText && nodeText.includes(text)) {
            paragraphNode = tempNode;
            foundParaId = true;
            break;
          }
        }
        tempNode = tempNode.parentNode;
      }
    }
    
    // Letzter Fallback: Verwende einfach das Element, das den Text enthält (auch wenn es kein Block-Element ist)
    if (!foundParaId && paragraphNode) {
      console.log('[HIGHLIGHT-SAVE] Fallback: Verwende aktuelles Element');
      // Prüfe ob das Element selbst Text enthält
      const nodeText = paragraphNode.textContent || '';
      if (!nodeText || !nodeText.includes(text)) {
        // Suche nach einem Parent, der den Text enthält
        tempNode = paragraphNode.parentNode;
        while (tempNode && tempNode !== document.body) {
          const nodeText2 = tempNode.textContent || '';
          if (nodeText2 && nodeText2.includes(text)) {
            paragraphNode = tempNode;
            foundParaId = true;
            console.log('[HIGHLIGHT-SAVE] Fallback: Parent mit Text gefunden:', tempNode.tagName);
            break;
          }
          tempNode = tempNode.parentNode;
        }
      } else {
        foundParaId = true;
      }
    }
    
    if (!paragraphNode || paragraphNode === document.body || !foundParaId) {
      console.error('[HIGHLIGHT-SAVE] Absatz nicht gefunden. paragraphNode:', paragraphNode, 'foundParaId:', foundParaId);
      throw new Error('Absatz nicht gefunden');
    }
    
    console.log('[HIGHLIGHT-SAVE] Absatz gefunden:', paragraphNode.tagName, paragraphNode.id || paragraphNode.dataset?.index || 'keine ID');
    
    // Hole den vollständigen Text des Absatzes
    // Verwende textContent für konsistente Berechnung (ignoriert HTML-Tags)
    const paragraphText = paragraphNode.textContent || paragraphNode.innerText || '';
    
    console.log('[HIGHLIGHT-SAVE] Paragraph Text Länge:', paragraphText.length);
    console.log('[HIGHLIGHT-SAVE] Selected Text:', text.substring(0, 50) + '...');
    console.log('[HIGHLIGHT-SAVE] Paragraph Index:', paragraphIndex);
    
    // Finde die Position des markierten Textes im Absatz
    // Verwende die Range-Informationen für präzisere Berechnung
    let textStartOffset = -1;
    let textEndOffset = -1;
    
    // Versuche zuerst mit der Range die exakte Position zu finden
    try {
      const range = selectionRangeForContext.cloneRange();
      const paraRange = document.createRange();
      paraRange.selectNodeContents(paragraphNode);
      
      // Berechne Offset relativ zum Absatz
      const startContainer = range.startContainer;
      const startOffset = range.startOffset;
      
      // Erstelle einen TreeWalker um die Position zu berechnen
      const walker = document.createTreeWalker(
        paragraphNode,
        NodeFilter.SHOW_TEXT,
        null,
        false
      );
      
      let currentOffset = 0;
      let node;
      let foundStart = false;
      
      while (node = walker.nextNode()) {
        if (node === startContainer || node.parentNode === startContainer) {
          if (node === startContainer) {
            textStartOffset = currentOffset + startOffset;
            foundStart = true;
          } else if (node.parentNode === startContainer) {
            // Text-Node ist Kind des Start-Containers
            let siblingOffset = 0;
            let sibling = node.previousSibling;
            while (sibling) {
              siblingOffset += (sibling.textContent || '').length;
              sibling = sibling.previousSibling;
            }
            textStartOffset = currentOffset + siblingOffset + startOffset;
            foundStart = true;
          }
          break;
        }
        currentOffset += node.textContent.length;
      }
      
      if (foundStart) {
        textEndOffset = textStartOffset + text.length;
        console.log('[HIGHLIGHT-SAVE] Offsets aus Range berechnet:', textStartOffset, textEndOffset);
      } else {
        // Fallback: Verwende indexOf
        textStartOffset = paragraphText.indexOf(text);
        textEndOffset = textStartOffset + text.length;
        console.log('[HIGHLIGHT-SAVE] Offsets mit indexOf berechnet:', textStartOffset, textEndOffset);
      }
    } catch (e) {
      console.warn('[HIGHLIGHT-SAVE] Fehler bei Range-Berechnung, verwende indexOf:', e);
      textStartOffset = paragraphText.indexOf(text);
      textEndOffset = textStartOffset + text.length;
    }
    
    if (textStartOffset === -1) {
      // Fallback: Versuche mit normalisiertem Text
      const normalizedParagraph = paragraphText.replace(/\s+/g, ' ').trim();
      const normalizedText = text.replace(/\s+/g, ' ').trim();
      const normalizedStart = normalizedParagraph.indexOf(normalizedText);
      
      if (normalizedStart === -1) {
        throw new Error('Textposition im Absatz nicht gefunden');
      }
      
      // Verwende die normalisierte Position als Näherung
      // Zeige Keyword-Eingabe-Dialog (mit Notizen-Feld)
      const result = await showKeywordDialog('Unterstreichung', text);
      if (result === null) {
        // Benutzer hat abgebrochen
        return;
      }
      
      const { keywords, note } = result;
      
      // Ermittle das Datum des Vortrags
      const lectureDate = getCurrentLectureDate(lectureId);
      console.log('[HIGHLIGHT-SAVE] LectureId:', lectureId, 'LectureDate:', lectureDate, '(normalisiert)');
      
      const insertData = {
        user_id: currentUser.id,
        ga_number: lectureId,
        lecture_title: lectureTitle,
        lecture_url: window.location.href,
        paragraph_id: paragraphIndex,
        paragraph_text: paragraphText,
        text_start_offset: normalizedStart,
        text_end_offset: normalizedStart + normalizedText.length,
        color: color,
        personal_note: note || '',
        tags: keywords
      };
      
      // Füge lecture_date hinzu, falls verfügbar
      if (lectureDate) {
        insertData.lecture_date = lectureDate;
        console.log('[HIGHLIGHT-SAVE] Füge lecture_date hinzu:', lectureDate);
      } else {
        console.warn('[HIGHLIGHT-SAVE] Kein lecture_date verfügbar für:', lectureId);
      }
      
      const { data, error } = await supabaseClient
        .from('highlights')
        .insert(insertData)
        .select();
      
      if (error) {
        console.error('Supabase Fehler:', error);
        throw new Error(error.message || 'Datenbankfehler');
      }
      
      showContextNotification('✓ Unterstreichung gespeichert!', 'success');
      
      // Unterstreichung visuell anzeigen und klickbar machen
      if (data && data.length > 0) {
        const savedHighlight = data[0];
        applyHighlightToSelection(selectionRangeForContext, color, savedHighlight.id, lectureId, paragraphIndex);
      } else {
        applyHighlightToSelection(selectionRangeForContext, color);
      }
      
      // MB aktualisieren falls offen (invalidiert Cache und lädt Highlights-Tab neu)
      if (typeof membersPanelActive !== 'undefined' && membersPanelActive) {
        // Invalidiere Cache für Highlights
        if (typeof invalidateMembersCache === 'function') {
          invalidateMembersCache('highlights');
        }
        // Aktualisiere Panel falls offen - aktualisiere auch wenn Tab nicht aktiv ist
        if (typeof updateMembersPanelIfOpen === 'function') {
          await updateMembersPanelIfOpen('highlights', true);
        } else if (typeof loadMembersTab === 'function' && currentMembersTab === 'highlights') {
          // Fallback: Nur aktualisieren wenn Highlights-Tab aktiv ist
          await loadMembersTab('highlights');
        }
      }
      
      return;
    }
    
    // Zeige Keyword-Eingabe-Dialog (mit Notizen-Feld)
    const result = await showKeywordDialog('Unterstreichung', text);
    if (result === null) {
      // Benutzer hat abgebrochen
      return;
    }
    
    const { keywords, note } = result;
    
    // Ermittle das Datum des Vortrags
    const lectureDate = getCurrentLectureDate(lectureId);
    console.log('[HIGHLIGHT-SAVE] LectureId:', lectureId, 'LectureDate:', lectureDate);
    
    const insertData = {
      user_id: currentUser.id,
      ga_number: lectureId,
      lecture_title: lectureTitle,
      lecture_url: window.location.href,
      paragraph_id: paragraphIndex,
      paragraph_text: paragraphText,
      text_start_offset: textStartOffset,
      text_end_offset: textEndOffset,
      color: color,
      personal_note: note || '',
      tags: keywords
    };
    
    // Füge lecture_date hinzu, falls verfügbar
    if (lectureDate) {
      insertData.lecture_date = lectureDate;
      console.log('[HIGHLIGHT-SAVE] Füge lecture_date hinzu:', lectureDate);
    } else {
      console.warn('[HIGHLIGHT-SAVE] Kein lecture_date verfügbar für:', lectureId);
    }
    
    const { data, error } = await supabaseClient
      .from('highlights')
      .insert(insertData)
      .select();
    
    if (error) {
      console.error('Supabase Fehler:', error);
      throw new Error(error.message || 'Datenbankfehler');
    }
    
    showContextNotification('✓ Unterstreichung gespeichert!', 'success');
    
    // Unterstreichung visuell anzeigen und klickbar machen
    if (data && data.length > 0) {
      const savedHighlight = data[0];
      applyHighlightToSelection(selectionRangeForContext, color, savedHighlight.id, lectureId, paragraphIndex);
    } else {
      applyHighlightToSelection(selectionRangeForContext, color);
    }
    
    // MB aktualisieren falls offen (invalidiert Cache und lädt Highlights-Tab neu)
    if (typeof membersPanelActive !== 'undefined' && membersPanelActive) {
      // Invalidiere Cache für Highlights
      if (typeof invalidateMembersCache === 'function') {
        invalidateMembersCache('highlights');
      }
      // Aktualisiere Panel falls offen - aktualisiere auch wenn Tab nicht aktiv ist
      if (typeof updateMembersPanelIfOpen === 'function') {
        await updateMembersPanelIfOpen('highlights', true);
      } else if (typeof loadMembersTab === 'function' && currentMembersTab === 'highlights') {
        // Fallback: Nur aktualisieren wenn Highlights-Tab aktiv ist
        await loadMembersTab('highlights');
      }
    }
  } catch (error) {
    console.error('Fehler beim Speichern der Unterstreichung:', error);
    showContextNotification(`✗ Fehler: ${error.message}`, 'error');
  }
}

/**
 * Unterstreichung visuell auf die Selection anwenden
 * @param {Range} range - Die Textauswahl
 * @param {string} color - Die Farbe der Unterstreichung
 * @param {string} highlightId - Optional: Die ID des gespeicherten Highlights (für Klick-Funktionalität)
 * @param {string} gaNumber - Optional: Die GA-Nummer (für Klick-Funktionalität)
 * @param {string} paragraphId - Optional: Die Paragraph-ID (für Klick-Funktionalität)
 */
function applyHighlightToSelection(range, color = 'blue', highlightId = null, gaNumber = null, paragraphId = null) {
  if (!range) return;
  
  try {
    const highlightColor = getHighlightColor(color);
    const span = document.createElement('span');
    span.className = 'member-highlight';
    span.style.setProperty('text-decoration', 'underline', 'important');
    span.style.setProperty('text-decoration-color', highlightColor, 'important');
    span.style.setProperty('-webkit-text-decoration-color', highlightColor, 'important');
    span.style.setProperty('text-decoration-thickness', '1.5px', 'important');
    span.setAttribute('data-highlight', 'true');
    span.setAttribute('data-highlight-color', color);
    
    // Füge Klick-Funktionalität hinzu, wenn Highlight-ID vorhanden ist
    if (highlightId && gaNumber && paragraphId) {
      span.setAttribute('data-highlight-id', highlightId);
      span.setAttribute('data-ga-number', gaNumber);
      span.setAttribute('data-paragraph-id', paragraphId);
      span.style.setProperty('cursor', 'pointer', 'important');
      span.setAttribute('title', 'Klicken zum Öffnen im Member Panel');
      
      // Event-Listener für Klick hinzufügen
      span.addEventListener('click', function(e) {
        e.stopPropagation();
        e.preventDefault();
        console.log('[HIGHLIGHT-CLICK] Klick auf Unterstreichung:', highlightId, gaNumber, paragraphId);
        // Öffne Members Panel und springe zum Highlight
        if (typeof openMembersPanel === 'function') {
          openMembersPanel().then(() => {
            if (typeof switchMembersTab === 'function') {
              switchMembersTab('highlights').then(() => {
                setTimeout(() => {
                  const targetItem = document.querySelector(`[data-id="${highlightId}"][data-type="highlight"]`);
                  if (targetItem) {
                    // Scrolle nur den Content-Bereich, nicht das gesamte Panel
                    const membersContent = document.querySelector('.members-content');
                    if (membersContent) {
                      const containerRect = membersContent.getBoundingClientRect();
                      const itemRect = targetItem.getBoundingClientRect();
                      const relativeTop = itemRect.top - containerRect.top + membersContent.scrollTop;
                      const containerHeight = membersContent.clientHeight;
                      const itemHeight = itemRect.height;
                      const targetScrollTop = relativeTop - (containerHeight / 2) + (itemHeight / 2);
                      
                      membersContent.scrollTo({
                        top: Math.max(0, targetScrollTop),
                        behavior: 'smooth'
                      });
                    } else {
                      const membersTabContent = document.getElementById('members-tab-content');
                      if (membersTabContent) {
                        const containerRect = membersTabContent.getBoundingClientRect();
                        const itemRect = targetItem.getBoundingClientRect();
                        const relativeTop = itemRect.top - containerRect.top + membersTabContent.scrollTop;
                        const containerHeight = membersTabContent.clientHeight;
                        const itemHeight = itemRect.height;
                        const targetScrollTop = relativeTop - (containerHeight / 2) + (itemHeight / 2);
                        
                        membersTabContent.scrollTo({
                          top: Math.max(0, targetScrollTop),
                          behavior: 'smooth'
                        });
                      }
                    }
                    // Visuelles Highlight
                    targetItem.style.backgroundColor = 'rgba(70, 120, 134, 0.1)';
                    setTimeout(() => {
                      targetItem.style.backgroundColor = '';
                    }, 2000);
                  } else {
                    // Fallback: Verwende jumpToHighlight falls verfügbar
                    if (typeof jumpToHighlight === 'function') {
                      jumpToHighlight(gaNumber, paragraphId, highlightId);
                    } else {
                      console.warn('[HIGHLIGHT-CLICK] jumpToHighlight Funktion nicht verfügbar');
                    }
                  }
                }, 300);
              });
            } else {
              // Fallback: Verwende jumpToHighlight falls verfügbar
              if (typeof jumpToHighlight === 'function') {
                jumpToHighlight(gaNumber, paragraphId, highlightId);
              }
            }
          });
        } else {
          // Fallback: Verwende jumpToHighlight falls verfügbar
          if (typeof jumpToHighlight === 'function') {
            jumpToHighlight(gaNumber, paragraphId, highlightId);
          } else {
            console.warn('[HIGHLIGHT-CLICK] openMembersPanel und jumpToHighlight Funktionen nicht verfügbar');
          }
        }
      });
    }
    
    const contents = range.extractContents();
    span.appendChild(contents);
    range.insertNode(span);
    
    // Stelle sicher, dass Links innerhalb des Highlights die Highlight-Farbe verwenden
    const linksInSpan = span.querySelectorAll('a');
    linksInSpan.forEach(link => {
      link.style.setProperty('text-decoration', 'underline', 'important');
      link.style.setProperty('text-decoration-color', highlightColor, 'important');
      link.style.setProperty('-webkit-text-decoration-color', highlightColor, 'important');
      link.style.setProperty('text-decoration-thickness', '1.5px', 'important');
    });
    
    // Selection aufheben
    const selection = window.getSelection();
    selection.removeAllRanges();
  } catch (e) {
    console.error('Fehler beim Anwenden der Unterstreichung:', e);
    // Unterstreichung nicht möglich
  }
}

/**
 * Gibt die Hex-Farbe basierend auf dem Farbnamen zurück
 */
function getHighlightColor(colorName) {
  const colors = {
    'blue': '#467886',
    'red': '#c62828',
    'yellow': '#ffc107'
  };
  return colors[colorName] || colors['blue'];
}

// Timer für das Verstecken der Untermenüs
let highlightMenuHideTimer = null;
let quoteMenuHideTimer = null;

/**
 * Zeigt das Farbauswahl-Untermenü für Unterstreichungen
 */
function showHighlightColorMenu() {
  // Lösche Timer falls vorhanden
  if (highlightMenuHideTimer) {
    clearTimeout(highlightMenuHideTimer);
    highlightMenuHideTimer = null;
  }
  
  const submenu = document.getElementById('highlight-color-menu');
  if (submenu) {
    // Entferne alle versteckenden Klassen und Styles
    submenu.classList.remove('highlight-submenu-hidden');
    submenu.style.display = 'block';
    submenu.style.visibility = 'visible';
    submenu.style.opacity = '1';
    submenu.style.position = 'absolute';
    submenu.style.left = 'calc(100% + 4px)';
    submenu.style.top = '0';
    submenu.style.zIndex = '10003';
  } else {
    console.warn('[HIGHLIGHT-MENU] Untermenü nicht gefunden!');
  }
}

/**
 * Versteckt das Farbauswahl-Untermenü für Unterstreichungen
 */
function hideHighlightColorMenu() {
  // Lösche vorherigen Timer falls vorhanden
  if (highlightMenuHideTimer) {
    clearTimeout(highlightMenuHideTimer);
  }
  
  const submenu = document.getElementById('highlight-color-menu');
  if (submenu) {
    // Kurze Verzögerung, damit Maus zum Untermenü bewegt werden kann
    highlightMenuHideTimer = setTimeout(() => {
      const submenuCheck = document.getElementById('highlight-color-menu');
      if (submenuCheck) {
        submenuCheck.classList.add('highlight-submenu-hidden');
        submenuCheck.style.display = 'none';
      }
      highlightMenuHideTimer = null;
    }, 200);
  }
}

/**
 * Zeigt das Farbauswahl-Untermenü für Zitate
 */
function showQuoteColorMenu() {
  // Lösche Timer falls vorhanden
  if (quoteMenuHideTimer) {
    clearTimeout(quoteMenuHideTimer);
    quoteMenuHideTimer = null;
  }
  
  const submenu = document.getElementById('quote-color-menu');
  if (submenu) {
    // Entferne alle versteckenden Klassen und Styles
    submenu.classList.remove('quote-submenu-hidden');
    submenu.style.display = 'block';
    submenu.style.visibility = 'visible';
    submenu.style.opacity = '1';
    submenu.style.position = 'absolute';
    submenu.style.left = 'calc(100% + 4px)';
    submenu.style.top = '0';
    submenu.style.zIndex = '10003';
  } else {
    console.warn('[QUOTE-MENU] Untermenü nicht gefunden!');
  }
}

/**
 * Versteckt das Farbauswahl-Untermenü für Zitate
 */
function hideQuoteColorMenu() {
  // Lösche vorherigen Timer falls vorhanden
  if (quoteMenuHideTimer) {
    clearTimeout(quoteMenuHideTimer);
  }
  
  const submenu = document.getElementById('quote-color-menu');
  if (submenu) {
    // Kurze Verzögerung, damit Maus zum Untermenü bewegt werden kann
    quoteMenuHideTimer = setTimeout(() => {
      const submenuCheck = document.getElementById('quote-color-menu');
      if (submenuCheck) {
        submenuCheck.classList.add('quote-submenu-hidden');
        submenuCheck.style.display = 'none';
      }
      quoteMenuHideTimer = null;
    }, 200);
  }
}

/**
 * Notiz aus Context-Menü öffnen
 */
function openContextNote(text, lectureId, lectureTitle) {
  // Öffne MB mit Notizen-Tab
  if (typeof openMembersPanel === 'function') {
    openMembersPanel();
    
    // Warte kurz, dann wechsle zu Notizen-Tab und fülle Text ein
    setTimeout(() => {
      if (typeof switchMembersTab === 'function') {
        currentMembersTab = 'notes';
        
        // Tabs aktualisieren
        document.querySelectorAll('.members-tab').forEach(tab => {
          tab.classList.remove('active');
        });
        const notesTab = Array.from(document.querySelectorAll('.members-tab')).find(t => 
          t.textContent.includes('Notizen')
        );
        if (notesTab) notesTab.classList.add('active');
        
        // Content laden
        loadMembersTab('notes');
        
        // Text ins Textfeld einfügen
        setTimeout(() => {
          const noteContent = document.getElementById('members-note-content');
          if (noteContent) {
            noteContent.value = `Aus [[${lectureId}]]${lectureTitle ? ` - ${lectureTitle}` : ''}:\n\n"${text}"\n\n`;
            noteContent.focus();
          }
        }, 300);
      }
    }, 100);
  } else {
    alert('Mitglieder-Panel nicht verfügbar');
  }
}

/**
 * Absatz-Index aus Selection ermitteln (Format wie Timeline: "1a", "42", "intro")
 * Für Bücher: Extrahiert auch Indizes direkt aus dem Text (Format: " ^yz23gu")
 */
function findParagraphId(range) {
  if (!range) return null;
  
  try {
    let node = range.startContainer;
    
    // SCHRITT 1: Suche nach para- IDs im DOM (für Vorträge)
    while (node && node !== document.body) {
      if (node.nodeType === 1) { // Element node
        // Prüfe ob ID vorhanden (Format: "para-1a", "para-42")
        if (node.id && node.id.startsWith('para-')) {
          // Extrahiere Index (entferne "para-" Präfix)
          return node.id.substring(5); // "para-1a" -> "1a"
        }
      }
      node = node.parentNode;
    }
    
    // SCHRITT 2: Falls keine para- ID gefunden, suche nach Indizes im Text (für Bücher)
    // Starte wieder vom Selection-Container
    node = range.startContainer;
    let parentLevel = 0;
    const maxParentLevels = 10; // Begrenze auf 10 Parent-Levels
    
    // Gehe durch alle Parent-Elemente und suche nach Text mit Indizes
    while (node && node !== document.body && parentLevel < maxParentLevels) {
      let textToSearch = '';
      let searchOffset = 0;
      
      // Sammle Text aus dem Element
      if (node.nodeType === 1) { // Element node
        // Hole Text-Content des Elements
        textToSearch = node.textContent || '';
      } else if (node.nodeType === 3) { // Text node
        // Für Text-Knoten: Hole Text vom Parent-Element
        if (node.parentNode && node.parentNode.nodeType === 1) {
          textToSearch = node.parentNode.textContent || '';
          // Berechne Offset: Wo im Parent-Text befindet sich unser Text-Knoten?
          let offset = 0;
          let sibling = node.previousSibling;
          while (sibling) {
            offset += (sibling.textContent || '').length;
            sibling = sibling.previousSibling;
          }
          searchOffset = offset;
        } else {
          textToSearch = node.textContent || '';
        }
      }
      
      // Suche nach Index im Format " ^yz23gu" (Leerzeichen + ^ + alphanumerisch)
      if (textToSearch) {
        // Suche alle Indizes im Text
        const indexMatches = [];
        let match;
        const indexRegex = /\s+(\^[a-z0-9]+)\b/g;
        
        while ((match = indexRegex.exec(textToSearch)) !== null) {
          indexMatches.push({
            index: match.index,
            id: match[1],
            cleanId: match[1].replace(/^\^/, '')
          });
        }
        
        if (indexMatches.length > 0) {
          // Wenn mehrere Indizes gefunden, wähle den, der am nächsten zur Selection ist
          let bestMatch = indexMatches[0];
          if (indexMatches.length > 1 && searchOffset > 0) {
            // Finde den Index, der am nächsten zur Selection-Position ist
            bestMatch = indexMatches.reduce((closest, current) => {
              const currentDist = Math.abs(current.index - searchOffset);
              const closestDist = Math.abs(closest.index - searchOffset);
              return currentDist < closestDist ? current : closest;
            });
          }
          
          return bestMatch.cleanId;
        }
      }
      
      // Gehe zum nächsten Parent
      node = node.parentNode;
      parentLevel++;
    }
  } catch (err) {
    // Paragraph-Index nicht gefunden
  }
  
  return null;
}

/**
 * GA-Nummer aus URL extrahieren
 */
function extractGAFromURL() {
  const urlParams = new URLSearchParams(window.location.search);
  const ga = urlParams.get('ga');
  if (ga) return ga;
  
  // Versuche aus Hash
  const hash = window.location.hash;
  const match = hash.match(/GA\s?(\d{1,3})/i);
  if (match) return `GA${match[1]}`;
  
  return null;
}

/**
 * Context vor markiertem Text
 */
function getContextBefore(selectedText, maxChars = 100) {
  const fullText = document.body.innerText;
  const index = fullText.indexOf(selectedText);
  if (index === -1) return '';
  
  const start = Math.max(0, index - maxChars);
  return '...' + fullText.substring(start, index).trim();
}

/**
 * Context nach markiertem Text
 */
function getContextAfter(selectedText, maxChars = 100) {
  const fullText = document.body.innerText;
  const index = fullText.indexOf(selectedText);
  if (index === -1) return '';
  
  const end = Math.min(fullText.length, index + selectedText.length + maxChars);
  return fullText.substring(index + selectedText.length, end).trim() + '...';
}

/**
 * Selection highlighten
 */
function highlightContextSelection(color) {
  if (!selectionRangeForContext) return;
  
  try {
    const span = document.createElement('span');
    span.style.backgroundColor = color;
    span.style.transition = 'background-color 2s';
    
    const contents = selectionRangeForContext.extractContents();
    span.appendChild(contents);
    selectionRangeForContext.insertNode(span);
    
    // Fade out
    setTimeout(() => {
      span.style.backgroundColor = 'transparent';
      setTimeout(() => {
        // Unwrap span
        const parent = span.parentNode;
        while (span.firstChild) {
          parent.insertBefore(span.firstChild, span);
        }
        parent.removeChild(span);
      }, 2000);
    }, 500);
  } catch (e) {
    // Highlight nicht möglich
  }
}

/**
 * Zitat visuell auf die Selection anwenden und klickbar machen
 * @param {Range} range - Die Textauswahl
 * @param {string} quoteId - Die ID des gespeicherten Zitats
 * @param {string} gaNumber - Die GA-Nummer
 * @param {string} paragraphId - Die Paragraph-ID
 */
function applyQuoteToSelection(range, quoteId, gaNumber, paragraphId) {
  if (!range) return;
  
  try {
    const span = document.createElement('span');
    span.className = 'member-quote-highlight';
    span.style.setProperty('background-color', 'rgba(70, 120, 134, 0.1)', 'important');
    span.style.setProperty('padding', '2px 0', 'important');
    span.style.setProperty('border-radius', '2px', 'important');
    span.style.setProperty('cursor', 'pointer', 'important');
    span.setAttribute('data-quote-id', quoteId);
    span.setAttribute('data-quote', 'true');
    span.setAttribute('data-ga-reference', gaNumber);
    span.setAttribute('data-paragraph-id', paragraphId);
    span.setAttribute('title', 'Klicken zum Öffnen im Member Panel');
    
    // Event-Listener für Klick hinzufügen
    span.addEventListener('click', function(e) {
      e.stopPropagation();
      e.preventDefault();
      console.log('[QUOTE-CLICK] Klick auf Zitat:', quoteId, gaNumber, paragraphId);
      // Öffne Members Panel und springe zum Zitat
      if (typeof openMembersPanel === 'function') {
        openMembersPanel().then(() => {
          if (typeof switchMembersTab === 'function') {
            switchMembersTab('quotes').then(() => {
              setTimeout(() => {
                const targetItem = document.querySelector(`[data-id="${quoteId}"][data-type="quote"]`);
                if (targetItem) {
                  // Scrolle nur den Content-Bereich, nicht das gesamte Panel
                  const membersContent = document.querySelector('.members-content');
                  if (membersContent) {
                    const containerRect = membersContent.getBoundingClientRect();
                    const itemRect = targetItem.getBoundingClientRect();
                    const relativeTop = itemRect.top - containerRect.top + membersContent.scrollTop;
                    const containerHeight = membersContent.clientHeight;
                    const itemHeight = itemRect.height;
                    const targetScrollTop = relativeTop - (containerHeight / 2) + (itemHeight / 2);
                    
                    membersContent.scrollTo({
                      top: Math.max(0, targetScrollTop),
                      behavior: 'smooth'
                    });
                  } else {
                    const membersTabContent = document.getElementById('members-tab-content');
                    if (membersTabContent) {
                      const containerRect = membersTabContent.getBoundingClientRect();
                      const itemRect = targetItem.getBoundingClientRect();
                      const relativeTop = itemRect.top - containerRect.top + membersTabContent.scrollTop;
                      const containerHeight = membersTabContent.clientHeight;
                      const itemHeight = itemRect.height;
                      const targetScrollTop = relativeTop - (containerHeight / 2) + (itemHeight / 2);
                      
                      membersTabContent.scrollTo({
                        top: Math.max(0, targetScrollTop),
                        behavior: 'smooth'
                      });
                    }
                  }
                  // Visuelles Highlight
                  targetItem.style.backgroundColor = 'rgba(70, 120, 134, 0.1)';
                  setTimeout(() => {
                    targetItem.style.backgroundColor = '';
                  }, 2000);
                }
              }, 300);
            });
          }
        });
      } else {
        console.warn('[QUOTE-CLICK] openMembersPanel Funktion nicht verfügbar');
      }
    });
    
    const contents = range.extractContents();
    span.appendChild(contents);
    range.insertNode(span);
    
    // Selection aufheben
    const selection = window.getSelection();
    selection.removeAllRanges();
    
    console.log('[QUOTE-SELECTION] Zitat-Markierung erfolgreich angewendet und klickbar gemacht');
  } catch (e) {
    console.error('[QUOTE-SELECTION] Fehler beim Anwenden der Zitat-Markierung:', e);
    // Fallback: Normale Highlight-Funktion verwenden
    highlightContextSelection('#ffffcc');
  }
}

/**
 * Keyword-Eingabe-Dialog anzeigen (mit Notizen-Feld)
 */
function showKeywordDialog(type, text) {
  return new Promise((resolve) => {
    // Erstelle Dialog
    const dialog = document.createElement('div');
    dialog.className = 'keyword-dialog-overlay';
    dialog.innerHTML = `
      <div class="keyword-dialog">
        <div class="keyword-dialog-header">
          <h3>${type} speichern</h3>
        </div>
        <div class="keyword-dialog-body">
          <div class="keyword-preview">"${text.substring(0, 100)}${text.length > 100 ? '...' : ''}"</div>
          <label for="keyword-input">Keywords (optional, durch Komma getrennt):</label>
          <input type="text" id="keyword-input" placeholder="z.B. Karma, Reinkarnation, Ätherleib" />
          <div class="keyword-hint">Keywords helfen beim späteren Filtern und Wiederfinden</div>
          <label for="note-input" style="margin-top: 1rem; display: block;">Notiz (optional):</label>
          <textarea id="note-input" rows="4" placeholder="Persönliche Notiz zu diesem ${type.toLowerCase()}..." style="width: 100%; padding: 0.6rem; border: 1px solid var(--border-color); border-radius: 4px; font-family: Georgia, serif; font-size: 0.9rem; background: var(--background-color); color: var(--text-color); box-sizing: border-box; resize: vertical;"></textarea>
        </div>
        <div class="keyword-dialog-footer">
          <button class="keyword-dialog-btn keyword-dialog-cancel">Abbrechen</button>
          <button class="keyword-dialog-btn keyword-dialog-save">Speichern</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Focus auf Input
    const input = dialog.querySelector('#keyword-input');
    setTimeout(() => input.focus(), 100);
    
    // Event Handlers
    const saveBtn = dialog.querySelector('.keyword-dialog-save');
    const cancelBtn = dialog.querySelector('.keyword-dialog-cancel');
    const noteInput = dialog.querySelector('#note-input');
    
    const handleSave = () => {
      const keywords = input.value
        .split(',')
        .map(kw => kw.trim())
        .filter(kw => kw.length > 0);
      const note = noteInput.value.trim();
      dialog.remove();
      resolve({ keywords, note });
    };
    
    const handleCancel = () => {
      dialog.remove();
      resolve(null);
    };
    
    saveBtn.addEventListener('click', handleSave);
    cancelBtn.addEventListener('click', handleCancel);
    
    // Enter zum Speichern (nur wenn nicht in Textarea)
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSave();
      }
    });
    
    // ESC zum Abbrechen
    dialog.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        handleCancel();
      }
    });
    
    // Click auf Overlay schließt Dialog
    dialog.addEventListener('click', (e) => {
      if (e.target === dialog) {
        handleCancel();
      }
    });
  });
}

/**
 * Notification anzeigen
 */
function showContextNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `context-notification context-notification-${type}`;
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

/**
 * Styles für Context-Menü
 */
function addContextMenuStyles() {
  if (document.querySelector('#members-context-menu-styles')) return;
  
  const style = document.createElement('style');
  style.id = 'members-context-menu-styles';
  style.textContent = `
    .members-context-menu {
      position: fixed;
      display: none;
      background: var(--background-color);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      z-index: 10001;
      min-width: 180px;
      overflow: visible;
    }
    
    .context-menu-item {
      display: flex;
      align-items: center;
      padding: 10px 14px;
      cursor: pointer;
      transition: background 0.2s;
      font-size: 0.9rem;
      color: var(--text-color);
    }
    
    .context-menu-item:hover {
      background: var(--accent-color);
      color: white;
    }
    
    .context-menu-text {
      flex: 1;
    }
    
    .context-menu-arrow {
      margin-left: 0.5rem;
      font-size: 0.7rem;
      color: var(--secondary-text);
    }
    
    .highlight-menu-item {
      position: relative;
    }
    
    .context-submenu {
      position: absolute;
      left: calc(100% + 4px);
      top: 0;
      background: var(--background-color);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      min-width: 120px;
      z-index: 10003;
      overflow: visible;
      pointer-events: auto;
    }
    
    .highlight-submenu-hidden {
      display: none !important;
      visibility: hidden !important;
      opacity: 0 !important;
    }
    
    /* Stelle sicher, dass das Untermenü sichtbar bleibt wenn Maus über Parent oder Untermenü ist */
    .highlight-menu-item:hover .context-submenu,
    .highlight-menu-item:hover .highlight-submenu-hidden {
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
    }
    
    .quote-menu-item {
      position: relative;
    }
    
    .quote-submenu-hidden {
      display: none !important;
      visibility: hidden !important;
      opacity: 0 !important;
    }
    
    /* Stelle sicher, dass das Quote-Untermenü sichtbar bleibt wenn Maus über Parent oder Untermenü ist */
    .quote-menu-item:hover .context-submenu,
    .quote-menu-item:hover .quote-submenu-hidden {
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
    }
    
    /* Auch wenn direkt über dem Untermenü gehovert wird */
    .context-submenu:hover {
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
    }
    
    .context-submenu .context-menu-item {
      padding: 8px 12px;
    }
    
    .context-submenu .context-menu-item:hover {
      background: var(--accent-color);
      color: white;
    }
    
    .context-notification {
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 6px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      z-index: 10002;
      font-size: 0.9rem;
      font-family: Georgia, serif;
      animation: slideIn 0.3s ease;
    }
    
    .context-notification-success {
      background: #467886;
      color: white;
    }
    
    .context-notification-error {
      background: #f44336;
      color: white;
    }
    
    .context-notification-info {
      background: #2196F3;
      color: white;
    }
    
    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    
    @keyframes slideOut {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(100%);
        opacity: 0;
      }
    }
    
    /* Dark Mode */
    body.dark-mode .members-context-menu {
      background: var(--dark-background-color);
      border-color: var(--dark-border-color);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    
    body.dark-mode .context-menu-item {
      color: var(--dark-text-color);
    }
    
    body.dark-mode .context-menu-item:hover {
      background: var(--dark-accent-color);
      color: white;
    }
    
    /* Keyword Dialog */
    .keyword-dialog-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10003;
      animation: fadeIn 0.2s ease;
    }
    
    .keyword-dialog {
      background: var(--background-color);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
      width: 90%;
      max-width: 500px;
      font-family: Georgia, serif;
    }
    
    .keyword-dialog-header {
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--border-color);
    }
    
    .keyword-dialog-header h3 {
      margin: 0;
      font-size: 1.1rem;
      color: var(--heading-color);
      font-weight: normal;
    }
    
    .keyword-dialog-body {
      padding: 1.25rem;
    }
    
    .keyword-preview {
      font-style: italic;
      color: var(--secondary-text);
      font-size: 0.85rem;
      margin-bottom: 1rem;
      padding: 0.75rem;
      background: rgba(0, 0, 0, 0.03);
      border-radius: 4px;
      line-height: 1.4;
    }
    
    .keyword-dialog-body label {
      display: block;
      margin-bottom: 0.5rem;
      color: var(--text-color);
      font-size: 0.9rem;
      font-weight: 600;
    }
    
    .keyword-dialog-body input {
      width: 100%;
      padding: 0.6rem;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      font-family: Georgia, serif;
      font-size: 0.9rem;
      background: var(--background-color);
      color: var(--text-color);
      box-sizing: border-box;
    }
    
    .keyword-dialog-body input:focus {
      outline: none;
      border-color: var(--accent-color);
    }
    
    .keyword-hint {
      margin-top: 0.5rem;
      font-size: 0.75rem;
      color: var(--secondary-text);
    }
    
    .keyword-dialog-footer {
      padding: 1rem 1.25rem;
      border-top: 1px solid var(--border-color);
      display: flex;
      gap: 0.75rem;
      justify-content: flex-end;
    }
    
    .keyword-dialog-btn {
      padding: 0.5rem 1.25rem;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      font-family: Georgia, serif;
      font-size: 0.9rem;
      cursor: pointer;
      transition: all 0.2s;
    }
    
    .keyword-dialog-cancel {
      background: transparent;
      color: var(--text-color);
    }
    
    .keyword-dialog-cancel:hover {
      background: rgba(0, 0, 0, 0.05);
    }
    
    .keyword-dialog-save {
      background: var(--accent-color);
      color: white;
      border-color: var(--accent-color);
    }
    
    .keyword-dialog-save:hover {
      background: #3a6270;
    }
    
    /* Dark Mode für Keyword Dialog */
    body.dark-mode .keyword-dialog {
      background: var(--dark-background-color);
      border-color: var(--dark-border-color);
    }
    
    body.dark-mode .keyword-dialog-header {
      border-bottom-color: var(--dark-border-color);
    }
    
    body.dark-mode .keyword-dialog-header h3 {
      color: var(--dark-heading-color);
    }
    
    body.dark-mode .keyword-dialog-body label {
      color: var(--dark-text-color);
    }
    
    body.dark-mode .keyword-dialog-body input,
    body.dark-mode .keyword-dialog-body textarea {
      background: var(--dark-background-color);
      color: var(--dark-text-color);
      border-color: var(--dark-border-color);
    }
    
    body.dark-mode .keyword-dialog-body input:focus,
    body.dark-mode .keyword-dialog-body textarea:focus {
      border-color: var(--dark-accent-color);
      outline: none;
    }
    
    .keyword-dialog-body textarea {
      width: 100%;
      padding: 0.6rem;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      font-family: Georgia, serif;
      font-size: 0.9rem;
      background: var(--background-color);
      color: var(--text-color);
      box-sizing: border-box;
      resize: vertical;
    }
    
    .keyword-dialog-body textarea:focus {
      outline: none;
      border-color: var(--accent-color);
    }
    
    body.dark-mode .keyword-preview {
      background: rgba(255, 255, 255, 0.05);
      color: var(--dark-secondary-text);
    }
    
    body.dark-mode .keyword-dialog-footer {
      border-top-color: var(--dark-border-color);
    }
    
    body.dark-mode .keyword-dialog-cancel {
      color: var(--dark-text-color);
    }
    
    body.dark-mode .keyword-dialog-cancel:hover {
      background: rgba(255, 255, 255, 0.1);
    }
    
    body.dark-mode .keyword-dialog-save {
      background: var(--dark-accent-color);
      border-color: var(--dark-accent-color);
    }
    
    body.dark-mode .keyword-dialog-save:hover {
      background: #5a8fa0;
    }
  `;
  document.head.appendChild(style);
}

// Global verfügbar machen
window.initMembersContextMenu = initMembersContextMenu;
window.contextMenuAction = contextMenuAction;
window.showHighlightColorMenu = showHighlightColorMenu;
window.hideHighlightColorMenu = hideHighlightColorMenu;
window.showQuoteColorMenu = showQuoteColorMenu;
window.hideQuoteColorMenu = hideQuoteColorMenu;
window.getHighlightColor = getHighlightColor;

// Auto-Init wenn DOM geladen - mit Verzögerung
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(initMembersContextMenu, 500);
  });
} else {
  setTimeout(initMembersContextMenu, 500);
}

