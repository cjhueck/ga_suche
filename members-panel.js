// ============================================
// GA-Suche - Mitglieder Panel Integration
// Zeigt Mitgliederbereich im Summary Panel
// ============================================

let membersPanelActive = false;
let currentMembersTab = 'bookmarks';
let savedScrollPositions = {
  summaryPanel: 0,
  summaryContent: 0,
  membersTabContent: 0
}; // Globale Variable für ALLE Scroll-Positionen
let savedPanelTop = null; // Speichere die top-Position des Panels
let membersScrollObserver = null; // MutationObserver für Scroll-Position
let sortOrder = 'desc'; // 'asc' oder 'desc' - Standard: neueste zuerst
let multiDeleteMode = false; // Multi-Delete-Modus aktiviert?

/**
 * Speichert die aktuelle Scroll-Position ALLER scrollenden Elemente UND die Panel-Position
 */
function saveMembersScrollPosition() {
  const summaryPanel = document.getElementById('summary-panel');
  const summaryContent = document.getElementById('summary-content');
  const membersTabContent = document.getElementById('members-tab-content');
  
  savedScrollPositions = {
    summaryPanel: summaryPanel ? summaryPanel.scrollTop : 0,
    summaryContent: summaryContent ? summaryContent.scrollTop : 0,
    membersTabContent: membersTabContent ? membersTabContent.scrollTop : 0
  };
  
  // ENTFERNT: top-Position wird NICHT mehr gespeichert - updateHeaderPosition() soll sie frei setzen können
  savedPanelTop = null;
  
  console.log('[MB-SCROLL] Alle Positionen gespeichert:', savedScrollPositions, 'Panel top:', savedPanelTop);
}

/**
 * Stellt ALLE gespeicherten Scroll-Positionen UND Panel-Position wieder her
 */
function restoreMembersScrollPosition() {
  const summaryPanel = document.getElementById('summary-panel');
  const summaryContent = document.getElementById('summary-content');
  const membersTabContent = document.getElementById('members-tab-content');
  
  // ENTFERNT: top-Position wird NICHT mehr wiederhergestellt - updateHeaderPosition() soll sie dynamisch setzen
  
  if (summaryPanel && savedScrollPositions.summaryPanel > 0) {
    summaryPanel.scrollTop = savedScrollPositions.summaryPanel;
  }
  
  if (summaryContent && savedScrollPositions.summaryContent > 0) {
    summaryContent.scrollTop = savedScrollPositions.summaryContent;
  }
  
  if (membersTabContent && savedScrollPositions.membersTabContent > 0) {
    membersTabContent.scrollTop = savedScrollPositions.membersTabContent;
  }
  
  console.log('[MB-SCROLL] Alle Positionen + Panel top wiederhergestellt:', savedScrollPositions, savedPanelTop);
}

/**
 * Startet die automatische Wiederherstellung der Scroll-Position bei DOM-Änderungen
 */
function startScrollPositionProtection() {
  // Stoppe vorherigen Observer falls vorhanden
  stopScrollPositionProtection();
  
  const summaryContent = document.getElementById('summary-content');
  if (!summaryContent) return;
  
  console.log('[MB-SCROLL] Starte Scroll-Position Schutz für ALLE Ebenen');
  
  // MutationObserver um DOM-Änderungen zu erkennen
  membersScrollObserver = new MutationObserver((mutations) => {
    if (!membersPanelActive || !window.membersNavigating) return;
    
    // Stelle ALLE Scroll-Positionen UND Panel-Top wieder her
    const summaryPanel = document.getElementById('summary-panel');
    const summaryContent = document.getElementById('summary-content');
    const membersTabContent = document.getElementById('members-tab-content');
    
    let restored = false;
    
    // ENTFERNT: top-Position wird NICHT mehr wiederhergestellt - updateHeaderPosition() soll sie dynamisch setzen
    
    if (summaryPanel && savedScrollPositions.summaryPanel > 0) {
      if (Math.abs(summaryPanel.scrollTop - savedScrollPositions.summaryPanel) > 5) {
        summaryPanel.scrollTop = savedScrollPositions.summaryPanel;
        restored = true;
      }
    }
    
    if (summaryContent && savedScrollPositions.summaryContent > 0) {
      if (Math.abs(summaryContent.scrollTop - savedScrollPositions.summaryContent) > 5) {
        summaryContent.scrollTop = savedScrollPositions.summaryContent;
        restored = true;
      }
    }
    
    if (membersTabContent && savedScrollPositions.membersTabContent > 0) {
      if (Math.abs(membersTabContent.scrollTop - savedScrollPositions.membersTabContent) > 5) {
        membersTabContent.scrollTop = savedScrollPositions.membersTabContent;
        restored = true;
      }
    }
    
    if (restored) {
      console.log('[MB-SCROLL] Auto-Wiederherstellung bei DOM-Änderung (multi-level + top)');
    }
  });
  
  // Beobachte Änderungen im summary-content
  membersScrollObserver.observe(summaryContent, {
    childList: true,
    subtree: true,
    attributes: false
  });
}

/**
 * Stoppt die automatische Wiederherstellung
 */
function stopScrollPositionProtection() {
  if (membersScrollObserver) {
    membersScrollObserver.disconnect();
    membersScrollObserver = null;
  }
  
  console.log('[MB-SCROLL] Scroll-Position Schutz gestoppt');
}

/**
 * Öffnet members.html in einem neuen Fenster mit window.opener
 */
function openMembersWindow() {
  const membersWindow = window.open('members.html', '_blank');
  if (membersWindow) {
    console.log('[MEMBERS-WINDOW] Neues Fenster geöffnet, window.opener sollte gesetzt sein');
  } else {
    console.error('[MEMBERS-WINDOW] Popup-Blocker verhindert das Öffnen des Fensters');
    alert('Bitte erlauben Sie Popups für diese Seite, um den Mitgliederbereich zu öffnen.');
  }
}

/**
 * Öffnet den Mitgliederbereich im Summary Panel
 */
async function openMembersPanel() {
  await initSupabase();
  
  if (!currentUser) {
    // Zeige Login-Form im Panel
    showMembersLoginPanel();
    return;
  }
  
  // Zeige Mitglieder-Content
  showMembersContent();
}

/**
 * Login-Form im Summary Panel anzeigen
 */
