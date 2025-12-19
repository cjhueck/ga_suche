// ============================================
// GA-Suche Mitglieder-Integration (Standalone)
// Funktioniert OHNE ES6 Modules - für file:// URLs
// ============================================

// Globale Variable für Supabase Client (nur deklarieren wenn noch nicht vorhanden)
if (typeof supabaseClient === 'undefined') {
  var supabaseClient = null;
}
if (typeof currentUser === 'undefined') {
  var currentUser = null;
}

// Supabase initialisieren
async function initSupabase() {
  if (supabaseClient) return supabaseClient;
  
  // WICHTIG: Diese Keys durch Ihre eigenen ersetzen!
  const SUPABASE_URL = 'https://qygirjbfvzyhpgwhllzs.supabase.co';
  const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF5Z2lyamJmdnp5aHBnd2hsbHpzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI4NjM4NjgsImV4cCI6MjA3ODQzOTg2OH0.8ePpjxvukwtxZMZ8GwDMKRmxhB1gFE41bv44PFvgVnA';
  
  // Supabase von CDN laden (bereits in HTML eingebunden)
  if (typeof supabase === 'undefined') {
    console.error('Supabase library nicht geladen! Bitte <script> Tag hinzufügen.');
    return null;
  }
  
  supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  
  // User Status prüfen
  const { data: { user } } = await supabaseClient.auth.getUser();
  currentUser = user;
  window.currentUser = user; // Auch global verfügbar machen
  
  return supabaseClient;
}

// Aktuellen User abrufen
async function getCurrentUser() {
  if (!supabaseClient) {
    await initSupabase();
  }
  if (!currentUser) {
    const { data: { user } } = await supabaseClient.auth.getUser();
    currentUser = user;
    window.currentUser = user;
  }
  return currentUser;
}

// ============================================
// 1. TEXT-SELEKTION POPUP
// ============================================

let selectionPopup = null;
let currentSelection = null;
let currentContext = { gaNumber: '', lectureTitle: '' };

function initSelectionPopup(gaNumber, lectureTitle) {
  currentContext = { gaNumber, lectureTitle };
  
  if (!selectionPopup) {
    createSelectionPopup();
  }
  
  document.addEventListener('mouseup', handleTextSelection);
  document.addEventListener('touchend', handleTextSelection);
}

function createSelectionPopup() {
  selectionPopup = document.createElement('div');
  selectionPopup.id = 'selection-popup';
  selectionPopup.innerHTML = `
    <button class="selection-btn" onclick="handlePopupClick('quote')" title="Als Zitat speichern">
      💬 Zitat
    </button>
    <button class="selection-btn" onclick="handlePopupClick('bookmark')" title="Als Bookmark speichern">
      🔖 Bookmark
    </button>
    <button class="selection-btn" onclick="handlePopupClick('note')" title="Notiz erstellen">
      📝 Notiz
    </button>
  `;
  
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
  
  // CSS für Buttons
  addStyles();
}

async function handleTextSelection(e) {
  const selection = window.getSelection();
  const selectedText = selection.toString().trim();
  
  if (selectedText.length < 10) {
    hideSelectionPopup();
    return;
  }
  
  currentSelection = selectedText;
  
  // User eingeloggt?
  await initSupabase();
  if (!currentUser) {
    // Stumm - User kann später speichern
    return;
  }
  
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  
  selectionPopup.style.display = 'flex';
  selectionPopup.style.left = `${rect.left + (rect.width / 2) - 150}px`;
  selectionPopup.style.top = `${rect.top - 60 + window.scrollY}px`;
}

function hideSelectionPopup() {
  if (selectionPopup) {
    selectionPopup.style.display = 'none';
  }
}

