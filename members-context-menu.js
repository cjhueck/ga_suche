// ============================================
// GA-Suche - Rechtsklick Kontextmenü für Mitglieder
// Bookmark, Zitat, Notiz per Rechtsklick
// ============================================

let contextMenu = null;
let selectedTextForContext = '';
let selectionRangeForContext = null;
let selectionInSidePanel = false; // Flag: Auswahl ist im Side Panel (erweiterte Suche/Index)

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
    <div class="context-menu-item quote-menu-item" onmouseenter="showQuoteColorMenu()" onmouseleave="hideQuoteColorMenu()">
      <span class="context-menu-text">Anstreichen</span>
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
    <div class="context-menu-item note-menu-item" onmouseenter="showNoteColorMenu()" onmouseleave="hideNoteColorMenu()">
      <span class="context-menu-text">Notiz erstellen</span>
      <span class="context-menu-arrow">▶</span>
      <div id="note-color-menu" class="context-submenu note-submenu-hidden" onmouseenter="showNoteColorMenu()" onmouseleave="hideNoteColorMenu()">
        <div class="context-menu-item" onclick="contextMenuAction('note', 'blue')" style="border-left: 3px solid #467886;">
          <span class="context-menu-text">Blau</span>
        </div>
        <div class="context-menu-item" onclick="contextMenuAction('note', 'red')" style="border-left: 3px solid #c62828;">
          <span class="context-menu-text">Rot</span>
        </div>
        <div class="context-menu-item" onclick="contextMenuAction('note', 'yellow')" style="border-left: 3px solid #ffc107;">
          <span class="context-menu-text">Gelb</span>
        </div>
      </div>
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
  const summaryContent = document.getElementById('summary-content');
  const target = e.target;
  
  // Prüfe ob Klick im relevanten Bereich
  // WICHTIG: summary-content ZUERST prüfen, da es innerhalb von main liegen kann
  const isInSummaryContent = summaryContent && (summaryContent.contains(target) || summaryContent === target);
  const isInViewer = viewer && (viewer.contains(target) || viewer === target);
  const isInMain = main && (main.contains(target) || main === target);
  
  // Setze Flag ob Auswahl im Side Panel ist (summary-content hat Priorität)
  selectionInSidePanel = isInSummaryContent;
  
  console.log('[CONTEXT-MENU] Selection check:', { isInSummaryContent, isInViewer, isInMain, selectionInSidePanel });
  
  // Context-Menü im Side Panel ist jetzt ERLAUBT
  // Die Daten (data-lecture-id, data-paragraph-id, data-index) werden aus dem DOM extrahiert
  
  // Prüfe ob Text lang genug ist UND ob wir in einem relevanten Bereich sind
  // WICHTIG: summary-content ist NICHT innerhalb von main, daher separat prüfen
  if (selectedText.length < 3 || (!isInViewer && !isInMain && !isInSummaryContent)) {
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
  // Bei Side Panel: ZUERST aus data-paragraph-id Attribut lesen (nicht aus dem Text!)
  let paragraphIndex;
  if (selectionInSidePanel) {
    // Im Side Panel: Verwende die DOM-Attribute, nicht die Text-Indizes
    paragraphIndex = findParagraphIdFromSidePanel(selectionRangeForContext);
    console.log('[CONTEXT-MENU] Side Panel - Paragraph-Index aus DOM:', paragraphIndex);
  }
  // Fallback: Verwende die Text-basierte Suche (für Main Viewer und wenn Side Panel nichts findet)
  if (!paragraphIndex) {
    paragraphIndex = findParagraphId(selectionRangeForContext);
  }
  
  // Hole vollständige Lecture-ID (GA058/01) statt nur GA-Nummer
  // NEU: Bei Side Panel (erweiterte Suche/Index) aus window.currentSidePanelLectureId holen
  // ODER: Aus data-lecture-id Attribut im DOM (falls globale Variable nicht gesetzt)
  console.log('[CONTEXT-MENU] contextMenuAction - selectionInSidePanel:', selectionInSidePanel);
  console.log('[CONTEXT-MENU] contextMenuAction - window.currentSidePanelLectureId:', window.currentSidePanelLectureId);
  
  let lectureId;
  if (selectionInSidePanel) {
    // 1. Zuerst aus globaler Variable versuchen
    if (typeof window.currentSidePanelLectureId !== 'undefined' && window.currentSidePanelLectureId) {
      lectureId = window.currentSidePanelLectureId;
      console.log('[CONTEXT-MENU] Lecture-ID aus Side Panel (global):', lectureId);
    }
    
    // 2. Falls nicht vorhanden: Aus DOM-Attribut data-lecture-id auslesen
    if (!lectureId && selectionRangeForContext) {
      lectureId = findLectureIdFromDOM(selectionRangeForContext);
      console.log('[CONTEXT-MENU] Lecture-ID aus DOM-Attribut:', lectureId);
    }
  }
  
  // 3. Fallback: Aus Main Viewer oder URL
  if (!lectureId) {
    lectureId = (typeof currentLectureData !== 'undefined' && currentLectureData?.ID) 
      ? currentLectureData.ID 
      : extractGAFromURL();
    console.log('[CONTEXT-MENU] Lecture-ID aus Main Viewer/URL:', lectureId);
  }
  const gaNumber = lectureId ? lectureId.split('/')[0] : 'Unbekannt';
  const lectureTitle = selectionInSidePanel 
    ? (typeof window.currentSidePanelLectureTitle !== 'undefined' ? window.currentSidePanelLectureTitle : '')
    : (currentContext?.lectureTitle || '');
  
  console.log('[CONTEXT-MENU] Final lectureId:', lectureId, 'gaNumber:', gaNumber);
  
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
      const noteColor = extraData || 'blue'; // Standard: blau
      openContextNote(selectedTextForContext, lectureId, lectureTitle, paragraphIndex, noteColor);
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
    
    const { keywords, groups, note } = result;
    
    const insertData = {
      user_id: currentUser.id,
      ga_number: lectureId,
      lecture_title: lectureTitle,
      paragraph_id: paragraphIndex,
      paragraph_text: text,
      note: note || '',
      tags: keywords,
      groups: groups || []
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
    
    // NEU: Prüfe ob wir im Members Panel Volltext sind (item-full-paragraph)
    const fullParagraphContainer = paragraphNode?.closest('.item-full-paragraph');
    const isInMembersPanelFullText = fullParagraphContainer && fullParagraphContainer.classList.contains('show');
    
    if (isInMembersPanelFullText) {
      console.log('[QUOTE-SAVE] Members Panel Volltext erkannt');
      // Im Members Panel: Verwende das full-paragraph-text div als Container
      const textContainer = fullParagraphContainer.querySelector('.full-paragraph-text');
      if (textContainer) {
        paragraphNode = textContainer;
        console.log('[QUOTE-SAVE] Verwende full-paragraph-text Container');
      } else {
        paragraphNode = fullParagraphContainer;
        console.log('[QUOTE-SAVE] Verwende item-full-paragraph Container');
      }
    }
    
    // Für Bücher: Suche zuerst nach para- ID oder data-index
    // (überspringe bei Members Panel Volltext - dort haben wir bereits den richtigen Container)
    let foundParaId = isInMembersPanelFullText; // Bei Members Panel schon gefunden
    let tempNode = paragraphNode;
    
    if (!isInMembersPanelFullText) {
      while (tempNode && tempNode !== document.body) {
        if (tempNode.nodeType === 1) { // Element node
          // Prüfe ob para- ID vorhanden (für Vorträge und Bücher)
          if (tempNode.id && tempNode.id.startsWith('para-')) {
            console.log('[QUOTE-SAVE] para- ID gefunden:', tempNode.id);
            paragraphNode = tempNode;
            foundParaId = true;
            break;
          }
          // NEU: Prüfe ob adv-para- ID vorhanden (für erweiterte Suche im Side Panel)
          if (tempNode.id && tempNode.id.startsWith('adv-para-')) {
            console.log('[QUOTE-SAVE] adv-para- ID gefunden:', tempNode.id);
            paragraphNode = tempNode;
            foundParaId = true;
            break;
          }
          // NEU: Prüfe ob .paragraph Klasse mit data-paragraph-id vorhanden (Side Panel)
          if (tempNode.classList && tempNode.classList.contains('paragraph') && tempNode.hasAttribute('data-paragraph-id')) {
            console.log('[QUOTE-SAVE] .paragraph mit data-paragraph-id gefunden:', tempNode.getAttribute('data-paragraph-id'));
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
    }
    
    // Falls keine para- ID gefunden, suche nach dem Absatz-Element (p, div, etc.)
    // (überspringe bei Members Panel Volltext)
    if (!foundParaId && !isInMembersPanelFullText) {
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
    // (überspringe bei Members Panel Volltext)
    if (!foundParaId && paragraphNode && !isInMembersPanelFullText) {
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
    
    const { keywords, groups, note } = result;
    
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
      groups: groups || [],
      is_public: false
    };
    
    // marker_color speichern (blue/red/yellow erlaubt)
    if (color && (color === 'blue' || color === 'red' || color === 'yellow')) {
      insertData.marker_color = color;
    }
    
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
        
        // MB aktualisieren - IMMER Cache invalidieren
        if (typeof invalidateMembersCache === 'function') {
          invalidateMembersCache('quotes');
        }
        // Panel aktualisieren falls offen
        if (typeof membersPanelActive !== 'undefined' && membersPanelActive) {
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
      const markerColor = savedQuote.marker_color || null;
      applyQuoteToSelection(selectionRangeForContext, savedQuote.id, lectureId, paragraphIndex, markerColor);
    } else {
      highlightContextSelection('#ffffcc');
    }
    
    // MB aktualisieren - IMMER Cache invalidieren
    if (typeof invalidateMembersCache === 'function') {
      invalidateMembersCache('quotes');
    }
    // Panel aktualisieren falls offen
    if (typeof membersPanelActive !== 'undefined' && membersPanelActive) {
      if (typeof updateMembersPanelIfOpen === 'function') {
        await updateMembersPanelIfOpen('quotes', true);
      } else if (typeof loadMembersTab === 'function' && currentMembersTab === 'quotes') {
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
    
    // NEU: Prüfe ob wir im Members Panel Volltext sind (item-full-paragraph)
    const fullParagraphContainer = paragraphNode?.closest('.item-full-paragraph');
    const isInMembersPanelFullText = fullParagraphContainer && fullParagraphContainer.classList.contains('show');
    
    if (isInMembersPanelFullText) {
      console.log('[HIGHLIGHT-SAVE] Members Panel Volltext erkannt');
      // Im Members Panel: Verwende das full-paragraph-text div als Container
      const textContainer = fullParagraphContainer.querySelector('.full-paragraph-text');
      if (textContainer) {
        paragraphNode = textContainer;
        console.log('[HIGHLIGHT-SAVE] Verwende full-paragraph-text Container');
      } else {
        paragraphNode = fullParagraphContainer;
        console.log('[HIGHLIGHT-SAVE] Verwende item-full-paragraph Container');
      }
    }
    
    // Für Bücher: Suche zuerst nach para- ID oder data-index
    // (überspringe bei Members Panel Volltext - dort haben wir bereits den richtigen Container)
    let foundParaId = isInMembersPanelFullText; // Bei Members Panel schon gefunden
    let tempNode = paragraphNode;
    
    if (!isInMembersPanelFullText) {
      while (tempNode && tempNode !== document.body) {
        if (tempNode.nodeType === 1) { // Element node
          // Prüfe ob para- ID vorhanden (für Vorträge und Bücher)
          if (tempNode.id && tempNode.id.startsWith('para-')) {
            console.log('[HIGHLIGHT-SAVE] para- ID gefunden:', tempNode.id);
            paragraphNode = tempNode;
            foundParaId = true;
            break;
          }
          // NEU: Prüfe ob adv-para- ID vorhanden (für erweiterte Suche im Side Panel)
          if (tempNode.id && tempNode.id.startsWith('adv-para-')) {
            console.log('[HIGHLIGHT-SAVE] adv-para- ID gefunden:', tempNode.id);
            paragraphNode = tempNode;
            foundParaId = true;
            break;
          }
          // NEU: Prüfe ob .paragraph Klasse mit data-paragraph-id vorhanden (Side Panel)
          if (tempNode.classList && tempNode.classList.contains('paragraph') && tempNode.hasAttribute('data-paragraph-id')) {
            console.log('[HIGHLIGHT-SAVE] .paragraph mit data-paragraph-id gefunden:', tempNode.getAttribute('data-paragraph-id'));
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
    }
    
    // Falls keine para- ID gefunden, suche nach dem Absatz-Element (p, div, etc.)
    // (überspringe bei Members Panel Volltext)
    if (!foundParaId && !isInMembersPanelFullText) {
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
    // (überspringe bei Members Panel Volltext)
    if (!foundParaId && paragraphNode && !isInMembersPanelFullText) {
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
      
      const { keywords, groups, note } = result;
      
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
        tags: keywords,
        groups: groups || []
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
      
    // MB aktualisieren - IMMER Cache invalidieren und Panel aktualisieren
    // Invalidiere Cache für Highlights
    if (typeof invalidateMembersCache === 'function') {
      invalidateMembersCache('highlights');
    }
    // Aktualisiere Panel falls offen
    if (typeof membersPanelActive !== 'undefined' && membersPanelActive) {
      if (typeof updateMembersPanelIfOpen === 'function') {
        await updateMembersPanelIfOpen('highlights', true);
      } else if (typeof loadMembersTab === 'function' && currentMembersTab === 'highlights') {
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
    
    const { keywords, groups, note } = result;
    
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
      tags: keywords,
      groups: groups || []
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
    
    // MB aktualisieren - IMMER Cache invalidieren
    if (typeof invalidateMembersCache === 'function') {
      invalidateMembersCache('highlights');
    }
    // Panel aktualisieren falls offen
    if (typeof membersPanelActive !== 'undefined' && membersPanelActive) {
      if (typeof updateMembersPanelIfOpen === 'function') {
        await updateMembersPanelIfOpen('highlights', true);
      } else if (typeof loadMembersTab === 'function' && currentMembersTab === 'highlights') {
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

// Timer für Notiz-Untermenü
let noteMenuHideTimer = null;

/**
 * Zeigt das Notiz-Farben-Untermenü
 */
function showNoteColorMenu() {
  // Lösche Timer falls vorhanden
  if (noteMenuHideTimer) {
    clearTimeout(noteMenuHideTimer);
    noteMenuHideTimer = null;
  }
  
  const submenu = document.getElementById('note-color-menu');
  if (submenu) {
    submenu.classList.remove('note-submenu-hidden');
    submenu.style.display = 'block';
    submenu.style.visibility = 'visible';
    submenu.style.opacity = '1';
    submenu.style.position = 'absolute';
    submenu.style.left = 'calc(100% + 4px)';
    submenu.style.top = '0';
  }
}

/**
 * Versteckt das Notiz-Farben-Untermenü
 */
function hideNoteColorMenu() {
  // Lösche vorherigen Timer falls vorhanden
  if (noteMenuHideTimer) {
    clearTimeout(noteMenuHideTimer);
  }
  
  const submenu = document.getElementById('note-color-menu');
  if (submenu) {
    noteMenuHideTimer = setTimeout(() => {
      const submenuCheck = document.getElementById('note-color-menu');
      if (submenuCheck) {
        submenuCheck.classList.add('note-submenu-hidden');
        submenuCheck.style.display = 'none';
      }
      noteMenuHideTimer = null;
    }, 200);
  }
}

/**
 * Notiz aus Context-Menü direkt speichern
 */
async function openContextNote(text, lectureId, lectureTitle, paragraphId = null, color = 'blue') {
  console.log('[MB-NOTE-SAVE] openContextNote aufgerufen:', {
    text: text.substring(0, 50) + '...',
    lectureId,
    lectureTitle,
    paragraphId,
    color
  });
  
  // Prüfe ob createNote verfügbar ist
  if (typeof createNote !== 'function') {
    alert('Fehler: Notiz-Funktion nicht verfügbar. Bitte Seite neu laden.');
    return;
  }
  
  // Berechne Text-Offsets falls möglich (auch über mehrere Absätze)
  let textStartOffset = null;
  let textEndOffset = null;
  let paragraphText = null;
  
  if (paragraphId && selectionRangeForContext) {
    try {
      // NEU: Prüfe ob wir im Members Panel Volltext sind (item-full-paragraph)
      let paragraphElement = null;
      const containerNode = selectionRangeForContext.commonAncestorContainer;
      const elementNode = containerNode.nodeType === Node.ELEMENT_NODE ? containerNode : containerNode.parentElement;
      const fullParagraphContainer = elementNode?.closest('.item-full-paragraph');
      const isInMembersPanelFullText = fullParagraphContainer && fullParagraphContainer.classList.contains('show');
      
      if (isInMembersPanelFullText) {
        console.log('[MB-NOTE-SAVE] Members Panel Volltext erkannt');
        // Im Members Panel: Verwende das full-paragraph-text div als Container
        const textContainer = fullParagraphContainer.querySelector('.full-paragraph-text');
        paragraphElement = textContainer || fullParagraphContainer;
      } else {
        // Standard: Suche nach para- Element
        paragraphElement = document.getElementById('para-' + paragraphId);
      }
      
      if (paragraphElement) {
        // Prüfe ob die Selektion über mehrere Absätze geht
        const range = selectionRangeForContext;
        const startContainer = range.startContainer;
        const endContainer = range.endContainer;
        
        // Finde Start- und End-Paragraph (bei Members Panel gibt es keine Multi-Paragraph Selektion)
        let startPara = null;
        let endPara = null;
        let isMultiParagraph = false;
        
        if (!isInMembersPanelFullText) {
          startPara = startContainer.nodeType === Node.TEXT_NODE 
            ? startContainer.parentElement.closest('[id^="para-"]')
            : startContainer.closest('[id^="para-"]');
          endPara = endContainer.nodeType === Node.TEXT_NODE 
            ? endContainer.parentElement.closest('[id^="para-"]')
            : endContainer.closest('[id^="para-"]');
          
          isMultiParagraph = startPara && endPara && startPara !== endPara;
        }
        
        if (isMultiParagraph) {
          console.log('[MB-CONTEXT] Multi-Paragraph Selektion erkannt');
          
          // Sammle Text aller betroffenen Absätze (vom Start-Paragraph aus)
          const contentContainer = paragraphElement.closest('.lecture-content, .text-content, article, main') 
            || paragraphElement.parentElement;
          const allParagraphs = contentContainer.querySelectorAll('[id^="para-"]');
          
          let collecting = false;
          let combinedText = '';
          let foundEnd = false;
          let parasInSelection = [];
          
          for (const para of allParagraphs) {
            if (para === startPara) {
              collecting = true;
            }
            
            if (collecting) {
              parasInSelection.push(para);
              combinedText += para.textContent;
              
              if (para === endPara) {
                foundEnd = true;
                break;
              }
            }
          }
          
          if (foundEnd) {
            paragraphText = combinedText;
            
            // Berechne Start-Offset im Start-Paragraph
            const startWalker = document.createTreeWalker(startPara, NodeFilter.SHOW_TEXT, null, false);
            let startCharCount = 0;
            let startNode;
            
            while (startNode = startWalker.nextNode()) {
              if (startNode === startContainer || startNode.contains(startContainer) || startContainer.contains(startNode)) {
                textStartOffset = startCharCount + range.startOffset;
                break;
              }
              startCharCount += startNode.textContent.length;
            }
            
            // Berechne End-Offset durch Durchlaufen aller Absätze
            if (textStartOffset !== null) {
              let totalCharCount = 0;
              let foundEndOffset = false;
              
              // Sammle alle Textknoten aller Absätze in Reihenfolge
              for (const para of parasInSelection) {
                const endWalker = document.createTreeWalker(para, NodeFilter.SHOW_TEXT, null, false);
                let endNode;
                
                while (endNode = endWalker.nextNode()) {
                  // Prüfe ob dies der End-Container ist (verschiedene Möglichkeiten)
                  const isEndNode = endNode === endContainer || 
                                    endNode === range.endContainer ||
                                    (endContainer.nodeType !== Node.TEXT_NODE && endContainer.contains(endNode));
                  
                  if (isEndNode) {
                    // Berechne den Offset innerhalb dieses Knotens
                    let offsetInNode = range.endOffset;
                    // Wenn endContainer ein Element ist, ist endOffset die Kind-Position
                    if (range.endContainer.nodeType !== Node.TEXT_NODE) {
                      offsetInNode = endNode.textContent.length;
                    }
                    textEndOffset = totalCharCount + offsetInNode;
                    foundEndOffset = true;
                    console.log('[MB-CONTEXT] End-Knoten gefunden, totalCharCount:', totalCharCount, 'offsetInNode:', offsetInNode);
                    break;
                  }
                  // Addiere Länge dieses Knotens
                  totalCharCount += endNode.textContent.length;
                }
                
                if (foundEndOffset) break;
              }
              
              // Fallback: Berechne Länge aus dem Range direkt
              if (!foundEndOffset || textEndOffset === null) {
                // Verwende Range.toString().length für exakte Länge
                const rangeText = range.toString();
                textEndOffset = textStartOffset + rangeText.length;
                console.log('[MB-CONTEXT] Fallback: Range.toString().length =', rangeText.length);
              }
              
              console.log('[MB-CONTEXT] Multi-Para Offsets (final):', textStartOffset, '-', textEndOffset);
            }
          }
        } else {
          // Einzelner Paragraph
          paragraphText = paragraphElement.textContent;
          
          // Finde den Offset des markierten Texts innerhalb des Paragraphs
          const textIndex = paragraphText.indexOf(text);
          if (textIndex !== -1) {
            textStartOffset = textIndex;
            textEndOffset = textIndex + text.length;
          }
        }
      }
    } catch (err) {
      console.warn('[MB-CONTEXT] Fehler beim Ermitteln der Text-Offsets:', err);
    }
  }
  
  // Zeige Modal für Keywords
  const dialogResult = await showContextNoteDialog(text, color);
  
  if (dialogResult === null) {
    // Benutzer hat abgebrochen
    return;
  }
  
  const { groups, keywords, selectedColor } = dialogResult;
  const tags = keywords
    .split(',')
    .map(kw => kw.trim())
    .filter(kw => kw.length > 0);
  const groupsArray = groups
    .split(',')
    .map(g => g.trim().toUpperCase())
    .filter(g => g.length > 0);
  
  // Erstelle Content mit GA-Referenz für die Extraktion (vollständige Vortragsnummer inkl. /Vortrag)
  const gaRef = lectureId ? `[[${lectureId}]]` : '';
  let content = `"${text}"\n\n${gaRef}`;
  
  // Füge Tags hinzu
  if (tags.length > 0) {
    const tagsString = tags.map(tag => `#${tag}`).join(' ');
    content = content + '\n\n' + tagsString;
  }
  
  const title = text.substring(0, 50);
  
  // Hole Vortragsdatum falls verfügbar
  let lectureDate = null;
  if (lectureId && typeof getCurrentLectureDate === 'function') {
    lectureDate = getCurrentLectureDate(lectureId);
  }
  
  // Speichere Notiz mit Gruppen
  console.log('[MB-NOTE-SAVE] Speichere Notiz mit:', { paragraphId, textStartOffset, textEndOffset, selectedColor, groupsArray });
  const result = await createNote(title, content, false, paragraphId, paragraphText, textStartOffset, textEndOffset, lectureDate, tags.length > 0 ? tags : null, selectedColor, groupsArray.length > 0 ? groupsArray : null);
  
  console.log('[MB-NOTE-SAVE] Ergebnis:', result);
  
  if (result.success) {
    showContextNotification('✓ Notiz gespeichert!', 'success');
    
    // IMMER Cache invalidieren für Notizen
    if (typeof invalidateMembersCache === 'function') {
      invalidateMembersCache('notes');
    }
    
    // Füge Bookmark-Icon im Main Viewer hinzu
    console.log('[MB-NOTE-SAVE] Prüfe Icon-Hinzufügung:', { paragraphId, hasData: !!result.data });
    if (paragraphId && result.data) {
      addNoteBookmarkToViewer(paragraphId, result.data, selectedColor);
    } else {
      console.log('[MB-NOTE-SAVE] Kein Icon hinzugefügt - paragraphId:', paragraphId, 'result.data:', result.data);
    }
    
    // Öffne Members Panel und zeige Notizen-Tab
    if (typeof openMembersPanel === 'function') {
      openMembersPanel();
      
      // Wechsle zum Notizen-Tab und lade neu
      setTimeout(() => {
        if (typeof switchMembersTab === 'function') {
          switchMembersTab('notes');
        }
        // Lade Notizen neu
        if (typeof loadSavedNotes === 'function') {
          loadSavedNotes();
        }
      }, 200);
    }
  } else {
    showContextNotification('✗ Fehler beim Speichern: ' + result.error, 'error');
  }
}

/**
 * Fügt ein Bookmark-Icon für eine Notiz im Main Viewer hinzu
 */
function addNoteBookmarkToViewer(paragraphId, noteData, color) {
  console.log('[MB-NOTE-VIEWER] addNoteBookmarkToViewer aufgerufen:', paragraphId, noteData, color);
  
  const paraElement = document.getElementById(`para-${paragraphId}`);
  if (!paraElement) {
    console.log('[MB-NOTE-VIEWER] Element para-' + paragraphId + ' nicht gefunden');
    return;
  }
  
  console.log('[MB-NOTE-VIEWER] Element gefunden:', paraElement.tagName);
  
  // Prüfe ob Icon bereits vorhanden ist
  let targetElement = paraElement;
  let existingIndicator = paraElement.querySelector('.bookmark-note-indicator');
  
  // Bei Büchern: para- IDs sind in versteckten Spans, finde das Parent-Element
  if (paraElement.style.display === 'none' || paraElement.tagName.toLowerCase() === 'span') {
    let parent = paraElement.parentElement;
    while (parent && parent !== document.body) {
      const tagName = parent.tagName.toLowerCase();
      if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
        targetElement = parent;
        existingIndicator = parent.querySelector('.bookmark-note-indicator');
        break;
      }
      parent = parent.parentElement;
    }
  }
  
  if (existingIndicator) return; // Bereits vorhanden
  
  // Hole Farbe und Text-Offset
  const noteColorHex = typeof getNoteColor === 'function' ? getNoteColor(color) : '#467886';
  const noteId = noteData.id || noteData[0]?.id;
  const textStartOffset = noteData.text_start_offset;
  
  // Erstelle Bookmark-Icon
  const indicator = document.createElement('span');
  indicator.className = 'bookmark-note-indicator';
  indicator.setAttribute('data-para-id', paragraphId);
  indicator.setAttribute('data-note-id', noteId);
  indicator.style.color = noteColorHex;
  indicator.style.cursor = 'pointer';
  indicator.title = 'Notiz vorhanden - Klick zum Öffnen';
  indicator.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
    </svg>
  `;
  indicator.onclick = (e) => {
    e.stopPropagation();
    e.preventDefault();
    if (typeof jumpToNoteById === 'function') {
      jumpToNoteById(noteId);
    }
  };
  
  // Stelle sicher, dass targetElement relativ positioniert ist
  targetElement.style.position = 'relative';
  
  // Positioniere das Icon absolut links neben dem Absatz (wie bei Zitaten)
  if (textStartOffset !== null && textStartOffset !== undefined) {
    try {
      const elementText = targetElement.textContent;
      
      if (elementText && elementText.length > textStartOffset) {
        // Erstelle einen Range, um die Position zu finden
        const range = document.createRange();
        const walker = document.createTreeWalker(
          targetElement,
          NodeFilter.SHOW_TEXT,
          null,
          false
        );
        
        let currentOffset = 0;
        let targetNode = null;
        let targetOffset = 0;
        let node;
        
        // Finde den Text-Knoten, der den text_start_offset enthält
        while (node = walker.nextNode()) {
          const nodeLength = node.textContent.length;
          if (currentOffset + nodeLength > textStartOffset) {
            targetNode = node;
            targetOffset = textStartOffset - currentOffset;
            break;
          }
          currentOffset += nodeLength;
        }
        
        if (targetNode) {
          try {
            range.setStart(targetNode, Math.min(targetOffset, targetNode.textContent.length));
            range.setEnd(targetNode, Math.min(targetOffset, targetNode.textContent.length));
            
            // Erstelle einen unsichtbaren Marker-Span
            const marker = document.createElement('span');
            marker.style.display = 'inline';
            marker.style.width = '0';
            marker.style.height = '0';
            marker.style.visibility = 'hidden';
            marker.style.pointerEvents = 'none';
            marker.setAttribute('data-note-marker', 'true');
            
            range.insertNode(marker);
            
            requestAnimationFrame(() => {
              try {
                const markerRect = marker.getBoundingClientRect();
                const targetRect = targetElement.getBoundingClientRect();
                const relativeTop = markerRect.top - targetRect.top;
                
                indicator.style.position = 'absolute';
                indicator.style.right = '-22px';
                indicator.style.top = relativeTop + 'px';
                
                targetElement.appendChild(indicator);
                
                setTimeout(() => {
                  if (marker.parentNode) {
                    marker.parentNode.removeChild(marker);
      }
    }, 100);
                
                console.log('[NOTE-VIEWER] Icon positioniert:', textStartOffset, 'top:', relativeTop);
              } catch (e) {
                if (marker.parentNode) {
                  marker.parentNode.removeChild(marker);
                }
                indicator.style.position = 'absolute';
                indicator.style.right = '-22px';
                indicator.style.top = '0px';
                targetElement.appendChild(indicator);
              }
            });
            
            return;
          } catch (e) {
            console.warn('[NOTE-VIEWER] Fehler bei Range-Positionierung:', e);
          }
        }
      }
    } catch (e) {
      console.warn('[NOTE-VIEWER] Fehler bei Text-Offset-Berechnung:', e);
    }
  }
  
  // Fallback: Position oben rechts neben dem Absatz
  indicator.style.position = 'absolute';
  indicator.style.right = '-22px';
  indicator.style.top = '0px';
  targetElement.appendChild(indicator);
}

/**
 * Dialog für Notiz-Keywords aus Context-Menü
 * Strukturiert wie das Modal für Unterstreichungen/Anstreichungen (ohne Farbauswahl)
 */
function showContextNoteDialog(text, preselectedColor = 'blue') {
  return new Promise((resolve) => {
    const dialog = document.createElement('div');
    dialog.className = 'keyword-dialog-overlay';
    dialog.style.zIndex = '10010';
    
    dialog.innerHTML = `
      <div class="keyword-dialog" style="max-width: 500px;">
        <div class="keyword-dialog-header">
          <h3>Notiz speichern</h3>
        </div>
        <div class="keyword-dialog-body">
          <div class="keyword-preview" style="max-height: 100px; overflow: hidden;">"${text.substring(0, 200)}${text.length > 200 ? '...' : ''}"</div>
          <label for="context-note-group-input">Gruppen (optional, durch Komma getrennt):</label>
          <input type="text" id="context-note-group-input" value="" placeholder="z.B. Christologie, Kosmologie, Anthropologie" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 4px; margin-top: 0.25rem; text-transform: uppercase;" />
          <div class="keyword-hint" style="font-size: 0.8rem; color: #666; margin-top: 0.25rem;">Gruppen werden in GROSSBUCHSTABEN angezeigt und kategorisieren thematisch</div>
          <label for="context-note-keyword-input" style="margin-top: 0.75rem; display: block;">Schlagwörter (optional, durch Komma getrennt):</label>
          <input type="text" id="context-note-keyword-input" value="" placeholder="z.B. Karma, Reinkarnation, Ätherleib" style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 4px; margin-top: 0.25rem;" />
          <div class="keyword-hint" style="font-size: 0.8rem; color: #666; margin-top: 0.25rem;">Schlagwörter helfen beim späteren Filtern</div>
        </div>
        <div class="keyword-dialog-footer" style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem;">
          <button class="keyword-dialog-btn keyword-dialog-cancel" style="padding: 0.5rem 1rem; cursor: pointer;">Abbrechen</button>
          <button class="keyword-dialog-btn keyword-dialog-save" style="padding: 0.5rem 1rem; background: var(--accent-color); color: white; border: none; border-radius: 4px; cursor: pointer;">Speichern</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Focus auf Gruppen-Input
    const groupInput = dialog.querySelector('#context-note-group-input');
    const keywordInput = dialog.querySelector('#context-note-keyword-input');
    setTimeout(() => groupInput.focus(), 100);
    
    // Event Handler
    const handleSave = () => {
      const groups = groupInput.value.trim();
      const keywords = keywordInput.value.trim();
      dialog.remove();
      resolve({
        groups: groups,
        keywords: keywords,
        selectedColor: preselectedColor // Verwende die vom Context-Menü übergebene Farbe
      });
    };
    
    const handleCancel = () => {
      dialog.remove();
      resolve(null);
    };
    
    dialog.querySelector('.keyword-dialog-save').addEventListener('click', handleSave);
    dialog.querySelector('.keyword-dialog-cancel').addEventListener('click', handleCancel);
    
    // Enter zum Speichern (in beiden Input-Feldern)
    const handleEnterKey = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSave();
      }
    };
    groupInput.addEventListener('keydown', handleEnterKey);
    keywordInput.addEventListener('keydown', handleEnterKey);
    
    // ESC zum Abbrechen
    dialog.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        handleCancel();
      }
    });
    
    // Klick außerhalb zum Abbrechen
    dialog.addEventListener('click', (e) => {
      if (e.target === dialog) {
        handleCancel();
      }
    });
  });
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
 * Absatz-Index aus Side Panel ermitteln (für erweiterte Suche, Index und Members Panel Volltext)
 * Sucht nach data-paragraph-id Attribut im DOM
 */
function findParagraphIdFromSidePanel(range) {
  if (!range) return null;
  
  try {
    let node = range.startContainer;
    
    // Gehe durch alle Parent-Elemente und suche nach data-paragraph-id Attribut
    while (node && node !== document.body) {
      if (node.nodeType === 1) { // Element node
        // Prüfe ob data-paragraph-id Attribut vorhanden ist
        if (node.hasAttribute && node.hasAttribute('data-paragraph-id')) {
          const paragraphId = node.getAttribute('data-paragraph-id');
          if (paragraphId) {
            console.log('[CONTEXT-MENU] Paragraph-ID aus Side Panel gefunden:', paragraphId);
            return paragraphId;
          }
        }
        
        // NEU: Für Members Panel Volltext - suche nach item-full-paragraph Container
        if (node.classList && node.classList.contains('item-full-paragraph')) {
          const paragraphId = node.getAttribute('data-paragraph-id');
          if (paragraphId) {
            console.log('[CONTEXT-MENU] Paragraph-ID aus item-full-paragraph gefunden:', paragraphId);
            return paragraphId;
          }
        }
        
        // NEU: Suche nach item-ga Link im Parent-Element (item-card)
        const itemCard = node.closest('.item-card');
        if (itemCard) {
          const itemGaLink = itemCard.querySelector('.item-ga');
          if (itemGaLink) {
            const paragraphId = itemGaLink.getAttribute('data-paragraph-id');
            if (paragraphId) {
              console.log('[CONTEXT-MENU] Paragraph-ID aus item-ga Link gefunden:', paragraphId);
              return paragraphId;
            }
          }
        }
        
        // Prüfe auch ID im Format "adv-para-X" (für erweiterte Suche)
        if (node.id && node.id.startsWith('adv-para-')) {
          // Extrahiere Index (entferne "adv-para-" Präfix)
          const idx = node.id.substring(9); // "adv-para-0" -> "0"
          console.log('[CONTEXT-MENU] Paragraph-Index aus Side Panel ID:', idx);
          return idx;
        }
        
        // Für Bücher - suche nach verstecktem Span mit data-paragraph-id im aktuellen Element
        // (Die versteckten Spans haben display:none und sind daher keine Parent-Elemente)
        const hiddenSpan = node.querySelector('[data-paragraph-id]');
        if (hiddenSpan) {
          const paragraphId = hiddenSpan.getAttribute('data-paragraph-id');
          if (paragraphId) {
            console.log('[CONTEXT-MENU] Paragraph-ID aus verstecktem Span gefunden:', paragraphId);
            return paragraphId;
          }
        }
        
        // Suche auch nach ID im Format "para-X" (für Bücher)
        if (node.id && node.id.startsWith('para-')) {
          const idx = node.id.substring(5); // "para-xyz123" -> "xyz123"
          console.log('[CONTEXT-MENU] Paragraph-Index aus para-ID gefunden:', idx);
          return idx;
        }
      }
      node = node.parentNode;
    }
    
    // Fallback: Suche nach dem nächsten versteckten Span mit data-index im summary-content
    // (für Bücher, wenn der Text zwischen zwei Indizes liegt)
    const summaryContent = document.getElementById('summary-content');
    if (summaryContent && range.startContainer) {
      // Finde alle versteckten Spans mit data-index
      const allIndexSpans = summaryContent.querySelectorAll('[data-index]');
      if (allIndexSpans.length > 0) {
        // Finde den nächsten Span vor der Selektion
        let closestSpan = null;
        let closestDistance = Infinity;
        
        const rangeRect = range.getBoundingClientRect();
        const rangeTop = rangeRect.top;
        
        allIndexSpans.forEach(span => {
          // Finde das Parent-Element, das sichtbar ist
          let visibleParent = span.parentElement;
          while (visibleParent && window.getComputedStyle(visibleParent).display === 'none') {
            visibleParent = visibleParent.parentElement;
          }
          
          if (visibleParent) {
            const rect = visibleParent.getBoundingClientRect();
            // Wähle den Span, der am nächsten oberhalb der Selektion ist
            if (rect.top <= rangeTop) {
              const distance = rangeTop - rect.top;
              if (distance < closestDistance) {
                closestDistance = distance;
                closestSpan = span;
              }
            }
          }
        });
        
        if (closestSpan) {
          const paragraphId = closestSpan.getAttribute('data-paragraph-id') || 
                             closestSpan.getAttribute('data-index')?.replace(/^\^/, '');
          if (paragraphId) {
            console.log('[CONTEXT-MENU] Paragraph-ID aus nächstem Index-Span gefunden:', paragraphId);
            return paragraphId;
          }
        }
      }
    }
  } catch (err) {
    console.warn('[CONTEXT-MENU] Fehler beim Ermitteln der Paragraph-ID aus Side Panel:', err);
  }
  
  return null;
}

/**
 * Lecture-ID aus DOM-Attributen extrahieren (für Side Panel)
 * Sucht nach data-lecture-id, data-ga-reference oder anderen Identifikatoren in Parent-Elementen
 */
function findLectureIdFromDOM(range) {
  if (!range) return null;
  
  try {
    let node = range.startContainer;
    
    // Gehe durch alle Parent-Elemente und suche nach Lecture-ID Attributen
    while (node && node !== document.body) {
      if (node.nodeType === 1) { // Element node
        // Prüfe ob data-lecture-id Attribut vorhanden (erweiterte Suche, TOC, etc.)
        if (node.hasAttribute && node.hasAttribute('data-lecture-id')) {
          const lectureId = node.getAttribute('data-lecture-id');
          if (lectureId) {
            console.log('[CONTEXT-MENU] Lecture-ID aus data-lecture-id gefunden:', lectureId);
            return lectureId;
          }
        }
        
        // Prüfe ob data-ga-reference Attribut vorhanden (Members Panel Volltext)
        if (node.hasAttribute && node.hasAttribute('data-ga-reference')) {
          const gaReference = node.getAttribute('data-ga-reference');
          if (gaReference) {
            console.log('[CONTEXT-MENU] Lecture-ID aus data-ga-reference gefunden:', gaReference);
            return gaReference;
          }
        }
        
        // Für Members Panel: Suche nach item-full-paragraph Container
        if (node.classList && node.classList.contains('item-full-paragraph')) {
          const gaReference = node.getAttribute('data-ga-reference');
          if (gaReference) {
            console.log('[CONTEXT-MENU] Lecture-ID aus item-full-paragraph gefunden:', gaReference);
            return gaReference;
          }
        }
        
        // Suche nach item-ga Link im Parent-Element (item-card)
        const itemCard = node.closest('.item-card');
        if (itemCard) {
          const itemGaLink = itemCard.querySelector('.item-ga');
          if (itemGaLink) {
            const gaReference = itemGaLink.getAttribute('data-ga');
            if (gaReference) {
              console.log('[CONTEXT-MENU] Lecture-ID aus item-ga Link gefunden:', gaReference);
              return gaReference;
            }
          }
        }
        
        // Suche nach book-content Container mit data-lecture-id
        const bookContent = node.closest('.book-content[data-lecture-id]');
        if (bookContent) {
          const lectureId = bookContent.getAttribute('data-lecture-id');
          if (lectureId) {
            console.log('[CONTEXT-MENU] Lecture-ID aus book-content gefunden:', lectureId);
            return lectureId;
          }
        }
      }
      node = node.parentNode;
    }
    
    // Fallback: Suche im summary-content nach data-lecture-id
    const summaryContent = document.getElementById('summary-content');
    if (summaryContent) {
      // Suche zuerst nach book-content
      const bookContent = summaryContent.querySelector('.book-content[data-lecture-id]');
      if (bookContent) {
        const lectureId = bookContent.getAttribute('data-lecture-id');
        if (lectureId) {
          console.log('[CONTEXT-MENU] Lecture-ID aus book-content in summary-content gefunden:', lectureId);
          return lectureId;
        }
      }
      
      // Suche nach Element mit data-lecture-id
      const lectureIdElement = summaryContent.querySelector('[data-lecture-id]');
      if (lectureIdElement) {
        const lectureId = lectureIdElement.getAttribute('data-lecture-id');
        if (lectureId) {
          console.log('[CONTEXT-MENU] Lecture-ID aus summary-content Element gefunden:', lectureId);
          return lectureId;
        }
      }
    }
  } catch (err) {
    console.warn('[CONTEXT-MENU] Fehler beim Ermitteln der Lecture-ID aus DOM:', err);
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
  
  // Versuche aus Hash - unterstützt auch GA-Nummern mit Buchstaben-Suffix wie GA266a
  const hash = window.location.hash;
  const match = hash.match(/GA\s?(\d{1,3}[a-z]?)/i);
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
 * @param {string} markerColor - Die Farbe des Zitats (optional)
 */
function applyQuoteToSelection(range, quoteId, gaNumber, paragraphId, markerColor = null) {
  if (!range) return;
  
  try {
    // Finde das Absatz-Element (Container für die Linie)
    let paragraphElement = null;
    let node = range.startContainer;
    while (node && node !== document.body) {
      if (node.nodeType === 1) { // Element node
        // Prüfe ob para- ID vorhanden
        if (node.id && node.id.startsWith('para-')) {
          paragraphElement = node;
          // Für Bücher: Falls paraElement ein verstecktes span ist, finde das Parent-Element
          if (node.style.display === 'none' || node.tagName.toLowerCase() === 'span') {
            let parent = node.parentElement;
            while (parent && parent !== document.body) {
              const tagName = parent.tagName.toLowerCase();
              if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
                paragraphElement = parent;
                break;
              }
              parent = parent.parentElement;
            }
          }
          break;
        }
        // Fallback: Suche nach Block-Element
        const tagName = node.tagName.toLowerCase();
        if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
          paragraphElement = node;
        }
      }
      node = node.parentNode;
    }
    
    // Hole Quote-Farbe aus dem DOM falls verfügbar, sonst Standard
    let quoteColor = markerColor || 'blue';
    if (!markerColor) {
      // Versuche Quote-Farbe aus dem Member Panel zu holen
      const quoteItem = document.querySelector(`[data-id="${quoteId}"][data-type="quote"]`);
      if (quoteItem) {
        const iconElement = quoteItem.querySelector('.quote-bookmark-icon-header');
        if (iconElement && iconElement.style.color) {
          // Konvertiere Hex-Farbe zurück zu Farbname (vereinfacht)
          const hexColor = iconElement.style.color.toLowerCase();
          if (hexColor === '#467886' || hexColor === 'rgb(70, 120, 134)') quoteColor = 'blue';
          else if (hexColor === '#c62828' || hexColor === 'rgb(198, 40, 40)') quoteColor = 'red';
          else if (hexColor === '#ffc107' || hexColor === 'rgb(255, 193, 7)') quoteColor = 'yellow';
        }
      }
    }
    
    // Wrappe Text mit span (ohne border-right)
    const span = document.createElement('span');
    span.className = 'member-quote-highlight';
    span.style.setProperty('cursor', 'pointer', 'important');
    span.setAttribute('data-quote-id', quoteId);
    span.setAttribute('data-quote', 'true');
    span.setAttribute('data-ga-reference', gaNumber);
    span.setAttribute('data-paragraph-id', paragraphId);
    span.setAttribute('data-quote-color', quoteColor);
    span.setAttribute('title', 'Klicken zum Öffnen im Member Panel');
    
    // Erstelle senkrechte Linie rechts neben dem Absatz (falls Absatz gefunden)
    if (paragraphElement) {
      if (typeof createQuoteVerticalLine === 'function') {
        const quoteObj = { id: quoteId, marker_color: quoteColor };
        createQuoteVerticalLine(paragraphElement, range, quoteObj);
      } else {
        // Fallback: Erstelle Linie direkt hier (falls Funktion nicht verfügbar)
        try {
          const computedStyle = window.getComputedStyle(paragraphElement);
          if (computedStyle.position === 'static') {
            paragraphElement.style.position = 'relative';
          }
          
          const rangeRect = range.getBoundingClientRect();
          const containerRect = paragraphElement.getBoundingClientRect();
          const topOffset = rangeRect.top - containerRect.top;
          const bottomOffset = rangeRect.bottom - containerRect.top;
          const lineHeight = bottomOffset - topOffset;
          const quoteColorHex = typeof getHighlightColor === 'function' ? getHighlightColor(quoteColor) : '#467886';
          
          const lineElement = document.createElement('div');
          lineElement.className = 'member-quote-vertical-line';
          lineElement.setAttribute('data-quote-id', quoteId);
          lineElement.setAttribute('data-quote', 'true');
          lineElement.setAttribute('data-quote-color', quoteColor);
          lineElement.style.position = 'absolute';
          lineElement.style.left = '-5px';
          lineElement.style.top = `${topOffset}px`;
          lineElement.style.width = '1.5px';
          lineElement.style.height = `${Math.max(lineHeight, 1)}px`;
          lineElement.style.backgroundColor = quoteColorHex;
          lineElement.style.pointerEvents = 'none';
          lineElement.style.zIndex = '10';
          
          paragraphElement.appendChild(lineElement);
        } catch (e) {
          console.warn('[QUOTE-SELECTION] Konnte Linie nicht erstellen:', e);
        }
      }
    }
    
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
 * Keyword-Eingabe-Dialog anzeigen (mit Gruppen- und Notizen-Feld)
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
          <label for="group-input">Gruppen (optional, durch Komma getrennt):</label>
          <input type="text" id="group-input" placeholder="z.B. Christologie, Kosmologie, Anthropologie" style="text-transform: uppercase;" />
          <div class="keyword-hint">Gruppen werden in GROSSBUCHSTABEN angezeigt und kategorisieren thematisch</div>
          <label for="keyword-input" style="margin-top: 0.75rem; display: block;">Schlagwörter (optional, durch Komma getrennt):</label>
          <input type="text" id="keyword-input" placeholder="z.B. Karma, Reinkarnation, Ätherleib" />
          <div class="keyword-hint">Schlagwörter helfen beim späteren Filtern und Wiederfinden</div>
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
    
    // Focus auf Gruppen-Input
    const groupInput = dialog.querySelector('#group-input');
    const input = dialog.querySelector('#keyword-input');
    setTimeout(() => groupInput.focus(), 100);
    
    // Event Handlers
    const saveBtn = dialog.querySelector('.keyword-dialog-save');
    const cancelBtn = dialog.querySelector('.keyword-dialog-cancel');
    const noteInput = dialog.querySelector('#note-input');
    
    const handleSave = () => {
      const groups = groupInput.value
        .split(',')
        .map(g => g.trim().toUpperCase())
        .filter(g => g.length > 0);
      const keywords = input.value
        .split(',')
        .map(kw => kw.trim())
        .filter(kw => kw.length > 0);
      const note = noteInput.value.trim();
      dialog.remove();
      resolve({ keywords, groups, note });
    };
    
    const handleCancel = () => {
      dialog.remove();
      resolve(null);
    };
    
    saveBtn.addEventListener('click', handleSave);
    cancelBtn.addEventListener('click', handleCancel);
    
    // Enter zum Speichern (für Gruppen- und Schlagwörter-Input, nicht für Textarea)
    const handleEnterKey = (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSave();
      }
    };
    groupInput.addEventListener('keydown', handleEnterKey);
    input.addEventListener('keydown', handleEnterKey);
    
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
    
    .note-submenu-hidden {
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
    
    /* Stelle sicher, dass das Note-Untermenü sichtbar bleibt wenn Maus über Parent oder Untermenü ist */
    .note-menu-item:hover .context-submenu,
    .note-menu-item:hover .note-submenu-hidden {
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

