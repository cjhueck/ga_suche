// ============================================
// GA-Suche - Mitglieder Header Icons
// Kompakte Icon-Leiste oben rechts
// ============================================

let iconBar = null;
let currentUserStatus = null;

/**
 * Erstellt die Icon-Leiste oben rechts
 */
async function createMemberHeaderIcons() {
  // Prüfe ob bereits vorhanden
  if (iconBar) return;
  
  // Supabase initialisieren
  await initSupabase();
  
  // Icon-Leiste erstellen
  iconBar = document.createElement('div');
  iconBar.id = 'member-header-icons';
  iconBar.style.cssText = `
    position: fixed;
    top: 15px;
    right: 15px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    z-index: 9999;
    background: transparent;
    padding: 0;
    border-radius: 0;
    box-shadow: none;
    border: none;
  `;
  
  document.body.appendChild(iconBar);
  
  // Icons basierend auf Login-Status
  updateHeaderIcons();
  
  // CSS hinzufügen
  addHeaderIconStyles();
}

/**
 * Icons aktualisieren basierend auf Login-Status
 */
async function updateHeaderIcons() {
  if (!iconBar) return;
  
  await initSupabase();
  
  if (!currentUser) {
    // Nicht eingeloggt - nur Login-Icon
    iconBar.innerHTML = `
      <button class="header-icon" onclick="openMembersLogin()" title="Anmelden">
        👤
      </button>
    `;
  } else {
    // Eingeloggt - Alle Icons
    iconBar.innerHTML = `
      <button class="header-icon active" onclick="openMembersArea()" title="${currentUser.email}">
        👤
      </button>
      <div style="height: 1px; background: #ddd; margin: 4px 0;"></div>
      <button class="header-icon" onclick="quickSaveQuote()" title="Zitat speichern">
        💬
      </button>
      <button class="header-icon" onclick="quickSaveBookmark()" title="Bookmark speichern">
        🔖
      </button>
      <button class="header-icon" onclick="openQuickNote()" title="Notiz erstellen">
        📝
      </button>
    `;
  }
}

/**
 * Öffne Members-Bereich (Login oder Dashboard)
 * Automatisch zum Login ODER Mitgliederbereich je nach Status
 */
async function openMembersLogin() {
  await initSupabase();
  
  if (!currentUser) {
    // Nicht eingeloggt → Zum Login
    window.location.href = 'members.html';
  } else {
    // Eingeloggt → Zum Mitgliederbereich
    window.location.href = 'members.html?tab=bookmarks';
  }
}

// Alias für Konsistenz
async function openMembersArea() {
  await openMembersLogin();
}

/**
 * Quick-Save für letzten markierten Text
 */
let lastSelection = '';
let lastSelectionContext = null;

// Text-Selektion tracken
document.addEventListener('mouseup', function() {
  const selection = window.getSelection().toString().trim();
  if (selection.length > 10) {
    lastSelection = selection;
    lastSelectionContext = {
      before: getContextBefore(selection, 100),
      after: getContextAfter(selection, 100)
    };
  }
});

async function quickSaveQuote() {
  if (!lastSelection) {
    showIconNotification('Bitte zuerst Text markieren!', 'info');
    return;
  }
  
  await initSupabase();
  
  if (!currentUser) {
    openMembersLogin();
    return;
  }
  
  try {
    const { error } = await supabaseClient
      .from('quotes')
      .insert({
        user_id: currentUser.id,
        quote_text: lastSelection,
        ga_reference: currentContext.gaNumber || 'Unbekannt',
        lecture_title: currentContext.lectureTitle || '',
        context_before: lastSelectionContext?.before || '',
        context_after: lastSelectionContext?.after || '',
        personal_note: '',
        tags: [],
        is_public: false
      });
    
    if (error) throw error;
    
    showIconNotification('✓ Zitat gespeichert!', 'success');
    highlightLastSelection('#ffffcc');
  } catch (error) {
    console.error('Fehler:', error);
    showIconNotification('✗ Fehler beim Speichern', 'error');
  }
}

