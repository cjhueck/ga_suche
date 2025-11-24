// ============================================
// GA-Suche Mitglieder-Integration
// ============================================
// Dieses Script in app.html einbinden, um Bookmark/Zitat-Funktionen zu aktivieren

import { getCurrentUser } from './members-auth.js';
import { createBookmark, createQuote } from './members-api.js';

// ============================================
// 1. TEXT-SELEKTION POPUP (wie Medium.com)
// ============================================

let selectionPopup = null;
let currentSelection = null;
let currentContext = null; // GA-Nummer, Titel, etc.

/**
 * Initialisiert das Text-Selektion Popup
 * Rufen Sie diese Funktion auf, wenn app.html geladen ist
 */
export function initSelectionPopup(gaNumber, lectureTitle) {
  currentContext = { gaNumber, lectureTitle };
  
  // Popup erstellen (falls noch nicht vorhanden)
  if (!selectionPopup) {
    createSelectionPopup();
  }
  
  // Event Listener für Text-Auswahl
  document.addEventListener('mouseup', handleTextSelection);
  document.addEventListener('touchend', handleTextSelection);
}

function createSelectionPopup() {
  selectionPopup = document.createElement('div');
  selectionPopup.id = 'selection-popup';
  selectionPopup.innerHTML = `
    <button class="selection-btn" data-action="quote" title="Als Zitat speichern">
      💬 Zitat
    </button>
    <button class="selection-btn" data-action="bookmark" title="Als Bookmark speichern">
      🔖 Bookmark
    </button>
    <button class="selection-btn" data-action="note" title="Notiz erstellen">
      📝 Notiz
    </button>
  `;
  
  // Styling
  selectionPopup.style.cssText = `
    position: absolute;
    background: white;
    border: 1px solid #467886;
    border-radius: 8px;
    padding: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    display: none;
    z-index: 10000;
    gap: 8px;
  `;
  
  document.body.appendChild(selectionPopup);
  
  // Event Listeners für Buttons
  selectionPopup.querySelectorAll('.selection-btn').forEach(btn => {
    btn.addEventListener('click', handlePopupAction);
  });
}

async function handleTextSelection(e) {
  const selection = window.getSelection();
  const selectedText = selection.toString().trim();
  
  // Mindestens 10 Zeichen
  if (selectedText.length < 10) {
    hideSelectionPopup();
    return;
  }
  
  currentSelection = selectedText;
  
  // User eingeloggt?
  const user = await getCurrentUser();
  if (!user) {
    // Optionales Login-Hinweis
    // showLoginPrompt();
    return;
  }
  
  // Position berechnen
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  
  // Popup positionieren (über der Selektion)
  selectionPopup.style.display = 'flex';
  selectionPopup.style.left = `${rect.left + (rect.width / 2) - 150}px`;
  selectionPopup.style.top = `${rect.top - 60 + window.scrollY}px`;
}

function hideSelectionPopup() {
  if (selectionPopup) {
    selectionPopup.style.display = 'none';
  }
}

async function handlePopupAction(e) {
  const action = e.target.dataset.action;
  const user = await getCurrentUser();
  
  if (!user) {
    alert('Bitte melden Sie sich im Mitgliederbereich an!');
    window.open('members.html', '_blank');
    return;
  }
  
  // Kontext holen (umliegender Text)
  const contextBefore = getContextBefore(currentSelection, 100);
  const contextAfter = getContextAfter(currentSelection, 100);
  
  switch(action) {
    case 'quote':
      await saveAsQuote(currentSelection, contextBefore, contextAfter);
      break;
    case 'bookmark':
      await saveAsBookmark(currentSelection);
      break;
    case 'note':
      openNoteEditor(currentSelection);
      break;
  }
  
  hideSelectionPopup();
}

async function saveAsQuote(text, contextBefore, contextAfter) {
  const result = await createQuote(
    text,
    currentContext.gaNumber,
    currentContext.lectureTitle,
    contextBefore,
    contextAfter,
    '', // persönliche Notiz (optional)
    [], // Tags (optional)
    false // nicht öffentlich
  );
  
  if (result.success) {
    showNotification('✓ Zitat gespeichert!', 'success');
    highlightSelection('#ffffcc'); // Gelb markieren
  } else {
    showNotification('✗ Fehler beim Speichern', 'error');
  }
}

