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
  
  console.log('✓ Members Context Menu aktiviert');
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
    <div class="context-menu-item" onclick="contextMenuAction('bookmark')">
      <span class="context-menu-icon">🔖</span>
      <span class="context-menu-text">Bookmark setzen</span>
    </div>
    <div class="context-menu-item" onclick="contextMenuAction('quote')">
      <span class="context-menu-icon">💬</span>
      <span class="context-menu-text">Zitat speichern</span>
    </div>
    <div class="context-menu-item" onclick="contextMenuAction('note')">
      <span class="context-menu-icon">📝</span>
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
async function contextMenuAction(action) {
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
  
  console.log('[CONTEXTMENU] Context:', { lectureId, gaNumber, paragraphIndex });
  
  switch(action) {
    case 'bookmark':
      await saveContextBookmark(selectedTextForContext, lectureId, lectureTitle, paragraphIndex);
      break;
    case 'quote':
      await saveContextQuote(selectedTextForContext, lectureId, lectureTitle, paragraphIndex, contextBefore, contextAfter);
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
    
    const insertData = {
      user_id: currentUser.id,
      ga_number: lectureId,
      lecture_title: lectureTitle,
      paragraph_id: paragraphIndex,
      paragraph_text: text,
      note: '',
      tags: []
    };
    
    const { data, error } = await supabaseClient
      .from('bookmarks')
      .insert(insertData)
      .select();
    
    if (error) {
      console.error('Supabase Fehler:', error);
      throw new Error(error.message || 'Datenbankfehler');
    }
    
    console.log('✓ Bookmark gespeichert:', data);
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
 * Zitat aus Context-Menü speichern
 */
async function saveContextQuote(text, lectureId, lectureTitle, paragraphIndex, contextBefore, contextAfter) {
  try {
    if (typeof supabaseClient === 'undefined' || !supabaseClient) {
      throw new Error('Supabase Client nicht initialisiert');
    }
    
    const insertData = {
      user_id: currentUser.id,
      quote_text: text,
      ga_reference: lectureId,
      lecture_title: lectureTitle,
      paragraph_id: paragraphIndex,
      context_before: contextBefore,
      context_after: contextAfter,
      personal_note: '',
      tags: [],
      is_public: false
    };
    
    const { data, error } = await supabaseClient
      .from('quotes')
      .insert(insertData)
      .select();
    
    if (error) {
      console.error('Supabase Fehler:', error);
      throw new Error(error.message || 'Datenbankfehler');
    }
    
    console.log('✓ Zitat gespeichert:', data);
    showContextNotification('✓ Zitat gespeichert!', 'success');
    highlightContextSelection('#ffffcc');
    
    // MB aktualisieren falls offen
    if (typeof membersPanelActive !== 'undefined' && membersPanelActive && currentMembersTab === 'quotes') {
      if (typeof loadMembersTab === 'function') {
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
 */
function findParagraphId(range) {
  if (!range) return null;
  
  try {
    let node = range.startContainer;
    
    // Gehe Parent-Nodes hoch bis Paragraph gefunden
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
  } catch (err) {
    console.log('[CONTEXTMENU] Paragraph-Index nicht gefunden:', err);
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
    console.log('Highlight nicht möglich');
  }
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
      overflow: hidden;
    }
    
    .context-menu-item {
      display: flex;
      align-items: center;
      gap: 8px;
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
    
    .context-menu-icon {
      font-size: 1rem;
    }
    
    .context-menu-text {
      flex: 1;
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
      background: #4CAF50;
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
  `;
  document.head.appendChild(style);
}

// Global verfügbar machen
window.initMembersContextMenu = initMembersContextMenu;
window.contextMenuAction = contextMenuAction;

// Auto-Init wenn DOM geladen - mit Verzögerung
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(initMembersContextMenu, 500);
  });
} else {
  setTimeout(initMembersContextMenu, 500);
}

// Debug: Zeige Status
console.log('[Members Context Menu] Script geladen, warte auf Init...');