async function quickSaveBookmark() {
  if (!lastSelection) {
    showIconNotification('Bitte zuerst Text markieren!', 'info');
    return;
  }
  
  await initSupabase();
  
  if (!currentUser) {
    openMembersLogin();
    return;
  }
  
  try {
    const { error } = await supabaseClient
      .from('bookmarks')
      .insert({
        user_id: currentUser.id,
        ga_number: currentContext.gaNumber || 'Unbekannt',
        lecture_title: currentContext.lectureTitle || '',
        paragraph_id: null,
        paragraph_text: lastSelection,
        note: '',
        tags: []
      });
    
    if (error) throw error;
    
    showIconNotification('✓ Bookmark gespeichert!', 'success');
    highlightLastSelection('#ccffcc');
  } catch (error) {
    console.error('Fehler:', error);
    showIconNotification('✗ Fehler beim Speichern', 'error');
  }
}

function openQuickNote() {
  if (lastSelection) {
    const noteData = encodeURIComponent(JSON.stringify({
      content: `Aus [[${currentContext.gaNumber || 'Unbekannt'}]]:\n\n"${lastSelection}"\n\n`,
      title: `Notiz zu ${currentContext.gaNumber || 'Vortrag'}`
    }));
    window.open(`members.html?tab=notes&prefill=${noteData}`, '_blank');
  } else {
    window.open('members.html?tab=notes', '_blank');
  }
}

/**
 * Icon-spezifische Notification (kleiner, neben Icons)
 */
function showIconNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 90px;
    padding: 12px 20px;
    background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
    color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 9998;
    animation: slideInRight 0.3s ease;
    font-size: 14px;
    white-space: nowrap;
  `;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideOutRight 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 2500);
}

function highlightLastSelection(color) {
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
    console.log('Highlight nicht möglich');
  }
}

/**
 * Styles für Header Icons
 */
function addHeaderIconStyles() {
  if (document.querySelector('#header-icon-styles')) return;
  
  const style = document.createElement('style');
  style.id = 'header-icon-styles';
  style.textContent = `
    .header-icon {
      width: 36px;
      height: 36px;
      background: transparent;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      font-size: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease;
      padding: 0;
      color: #467886;
      filter: grayscale(100%) brightness(0) saturate(100%);
      opacity: 0.7;
    }
    
    .header-icon:hover {
      opacity: 1;
      transform: scale(1.15);
      filter: none;
    }
    
    .header-icon.active {
      opacity: 1;
      filter: none;
    }
    
    .header-icon:active {
      transform: scale(0.9);
    }
    
    @keyframes slideInRight {
      from {
        transform: translateX(100px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    
    @keyframes slideOutRight {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(100px);
        opacity: 0;
      }
    }
    
    /* Responsive: Auf Mobilgeräten etwas kleiner */
    @media (max-width: 768px) {
      #member-header-icons {
        top: 10px;
        right: 10px;
      }
      
      .header-icon {
        width: 32px;
        height: 32px;
        font-size: 18px;
      }
    }
  `;
  document.head.appendChild(style);
}

/**
 * Login-Status überwachen und Icons aktualisieren
 */
async function monitorLoginStatus() {
  // Alle 30 Sekunden prüfen
  setInterval(async () => {
    const oldStatus = currentUser !== null;
    await initSupabase();
    const newStatus = currentUser !== null;
    
    if (oldStatus !== newStatus) {
      updateHeaderIcons();
    }
  }, 30000);
}

/**
 * Globale Initialisierung
 */
window.initMemberHeaderIcons = async function(gaNumber, lectureTitle) {
  currentContext = { gaNumber, lectureTitle };
  await createMemberHeaderIcons();
  monitorLoginStatus();
  console.log('✓ Member Header Icons aktiviert');
};

// Funktionen global verfügbar machen
window.openMembersLogin = openMembersLogin;
window.openMembersArea = openMembersArea;
window.quickSaveQuote = quickSaveQuote;
window.quickSaveBookmark = quickSaveBookmark;
window.openQuickNote = openQuickNote;