async function handlePopupClick(action) {
  await initSupabase();
  
  if (!currentUser) {
    if (confirm('Sie müssen angemeldet sein. Möchten Sie sich jetzt anmelden?')) {
      window.open('members.html', '_blank');
    }
    hideSelectionPopup();
    return;
  }
  
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

/**
 * Ermittelt das Datum des aktuellen Vortrags
 * Gibt das Datum im Format YYYY-MM-DD zurück oder null wenn nicht verfügbar
 */
function getCurrentLectureDate(lectureId) {
  if (!lectureId) return null;
  
  // Versuche aus currentLectureData zu holen
  if (typeof currentLectureData !== 'undefined' && currentLectureData) {
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

async function saveAsQuote(text, contextBefore, contextAfter) {
  try {
    const lectureId = currentContext.gaNumber;
    const lectureDate = getCurrentLectureDate(lectureId);
    
    const insertData = {
        user_id: currentUser.id,
        quote_text: text,
      ga_reference: lectureId,
        lecture_title: currentContext.lectureTitle,
        lecture_url: window.location.href,
        context_before: contextBefore,
        context_after: contextAfter,
        personal_note: '',
        tags: [],
        is_public: false
    };
    
    // Füge lecture_date hinzu, falls verfügbar
    if (lectureDate) {
      insertData.lecture_date = lectureDate;
    }
    
    const { data, error } = await supabaseClient
      .from('quotes')
      .insert(insertData)
      .select()
      .single();
    
    if (error) throw error;
    
    showNotification('✓ Zitat gespeichert!', 'success');
    highlightSelection('#ffffcc');
  } catch (error) {
    console.error('Fehler:', error);
    showNotification('✗ Fehler beim Speichern', 'error');
  }
}

async function saveAsBookmark(text) {
  try {
    const { data, error } = await supabaseClient
      .from('bookmarks')
      .insert({
        user_id: currentUser.id,
        ga_number: currentContext.gaNumber,
        lecture_title: currentContext.lectureTitle,
        lecture_url: window.location.href,
        paragraph_id: null,
        paragraph_text: text,
        note: '',
        tags: []
      })
      .select()
      .single();
    
    if (error) throw error;
    
    showNotification('✓ Bookmark gespeichert!', 'success');
    highlightSelection('#ccffcc');
  } catch (error) {
    console.error('Fehler:', error);
    showNotification('✗ Fehler beim Speichern', 'error');
  }
}

function openNoteEditor(prefilledText) {
  const noteData = encodeURIComponent(JSON.stringify({
    content: `Aus [[${currentContext.gaNumber}]]:\n\n"${prefilledText}"\n\n`,
    title: `Notiz zu ${currentContext.gaNumber}`
  }));
  
  window.open(`members.html?tab=notes&prefill=${noteData}`, '_blank');
}

function getContextBefore(selectedText, maxChars = 100) {
  const fullText = document.body.innerText;
  const index = fullText.indexOf(selectedText);
  if (index === -1) return '';
  
  const start = Math.max(0, index - maxChars);
  return '...' + fullText.substring(start, index).trim();
}

function getContextAfter(selectedText, maxChars = 100) {
  const fullText = document.body.innerText;
  const index = fullText.indexOf(selectedText);
  if (index === -1) return '';
  
  const end = Math.min(fullText.length, index + selectedText.length + maxChars);
  return fullText.substring(index + selectedText.length, end).trim() + '...';
}

function highlightSelection(color) {
  const selection = window.getSelection();
  if (selection.rangeCount === 0) return;
  
  try {
    const range = selection.getRangeAt(0);
    const span = document.createElement('span');
    span.style.backgroundColor = color;
    span.style.transition = 'background-color 2s';
    
    range.surroundContents(span);
    
    setTimeout(() => {
      span.style.backgroundColor = 'transparent';
    }, 2000);
  } catch (e) {
    // Falls Selektion komplex ist, einfach ignorieren
  }
}

// ============================================
// 2. HOVER-ICONS bei Absätzen
// ============================================

function addParagraphBookmarkIcons(gaNumber, lectureTitle) {
  // Selector anpassen - je nachdem wo Ihre Absätze sind
  const selector = 'p'; // ODER: '.lecture-content p' oder '#content p'
  
  document.querySelectorAll(selector).forEach((paragraph, index) => {
    if (paragraph.textContent.trim().length < 50) return;
    if (paragraph.querySelector('.paragraph-bookmark-icon')) return; // Bereits vorhanden
    
    const icon = document.createElement('button');
    icon.innerHTML = '🔖';
    icon.className = 'paragraph-bookmark-icon';
    icon.title = 'Als Bookmark speichern';
    icon.dataset.paragraphIndex = index;
    
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
    
    paragraph.style.position = 'relative';
    paragraph.appendChild(icon);
    
    paragraph.addEventListener('mouseenter', () => {
      icon.style.opacity = '0.6';
    });
    
    paragraph.addEventListener('mouseleave', () => {
      icon.style.opacity = '0';
    });
    
    icon.addEventListener('mouseenter', () => {
      icon.style.opacity = '1';
    });
    
    icon.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      await initSupabase();
      
      if (!currentUser) {
        if (confirm('Sie müssen angemeldet sein. Möchten Sie sich jetzt anmelden?')) {
          window.open('members.html', '_blank');
        }
        return;
      }
      
      try {
        const { error } = await supabaseClient
          .from('bookmarks')
          .insert({
            user_id: currentUser.id,
            ga_number: gaNumber,
            lecture_title: lectureTitle,
            lecture_url: window.location.href,
            paragraph_id: `p-${index}`,
            paragraph_text: paragraph.textContent.trim(),
            note: '',
            tags: []
          });
        
        if (error) throw error;
        
        showNotification('✓ Bookmark gespeichert!', 'success');
        icon.innerHTML = '✓';
        paragraph.style.backgroundColor = '#ffffcc';
        
        setTimeout(() => {
          icon.innerHTML = '🔖';
          paragraph.style.backgroundColor = 'transparent';
        }, 2000);
      } catch (error) {
        console.error('Fehler:', error);
        showNotification('✗ Fehler beim Speichern', 'error');
      }
    });
  });
}

// ============================================
// 3. TOOLBAR für eingeloggte User
// ============================================

async function createMemberToolbar(gaNumber, lectureTitle) {
  await initSupabase();
  
  if (!currentUser) return;
  
  // Prüfen ob bereits vorhanden
  if (document.getElementById('member-toolbar')) return;
  
  const toolbar = document.createElement('div');
  toolbar.id = 'member-toolbar';
  toolbar.innerHTML = `
    <div style="display: flex; align-items: center; gap: 15px;">
      <span style="color: #467886; font-weight: 600;">
        👤 ${currentUser.email}
      </span>
      <button class="toolbar-btn" onclick="window.open('members.html?tab=bookmarks', '_blank')">
        🔖 Meine Bookmarks
      </button>
      <button class="toolbar-btn" onclick="window.open('members.html?tab=notes', '_blank')">
        📝 Meine Notizen
      </button>
      <button class="toolbar-btn" onclick="window.open('members.html?tab=notes&ga=${gaNumber}', '_blank')">
        ➕ Neue Notiz
      </button>
    </div>
  `;
  
  toolbar.style.cssText = `
    position: sticky;
    top: 0;
    background: #f5f5f5;
    border-bottom: 2px solid #467886;
    padding: 12px 20px;
    z-index: 1000;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  `;
  
  document.body.insertBefore(toolbar, document.body.firstChild);
  
  // Button Styling via CSS (bereits in addStyles())
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
  
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// ============================================
// 5. STYLES
// ============================================

function addStyles() {
  if (document.querySelector('#member-integration-styles')) return;
  
  const style = document.createElement('style');
  style.id = 'member-integration-styles';
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
    
    #selection-popup {
      display: flex;
    }
    
    .toolbar-btn {
      background: white;
      border: 1px solid #467886;
      color: #467886;
      padding: 8px 16px;
      cursor: pointer;
      font-size: 14px;
      border-radius: 4px;
      transition: all 0.2s;
    }
    
    .toolbar-btn:hover {
      background: #467886;
      color: white;
    }
  `;
  document.head.appendChild(style);
}

// ============================================
// 6. AUTO-INIT (Optional)
// ============================================

// Automatisch initialisieren wenn Seite geladen ist
// (kann auch manuell aufgerufen werden)
document.addEventListener('DOMContentLoaded', function() {
  
  // Optional: Automatisch starten wenn GA-Nummer im URL ist
  const urlParams = new URLSearchParams(window.location.search);
  const gaFromUrl = urlParams.get('ga');
  
  if (gaFromUrl) {
    // Auto-init hier wenn gewünscht
  }
});

// ============================================
// GLOBALE FUNKTIONEN (von HTML aufrufbar)
// ============================================

// Diese Funktionen können direkt aus HTML aufgerufen werden
window.initMembersIntegration = async function(gaNumber, lectureTitle) {
  await initSupabase();
  await createMemberToolbar(gaNumber, lectureTitle);
  initSelectionPopup(gaNumber, lectureTitle);
  addParagraphBookmarkIcons(gaNumber, lectureTitle);
};

// WICHTIG: initSupabase und getCurrentUser global verfügbar machen
window.initSupabase = initSupabase;
window.getCurrentUser = getCurrentUser;

window.handlePopupClick = handlePopupClick;