function showMembersLoginPanel() {
  const summaryPanel = document.getElementById('summary-panel');
  const summaryContent = document.getElementById('summary-content');
  const resizeHandle = document.getElementById('verticalResizeHandle');
  
  if (!summaryPanel || !summaryContent) return;
  
  membersPanelActive = true;
  
  // Panel öffnen
  summaryPanel.classList.add('visible');
  if (resizeHandle) {
    resizeHandle.classList.add('visible');
  }
  summaryPanel.style.width = '350px';
  summaryPanel.style.minWidth = '350px';
  summaryPanel.style.marginRight = '0px';
  summaryPanel.style.display = 'block'; // Explizit sichtbar machen
  summaryPanel.style.opacity = '1';
  summaryPanel.style.visibility = 'visible';
  document.body.classList.remove('summary-panel-collapsed');
  
  // Setze Klasse auf summary-panel und summary-content
  summaryPanel.classList.add('has-members-panel');
  summaryContent.classList.add('has-members-panel');
  
  // Login-Form HTML
  summaryContent.innerHTML = `
    <div class="members-panel">
      <div class="members-header">
        <h2>Mitglieder Login</h2>
        <button class="close-btn" onclick="closeMembersPanel()">×</button>
      </div>
      
      <div class="members-login-form">
        <p class="login-description">Nach Anmeldung können Sie Zitate und Bookmarks abspeichern, mit Schlagworten versehen, ordnen und kommentieren sowie sich mit anderen Mitgliedern per Chat austauschen.</p>
        <div id="login-message"></div>
        
        <div id="login-form-content">
          <div class="form-group">
            <label for="members-email">E-Mail</label>
            <input type="email" id="members-email" />
          </div>
          
          <div class="form-group">
            <label for="members-password">Passwort</label>
            <input type="password" id="members-password" onkeypress="if(event.key==='Enter') handleMembersLogin()" />
          </div>
          
          <button onclick="handleMembersLogin()" class="primary-btn">Anmelden</button>
          
          <p class="auth-switch">
            <a href="#" onclick="showMembersRegister(); return false;">Noch kein Account? Registrieren</a>
          </p>
        </div>
        
        <div id="register-form-content" style="display:none;">
          <div class="form-group">
            <label for="members-reg-email">E-Mail</label>
            <input type="email" id="members-reg-email" />
          </div>
          
          <div class="form-group">
            <label for="members-reg-password">Passwort (min. 6 Zeichen)</label>
            <input type="password" id="members-reg-password" onkeypress="if(event.key==='Enter') handleMembersRegister()" />
          </div>
          
          <button onclick="handleMembersRegister()" class="primary-btn">Registrieren</button>
          
          <p class="auth-switch">
            <a href="#" onclick="showMembersLogin(); return false;">Bereits registriert? Anmelden</a>
          </p>
        </div>
      </div>
    </div>
  `;
  
  // WICHTIG: Verwende zentrale Synchronisationsfunktion für Main-Container und RH
  // (keine manuelle Setzung - wie in allen anderen Fällen auch)
  if (typeof resetPanelSync === 'function') {
    resetPanelSync(); // Setze Sync zurück, damit neue Breite erkannt wird
  }
  
  // Positioniere Panel unter dem Header (wie bei TOC) und synchronisiere Layout
  setTimeout(() => {
    if (typeof updateHeaderPosition === 'function') {
      updateHeaderPosition();
    }
    // Main-Container wird automatisch von syncMainContainerWithPanel() angepasst
    if (typeof syncMainContainerWithPanel === 'function') {
      syncMainContainerWithPanel();
    }
    // RH wird von updateResizeHandle() positioniert
    if (typeof updateResizeHandle === 'function') {
      updateResizeHandle();
    }
  }, 100);
}

/**
 * Mitglieder-Content im Summary Panel anzeigen
 */
async function showMembersContent() {
  const summaryPanel = document.getElementById('summary-panel');
  const summaryContent = document.getElementById('summary-content');
  const resizeHandle = document.getElementById('verticalResizeHandle');
  const mainContainer = document.getElementById('main-container');
  
  if (!summaryPanel || !summaryContent) return;
  
  membersPanelActive = true;
  
  // Panel öffnen
  summaryPanel.classList.add('visible');
  if (resizeHandle) {
    resizeHandle.classList.add('visible');
  }
  const mbWidth = 400; // Breite für Mitgliederbereich
  summaryPanel.style.width = mbWidth + 'px';
  summaryPanel.style.minWidth = mbWidth + 'px';
  summaryPanel.style.marginRight = '0px';
  summaryPanel.style.display = 'block'; // Explizit sichtbar machen
  summaryPanel.style.opacity = '1';
  summaryPanel.style.visibility = 'visible';
  document.body.classList.remove('summary-panel-collapsed');
  
  // WICHTIG: Verwende zentrale Synchronisationsfunktion für Main-Container und RH
  // (keine manuelle Setzung - wie in allen anderen Fällen auch)
  if (typeof resetPanelSync === 'function') {
    resetPanelSync(); // Setze Sync zurück, damit neue Breite erkannt wird
  }
  
  // Warte kurz, damit die Panel-Breite korrekt gesetzt ist, bevor zentrale Funktionen aufgerufen werden
  setTimeout(() => {
    // Main-Container wird automatisch von syncMainContainerWithPanel() angepasst (läuft alle 100ms)
    // Aber rufe es einmal direkt auf für sofortige Anpassung
    if (typeof syncMainContainerWithPanel === 'function') {
      syncMainContainerWithPanel();
    }
    // RH wird von updateResizeHandle() positioniert
    if (typeof updateResizeHandle === 'function') {
      updateResizeHandle();
    }
  }, 50);
  
  // Setze Klasse auf summary-panel und summary-content damit CSS-Regeln greifen (Fallback für :has())
  summaryPanel.classList.add('has-members-panel');
  summaryContent.classList.add('has-members-panel');
  
  // Content HTML
  summaryContent.innerHTML = `
    <div class="members-panel">
      <div class="members-header-container">
        <div class="members-header">
          <h2><a href="#" onclick="openMembersWindow(); return false;" style="color: inherit; text-decoration: none; cursor: pointer;">Mitgliederbereich</a></h2>
          <button class="close-btn" onclick="closeMembersPanel()">×</button>
        </div>
        
        <div class="members-tabs">
        <button class="members-tab ${currentMembersTab === 'bookmarks' ? 'active' : ''}" onclick="switchMembersTab('bookmarks')">Bookmarks</button>
        <button class="members-tab ${currentMembersTab === 'quotes' ? 'active' : ''}" onclick="switchMembersTab('quotes')">Zitate</button>
        <button class="members-tab ${currentMembersTab === 'notes' ? 'active' : ''}" onclick="switchMembersTab('notes')">Notizen</button>
        <button class="members-tab ${currentMembersTab === 'graph' ? 'active' : ''}" onclick="switchMembersTab('graph')">Graph</button>
        <div class="keyword-filter-tab">
          <select id="keyword-filter-select" onchange="handleKeywordFilter(this.value)" class="keyword-select-btn">
            <option value="">Schlagwörter</option>
          </select>
        </div>
        <button class="members-tab ${currentMembersTab === 'chat' ? 'active' : ''}" onclick="switchMembersTab('chat')">Chat</button>
        <button class="members-tab members-action-btn" onclick="toggleSortOrder()" title="Nach Datum sortieren">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 6h18M7 12h10M11 18h6"></path>
          </svg>
        </button>
        <button class="members-tab members-action-btn" onclick="toggleMultiDeleteMode()" title="Mehrere löschen">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
          </svg>
        </button>
        </div>
      </div>
      
      <div class="members-content" id="members-tab-content">
        <!-- Content wird dynamisch geladen -->
      </div>
    </div>
  `;
  
  // Aktuellen Tab laden - kurze Verzögerung damit API-Module geladen sind
  setTimeout(async () => {
    await loadMembersTab(currentMembersTab);
  }, 100);
  
  // Stelle sicher, dass Panel nach dem Laden sichtbar bleibt
  setTimeout(() => {
    if (summaryPanel) {
      summaryPanel.style.display = 'block';
      summaryPanel.style.opacity = '1';
      summaryPanel.style.visibility = 'visible';
    }
    if (summaryContent) {
      summaryContent.style.display = 'block';
      summaryContent.style.opacity = '1';
      summaryContent.style.visibility = 'visible';
    }
    
    // WICHTIG: Positioniere Panel unter dem Header (wie bei TOC) und RH
    if (typeof updateHeaderPosition === 'function') {
      updateHeaderPosition();
    }
    // RH nochmal aktualisieren nach dem Laden des Contents
    if (typeof updateResizeHandle === 'function') {
      updateResizeHandle();
    }
    
    console.log('[MB-OPEN] Panel und Content-Sichtbarkeit nachkorrigiert');
  }, 100);
}

/**
 * Tab wechseln
 */
async function switchMembersTab(tabName, preserveKeyword = false) {
  currentMembersTab = tabName;
  
  // Tab-Buttons aktualisieren
  document.querySelectorAll('.members-tab').forEach(tab => {
    tab.classList.remove('active');
  });
  
  // Aktiviere den richtigen Tab-Button
  const tabButtons = document.querySelectorAll('.members-tab');
  tabButtons.forEach(btn => {
    const onclickAttr = btn.getAttribute('onclick');
    if (onclickAttr && onclickAttr.includes(`'${tabName}'`)) {
      btn.classList.add('active');
    }
  });
  
  // Wenn event vorhanden ist (bei manuellem Klick), nutze es
  if (typeof event !== 'undefined' && event && event.target) {
    event.target.classList.add('active');
  }
  
  // Keyword-Filter zurücksetzen (außer wenn preserveKeyword true ist)
  const keywordSelect = document.getElementById('keyword-filter-select');
  if (keywordSelect && !preserveKeyword) {
    keywordSelect.value = '';
  }
  
  // Content laden
  await loadMembersTab(tabName);
}