async function saveAsBookmark(text) {
  const result = await createBookmark(
    currentContext.gaNumber,
    currentContext.lectureTitle,
    null, // paragraph_id
    text,
    '', // note
    [] // tags
  );
  
  if (result.success) {
    showNotification('✓ Bookmark gespeichert!', 'success');
    highlightSelection('#ccffcc'); // Grün markieren
  } else {
    showNotification('✗ Fehler beim Speichern', 'error');
  }
}

function openNoteEditor(prefilledText) {
  // Öffne members.html mit vorgefülltem Text
  const noteData = encodeURIComponent(JSON.stringify({
    content: `Aus [[${currentContext.gaNumber}]]:\n\n"${prefilledText}"\n\n`,
    title: `Notiz zu ${currentContext.gaNumber}`
  }));
  
  window.open(`members.html?tab=notes&prefill=${noteData}`, '_blank');
}

// Helper: Kontext vor Selektion
function getContextBefore(selectedText, maxChars = 100) {
  const fullText = document.body.innerText;
  const index = fullText.indexOf(selectedText);
  if (index === -1) return '';
  
  const start = Math.max(0, index - maxChars);
  return '...' + fullText.substring(start, index).trim();
}

// Helper: Kontext nach Selektion
function getContextAfter(selectedText, maxChars = 100) {
  const fullText = document.body.innerText;
  const index = fullText.indexOf(selectedText);
  if (index === -1) return '';
  
  const end = Math.min(fullText.length, index + selectedText.length + maxChars);
  return fullText.substring(index + selectedText.length, end).trim() + '...';
}

// Helper: Selektion farbig markieren
function highlightSelection(color) {
  const selection = window.getSelection();
  if (selection.rangeCount === 0) return;
  
  const range = selection.getRangeAt(0);
  const span = document.createElement('span');
  span.style.backgroundColor = color;
  span.style.transition = 'background-color 2s';
  
  range.surroundContents(span);
  
  // Nach 2 Sekunden ausblenden
  setTimeout(() => {
    span.style.backgroundColor = 'transparent';
  }, 2000);
}


// ============================================
// 2. HOVER-ICONS bei Absätzen
// ============================================

/**
 * Fügt Hover-Icons zu allen Absätzen hinzu
 */
export function addParagraphBookmarkIcons(gaNumber, lectureTitle) {
  // Alle <p> Tags finden
  document.querySelectorAll('p').forEach((paragraph, index) => {
    // Nur wenn genug Text vorhanden
    if (paragraph.textContent.trim().length < 50) return;
    
    // Icon erstellen
    const icon = document.createElement('button');
    icon.innerHTML = '🔖';
    icon.className = 'paragraph-bookmark-icon';
    icon.title = 'Als Bookmark speichern';
    icon.dataset.paragraphIndex = index;
    
    // Styling
    icon.style.cssText = `
      position: absolute;
      right: -35px;
      top: 0;
      opacity: 0;
      background: none;
      border: none;
      font-size: 20px;
      cursor: pointer;
      transition: opacity 0.2s;
      padding: 5px;
    `;
    
    // Paragraph relativ positionieren
    paragraph.style.position = 'relative';
    
    // Icon hinzufügen
    paragraph.appendChild(icon);
    
    // Hover-Effekt
    paragraph.addEventListener('mouseenter', () => {
      icon.style.opacity = '0.6';
    });
    
    paragraph.addEventListener('mouseleave', () => {
      icon.style.opacity = '0';
    });
    
    icon.addEventListener('mouseenter', () => {
      icon.style.opacity = '1';
    });
    
    // Click-Handler
    icon.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const user = await getCurrentUser();
      if (!user) {
        alert('Bitte melden Sie sich im Mitgliederbereich an!');
        window.open('members.html', '_blank');
        return;
      }
      
      const result = await createBookmark(
        gaNumber,
        lectureTitle,
        `p-${index}`,
        paragraph.textContent.trim(),
        '',
        []
      );
      
      if (result.success) {
        showNotification('✓ Bookmark gespeichert!', 'success');
        icon.innerHTML = '✓';
        paragraph.style.backgroundColor = '#ffffcc';
        
        setTimeout(() => {
          icon.innerHTML = '🔖';
          paragraph.style.backgroundColor = 'transparent';
        }, 2000);
      }
    });
  });
}


// ============================================
// 3. TOOLBAR für eingeloggte User
// ============================================

/**
 * Erstellt eine Toolbar oben für schnellen Zugriff
 */
export async function createMemberToolbar(gaNumber, lectureTitle) {
  const user = await getCurrentUser();
  
  // Nur für eingeloggte User
  if (!user) return;
  
  const toolbar = document.createElement('div');
  toolbar.id = 'member-toolbar';
  toolbar.innerHTML = `
    <div style="display: flex; align-items: center; gap: 15px;">
      <span style="color: #467886; font-weight: 600;">
        👤 ${user.email}
      </span>
      <button class="toolbar-btn" data-action="view-bookmarks">
        🔖 Meine Bookmarks
      </button>
      <button class="toolbar-btn" data-action="view-notes">
        📝 Meine Notizen
      </button>
      <button class="toolbar-btn" data-action="new-note">
        ➕ Neue Notiz
      </button>
    </div>
  `;
  
  // Styling
  toolbar.style.cssText = `
    position: sticky;
    top: 0;
    background: #f5f5f5;
    border-bottom: 2px solid #467886;
    padding: 12px 20px;
    z-index: 1000;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  `;
  
  // Button Styling
  toolbar.querySelectorAll('.toolbar-btn').forEach(btn => {
    btn.style.cssText = `
      background: white;
      border: 1px solid #467886;
      color: #467886;
      padding: 8px 16px;
      cursor: pointer;
      font-size: 14px;
      border-radius: 4px;
      transition: all 0.2s;
    `;
    
    btn.addEventListener('mouseenter', () => {
      btn.style.backgroundColor = '#467886';
      btn.style.color = 'white';
    });
    
    btn.addEventListener('mouseleave', () => {
      btn.style.backgroundColor = 'white';
      btn.style.color = '#467886';
    });
  });
  
  // Event Handlers
  toolbar.querySelectorAll('.toolbar-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const action = e.target.dataset.action;
      
      switch(action) {
        case 'view-bookmarks':
          window.open('members.html?tab=bookmarks', '_blank');
          break;
        case 'view-notes':
          window.open('members.html?tab=notes', '_blank');
          break;
        case 'new-note':
          window.open(`members.html?tab=notes&ga=${gaNumber}`, '_blank');
          break;
      }
    });
  });
  
  // Am Anfang des body einfügen
  document.body.insertBefore(toolbar, document.body.firstChild);
}


// ============================================
// 4. NOTIFICATIONS
// ============================================

function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 25px;
    background: ${type === 'success' ? '#467886' : type === 'error' ? '#f44336' : '#2196F3'};
    color: white;
    border-radius: 4px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 10001;
    animation: slideIn 0.3s ease;
  `;
  
  document.body.appendChild(notification);
  
  // Nach 3 Sekunden entfernen
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// Animation CSS (einmalig hinzufügen)
if (!document.querySelector('#notification-styles')) {
  const style = document.createElement('style');
  style.id = 'notification-styles';
  style.textContent = `
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
    
    .selection-btn {
      background: white;
      border: 1px solid #467886;
      color: #467886;
      padding: 8px 12px;
      cursor: pointer;
      font-size: 13px;
      border-radius: 4px;
      transition: all 0.2s;
    }
    
    .selection-btn:hover {
      background: #467886;
      color: white;
    }
  `;
  document.head.appendChild(style);
}


// ============================================
// 5. CLEANUP
// ============================================

/**
 * Cleanup-Funktion wenn Seite verlassen wird
 */
export function cleanupIntegration() {
  document.removeEventListener('mouseup', handleTextSelection);
  document.removeEventListener('touchend', handleTextSelection);
  
  if (selectionPopup) {
    selectionPopup.remove();
    selectionPopup = null;
  }
}