/**
 * Tab-Content laden
 */
async function loadMembersTab(tabName) {
  const content = document.getElementById('members-tab-content');
  if (!content) {
    console.error('[MB-TAB] members-tab-content Element nicht gefunden!');
    return;
  }
  
  console.log('[MB-TAB] Lade Tab:', tabName);
  
  try {
    switch(tabName) {
      case 'bookmarks':
        await loadBookmarksTab(content);
        break;
      case 'quotes':
        await loadQuotesTab(content);
        break;
      case 'notes':
        loadNotesTab(content);
        break;
      case 'graph':
        loadGraphTab(content);
        break;
      case 'chat':
        await loadChatTab(content);
        break;
      default:
        console.warn('[MB-TAB] Unbekannter Tab:', tabName);
        content.innerHTML = '<div class="empty-state">Unbekannter Tab</div>';
    }
  } catch (error) {
    console.error('[MB-TAB] Fehler beim Laden des Tabs:', tabName, error);
    content.innerHTML = `<div class="empty-state">Fehler beim Laden: ${error.message}</div>`;
  }
}

/**
 * Bookmarks Tab
 */
async function loadBookmarksTab(container) {
  if (typeof getBookmarks !== 'function') {
    console.error('[MB-BOOKMARKS] getBookmarks ist nicht verfügbar!');
    container.innerHTML = '<div class="empty-state">API-Funktionen nicht geladen. Bitte Seite neu laden.</div>';
    return;
  }
  
  const result = await getBookmarks();
  
  // Lade alle Keywords aus Bookmarks und Quotes
  await updateKeywordFilterDropdownWithAllKeywords();
  
  if (!result.success || result.data.length === 0) {
    container.innerHTML = '<div class="empty-state">Noch keine Bookmarks</div>';
    return;
  }
  
  // Sortiere nach Datum
  const sortedData = [...result.data].sort((a, b) => {
    const dateA = new Date(a.created_at);
    const dateB = new Date(b.created_at);
    return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
  });
  
  // Multi-Delete-Button hinzufügen wenn Modus aktiv
  const multiDeleteHtml = multiDeleteMode ? `
    <div style="margin-bottom: 1rem; padding: 0.75rem; background: var(--background-color); border: 1px solid var(--border-color); border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
      <span style="font-size: 0.85rem; color: var(--text-color);">Auswahl-Modus aktiv</span>
      <button id="multi-delete-btn" onclick="deleteSelectedItems()" disabled style="padding: 0.4rem 0.8rem; font-size: 0.8rem; background: #c62828; color: white; border: none; border-radius: 4px; cursor: pointer;">Ausgewählte löschen</button>
    </div>
  ` : '';
  
  const html = multiDeleteHtml + sortedData.map(bookmark => `
    <div class="member-item" data-keywords="${bookmark.tags ? bookmark.tags.join(',') : ''}" data-id="${bookmark.id}">
      ${multiDeleteMode ? `<input type="checkbox" class="member-item-checkbox" data-id="${bookmark.id}" onchange="updateMultiDeleteButton()">` : ''}
      <div style="flex: 1;">
        <div class="member-item-header">
          ${bookmark.paragraph_id 
            ? `<strong><a href="#" onclick="saveMembersScrollPosition(); navigateToLectureFromMembersPanel('${bookmark.ga_number}', '${bookmark.paragraph_id}'); return false;" style="color: var(--link-color); text-decoration: none;">${bookmark.ga_number}</a></strong>`
            : `<strong>${bookmark.ga_number}</strong>`
          }
          <span class="member-item-date">${new Date(bookmark.created_at).toLocaleDateString('de-DE')}</span>
        </div>
        ${bookmark.lecture_title ? `<div class="member-item-subtitle">${bookmark.lecture_title}</div>` : ''}
        <div class="member-item-text">${bookmark.paragraph_text.substring(0, 150)}${bookmark.paragraph_text.length > 150 ? '...' : ''}</div>
        ${bookmark.note ? `<div class="member-item-note">${bookmark.note}</div>` : ''}
        ${bookmark.tags && bookmark.tags.length > 0 ? `<div class="member-item-tags">${bookmark.tags.map(tag => `<span class="tag">#${tag}</span>`).join(' ')}</div>` : ''}
        <div class="member-item-actions">
          <button class="edit-btn" onclick="editMemberBookmark('${bookmark.id}')" title="Bearbeiten">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
          </button>
          <button class="delete-btn" onclick="deleteMemberBookmark('${bookmark.id}')" title="Löschen">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 6h18"></path>
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
          </button>
        </div>
      </div>
    </div>
  `).join('');
  
  container.innerHTML = html;
  
  // Scroll-Position wiederherstellen nach Rendering
  setTimeout(() => restoreMembersScrollPosition(), 50);
}

/**
 * Quotes Tab
 */
async function loadQuotesTab(container) {
  if (typeof getQuotes !== 'function') {
    console.error('[MB-QUOTES] getQuotes ist nicht verfügbar!');
    container.innerHTML = '<div class="empty-state">API-Funktionen nicht geladen. Bitte Seite neu laden.</div>';
    return;
  }
  
  const result = await getQuotes();
  
  // Lade alle Keywords aus Bookmarks und Quotes
  await updateKeywordFilterDropdownWithAllKeywords();
  
  if (!result.success || result.data.length === 0) {
    container.innerHTML = '<div class="empty-state">Noch keine Zitate</div>';
    return;
  }
  
  // Sortiere nach Datum
  const sortedData = [...result.data].sort((a, b) => {
    const dateA = new Date(a.created_at);
    const dateB = new Date(b.created_at);
    return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
  });
  
  // Multi-Delete-Button hinzufügen wenn Modus aktiv
  const multiDeleteHtml = multiDeleteMode ? `
    <div style="margin-bottom: 1rem; padding: 0.75rem; background: var(--background-color); border: 1px solid var(--border-color); border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
      <span style="font-size: 0.85rem; color: var(--text-color);">Auswahl-Modus aktiv</span>
      <button id="multi-delete-btn" onclick="deleteSelectedItems()" disabled style="padding: 0.4rem 0.8rem; font-size: 0.8rem; background: #c62828; color: white; border: none; border-radius: 4px; cursor: pointer;">Ausgewählte löschen</button>
    </div>
  ` : '';
  
  const html = multiDeleteHtml + sortedData.map(quote => `
    <div class="member-item" data-keywords="${quote.tags ? quote.tags.join(',') : ''}" data-id="${quote.id}">
      ${multiDeleteMode ? `<input type="checkbox" class="member-item-checkbox" data-id="${quote.id}" onchange="updateMultiDeleteButton()">` : ''}
      <div style="flex: 1;">
        <div class="member-item-header">
          ${quote.paragraph_id 
            ? `<strong><a href="#" onclick="saveMembersScrollPosition(); navigateToLectureFromMembersPanel('${quote.ga_reference}', '${quote.paragraph_id}'); return false;" style="color: var(--link-color); text-decoration: none;">${quote.ga_reference}</a></strong>`
            : `<strong>${quote.ga_reference}</strong>`
          }
          <span class="member-item-date">${new Date(quote.created_at).toLocaleDateString('de-DE')}</span>
        </div>
        <div class="member-item-quote">"${quote.quote_text.substring(0, 150)}${quote.quote_text.length > 150 ? '...' : ''}"</div>
        ${quote.personal_note ? `<div class="member-item-note">${quote.personal_note}</div>` : ''}
        ${quote.tags && quote.tags.length > 0 ? `<div class="member-item-tags">${quote.tags.map(tag => `<span class="tag">#${tag}</span>`).join(' ')}</div>` : ''}
        <div class="member-item-actions">
          <button class="edit-btn" onclick="editMemberQuote('${quote.id}')" title="Bearbeiten">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
          </button>
          <button class="delete-btn" onclick="deleteMemberQuote('${quote.id}')" title="Löschen">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 6h18"></path>
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
          </button>
        </div>
      </div>
    </div>
  `).join('');
  
  container.innerHTML = html;
  
  // Scroll-Position wiederherstellen nach Rendering
  setTimeout(() => restoreMembersScrollPosition(), 50);
}

/**
 * Navigiere zu Vortrag aus Members Panel (behält Panel offen)
 * @param {string} lectureId - Die Vortrags-ID (z.B. "GA121/6")
 * @param {string} targetIndex - Optional: Der Index des Absatzes zum Scrollen
 */
async function navigateToLectureFromMembersPanel(lectureId, targetIndex = null) {
  console.log('[MB-NAVIGATION] Navigiere zu Vortrag:', lectureId, 'mit targetIndex:', targetIndex);
  
  const summaryPanel = document.getElementById('summary-panel');
  const summaryContent = document.getElementById('summary-content');
  
  if (!summaryPanel || !membersPanelActive) {
    console.error('[MB-NAVIGATION] Members Panel nicht aktiv');
    return;
  }
  
  const mbWidth = 400;
  
  // Klone den GESAMTEN Members-Content
  const savedContentNode = summaryContent ? summaryContent.cloneNode(true) : null;
  console.log('[MB-NAVIGATION] Members Content geklont');
  
  // Setze Flag
  window.membersNavigating = true;
  
  // Extrahiere GA-Nummer
  const gaNumber = lectureId.split('/')[0];
  
  // Blockiere buildTableOfContents
  const originalBuildTOC = window.buildTableOfContents;
  window.buildTableOfContents = function() {
    if (window.membersNavigating) {
      console.log('[MB-NAVIGATION] buildTableOfContents blockiert');
      return;
    }
    return originalBuildTOC ? originalBuildTOC.apply(this, arguments) : null;
  };
  
  // Prüfe ob wir bereits im Texte-Tab sind
  const texteTab = document.getElementById('texte-tab');
  const isInTexteTab = texteTab && texteTab.classList.contains('active');
  
  // Nur Tab wechseln wenn nötig - ABER OHNE Panel zu schließen
  if (!isInTexteTab && typeof switchTab === 'function') {
    // Temporär Flag setzen damit switchTab das Panel nicht schließt
    switchTab('texte');
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  
  // Setze den GA-Filter (nur wenn GA-Band wechselt)
  const texteGAFilter = document.getElementById('texteGAFilter');
  if (texteGAFilter && gaNumber) {
    const currentGA = texteGAFilter.value;
    if (currentGA !== gaNumber) {
      texteGAFilter.value = gaNumber;
      console.log(`[MB-NAVIGATION] GA-Filter geändert von ${currentGA} zu ${gaNumber}`);
    }
  }
  
  // Lade Vortrag - EINFACH wie showLectureFromOverview()
  if (typeof showLecture === 'function') {
    await showLecture(lectureId, targetIndex, []);
  }
  
  // SOFORT DANACH: Stelle Members Content wieder her (showLecture hat es überschrieben!)
  if (savedContentNode && summaryContent) {
    const newNode = savedContentNode.cloneNode(true);
    summaryContent.parentNode.replaceChild(newNode, summaryContent);
    console.log('[MB-NAVIGATION] Members Content wiederhergestellt');
  }
  
  // Stelle Panel-Eigenschaften sicher
  if (summaryPanel) {
    summaryPanel.style.width = mbWidth + 'px';
    summaryPanel.style.minWidth = mbWidth + 'px';
    summaryPanel.classList.add('visible');
    summaryPanel.style.display = 'block';
  }
  
  // WICHTIG: Verwende zentrale Synchronisationsfunktion für Main-Container und RH
  // (keine manuelle Setzung - wie in allen anderen Fällen auch)
  if (typeof resetPanelSync === 'function') {
    resetPanelSync(); // Setze Sync zurück, damit neue Breite erkannt wird
  }
  
  // Warte kurz, damit die Panel-Breite korrekt gesetzt ist, bevor zentrale Funktionen aufgerufen werden
  setTimeout(() => {
    // Main-Container wird automatisch von syncMainContainerWithPanel() angepasst
    if (typeof syncMainContainerWithPanel === 'function') {
      syncMainContainerWithPanel();
    }
    // RH wird von updateResizeHandle() positioniert
    if (typeof updateResizeHandle === 'function') {
      updateResizeHandle();
    }
  }, 50);
  
  // Lade GA-Übersicht im linken Panel (wie beim normalen Vortragswechsel)
  if (gaNumber && typeof loadGAOverviewInSidePanelOnly === 'function') {
    await loadGAOverviewInSidePanelOnly(gaNumber);
  }
  
  // Cleanup
  setTimeout(() => {
    window.membersNavigating = false;
    
    if (originalBuildTOC) {
      window.buildTableOfContents = originalBuildTOC;
    }
    
    // Finale Position - verwende zentrale Funktionen
    if (typeof updateHeaderPosition === 'function') {
      updateHeaderPosition();
    }
    // Main-Container und RH werden automatisch synchronisiert
    if (typeof syncMainContainerWithPanel === 'function') {
      syncMainContainerWithPanel();
    }
    if (typeof updateResizeHandle === 'function') {
      updateResizeHandle();
    }
    
    // Finale Scroll-Wiederherstellung
    setTimeout(() => {
      restoreMembersScrollPosition();
      console.log('[MB-NAVIGATION] Abgeschlossen');
    }, 50);
  }, 200);
}

/**
 * Notes Tab
 */
function loadNotesTab(container) {
  updateKeywordFilterDropdown([]); // Keine Keywords für Notes
  
  container.innerHTML = `
    <div class="notes-editor">
      <textarea id="members-note-content" placeholder="Schreibe deine Notiz hier...

Verwende:
- [[Wiki Links]] für Verknüpfungen
- #Tags für Kategorien
- GA123/4 für GA-Referenzen"></textarea>
      <button class="primary-btn" onclick="saveMemberNote()">Notiz speichern</button>
      <div id="notes-list"></div>
    </div>
  `;
  
  loadSavedNotes();
}

async function loadSavedNotes() {
  const result = await getNotes();
  const list = document.getElementById('notes-list');
  
  if (!result.success || result.data.length === 0) {
    list.innerHTML = '<div class="empty-state" style="margin-top: 1rem;">Noch keine Notizen</div>';
    return;
  }
  
  const html = result.data.map(note => `
    <div class="member-item">
      <div class="member-item-header">
        <strong>${note.title || 'Unbenannte Notiz'}</strong>
        <span class="member-item-date">${new Date(note.created_at).toLocaleDateString('de-DE')}</span>
      </div>
      <div class="member-item-text">${note.content.substring(0, 100)}${note.content.length > 100 ? '...' : ''}</div>
      ${note.tags.length > 0 ? `<div class="member-item-tags">${note.tags.map(tag => `<span class="tag">#${tag}</span>`).join(' ')}</div>` : ''}
      <button class="delete-btn" onclick="deleteMemberNote('${note.id}')">🗑️</button>
    </div>
  `).join('');
  
  list.innerHTML = html;
}

async function saveMemberNote() {
  const content = document.getElementById('members-note-content').value.trim();
  
  if (!content) {
    alert('Bitte Text eingeben');
    return;
  }
  
  const title = content.split('\n')[0].substring(0, 50);
  const result = await createNote(title, content, false);
  
  if (result.success) {
    document.getElementById('members-note-content').value = '';
    await loadSavedNotes();
    alert('✓ Notiz gespeichert!');
  } else {
    alert('✗ Fehler beim Speichern');
  }
}

/**
 * Graph Tab
 */
function loadGraphTab(container) {
  updateKeywordFilterDropdown([]); // Keine Keywords für Graph
  
  container.innerHTML = `
    <div class="graph-placeholder">
      <div class="empty-state">
        Graph-Visualisierung<br>
        <small style="opacity: 0.7;">Zeigt Verbindungen zwischen<br>Notizen, Tags und GA-Referenzen</small>
      </div>
      <button class="primary-btn" onclick="generateMemberGraph()">Graph generieren</button>
    </div>
    <div id="graph-container"></div>
  `;
}

async function generateMemberGraph() {
  const result = await generateGraphData();
  
  if (!result.success) {
    alert('Fehler beim Generieren des Graphs');
    return;
  }
  
  const container = document.getElementById('graph-container');
  container.innerHTML = `
    <div class="graph-stats">
      <div>${result.data.nodes.filter(n => n.type === 'note').length} Notizen</div>
      <div>${result.data.links.length} Verbindungen</div>
    </div>
    <div class="graph-nodes">
      ${result.data.nodes.filter(n => n.type === 'note').map(node => `
        <div class="graph-node">${node.label}</div>
      `).join('')}
    </div>
  `;
}

/**
 * Chat Tab
 */
async function loadChatTab(container) {
  updateKeywordFilterDropdown([]); // Keine Keywords für Chat
  
  container.innerHTML = `
    <div class="chat-panel">
      <div id="chat-messages" class="chat-messages"></div>
      <div class="chat-input">
        <textarea id="chat-message-input" placeholder="Nachricht schreiben..." onkeypress="if(event.key==='Enter' && !event.shiftKey){sendMemberChatMessage(); return false;}"></textarea>
        <button onclick="sendMemberChatMessage()">📤</button>
      </div>
    </div>
  `;
  
  await loadChatMessages();
  
  // Realtime Listener
  window.chatChannel = subscribeToChatMessages('general', (message) => {
    appendChatMessage(message);
  });
}

async function loadChatMessages() {
  const result = await getChatMessages('general', 50);
  const container = document.getElementById('chat-messages');
  
  if (!result.success || result.data.length === 0) {
    container.innerHTML = '<div class="empty-state">Noch keine Nachrichten</div>';
    return;
  }
  
  container.innerHTML = result.data.map(msg => `
    <div class="chat-message">
      <div class="chat-message-header">
        <strong>${msg.user_name}</strong>
        <span>${new Date(msg.created_at).toLocaleTimeString('de-DE', {hour: '2-digit', minute: '2-digit'})}</span>
      </div>
      <div class="chat-message-text">${msg.message}</div>
    </div>
  `).join('');
  
  // Scroll to bottom
  container.scrollTop = container.scrollHeight;
}

function appendChatMessage(message) {
  const container = document.getElementById('chat-messages');
  if (!container) return;
  
  const isEmpty = container.querySelector('.empty-state');
  if (isEmpty) {
    container.innerHTML = '';
  }
  
  container.innerHTML += `
    <div class="chat-message">
      <div class="chat-message-header">
        <strong>${message.user_name}</strong>
        <span>${new Date(message.created_at).toLocaleTimeString('de-DE', {hour: '2-digit', minute: '2-digit'})}</span>
      </div>
      <div class="chat-message-text">${message.message}</div>
    </div>
  `;
  
  container.scrollTop = container.scrollHeight;
}

async function sendMemberChatMessage() {
  const input = document.getElementById('chat-message-input');
  const message = input.value.trim();
  
  if (!message) return;
  
  const result = await sendChatMessage(message, 'general');
  
  if (result.success) {
    input.value = '';
  } else {
    alert('Fehler beim Senden');
  }
}

/**
 * Edit Handlers
 */
async function editMemberBookmark(id) {
  try {
    // Hole Bookmark-Daten
    const result = await getBookmarks();
    if (!result.success) {
      alert('Fehler beim Laden des Bookmarks');
      return;
    }
    
    const bookmark = result.data.find(b => b.id === id);
    if (!bookmark) {
      alert('Bookmark nicht gefunden');
      return;
    }
    
    // Zeige Bearbeitungs-Dialog
    const editResult = await showEditDialog('Bookmark', {
      text: bookmark.paragraph_text,
      keywords: bookmark.tags ? bookmark.tags.join(', ') : '',
      note: bookmark.note || ''
    });
    
    if (editResult === null) {
      // Benutzer hat abgebrochen
      return;
    }
    
    const { keywords, note } = editResult;
    const tags = keywords
      .split(',')
      .map(kw => kw.trim())
      .filter(kw => kw.length > 0);
    
    // Update in Supabase
    const updateResult = await updateBookmark(id, {
      tags: tags,
      note: note || ''
    });
    
    if (updateResult.success) {
      await loadMembersTab('bookmarks');
    } else {
      alert('Fehler beim Speichern: ' + updateResult.error);
    }
  } catch (error) {
    console.error('Fehler beim Bearbeiten:', error);
    alert('Fehler beim Bearbeiten des Bookmarks');
  }
}

async function editMemberQuote(id) {
  try {
    // Hole Zitat-Daten
    const result = await getQuotes();
    if (!result.success) {
      alert('Fehler beim Laden des Zitats');
      return;
    }
    
    const quote = result.data.find(q => q.id === id);
    if (!quote) {
      alert('Zitat nicht gefunden');
      return;
    }
    
    // Zeige Bearbeitungs-Dialog
    const editResult = await showEditDialog('Zitat', {
      text: quote.quote_text,
      keywords: quote.tags ? quote.tags.join(', ') : '',
      note: quote.personal_note || ''
    });
    
    if (editResult === null) {
      // Benutzer hat abgebrochen
      return;
    }
    
    const { keywords, note } = editResult;
    const tags = keywords
      .split(',')
      .map(kw => kw.trim())
      .filter(kw => kw.length > 0);
    
    // Update in Supabase
    const updateResult = await updateQuote(id, {
      tags: tags,
      personal_note: note || ''
    });
    
    if (updateResult.success) {
      await loadMembersTab('quotes');
    } else {
      alert('Fehler beim Speichern: ' + updateResult.error);
    }
  } catch (error) {
    console.error('Fehler beim Bearbeiten:', error);
    alert('Fehler beim Bearbeiten des Zitats');
  }
}

/**
 * Bearbeitungs-Dialog anzeigen
 */
function showEditDialog(type, data) {
  return new Promise((resolve) => {
    // Erstelle Dialog
    const dialog = document.createElement('div');
    dialog.className = 'keyword-dialog-overlay';
    dialog.innerHTML = `
      <div class="keyword-dialog">
        <div class="keyword-dialog-header">
          <h3>${type} bearbeiten</h3>
        </div>
        <div class="keyword-dialog-body">
          <div class="keyword-preview">"${data.text.substring(0, 100)}${data.text.length > 100 ? '...' : ''}"</div>
          <label for="edit-keyword-input">Keywords (optional, durch Komma getrennt):</label>
          <input type="text" id="edit-keyword-input" value="${(data.keywords || '').replace(/"/g, '&quot;')}" placeholder="z.B. Karma, Reinkarnation, Ätherleib" />
          <div class="keyword-hint">Keywords helfen beim späteren Filtern und Wiederfinden</div>
          <label for="edit-note-input" style="margin-top: 1rem; display: block;">Notiz (optional):</label>
          <textarea id="edit-note-input" rows="4" placeholder="Persönliche Notiz zu diesem ${type.toLowerCase()}..." style="width: 100%; padding: 0.6rem; border: 1px solid var(--border-color); border-radius: 4px; font-family: Georgia, serif; font-size: 0.9rem; background: var(--background-color); color: var(--text-color); box-sizing: border-box; resize: vertical;">${(data.note || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</textarea>
        </div>
        <div class="keyword-dialog-footer">
          <button class="keyword-dialog-btn keyword-dialog-cancel">Abbrechen</button>
          <button class="keyword-dialog-btn keyword-dialog-save">Speichern</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Focus auf Input
    const input = dialog.querySelector('#edit-keyword-input');
    setTimeout(() => input.focus(), 100);
    
    // Event Handlers
    const saveBtn = dialog.querySelector('.keyword-dialog-save');
    const cancelBtn = dialog.querySelector('.keyword-dialog-cancel');
    const noteInput = dialog.querySelector('#edit-note-input');
    
    const handleSave = () => {
      const keywords = input.value.trim();
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
 * Delete Handlers
 */
async function deleteMemberBookmark(id) {
  if (!confirm('Bookmark wirklich löschen?')) return;
  
  const result = await deleteBookmark(id);
  if (result.success) {
    await loadMembersTab('bookmarks');
  }
}

async function deleteMemberQuote(id) {
  if (!confirm('Zitat wirklich löschen?')) return;
  
  const result = await deleteQuote(id);
  if (result.success) {
    await loadMembersTab('quotes');
  }
}

async function deleteMemberNote(id) {
  if (!confirm('Notiz wirklich löschen?')) return;
  
  const result = await deleteNote(id);
  if (result.success) {
    await loadSavedNotes();
  }
}

/**
 * Sortier-Reihenfolge umschalten
 */
function toggleSortOrder() {
  sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
  // Aktuellen Tab neu laden
  if (currentMembersTab === 'bookmarks') {
    loadMembersTab('bookmarks');
  } else if (currentMembersTab === 'quotes') {
    loadMembersTab('quotes');
  }
}

/**
 * Multi-Delete-Modus umschalten
 */
function toggleMultiDeleteMode() {
  multiDeleteMode = !multiDeleteMode;
  // Aktuellen Tab neu laden
  if (currentMembersTab === 'bookmarks') {
    loadMembersTab('bookmarks');
  } else if (currentMembersTab === 'quotes') {
    loadMembersTab('quotes');
  }
  
  // Update Button-Status
  setTimeout(() => updateMultiDeleteButton(), 100);
}

/**
 * Multi-Delete-Button Status aktualisieren
 */
function updateMultiDeleteButton() {
  const checkboxes = document.querySelectorAll('.member-item-checkbox:checked');
  const deleteBtn = document.getElementById('multi-delete-btn');
  
  if (deleteBtn) {
    if (checkboxes.length > 0) {
      deleteBtn.disabled = false;
      deleteBtn.textContent = `${checkboxes.length} löschen`;
    } else {
      deleteBtn.disabled = true;
      deleteBtn.textContent = 'Ausgewählte löschen';
    }
  }
}

/**
 * Ausgewählte Items löschen
 */
async function deleteSelectedItems() {
  const checkboxes = document.querySelectorAll('.member-item-checkbox:checked');
  if (checkboxes.length === 0) return;
  
  if (!confirm(`Wirklich ${checkboxes.length} ${currentMembersTab === 'bookmarks' ? 'Bookmark(s)' : 'Zitat(e)'} löschen?`)) {
    return;
  }
  
  const ids = Array.from(checkboxes).map(cb => cb.dataset.id);
  
  try {
    if (currentMembersTab === 'bookmarks') {
      for (const id of ids) {
        await deleteBookmark(id);
      }
    } else if (currentMembersTab === 'quotes') {
      for (const id of ids) {
        await deleteQuote(id);
      }
    }
    
    // Multi-Delete-Modus beenden und Tab neu laden
    multiDeleteMode = false;
    await loadMembersTab(currentMembersTab);
  } catch (error) {
    console.error('Fehler beim Löschen:', error);
    alert('Fehler beim Löschen einiger Items');
  }
}

// Cache für die letzten markierten Lecture-IDs, um Icons nach DOM-Änderungen wiederherzustellen
let lastMarkedLectureId = null;
let lastBookmarksData = null;
let lastQuotesData = null;

/**
 * Markiere Absätze im Viewer, die bereits Bookmarks oder Zitate haben
 */
async function markParagraphsWithBookmarksAndQuotes(lectureId) {
  try {
    // Prüfe ob User angemeldet ist
    if (typeof currentUser === 'undefined' || !currentUser) {
      return; // Nicht angemeldet - keine Markierungen
    }
    
    // Lade alle Bookmarks und Zitate für diesen Vortrag
    const [bookmarksResult, quotesResult] = await Promise.all([
      getBookmarks(),
      getQuotes()
    ]);
    
    if (!bookmarksResult.success && !quotesResult.success) {
      return; // Fehler beim Laden
    }
    
    // Cache für spätere Wiederherstellung
    lastMarkedLectureId = lectureId;
    lastBookmarksData = bookmarksResult;
    lastQuotesData = quotesResult;
    
    // Sammle alle paragraph_ids für diesen Vortrag
    const paragraphIds = new Set();
    
    if (bookmarksResult.success && bookmarksResult.data) {
      bookmarksResult.data
        .filter(b => b.ga_number === lectureId && b.paragraph_id)
        .forEach(b => paragraphIds.add(b.paragraph_id));
    }
    
    if (quotesResult.success && quotesResult.data) {
      quotesResult.data
        .filter(q => q.ga_reference === lectureId && q.paragraph_id)
        .forEach(q => paragraphIds.add(q.paragraph_id));
    }
    
    // Markiere alle Absätze im Viewer
    paragraphIds.forEach(paraId => {
      addBookmarkQuoteIndicator(paraId, lectureId, bookmarksResult, quotesResult);
    });
  } catch (error) {
    console.error('Fehler beim Markieren der Absätze:', error);
  }
}

/**
 * Fügt ein Bookmark/Quote-Icon zu einem Absatz hinzu
 */
function addBookmarkQuoteIndicator(paraId, lectureId, bookmarksResult, quotesResult) {
  const paraElement = document.getElementById(`para-${paraId}`);
  if (!paraElement) return;
  
  // Prüfe ob Icon bereits vorhanden ist (auch nach DOM-Manipulationen)
  const existingIndicator = paraElement.querySelector('.bookmark-quote-indicator');
  if (existingIndicator) return; // Bereits vorhanden
  
  // Prüfe ob Bookmark oder Zitat (oder beides)
  const hasBookmark = bookmarksResult.success && bookmarksResult.data.some(b => 
    b.ga_number === lectureId && b.paragraph_id === paraId
  );
  const hasQuote = quotesResult.success && quotesResult.data.some(q => 
    q.ga_reference === lectureId && q.paragraph_id === paraId
  );
  
  // Erstelle Markierung
  const indicator = document.createElement('span');
  indicator.className = 'bookmark-quote-indicator';
  indicator.setAttribute('data-para-id', paraId); // Für Wiederherstellung
  indicator.title = `${hasBookmark ? 'Bookmark' : ''}${hasBookmark && hasQuote ? ' & ' : ''}${hasQuote ? 'Zitat' : ''} vorhanden - Klick zum Öffnen`;
  indicator.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
    </svg>
  `;
  indicator.onclick = (e) => {
    e.stopPropagation();
    jumpToBookmarkOrQuote(lectureId, paraId, hasBookmark, hasQuote);
  };
  
  // Füge am Anfang des Absatzes hinzu
  paraElement.style.position = 'relative';
  paraElement.insertBefore(indicator, paraElement.firstChild);
}

/**
 * Stellt Icons wieder her, die durch DOM-Manipulationen verloren gegangen sind
 */
function restoreBookmarkQuoteIndicators() {
  if (!lastMarkedLectureId || !lastBookmarksData || !lastQuotesData) return;
  
  // Sammle alle paragraph_ids für diesen Vortrag
  const paragraphIds = new Set();
  
  if (lastBookmarksData.success && lastBookmarksData.data) {
    lastBookmarksData.data
      .filter(b => b.ga_number === lastMarkedLectureId && b.paragraph_id)
      .forEach(b => paragraphIds.add(b.paragraph_id));
  }
  
  if (lastQuotesData.success && lastQuotesData.data) {
    lastQuotesData.data
      .filter(q => q.ga_reference === lastMarkedLectureId && q.paragraph_id)
      .forEach(q => paragraphIds.add(q.paragraph_id));
  }
  
  // Stelle Icons wieder her
  paragraphIds.forEach(paraId => {
    const paraElement = document.getElementById(`para-${paraId}`);
    if (paraElement && !paraElement.querySelector('.bookmark-quote-indicator')) {
      addBookmarkQuoteIndicator(paraId, lastMarkedLectureId, lastBookmarksData, lastQuotesData);
    }
  });
}

/**
 * Springe zum Bookmark oder Zitat im MB
 */
async function jumpToBookmarkOrQuote(lectureId, paragraphId, hasBookmark, hasQuote) {
  try {
    // Öffne MB falls nicht offen
    if (!membersPanelActive) {
      if (typeof openMembersPanel === 'function') {
        await openMembersPanel();
      }
    }
    
    // Entscheide welcher Tab: Bookmark hat Priorität
    const targetTab = hasBookmark ? 'bookmarks' : 'quotes';
    
    // Wechsle zum entsprechenden Tab
    if (typeof switchMembersTab === 'function') {
      await switchMembersTab(targetTab);
    }
    
    // Warte kurz, dann scrolle zum Item
    setTimeout(async () => {
      // Lade Bookmarks/Zitate erneut, um die IDs zu bekommen
      let targetItemId = null;
      
      if (hasBookmark) {
        const bookmarksResult = await getBookmarks();
        if (bookmarksResult.success && bookmarksResult.data) {
          const bookmark = bookmarksResult.data.find(b => 
            b.ga_number === lectureId && b.paragraph_id === paragraphId
          );
          if (bookmark) targetItemId = bookmark.id;
        }
      }
      
      if (!targetItemId && hasQuote) {
        const quotesResult = await getQuotes();
        if (quotesResult.success && quotesResult.data) {
          const quote = quotesResult.data.find(q => 
            q.ga_reference === lectureId && q.paragraph_id === paragraphId
          );
          if (quote) targetItemId = quote.id;
        }
      }
      
      if (targetItemId) {
        const targetItem = document.querySelector(`.member-item[data-id="${targetItemId}"]`);
        if (targetItem) {
          // Scrolle so, dass das Item ganz oben im sichtbaren Bereich erscheint
          const membersContent = document.querySelector('.members-content');
          if (membersContent) {
            // Berechne Position relativ zum scrollbaren Container
            // Verwende getBoundingClientRect() für absolute Positionen
            const containerRect = membersContent.getBoundingClientRect();
            const itemRect = targetItem.getBoundingClientRect();
            
            // Berechne die relative Position: Item-Position minus Container-Position plus aktueller Scroll
            const relativeTop = itemRect.top - containerRect.top + membersContent.scrollTop;
            
            // Scrolle so, dass das Item oben erscheint (mit etwas Abstand)
            membersContent.scrollTo({
              top: relativeTop - 20, // 20px Abstand oben
              behavior: 'smooth'
            });
          } else {
            // Fallback: scrollIntoView mit 'start'
            targetItem.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
          // Highlighte kurz mit abgerundeten Ecken und minimalem Padding
          targetItem.classList.add('member-item-highlighted');
          setTimeout(() => {
            targetItem.classList.remove('member-item-highlighted');
          }, 2000);
        }
      }
    }, 500);
  } catch (error) {
    console.error('Fehler beim Springen zum Bookmark/Zitat:', error);
  }
}

/**
 * Login/Register Handlers
 */
async function handleMembersLogin() {
  const email = document.getElementById('members-email').value;
  const password = document.getElementById('members-password').value;
  const messageDiv = document.getElementById('login-message');
  
  if (!email || !password) {
    messageDiv.innerHTML = '<div class="error-msg">Bitte alle Felder ausfüllen</div>';
    return;
  }
  
  try {
    const { data, error } = await supabaseClient.auth.signInWithPassword({
      email: email,
      password: password
    });
    
    if (error) throw error;
    
    currentUser = data.user;
    messageDiv.innerHTML = '<div class="success-msg">✓ Erfolgreich angemeldet!</div>';
    
    setTimeout(() => {
      showMembersContent();
    }, 1000);
    
  } catch (error) {
    messageDiv.innerHTML = `<div class="error-msg">✗ ${error.message}</div>`;
  }
}

async function handleMembersRegister() {
  const email = document.getElementById('members-reg-email').value;
  const password = document.getElementById('members-reg-password').value;
  const messageDiv = document.getElementById('login-message');
  
  if (!email || !password) {
    messageDiv.innerHTML = '<div class="error-msg">Bitte alle Felder ausfüllen</div>';
    return;
  }
  
  if (password.length < 6) {
    messageDiv.innerHTML = '<div class="error-msg">Passwort muss mindestens 6 Zeichen haben</div>';
    return;
  }
  
  try {
    const { data, error } = await supabaseClient.auth.signUp({
      email: email,
      password: password
    });
    
    if (error) throw error;
    
    messageDiv.innerHTML = '<div class="success-msg">✓ Registrierung erfolgreich!<br>Bitte bestätigen Sie Ihre E-Mail.<br><br>Bitte schauen Sie auch in Ihren Spam-Ordner, falls Sie keine E-Mail erhalten.</div>';
    
  } catch (error) {
    messageDiv.innerHTML = `<div class="error-msg">✗ ${error.message}</div>`;
  }
}

function showMembersLogin() {
  document.getElementById('login-form-content').style.display = 'block';
  document.getElementById('register-form-content').style.display = 'none';
  document.querySelector('.members-header h2').textContent = 'Mitglieder Login';
  document.getElementById('login-message').innerHTML = '';
}

function showMembersRegister() {
  document.getElementById('login-form-content').style.display = 'none';
  document.getElementById('register-form-content').style.display = 'block';
  document.querySelector('.members-header h2').textContent = 'Registrierung';
  document.getElementById('login-message').innerHTML = '';
}

/**
 * Panel schließen
 */
function closeMembersPanel() {
  membersPanelActive = false;
  
  const summaryPanel = document.getElementById('summary-panel');
  const summaryContent = document.getElementById('summary-content');
  const resizeHandle = document.getElementById('verticalResizeHandle');
  
  if (summaryPanel) {
    summaryPanel.classList.remove('visible');
    if (resizeHandle) {
      resizeHandle.classList.remove('visible');
    }
    document.body.classList.add('summary-panel-collapsed');
    summaryPanel.style.width = '0';
    summaryPanel.style.minWidth = '0';
    
    // Zurück zur Standard-TOC-Ansicht
    if (summaryPanel) {
      summaryPanel.classList.remove('has-members-panel');
    }
    if (summaryContent) {
      summaryContent.classList.remove('has-members-panel');
      summaryContent.innerHTML = '<div id="toc-list"></div>';
    }
  }
  
  // Chat-Channel beenden
  if (window.chatChannel) {
    unsubscribeFromChat(window.chatChannel);
    window.chatChannel = null;
  }
  
  // RH positionieren: Verwende zentrale Funktion wenn verfügbar
  if (typeof updateResizeHandle === 'function') {
    setTimeout(() => {
      updateResizeHandle();
    }, 50);
  }
}

/**
 * Wechselt vom Mitgliederbereich zum TOC (Panel bleibt offen)
 */
function switchFromMembersPanelToTOC() {
  membersPanelActive = false;
  
  const summaryPanel = document.getElementById('summary-panel');
  const summaryContent = document.getElementById('summary-content');
  const mainContainer = document.getElementById('main-container');
  
  if (summaryContent) {
    // Setze Inhalt auf TOC zurück, aber lasse Panel offen
    summaryContent.innerHTML = '<div id="toc-list"></div>';
  }
  
  // Chat-Channel beenden falls aktiv
  if (window.chatChannel) {
    unsubscribeFromChat(window.chatChannel);
    window.chatChannel = null;
  }
  
  // Panel bleibt sichtbar - nur Breite auf TOC-Standard anpassen
  if (summaryPanel && summaryPanel.classList.contains('visible')) {
    const tocWidth = 280; // Standard-Breite für TOC (statt 400px vom MB)
    summaryPanel.style.width = tocWidth + 'px';
    summaryPanel.style.minWidth = tocWidth + 'px';
    
    // WICHTIG: Verwende zentrale Synchronisationsfunktion für Main-Container und RH
    // (keine manuelle Setzung - wie in allen anderen Fällen auch)
    if (typeof resetPanelSync === 'function') {
      resetPanelSync(); // Setze Sync zurück, damit neue Breite erkannt wird
    }
    
    // Resize-Handle positionieren: Verwende IMMER zentrale Funktion (wie in allen anderen Fällen)
    setTimeout(() => {
      // Main-Container wird automatisch von syncMainContainerWithPanel() angepasst
      if (typeof syncMainContainerWithPanel === 'function') {
        syncMainContainerWithPanel();
      }
      // RH wird von updateResizeHandle() positioniert
      if (typeof updateResizeHandle === 'function') {
        updateResizeHandle();
      }
    }, 50);
    
    console.log('[MB→TOC] Panel-Breite, Main-Container und Resize-Handle wurden angepasst');
  }
  
  console.log('[MB→TOC] Wechsel vom Mitgliederbereich zum TOC - Layout-Update wird vom Aufrufer abgeschlossen');
}

/**
 * Prüft ob MB aktiv ist
 */
function isMembersPanelActive() {
  return membersPanelActive;
}

/**
 * Lädt alle Keywords aus Bookmarks und Quotes und aktualisiert das Dropdown
 */
async function updateKeywordFilterDropdownWithAllKeywords() {
  if (typeof getBookmarks !== 'function' || typeof getQuotes !== 'function') {
    console.warn('[MB-KEYWORDS] API-Funktionen nicht verfügbar');
    return;
  }
  
  try {
    // Lade beide Datenquellen parallel
    const [bookmarksResult, quotesResult] = await Promise.all([
      getBookmarks(),
      getQuotes()
    ]);
    
    // Sammle alle Keywords aus beiden Quellen
    const allKeywords = new Set();
    
    if (bookmarksResult.success && bookmarksResult.data) {
      bookmarksResult.data.forEach(bookmark => {
        if (bookmark.tags && Array.isArray(bookmark.tags)) {
          bookmark.tags.forEach(tag => allKeywords.add(tag));
        }
      });
    }
    
    if (quotesResult.success && quotesResult.data) {
      quotesResult.data.forEach(quote => {
        if (quote.tags && Array.isArray(quote.tags)) {
          quote.tags.forEach(tag => allKeywords.add(tag));
        }
      });
    }
    
    // Sortiere und aktualisiere Dropdown
    const sortedKeywords = Array.from(allKeywords).sort((a, b) => a.localeCompare(b, 'de'));
    updateKeywordFilterDropdown(sortedKeywords);
  } catch (error) {
    console.error('[MB-KEYWORDS] Fehler beim Laden der Keywords:', error);
  }
}

/**
 * Aktualisiert das Keyword-Filter Dropdown mit neuen Keywords
 */
function updateKeywordFilterDropdown(keywords) {
  const select = document.getElementById('keyword-filter-select');
  if (!select) return;
  
  // Reset
  select.innerHTML = '<option value="">Schlagwörter</option>';
  
  // Füge Keywords hinzu
  if (keywords && keywords.length > 0) {
    keywords.forEach(kw => {
      const option = document.createElement('option');
      option.value = kw;
      option.textContent = kw;
      select.appendChild(option);
    });
    select.disabled = false;
  } else {
    select.disabled = true;
  }
}

/**
 * Prüft, in welchem Tab ein Keyword vorhanden ist
 */
async function findTabForKeyword(keyword) {
  if (!keyword) return null;
  
  if (typeof getBookmarks !== 'function' || typeof getQuotes !== 'function') {
    return null;
  }
  
  try {
    const [bookmarksResult, quotesResult] = await Promise.all([
      getBookmarks(),
      getQuotes()
    ]);
    
    // Prüfe Bookmarks
    let hasInBookmarks = false;
    if (bookmarksResult.success && bookmarksResult.data) {
      hasInBookmarks = bookmarksResult.data.some(bookmark => 
        bookmark.tags && Array.isArray(bookmark.tags) && bookmark.tags.includes(keyword)
      );
    }
    
    // Prüfe Quotes
    let hasInQuotes = false;
    if (quotesResult.success && quotesResult.data) {
      hasInQuotes = quotesResult.data.some(quote => 
        quote.tags && Array.isArray(quote.tags) && quote.tags.includes(keyword)
      );
    }
    
    // Wenn in beiden vorhanden, bleibe im aktuellen Tab
    if (hasInBookmarks && hasInQuotes) {
      return currentMembersTab;
    }
    
    // Wenn nur in einem vorhanden, wechsle zu diesem Tab
    if (hasInBookmarks) return 'bookmarks';
    if (hasInQuotes) return 'quotes';
    
    return null;
  } catch (error) {
    console.error('[MB-KEYWORDS] Fehler beim Prüfen des Keywords:', error);
    return null;
  }
}

/**
 * Handler für Keyword-Filter - wechselt zum richtigen Tab wenn nötig
 */
async function handleKeywordFilter(keyword) {
  if (!keyword) {
    // Kein Keyword ausgewählt - zeige alle Items im aktuellen Tab
    filterItemsByKeyword('');
    return;
  }
  
  // Prüfe, in welchem Tab das Keyword vorhanden ist
  const targetTab = await findTabForKeyword(keyword);
  
  if (targetTab && targetTab !== currentMembersTab) {
    // Wechsle zum Tab, in dem das Keyword vorhanden ist
    // preserveKeyword=true, damit das Dropdown nicht zurückgesetzt wird
    await switchMembersTab(targetTab, true);
    
    // Stelle sicher, dass das Keyword im Dropdown ausgewählt bleibt
    const keywordSelect = document.getElementById('keyword-filter-select');
    if (keywordSelect) {
      keywordSelect.value = keyword;
    }
    
    // Warte kurz, damit der Tab geladen ist, dann filtere
    setTimeout(() => {
      filterItemsByKeyword(keyword);
    }, 150);
  } else {
    // Keyword ist im aktuellen Tab vorhanden (oder in beiden) - filtere einfach
    filterItemsByKeyword(keyword);
  }
}

/**
 * Filtert die aktuell sichtbaren Items nach Keyword
 */
function filterItemsByKeyword(keyword) {
  const items = document.querySelectorAll('#members-tab-content .member-item');
  
  items.forEach(item => {
    if (!keyword) {
      // Zeige alle
      item.style.display = 'block';
    } else {
      // Prüfe ob Keyword vorhanden
      const keywords = item.getAttribute('data-keywords');
      if (keywords && keywords.split(',').includes(keyword)) {
        item.style.display = 'block';
      } else {
        item.style.display = 'none';
      }
    }
  });
}

// Global verfügbar machen
window.openMembersPanel = openMembersPanel;
window.openMembersWindow = openMembersWindow;
window.closeMembersPanel = closeMembersPanel;
window.switchFromMembersPanelToTOC = switchFromMembersPanelToTOC;
window.isMembersPanelActive = isMembersPanelActive;
window.switchMembersTab = switchMembersTab;
window.handleMembersLogin = handleMembersLogin;
window.handleMembersRegister = handleMembersRegister;
window.showMembersLogin = showMembersLogin;
window.showMembersRegister = showMembersRegister;
window.editMemberBookmark = editMemberBookmark;
window.editMemberQuote = editMemberQuote;
window.deleteMemberBookmark = deleteMemberBookmark;
window.deleteMemberQuote = deleteMemberQuote;
window.deleteMemberNote = deleteMemberNote;
window.toggleSortOrder = toggleSortOrder;
window.toggleMultiDeleteMode = toggleMultiDeleteMode;
window.updateMultiDeleteButton = updateMultiDeleteButton;
window.deleteSelectedItems = deleteSelectedItems;
window.saveMemberNote = saveMemberNote;
window.generateMemberGraph = generateMemberGraph;
window.sendMemberChatMessage = sendMemberChatMessage;
window.handleKeywordFilter = handleKeywordFilter;
window.navigateToLectureFromMembersPanel = navigateToLectureFromMembersPanel;
window.saveMembersScrollPosition = saveMembersScrollPosition;
window.restoreMembersScrollPosition = restoreMembersScrollPosition;
window.markParagraphsWithBookmarksAndQuotes = markParagraphsWithBookmarksAndQuotes;
window.jumpToBookmarkOrQuote = jumpToBookmarkOrQuote;

