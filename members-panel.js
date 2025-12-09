// ============================================
// GA-Suche - Mitglieder Panel Integration
// Zeigt Mitgliederbereich im Summary Panel
// ============================================

let membersPanelActive = false;
let currentMembersTab = 'highlights';
let savedScrollPositions = {
  summaryPanel: 0,
  summaryContent: 0,
  membersTabContent: 0
}; // Globale Variable für ALLE Scroll-Positionen
let savedPanelTop = null; // Speichere die top-Position des Panels
let membersScrollObserver = null; // MutationObserver für Scroll-Position
let sortOrder = 'desc'; // 'asc' oder 'desc' - Standard: neueste zuerst
let multiDeleteMode = false; // Multi-Delete-Modus aktiviert?
let selectedGAFilter = ''; // Aktuell ausgewähltes GA-Band für Filterung

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
  
}

/**
 * Startet die automatische Wiederherstellung der Scroll-Position bei DOM-Änderungen
 */
function startScrollPositionProtection() {
  // Stoppe vorherigen Observer falls vorhanden
  stopScrollPositionProtection();
  
  const summaryContent = document.getElementById('summary-content');
  if (!summaryContent) return;
  
  
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
  
}

/**
 * Öffnet members.html in einem neuen Fenster mit window.opener
 */
function openMembersWindow() {
  const membersWindow = window.open('members.html', '_blank');
  if (membersWindow) {
  } else {
    console.error('[MEMBERS-WINDOW] Popup-Blocker verhindert das Öffnen des Fensters');
    alert('Bitte erlauben Sie Popups für diese Seite, um den Mitgliederbereich zu öffnen.');
  }
}

/**
 * Aktualisiert den visuellen Status des Mitglieder-Buttons
 */
function updateMembersButtonStatus() {
  const membersBtn = document.getElementById('membersPanelBtn');
  if (membersBtn) {
    if (membersPanelActive) {
      membersBtn.classList.add('active');
      membersBtn.setAttribute('title', 'Mitgliederbereich schließen');
    } else {
      membersBtn.classList.remove('active');
      membersBtn.setAttribute('title', 'Mitgliederbereich öffnen');
    }
  }
}

/**
 * Toggle-Funktion für Mitglieder-Panel: öffnet oder schließt das Panel
 */
async function toggleMembersPanel() {
  if (membersPanelActive) {
    // Panel ist aktiv → schließen
    closeMembersPanel();
  } else {
    // Panel ist nicht aktiv → öffnen
    await openMembersPanel();
  }
}

/**
 * Öffnet den Mitgliederbereich im Summary Panel
 */
async function openMembersPanel() {
  await initSupabase();
  
  // Stelle sicher, dass Event-Delegation für Highlights aktiviert ist
  if (typeof attachHighlightDelegationListener === 'function') {
    attachHighlightDelegationListener();
  }
  
  if (!currentUser) {
    // Zeige Login-Form im Panel
    showMembersLoginPanel();
    return;
  }
  
  // Zeige Mitglieder-Content
  showMembersContent();
  
  // Initialisiere Chat-Realtime-Listener für Badge-Updates (auch wenn Chat-Tab nicht aktiv ist)
  initializeChatRealtimeListener();
  
  // Aktualisiere Button-Status nach dem Öffnen
  setTimeout(() => {
    updateMembersButtonStatus();
  }, 100);
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
        <p class="login-description">Nach Anmeldung können Sie Zitate abspeichern, mit Schlagworten versehen, ordnen und kommentieren sowie sich mit anderen Mitgliedern per Chat austauschen.</p>
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
          
          <p class="auth-switch" style="margin-top: 0.5rem;">
            <a href="#" onclick="showPasswordReset(); return false;" style="font-size: 0.85rem;">Passwort vergessen?</a>
          </p>
          
          <p class="auth-switch">
            <a href="#" onclick="showMembersRegister(); return false;">Noch kein Account? Registrieren</a>
          </p>
        </div>
        
        <div id="password-reset-form-content" style="display:none;">
          <div class="form-group">
            <label for="members-reset-email">E-Mail</label>
            <input type="email" id="members-reset-email" placeholder="Ihre E-Mail-Adresse" />
          </div>
          
          <button onclick="handlePasswordReset()" class="primary-btn">Passwort-Reset-Link senden</button>
          
          <p class="auth-switch">
            <a href="#" onclick="showMembersLogin(); return false;">Zurück zum Login</a>
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
          
          <div class="form-group" style="margin-top: 1rem;">
            <label style="font-weight: normal; font-size: 0.85rem; line-height: 1.5; display: block;">
              <input type="checkbox" id="members-privacy-checkbox" style="margin-bottom: 0.5rem; display: block;" />
              <span style="display: block;">Mit der Registrierung stimme ich der <a href="#" id="members-privacy-link" onclick="showMembersPrivacyModal(); return false;" style="color: var(--link-color); text-decoration: underline;">Datenschutzerklärung</a> zu.</span>
            </label>
          </div>
          
          <button onclick="handleMembersRegister()" class="primary-btn">Registrieren</button>
          
          <p class="auth-switch">
            <a href="#" onclick="showMembersLogin(); return false;">Bereits registriert? Anmelden</a>
          </p>
        </div>
      </div>
    </div>
    
    <style>
      /* Privacy Modal Styles */
      .members-privacy-modal {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 10001 !important;
        align-items: center;
        justify-content: center;
        opacity: 1 !important;
      }

      .members-privacy-modal.active {
        display: flex !important;
      }

      .members-privacy-modal-content {
        background: #ffffff !important;
        background-color: #ffffff !important;
        padding: 2rem;
        border-radius: 8px;
        max-width: 700px;
        width: 90%;
        max-height: 85vh;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        display: flex;
        flex-direction: column;
        color: #333333;
        opacity: 1 !important;
        z-index: 10002 !important;
        position: relative;
      }

      .members-privacy-modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e0e0e0;
        flex-shrink: 0;
      }

      .members-privacy-modal-header h3 {
        color: #333333;
        font-size: 1.3rem;
        font-weight: normal;
        margin: 0;
      }

      .members-privacy-modal-close {
        background: none;
        border: none;
        font-size: 1.5rem;
        color: #666666;
        cursor: pointer;
        padding: 0;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: color 0.2s;
      }

      .members-privacy-modal-close:hover {
        color: #333333;
      }

      .members-privacy-modal-body {
        flex: 1;
        overflow-y: auto;
        padding-right: 0.5rem;
      }

      .members-privacy-modal-body h4 {
        color: #333333;
        font-size: 1.1rem;
        font-weight: normal;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
      }

      .members-privacy-modal-body h4:first-child {
        margin-top: 0;
      }

      .members-privacy-modal-body p {
        margin-bottom: 1rem;
        line-height: 1.6;
      }

      .members-privacy-modal-body ul {
        margin-bottom: 1rem;
        padding-left: 1.5rem;
      }

      .members-privacy-modal-body li {
        margin-bottom: 0.5rem;
        line-height: 1.6;
      }
    </style>
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
 * Öffnet das Member Panel unabhängig vom vorherigen Zustand
 */
async function showMembersContent() {
  const summaryPanel = document.getElementById('summary-panel');
  const summaryContent = document.getElementById('summary-content');
  const resizeHandle = document.getElementById('verticalResizeHandle');
  const mainContainer = document.getElementById('main-container');
  
  if (!summaryPanel || !summaryContent) return;
  
  // WICHTIG: Wenn Navigation läuft, NICHT den Observer stoppen oder Panel neu öffnen
  // Das würde das Springen verursachen
  if (window.membersNavigating) {
    console.log('[MB-CONTENT] Navigation läuft - überspringe showMembersContent');
    return;
  }
  
  // WICHTIG: Setze Flags ZUERST zurück, damit alles sauber ist
  // ABER: Setze membersPanelActive NICHT auf false, wenn es bereits true ist (verhindert Flackern)
  // Nur zurücksetzen, wenn es wirklich nicht aktiv ist
  const wasAlreadyActive = membersPanelActive;
  if (!wasAlreadyActive) {
    membersPanelActive = false; // Nur zurücksetzen, wenn nicht bereits aktiv
  }
  // membersNavigating nur zurücksetzen, wenn nicht bereits aktiv (während Navigation)
  if (!window.membersNavigating) {
    window.membersNavigating = false;
    document.body.classList.remove('members-navigating');
  }
  stopScrollPositionProtection();
  
  // Stelle innerHTML Setter wieder her, falls überschrieben
  if (summaryContent) {
    try {
      const currentDescriptor = Object.getOwnPropertyDescriptor(summaryContent, 'innerHTML');
      if (currentDescriptor && currentDescriptor.configurable) {
        delete summaryContent.innerHTML;
      }
    } catch (e) {
      // Ignoriere Fehler
    }
  }
  
  // WICHTIG: Stoppe Panel-Visibility Observer NUR wenn KEINE Navigation läuft
  // Während Navigation muss der Observer aktiv bleiben, um das Panel zu schützen
  if (window.panelVisibilityObserver && !window.membersNavigating) {
    window.panelVisibilityObserver.disconnect();
    window.panelVisibilityObserver = null;
  }
  
  // WICHTIG: Stoppe Width-Check Interval NUR wenn KEINE Navigation läuft
  if (window.panelWidthCheckInterval && !window.membersNavigating) {
    clearInterval(window.panelWidthCheckInterval);
    window.panelWidthCheckInterval = null;
  }
  
  // JETZT: Setze Member Panel aktiv
  // WICHTIG: Setze immer auf true, auch wenn es bereits true war (verhindert Flackern)
  membersPanelActive = true;
  
  // Aktualisiere Button-Status
  updateMembersButtonStatus();
  
  // Panel öffnen - stelle sicher, dass es sichtbar bleibt
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
  
  // Main-Container SOFORT anpassen (auch wenn Panel bereits geöffnet war)
  if (mainContainer) {
    mainContainer.style.marginRight = mbWidth + 'px';
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
  
  // WICHTIG: Stelle innerHTML Setter wieder her, falls er überschrieben wurde
  // (damit innerHTML wieder normal funktioniert)
  if (summaryContent) {
    try {
      const proto = Object.getPrototypeOf(summaryContent);
      const currentDescriptor = Object.getOwnPropertyDescriptor(summaryContent, 'innerHTML');
      
      // Wenn innerHTML direkt auf summaryContent definiert ist (überschrieben), entferne es
      if (currentDescriptor && currentDescriptor.configurable) {
        delete summaryContent.innerHTML;
      }
    } catch (e) {
      // Ignoriere Fehler beim Zurücksetzen
      console.warn('[MB-CONTENT] Fehler beim Zurücksetzen des innerHTML Setters:', e);
    }
  }
  
  // Content HTML - verwende innerHTML (sollte jetzt funktionieren, da Setter zurückgesetzt wurde)
  // Fallback: Falls innerHTML blockiert wird, verwende direkte DOM-Manipulation
  try {
    summaryContent.innerHTML = `
    <div class="members-panel">
      <div class="members-header-container">
        <div class="members-header">
          <div style="flex: 1;">
            <h2 style="font-size: 1.4rem;"><a href="#" onclick="openMembersWindow(); return false;" style="color: inherit; text-decoration: none; cursor: pointer;">Mitgliederbereich</a></h2>
            <div style="font-size: 0.75rem; color: var(--text-color); opacity: 0.7; margin-top: 0.25rem;">Textstellen per Rechtsklick speichern</div>
          </div>
          <button class="close-btn" onclick="closeMembersPanel()">×</button>
        </div>
        
        <div class="members-tabs">
        <div style="display: flex; flex-wrap: wrap; gap: 0.25rem; width: 100%;">
          <div style="display: flex; gap: 0.25rem; flex: 1;">
            <button class="members-tab members-tab-quotes ${currentMembersTab === 'quotes' ? 'active' : ''}" onclick="switchMembersTab('quotes')">Anstreichungen</button>
            <button class="members-tab members-tab-highlights ${currentMembersTab === 'highlights' ? 'active' : ''}" onclick="switchMembersTab('highlights')">Unterstreichungen</button>
            <div class="keyword-filter-tab" style="flex: 0 0 auto; min-width: 40px;">
              <select id="ga-filter-select" onchange="handleGAFilter(this.value)" class="keyword-select-btn" style="min-width: 40px; padding-right: 0.3rem; background-image: none;">
                <option value="">GA</option>
              </select>
            </div>
          </div>
          <div style="display: flex; gap: 0.25rem; align-items: center; margin-top: 0.25rem; width: 100%;">
            <button class="members-tab members-tab-notes ${currentMembersTab === 'notes' ? 'active' : ''}" onclick="switchMembersTab('notes')" style="flex: 1.8; min-width: 0;">Notizen</button>
            <div class="keyword-filter-tab" style="flex: 1; min-width: 0;">
              <select id="keyword-filter-select" onchange="handleKeywordFilter(this.value)" class="keyword-select-btn">
                <option value="">Schlagwörter</option>
              </select>
            </div>
            <button class="members-tab ${currentMembersTab === 'chat' ? 'active' : ''}" onclick="switchMembersTab('chat')" id="members-chat-tab-btn" style="display: none;">
              Chat
              <span class="chat-badge" id="members-chat-badge" style="display: none;">0</span>
            </button>
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
        </div>
      </div>
      
      <div class="members-content" id="members-tab-content">
        <!-- Content wird dynamisch geladen -->
      </div>
    </div>
  `;
  
  // Initialisiere Chat-Badge nach dem Rendern
  setTimeout(() => {
    updateChatBadge();
  }, 100);
  
  } catch (e) {
    // Fallback: Falls innerHTML blockiert wird, verwende direkte DOM-Manipulation
    console.warn('[MB-CONTENT] innerHTML blockiert, verwende direkte DOM-Manipulation:', e);
    summaryContent.textContent = ''; // Leere zuerst
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = `
      <div class="members-panel">
        <div class="members-header-container">
          <div class="members-header">
            <div style="flex: 1;">
              <h2 style="font-size: 1.4rem;"><a href="#" onclick="openMembersWindow(); return false;" style="color: inherit; text-decoration: none; cursor: pointer;">Mitgliederbereich</a></h2>
              <div style="font-size: 0.75rem; color: var(--text-color); opacity: 0.7; margin-top: 0.25rem;">Textstellen per Rechtsklick speichern</div>
            </div>
            <button class="close-btn" onclick="closeMembersPanel()">×</button>
          </div>
          
          <div class="members-tabs">
          <div style="display: flex; flex-wrap: wrap; gap: 0.25rem; width: 100%;">
            <div style="display: flex; gap: 0.25rem; flex: 1;">
              <button class="members-tab members-tab-quotes ${currentMembersTab === 'quotes' ? 'active' : ''}" onclick="switchMembersTab('quotes')">Anstreichungen</button>
              <button class="members-tab members-tab-highlights ${currentMembersTab === 'highlights' ? 'active' : ''}" onclick="switchMembersTab('highlights')">Unterstreichungen</button>
              <div class="keyword-filter-tab" style="flex: 0 0 auto; min-width: 40px;">
                <select id="ga-filter-select" onchange="handleGAFilter(this.value)" class="keyword-select-btn" style="min-width: 40px; padding-right: 0.3rem; background-image: none;">
                  <option value="">GA</option>
                </select>
              </div>
            </div>
            <div style="display: flex; gap: 0.25rem; align-items: center; margin-top: 0.25rem; width: 100%;">
              <button class="members-tab members-tab-notes ${currentMembersTab === 'notes' ? 'active' : ''}" onclick="switchMembersTab('notes')" style="flex: 1.8; min-width: 0;">Notizen</button>
              <div class="keyword-filter-tab" style="flex: 1; min-width: 0;">
                <select id="keyword-filter-select" onchange="handleKeywordFilter(this.value)" class="keyword-select-btn">
                  <option value="">Schlagwörter</option>
                </select>
              </div>
              <button class="members-tab ${currentMembersTab === 'chat' ? 'active' : ''}" onclick="switchMembersTab('chat')" id="members-chat-tab-btn-2" style="display: none;">
                Chat
                <span class="chat-badge" id="members-chat-badge-2" style="display: none;">0</span>
              </button>
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
          </div>
        </div>
        
        <div class="members-content" id="members-tab-content">
          <!-- Content wird dynamisch geladen -->
        </div>
      </div>
    `;
    // Verschiebe alle Kinder von tempDiv zu summaryContent
    while (tempDiv.firstChild) {
      summaryContent.appendChild(tempDiv.firstChild);
    }
  }
  
  // Lade Quotes und Highlights im Hintergrund für schnellen Tab-Wechsel (nur wenn Cache nicht vorhanden)
  const now = Date.now();
  const cacheValid = cachedQuotesData && cachedHighlightsData && 
                     bookmarksQuotesCacheTimestamp && 
                     (now - bookmarksQuotesCacheTimestamp) < BOOKMARKS_QUOTES_CACHE_TTL;
  
  if (!cacheValid && typeof getQuotes === 'function' && typeof getHighlights === 'function') {
    // Lade im Hintergrund, blockiert nicht das Rendering
    Promise.all([getQuotes(), getHighlights()]).then(async ([quotesResult, highlightsResult]) => {
      cachedQuotesData = quotesResult;
      cachedHighlightsData = highlightsResult;
      bookmarksQuotesCacheTimestamp = Date.now();
      
      // Sammle alle GA-Nummern für Filter-Dropdown
      const allGANumbers = [
        ...new Set([
          ...(quotesResult.success ? quotesResult.data.map(q => q.ga_reference).filter(Boolean) : []),
          ...(highlightsResult.success ? highlightsResult.data.map(h => h.ga_number).filter(Boolean) : [])
        ])
      ];
      
      if (allGANumbers.length > 0) {
        // Aktualisiere GA-Filter-Dropdown mit allen verfügbaren GA-Nummern
        updateGAFilterDropdown(allGANumbers);
      }
    }).catch(err => {
      console.warn('[MB-CACHE] Fehler beim Cachen der Daten:', err);
    });
  }
  
  // Aktuellen Tab laden - kurze Verzögerung damit API-Module geladen sind
  setTimeout(async () => {
    await loadMembersTab(currentMembersTab);
    // Lade Keywords nach dem Laden des Tabs
    updateKeywordFilterDropdownWithAllKeywords().catch(err => console.warn('[MB-KEYWORDS] Fehler:', err));
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
  
  // GA-Filter zurücksetzen beim Wechsel zwischen Unterstreichungen, Zitate und Notizen
  if (tabName === 'highlights' || tabName === 'quotes' || tabName === 'notes') {
    const gaFilterSelect = document.getElementById('ga-filter-select');
    if (gaFilterSelect) {
      gaFilterSelect.value = '';
    }
    selectedGAFilter = ''; // Setze auch die Variable zurück
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
  
  
  try {
    switch(tabName) {
      case 'quotes':
        await loadQuotesTab(content);
        break;
      case 'highlights':
        await loadHighlightsTab(content);
        break;
      case 'notes':
        loadNotesTab(content);
        break;
      case 'chat':
        await loadChatTab(content);
        // markChatAsRead() und updateChatBadge() werden bereits in loadChatTab() aufgerufen
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
 * Holt das Datum eines Vortrags direkt aus den Quote/Highlight-Daten
 * Die Datumsangaben kommen jetzt direkt aus Supabase
 */
function getLectureDate(item) {
  if (!item) return '';
  
  // Prüfe ob das Item ein lecture_date Feld hat (kommt direkt aus Supabase)
  if (item.lecture_date) {
    return formatLectureDate(item.lecture_date);
  }
  
  return '';
}

/**
 * Holt das Vortragsdatum als Date-Objekt für Sortierung direkt aus den Quote/Highlight-Daten
 * Gibt null zurück, wenn kein Datum gefunden wird
 * Unterstützt sowohl Vorträge (lecture_date) als auch Bücher (yearRange)
 */
function getLectureDateForSorting(item) {
  if (!item) return null;
  
  // Prüfe ob das Item ein lecture_date Feld hat (kommt direkt aus Supabase)
  if (item.lecture_date) {
    try {
      const dateStr = item.lecture_date;
      // Unterstütze verschiedene Formate: "1908-10-21", "21. Oktober 1908", etc.
      const dateMatch = dateStr.match(/(\d{4})-(\d{2})-(\d{2})/); // ISO-Format
      if (dateMatch) {
        return new Date(parseInt(dateMatch[1]), parseInt(dateMatch[2]) - 1, parseInt(dateMatch[3]));
      }
      
      // Versuche Jahr zu extrahieren (für Fallback-Sortierung)
      const yearMatch = dateStr.match(/\b(19\d{2}|20\d{2})\b/);
      if (yearMatch) {
        return new Date(parseInt(yearMatch[1]), 0, 1); // 1. Januar des Jahres
      }
      
      // Versuche direkt zu parsen
      const parsedDate = new Date(dateStr);
      if (!isNaN(parsedDate.getTime())) {
        return parsedDate;
      }
    } catch (error) {
      console.warn('[MB-DATE] Fehler beim Parsen des Datums:', error);
    }
  }
  
  // Für Bücher: Prüfe ob es ein Buch ist und versuche aus window.fullBooksData zu holen
  const gaReference = item.ga_reference || item.ga_number;
  if (gaReference) {
    const isBook = isBookGANumber(gaReference);
    if (isBook && typeof window !== 'undefined' && window.fullBooksData) {
      const normalizedId = gaReference.toLowerCase();
      const book = window.fullBooksData[normalizedId] || 
                   window.fullBooksData[gaReference] ||
                   window.fullBooksData[gaReference.toUpperCase()];
      
      if (book && book.yearRange) {
        // Bücher haben yearRange im Format "1912-1913" oder "1912"
        const yearMatch = book.yearRange.match(/^(\d{4})/);
        if (yearMatch) {
          return new Date(parseInt(yearMatch[1]), 0, 1); // 1. Januar des ersten Jahres
        }
      }
    }
  }
  
  return null;
}

/**
 * Formatiert ein Datum im deutschen Format (z.B. "21. Oktober 1908")
 */
function formatLectureDate(dateStr) {
  if (!dateStr) return '';
  
  try {
    // Unterstütze ISO-Format (YYYY-MM-DD)
    if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
      const [year, month, day] = dateStr.split('-');
      const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
      return date.toLocaleDateString('de-DE', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    }
    
    // Versuche direkt zu parsen
    const date = new Date(dateStr);
    if (!isNaN(date.getTime())) {
      return date.toLocaleDateString('de-DE', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    }
    
    // Falls Parsing fehlschlägt, gib Original zurück
    return dateStr;
  } catch (error) {
    console.warn('[FORMAT-DATE] Fehler beim Formatieren:', dateStr, error);
    return dateStr;
  }
}

/**
 * Prüft, ob eine GA-Nummer ein Buch ist (GA001-GA046)
 */
function isBookGANumber(gaNumber) {
  if (!gaNumber) return false;
  
  // Normalisiere GA-Nummer (entferne "GA" und konvertiere zu Zahl)
  const normalized = gaNumber.replace(/^GA/i, '').trim();
  const gaNum = parseInt(normalized);
  
  // Bücher sind GA001-GA046
  return !isNaN(gaNum) && gaNum >= 1 && gaNum <= 46;
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

/**
 * Gibt die Hex-Farbe für eine Notiz-Farbe zurück (gleiche Farben wie Zitate/Unterstreichungen)
 */
function getNoteColor(colorName) {
  const colors = {
    'blue': '#467886',
    'red': '#c62828',
    'yellow': '#ffc107'
  };
  return colors[colorName] || colors['blue'];
}

/**
 * Highlights Tab (Unterstreichungen)
 */
async function loadHighlightsTab(container) {
  if (typeof getHighlights !== 'function') {
    console.error('[MB-HIGHLIGHTS] getHighlights ist nicht verfügbar!');
    container.innerHTML = '<div class="empty-state">API-Funktionen nicht geladen. Bitte Seite neu laden.</div>';
    return;
  }
  
  // Zeige Ladeanzeige während Daten geladen werden
  container.innerHTML = '<div class="empty-state"><em>Laden...</em></div>';
  
  // Verwende Cache wenn verfügbar, sonst lade neu
  let result;
  const now = Date.now();
  const cacheValid = cachedHighlightsData && 
                     bookmarksQuotesCacheTimestamp && 
                     (now - bookmarksQuotesCacheTimestamp) < BOOKMARKS_QUOTES_CACHE_TTL;
  
  if (cacheValid) {
    result = cachedHighlightsData;
  } else {
    result = await getHighlights();
    // Aktualisiere Cache
    cachedHighlightsData = result;
    bookmarksQuotesCacheTimestamp = now;
  }
  
  if (!result.success || result.data.length === 0) {
    container.innerHTML = '<div class="empty-state">Noch keine Unterstreichungen</div>';
    // Lade Keywords trotzdem im Hintergrund
    updateKeywordFilterDropdownWithAllKeywords().catch(err => console.warn('[MB-KEYWORDS] Fehler:', err));
    return;
  }
  
  // Sammle alle eindeutigen GA-Nummern für Filter-Dropdown
  const uniqueGANumbers = [...new Set(result.data.map(h => h.ga_number).filter(Boolean))];
  
  // Sortiere nach Vortragsdatum (kommt direkt aus Supabase) oder Erstellungsdatum als Fallback
  const sortedData = [...result.data].sort((a, b) => {
    const dateA = getLectureDateForSorting(a);
    const dateB = getLectureDateForSorting(b);
    
    if (dateA && dateB) {
      return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
    }
    
    if (dateA && !dateB) {
      return sortOrder === 'asc' ? -1 : 1;
    }
    if (!dateA && dateB) {
      return sortOrder === 'asc' ? 1 : -1;
    }
    
    const createdA = new Date(a.created_at);
    const createdB = new Date(b.created_at);
    return sortOrder === 'asc' ? createdA - createdB : createdB - createdA;
  });
  
  // Rendere mit vollständig geladenen Daten (inkl. Vortragsdaten)
  renderHighlightsList(container, sortedData);
  
  // Aktualisiere GA-Filter-Dropdown
  updateGAFilterDropdown(uniqueGANumbers);
  
  // Lade Keywords parallel (nicht-blockierend für Rendering)
  updateKeywordFilterDropdownWithAllKeywords().catch(err => console.warn('[MB-KEYWORDS] Fehler:', err));
  
}

/**
 * Rendert die Highlights-Liste
 */
function renderHighlightsList(container, sortedData) {
  // Filtere nach GA-Nummer wenn Filter aktiv ist
  let filteredData = sortedData;
  if (selectedGAFilter) {
    filteredData = sortedData.filter(highlight => {
      const gaNumber = highlight.ga_number || '';
      return gaNumber.toLowerCase().startsWith(selectedGAFilter.toLowerCase());
    });
  }
  
  const multiDeleteHtml = multiDeleteMode ? `
    <div style="margin-bottom: 1rem; padding: 0.75rem; background: var(--background-color); border: 1px solid var(--border-color); border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
      <span style="font-size: 0.85rem; color: var(--text-color);">Auswahl-Modus aktiv</span>
      <button id="multi-delete-btn" onclick="deleteSelectedItems()" disabled style="padding: 0.4rem 0.8rem; font-size: 0.8rem; background: #c62828; color: white; border: none; border-radius: 4px; cursor: pointer;">Ausgewählte löschen</button>
    </div>
  ` : '';
  
  if (filteredData.length === 0 && sortedData.length > 0) {
    container.innerHTML = '<div class="empty-state">Keine Einträge für das ausgewählte GA-Band gefunden</div>';
    return;
  }
  
  const html = multiDeleteHtml + filteredData.map((highlight) => {
    const lectureDate = getLectureDate(highlight);
    const dateDisplay = lectureDate ? `<span data-lecture-date="true" style="font-size: 0.85rem; font-weight: normal; color: var(--text-color);">${lectureDate}</span>` : '';
    
    const isBook = isBookGANumber(highlight.ga_number);
    // Link immer anzeigen, auch ohne paragraph_id (springt dann zum Vortrag ohne spezifische Stelle)
    const shouldShowLink = true; // Immer Link anzeigen, auch wenn kein paragraph_id vorhanden ist
    
    const highlightedText = highlight.paragraph_text && highlight.text_start_offset !== null && highlight.text_end_offset !== null
      ? highlight.paragraph_text.substring(highlight.text_start_offset, highlight.text_end_offset)
      : highlight.paragraph_text || '';
    
    const highlightColor = getHighlightColor(highlight.color || 'blue');
    
    return `
      <div class="member-item" data-keywords="${highlight.tags ? highlight.tags.join(',') : ''}" data-id="${highlight.id}" data-type="highlight" data-ga-reference="${highlight.ga_number}">
        ${multiDeleteMode ? `<input type="checkbox" class="member-item-checkbox" data-id="${highlight.id}" onchange="updateMultiDeleteButton()">` : ''}
        <div style="flex: 1;">
          <div class="member-item-header">
            ${shouldShowLink
              ? `<strong><a href="#" onclick="saveMembersScrollPosition(); navigateToLectureFromMembersPanel('${highlight.ga_number}', ${highlight.paragraph_id ? `'${highlight.paragraph_id}'` : 'null'}, ${highlight.text_start_offset !== null && highlight.text_start_offset !== undefined ? highlight.text_start_offset : 'null'}, ${highlight.text_end_offset !== null && highlight.text_end_offset !== undefined ? highlight.text_end_offset : 'null'}); return false;" style="color: var(--link-color); text-decoration: none;">${highlight.ga_number}</a>${dateDisplay ? ', ' + dateDisplay : ''}</strong>`
              : `<strong>${highlight.ga_number}${dateDisplay ? ', ' + dateDisplay : ''}</strong>`
            }
            <span class="member-item-date">${new Date(highlight.created_at).toLocaleDateString('de-DE')}</span>
          </div>
          ${highlight.lecture_title ? `<div class="member-item-subtitle">${highlight.lecture_title}</div>` : ''}
          ${shouldShowLink
            ? `<div class="member-item-text"><a href="#" onclick="saveMembersScrollPosition(); navigateToLectureFromMembersPanel('${highlight.ga_number}', ${highlight.paragraph_id ? `'${highlight.paragraph_id}'` : 'null'}, ${highlight.text_start_offset !== null && highlight.text_start_offset !== undefined ? highlight.text_start_offset : 'null'}, ${highlight.text_end_offset !== null && highlight.text_end_offset !== undefined ? highlight.text_end_offset : 'null'}); return false;" style="text-decoration: underline; text-decoration-color: ${highlightColor}; text-decoration-thickness: 1.5px; font-style: normal; color: var(--text-color); cursor: pointer;">${highlightedText.substring(0, 150)}${highlightedText.length > 150 ? '...' : ''}</a></div>`
            : `<div class="member-item-text" style="text-decoration: underline; text-decoration-color: ${highlightColor}; text-decoration-thickness: 1.5px; font-style: normal;">${highlightedText.substring(0, 150)}${highlightedText.length > 150 ? '...' : ''}</div>`
          }
          ${highlight.personal_note ? `<div class="member-item-note">${highlight.personal_note}</div>` : ''}
          ${highlight.tags && highlight.tags.length > 0 ? `<div class="member-item-tags">${highlight.tags.map(tag => `<span class="tag clickable-tag" onclick="handleKeywordFilter('${tag.replace(/'/g, "\\'")}'); return false;" style="cursor: pointer;" title="Nach diesem Schlagwort filtern">#${tag}</span>`).join(' ')}</div>` : ''}
          <div class="member-item-actions">
            <button class="edit-btn" onclick="editMemberHighlight('${highlight.id}')" title="Bearbeiten">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
            <button class="delete-btn" onclick="deleteMemberHighlight('${highlight.id}')" title="Löschen">
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
    `;
  }).join('');
  
  container.innerHTML = html;
  
  // Füge Event-Listener für Rechtsklick-Kontextmenü hinzu
  attachHighlightContextMenuListeners(container);
}

/**
 * Fügt Event-Listener für Rechtsklick-Kontextmenü auf Highlight-Items hinzu
 */
function attachHighlightContextMenuListeners(container) {
  const highlightItems = container.querySelectorAll('.member-item[data-type="highlight"]');
  
  highlightItems.forEach(item => {
    item.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const highlightId = item.getAttribute('data-id');
      if (!highlightId) return;
      
      showHighlightColorContextMenu(e.clientX, e.clientY, highlightId);
    });
  });
}

/**
 * Zeigt das Kontextmenü zum Ändern der Highlight-Farbe
 */
function showHighlightColorContextMenu(x, y, highlightId) {
  // Entferne vorheriges Menü falls vorhanden
  const existingMenu = document.getElementById('members-highlight-context-menu');
  if (existingMenu) {
    existingMenu.remove();
  }
  
  // Erstelle neues Menü
  const menu = document.createElement('div');
  menu.id = 'members-highlight-context-menu';
  menu.className = 'members-highlight-context-menu';
  menu.innerHTML = `
    <div class="highlight-context-menu-item" onclick="changeHighlightColor('${highlightId}', 'blue')" style="border-left: 3px solid #467886;">
      <span class="highlight-context-menu-text">Blau</span>
    </div>
    <div class="highlight-context-menu-item" onclick="changeHighlightColor('${highlightId}', 'red')" style="border-left: 3px solid #c62828;">
      <span class="highlight-context-menu-text">Rot</span>
    </div>
    <div class="highlight-context-menu-item" onclick="changeHighlightColor('${highlightId}', 'yellow')" style="border-left: 3px solid #ffc107;">
      <span class="highlight-context-menu-text">Gelb</span>
    </div>
  `;
  
  document.body.appendChild(menu);
  
  // Positioniere Menü
  menu.style.display = 'block';
  menu.style.left = x + 'px';
  menu.style.top = y + 'px';
  
  // Viewport-Grenzen prüfen
  const menuRect = menu.getBoundingClientRect();
  
  // Rechts aus dem Viewport?
  if (menuRect.right > window.innerWidth) {
    menu.style.left = (window.innerWidth - menuRect.width - 10) + 'px';
  }
  
  // Unten aus dem Viewport?
  if (menuRect.bottom > window.innerHeight) {
    menu.style.top = (window.innerHeight - menuRect.height - 10) + 'px';
  }
  
  // Klick außerhalb schließt Menü
  const closeMenu = (e) => {
    if (!menu.contains(e.target)) {
      menu.remove();
      document.removeEventListener('click', closeMenu);
      document.removeEventListener('contextmenu', closeMenu);
    }
  };
  
  // Warte kurz bevor Event-Listener hinzugefügt wird, damit onclick funktioniert
  setTimeout(() => {
    document.addEventListener('click', closeMenu);
    document.addEventListener('contextmenu', closeMenu);
  }, 100);
}

/**
 * Ändert die Farbe einer Unterstreichung
 */
async function changeHighlightColor(highlightId, color) {
  // Entferne Kontextmenü
  const menu = document.getElementById('members-highlight-context-menu');
  if (menu) {
    menu.remove();
  }
  
  try {
    if (typeof updateHighlight !== 'function') {
      alert('Fehler: updateHighlight Funktion nicht verfügbar. Bitte Seite neu laden.');
      console.error('[MB-HIGHLIGHTS] updateHighlight nicht verfügbar');
      return;
    }
    
    const updateResult = await updateHighlight(highlightId, {
      color: color
    });
    
    if (updateResult.success) {
      // Invalidiere Cache, damit Daten neu geladen werden
      invalidateMembersCache('highlights');
      
      // Aktualisiere Highlight im Viewer (falls vorhanden)
      const highlightElement = document.querySelector(`[data-highlight-id="${highlightId}"]`);
      if (highlightElement) {
        // Aktualisiere Farbe im DOM
        const highlightColor = getHighlightColor(color);
        highlightElement.style.setProperty('text-decoration-color', highlightColor, 'important');
        highlightElement.style.setProperty('-webkit-text-decoration-color', highlightColor, 'important');
        highlightElement.setAttribute('data-highlight-color', color);
      }
      
      // Aktualisiere Member Panel falls offen
      if (typeof membersPanelActive !== 'undefined' && membersPanelActive && currentMembersTab === 'highlights') {
        await loadMembersTab('highlights');
      }
      
      // Zeige Erfolgsmeldung (optional - kann später durch Toast-Notification ersetzt werden)
      console.log('✓ Farbe geändert');
    } else {
      alert('Fehler beim Ändern der Farbe: ' + updateResult.error);
    }
  } catch (error) {
    console.error('Fehler beim Ändern der Farbe:', error);
    alert('Fehler beim Ändern der Farbe');
  }
}


/**
 * Fügt Event-Listener für Rechtsklick-Kontextmenü auf Quote-Items hinzu
 */
function attachQuoteContextMenuListeners(container) {
  const quoteItems = container.querySelectorAll('.member-item[data-type="quote"]');
  
  quoteItems.forEach(item => {
    item.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const quoteId = item.getAttribute('data-id');
      if (!quoteId) return;
      
      showQuoteColorContextMenu(e.clientX, e.clientY, quoteId);
    });
  });
}

/**
 * Zeigt das Kontextmenü zum Ändern der Quote-Farbe
 */
function showQuoteColorContextMenu(x, y, quoteId) {
  // Entferne vorheriges Menü falls vorhanden
  const existingMenu = document.getElementById('members-quote-context-menu');
  if (existingMenu) {
    existingMenu.remove();
  }
  
  // Erstelle neues Menü
  const menu = document.createElement('div');
  menu.id = 'members-quote-context-menu';
  menu.className = 'members-highlight-context-menu';
  menu.innerHTML = `
    <div class="highlight-context-menu-item" onclick="changeQuoteColor('${quoteId}', 'blue')" style="border-left: 3px solid #467886;">
      <span class="highlight-context-menu-text">Blau</span>
    </div>
    <div class="highlight-context-menu-item" onclick="changeQuoteColor('${quoteId}', 'red')" style="border-left: 3px solid #c62828;">
      <span class="highlight-context-menu-text">Rot</span>
    </div>
    <div class="highlight-context-menu-item" onclick="changeQuoteColor('${quoteId}', 'yellow')" style="border-left: 3px solid #ffc107;">
      <span class="highlight-context-menu-text">Gelb</span>
    </div>
  `;
  
  document.body.appendChild(menu);
  
  // Positioniere Menü
  menu.style.display = 'block';
  menu.style.left = x + 'px';
  menu.style.top = y + 'px';
  
  // Viewport-Grenzen prüfen
  const menuRect = menu.getBoundingClientRect();
  
  // Rechts aus dem Viewport?
  if (menuRect.right > window.innerWidth) {
    menu.style.left = (window.innerWidth - menuRect.width - 10) + 'px';
  }
  
  // Unten aus dem Viewport?
  if (menuRect.bottom > window.innerHeight) {
    menu.style.top = (window.innerHeight - menuRect.height - 10) + 'px';
  }
  
  // Klick außerhalb schließt Menü
  const closeMenu = (e) => {
    if (!menu.contains(e.target)) {
      menu.remove();
      document.removeEventListener('click', closeMenu);
      document.removeEventListener('contextmenu', closeMenu);
    }
  };
  
  // Warte kurz bevor Event-Listener hinzugefügt wird, damit onclick funktioniert
  setTimeout(() => {
    document.addEventListener('click', closeMenu);
    document.addEventListener('contextmenu', closeMenu);
  }, 100);
}

/**
 * Ändert die Farbe eines Zitats
 */
async function changeQuoteColor(quoteId, color) {
  // Entferne Kontextmenü
  const menu = document.getElementById('members-quote-context-menu');
  if (menu) {
    menu.remove();
  }
  
  try {
    if (typeof updateQuote !== 'function') {
      alert('Fehler: updateQuote Funktion nicht verfügbar. Bitte Seite neu laden.');
      console.error('[MB-QUOTES] updateQuote nicht verfügbar');
      return;
    }
    
    const updateResult = await updateQuote(quoteId, {
      marker_color: color
    });
    
    if (updateResult.success) {
      // Aktualisiere Icon im Member Panel
      const quoteItem = document.querySelector(`.member-item[data-id="${quoteId}"][data-type="quote"]`);
      if (quoteItem) {
        const iconElement = quoteItem.querySelector('.quote-bookmark-icon-header');
        if (iconElement) {
          const quoteColorHex = getHighlightColor(color);
          iconElement.style.color = quoteColorHex;
        }
      }
      
      // Aktualisiere Quote-Markierungen im Viewer (senkrechte Linie)
      const quoteColorHex = getHighlightColor(color);
      const quoteSpans = document.querySelectorAll(`[data-quote-id="${quoteId}"][data-quote="true"]`);
      quoteSpans.forEach(span => {
        span.setAttribute('data-quote-color', color);
        
        // Aktualisiere Bookmark-Icons falls vorhanden
        const bookmarkIcon = span.querySelector('.quote-bookmark-icon');
        if (bookmarkIcon) {
          bookmarkIcon.style.color = quoteColorHex;
        }
      });
      
      // Aktualisiere senkrechte Linien rechts neben Absätzen
      const verticalLines = document.querySelectorAll(`.member-quote-vertical-line[data-quote-id="${quoteId}"]`);
      verticalLines.forEach(line => {
        line.style.backgroundColor = quoteColorHex;
        line.setAttribute('data-quote-color', color);
      });
      
      // Aktualisiere Bookmark-Icons in Absätzen
      const quote = updateResult.data;
      if (quote && quote.paragraph_id) {
        const paraElement = document.getElementById(`para-${quote.paragraph_id}`);
        if (paraElement) {
          const indicator = paraElement.querySelector('.bookmark-quote-indicator');
          if (indicator) {
            const quoteColorHex = getHighlightColor(color);
            indicator.style.color = quoteColorHex;
          }
        }
      }
      
      // Invalidiere Cache
      invalidateMembersCache('quotes');
      
      // Aktualisiere Member Panel falls offen
      if (typeof membersPanelActive !== 'undefined' && membersPanelActive && currentMembersTab === 'quotes') {
        await loadMembersTab('quotes');
      }
      
      // Zeige Erfolgsmeldung
      console.log('✓ Farbe geändert');
    } else {
      alert('Fehler beim Ändern der Farbe: ' + updateResult.error);
    }
  } catch (error) {
    console.error('Fehler beim Ändern der Farbe:', error);
    alert('Fehler beim Ändern der Farbe');
  }
}

/**
 * Zeigt das Kontextmenü zum Ändern der Notiz-Farbe
 */
function showNoteColorContextMenu(x, y, noteId) {
  // Entferne vorheriges Menü falls vorhanden
  const existingMenu = document.getElementById('members-note-context-menu');
  if (existingMenu) {
    existingMenu.remove();
  }
  
  // Erstelle neues Menü
  const menu = document.createElement('div');
  menu.id = 'members-note-context-menu';
  menu.className = 'members-highlight-context-menu';
  menu.innerHTML = `
    <div class="highlight-context-menu-item" onclick="changeNoteColor('${noteId}', 'blue')" style="border-left: 3px solid #467886;">
      <span class="highlight-context-menu-text">Blau</span>
    </div>
    <div class="highlight-context-menu-item" onclick="changeNoteColor('${noteId}', 'red')" style="border-left: 3px solid #c62828;">
      <span class="highlight-context-menu-text">Rot</span>
    </div>
    <div class="highlight-context-menu-item" onclick="changeNoteColor('${noteId}', 'yellow')" style="border-left: 3px solid #ffc107;">
      <span class="highlight-context-menu-text">Gelb</span>
    </div>
  `;
  
  document.body.appendChild(menu);
  
  // Positioniere Menü
  menu.style.display = 'block';
  menu.style.left = x + 'px';
  menu.style.top = y + 'px';
  
  // Viewport-Grenzen prüfen
  const menuRect = menu.getBoundingClientRect();
  
  // Rechts aus dem Viewport?
  if (menuRect.right > window.innerWidth) {
    menu.style.left = (window.innerWidth - menuRect.width - 10) + 'px';
  }
  
  // Unten aus dem Viewport?
  if (menuRect.bottom > window.innerHeight) {
    menu.style.top = (window.innerHeight - menuRect.height - 10) + 'px';
  }
  
  // Klick außerhalb schließt Menü
  const closeMenu = (e) => {
    if (!menu.contains(e.target)) {
      menu.remove();
      document.removeEventListener('click', closeMenu);
      document.removeEventListener('contextmenu', closeMenu);
    }
  };
  
  // Warte kurz bevor Event-Listener hinzugefügt wird, damit onclick funktioniert
  setTimeout(() => {
    document.addEventListener('click', closeMenu);
    document.addEventListener('contextmenu', closeMenu);
  }, 100);
}

/**
 * Ändert die Farbe einer Notiz
 */
async function changeNoteColor(noteId, color) {
  // Entferne Kontextmenü
  const menu = document.getElementById('members-note-context-menu');
  if (menu) {
    menu.remove();
  }
  
  try {
    if (typeof updateNote !== 'function') {
      alert('Fehler: updateNote Funktion nicht verfügbar. Bitte Seite neu laden.');
      console.error('[MB-NOTES] updateNote nicht verfügbar');
      return;
    }
    
    // Hole aktuelle Notiz-Daten
    const notesResult = await getNotes();
    if (!notesResult.success) {
      alert('Fehler beim Laden der Notiz');
      return;
    }
    
    const note = notesResult.data.find(n => n.id === noteId);
    if (!note) {
      alert('Notiz nicht gefunden');
      return;
    }
    
    // Aktualisiere nur die Farbe
    const updateResult = await updateNote(noteId, note.title, note.content, note.is_public, note.tags, color);
    
    if (updateResult.success) {
      // Aktualisiere Icon im Member Panel
      const noteItem = document.querySelector(`.member-item[data-id="${noteId}"][data-type="note"]`);
      if (noteItem) {
        const iconElement = noteItem.querySelector('.note-bookmark-icon-header');
        if (iconElement) {
          const noteColorHex = getNoteColor(color);
          iconElement.style.color = noteColorHex;
        }
      }
      
      // Aktualisiere Bookmark-Icon im Viewer
      const noteColorHex = getNoteColor(color);
      const bookmarkIndicator = document.querySelector(`.bookmark-note-indicator[data-note-id="${noteId}"]`);
      if (bookmarkIndicator) {
        bookmarkIndicator.style.color = noteColorHex;
      }
      
      // Invalidiere Cache
      invalidateMembersCache('notes');
      
      // Zeige Erfolgsmeldung
      console.log('✓ Notiz-Farbe geändert');
    } else {
      alert('Fehler beim Ändern der Farbe: ' + updateResult.error);
    }
  } catch (error) {
    console.error('Fehler beim Ändern der Notiz-Farbe:', error);
    alert('Fehler beim Ändern der Farbe');
  }
}

/**
 * Entfernt ein visuelles Zitat aus dem Text
 */
function removeQuoteFromText(quoteId) {
  try {
    // Konvertiere ID zu String für Vergleich (kann als Zahl oder String übergeben werden)
    const idString = String(quoteId);
    
    console.log(`[REMOVE-QUOTE] Suche nach Zitat-ID: ${idString}`);
    
    // Suche alle Zitat-Elemente mit dieser ID
    const quoteElements = document.querySelectorAll(`[data-quote-id="${idString}"]`);
    
    // Debug: Zeige alle vorhandenen Quote-IDs
    if (quoteElements.length === 0) {
      const allIds = Array.from(document.querySelectorAll('[data-quote-id]')).map(el => el.getAttribute('data-quote-id'));
      console.log(`[REMOVE-QUOTE] Vorhandene Quote-IDs im DOM:`, allIds);
    }
    
    console.log(`[REMOVE-QUOTE] Gefunden: ${quoteElements.length} Element(e)`);
    
    quoteElements.forEach(element => {
      // Prüfe ob es eine senkrechte Linie ist
      if (element.classList.contains('member-quote-vertical-line')) {
        element.parentNode?.removeChild(element);
        console.log(`[REMOVE-QUOTE] Senkrechte Linie entfernt`);
        return;
      }
      
      // Prüfe ob es ein klickbarer Text-Link ist
      if (element.classList.contains('quote-text-link')) {
        // Ersetze Span durch seinen Inhalt
        const parent = element.parentNode;
        if (parent) {
          while (element.firstChild) {
            parent.insertBefore(element.firstChild, element);
          }
          parent.removeChild(element);
          parent.normalize();
        }
        console.log(`[REMOVE-QUOTE] Text-Link entfernt`);
        return;
      }
      
      // Prüfe ob es ein Overlay-Marker ist (unsichtbar)
      if (element.getAttribute('data-quote-overlay-marker') === 'true') {
        // Einfach entfernen
        element.parentNode?.removeChild(element);
        console.log(`[REMOVE-QUOTE] Overlay-Marker entfernt`);
        return;
      }
      
      // Prüfe ob es eine Überlagerung auf einer Unterstreichung ist
      if (element.hasAttribute('data-quote-overlay')) {
        // Entferne nur die Hintergrundfarbe und das Overlay-Attribut
        element.style.removeProperty('background-color');
        element.removeAttribute('data-quote-overlay');
        console.log(`[REMOVE-QUOTE] Overlay-Hintergrund von Unterstreichung entfernt`);
        return;
      }
      
      // Normaler Fall: Entferne das span-Element, aber behalte den Inhalt
      const parent = element.parentNode;
      if (parent) {
        // Verschiebe alle Kindknoten aus dem span heraus
        const fragment = document.createDocumentFragment();
        while (element.firstChild) {
          fragment.appendChild(element.firstChild);
        }
        // Füge den Fragment-Inhalt vor dem span ein
        parent.insertBefore(fragment, element);
        // Entferne das leere span-Element
        parent.removeChild(element);
        
        // Normalisiere den Text, um leere Textknoten zu entfernen
        parent.normalize();
        
        console.log(`[REMOVE-QUOTE] Zitat-Element entfernt`);
      }
    });
    
    // Entferne auch Bookmark-Icons, die auf dieses Zitat verweisen
    const bookmarkIcons = document.querySelectorAll(`.bookmark-quote-indicator[data-quote-id="${idString}"]`);
    bookmarkIcons.forEach(icon => {
      icon.parentNode?.removeChild(icon);
      console.log(`[REMOVE-QUOTE] Bookmark-Icon entfernt`);
    });
    
    if (quoteElements.length === 0 && bookmarkIcons.length === 0) {
      console.warn(`[REMOVE-QUOTE] Kein Zitat-Element mit ID ${idString} gefunden`);
    }
  } catch (error) {
    console.error('Fehler beim Entfernen des Zitats aus dem Text:', error);
  }
}

/**
 * Entfernt eine visuelle Unterstreichung aus dem Text
 */
function removeHighlightFromText(highlightId) {
  try {
    // Konvertiere ID zu String für Vergleich (kann als Zahl oder String übergeben werden)
    const idString = String(highlightId);
    
    // Suche im gesamten Dokument nach Highlight-Elementen
    // Prüfe sowohl data-highlight-id als auch andere mögliche Attribute
    const allHighlightElements = document.querySelectorAll('[data-highlight-id], .member-highlight, span[data-highlight="true"]');
    
    const highlightElements = Array.from(allHighlightElements).filter(element => {
      // Prüfe data-highlight-id Attribut
      const elementId = element.getAttribute('data-highlight-id');
      if (elementId) {
        return String(elementId) === idString;
      }
      // Falls kein data-highlight-id vorhanden, prüfe ob es ein Highlight-Element ist
      // und ob es die Klasse member-highlight hat
      return element.classList.contains('member-highlight') || element.getAttribute('data-highlight') === 'true';
    });
    
    // Wenn keine Elemente mit exakter ID gefunden, suche nach allen Highlights
    // und entferne die, die zur gelöschten ID passen könnten
    if (highlightElements.length === 0) {
      // Debug: Zeige alle vorhandenen Highlight-IDs
      const allIds = Array.from(document.querySelectorAll('[data-highlight-id]')).map(el => el.getAttribute('data-highlight-id'));
      console.log(`[REMOVE-HIGHLIGHT] Suche nach Highlight-ID: ${idString}`);
      console.log(`[REMOVE-HIGHLIGHT] Vorhandene Highlight-IDs im DOM:`, allIds);
      
      // Versuche auch mit querySelector direkt
      const directMatch = document.querySelector(`[data-highlight-id="${idString}"]`);
      if (directMatch) {
        highlightElements.push(directMatch);
      }
    }
    
    console.log(`[REMOVE-HIGHLIGHT] Gefunden: ${highlightElements.length} Element(e)`);
    
    highlightElements.forEach(element => {
      // Entferne das span-Element, aber behalte den Inhalt
      const parent = element.parentNode;
      if (parent) {
        // Verschiebe alle Kindknoten aus dem span heraus
        // Erstelle einen DocumentFragment, um alle Knoten zu sammeln
        const fragment = document.createDocumentFragment();
        while (element.firstChild) {
          fragment.appendChild(element.firstChild);
        }
        // Füge den Fragment-Inhalt vor dem span ein
        parent.insertBefore(fragment, element);
        // Entferne das leere span-Element
        parent.removeChild(element);
        
        // Normalisiere den Text, um leere Textknoten zu entfernen
        parent.normalize();
        
        console.log(`[REMOVE-HIGHLIGHT] Highlight-Element entfernt`);
      }
    });
    
    if (highlightElements.length === 0) {
      console.warn(`[REMOVE-HIGHLIGHT] Kein Highlight-Element mit ID ${idString} gefunden`);
    }
  } catch (error) {
    console.error('Fehler beim Entfernen der Unterstreichung aus dem Text:', error);
  }
}

/**
 * Löscht eine Unterstreichung
 */
async function deleteMemberHighlight(id) {
  if (!confirm('Unterstreichung wirklich löschen?')) return;
  
  if (typeof deleteHighlight !== 'function') {
    console.error('[MB-HIGHLIGHTS] deleteHighlight ist nicht verfügbar!');
    return;
  }
  
  const result = await deleteHighlight(id);
  if (result && result.success) {
    // Entferne die visuelle Unterstreichung sofort aus dem Text
    // Versuche mehrmals, falls das Element noch nicht im DOM ist
    removeHighlightFromText(id);
    setTimeout(() => removeHighlightFromText(id), 100);
    setTimeout(() => removeHighlightFromText(id), 500);
    
    // Invalidiere Cache, damit Daten neu geladen werden
    cachedHighlightsData = null;
    await loadMembersTab('highlights');
  }
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
  
  // Zeige Ladeanzeige während Daten geladen werden
  container.innerHTML = '<div class="empty-state"><em>Lade Zitate...</em></div>';
  
  // Verwende Cache wenn verfügbar, sonst lade neu
  let result;
  const now = Date.now();
  const cacheValid = cachedQuotesData && 
                     bookmarksQuotesCacheTimestamp && 
                     (now - bookmarksQuotesCacheTimestamp) < BOOKMARKS_QUOTES_CACHE_TTL;
  
  if (cacheValid) {
    result = cachedQuotesData;
  } else {
    result = await getQuotes();
    // Aktualisiere Cache
    cachedQuotesData = result;
    bookmarksQuotesCacheTimestamp = now;
  }
  
  if (!result.success || result.data.length === 0) {
    container.innerHTML = '<div class="empty-state">Noch keine Zitate</div>';
    // Lade Keywords trotzdem im Hintergrund
    updateKeywordFilterDropdownWithAllKeywords().catch(err => console.warn('[MB-KEYWORDS] Fehler:', err));
    return;
  }
  
  // Sammle alle eindeutigen GA-Nummern für Filter-Dropdown
  const uniqueGANumbers = [...new Set(result.data.map(q => q.ga_reference).filter(Boolean))];
  
  // Sortiere nach Vortragsdatum (kommt direkt aus Supabase) oder Erstellungsdatum als Fallback
  const sortedData = [...result.data].sort((a, b) => {
    const dateA = getLectureDateForSorting(a);
    const dateB = getLectureDateForSorting(b);
    
    if (dateA && dateB) {
      return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
    }
    
    if (dateA && !dateB) {
      return sortOrder === 'asc' ? -1 : 1;
    }
    if (!dateA && dateB) {
      return sortOrder === 'asc' ? 1 : -1;
    }
    
    const createdA = new Date(a.created_at);
    const createdB = new Date(b.created_at);
    return sortOrder === 'asc' ? createdA - createdB : createdB - createdA;
  });
  
  // Rendere mit vollständig geladenen Daten (inkl. Vortragsdaten)
  renderQuotesList(container, sortedData);
  
  // Aktualisiere GA-Filter-Dropdown
  updateGAFilterDropdown(uniqueGANumbers);

  // Lade Keywords parallel (nicht-blockierend für Rendering)
  updateKeywordFilterDropdownWithAllKeywords().catch(err => console.warn('[MB-KEYWORDS] Fehler:', err));
  
}

/**
 * Rendert die Quotes-Liste
 */
function renderQuotesList(container, sortedData) {
  // Filtere nach GA-Nummer wenn Filter aktiv ist
  let filteredData = sortedData;
  if (selectedGAFilter) {
    filteredData = sortedData.filter(quote => {
      const gaNumber = quote.ga_reference || quote.ga_number || '';
      return gaNumber.toLowerCase().startsWith(selectedGAFilter.toLowerCase());
    });
  }
  
  // Multi-Delete-Button hinzufügen wenn Modus aktiv
  const multiDeleteHtml = multiDeleteMode ? `
    <div style="margin-bottom: 1rem; padding: 0.75rem; background: var(--background-color); border: 1px solid var(--border-color); border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
      <span style="font-size: 0.85rem; color: var(--text-color);">Auswahl-Modus aktiv</span>
      <button id="multi-delete-btn" onclick="deleteSelectedItems()" disabled style="padding: 0.4rem 0.8rem; font-size: 0.8rem; background: #c62828; color: white; border: none; border-radius: 4px; cursor: pointer;">Ausgewählte löschen</button>
    </div>
  ` : '';
  
  if (filteredData.length === 0 && sortedData.length > 0) {
    container.innerHTML = '<div class="empty-state">Keine Einträge für das ausgewählte GA-Band gefunden</div>';
    return;
  }
  
  const html = multiDeleteHtml + filteredData.map((quote) => {
    // Hole Datum direkt aus den Quote-Daten (kommt aus Supabase)
    const lectureDate = getLectureDate(quote);
    const dateDisplay = lectureDate ? `<span data-lecture-date="true" style="font-size: 0.85rem; font-weight: normal; color: var(--text-color);">${lectureDate}</span>` : '';
    
    // Prüfe ob es ein Buch ist oder ob paragraph_id vorhanden ist
    const isBook = isBookGANumber(quote.ga_reference);
    const shouldShowLink = quote.paragraph_id || isBook;
    
    // Hole Farbe für Bookmark-Icon
    const quoteColor = quote.marker_color || 'blue';
    const quoteColorHex = getHighlightColor(quoteColor);
    
    return `
    <div class="member-item" data-keywords="${quote.tags ? quote.tags.join(',') : ''}" data-id="${quote.id}" data-type="quote" data-ga-reference="${quote.ga_reference}">
      ${multiDeleteMode ? `<input type="checkbox" class="member-item-checkbox" data-id="${quote.id}" onchange="updateMultiDeleteButton()">` : ''}
      <div style="flex: 1;">
        <div class="member-item-header">
          <div style="display: flex; align-items: center; gap: 0.25rem;">
            ${shouldShowLink
              ? `<a href="#" onclick="saveMembersScrollPosition(); navigateToQuoteById('${quote.id}'); return false;" style="display: inline-block; text-decoration: none; cursor: pointer;" title="Zur Textstelle springen">
                <span class="quote-bookmark-icon-header" style="display: inline-block; color: ${quoteColorHex};">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="4" y="4" width="16" height="16"></rect>
                  </svg>
                </span>
              </a>`
              : `<span class="quote-bookmark-icon-header" style="display: inline-block; color: ${quoteColorHex};">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="4" y="4" width="16" height="16"></rect>
                  </svg>
                </span>`
            }
            ${shouldShowLink
              ? `<strong><a href="#" onclick="saveMembersScrollPosition(); navigateToQuoteById('${quote.id}'); return false;" style="color: var(--link-color); text-decoration: none;">${quote.ga_reference}</a>${dateDisplay ? ', ' + dateDisplay : ''}</strong>`
              : `<strong>${quote.ga_reference}${dateDisplay ? ', ' + dateDisplay : ''}</strong>`
            }
          </div>
          <span class="member-item-date">${new Date(quote.created_at).toLocaleDateString('de-DE')}</span>
        </div>
        ${shouldShowLink
          ? `<div class="member-item-quote"><a href="#" onclick="saveMembersScrollPosition(); navigateToQuoteById('${quote.id}'); return false;" style="color: var(--text-color); text-decoration: none; cursor: pointer;" title="Zur Textstelle springen">"${quote.quote_text.substring(0, 150)}${quote.quote_text.length > 150 ? '...' : ''}"</a></div>`
          : `<div class="member-item-quote">"${quote.quote_text.substring(0, 150)}${quote.quote_text.length > 150 ? '...' : ''}"</div>`
        }
        ${quote.personal_note ? `<div class="member-item-note">${quote.personal_note}</div>` : ''}
        ${quote.tags && quote.tags.length > 0 ? `<div class="member-item-tags">${quote.tags.map(tag => `<span class="tag clickable-tag" onclick="handleKeywordFilter('${tag.replace(/'/g, "\\'")}'); return false;" style="cursor: pointer;" title="Nach diesem Schlagwort filtern">#${tag}</span>`).join(' ')}</div>` : ''}
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
    `;
  }).join('');
  
  container.innerHTML = html;
  
  // Füge Event-Listener für Rechtsklick-Kontextmenü hinzu
  attachQuoteContextMenuListeners(container);
  
  // Scroll-Position wiederherstellen nach Rendering
  setTimeout(() => restoreMembersScrollPosition(), 50);
}


/**
 * Robuste Hilfsfunktion: Findet ein Paragraph-Element mit verschiedenen Strategien
 * @param {string} targetIndex - Der Index des Absatzes
 * @returns {Object} {paraElement, elementToCheck} - Das gefundene Element und das Element zum Prüfen
 */
function findParagraphElementRobust(targetIndex) {
  if (!targetIndex || targetIndex === 'null') {
    return { paraElement: null, elementToCheck: null };
  }
  
  const cleanIndex = targetIndex.toString().replace(/^para-/, '').replace(/^\^/, '');
  let paraElement = null;
  
  // Strategie 1: Direkte Suche mit para- Präfix
  paraElement = document.getElementById(`para-${cleanIndex}`);
  
  // Strategie 2: Suche ohne para- Präfix (falls cleanIndex bereits para- enthält)
  if (!paraElement && !cleanIndex.startsWith('para-')) {
    paraElement = document.getElementById(`para-${cleanIndex}`);
  }
  
  // Strategie 3: Direkte Suche mit der ID
  if (!paraElement) {
    paraElement = document.getElementById(cleanIndex);
  }
  
  // Strategie 4: Suche mit querySelector (für komplexere Selektoren)
  if (!paraElement) {
    paraElement = document.querySelector(`[id*="${cleanIndex}"]`);
  }
  
  // Strategie 5: Suche nach data-paragraph-id Attribut
  if (!paraElement) {
    paraElement = document.querySelector(`[data-paragraph-id="${cleanIndex}"]`);
  }
  
  // Für Bücher: Falls paraElement ein verstecktes span ist, finde das Parent-Element
  let elementToCheck = paraElement;
  if (paraElement && (paraElement.style.display === 'none' || paraElement.tagName.toLowerCase() === 'span')) {
    let parent = paraElement.parentElement;
    while (parent && parent !== document.body) {
      const tagName = parent.tagName.toLowerCase();
      if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
        elementToCheck = parent;
        break;
      }
      parent = parent.parentElement;
    }
  }
  
  return { paraElement, elementToCheck };
}

/**
 * EINFACHE Navigation zu einem Zitat per ID
 * Sucht den quote_text direkt im DOM - viel zuverlässiger als Offset-basierte Suche
 * @param {string} quoteId - Die Quote-ID aus der Datenbank
 */
async function navigateToQuoteById(quoteId) {
  console.log('[QUOTE-NAV] Starte Navigation zu Zitat:', quoteId);
  
  // 1. Hole Zitat-Daten aus Cache oder lade neu
  let quote = null;
  
  if (cachedQuotesData && cachedQuotesData.success && cachedQuotesData.data) {
    quote = cachedQuotesData.data.find(q => q.id === quoteId);
  }
  
  // Falls nicht im Cache, lade Quotes neu
  if (!quote && typeof getQuotes === 'function') {
    console.log('[QUOTE-NAV] Zitat nicht im Cache, lade neu...');
    cachedQuotesData = await getQuotes();
    bookmarksQuotesCacheTimestamp = Date.now();
    if (cachedQuotesData && cachedQuotesData.success && cachedQuotesData.data) {
      quote = cachedQuotesData.data.find(q => q.id === quoteId);
    }
  }
  
  if (!quote) {
    console.error('[QUOTE-NAV] Zitat nicht gefunden:', quoteId);
    return;
  }
  
  console.log('[QUOTE-NAV] Zitat gefunden:', quote.ga_reference, 'Text:', quote.quote_text?.substring(0, 50));
  
  // 2. Lade den Text (GA-Band/Vortrag)
  window.membersNavigating = true;
  membersPanelActive = true;
  
  // WICHTIG: CSS-Klasse hinzufügen, um Absatz-Highlighting zu deaktivieren
  document.body.classList.add('members-navigating');
  
  // Erstelle MutationObserver, der ALLE highlighted-paragraph Klassen SOFORT SYNCHRON entfernt
  const viewer = document.getElementById('viewer') || document.getElementById('main');
  if (viewer) {
    const highlightObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          const element = mutation.target;
          if (element.classList && element.classList.contains('highlighted-paragraph')) {
            element.classList.remove('highlighted-paragraph');
            element.style.removeProperty('background');
            element.style.removeProperty('box-shadow');
          }
        }
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === 1) { // Element node
              if (node.classList && node.classList.contains('highlighted-paragraph')) {
                node.classList.remove('highlighted-paragraph');
                node.style.removeProperty('background');
                node.style.removeProperty('box-shadow');
              }
              const highlightedElements = node.querySelectorAll('.highlighted-paragraph');
              highlightedElements.forEach((el) => {
                el.classList.remove('highlighted-paragraph');
                el.style.removeProperty('background');
                el.style.removeProperty('box-shadow');
              });
            }
          });
        }
      });
    });
    
    highlightObserver.observe(viewer, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class']
    });
    
    // Speichere Observer für späteres Cleanup
    window.membersQuoteHighlightObserver = highlightObserver;
    
    // ZUSÄTZLICH: Entferne sofort alle bestehenden highlighted-paragraph Klassen
    const existingHighlighted = viewer.querySelectorAll('.highlighted-paragraph');
    existingHighlighted.forEach(el => {
      el.classList.remove('highlighted-paragraph');
      el.style.removeProperty('background');
      el.style.removeProperty('box-shadow');
    });
  }
  
  const summaryPanel = document.getElementById('summary-panel');
  if (summaryPanel) {
    summaryPanel.style.setProperty('width', '400px', 'important');
    summaryPanel.style.setProperty('display', 'block', 'important');
    summaryPanel.classList.add('visible');
    document.body.classList.remove('summary-panel-collapsed');
  }
  
  // Verwende paragraph_id wenn vorhanden, damit showLecture den Text lädt
  const targetIndex = quote.paragraph_id || null;
  
  if (typeof showLecture === 'function') {
    await showLecture(quote.ga_reference, targetIndex, [], false);
  }
  
  // 3. Warte bis DOM bereit ist und suche nach dem quote_text
  const findAndScrollToQuote = () => {
    const mainContainer = document.getElementById('main');
    if (!mainContainer) return false;
    
    const quoteText = quote.quote_text;
    if (!quoteText || quoteText.length === 0) {
      console.warn('[QUOTE-NAV] Kein quote_text vorhanden');
      return false;
    }
    
    // WICHTIG: Suche NUR im Textbereich (book-content oder lecture-content), nicht im Inhaltsverzeichnis
    let searchContainer = mainContainer.querySelector('.book-content') || 
                          mainContainer.querySelector('#book-content') ||
                          mainContainer.querySelector('.lecture-content') ||
                          mainContainer.querySelector('#lecture-content');
    
    // Falls kein spezifischer Content-Container gefunden, verwende Main
    if (!searchContainer) {
      searchContainer = mainContainer;
    }
    
    // Prüfe ob der Textbereich tatsächlich Inhalt hat
    if (!searchContainer.textContent || searchContainer.textContent.length < 100) {
      console.log('[QUOTE-NAV] Textbereich noch nicht geladen, warte...');
      return false;
    }
    
    // Suche nach dem Text im Text-Container
    const fullText = searchContainer.textContent || '';
    const textIndex = fullText.indexOf(quoteText);
    
    if (textIndex === -1) {
      console.log('[QUOTE-NAV] Text nicht gefunden, versuche verkürzte Suche...');
      // Versuche mit kürzerem Text (erste 100 Zeichen)
      const shortText = quoteText.substring(0, Math.min(100, quoteText.length));
      if (fullText.indexOf(shortText) === -1) {
        return false;
      }
    }
    
    console.log('[QUOTE-NAV] Text gefunden, suche DOM-Element...');
    
    // Finde das DOM-Element, das den Text enthält
    const walker = document.createTreeWalker(
      searchContainer,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    let node;
    let accumulatedLength = 0;
    let targetNode = null;
    
    while (node = walker.nextNode()) {
      const nodeText = node.textContent;
      if (nodeText.includes(quoteText) || nodeText.includes(quoteText.substring(0, 50))) {
        targetNode = node;
        break;
      }
      // Alternativ: Prüfe ob wir in der Nähe des Indexes sind
      if (!targetNode && accumulatedLength <= textIndex && accumulatedLength + nodeText.length > textIndex) {
        targetNode = node;
        break;
      }
      accumulatedLength += nodeText.length;
    }
    
    if (!targetNode) {
      console.warn('[QUOTE-NAV] Kein DOM-Element gefunden');
      return false;
    }
    
    // Finde das Parent-Element (p, div, etc.) für das Highlighting
    let scrollTarget = targetNode.parentElement;
    while (scrollTarget && !['P', 'DIV', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'LI', 'BLOCKQUOTE'].includes(scrollTarget.tagName)) {
      scrollTarget = scrollTarget.parentElement;
    }
    
    if (!scrollTarget) {
      scrollTarget = targetNode.parentElement;
    }
    
    // 4. ERST Highlighting anwenden, DANN zum Highlight-Element scrollen
    if (typeof applyQuoteHighlightToElement === 'function') {
      applyQuoteHighlightToElement(scrollTarget, quote);
    }
    
    // 5. Finde das erstellte Highlight-Element und scrolle dorthin
    const header = document.getElementById('viewer-header');
    const headerHeight = header ? header.offsetHeight + 5 : 5;
    const mainRect = mainContainer.getBoundingClientRect();
    const viewportHeight = mainRect.height - headerHeight;
    const upperQuarterOffset = Math.round(viewportHeight * 0.02);
    
    // Suche das erstellte Highlight-Element für dieses Zitat
    const highlightElement = document.querySelector(`[data-quote-id="${quote.id}"][data-quote="true"]`);
    
    if (highlightElement) {
      // Scrolle zum Highlight-Element (nicht zum Absatz)
      const highlightRect = highlightElement.getBoundingClientRect();
      const relativeTop = highlightRect.top - mainRect.top + mainContainer.scrollTop - headerHeight - upperQuarterOffset;
      mainContainer.scrollTop = Math.max(0, relativeTop);
      console.log('[QUOTE-NAV] Gescrollt zum Zitat-Highlight, Position:', mainContainer.scrollTop);
    } else {
      // Fallback: Scrolle zum Absatz
      const elementRect = scrollTarget.getBoundingClientRect();
      const relativeTop = elementRect.top - mainRect.top + mainContainer.scrollTop - headerHeight - upperQuarterOffset;
      mainContainer.scrollTop = Math.max(0, relativeTop);
      console.log('[QUOTE-NAV] Fallback: Gescrollt zum Absatz, Position:', mainContainer.scrollTop);
    }
    
    return true;
  };
  
  // Versuche mehrmals (für langsam ladende Inhalte)
  let attempts = 0;
  const maxAttempts = 30;
  
  const tryFind = () => {
    attempts++;
    if (findAndScrollToQuote()) {
      // Erfolgreich - Cleanup
      setTimeout(() => {
        window.membersNavigating = false;
        document.body.classList.remove('members-navigating');
        // Entferne MutationObserver
        if (window.membersQuoteHighlightObserver) {
          window.membersQuoteHighlightObserver.disconnect();
          window.membersQuoteHighlightObserver = null;
        }
      }, 500);
      return;
    }
    
    if (attempts < maxAttempts) {
      setTimeout(tryFind, 100);
    } else {
      console.warn('[QUOTE-NAV] Konnte Zitat nach', maxAttempts, 'Versuchen nicht finden');
      window.membersNavigating = false;
      document.body.classList.remove('members-navigating');
      // Entferne MutationObserver
      if (window.membersQuoteHighlightObserver) {
        window.membersQuoteHighlightObserver.disconnect();
        window.membersQuoteHighlightObserver = null;
      }
    }
  };
  
  // Starte Suche nach kurzer Verzögerung
  setTimeout(tryFind, 300);
}

// Expose für onclick
window.navigateToQuoteById = navigateToQuoteById;

/**
 * Navigiere zu Notiz aus Members Panel
 * Ruft navigateToLectureFromMembersPanel auf, falls GA-Referenz vorhanden ist
 */
async function navigateToNoteFromMembersPanel(noteId, gaReference, paragraphId = null, textStartOffset = null, textEndOffset = null) {
  if (!gaReference) {
    console.warn('[MB-NOTE-NAV] Keine GA-Referenz für Notiz:', noteId);
    return;
  }
  
  // Hole Notiz-Daten für Textsuche
  try {
    const result = await getNotes();
    if (!result.success) {
      console.error('[MB-NOTE-NAV] Fehler beim Laden der Notiz');
      // Fallback: Verwende normale Navigation
      if (typeof navigateToLectureFromMembersPanel === 'function') {
        await navigateToLectureFromMembersPanel(gaReference, paragraphId, textStartOffset, textEndOffset, false);
      }
      return;
    }
    
    const note = result.data.find(n => n.id === noteId);
    if (!note || !note.content) {
      console.warn('[MB-NOTE-NAV] Notiz nicht gefunden oder kein Content');
      // Fallback: Verwende normale Navigation
      if (typeof navigateToLectureFromMembersPanel === 'function') {
        await navigateToLectureFromMembersPanel(gaReference, paragraphId, textStartOffset, textEndOffset, false);
      }
      return;
    }
    
    // Bereinige Text: Entferne Präfixe wie "Aus [[GA001]]:" und Tags am Ende
    let fullNoteText = note.content;
    console.log('[MB-NOTE-NAV] Original Content:', fullNoteText.substring(0, 100));
    
    fullNoteText = fullNoteText.replace(/^Aus\s*\[\[[^\]]+\]\]\s*[-:]\s*/i, '');
    fullNoteText = fullNoteText.replace(/^["„"']\s*/g, '').trim(); // Entferne verschiedene Anführungszeichen am Anfang
    fullNoteText = fullNoteText.replace(/["„"']\s*$/g, '').trim(); // Entferne verschiedene Anführungszeichen am Ende
    fullNoteText = fullNoteText.replace(/\n\n\[\[GA\d+\]\]/g, ''); // Entferne GA-Referenzen am Ende
    fullNoteText = fullNoteText.replace(/\n\n#\w+(\s+#\w+)*/g, ''); // Entferne Tags am Ende
    fullNoteText = fullNoteText.replace(/^\s+/, '').trim();
    
    console.log('[MB-NOTE-NAV] Bereinigter Text:', fullNoteText.substring(0, 100));
    
    // Kurzer Suchtext für die Suche (erste 100 Zeichen)
    const searchLength = Math.min(100, fullNoteText.length);
    const searchTerm = fullNoteText.substring(0, searchLength).trim();
    
    if (!searchTerm || searchTerm.length < 10) {
      console.warn('[MB-NOTE-NAV] Suchtext zu kurz:', searchTerm);
      // Fallback: Verwende normale Navigation
      if (typeof navigateToLectureFromMembersPanel === 'function') {
        await navigateToLectureFromMembersPanel(gaReference, paragraphId, textStartOffset, textEndOffset, false);
      }
      return;
    }
    
    // Navigiere zum Vortrag (ohne searchTerm, da wir Offset-Markierung verwenden)
    if (typeof navigateToLectureFromMembersPanel === 'function') {
      // Wenn paragraphId vorhanden ist, verwende normale Navigation
      if (paragraphId) {
        // Kein searchTerm übergeben - nur die Offset-Markierung verwenden
        await navigateToLectureFromMembersPanel(gaReference, paragraphId, null, null, false, null);
        // Markiere den gesamten Notiztext im Paragraph nach dem Laden
        // Verwende die gespeicherten Offsets
        const startOffset = note.text_start_offset;
        const endOffset = note.text_end_offset;
        setTimeout(() => markNoteTextByOffset(paragraphId, startOffset, endOffset, fullNoteText), 800);
      } else {
        // Kein paragraphId: Verwende Textsuche
        await navigateToLectureFromMembersPanel(gaReference, null, null, null, false, null);
        // Nach dem Laden des Vortrags: Suche nach dem Text und scrolle dorthin
        await findAndScrollToTextInLecture(searchTerm, fullNoteText);
      }
    } else {
      console.error('[MB-NOTE-NAV] navigateToLectureFromMembersPanel nicht verfügbar');
    }
  } catch (error) {
    console.error('[MB-NOTE-NAV] Fehler bei Navigation:', error);
    // Fallback: Verwende normale Navigation
    if (typeof navigateToLectureFromMembersPanel === 'function') {
      await navigateToLectureFromMembersPanel(gaReference, paragraphId, textStartOffset, textEndOffset, false);
    }
  }
}

// Expose für onclick
window.navigateToNoteFromMembersPanel = navigateToNoteFromMembersPanel;

/**
 * Sucht nach Text im geladenen Vortrag und scrollt zur gefundenen Stelle
 * @param searchText - Kurzer Text für die Suche (erste 100 Zeichen)
 * @param fullText - Vollständiger Text zum Markieren (optional)
 */
async function findAndScrollToTextInLecture(searchText, fullText = null) {
  if (!searchText || !searchText.trim()) {
    return;
  }
  
  const cleanSearchText = searchText.trim();
  const textToHighlight = fullText ? fullText.trim() : cleanSearchText;
  console.log('[NOTE-TEXT-SEARCH] Suche nach Text:', cleanSearchText.substring(0, 50) + '...');
  
  // Warte bis der Vortrag geladen ist
  let attempts = 0;
  const maxAttempts = 50;
  
  const tryFindText = () => {
    attempts++;
    
    const mainContainer = document.getElementById('main');
    if (!mainContainer) {
      if (attempts < maxAttempts) {
        setTimeout(() => requestAnimationFrame(tryFindText), 100);
      }
      return;
    }
    
    // Suche im Textbereich (book-content oder lecture-content)
    let searchContainer = mainContainer.querySelector('.book-content') || 
                          mainContainer.querySelector('#book-content') ||
                          mainContainer.querySelector('.lecture-content') ||
                          mainContainer.querySelector('#lecture-content');
    
    if (!searchContainer) {
      searchContainer = mainContainer;
    }
    
    // Prüfe ob Text geladen ist
    if (!searchContainer.textContent || searchContainer.textContent.length < 100) {
      if (attempts < maxAttempts) {
        setTimeout(() => requestAnimationFrame(tryFindText), 100);
      }
      return;
    }
    
    // Suche nach dem Text im gesamten Container
    const containerText = searchContainer.textContent || '';
    const textIndex = containerText.indexOf(cleanSearchText);
    
    if (textIndex === -1) {
      // Versuche mit kürzerem Text (erste 50 Zeichen)
      const shortText = cleanSearchText.substring(0, Math.min(50, cleanSearchText.length));
      const shortIndex = containerText.indexOf(shortText);
      
      if (shortIndex === -1) {
        console.warn('[NOTE-TEXT-SEARCH] Text nicht gefunden');
        return;
      }
      
      // Text gefunden, scrolle zur Stelle und highlighte vollständigen Text
      scrollToTextPosition(searchContainer, shortIndex, textToHighlight);
    } else {
      // Text gefunden, scrolle zur Stelle und highlighte vollständigen Text
      scrollToTextPosition(searchContainer, textIndex, textToHighlight);
    }
  };
  
  // Starte Suche nach kurzer Verzögerung
  setTimeout(() => {
    requestAnimationFrame(tryFindText);
  }, 500);
}

/**
 * Scrollt zur Textposition im Container
 */
function scrollToTextPosition(container, textIndex, searchText) {
  const mainContainer = document.getElementById('main');
  if (!mainContainer || !container) {
    return;
  }
  
  // Erstelle einen Range, um die Position zu finden
  const range = document.createRange();
  let textNode = null;
  let charCount = 0;
  
  // Durchlaufe alle Textknoten im Container
  const walker = document.createTreeWalker(
    container,
    NodeFilter.SHOW_TEXT,
    null,
    false
  );
  
  let node;
  while (node = walker.nextNode()) {
    const nodeLength = node.textContent.length;
    if (charCount + nodeLength >= textIndex) {
      textNode = node;
      break;
    }
    charCount += nodeLength;
  }
  
  if (!textNode) {
    console.warn('[NOTE-TEXT-SEARCH] Textknoten nicht gefunden');
    return;
  }
  
  // Setze Range auf die gefundene Position
  const offsetInNode = textIndex - charCount;
  range.setStart(textNode, Math.min(offsetInNode, textNode.textContent.length));
  range.setEnd(textNode, Math.min(offsetInNode, textNode.textContent.length));
  
  // Finde das umschließende Element (Paragraph oder ähnliches)
  let element = range.commonAncestorContainer;
  if (element.nodeType === Node.TEXT_NODE) {
    element = element.parentElement;
  }
  
  // Suche nach einem Block-Element (p, div, etc.)
  while (element && element !== container) {
    if (element.tagName === 'P' || element.tagName === 'DIV' || element.classList.contains('paragraph')) {
      break;
    }
    element = element.parentElement;
  }
  
  if (!element || element === container) {
    element = textNode.parentElement;
  }
  
  // Scrolle zum Element
  const elementRect = element.getBoundingClientRect();
  const mainRect = mainContainer.getBoundingClientRect();
  const header = document.getElementById('viewer-header');
  const headerHeight = header ? header.offsetHeight + 5 : 5;
  
  const viewportHeight = mainRect.height - headerHeight;
  const upperQuarterOffset = Math.round(viewportHeight * 0.02);
  
  const relativeTop = elementRect.top - mainRect.top + mainContainer.scrollTop - headerHeight - upperQuarterOffset;
  mainContainer.scrollTop = Math.max(0, relativeTop);
  
  console.log('[NOTE-TEXT-SEARCH] Zu Textstelle gescrollt');
}

/**
 * Markiert den Notiztext anhand von Start- und End-Offset im Paragraph
 */
function markNoteTextByOffset(paragraphId, startOffset, endOffset, noteText) {
  console.log('[NOTE-MARK] Markiere Notiz ab Paragraph:', paragraphId);
  console.log('[NOTE-MARK] Offsets:', startOffset, '-', endOffset);
  console.log('[NOTE-MARK] noteText:', noteText?.substring(0, 100));
  
  if (!paragraphId) {
    console.warn('[NOTE-MARK] Fehlende paragraphId');
    return;
  }
  
  // Finde den Start-Paragraph
  const paraElement = document.getElementById(`para-${paragraphId}`);
  if (!paraElement) {
    console.warn('[NOTE-MARK] Paragraph nicht gefunden:', paragraphId);
    return;
  }
  
  // Finde den Content-Container
  let contentContainer = document.getElementById('lecture-content') || 
                         document.getElementById('text-content') ||
                         document.querySelector('.lecture-content') ||
                         document.querySelector('.text-content');
  
  if (!contentContainer) {
    contentContainer = paraElement.closest('.lecture-content, .text-content, article, main') || paraElement.parentElement;
  }
  
  // Entferne vorherige Notiz-Markierungen
  const existingMarks = document.querySelectorAll('mark.note-highlight');
  existingMarks.forEach(mark => {
    const parent = mark.parentNode;
    while (mark.firstChild) {
      parent.insertBefore(mark.firstChild, mark);
    }
    parent.removeChild(mark);
  });
  if (contentContainer) contentContainer.normalize();
  
  // Suche den noteText direkt im DOM
  try {
    // Sammle alle Absätze ab dem Start-Paragraph
    const allParagraphs = contentContainer.querySelectorAll('[id^="para-"]');
    let startCollecting = false;
    const relevantParagraphs = [];
    
    for (const para of allParagraphs) {
      if (para.id === `para-${paragraphId}`) {
        startCollecting = true;
      }
      if (startCollecting) {
        relevantParagraphs.push(para);
        // Sammle max 10 Absätze
        if (relevantParagraphs.length >= 10) break;
      }
    }
    
    // Sammle alle Textknoten aus den relevanten Absätzen
    const textNodes = [];
    let charCount = 0;
    for (const para of relevantParagraphs) {
      const walker = document.createTreeWalker(para, NodeFilter.SHOW_TEXT, null, false);
      let node;
      while (node = walker.nextNode()) {
        if (node.textContent.length > 0) {
          textNodes.push({
            node: node,
            start: charCount,
            end: charCount + node.textContent.length
          });
          charCount += node.textContent.length;
        }
      }
    }
    
    // Baue den kombinierten Text
    const combinedText = textNodes.map(n => n.node.textContent).join('');
    console.log('[NOTE-MARK] Kombinierter Text Länge:', combinedText.length);
    console.log('[NOTE-MARK] Kombinierter Text Anfang:', combinedText.substring(0, 100));
    
    let foundStart = -1;
    let foundEnd = -1;
    
    // METHODE 1: Verwende gespeicherte Offsets wenn vorhanden
    if (startOffset !== null && startOffset !== undefined && endOffset !== null && endOffset !== undefined) {
      foundStart = startOffset;
      foundEnd = endOffset;
      console.log('[NOTE-MARK] Verwende gespeicherte Offsets:', foundStart, '-', foundEnd);
    }
    
    // METHODE 2: Suche den noteText im kombinierten Text
    if (noteText && noteText.length > 0) {
      // Bereite den Suchtext vor
      let searchText = noteText.trim();
      
      // Exakte Suche
      let textFoundStart = combinedText.indexOf(searchText);
      
      if (textFoundStart === -1) {
        // Versuche normalisierte Suche (mehrfache Leerzeichen zu einem)
        const normalizedSearch = searchText.replace(/\s+/g, ' ').trim();
        const normalizedCombined = combinedText.replace(/\s+/g, ' ');
        const normalizedFoundStart = normalizedCombined.indexOf(normalizedSearch);
        
        if (normalizedFoundStart !== -1) {
          // Mappe normalisierte Position zurück auf Original
          let origPos = 0;
          let normPos = 0;
          for (let i = 0; i < combinedText.length; i++) {
            if (normPos >= normalizedFoundStart) {
              textFoundStart = i;
              break;
            }
            if (/\s/.test(combinedText[i])) {
              // Nur zählen wenn vorheriges Zeichen kein Whitespace war
              if (i === 0 || !/\s/.test(combinedText[i-1])) {
                normPos++;
              }
            } else {
              normPos++;
            }
          }
          console.log('[NOTE-MARK] Normalisierte Suche erfolgreich');
        }
      }
      
      // Wenn Textsuche erfolgreich, verwende diese Positionen
      if (textFoundStart !== -1) {
        foundStart = textFoundStart;
        // End-Position: Suche im Original-Text
        foundEnd = textFoundStart + searchText.length;
        
        // Korrigiere End-Position für normalisierte Texte
        if (foundEnd > combinedText.length) {
          foundEnd = combinedText.length;
        }
        
        console.log('[NOTE-MARK] Textsuche erfolgreich:', foundStart, '-', foundEnd);
      }
    }
    
    if (foundStart === -1 || foundEnd === -1) {
      console.warn('[NOTE-MARK] Keine gültige Position gefunden');
      return;
    }
    
    // Stelle sicher, dass End nicht kleiner als Start ist
    if (foundEnd <= foundStart) {
      foundEnd = foundStart + (noteText?.length || 100);
    }
    console.log('[NOTE-MARK] Finale Position:', foundStart, '-', foundEnd);
    
    // Finde und markiere alle betroffenen Textknoten
    const nodesToMark = [];
    
    for (const nodeInfo of textNodes) {
      // Prüfe Überlappung mit dem zu markierenden Bereich
      if (nodeInfo.end > foundStart && nodeInfo.start < foundEnd) {
        const markStart = Math.max(0, foundStart - nodeInfo.start);
        const markEnd = Math.min(nodeInfo.node.textContent.length, foundEnd - nodeInfo.start);
        
        nodesToMark.push({ 
          node: nodeInfo.node, 
          start: markStart, 
          end: markEnd 
        });
      }
      
      if (nodeInfo.end >= foundEnd) break;
    }
    
    console.log('[NOTE-MARK] Knoten zu markieren:', nodesToMark.length);
    
    // Markiere rückwärts (um Offsets nicht zu verschieben)
    for (let i = nodesToMark.length - 1; i >= 0; i--) {
      const info = nodesToMark[i];
      try {
        const range = document.createRange();
        range.setStart(info.node, info.start);
        range.setEnd(info.node, info.end);
        
        const mark = document.createElement('mark');
        mark.className = 'note-highlight';
        
        try {
          range.surroundContents(mark);
        } catch (e) {
          const fragment = range.extractContents();
          mark.appendChild(fragment);
          range.insertNode(mark);
        }
      } catch (e) {
        console.warn('[NOTE-MARK] Fehler:', e);
      }
    }
    
    if (nodesToMark.length > 0) {
      console.log('[NOTE-MARK] ✓ Erfolgreich markiert');
    }
    
  } catch (error) {
    console.error('[NOTE-MARK] Fehler:', error);
  }
}

/**
 * Navigiere zu Vortrag oder Buch aus Members Panel (behält Panel offen)
 * @param {string} lectureId - Die Vortrags-ID (z.B. "GA121/6") oder Buch-ID (z.B. "GA011")
 * @param {string} targetIndex - Optional: Der Index des Absatzes zum Scrollen
 * @param {number} textStartOffset - Optional: Start-Offset für Textposition
 * @param {number} textEndOffset - Optional: End-Offset für Textposition
 * @param {boolean} shouldHighlightParagraph - Optional: Ob der Absatz markiert werden soll (nur für Zitate)
 */
async function navigateToLectureFromMembersPanel(lectureId, targetIndex = null, textStartOffset = null, textEndOffset = null, shouldHighlightParagraph = false, searchTerm = null) {
  
  const summaryPanel = document.getElementById('summary-panel');
  const summaryContent = document.getElementById('summary-content');
  
  if (!summaryPanel || !membersPanelActive) {
    console.error('[MB-NAVIGATION] Members Panel nicht aktiv');
    return;
  }
  
  const mbWidth = 400;
  
  // WICHTIG: Stelle Panel-Breite SOFORT sicher, BEVOR irgendetwas anderes passiert
  // Das verhindert, dass das Panel während der Navigation springt
  // Verwende sowohl synchron als auch asynchron für maximale Sicherheit
  summaryPanel.style.setProperty('width', mbWidth + 'px', 'important');
  summaryPanel.style.setProperty('min-width', mbWidth + 'px', 'important');
  summaryPanel.style.setProperty('max-width', mbWidth + 'px', 'important');
  summaryPanel.style.transition = 'none';
  summaryPanel.classList.add('visible');
  summaryPanel.style.setProperty('display', 'block', 'important');
  summaryPanel.style.setProperty('opacity', '1', 'important');
  summaryPanel.style.setProperty('visibility', 'visible', 'important');
  document.body.classList.remove('summary-panel-collapsed');
  
  // Zusätzlich mit requestAnimationFrame für sofortige visuelle Aktualisierung
  requestAnimationFrame(() => {
    summaryPanel.style.setProperty('width', mbWidth + 'px', 'important');
    summaryPanel.style.setProperty('min-width', mbWidth + 'px', 'important');
    summaryPanel.style.setProperty('max-width', mbWidth + 'px', 'important');
    summaryPanel.style.transition = 'none';
  });
  
  // Hole Suchbegriff aus Suchfeldern, falls nicht übergeben
  if (!searchTerm || !searchTerm.trim()) {
    // Versuche Suchbegriff aus Suchfeldern zu holen (wie in Suche/erweitert)
    const word1Input = document.getElementById('word1');
    if (word1Input && word1Input.value.trim()) {
      searchTerm = word1Input.value.trim();
      // Die Markierung erfolgt nur mit dem ersten Suchwort
    }
  }
  
  // Klone den GESAMTEN Members-Content
  const savedContentNode = summaryContent ? summaryContent.cloneNode(true) : null;
  const savedContentHTML = summaryContent ? summaryContent.innerHTML : null;
  const savedContentClassName = summaryContent ? summaryContent.className : '';
  
  // Setze Flag - aber nur wenn nicht bereits aktiv (verhindert doppelte Ausführung)
  if (window.membersNavigating) {
    console.warn('[MB-NAVIGATION] Navigation bereits aktiv, ignoriere weiteren Klick');
    return;
  }
  
  window.membersNavigating = true;
  // WICHTIG: CSS-Klasse hinzufügen, um Absatz-Highlighting zu deaktivieren
  document.body.classList.add('members-navigating');
  
  // WICHTIG: KEINE innerHTML-Überschreibung mehr - das blockiert showLecture!
  // Stattdessen verwenden wir einen MutationObserver, der den Content wiederherstellt
  let contentRestoreObserver = null;
  let originalInnerHTMLDescriptor = null;
  
  // Speichere originalen Content - WICHTIG: Speichere auch wenn leer (für späteres Neuladen)
  const savedContentForRestore = summaryContent ? summaryContent.innerHTML : null;
  
  // WICHTIG: Stelle Panel-Breite SOFORT sicher, BEVOR wir Content laden
  // Das verhindert, dass das Panel während des Ladens springt
  if (summaryPanel) {
    summaryPanel.style.setProperty('width', mbWidth + 'px', 'important');
    summaryPanel.style.setProperty('min-width', mbWidth + 'px', 'important');
    summaryPanel.style.setProperty('max-width', mbWidth + 'px', 'important');
    summaryPanel.style.transition = 'none';
    summaryPanel.classList.add('visible');
    summaryPanel.style.setProperty('display', 'block', 'important');
    summaryPanel.style.setProperty('opacity', '1', 'important');
    summaryPanel.style.setProperty('visibility', 'visible', 'important');
    document.body.classList.remove('summary-panel-collapsed');
  }
  
  // WICHTIG: Wenn Content leer ist beim ersten Öffnen, lade ihn vor der Navigation
  if (summaryContent && (!savedContentForRestore || savedContentForRestore.trim().length === 0 || 
      (!savedContentForRestore.includes('members-tab-content') && 
       !savedContentForRestore.includes('members-login-form') && 
       !savedContentForRestore.includes('member-item')))) {
    console.log('[MB-NAVIGATION] Content ist leer oder nicht Members-Content, lade vor Navigation');
    
    // Stelle sicher, dass Panel-Breite während des Ladens geschützt bleibt
    if (summaryPanel) {
      summaryPanel.style.setProperty('width', mbWidth + 'px', 'important');
      summaryPanel.style.setProperty('min-width', mbWidth + 'px', 'important');
      summaryPanel.style.setProperty('max-width', mbWidth + 'px', 'important');
      summaryPanel.style.transition = 'none';
    }
    
    if (typeof loadMembersTab === 'function') {
      await loadMembersTab(currentMembersTab || 'highlights');
      // Warte kurz, damit Content geladen wird
      await new Promise(resolve => setTimeout(resolve, 200));
      // Speichere Content erneut nach dem Laden
      const refreshedContent = summaryContent ? summaryContent.innerHTML : null;
      if (refreshedContent && refreshedContent.trim().length > 0) {
        // Verwende den neuen Content als gespeicherten Content
        window.savedMembersContentForRestore = refreshedContent;
      }
      
      // Stelle sicher, dass Panel-Breite nach dem Laden noch geschützt ist
      if (summaryPanel) {
        summaryPanel.style.setProperty('width', mbWidth + 'px', 'important');
        summaryPanel.style.setProperty('min-width', mbWidth + 'px', 'important');
        summaryPanel.style.setProperty('max-width', mbWidth + 'px', 'important');
        summaryPanel.style.transition = 'none';
      }
    }
  }
  
  // Verwende gespeicherten Content aus window, falls vorhanden (wurde oben gesetzt)
  const contentToRestore = window.savedMembersContentForRestore || savedContentForRestore;
  
  // Erstelle MutationObserver, der den Members-Content wiederherstellt, falls er überschrieben wird
  if (summaryContent && contentToRestore) {
    contentRestoreObserver = new MutationObserver((mutations) => {
      // Prüfe ob der Content geändert wurde und ob Members Panel noch aktiv ist
      if (membersPanelActive && window.membersNavigating) {
        const currentContent = summaryContent.innerHTML;
        // Prüfe ob Members-Content noch vorhanden ist
        const hasMembersContent = currentContent.includes('members-tab-content') || 
                                  currentContent.includes('members-login-form') ||
                                  currentContent.includes('member-item');
        
        // Wenn Members-Content fehlt, stelle ihn SYNCHRON wieder her
        // WICHTIG: Keine requestAnimationFrame verwenden - das verursacht Flackern!
        const contentToUse = window.savedMembersContentForRestore || savedContentForRestore;
        if (!hasMembersContent && contentToUse && contentToUse.trim().length > 0) {
          console.log('[MB-NAVIGATION] Content wurde überschrieben, stelle SOFORT wieder her');
          // SYNCHRONE Wiederherstellung - verhindert Flackern
          if (membersPanelActive && summaryContent) {
            summaryContent.innerHTML = contentToUse;
          }
        } else if (!hasMembersContent && membersPanelActive) {
          // Content ist leer - lade neu
          console.log('[MB-NAVIGATION] Content ist leer, lade neu');
          if (typeof loadMembersTab === 'function') {
            loadMembersTab(currentMembersTab || 'highlights');
          }
        }
      }
    });
    
    // Beobachte nur childList-Änderungen (nicht attributes, um Performance zu verbessern)
    contentRestoreObserver.observe(summaryContent, {
      childList: true,
      subtree: false // Nur direkte Kinder, nicht den ganzen Subtree
    });
  }
  
  // Stoppe Scroll-Position-Schutz während Navigation, um Springen zu vermeiden
  stopScrollPositionProtection();
  
  // Extrahiere GA-Nummer
  const gaNumber = lectureId.split('/')[0];
  
  // Prüfe ob es ein Buch ist
  const isBook = isBookGANumber(gaNumber);
  
  // Blockiere buildTableOfContents - WICHTIG: Blockiere solange Members Panel aktiv ist
  // Dies verhindert, dass das TOC geöffnet wird, wenn auf einen Link geklickt wird
  const originalBuildTOC = window.buildTableOfContents;
  if (!window.originalBuildTOC && originalBuildTOC) {
    window.originalBuildTOC = originalBuildTOC;
  }
  
  window.buildTableOfContents = function() {
    // Blockiere TOC-Bau, wenn Members Panel aktiv ist (nicht nur während Navigation)
    if (membersPanelActive) {
      console.log('[MB-NAVIGATION] buildTableOfContents blockiert - Members Panel ist aktiv');
      return;
    }
    // Auch während Navigation blockieren
    if (window.membersNavigating) {
      console.log('[MB-NAVIGATION] buildTableOfContents blockiert - Navigation läuft');
      return;
    }
    const funcToCall = originalBuildTOC || window.originalBuildTOC;
    return funcToCall ? funcToCall.apply(this, arguments) : null;
  };
  
  // Stelle Panel-Eigenschaften sicher BEVOR wir navigieren (damit es offen bleibt)
  // WICHTIG: Dies muss VOR dem Content-Laden passieren, um Springen zu verhindern
  if (summaryPanel) {
    // WICHTIG: Deaktiviere CSS-Transitions während Navigation (verhindert Springen)
    const originalTransition = summaryPanel.style.transition;
    summaryPanel.style.transition = 'none';
    
    // Setze Breite mit !important-Level (setProperty mit important)
    // WICHTIG: Verwende requestAnimationFrame für sofortige Ausführung
    requestAnimationFrame(() => {
      summaryPanel.style.setProperty('width', mbWidth + 'px', 'important');
      summaryPanel.style.setProperty('min-width', mbWidth + 'px', 'important');
      summaryPanel.style.setProperty('max-width', mbWidth + 'px', 'important');
      summaryPanel.classList.add('visible');
      summaryPanel.style.setProperty('display', 'block', 'important');
      summaryPanel.style.setProperty('opacity', '1', 'important');
      summaryPanel.style.setProperty('visibility', 'visible', 'important');
      document.body.classList.remove('summary-panel-collapsed');
    });
    
    // Setze auch synchron, damit es sofort wirksam ist
    summaryPanel.style.setProperty('width', mbWidth + 'px', 'important');
    summaryPanel.style.setProperty('min-width', mbWidth + 'px', 'important');
    summaryPanel.style.setProperty('max-width', mbWidth + 'px', 'important');
    summaryPanel.classList.add('visible');
    summaryPanel.style.setProperty('display', 'block', 'important');
    summaryPanel.style.setProperty('opacity', '1', 'important');
    summaryPanel.style.setProperty('visibility', 'visible', 'important');
    document.body.classList.remove('summary-panel-collapsed');
    
    // Erstelle einen aggressiven Observer, der kontinuierlich die Breite überwacht
    const panelVisibilityObserver = new MutationObserver(() => {
      // Prüfe und stelle Breite SOFORT wieder her, wenn sie geändert wurde
      if (membersPanelActive && window.membersNavigating) {
        const currentWidth = summaryPanel.style.width || window.getComputedStyle(summaryPanel).width;
        const widthValue = parseInt(currentWidth);
        
        // Wenn Breite nicht 400px ist, stelle sie sofort wieder her
        if (widthValue !== mbWidth) {
          summaryPanel.style.setProperty('width', mbWidth + 'px', 'important');
          summaryPanel.style.setProperty('min-width', mbWidth + 'px', 'important');
          summaryPanel.style.setProperty('max-width', mbWidth + 'px', 'important');
          summaryPanel.style.transition = 'none'; // Transition bleibt deaktiviert
          
          // Stelle auch andere Eigenschaften sicher
          if (!summaryPanel.classList.contains('visible')) {
            summaryPanel.classList.add('visible');
          }
          if (summaryPanel.style.display === 'none') {
            summaryPanel.style.setProperty('display', 'block', 'important');
          }
          if (summaryPanel.style.opacity === '0') {
            summaryPanel.style.setProperty('opacity', '1', 'important');
          }
          if (summaryPanel.style.visibility === 'hidden') {
            summaryPanel.style.setProperty('visibility', 'visible', 'important');
          }
        }
      }
    });
    
    // Beobachte sowohl Attribute- als auch ChildList-Änderungen
    panelVisibilityObserver.observe(summaryPanel, {
      attributes: true,
      attributeFilter: ['style', 'class'],
      childList: false,
      subtree: false
    });
    
    // Zusätzlich: Kontinuierliche Überwachung mit setInterval während Navigation
    const widthCheckInterval = setInterval(() => {
      if (membersPanelActive && window.membersNavigating) {
        const currentWidth = summaryPanel.style.width || window.getComputedStyle(summaryPanel).width;
        const widthValue = parseInt(currentWidth);
        
        if (widthValue !== mbWidth) {
          summaryPanel.style.setProperty('width', mbWidth + 'px', 'important');
          summaryPanel.style.setProperty('min-width', mbWidth + 'px', 'important');
          summaryPanel.style.setProperty('max-width', mbWidth + 'px', 'important');
          summaryPanel.style.transition = 'none';
        }
      } else {
        // Navigation beendet - stelle Transition wieder her und stoppe Interval
        if (originalTransition) {
          summaryPanel.style.transition = originalTransition;
        } else {
          summaryPanel.style.removeProperty('transition');
        }
        clearInterval(widthCheckInterval);
      }
    }, 50); // Prüfe alle 50ms
    
    // Speichere Observer und Interval für Cleanup
    window.panelVisibilityObserver = panelVisibilityObserver;
    window.panelWidthCheckInterval = widthCheckInterval;
  }
  
  // Prüfe ob wir bereits im Texte-Tab sind
  const texteTab = document.getElementById('texte-tab');
  const isInTexteTab = texteTab && texteTab.classList.contains('active');
  
  // Nur Tab wechseln wenn nötig - ABER OHNE Panel zu schließen
  if (!isInTexteTab && typeof switchTab === 'function') {
    // Temporär Flag setzen damit switchTab das Panel nicht schließt
    switchTab('texte');
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Stelle sicher, dass Panel nach Tab-Wechsel noch offen ist
    if (summaryPanel) {
      summaryPanel.style.width = mbWidth + 'px';
      summaryPanel.style.minWidth = mbWidth + 'px';
      summaryPanel.classList.add('visible');
      summaryPanel.style.display = 'block';
      summaryPanel.style.opacity = '1';
      summaryPanel.style.visibility = 'visible';
      document.body.classList.remove('summary-panel-collapsed');
    }
  }
  
  // Setze den GA-Filter und aktualisiere UI-Elemente
  const texteGAFilter = document.getElementById('texteGAFilter');
  if (texteGAFilter && gaNumber) {
    const currentGA = texteGAFilter.value;
    if (currentGA !== gaNumber) {
      texteGAFilter.value = gaNumber;
    }
    
    // Für GA-Bände mit Vorträgen (nicht Bücher): Lade GA-Daten und aktualisiere UI-Elemente
    // (auch wenn der Wert bereits gesetzt ist, um sicherzustellen, dass UI-Elemente angezeigt werden)
    if (!isBook) {
      try {
        // Lade GA-Übersicht-Daten, um UI-Elemente (Anzahl Vorträge, Toggle-Buttons) anzuzeigen
        const API_BASE = window.API_BASE || '';
        const response = await fetch(`${API_BASE}/api/ga-overview/${gaNumber}`);
        if (response.ok) {
          const data = await response.json();
          
          // Aktualisiere UI-Elemente direkt (ohne openGAOverview aufzurufen, da es das Panel schließt)
          const texteServerInfo = document.getElementById('texteServerInfo');
          if (texteServerInfo) {
            texteServerInfo.textContent = `${data.lectureCount} Vorträge`;
          }
          
          // Zeige Toggle-Buttons
          const texteViewToggle = document.getElementById('texteViewToggle');
          if (texteViewToggle) {
            texteViewToggle.style.display = 'inline-block';
          }
          
          const texteSummaryToggle = document.getElementById('texteSummaryToggle');
          const texteAdminButtons = document.getElementById('texte-admin-buttons');
          if (texteSummaryToggle && texteAdminButtons && texteAdminButtons.style.display !== 'none') {
            texteSummaryToggle.style.display = 'inline-block';
            // Initialisiere Button-Text
            const texteSummaryToggleText = document.getElementById('texteSummaryToggleText');
            if (texteSummaryToggleText) {
              const gaOverviewShowSummaries = window.gaOverviewShowSummaries || false;
              texteSummaryToggleText.textContent = gaOverviewShowSummaries ? 'nur Titel' : 'Kurzzusammenfassung';
            }
          }
        }
      } catch (error) {
        console.error('[MB-NAVIGATION] Fehler beim Laden der GA-Übersicht:', error);
        // Fallback: Trigger Change Event nur wenn Wert geändert wurde
        if (currentGA !== gaNumber) {
          const changeEvent = new Event('change', { bubbles: true });
          texteGAFilter.dispatchEvent(changeEvent);
        }
      }
    }
  }
  
  // WICHTIG: Verhindere IMMER die Absatz-Markierung bei Navigation vom Member Panel
  // (egal ob mit oder ohne Textposition)
  // Verwende globale Variable, damit die originale Funktion bei mehrfachen Klicks erhalten bleibt
  if (!window.originalScrollToIndexInViewer && typeof window.scrollToIndexInViewer === 'function') {
    window.originalScrollToIndexInViewer = window.scrollToIndexInViewer;
  }
  
  const originalScrollToIndexInViewer = window.originalScrollToIndexInViewer;
  const hasTextPosition = targetIndex && textStartOffset !== null && textStartOffset !== undefined;
  
  // Überschreibe scrollToIndexInViewer IMMER, um Markierung zu verhindern
  if (typeof window.scrollToIndexInViewer === 'function') {
    window.scrollToIndexInViewer = function() {
      // Tue nichts - verhindere Markierung
    };
  }
  
  // Verwende MutationObserver um die Markierung zu verhindern
  // WICHTIG: Absätze sollen NIE markiert werden - nur der exakte Zitat-Text wird markiert
  // Stoppe vorherigen Observer falls vorhanden (verhindert mehrere Observer)
  if (window.membersHighlightObserver) {
    window.membersHighlightObserver.disconnect();
    window.membersHighlightObserver = null;
  }
  
  let highlightObserver = null;
  const viewer = document.getElementById('viewer');
  
  // Verhindere Absatz-Markierungen IMMER (auch für Zitate - nur exakter Text wird markiert)
  if (viewer) {
    // Erstelle MutationObserver, der ALLE highlighted-paragraph Klassen SOFORT SYNCHRON entfernt
    // WICHTIG: Keine requestAnimationFrame verwenden - das verursacht sichtbares Flackern!
    
    highlightObserver = new MutationObserver((mutations) => {
      // SOFORT synchron verarbeiten - keine Verzögerung!
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          const element = mutation.target;
          if (element.classList && element.classList.contains('highlighted-paragraph')) {
            element.classList.remove('highlighted-paragraph');
            // Entferne auch inline-Styles
            element.style.removeProperty('background');
            element.style.removeProperty('box-shadow');
          }
        }
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            if (node.classList && node.classList.contains('highlighted-paragraph')) {
              node.classList.remove('highlighted-paragraph');
              node.style.removeProperty('background');
              node.style.removeProperty('box-shadow');
            }
            if (node.querySelectorAll) {
              const highlightedElements = node.querySelectorAll('.highlighted-paragraph');
              highlightedElements.forEach(el => {
                el.classList.remove('highlighted-paragraph');
                el.style.removeProperty('background');
                el.style.removeProperty('box-shadow');
              });
            }
          }
        });
      });
    });
    
    // Starte Beobachtung des Viewers
    highlightObserver.observe(viewer, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class']
    });
    
    // Speichere Observer global, damit er später gestoppt werden kann
    window.membersHighlightObserver = highlightObserver;
    
    // ZUSÄTZLICH: Entferne sofort alle bestehenden highlighted-paragraph Klassen
    const existingHighlighted = viewer.querySelectorAll('.highlighted-paragraph');
    existingHighlighted.forEach(el => {
      el.classList.remove('highlighted-paragraph');
      el.style.removeProperty('background');
      el.style.removeProperty('box-shadow');
    });
  }
  
  // VEREINHEITLICHT: Verwende showLecture für ALLE Fälle (Bücher UND Vorträge)
  // showLecture erkennt automatisch ob es ein Buch ist und ruft displayBook intern auf
  {
    // Für alle: Verwende showLecture (behandelt Bücher und Vorträge einheitlich)
    // WICHTIG: Verhindere IMMER die Absatz-Markierung bei Navigation vom Member Panel
    
    // WICHTIG: Speichere Unterstreichungen vor dem Neuladen, damit wir sie sofort wieder anwenden können
    const highlightsToRestore = [];
    if (cachedHighlightsData && cachedHighlightsData.success && cachedHighlightsData.data) {
      // Filter unterstützt sowohl Bücher (GA001) als auch Vorträge (GA121/6)
      const lectureHighlights = cachedHighlightsData.data.filter(h => 
        (h.ga_number === lectureId || h.ga_number === gaNumber) && h.paragraph_id
      );
      highlightsToRestore.push(...lectureHighlights);
    }
    
    if (typeof showLecture === 'function') {
      // WICHTIG: KEINE innerHTML-Blockierung mehr - rufe showLecture direkt auf
      // Der MutationObserver stellt den Content automatisch wieder her, falls nötig
      console.log('[MB-NAVIGATION] Rufe showLecture auf für:', lectureId, 'targetIndex:', targetIndex);
      
      // WICHTIG: Behalte membersNavigating=true, damit showLecture weiß, dass Navigation aus MB kommt
      // und das MB nicht schließt und TOC nicht öffnet
      
      try {
        // WICHTIG: Stelle sicher, dass membersPanelActive während showLecture TRUE bleibt
        // (verhindert, dass das Panel während showLecture geschlossen wird)
        const panelWasActive = membersPanelActive;
        membersPanelActive = true;
        
        // Rufe showLecture auf - membersNavigating bleibt true, damit Panel offen bleibt
        const showLectureResult = await showLecture(lectureId, targetIndex, [], false); // false = keine Markierung
        console.log('[MB-NAVIGATION] showLecture abgeschlossen, Ergebnis:', showLectureResult);
        
        // Stelle sicher, dass Panel nach showLecture noch aktiv ist
        if (panelWasActive || window.membersNavigating) {
          membersPanelActive = true;
        }
        
        // WICHTIG: Stelle Panel-Breite SOFORT nach showLecture wieder her (SYNCHRON!)
        // KEINE requestAnimationFrame verwenden - das verursacht Flackern!
        const panelAfterShowLecture = document.getElementById('summary-panel');
        if (panelAfterShowLecture && membersPanelActive) {
          panelAfterShowLecture.style.width = mbWidth + 'px';
          panelAfterShowLecture.style.minWidth = mbWidth + 'px';
          panelAfterShowLecture.classList.add('visible');
          panelAfterShowLecture.classList.add('has-members-panel');
          panelAfterShowLecture.style.display = 'block';
          panelAfterShowLecture.style.opacity = '1';
          panelAfterShowLecture.style.visibility = 'visible';
          document.body.classList.remove('summary-panel-collapsed');
          console.log('[MB-NAVIGATION] Panel SYNCHRON nach showLecture wiederhergestellt');
        }
        
        // Für Vorträge: Markiere Zitat-Text wenn Offsets vorhanden sind (exakte Textmarkierung)
        if (targetIndex && shouldHighlightParagraph && textStartOffset !== null && textEndOffset !== null) {
          // Warte kurz, damit der DOM bereit ist - mehrere Versuche für robustere Navigation
          let highlightAttempts = 0;
          const maxHighlightAttempts = 20;
          let cacheRefreshed = false;
          
          const tryApplyQuoteHighlight = async () => {
            highlightAttempts++;
            
            // Verwende robuste Element-Suche
            const { paraElement, elementToCheck } = findParagraphElementRobust(targetIndex);
            const elementToUse = elementToCheck || paraElement;
            
            if (elementToUse && elementToUse.textContent && elementToUse.textContent.length > 0) {
              // WICHTIG: Für neu gespeicherte Zitate - lade Cache neu, falls er null ist
              if (!cachedQuotesData && !cacheRefreshed && typeof getQuotes === 'function') {
                console.log('[MB-NAVIGATION] Cache leer, lade Quotes neu...');
                cacheRefreshed = true;
                try {
                  cachedQuotesData = await getQuotes();
                  bookmarksQuotesCacheTimestamp = Date.now();
                } catch (e) {
                  console.warn('[MB-NAVIGATION] Fehler beim Laden der Quotes:', e);
                }
              }
              
              // Finde das Zitat basierend auf paragraph_id und offsets
              let quote = null;
              if (cachedQuotesData && cachedQuotesData.success && cachedQuotesData.data) {
                quote = cachedQuotesData.data.find(q => 
                  q.ga_reference === lectureId && 
                  q.paragraph_id === targetIndex &&
                  q.text_start_offset === textStartOffset &&
                  q.text_end_offset === textEndOffset
                );
              }
              
              // WICHTIG: Falls Zitat nicht im Cache gefunden, erstelle ein temporäres Zitat-Objekt
              // Das ermöglicht Highlighting auch für gerade eben gespeicherte Zitate
              if (!quote) {
                console.log('[MB-NAVIGATION] Zitat nicht im Cache, erstelle temporäres Objekt');
                quote = {
                  id: `temp-${Date.now()}`,
                  ga_reference: lectureId,
                  paragraph_id: targetIndex,
                  text_start_offset: textStartOffset,
                  text_end_offset: textEndOffset,
                  quote_text: elementToUse.textContent.substring(textStartOffset, textEndOffset)
                };
              }
              
              if (quote && typeof applyQuoteHighlightToElement === 'function') {
                applyQuoteHighlightToElement(elementToUse, quote);
                return; // Erfolgreich angewendet
              } else if (highlightAttempts < maxHighlightAttempts) {
                // Noch kein Zitat gefunden, versuche es erneut
                setTimeout(() => tryApplyQuoteHighlight(), 100 + (highlightAttempts * 10));
              }
            } else if (highlightAttempts < maxHighlightAttempts) {
              // Element noch nicht bereit, versuche es erneut
              setTimeout(() => tryApplyQuoteHighlight(), 100 + (highlightAttempts * 10));
            }
          };
          
          // Starte den ersten Versuch
          setTimeout(() => tryApplyQuoteHighlight(), 300);
        }
      } catch (error) {
        console.error('[MB-NAVIGATION] Fehler in showLecture:', error);
        console.error('[MB-NAVIGATION] Stack:', error.stack);
        // NICHT weiterwerfen - wir wollen trotzdem fortfahren
      }
      
      // WICHTIG: Wende Unterstreichungen SOFORT wieder an, damit sie nicht abblitzen
      // Verwende mehrere Versuche, um sicherzustellen, dass sie angewendet werden
      // WICHTIG: Sortiere nach text_start_offset, damit Highlights in der richtigen Reihenfolge angewendet werden
      const restoreHighlights = () => {
        if (highlightsToRestore.length > 0 && typeof applyStoredHighlight === 'function') {
          // Gruppiere nach paragraph_id und sortiere innerhalb jeder Gruppe nach text_start_offset
          const highlightsByParagraph = {};
          highlightsToRestore.forEach(highlight => {
            const paraId = highlight.paragraph_id || '';
            if (!highlightsByParagraph[paraId]) {
              highlightsByParagraph[paraId] = [];
            }
            highlightsByParagraph[paraId].push(highlight);
          });
          
          // Sortiere jede Gruppe nach text_start_offset (von Anfang nach Ende)
          Object.keys(highlightsByParagraph).forEach(paraId => {
            highlightsByParagraph[paraId].sort((a, b) => {
              const offsetA = a.text_start_offset !== null && a.text_start_offset !== undefined ? a.text_start_offset : 0;
              const offsetB = b.text_start_offset !== null && b.text_start_offset !== undefined ? b.text_start_offset : 0;
              return offsetA - offsetB;
            });
          });
          
          // Wende Highlights in sortierter Reihenfolge an
          Object.values(highlightsByParagraph).forEach(highlightGroup => {
            highlightGroup.forEach(highlight => {
              applyStoredHighlight(highlight);
            });
          });
        }
      };
      
      // Sofort anwenden (mehrmals versuchen, falls DOM noch nicht bereit)
      restoreHighlights();
      requestAnimationFrame(() => {
        restoreHighlights();
        setTimeout(restoreHighlights, 10);
        setTimeout(restoreHighlights, 50);
        
        // WICHTIG: Nach dem Anwenden der Highlights nochmal zur Unterstreichung scrollen
        // Das stellt sicher, dass die Unterstreichung (nicht der Absatz) oben angezeigt wird
        setTimeout(() => {
          if (textStartOffset !== null && textStartOffset !== undefined && targetIndex) {
            const mainContainer = document.getElementById('main');
            if (!mainContainer) return;
            
            // Suche das Highlight-Element im entsprechenden Absatz
            const { paraElement, elementToCheck } = findParagraphElementRobust(targetIndex);
            if (!elementToCheck) return;
            
            const highlightElements = elementToCheck.querySelectorAll('[data-highlight-id]');
            for (const highlightEl of highlightElements) {
              // Finde das Highlight-Element, das am nächsten zum textStartOffset liegt
              const highlightText = highlightEl.textContent || '';
              const parentText = elementToCheck.textContent || '';
              const highlightStartInParent = parentText.indexOf(highlightText);
              
              // Wenn das Highlight in der Nähe des Offsets liegt (Toleranz: ±50 Zeichen)
              if (Math.abs(highlightStartInParent - textStartOffset) < 50) {
                const highlightRect = highlightEl.getBoundingClientRect();
                const mainRect = mainContainer.getBoundingClientRect();
                const header = document.getElementById('viewer-header');
                const headerHeight = header ? header.offsetHeight + 5 : 5;
                const viewportHeight = mainRect.height - headerHeight;
                const upperQuarterOffset = Math.round(viewportHeight * 0.02);
                
                const currentScrollTop = mainContainer.scrollTop;
                const highlightTopRelativeToViewport = highlightRect.top - mainRect.top;
                const targetScrollTop = currentScrollTop + highlightTopRelativeToViewport - headerHeight - upperQuarterOffset;
                
                mainContainer.scrollTop = Math.max(0, targetScrollTop);
                console.log('[MB-SCROLL] Finaler Scroll zur Unterstreichung, Position:', mainContainer.scrollTop);
                break;
              }
            }
          }
        }, 150);
      });
      
      // Auch über markParagraphsWithBookmarksAndQuotes (falls es noch nicht aufgerufen wurde)
      if (typeof markParagraphsWithBookmarksAndQuotes === 'function') {
        requestAnimationFrame(() => {
          markParagraphsWithBookmarksAndQuotes(lectureId);
        });
      }
    }
  }
  
  // Stelle scrollToIndexInViewer wieder her (nach kurzer Verzögerung)
  // WICHTIG: Verwende die globale Variable, damit die Funktion bei mehrfachen Klicks erhalten bleibt
  if (window.originalScrollToIndexInViewer) {
    setTimeout(() => {
      window.scrollToIndexInViewer = window.originalScrollToIndexInViewer;
    }, 500);
  } else if (originalScrollToIndexInViewer) {
    setTimeout(() => {
      window.scrollToIndexInViewer = originalScrollToIndexInViewer;
    }, 500);
  }
  
  // SOFORT nach dem Laden: Scroll zur Textposition (falls Offsets vorhanden) oder zum Absatz (falls keine Offsets)
  // Mache dies VOR anderen Operationen, damit keine Sprünge sichtbar sind
  // Wenn targetIndex null ist, wird nur der Vortrag geladen ohne zu scrollen
  if (targetIndex && targetIndex !== 'null') {
    // Wenn Offsets vorhanden sind, scrolle zur Textposition
    if (textStartOffset !== null && textStartOffset !== undefined) {
    // Versuche mehrmals zu scrollen, falls das Element noch nicht bereit ist
    let attempts = 0;
    const maxAttempts = 80; // Erhöht für robustere Navigation
    let scrollExecuted = false;
    
    const tryScroll = () => {
      attempts++;
      
      // Verwende robuste Element-Suche
      const { paraElement, elementToCheck } = findParagraphElementRobust(targetIndex);
      
      const mainContainer = document.getElementById('main');
      
      // Prüfe ob Element vorhanden ist UND ob der Text bereits geladen ist
      // Für neue Einträge: Warte bis der Text wirklich vorhanden ist
      // WICHTIG: Verwende elementToCheck statt paraElement für Text-Länge-Prüfung
      if (elementToCheck && elementToCheck.textContent && elementToCheck.textContent.length > 0 && mainContainer) {
        // Prüfe ob die Offsets innerhalb des Textes liegen
        // WICHTIG: Verwende elementToCheck.textContent, nicht paraElement.textContent
        const paraText = elementToCheck.textContent || elementToCheck.innerText || '';
        console.log('[MB-SCROLL] tryScroll: Text-Länge:', paraText.length, 'Offset:', textStartOffset, 'Element:', elementToCheck.tagName);
        
        // Wenn Offset 0 ist, scrolle direkt zum Absatz (da Offset 0 am Anfang des Textes ist)
        if (textStartOffset === 0) {
          // Scrolle direkt zum Absatz - positioniere im oberen Viertel des Main Viewers
          // Verwende elementToCheck für Scroll-Position, aber paraElement für Position falls es sichtbar ist
          const scrollElement = (elementToCheck !== paraElement && paraElement) ? paraElement : elementToCheck;
          const paraRect = scrollElement.getBoundingClientRect();
          const mainRect = mainContainer.getBoundingClientRect();
          const header = document.getElementById('viewer-header');
          const headerHeight = header ? header.offsetHeight + 5 : 5;
          
          // Berechne Position im oberen Viertel des sichtbaren Bereichs
          const viewportHeight = mainRect.height - headerHeight;
          const upperQuarterOffset = Math.round(viewportHeight * 0.02); // 2% vom oberen Rand = knapp unter Header
          
          const relativeTop = paraRect.top - mainRect.top + mainContainer.scrollTop - headerHeight - upperQuarterOffset;
          mainContainer.scrollTop = Math.max(0, relativeTop);
          
          console.log('[MB-SCROLL] Scrolle zum Absatz - Position im oberen Viertel');
          
          // Markiere als ausgeführt - KEINE Verifizierung mehr, um doppeltes Springen zu verhindern
          scrollExecuted = true;
          
          // Markiere Suchwort im Absatz (falls vorhanden)
          if (searchTerm && searchTerm.trim()) {
            setTimeout(() => {
              markSearchTermInParagraph(elementToCheck, searchTerm);
            }, 100);
          }
        } else if (textStartOffset > 0 && textStartOffset <= paraText.length) {
          // Element ist bereit, scrolle zur Textposition
          // WICHTIG: scrollToTextPositionInParagraph hat bereits eine Verifizierung - keine doppelte Verifizierung mehr
          scrollToTextPositionInParagraph(targetIndex, textStartOffset, textEndOffset, shouldHighlightParagraph, null, searchTerm);
          
          // Markiere als ausgeführt
          scrollExecuted = true;
        } else {
          // Offsets außerhalb des Textes - versuche es trotzdem mit dem Absatz
          console.warn('[MB-SCROLL] Offsets außerhalb des Textes:', textStartOffset, 'vs', paraText.length, 'Element:', elementToCheck.tagName);
          if (attempts < maxAttempts) {
            // Versuche es nochmal, vielleicht wird der Text noch geladen
            // Erhöhe Delay bei späteren Versuchen für robustere Navigation
            const delay = Math.min(100 + (attempts * 10), 300);
            setTimeout(() => requestAnimationFrame(tryScroll), delay);
          } else {
            // Nach maxAttempts Versuchen immer noch nicht erfolgreich - verwende scrollToTextPositionInParagraph direkt
            console.log('[MB-SCROLL] Max Versuche erreicht, verwende scrollToTextPositionInParagraph direkt');
            scrollToTextPositionInParagraph(targetIndex, textStartOffset, textEndOffset, shouldHighlightParagraph, null, searchTerm);
            scrollExecuted = true;
          }
        }
      } else if (attempts < maxAttempts) {
        // Element noch nicht bereit, versuche es erneut
        // Erhöhe Delay bei späteren Versuchen für robustere Navigation
        const delay = Math.min(50 + (attempts * 5), 200);
        setTimeout(() => requestAnimationFrame(tryScroll), delay);
      } else {
        // Max Versuche erreicht - Fallback: Scrolle zum Absatz
        console.warn('[MB-SCROLL] Max Versuche erreicht, scrolle zum Absatz');
        const { paraElement } = findParagraphElementRobust(targetIndex);
        const mainContainer = document.getElementById('main');
        if (paraElement && mainContainer) {
          const paraRect = paraElement.getBoundingClientRect();
          const mainRect = mainContainer.getBoundingClientRect();
          const header = document.getElementById('viewer-header');
          const headerHeight = header ? header.offsetHeight + 5 : 5;
          
          // Berechne Position im oberen Viertel des sichtbaren Bereichs
          const viewportHeight = mainRect.height - headerHeight;
          const upperQuarterOffset = Math.round(viewportHeight * 0.02); // 2% vom oberen Rand = knapp unter Header
          
          const relativeTop = paraRect.top - mainRect.top + mainContainer.scrollTop - headerHeight - upperQuarterOffset;
          mainContainer.scrollTop = Math.max(0, relativeTop);
          
          // Markiere Suchwort im Absatz (falls vorhanden)
          if (searchTerm && searchTerm.trim()) {
            setTimeout(() => {
              markSearchTermInParagraph(paraElement, searchTerm);
            }, 100);
          }
        }
      }
    };
    
    // Starte den ersten Versuch nach kurzer Verzögerung, damit der DOM bereit ist
    // Für neue Einträge: Warte etwas länger, damit der Text vollständig geladen ist
    setTimeout(() => {
      requestAnimationFrame(tryScroll);
    }, 300); // Erhöht für robustere Navigation
    } else {
      // Keine Offsets vorhanden - scrolle zum Absatz (für ältere Einträge ohne Offsets)
      let attempts = 0;
      const maxAttempts = 50; // Erhöht für robustere Navigation
      
      const tryScrollToParagraph = () => {
        attempts++;
        
        // Verwende robuste Element-Suche
        const { paraElement } = findParagraphElementRobust(targetIndex);
        const mainContainer = document.getElementById('main');
        
        if (paraElement && mainContainer) {
          const paraRect = paraElement.getBoundingClientRect();
          const mainRect = mainContainer.getBoundingClientRect();
          const header = document.getElementById('viewer-header');
          const headerHeight = header ? header.offsetHeight + 5 : 5;
          
          // Berechne Position im oberen Viertel des sichtbaren Bereichs
          const viewportHeight = mainRect.height - headerHeight;
          const upperQuarterOffset = Math.round(viewportHeight * 0.02); // 2% vom oberen Rand = knapp unter Header
          
          const relativeTop = paraRect.top - mainRect.top + mainContainer.scrollTop - headerHeight - upperQuarterOffset;
          mainContainer.scrollTop = Math.max(0, relativeTop);
          
          console.log('[MB-SCROLL] Scrolle zum Absatz (ohne Offset) - Position im oberen Viertel');
          
          // Markiere Suchwort im Absatz (falls vorhanden)
          if (searchTerm && searchTerm.trim()) {
            setTimeout(() => {
              markSearchTermInParagraph(paraElement, searchTerm);
            }, 100);
          }
          
          // KEINE zusätzliche Verifizierung mehr - verursacht Springen
        } else if (attempts < maxAttempts) {
          // Erhöhe Delay bei späteren Versuchen für robustere Navigation
          const delay = Math.min(50 + (attempts * 5), 200);
          setTimeout(() => requestAnimationFrame(tryScrollToParagraph), delay);
        }
      };
      
      setTimeout(() => {
        requestAnimationFrame(tryScrollToParagraph);
      }, 300); // Erhöht für robustere Navigation
    }
  }
  
  // Warte kurz, damit displayBook/showLecture fertig ist
  // Der MutationObserver stellt den Content automatisch wieder her, wenn er überschrieben wird
  await new Promise(resolve => setTimeout(resolve, 150));
  
  // WICHTIG: Stelle sicher, dass membersPanelActive während der Navigation TRUE bleibt
  // (verhindert, dass das Panel geschlossen wird)
  if (window.membersNavigating) {
    membersPanelActive = true;
  }
  
  // Stelle sicher, dass Panel-Eigenschaften erhalten bleiben
  const currentSummaryPanel = document.getElementById('summary-panel');
  if (currentSummaryPanel) {
    currentSummaryPanel.style.width = mbWidth + 'px';
    currentSummaryPanel.style.minWidth = mbWidth + 'px';
    currentSummaryPanel.classList.add('visible');
    currentSummaryPanel.style.display = 'block';
    currentSummaryPanel.style.opacity = '1';
    currentSummaryPanel.style.visibility = 'visible';
    document.body.classList.remove('summary-panel-collapsed');
  }
  
  // Stelle sicher, dass Content sichtbar bleibt und Members-Panel-Content angezeigt wird
  const currentSummaryContent = document.getElementById('summary-content');
  if (currentSummaryContent) {
    currentSummaryContent.style.display = 'block';
    currentSummaryContent.style.opacity = '1';
    currentSummaryContent.style.visibility = 'visible';
    currentSummaryContent.classList.add('has-members-panel');
    
    // WICHTIG: Stelle sicher, dass der Members-Content nicht durch TOC ersetzt wird
    // Prüfe ob der Content noch Members-Content ist (nicht TOC)
    const hasMembersContent = currentSummaryContent.querySelector('#members-tab-content') || 
                              currentSummaryContent.querySelector('.members-login-form') ||
                              currentSummaryContent.querySelector('.member-item');
    
    if (!hasMembersContent && membersPanelActive) {
      // Content wurde überschrieben - versuche zuerst gespeicherten Content wiederherzustellen
      const contentToRestoreHere = window.savedMembersContentForRestore || savedContentForRestore;
      if (contentToRestoreHere && contentToRestoreHere.trim().length > 0) {
        console.log('[MB-NAVIGATION] Stelle gespeicherten Content wieder her');
        currentSummaryContent.innerHTML = contentToRestoreHere;
        
        // Prüfe nach kurzer Verzögerung erneut
        setTimeout(() => {
          const hasContentAfterRestore = currentSummaryContent.querySelector('#members-tab-content') || 
                                        currentSummaryContent.querySelector('.members-login-form') ||
                                        currentSummaryContent.querySelector('.member-item');
          
          if (!hasContentAfterRestore && membersPanelActive) {
            // Content konnte nicht wiederhergestellt werden - lade neu
            console.warn('[MB-NAVIGATION] Content konnte nicht wiederhergestellt werden, lade neu');
            if (typeof loadMembersTab === 'function') {
              loadMembersTab(currentMembersTab || 'highlights');
            }
          }
        }, 100);
      } else {
        // Kein gespeicherter Content vorhanden - lade neu
        console.warn('[MB-NAVIGATION] Kein gespeicherter Content vorhanden, lade neu');
        if (typeof loadMembersTab === 'function') {
          loadMembersTab(currentMembersTab || 'highlights');
        }
      }
    }
  }
  
  // Stelle Scroll-Position einmalig wieder her (nach kurzer Verzögerung, damit DOM bereit ist)
  setTimeout(() => {
    restoreMembersScrollPosition();
    // Starte Scroll-Position-Schutz wieder (für zukünftige Änderungen)
    startScrollPositionProtection();
  }, 50);
  
  // Stelle Panel-Eigenschaften sicher (nochmal, falls sie überschrieben wurden)
  if (currentSummaryPanel) {
    currentSummaryPanel.style.width = mbWidth + 'px';
    currentSummaryPanel.style.minWidth = mbWidth + 'px';
    currentSummaryPanel.classList.add('visible');
    currentSummaryPanel.style.display = 'block';
    currentSummaryPanel.style.opacity = '1';
    currentSummaryPanel.style.visibility = 'visible';
    document.body.classList.remove('summary-panel-collapsed');
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
    
    // WICHTIG: KEINE zusätzliche Scroll-Operation mehr hier!
    // Das Scrollen wird bereits durch scrollToTextPositionInParagraph beim ersten Aufruf erledigt.
    // Eine zusätzliche Scroll-Operation würde das Springen verursachen.
  }, 50);
  
  // Lade GA-Übersicht im linken Panel (nur für Vorträge, nicht für Bücher)
  if (!isBook && gaNumber && typeof loadGAOverviewInSidePanelOnly === 'function') {
    await loadGAOverviewInSidePanelOnly(gaNumber);
  }
  
  // Cleanup
  // WICHTIG: membersNavigating wurde bereits nach showLecture/displayBook zurückgesetzt
  // Hier nur noch finale Aufräumarbeiten
  setTimeout(() => {
    // WICHTIG: Stelle sicher, dass Panel noch offen ist, BEVOR wir membersNavigating zurücksetzen
    // (verhindert, dass andere Code-Pfade das Panel schließen)
    if (membersPanelActive) {
      const finalSummaryPanel = document.getElementById('summary-panel');
      if (finalSummaryPanel) {
        finalSummaryPanel.style.width = mbWidth + 'px';
        finalSummaryPanel.style.minWidth = mbWidth + 'px';
        finalSummaryPanel.classList.add('visible');
        finalSummaryPanel.style.display = 'block';
        finalSummaryPanel.style.opacity = '1';
        finalSummaryPanel.style.visibility = 'visible';
        document.body.classList.remove('summary-panel-collapsed');
      }
    }
    
    // Stelle sicher, dass membersNavigating false ist (falls es noch nicht zurückgesetzt wurde)
    // ABER: Nur wenn Panel noch aktiv ist (sonst könnte es geschlossen werden)
    if (membersPanelActive) {
      window.membersNavigating = false;
      document.body.classList.remove('members-navigating');
    }
    
    // Entferne Absatz-Markierungen IMMER (auch für Zitate - nur exakter Text wird markiert)
    const allHighlighted = document.querySelectorAll('.highlighted-paragraph');
    allHighlighted.forEach(el => {
      el.classList.remove('highlighted-paragraph');
    });
    
    // Stoppe MutationObserver
    setTimeout(() => {
      if (highlightObserver) {
        highlightObserver.disconnect();
        highlightObserver = null;
      }
      if (window.membersHighlightObserver) {
        window.membersHighlightObserver.disconnect();
        window.membersHighlightObserver = null;
      }
    }, 1000);
    
    // Stoppe Content-Restore Observer (KEINE innerHTML-Setter-Wiederherstellung mehr)
    if (contentRestoreObserver) {
      contentRestoreObserver.disconnect();
      contentRestoreObserver = null;
    }
    
    // Stoppe Panel-Visibility Observer
    if (window.panelVisibilityObserver) {
      window.panelVisibilityObserver.disconnect();
      window.panelVisibilityObserver = null;
    }
    
    // Stoppe Width-Check Interval
    if (window.panelWidthCheckInterval) {
      clearInterval(window.panelWidthCheckInterval);
      window.panelWidthCheckInterval = null;
    }
    
    // Stelle CSS-Transition wieder her (nur wenn Panel noch aktiv ist)
    const finalSummaryPanelForTransition = document.getElementById('summary-panel');
    if (finalSummaryPanelForTransition && membersPanelActive) {
      // Transition bleibt deaktiviert, solange Panel aktiv ist
      // Wird erst wiederhergestellt, wenn Panel geschlossen wird
    }
    
    // Stelle buildTableOfContents wieder her - aber nur wenn Members Panel nicht mehr aktiv ist
    // WICHTIG: Wenn Members Panel noch aktiv ist, behalte die Blockierung bei
    if (membersPanelActive) {
      // Panel ist noch aktiv - behalte Blockierung bei
      console.log('[MB-NAVIGATION] buildTableOfContents bleibt blockiert - Members Panel ist noch aktiv');
    } else {
      // Panel ist nicht mehr aktiv - stelle originale Funktion wieder her
      const funcToRestore = originalBuildTOC || window.originalBuildTOC;
      if (funcToRestore) {
        window.buildTableOfContents = funcToRestore;
        console.log('[MB-NAVIGATION] buildTableOfContents wiederhergestellt');
      }
    }
    
    // WICHTIG: Stelle sicher, dass Panel noch offen ist und Members-Content angezeigt wird
    const finalSummaryPanel = document.getElementById('summary-panel');
    const finalSummaryContent = document.getElementById('summary-content');
    
    if (finalSummaryPanel && membersPanelActive) {
      // Stelle sicher, dass Panel offen ist
      finalSummaryPanel.style.width = mbWidth + 'px';
      finalSummaryPanel.style.minWidth = mbWidth + 'px';
      finalSummaryPanel.classList.add('visible');
      finalSummaryPanel.classList.add('has-members-panel');
      finalSummaryPanel.style.display = 'block';
      finalSummaryPanel.style.opacity = '1';
      finalSummaryPanel.style.visibility = 'visible';
      document.body.classList.remove('summary-panel-collapsed');
      
      // Stelle sicher, dass Content Members-Content ist (nicht TOC)
      if (finalSummaryContent) {
        finalSummaryContent.classList.add('has-members-panel');
        const hasMembersContent = finalSummaryContent.querySelector('#members-tab-content') || 
                                  finalSummaryContent.querySelector('.members-login-form') ||
                                  finalSummaryContent.querySelector('.member-item');
        
        if (!hasMembersContent) {
          // Content wurde durch TOC ersetzt - versuche zuerst gespeicherten Content wiederherzustellen
          const contentToRestoreFinal = window.savedMembersContentForRestore || savedContentForRestore;
          if (contentToRestoreFinal && contentToRestoreFinal.trim().length > 0) {
            console.log('[MB-NAVIGATION] Stelle gespeicherten Content wieder her (finale Prüfung)');
            finalSummaryContent.innerHTML = contentToRestoreFinal;
            
            // Prüfe nach kurzer Verzögerung erneut
            setTimeout(() => {
              const hasContentAfterFinalRestore = finalSummaryContent.querySelector('#members-tab-content') || 
                                                  finalSummaryContent.querySelector('.members-login-form') ||
                                                  finalSummaryContent.querySelector('.member-item');
              
              if (!hasContentAfterFinalRestore && membersPanelActive) {
                // Content konnte nicht wiederhergestellt werden - lade neu
                console.warn('[MB-NAVIGATION] Content konnte nicht wiederhergestellt werden (finale Prüfung), lade neu');
                if (typeof loadMembersTab === 'function') {
                  loadMembersTab(currentMembersTab || 'highlights');
                }
              }
            }, 100);
          } else {
            // Kein gespeicherter Content vorhanden - lade neu
            console.warn('[MB-NAVIGATION] Members-Content wurde durch TOC ersetzt, lade neu');
            if (typeof loadMembersTab === 'function') {
              loadMembersTab(currentMembersTab || 'highlights');
            }
          }
        }
      }
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
    
    // Scroll-Position wird bereits nach Content-Wiederherstellung wiederhergestellt
    // Keine doppelte Wiederherstellung hier, um Springen zu vermeiden
  }, 200);
}

/**
 * Scrollt zur Textposition innerhalb eines Absatzes
 * @param {boolean} shouldHighlight - Ob der Absatz markiert werden soll (nur für Zitate)
 */
/**
 * Markiert ein Suchwort in einem Absatz-Element (analog zu Suche/erweitert)
 * @param {HTMLElement} targetElement - Das Absatz-Element
 * @param {string} searchTerm - Das zu markierende Suchwort
 */
function markSearchTermInParagraph(targetElement, searchTerm) {
  if (!targetElement || !searchTerm || !searchTerm.trim()) {
    return;
  }
  
  const cleanTerm = searchTerm.trim();
  const isExactMatch = cleanTerm.startsWith('"') && cleanTerm.endsWith('"');
  const termToHighlight = isExactMatch ? cleanTerm.slice(1, -1) : cleanTerm;
  
  if (!termToHighlight) {
    return;
  }
  
  // Prüfe ob das Suchwort im Absatz-Text vorkommt (case-insensitive)
  const paragraphText = targetElement.textContent || targetElement.innerText || '';
  const flags = isExactMatch ? 'g' : 'gi';
  const testRegex = new RegExp(termToHighlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), flags);
  
  if (!testRegex.test(paragraphText)) {
    // Suchwort kommt nicht im Absatz vor - keine Markierung
    return;
  }
  
  // Suchwort kommt vor - markiere es NUR in Textknoten, nicht in HTML-Attributen!
  // Verwende TreeWalker um nur Textknoten zu markieren (verhindert Beschädigung von img-Tags)
  const escapedTerm = termToHighlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escapedTerm})`, flags);
  
  const walker = document.createTreeWalker(
    targetElement,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: function(node) {
        // Überspringe Textknoten die bereits in <mark> Tags sind
        let parent = node.parentNode;
        while (parent && parent !== targetElement) {
          if (parent.tagName && parent.tagName.toLowerCase() === 'mark') {
            return NodeFilter.FILTER_REJECT;
          }
          // Überspringe Textknoten innerhalb von img-Tags (Attributen)
          if (parent.tagName && parent.tagName.toLowerCase() === 'img') {
            return NodeFilter.FILTER_REJECT;
          }
          parent = parent.parentNode;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    },
    false
  );
  
  const textNodesToMark = [];
  let textNode;
  while (textNode = walker.nextNode()) {
    if (textNode.textContent.trim() && regex.test(textNode.textContent)) {
      textNodesToMark.push(textNode);
    }
  }
  
  // Markiere Suchwort in Textknoten
  textNodesToMark.forEach(textNode => {
    const text = textNode.textContent;
    const highlightedText = text.replace(regex, '<mark>$1</mark>');
    const tempSpan = document.createElement('span');
    tempSpan.innerHTML = highlightedText;
    
    const parent = textNode.parentNode;
    if (parent && parent.nodeType === Node.ELEMENT_NODE) {
      while (tempSpan.firstChild) {
        parent.insertBefore(tempSpan.firstChild, textNode);
      }
      parent.removeChild(textNode);
    }
  });
}

function scrollToTextPositionInParagraph(paragraphId, textStartOffset, textEndOffset = null, shouldHighlight = false, highlightId = null, searchTerm = null) {
  if (!paragraphId || textStartOffset === null || textStartOffset === undefined) {
    console.warn('[MB-SCROLL] Ungültige Parameter:', { paragraphId, textStartOffset, textEndOffset });
    return;
  }
  
  const mainContainer = document.getElementById('main');
  if (!mainContainer) {
    console.warn('[MB-SCROLL] Main Container nicht gefunden');
    return;
  }
  
  // WICHTIG: Versuche zuerst, das Highlight-Element direkt zu finden (falls es bereits im DOM ist)
  // Das ist genauer als die Berechnung aus dem Offset
  if (highlightId) {
    const highlightElement = document.querySelector(`[data-highlight-id="${highlightId}"]`);
    if (highlightElement) {
      console.log('[MB-SCROLL] Highlight-Element direkt gefunden, scrolle dazu');
      const highlightRect = highlightElement.getBoundingClientRect();
      const mainRect = mainContainer.getBoundingClientRect();
      const header = document.getElementById('viewer-header');
      const headerHeight = header ? header.offsetHeight + 5 : 5;
      
      // Berechne Position im oberen Viertel des sichtbaren Bereichs
      const viewportHeight = mainRect.height - headerHeight;
      const upperQuarterOffset = Math.round(viewportHeight * 0.02); // 2% vom oberen Rand = knapp unter Header
      
      const currentScrollTop = mainContainer.scrollTop;
      const highlightTopRelativeToViewport = highlightRect.top - mainRect.top;
      const targetScrollTop = currentScrollTop + highlightTopRelativeToViewport - headerHeight - upperQuarterOffset;
      
      mainContainer.scrollTop = Math.max(0, targetScrollTop);
      console.log('[MB-SCROLL] Direkt zu Highlight-Element gescrollt (knapp unter Header), scrollTop:', mainContainer.scrollTop);
      return;
    }
  }
  
  // Bereinige paragraphId (entferne 'para-' Präfix falls vorhanden)
  const cleanIndex = paragraphId.toString().replace(/^para-/, '').replace(/^\^/, '');
  let paraElement = document.getElementById(`para-${cleanIndex}`);
  
  // Falls nicht gefunden, versuche auch ohne 'para-' Präfix (für IDs wie 'wxa77q')
  if (!paraElement && !cleanIndex.startsWith('para-')) {
    paraElement = document.getElementById(`para-${cleanIndex}`);
  }
  
  // Falls immer noch nicht gefunden, versuche direkt mit der ID
  if (!paraElement) {
    paraElement = document.getElementById(cleanIndex);
  }
  
  // Für Bücher: Falls paraElement ein verstecktes span ist, finde das Parent-Element
  let targetElement = paraElement;
  if (paraElement && (paraElement.style.display === 'none' || paraElement.tagName.toLowerCase() === 'span')) {
    // Für Bücher: Suche nach dem Parent-Element, das den Text enthält
    let parent = paraElement.parentElement;
    while (parent && parent !== document.body) {
      const tagName = parent.tagName.toLowerCase();
      if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
        targetElement = parent;
        break;
      }
      parent = parent.parentElement;
    }
  }
  
  if (!paraElement) {
    console.warn('[MB-SCROLL] Absatz nicht gefunden:', cleanIndex, '- versuche erneut nach kurzer Zeit');
    // Versuche erneut nach kurzer Zeit (falls DOM noch nicht bereit ist)
    setTimeout(() => {
      scrollToTextPositionInParagraph(paragraphId, textStartOffset, textEndOffset, shouldHighlight, highlightId, searchTerm);
    }, 200);
    return;
  }
  
  // Für Bücher: Falls paraElement ein verstecktes span ist, finde das Parent-Element
  let elementToScroll = paraElement;
  if (paraElement && (paraElement.style.display === 'none' || paraElement.tagName.toLowerCase() === 'span')) {
    // Für Bücher: Suche nach dem Parent-Element, das den Text enthält
    let parent = paraElement.parentElement;
    while (parent && parent !== document.body) {
      const tagName = parent.tagName.toLowerCase();
      if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
        elementToScroll = parent;
        break;
      }
      parent = parent.parentElement;
    }
  }
  
  // WICHTIG: Markiere nur den exakten Zitat-Text (nicht den ganzen Absatz)
  // Analog zu Unterstreichungen: dauerhaft, aber nur beim Klick angezeigt
  if (shouldHighlight) {
    if (textStartOffset !== null && textEndOffset !== null) {
      // Exakte Textmarkierung für Zitate mit Offsets
      // Finde das Zitat im Cache ODER erstelle ein temporäres Objekt
      let quote = null;
      if (cachedQuotesData && cachedQuotesData.success && cachedQuotesData.data) {
        quote = cachedQuotesData.data.find(q => 
          q.paragraph_id === paragraphId &&
          q.text_start_offset === textStartOffset &&
          q.text_end_offset === textEndOffset
        );
      }
      
      // WICHTIG: Falls nicht im Cache, erstelle temporäres Objekt mit Text aus Element
      if (!quote && elementToScroll.textContent) {
        quote = {
          id: `temp-scroll-${Date.now()}`,
          paragraph_id: paragraphId,
          text_start_offset: textStartOffset,
          text_end_offset: textEndOffset,
          quote_text: elementToScroll.textContent.substring(textStartOffset, textEndOffset)
        };
      }
      
      if (quote && typeof applyQuoteHighlightToElement === 'function') {
        setTimeout(() => {
          applyQuoteHighlightToElement(elementToScroll, quote);
        }, 100);
      }
    }
    // KEIN Fallback mehr - Absatz wird nicht mehr gehighlighted
  }
  
  // Erstelle temporäres Range-Element, um die Position zu finden
  // Verwende textContent für konsistente Berechnung
  // Für Bücher: Verwende targetElement, für Vorträge: paraElement
  const textContent = elementToScroll.textContent || elementToScroll.innerText || '';
  
  console.log('[MB-SCROLL] Paragraph:', cleanIndex, 'Text Länge:', textContent.length, 'Offset:', textStartOffset);
  
  // Wenn Offset 0 ist, scrolle direkt zum Absatz (am Anfang des Textes)
  if (textStartOffset === 0) {
    console.log('[MB-SCROLL] Offset ist 0, scrolle zum Absatz (knapp unter Header)');
    const mainRect = mainContainer.getBoundingClientRect();
    const elementRect = elementToScroll.getBoundingClientRect();
    const header = document.getElementById('viewer-header');
    const headerHeight = header ? header.offsetHeight + 5 : 5;
    
    // Berechne Position im oberen Viertel des sichtbaren Bereichs
    const viewportHeight = mainRect.height - headerHeight;
    const upperQuarterOffset = Math.round(viewportHeight * 0.02); // 2% vom oberen Rand = knapp unter Header
    
    const relativeTop = elementRect.top - mainRect.top + mainContainer.scrollTop - headerHeight - upperQuarterOffset;
    mainContainer.scrollTop = Math.max(0, relativeTop);
    
    // Markiere Suchwort im Absatz (falls vorhanden)
    if (searchTerm && searchTerm.trim()) {
      setTimeout(() => {
        markSearchTermInParagraph(elementToScroll, searchTerm);
      }, 100);
    }
    
    // KEINE Verifizierung mehr - verursacht Springen
    return;
  }
  
  if (textStartOffset >= textContent.length) {
    // Falls Offset außerhalb des Textes liegt, scrolle einfach zum Absatz
    console.warn('[MB-SCROLL] Offset außerhalb des Textes, scrolle zum Absatz (knapp unter Header)');
    const mainRect = mainContainer.getBoundingClientRect();
    const elementRect = elementToScroll.getBoundingClientRect();
    const header = document.getElementById('viewer-header');
    const headerHeight = header ? header.offsetHeight + 5 : 5;
    
    // Berechne Position im oberen Viertel des sichtbaren Bereichs
    const viewportHeight = mainRect.height - headerHeight;
    const upperQuarterOffset = Math.round(viewportHeight * 0.02); // 2% vom oberen Rand = knapp unter Header
    
    const relativeTop = elementRect.top - mainRect.top + mainContainer.scrollTop - headerHeight - upperQuarterOffset;
    mainContainer.scrollTop = Math.max(0, relativeTop);
    
    // Markiere Suchwort im Absatz (falls vorhanden)
    if (searchTerm && searchTerm.trim()) {
      setTimeout(() => {
        markSearchTermInParagraph(elementToScroll, searchTerm);
      }, 100);
    }
    
    return;
  }
  
  // Für neue Einträge: Stelle sicher, dass der Text wirklich geladen ist
  if (textContent.length === 0) {
    console.warn('[MB-SCROLL] Text noch nicht geladen, versuche später erneut');
    setTimeout(() => {
      scrollToTextPositionInParagraph(paragraphId, textStartOffset, textEndOffset, shouldHighlight, highlightId, searchTerm);
    }, 100);
    return;
  }
  
  // WICHTIG: Versuche zuerst, ein Highlight-Element im Absatz zu finden (falls vorhanden)
  // Das ist genauer als die Berechnung aus dem Offset
  // Suche sowohl mit highlightId als auch ohne (falls highlightId nicht übergeben wurde)
  const highlightElements = elementToScroll.querySelectorAll('[data-highlight-id]');
  console.log('[MB-SCROLL] Gefundene Highlight-Elemente im Absatz:', highlightElements.length, 'highlightId:', highlightId);
  
  for (const highlightEl of highlightElements) {
      // Wenn highlightId übergeben wurde, prüfe ob es passt
      if (highlightId && highlightEl.getAttribute('data-highlight-id') === String(highlightId)) {
        console.log('[MB-SCROLL] Highlight-Element mit passender ID gefunden, scrolle dazu (knapp unter Header)');
        const highlightRect = highlightEl.getBoundingClientRect();
        const mainRect = mainContainer.getBoundingClientRect();
        const header = document.getElementById('viewer-header');
        const headerHeight = header ? header.offsetHeight + 5 : 5;
        
        // Berechne Position im oberen Viertel des sichtbaren Bereichs
        const viewportHeight = mainRect.height - headerHeight;
        const upperQuarterOffset = Math.round(viewportHeight * 0.02); // 2% vom oberen Rand = knapp unter Header
        
        const currentScrollTop = mainContainer.scrollTop;
        const highlightTopRelativeToViewport = highlightRect.top - mainRect.top;
        const targetScrollTop = currentScrollTop + highlightTopRelativeToViewport - headerHeight - upperQuarterOffset;
        
        mainContainer.scrollTop = Math.max(0, targetScrollTop);
        console.log('[MB-SCROLL] Zu Highlight-Element gescrollt (mit ID, knapp unter Header), scrollTop:', mainContainer.scrollTop);
        
        // Markiere Suchwort im Absatz (falls vorhanden)
        if (searchTerm && searchTerm.trim()) {
          setTimeout(() => {
            markSearchTermInParagraph(elementToScroll, searchTerm);
          }, 100);
        }
        
        return;
      }
    
    // Wenn kein highlightId übergeben wurde, prüfe ob das Highlight-Element in der Nähe des Offsets liegt
    if (!highlightId) {
      const highlightText = highlightEl.textContent || '';
      const highlightParent = highlightEl.closest('p, div, h1, h2, h3, h4, h5, h6, li, blockquote') || elementToScroll;
      const parentText = highlightParent.textContent || '';
      const highlightStartInParent = parentText.indexOf(highlightText);
      
      // Wenn das Highlight in der Nähe des Offsets liegt (Toleranz: ±50 Zeichen)
      if (Math.abs(highlightStartInParent - textStartOffset) < 50) {
        console.log('[MB-SCROLL] Passendes Highlight-Element gefunden (nach Offset), scrolle dazu (knapp unter Header)');
        const highlightRect = highlightEl.getBoundingClientRect();
        const mainRect = mainContainer.getBoundingClientRect();
        const header = document.getElementById('viewer-header');
        const headerHeight = header ? header.offsetHeight + 5 : 5;
        
        // Berechne Position im oberen Viertel des sichtbaren Bereichs
        const viewportHeight = mainRect.height - headerHeight;
        const upperQuarterOffset = Math.round(viewportHeight * 0.02); // 2% vom oberen Rand = knapp unter Header
        
        const currentScrollTop = mainContainer.scrollTop;
        const highlightTopRelativeToViewport = highlightRect.top - mainRect.top;
        const targetScrollTop = currentScrollTop + highlightTopRelativeToViewport - headerHeight - upperQuarterOffset;
        
        mainContainer.scrollTop = Math.max(0, targetScrollTop);
        console.log('[MB-SCROLL] Zu Highlight-Element gescrollt (nach Offset, knapp unter Header), scrollTop:', mainContainer.scrollTop);
        
        // Markiere Suchwort im Absatz (falls vorhanden)
        if (searchTerm && searchTerm.trim()) {
          setTimeout(() => {
            markSearchTermInParagraph(elementToScroll, searchTerm);
          }, 100);
        }
        
        return;
      }
    }
  }
  
  // Erstelle einen temporären Range, um die Position zu berechnen
  // Für Bücher: Verwende targetElement, für Vorträge: paraElement
  const range = document.createRange();
  const walker = document.createTreeWalker(
    elementToScroll,
    NodeFilter.SHOW_TEXT,
    null,
    false
  );
  
  let currentOffset = 0;
  let targetNode = null;
  let targetOffset = 0;
  
  let node;
  while (node = walker.nextNode()) {
    const nodeLength = node.textContent.length;
    if (currentOffset + nodeLength >= textStartOffset) {
      targetNode = node;
      targetOffset = textStartOffset - currentOffset;
      break;
    }
    currentOffset += nodeLength;
  }
  
  if (!targetNode) {
    // Fallback: Scrolle zum Absatz (z.B. wenn Offset 0 ist oder Text-Node nicht gefunden wird)
    console.warn('[MB-SCROLL] Text-Node nicht gefunden für Offset', textStartOffset, '- scrolle zum Absatz');
    const mainRect = mainContainer.getBoundingClientRect();
    const paraRect = paraElement.getBoundingClientRect();
    const header = document.getElementById('viewer-header');
    const headerHeight = header ? header.offsetHeight + 5 : 5;
    
    // Berechne Position im oberen Viertel des sichtbaren Bereichs
    const viewportHeight = mainRect.height - headerHeight;
    const upperQuarterOffset = Math.round(viewportHeight * 0.02); // 2% vom oberen Rand = knapp unter Header
    
    const relativeTop = paraRect.top - mainRect.top + mainContainer.scrollTop - headerHeight - upperQuarterOffset;
    mainContainer.scrollTop = Math.max(0, relativeTop);
    
    // Markiere Suchwort im Absatz (falls vorhanden)
    if (searchTerm && searchTerm.trim()) {
      setTimeout(() => {
        markSearchTermInParagraph(elementToScroll, searchTerm);
      }, 100);
    }
    
    // KEINE Verifizierung mehr - verursacht Springen
    return;
  }
  
  // Setze Range auf die Zielposition
  try {
    range.setStart(targetNode, Math.min(targetOffset, targetNode.textContent.length));
    range.setEnd(targetNode, Math.min(targetOffset, targetNode.textContent.length));
    
    // Berechne die Position relativ zum Main Container
    const rangeRect = range.getBoundingClientRect();
    const mainRect = mainContainer.getBoundingClientRect();
    const header = document.getElementById('viewer-header');
    const headerHeight = header ? header.offsetHeight + 5 : 5;
    
    // Berechne Position im oberen Viertel des sichtbaren Bereichs
    const viewportHeight = mainRect.height - headerHeight;
    const upperQuarterOffset = Math.round(viewportHeight * 0.02); // 2% vom oberen Rand = knapp unter Header
    
    const currentScrollTop = mainContainer.scrollTop;
    const rangeTopRelativeToViewport = rangeRect.top - mainRect.top;
    const targetScrollTop = currentScrollTop + rangeTopRelativeToViewport - headerHeight - upperQuarterOffset;
    
    console.log('[MB-SCROLL] Scroll-Berechnung (knapp unter Header):', {
      currentScrollTop,
      rangeTopRelativeToViewport,
      headerHeight,
      upperQuarterOffset,
      targetScrollTop
    });
    
    // Scroll sofort zur Position (ohne Animation für sofortiges Scrollen)
    mainContainer.scrollTop = Math.max(0, targetScrollTop);
    
    // Markiere Suchwort im Absatz (falls vorhanden)
    if (searchTerm && searchTerm.trim()) {
      setTimeout(() => {
        markSearchTermInParagraph(elementToScroll, searchTerm);
      }, 100);
    }
    
    // WICHTIG: KEINE Verifizierung mehr - verursacht das Springen!
    // Die Position ist bereits korrekt gesetzt, eine Verifizierung würde sie nur überschreiben.
  } catch (error) {
    console.warn('[MB-SCROLL] Fehler beim Scrollen zur Textposition:', error);
    // Fallback: Scrolle zum Absatz (knapp unter Header)
    const mainRect = mainContainer.getBoundingClientRect();
    const paraRect = paraElement.getBoundingClientRect();
    const header = document.getElementById('viewer-header');
    const headerHeight = header ? header.offsetHeight + 5 : 5;
    
    // Berechne Position im oberen Viertel des sichtbaren Bereichs
    const viewportHeight = mainRect.height - headerHeight;
    const upperQuarterOffset = Math.round(viewportHeight * 0.02); // 2% vom oberen Rand = knapp unter Header
    
    const relativeTop = paraRect.top - mainRect.top + mainContainer.scrollTop - headerHeight - upperQuarterOffset;
    mainContainer.scrollTop = Math.max(0, relativeTop);
    
    // Markiere Suchwort im Absatz (falls vorhanden)
    if (searchTerm && searchTerm.trim()) {
      setTimeout(() => {
        markSearchTermInParagraph(elementToScroll, searchTerm);
      }, 100);
    }
  }
}

/**
 * Notes Tab
 */
async function loadNotesTab(container) {
  // Lade alle Keywords aus Notes, Quotes und Highlights für das Dropdown
  updateKeywordFilterDropdownWithAllKeywords();
  
  // Lade Notizen für GA-Dropdown
  const notesResult = await getNotes();
  if (notesResult.success && notesResult.data) {
    // Sammle alle GA-Nummern aus Notizen
    const gaNumbers = [];
    notesResult.data.forEach(note => {
      if (note.ga_references && Array.isArray(note.ga_references)) {
        note.ga_references.forEach(ga => gaNumbers.push(ga));
      }
    });
    updateGAFilterDropdown(gaNumbers);
  }
  
  container.innerHTML = `
    <div class="notes-editor">
      <textarea id="members-note-content" placeholder="Schreiben Sie Ihre Notiz hier..."></textarea>
      <button class="primary-btn" onclick="saveMemberNote()">Notiz speichern</button>
      <div id="notes-list"></div>
    </div>
  `;
  
  loadSavedNotes();
}

async function loadSavedNotes() {
  const result = await getNotes();
  const list = document.getElementById('notes-list');
  
  // Falls das notes-list Element nicht existiert (z.B. bei gefilterter Ansicht), nichts tun
  if (!list) {
    console.log('[MB-NOTES] notes-list Element nicht gefunden, überspringe loadSavedNotes');
    return;
  }
  
  if (!result.success || result.data.length === 0) {
    list.innerHTML = '<div class="empty-state" style="margin-top: 1rem;">Noch keine Notizen</div>';
    return;
  }
  
  // Filtere nach GA-Nummer falls Filter aktiv
  let filteredNotes = result.data;
  if (selectedGAFilter) {
    filteredNotes = result.data.filter(note => {
      if (!note.ga_references || !Array.isArray(note.ga_references)) return false;
      return note.ga_references.some(ga => {
        const baseMatch = ga.match(/^(GA\d{3})/i);
        return baseMatch && baseMatch[1].toUpperCase() === selectedGAFilter.toUpperCase();
      });
    });
  }
  
  if (filteredNotes.length === 0) {
    list.innerHTML = `<div class="empty-state" style="margin-top: 1rem;">Keine Notizen${selectedGAFilter ? ` für ${selectedGAFilter}` : ''}</div>`;
    return;
  }
  
  const html = filteredNotes.map(note => {
    // Extrahiere erste GA-Referenz falls vorhanden
    const gaReference = note.ga_references && note.ga_references.length > 0 ? note.ga_references[0] : null;
    const paragraphId = note.paragraph_id || null;
    const textStartOffset = note.text_start_offset !== null && note.text_start_offset !== undefined ? note.text_start_offset : null;
    const textEndOffset = note.text_end_offset !== null && note.text_end_offset !== undefined ? note.text_end_offset : null;
    
    // Hole Vortragsdatum falls vorhanden
    const lectureDate = note.lecture_date ? formatLectureDate(note.lecture_date) : '';
    const dateDisplay = lectureDate ? `, ${lectureDate}` : '';
    
    // Hole Farbe der Notiz
    const noteColor = note.marker_color || 'blue';
    const noteColorHex = getNoteColor(noteColor);
    
    // Bereinige Text: Entferne Präfixe wie "Aus [[GA001]]:" oder "Aus [[GA001]] - Titel:"
    let cleanedContent = note.content;
    // Entferne "Aus [[GA...]]:" oder "Aus [[GA...]] - Titel:" am Anfang (mit optionalen Leerzeichen)
    cleanedContent = cleanedContent.replace(/^Aus\s*\[\[[^\]]+\]\]\s*[-:]\s*/i, '');
    // Entferne auch Varianten wie "Aus [[GA...]] - " oder "Aus [[GA...]]: "
    cleanedContent = cleanedContent.replace(/^Aus\s*\[\[[^\]]+\]\]\s*[-:]\s*/i, '');
    // Entferne führende Anführungszeichen und Leerzeichen
    cleanedContent = cleanedContent.replace(/^["']\s*/, '').trim();
    // Entferne auch mehrfache Leerzeichen am Anfang
    cleanedContent = cleanedContent.replace(/^\s+/, '');
    
    // Text auf zwei Zeilen begrenzen (ca. 150 Zeichen)
    const contentPreview = cleanedContent.substring(0, 150);
    const hasMore = cleanedContent.length > 150;
    
    // Prüfe ob Navigation möglich ist (mindestens GA-Referenz vorhanden)
    const canNavigate = gaReference !== null;
    
    return `
      <div class="member-item" data-id="${note.id}" data-type="note" oncontextmenu="event.preventDefault(); showNoteColorContextMenu(event.clientX, event.clientY, '${note.id}'); return false;">
        <div style="flex: 1;">
          <div class="member-item-header">
            <div style="display: flex; align-items: center; gap: 0.25rem;">
              ${canNavigate
                ? `<a href="#" onclick="saveMembersScrollPosition(); navigateToNoteFromMembersPanel('${note.id}', '${gaReference}', ${paragraphId ? `'${paragraphId}'` : 'null'}, ${textStartOffset !== null ? textStartOffset : 'null'}, ${textEndOffset !== null ? textEndOffset : 'null'}); return false;" style="display: inline-block; text-decoration: none; cursor: pointer;" title="Zur Textstelle springen">
                    <span class="note-bookmark-icon-header" style="display: inline-block; color: ${noteColorHex};">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                      </svg>
                    </span>
                  </a>`
                : `<span class="note-bookmark-icon-header" style="display: inline-block; color: ${noteColorHex};">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                    </svg>
                  </span>`
              }
              ${canNavigate
                ? `<strong><a href="#" onclick="saveMembersScrollPosition(); navigateToNoteFromMembersPanel('${note.id}', '${gaReference}', ${paragraphId ? `'${paragraphId}'` : 'null'}, ${textStartOffset !== null ? textStartOffset : 'null'}, ${textEndOffset !== null ? textEndOffset : 'null'}); return false;" style="color: var(--link-color); text-decoration: none;">${gaReference}${dateDisplay}</a></strong>`
                : `<strong>${gaReference || 'Notiz'}${dateDisplay}</strong>`
              }
            </div>
            <span class="member-item-date">${new Date(note.created_at).toLocaleDateString('de-DE')}</span>
          </div>
          ${canNavigate
            ? `<div class="member-item-quote"><a href="#" onclick="saveMembersScrollPosition(); navigateToNoteFromMembersPanel('${note.id}', '${gaReference}', ${paragraphId ? `'${paragraphId}'` : 'null'}, ${textStartOffset !== null ? textStartOffset : 'null'}, ${textEndOffset !== null ? textEndOffset : 'null'}); return false;" style="color: var(--text-color); text-decoration: none; cursor: pointer;" title="Zur Textstelle springen">"${contentPreview}${hasMore ? '...' : ''}"</a></div>`
            : `<div class="member-item-quote">"${contentPreview}${hasMore ? '...' : ''}"</div>`
          }
          ${note.tags && Array.isArray(note.tags) && note.tags.length > 0 ? `<div class="member-item-tags">${note.tags.map(tag => `<span class="tag clickable-tag" onclick="handleKeywordFilter('${tag.replace(/'/g, "\\'")}'); return false;" style="cursor: pointer;" title="Nach diesem Schlagwort filtern">#${tag}</span>`).join(' ')}</div>` : ''}
        </div>
        <div class="member-item-actions">
          <button class="edit-btn" onclick="editMemberNote('${note.id}')" title="Bearbeiten">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
          </button>
          <button class="delete-btn" onclick="deleteMemberNote('${note.id}')" title="Löschen">
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
    `;
  }).join('');
  
  list.innerHTML = html;
}

async function saveMemberNote() {
  const content = document.getElementById('members-note-content').value.trim();
  
  if (!content) {
    alert('Bitte Text eingeben');
    return;
  }
  
  // Öffne Dialog für Keywords
  const dialogResult = await showNoteKeywordsDialog(content);
  
  if (dialogResult === null) {
    // Benutzer hat abgebrochen
    return;
  }
  
  const { keywords, content: finalContent, color } = dialogResult;
  const tags = keywords
    .split(',')
    .map(kw => kw.trim())
    .filter(kw => kw.length > 0);
  // Verwende Farbe aus Kontextdaten (vom Context-Menü) falls vorhanden, sonst aus Dialog
  const markerColor = (window.noteContextData && window.noteContextData.color) || color || 'blue';
  
  // Entferne Präfix "Aus [[GA001]]:" falls vorhanden (soll nicht gespeichert werden)
  let contentWithTags = finalContent;
  contentWithTags = contentWithTags.replace(/^Aus\s*\[\[[^\]]+\]\]\s*[-:]\s*/i, '').trim();
  
  // Füge Tags als #tags am Ende des Contents hinzu, damit sie automatisch extrahiert werden
  if (tags.length > 0) {
    // Prüfe ob Tags bereits im Content vorhanden sind
    const existingTags = contentWithTags.match(/#(\w+)/g) || [];
    const existingTagNames = existingTags.map(t => t.substring(1).toLowerCase());
    
    // Füge nur neue Tags hinzu, die noch nicht vorhanden sind
    const newTags = tags.filter(tag => !existingTagNames.includes(tag.toLowerCase()));
    if (newTags.length > 0) {
      const tagsString = newTags.map(tag => `#${tag}`).join(' ');
      contentWithTags = contentWithTags.trim() + '\n\n' + tagsString;
    }
  }
  
  const title = contentWithTags.split('\n')[0].substring(0, 50);
  
  // Prüfe ob Kontext-Daten vorhanden sind (von Textauswahl)
  let paragraphId = null;
  let paragraphText = null;
  let textStartOffset = null;
  let textEndOffset = null;
  let lectureDate = null;
  
  if (window.noteContextData) {
    paragraphId = window.noteContextData.paragraphId;
    paragraphText = window.noteContextData.paragraphText;
    textStartOffset = window.noteContextData.textStartOffset;
    textEndOffset = window.noteContextData.textEndOffset;
    
    // Hole Vortragsdatum falls verfügbar
    if (window.noteContextData.lectureId && typeof getCurrentLectureDate === 'function') {
      lectureDate = getCurrentLectureDate(window.noteContextData.lectureId);
    }
    
    // Lösche Kontext-Daten nach Verwendung
    delete window.noteContextData;
  }
  
  // Erstelle Notiz - Tags werden automatisch aus dem Content extrahiert
  const result = await createNote(title, contentWithTags, false, paragraphId, paragraphText, textStartOffset, textEndOffset, lectureDate, tags.length > 0 ? tags : null, markerColor);
  
  if (result.success) {
    
    document.getElementById('members-note-content').value = '';
    await loadSavedNotes();
    // Aktualisiere MB falls offen und Notizen-Tab aktiv
    if (typeof membersPanelActive !== 'undefined' && membersPanelActive && currentMembersTab === 'notes') {
      // Notizen-Tab wird bereits durch loadSavedNotes() aktualisiert
      // Kein Cache für Notizen, daher keine Invalidierung nötig
    }
    alert('✓ Notiz gespeichert!');
  } else {
    alert('✗ Fehler beim Speichern');
  }
}

/**
 * Zeigt Dialog für Keywords beim Erstellen einer neuen Notiz
 */
function showNoteKeywordsDialog(content) {
  return new Promise((resolve) => {
    // Hole vorausgewählte Farbe aus Kontextdaten (vom Context-Menü)
    const preselectedColor = (window.noteContextData && window.noteContextData.color) || 'blue';
    
    // Erstelle Dialog
    const dialog = document.createElement('div');
    dialog.className = 'keyword-dialog-overlay';
    
    // Bereinige Content für Vorschau (entferne GA-Link-Präfix)
    let previewContent = content;
    previewContent = previewContent.replace(/^Aus\s*\[\[[^\]]+\]\]\s*[-:]\s*/i, '');
    previewContent = previewContent.replace(/^["']\s*/, '').trim();
    
    // Bestimme welcher Button vorausgewählt ist
    const isBlueSelected = preselectedColor === 'blue';
    const isRedSelected = preselectedColor === 'red';
    const isYellowSelected = preselectedColor === 'yellow';
    
    dialog.innerHTML = `
      <div class="keyword-dialog">
        <div class="keyword-dialog-header">
          <h3>Notiz speichern</h3>
        </div>
        <div class="keyword-dialog-body">
          <div class="keyword-preview">"${previewContent.substring(0, 100)}${previewContent.length > 100 ? '...' : ''}"</div>
          <label for="note-keyword-input">Keywords (optional, durch Komma getrennt):</label>
          <input type="text" id="note-keyword-input" value="" placeholder="z.B. Karma, Reinkarnation, Ätherleib" />
          <div class="keyword-hint">Keywords helfen beim späteren Filtern und Wiederfinden</div>
          <label style="margin-top: 0.75rem; display: block;">Farbe:</label>
          <div class="note-color-selection" style="display: flex; gap: 0.5rem; margin-top: 0.25rem;">
            <button type="button" class="note-color-btn ${isBlueSelected ? 'selected' : ''}" data-color="blue" style="width: 28px; height: 28px; border-radius: 50%; border: 2px solid ${isBlueSelected ? '#467886' : 'transparent'}; background-color: #467886; cursor: pointer;" title="Blau"></button>
            <button type="button" class="note-color-btn ${isRedSelected ? 'selected' : ''}" data-color="red" style="width: 28px; height: 28px; border-radius: 50%; border: 2px solid ${isRedSelected ? '#c62828' : 'transparent'}; background-color: #c62828; cursor: pointer;" title="Rot"></button>
            <button type="button" class="note-color-btn ${isYellowSelected ? 'selected' : ''}" data-color="yellow" style="width: 28px; height: 28px; border-radius: 50%; border: 2px solid ${isYellowSelected ? '#ffc107' : 'transparent'}; background-color: #ffc107; cursor: pointer;" title="Gelb"></button>
          </div>
        </div>
        <div class="keyword-dialog-footer">
          <button class="keyword-dialog-btn keyword-dialog-cancel">Abbrechen</button>
          <button class="keyword-dialog-btn keyword-dialog-save">Speichern</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Farbauswahl-Logik
    let selectedColor = preselectedColor;
    const colorBtns = dialog.querySelectorAll('.note-color-btn');
    colorBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        colorBtns.forEach(b => {
          b.style.border = '2px solid transparent';
          b.classList.remove('selected');
        });
        btn.style.border = `2px solid ${btn.style.backgroundColor}`;
        btn.classList.add('selected');
        selectedColor = btn.getAttribute('data-color');
      });
    });
    
    // Focus auf Input
    const input = dialog.querySelector('#note-keyword-input');
    setTimeout(() => input.focus(), 100);
    
    // Event Handler
    const handleSave = () => {
      const keywords = input.value.trim();
      dialog.remove();
      resolve({
        keywords: keywords,
        content: content,
        color: selectedColor
      });
    };
    
    const handleCancel = () => {
      dialog.remove();
      resolve(null);
    };
    
    dialog.querySelector('.keyword-dialog-save').addEventListener('click', handleSave);
    dialog.querySelector('.keyword-dialog-cancel').addEventListener('click', handleCancel);
    
    // Enter-Taste zum Speichern
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        handleSave();
      }
    });
    
    // ESC zum Abbrechen
    dialog.addEventListener('click', (e) => {
      if (e.target === dialog) {
        handleCancel();
      }
    });
  });
}

/**
 * Initialisiert den Chat-Realtime-Listener für Badge-Updates
 * Wird aufgerufen, wenn das members-panel geöffnet wird oder beim Laden der Seite
 */
function initializeChatRealtimeListener() {
  // Prüfe currentUser aus verschiedenen Quellen
  const user = currentUser || window.currentUser;
  if (!user) return;
  
  // Entferne alten Listener falls vorhanden
  if (window.chatChannel) {
    unsubscribeFromChat(window.chatChannel);
    window.chatChannel = null;
  }
  
  // Initialisiere neuen Realtime-Listener
  window.chatChannel = subscribeToChatMessages('general', (message) => {
    // Prüfe currentUser aus verschiedenen Quellen
    const userForCheck = currentUser || window.currentUser;
    // Prüfe ob es eine eigene Nachricht ist
    const isOwnMessage = userForCheck && message.user_id === userForCheck.id;
    
    // Wenn Chat-Tab aktiv ist, zeige Nachricht sofort an
    const isChatTabActive = (typeof currentMembersTab !== 'undefined' && currentMembersTab === 'chat') || 
                            (document.getElementById('chat-messages') !== null);
    
    if (isChatTabActive) {
      appendChatMessage(message);
    }
    
    // Wenn es keine eigene Nachricht ist, aktualisiere Badge IMMER (auch wenn Panel geschlossen ist)
    if (!isOwnMessage) {
      // Aktualisiere Badge mit aktueller Anzahl (nicht nur erhöhen)
      // Das Badge wird auch in app.html aktualisiert, wenn das Panel geschlossen ist
      if (typeof updateChatBadge === 'function') {
        updateChatBadge();
      }
    }
  });
}

/**
 * Chat Tab
 */
async function loadChatTab(container) {
  updateKeywordFilterDropdown([]); // Keine Keywords für Chat
  
  container.innerHTML = `
    <div class="chat-panel">
      <div id="chat-messages" class="chat-messages"></div>
      <div class="chat-input-container">
        <input type="text" id="chat-address-input" class="chat-address-field" placeholder="Adresse" />
        <div class="chat-input-row">
          <textarea id="chat-message-input" class="chat-message-field" placeholder="Nachricht schreiben..." onkeypress="if(event.key==='Enter' && !event.shiftKey){sendMemberChatMessage(); return false;}"></textarea>
        </div>
        <div class="chat-send-container">
          <button class="chat-send-btn" onclick="sendMemberChatMessage()">Senden</button>
        </div>
      </div>
    </div>
  `;
  
  await loadChatMessages();
  
  // Markiere Chat als gelesen
  markChatAsRead();
  
  // Aktualisiere Badge (sollte jetzt 0 sein)
  updateChatBadge();
  
  // Stelle sicher, dass Realtime-Listener aktiv ist (wird normalerweise bereits in initializeChatRealtimeListener erstellt)
  if (!window.chatChannel) {
    initializeChatRealtimeListener();
  }
}

async function loadChatMessages() {
  const result = await getChatMessages('general', 50);
  const container = document.getElementById('chat-messages');
  
  // Set zurücksetzen beim Laden
  window.displayedChatMessageIds = new Set();
  
  if (!result.success || result.data.length === 0) {
    container.innerHTML = '<div class="empty-state">Noch keine Nachrichten</div>';
    return;
  }
  
  // Prüfe currentUser aus verschiedenen Quellen
  const user = currentUser || window.currentUser;
  const isOwnMessage = (msg) => user && msg.user_id === user.id;
  
  container.innerHTML = result.data.map(msg => {
    // Markiere Nachricht als angezeigt
    if (msg.id) {
      window.displayedChatMessageIds.add(msg.id);
    }
    
    const own = isOwnMessage(msg);
    return `
    <div class="chat-message ${own ? 'chat-message-own' : 'chat-message-received'}" ${msg.id ? `data-message-id="${msg.id}"` : ''}>
      <div class="chat-message-header">
        <strong>${msg.user_name}</strong>
        <span>${new Date(msg.created_at).toLocaleTimeString('de-DE', {hour: '2-digit', minute: '2-digit'})}</span>
      </div>
      <div class="chat-message-text">${msg.message}</div>
    </div>
  `;
  }).join('');
  
  // Scroll to bottom
  container.scrollTop = container.scrollHeight;
}

// Set zum Verfolgen bereits angezeigter Nachrichten-IDs
window.displayedChatMessageIds = window.displayedChatMessageIds || new Set();

function appendChatMessage(message) {
  const container = document.getElementById('chat-messages');
  if (!container) return;
  
  // Prüfe ob Nachricht bereits angezeigt wurde (verhindert Duplikate)
  if (message.id && window.displayedChatMessageIds.has(message.id)) {
    return;
  }
  
  // Markiere Nachricht als angezeigt
  if (message.id) {
    window.displayedChatMessageIds.add(message.id);
  }
  
  const isEmpty = container.querySelector('.empty-state');
  if (isEmpty) {
    container.innerHTML = '';
  }
  
  // Prüfe currentUser aus verschiedenen Quellen
  const user = currentUser || window.currentUser;
  const isOwn = user && message.user_id === user.id;
  const messageDiv = document.createElement('div');
  messageDiv.className = `chat-message ${isOwn ? 'chat-message-own' : 'chat-message-received'}`;
  if (message.id) {
    messageDiv.setAttribute('data-message-id', message.id);
  }
  messageDiv.innerHTML = `
    <div class="chat-message-header">
      <strong>${message.user_name}</strong>
      <span>${new Date(message.created_at).toLocaleTimeString('de-DE', {hour: '2-digit', minute: '2-digit'})}</span>
    </div>
    <div class="chat-message-text">${message.message}</div>
  `;
  
  container.appendChild(messageDiv);
  container.scrollTop = container.scrollHeight;
}

/**
 * Markiert Chat als gelesen (speichert aktuellen Zeitstempel)
 */
function markChatAsRead() {
  if (typeof Storage !== 'undefined') {
    localStorage.setItem('chatLastRead', new Date().toISOString());
  }
}

/**
 * Zählt ungelesene Nachrichten seit dem letzten Besuch
 */
async function getUnreadChatCount() {
  // Prüfe currentUser aus verschiedenen Quellen
  const user = currentUser || window.currentUser;
  if (!user) return 0;
  
  const lastRead = localStorage.getItem('chatLastRead');
  if (!lastRead) {
    // Wenn noch nie gelesen, markiere alle aktuellen Nachrichten als gelesen
    markChatAsRead();
    return 0;
  }
  
  const result = await getChatMessages('general', 100);
  if (!result.success || !result.data || result.data.length === 0) {
    return 0;
  }
  
  const lastReadDate = new Date(lastRead);
  const unreadCount = result.data.filter(msg => {
    const msgDate = new Date(msg.created_at);
    return msgDate > lastReadDate && msg.user_id !== user.id;
  }).length;
  
  return unreadCount;
}

/**
 * Aktualisiert das Chat-Badge mit der Anzahl ungelesener Nachrichten
 */
async function updateChatBadge() {
  // Prüfe currentUser aus verschiedenen Quellen
  const user = currentUser || window.currentUser;
  if (!user) {
    // Wenn kein Benutzer eingeloggt ist, verstecke alle Badges
    const badges = [
      document.getElementById('members-chat-badge'),
      document.getElementById('members-chat-badge-2'),
      document.getElementById('members-html-chat-badge'),
      document.getElementById('app-header-chat-badge')
    ];
    badges.forEach(badge => {
      if (badge) {
        badge.textContent = '';
        badge.style.display = 'none';
      }
    });
    return;
  }
  
  const count = await getUnreadChatCount();
  const badges = [
    document.getElementById('members-chat-badge'),
    document.getElementById('members-chat-badge-2'),
    document.getElementById('members-html-chat-badge'),
    document.getElementById('app-header-chat-badge')
  ];
  
  badges.forEach(badge => {
    if (badge) {
      if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count.toString();
        badge.style.display = 'inline-block';
      } else {
        // Badge ausblenden wenn count 0 oder kleiner ist - KEINE Anzeige bei 0!
        badge.textContent = '';
        badge.style.display = 'none';
      }
    }
  });
}

/**
 * Erhöht das Chat-Badge um 1
 */
function incrementChatBadge() {
  const badges = [
    document.getElementById('members-chat-badge'),
    document.getElementById('members-chat-badge-2'),
    document.getElementById('members-html-chat-badge'),
    document.getElementById('app-header-chat-badge')
  ];
  
  badges.forEach(badge => {
    if (badge) {
      const currentCount = parseInt(badge.textContent) || 0;
      const newCount = currentCount + 1;
      // Badge nur anzeigen wenn newCount > 0 - KEINE Anzeige bei 0!
      if (newCount > 0) {
        badge.textContent = newCount > 99 ? '99+' : newCount.toString();
        badge.style.display = 'inline-block';
      } else {
        badge.textContent = '';
        badge.style.display = 'none';
      }
    }
  });
}

async function sendMemberChatMessage() {
  const input = document.getElementById('chat-message-input');
  const message = input.value.trim();
  
  if (!message) return;
  
  // Optimistisches UI Update: Zeige Nachricht sofort an
  const tempMessage = {
    id: 'temp-' + Date.now(),
    user_id: currentUser?.id,
    user_name: currentUser?.email || 'Ich',
    message: message,
    created_at: new Date().toISOString(),
    room: 'general'
  };
  
  // Zeige Nachricht sofort an
  appendChatMessage(tempMessage);
  
  // Leere Eingabefeld sofort
  input.value = '';
  
  // Sende Nachricht an Server
  const result = await sendChatMessage(message, 'general');
  
  if (result.success && result.data) {
    // Entferne temporäre Nachricht und ersetze durch echte
    const container = document.getElementById('chat-messages');
    const tempElement = container.querySelector(`[data-message-id="${tempMessage.id}"]`);
    if (tempElement) {
      tempElement.remove();
      window.displayedChatMessageIds.delete(tempMessage.id);
    }
    
    // Füge echte Nachricht hinzu (wird normalerweise auch über Realtime-Listener kommen, aber sicherheitshalber)
    appendChatMessage(result.data);
  } else {
    // Bei Fehler: Entferne temporäre Nachricht
    const container = document.getElementById('chat-messages');
    const tempElement = container.querySelector(`[data-message-id="${tempMessage.id}"]`);
    if (tempElement) {
      tempElement.remove();
      window.displayedChatMessageIds.delete(tempMessage.id);
    }
    alert('Fehler beim Senden');
    // Setze Text zurück
    input.value = message;
  }
}

/**
 * Edit Handlers
 */
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
      // Invalidiere Cache, damit Daten neu geladen werden
      invalidateMembersCache('quotes');
      await loadMembersTab('quotes');
      // Aktualisiere Schlagwort-Dropdown mit neuen Keywords
      await updateKeywordFilterDropdownWithAllKeywords();
    } else {
      alert('Fehler beim Speichern: ' + updateResult.error);
    }
  } catch (error) {
    console.error('Fehler beim Bearbeiten:', error);
    alert('Fehler beim Bearbeiten des Zitats');
  }
}

async function editMemberHighlight(id) {
  try {
    // Hole Highlight-Daten
    const result = await getHighlights();
    if (!result.success) {
      alert('Fehler beim Laden der Unterstreichung');
      return;
    }
    
    const highlight = result.data.find(h => h.id === id);
    if (!highlight) {
      alert('Unterstreichung nicht gefunden');
      return;
    }
    
    // Extrahiere den unterstrichenen Text
    const highlightedText = highlight.paragraph_text && highlight.text_start_offset !== null && highlight.text_end_offset !== null
      ? highlight.paragraph_text.substring(highlight.text_start_offset, highlight.text_end_offset)
      : highlight.paragraph_text || '';
    
    // Zeige Bearbeitungs-Dialog
    const editResult = await showEditDialog('Unterstreichung', {
      text: highlightedText,
      keywords: highlight.tags ? highlight.tags.join(', ') : '',
      note: highlight.personal_note || ''
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
    if (typeof updateHighlight !== 'function') {
      alert('Fehler: updateHighlight Funktion nicht verfügbar. Bitte Seite neu laden.');
      console.error('[MB-HIGHLIGHTS] updateHighlight nicht verfügbar');
      return;
    }
    
    const updateResult = await updateHighlight(id, {
      tags: tags,
      personal_note: note || ''
    });
    
    if (updateResult.success) {
      // Invalidiere Cache, damit Daten neu geladen werden
      invalidateMembersCache('highlights');
      await loadMembersTab('highlights');
      // Aktualisiere Schlagwort-Dropdown mit neuen Keywords
      await updateKeywordFilterDropdownWithAllKeywords();
    } else {
      alert('Fehler beim Speichern: ' + updateResult.error);
    }
  } catch (error) {
    console.error('Fehler beim Bearbeiten:', error);
    alert('Fehler beim Bearbeiten der Unterstreichung');
  }
}

/**
 * Spezieller Bearbeitungs-Dialog für Notizen (mit Textfeld für Content)
 */
function showNoteEditDialog(content, keywords = '') {
  return new Promise((resolve) => {
    // Erstelle Dialog
    const dialog = document.createElement('div');
    dialog.className = 'keyword-dialog-overlay';
    dialog.innerHTML = `
      <div class="keyword-dialog" style="max-width: 600px;">
        <div class="keyword-dialog-header">
          <h3>Notiz bearbeiten</h3>
        </div>
        <div class="keyword-dialog-body">
          <label for="note-content-input" style="display: block; margin-bottom: 0.5rem;">Inhalt:</label>
          <textarea id="note-content-input" rows="8" placeholder="Notiz-Text..." style="width: 100%; padding: 0.6rem; border: 1px solid var(--border-color); border-radius: 4px; font-family: Georgia, serif; font-size: 0.9rem; background: var(--background-color); color: var(--text-color); box-sizing: border-box; resize: vertical;">${(content || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</textarea>
          <label for="note-keyword-input" style="display: block; margin-top: 1rem; margin-bottom: 0.5rem;">Keywords (optional, durch Komma getrennt):</label>
          <input type="text" id="note-keyword-input" value="${(keywords || '').replace(/"/g, '&quot;')}" placeholder="z.B. Karma, Reinkarnation, Ätherleib" style="width: 100%; padding: 0.6rem; border: 1px solid var(--border-color); border-radius: 4px; font-family: inherit; font-size: 0.9rem; background: var(--background-color); color: var(--text-color); box-sizing: border-box;" />
          <div class="keyword-hint">Keywords helfen beim späteren Filtern und Wiederfinden</div>
        </div>
        <div class="keyword-dialog-footer">
          <button class="keyword-dialog-btn keyword-dialog-cancel">Abbrechen</button>
          <button class="keyword-dialog-btn keyword-dialog-save">Speichern</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Focus auf Textarea
    const contentInput = dialog.querySelector('#note-content-input');
    const keywordInput = dialog.querySelector('#note-keyword-input');
    setTimeout(() => contentInput.focus(), 100);
    
    // Event Handlers
    const saveBtn = dialog.querySelector('.keyword-dialog-save');
    const cancelBtn = dialog.querySelector('.keyword-dialog-cancel');
    
    const handleSave = () => {
      const text = contentInput.value.trim();
      const keywords = keywordInput.value.trim();
      dialog.remove();
      resolve({ keywords, text });
    };
    
    const handleCancel = () => {
      dialog.remove();
      resolve(null);
    };
    
    saveBtn.addEventListener('click', handleSave);
    cancelBtn.addEventListener('click', handleCancel);
    
    // ESC zum Abbrechen
    dialog.addEventListener('click', (e) => {
      if (e.target === dialog) {
        handleCancel();
      }
    });
    
    // ESC-Taste zum Abbrechen
    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        handleCancel();
        document.removeEventListener('keydown', handleEsc);
      }
    };
    document.addEventListener('keydown', handleEsc);
  });
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
      resolve({ keywords, note, text: data.text }); // Füge text hinzu für Notizen
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
 * Edit Handlers
 */
async function editMemberNote(id) {
  try {
    // Hole Notiz-Daten
    const result = await getNotes();
    if (!result.success) {
      alert('Fehler beim Laden der Notiz');
      return;
    }
    
    const note = result.data.find(n => n.id === id);
    if (!note) {
      alert('Notiz nicht gefunden');
      return;
    }
    
    // GA-Referenz für Navigation (wird nicht mehr im Content gespeichert)
    const gaReference = note.ga_references && note.ga_references.length > 0 ? note.ga_references[0] : null;
    
    // Bereinige Content für Anzeige (entferne Präfix falls vorhanden)
    let displayContent = note.content || '';
    displayContent = displayContent.replace(/^Aus\s*\[\[[^\]]+\]\]\s*[-:]\s*/i, '').trim();
    
    // Zeige speziellen Bearbeitungs-Dialog für Notizen (mit Textfeld für Content)
    const editResult = await showNoteEditDialog(displayContent, note.tags ? note.tags.join(', ') : '');
    
    if (editResult === null) {
      // Benutzer hat abgebrochen
      return;
    }
    
    const { keywords, text } = editResult;
    const tags = keywords
      .split(',')
      .map(kw => kw.trim())
      .filter(kw => kw.length > 0);
    
    // Stelle sicher, dass Text vorhanden ist
    if (!text && text !== '') {
      console.error('[MB-NOTES] editResult.text ist undefined');
      alert('Fehler: Kein Text im Bearbeitungsdialog erhalten');
      return;
    }
    
    // Entferne Präfix "Aus [[GA001]]:" falls vorhanden (soll nicht gespeichert werden)
    let updatedContent = text || '';
    updatedContent = updatedContent.replace(/^Aus\s*\[\[[^\]]+\]\]\s*[-:]\s*/i, '').trim();
    
    // Update in Supabase
    if (typeof updateNote !== 'function') {
      alert('Fehler: updateNote Funktion nicht verfügbar. Bitte Seite neu laden.');
      console.error('[MB-NOTES] updateNote nicht verfügbar');
      return;
    }
    
    // Füge Tags als #tags hinzu, falls sie nicht bereits im Content vorhanden sind
    if (tags.length > 0) {
      const existingTags = updatedContent.match(/#(\w+)/g) || [];
      const existingTagNames = existingTags.map(t => t.substring(1).toLowerCase());
      const newTags = tags.filter(tag => !existingTagNames.includes(tag.toLowerCase()));
      if (newTags.length > 0) {
        const tagsString = newTags.map(tag => `#${tag}`).join(' ');
        updatedContent = updatedContent.trim() + '\n\n' + tagsString;
      }
    }
    
    const title = updatedContent.split('\n')[0].substring(0, 50);
    
    // Tags aus dem keywords-Feld verwenden (manuell eingegeben)
    const updateResult = await updateNote(id, title, updatedContent, note.is_public || false, tags);
    
    if (updateResult.success) {
      // Invalidiere Cache, damit Daten neu geladen werden
      invalidateMembersCache('notes');
      await loadSavedNotes();
      // Aktualisiere auch members.html falls geöffnet
      if (typeof loadItems === 'function' && typeof currentTab !== 'undefined' && currentTab === 'notes') {
        await loadItems();
      }
      // Aktualisiere Schlagwort-Dropdown mit neuen Keywords
      await updateKeywordFilterDropdownWithAllKeywords();
    } else {
      alert('Fehler beim Speichern: ' + updateResult.error);
    }
  } catch (error) {
    console.error('Fehler beim Bearbeiten der Notiz:', error);
    alert('Fehler beim Bearbeiten: ' + error.message);
  }
}

/**
 * Delete Handlers
 */
async function deleteMemberQuote(id) {
  if (!confirm('Zitat wirklich löschen?')) return;
  
  const result = await deleteQuote(id);
  if (result.success) {
    // Entferne das visuelle Zitat sofort aus dem Main Viewer
    // Versuche mehrmals, falls das Element noch nicht im DOM ist
    removeQuoteFromText(id);
    setTimeout(() => removeQuoteFromText(id), 100);
    setTimeout(() => removeQuoteFromText(id), 500);
    
    // Invalidiere Cache, damit Daten neu geladen werden
    invalidateMembersCache('quotes');
    await loadMembersTab('quotes');
  }
}

async function deleteMemberNote(id) {
  if (!confirm('Notiz wirklich löschen?')) return;
  
  const result = await deleteNote(id);
  if (result.success) {
    // Entferne Bookmark-Icon im Main Viewer
    const bookmarkIndicator = document.querySelector(`.bookmark-note-indicator[data-note-id="${id}"]`);
    if (bookmarkIndicator) {
      bookmarkIndicator.remove();
      console.log('[MB-NOTES] Bookmark-Icon aus Main Viewer entfernt');
    }
    
    // Entferne eventuelle Notiz-Markierungen im Text (Inhalt erhalten)
    const noteHighlights = document.querySelectorAll('mark.note-highlight');
    noteHighlights.forEach(mark => {
      const parent = mark.parentNode;
      while (mark.firstChild) {
        parent.insertBefore(mark.firstChild, mark);
      }
      mark.remove();
    });
    
    await loadSavedNotes();
    // Aktualisiere MB falls offen und Notizen-Tab aktiv
    if (typeof membersPanelActive !== 'undefined' && membersPanelActive && currentMembersTab === 'notes') {
      // Notizen-Tab wird bereits durch loadSavedNotes() aktualisiert
      // Kein Cache für Notizen, daher keine Invalidierung nötig
    }
  }
}

/**
 * Sortier-Reihenfolge umschalten
 */
function toggleSortOrder() {
  sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
  // Aktuellen Tab neu laden (funktioniert für alle Tabs: quotes, highlights, bookmarks, etc.)
  if (currentMembersTab) {
    loadMembersTab(currentMembersTab);
  }
}

/**
 * Multi-Delete-Modus umschalten
 */
function toggleMultiDeleteMode() {
  multiDeleteMode = !multiDeleteMode;
  // Aktuellen Tab neu laden (funktioniert für beide: quotes und highlights)
  if (currentMembersTab === 'quotes' || currentMembersTab === 'highlights') {
    loadMembersTab(currentMembersTab);
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
  
  const itemName = currentMembersTab === 'quotes' ? 'Zitat(e)' : 
                   currentMembersTab === 'highlights' ? 'Unterstreichung(en)' : 'Item(s)';
  if (!confirm(`Wirklich ${checkboxes.length} ${itemName} löschen?`)) {
    return;
  }
  
  const ids = Array.from(checkboxes).map(cb => cb.dataset.id);
  
  try {
    if (currentMembersTab === 'quotes') {
      for (const id of ids) {
        await deleteQuote(id);
      }
    } else if (currentMembersTab === 'highlights') {
      for (const id of ids) {
        const result = await deleteHighlight(id);
        if (result && result.success) {
          // Entferne die visuelle Unterstreichung sofort aus dem Text
          removeHighlightFromText(id);
        }
      }
    }
    
    // Multi-Delete-Modus beenden und Tab neu laden
    multiDeleteMode = false;
    // Invalidiere Cache, damit Daten neu geladen werden
    invalidateMembersCache(currentMembersTab);
    await loadMembersTab(currentMembersTab);
  } catch (error) {
    console.error('Fehler beim Löschen:', error);
    alert('Fehler beim Löschen einiger Items');
  }
}

// Cache für die letzten markierten Lecture-IDs, um Icons nach DOM-Änderungen wiederherzustellen
let lastMarkedLectureId = null;
let lastQuotesData = null;

// Globaler Cache für Quotes und Highlights (wird beim Öffnen des Mitgliederbereichs geladen)
let cachedQuotesData = null;
let cachedHighlightsData = null;
let bookmarksQuotesCacheTimestamp = null;
const BOOKMARKS_QUOTES_CACHE_TTL = 300000; // 5 Minuten Cache-Gültigkeit (erhöht für bessere Performance)

/**
 * Markiere Absätze im Viewer, die bereits Zitate oder Unterstreichungen haben
 */
async function markParagraphsWithBookmarksAndQuotes(lectureId) {
  try {
    // Prüfe ob User angemeldet ist
    if (typeof currentUser === 'undefined' || !currentUser) {
      return; // Nicht angemeldet - keine Markierungen
    }
    
    // Prüfe Cache zuerst (wenn vorhanden und noch gültig)
    let quotesResult, highlightsResult;
    const now = Date.now();
    const cacheValid = cachedQuotesData && cachedHighlightsData && 
                       bookmarksQuotesCacheTimestamp && 
                       (now - bookmarksQuotesCacheTimestamp) < BOOKMARKS_QUOTES_CACHE_TTL;
    
    if (cacheValid) {
      // Verwende gecachte Daten (synchron, sehr schnell!)
      quotesResult = cachedQuotesData;
      highlightsResult = cachedHighlightsData;
    } else {
      // Lade alle Zitate und Unterstreichungen (nur wenn Cache nicht verfügbar)
      const results = await Promise.all([
        getQuotes(),
        getHighlights ? getHighlights() : Promise.resolve({ success: false, data: [] })
      ]);
      quotesResult = results[0];
      highlightsResult = results[1];
      
      // Aktualisiere Cache
      cachedQuotesData = quotesResult;
      cachedHighlightsData = highlightsResult;
      bookmarksQuotesCacheTimestamp = now;
    }
    
    // Lade auch Notizen für Icons
    let notesResult = { success: false, data: [] };
    if (typeof getNotes === 'function') {
      try {
        notesResult = await getNotes();
      } catch (e) {
        console.warn('[MB-MARKS] Fehler beim Laden der Notizen:', e);
      }
    }
    
    if (!quotesResult.success && !highlightsResult.success) {
      return; // Fehler beim Laden
    }
    
    // Cache für spätere Wiederherstellung
    lastMarkedLectureId = lectureId;
    lastQuotesData = quotesResult;
    
    // Sammle alle paragraph_ids für diesen Vortrag (Zitate)
    const paragraphIds = new Set();
    
    if (quotesResult.success && quotesResult.data) {
      quotesResult.data
        .filter(q => q.ga_reference === lectureId && q.paragraph_id)
        .forEach(q => paragraphIds.add(q.paragraph_id));
    }
    
    // Markiere alle Absätze im Viewer mit Quote-Icons
    paragraphIds.forEach(paraId => {
      addBookmarkQuoteIndicator(paraId, lectureId, null, quotesResult);
    });
    
    // Sammle alle paragraph_ids für Notizen
    const noteParagraphIds = new Set();
    const notesForLecture = [];
    
    if (notesResult.success && notesResult.data) {
      console.log('[MB-NOTES] Alle Notizen:', notesResult.data.length, 'Lecture-ID:', lectureId);
      
      notesResult.data.forEach(n => {
        // Prüfe ob Notiz zu diesem Vortrag gehört
        if (!n.ga_references || !Array.isArray(n.ga_references)) {
          console.log('[MB-NOTES] Notiz ohne ga_references:', n.id);
          return;
        }
        
        const matchesGA = n.ga_references.some(ga => {
          // Prüfe auf exakte Übereinstimmung
          if (ga === lectureId) return true;
          // Prüfe auf Basis-GA Übereinstimmung (GA001 vs GA001/5)
          const baseMatch = ga.match(/^(GA\d{3})/i);
          const lectureBase = lectureId.match(/^(GA\d{3})/i);
          return baseMatch && lectureBase && baseMatch[1].toUpperCase() === lectureBase[1].toUpperCase();
        });
        
        if (matchesGA) {
          console.log('[MB-NOTES] Notiz passt zu Lecture:', n.id, 'GA:', n.ga_references, 'ParagraphId:', n.paragraph_id);
          notesForLecture.push(n);
          if (n.paragraph_id) {
            noteParagraphIds.add(n.paragraph_id);
          }
        }
      });
      
      console.log('[MB-NOTES] Notizen für diesen Vortrag:', notesForLecture.length, 'Mit paragraph_id:', noteParagraphIds.size);
    }
    
    // Markiere alle Absätze mit Notiz-Icons
    noteParagraphIds.forEach(paraId => {
      console.log('[MB-NOTES] Füge Icon hinzu für:', paraId);
      addBookmarkNoteIndicator(paraId, lectureId, notesResult);
    });
    
    // Wende Zitat-Linien an (senkrechte Linie am linken Rand)
    if (quotesResult.success && quotesResult.data) {
      const lectureQuotes = quotesResult.data.filter(q => 
        q.ga_reference === lectureId && q.paragraph_id && q.text_start_offset !== null
      );
      
      // Wende jedes Zitat an
      lectureQuotes.forEach(quote => {
        applyStoredQuoteLine(quote);
      });
    }
    
    // Wende Unterstreichungen an
    // WICHTIG: Sortiere nach text_start_offset, damit Highlights in der richtigen Reihenfolge angewendet werden
    // Dies verhindert Verschiebungen, wenn mehrere Highlights im selben Absatz vorhanden sind
    if (highlightsResult.success && highlightsResult.data) {
      const lectureHighlights = highlightsResult.data.filter(h => 
        h.ga_number === lectureId && h.paragraph_id
      );
      
      // Gruppiere nach paragraph_id und sortiere innerhalb jeder Gruppe nach text_start_offset
      const highlightsByParagraph = {};
      lectureHighlights.forEach(highlight => {
        const paraId = highlight.paragraph_id || '';
        if (!highlightsByParagraph[paraId]) {
          highlightsByParagraph[paraId] = [];
        }
        highlightsByParagraph[paraId].push(highlight);
      });
      
      // Sortiere jede Gruppe nach text_start_offset (von Anfang nach Ende)
      Object.keys(highlightsByParagraph).forEach(paraId => {
        highlightsByParagraph[paraId].sort((a, b) => {
          const offsetA = a.text_start_offset !== null && a.text_start_offset !== undefined ? a.text_start_offset : 0;
          const offsetB = b.text_start_offset !== null && b.text_start_offset !== undefined ? b.text_start_offset : 0;
          return offsetA - offsetB;
        });
      });
      
      // Wende Highlights in sortierter Reihenfolge an
      Object.values(highlightsByParagraph).forEach(highlightGroup => {
        highlightGroup.forEach(highlight => {
          applyStoredHighlight(highlight);
        });
      });
    }
    
    // KEIN Bookmark-Icon mehr in den Highlight-Spans - nur noch das Icon am Absatzanfang (bookmark-quote-indicator)
    // setTimeout(() => {
    //   if (typeof addBookmarkIconsToExistingQuotes === 'function') {
    //     addBookmarkIconsToExistingQuotes();
    //   }
    // }, 100);
  } catch (error) {
    console.error('Fehler beim Markieren der Absätze:', error);
  }
}

/**
 * Fügt ein Quote-Icon zu einem Absatz hinzu
 * DEAKTIVIERT: Zitate werden nur noch durch senkrechte Linie markiert, nicht mehr durch Icons
 */
function addBookmarkQuoteIndicator(paraId, lectureId, bookmarksResult, quotesResult) {
  // DEAKTIVIERT: Keine Icons mehr für Zitate im Main Viewer
  // Zitate werden nur noch durch die senkrechte Linie markiert
  return;
  
  const paraElement = document.getElementById(`para-${paraId}`);
  if (!paraElement) return;
  
  // Prüfe ob Icon bereits vorhanden ist (auch nach DOM-Manipulationen)
  // Suche im paraElement selbst und in Parent-Elementen
  let targetElement = paraElement;
  let existingIndicator = paraElement.querySelector('.bookmark-quote-indicator');
  
  // Bei Büchern: para- IDs sind in versteckten Spans, finde das Parent-Element
  if (paraElement.style.display === 'none' || paraElement.tagName.toLowerCase() === 'span') {
    // Suche nach dem nächsten Block-Element (p, div, etc.)
    let parent = paraElement.parentElement;
    while (parent && parent !== document.body) {
      const tagName = parent.tagName.toLowerCase();
      if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
        targetElement = parent;
        existingIndicator = parent.querySelector('.bookmark-quote-indicator');
        break;
      }
      parent = parent.parentElement;
    }
  }
  
  if (existingIndicator) return; // Bereits vorhanden
  
  // Prüfe ob Zitat vorhanden und hole das erste Zitat (mit kleinstem text_start_offset)
  const quotes = quotesResult && quotesResult.success ? quotesResult.data.filter(q => 
    q.ga_reference === lectureId && q.paragraph_id === paraId && q.text_start_offset !== null
  ) : [];
  
  if (quotes.length === 0) return; // Kein Zitat vorhanden
  
  // Sortiere nach text_start_offset und nimm das erste (früheste) Zitat
  const sortedQuotes = quotes.sort((a, b) => {
    const offsetA = a.text_start_offset !== null && a.text_start_offset !== undefined ? a.text_start_offset : 0;
    const offsetB = b.text_start_offset !== null && b.text_start_offset !== undefined ? b.text_start_offset : 0;
    return offsetA - offsetB;
  });
  const firstQuote = sortedQuotes[0];
  
  // Erstelle Markierung mit Farbe
  const quoteColor = firstQuote.marker_color || 'blue';
  const quoteColorHex = getHighlightColor(quoteColor);
  const indicator = document.createElement('span');
  indicator.className = 'bookmark-quote-indicator';
  indicator.setAttribute('data-para-id', paraId); // Für Wiederherstellung
  indicator.setAttribute('data-quote-id', firstQuote.id); // Für Farbänderung
  indicator.style.color = quoteColorHex;
  indicator.title = 'Zitat vorhanden - Klick zum Öffnen';
  indicator.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="4" width="16" height="16"></rect>
    </svg>
  `;
  indicator.onclick = (e) => {
    e.stopPropagation();
    e.preventDefault();
    // Verwende direkt die quoteId für robuste Navigation
    if (typeof jumpToQuoteById === 'function') {
      jumpToQuoteById(firstQuote.id);
    } else {
      // Fallback: Verwende die alte Methode
      jumpToBookmarkOrQuote(lectureId, paraId, false, true);
    }
  };
  
  // Stelle sicher, dass targetElement relativ positioniert ist
  targetElement.style.position = 'relative';
  
  // Berechne die Position basierend auf text_start_offset
  // Verwende einen Range, um die Position des Textes zu finden
  if (firstQuote.text_start_offset !== null && firstQuote.text_start_offset !== undefined) {
    try {
      // Hole den Text ohne Highlights/Quotes für die Berechnung
      const elementTextWithoutHighlights = getTextContentWithoutHighlights(targetElement);
      
      if (elementTextWithoutHighlights && elementTextWithoutHighlights.length > firstQuote.text_start_offset) {
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
          if (currentOffset + nodeLength > firstQuote.text_start_offset) {
            targetNode = node;
            targetOffset = firstQuote.text_start_offset - currentOffset;
            break;
          }
          currentOffset += nodeLength;
        }
        
        if (targetNode) {
          try {
            // Setze Range auf die Position des Zitat-Beginns
            range.setStart(targetNode, Math.min(targetOffset, targetNode.textContent.length));
            range.setEnd(targetNode, Math.min(targetOffset, targetNode.textContent.length));
            
            // Erstelle einen unsichtbaren Marker-Span an dieser Position für die Positionierung
            const marker = document.createElement('span');
            marker.style.display = 'inline';
            marker.style.width = '0';
            marker.style.height = '0';
            marker.style.visibility = 'hidden';
            marker.style.pointerEvents = 'none';
            marker.setAttribute('data-quote-marker', 'true');
            
            // Füge Marker ein
            range.insertNode(marker);
            
            // Warte kurz, damit der DOM aktualisiert ist, dann positioniere das Icon
            requestAnimationFrame(() => {
              try {
                // Hole Positionen
                const markerRect = marker.getBoundingClientRect();
                const targetRect = targetElement.getBoundingClientRect();
                const relativeTop = markerRect.top - targetRect.top;
                
                // Setze Position des Icons absolut
                indicator.style.position = 'absolute';
                indicator.style.left = '-20px';
                indicator.style.top = relativeTop + 'px';
                indicator.style.marginTop = '0'; // Keine zusätzliche Anpassung
                
                // Füge Icon zum targetElement hinzu
                targetElement.appendChild(indicator);
                
                // Entferne Marker nach kurzer Zeit
                setTimeout(() => {
                  if (marker.parentNode) {
                    marker.parentNode.removeChild(marker);
                  }
                }, 100);
                
                console.log('[QUOTE-INDICATOR] Icon auf Höhe des Zitat-Beginns positioniert:', firstQuote.text_start_offset, 'top:', relativeTop);
              } catch (e) {
                console.warn('[QUOTE-INDICATOR] Fehler bei Icon-Positionierung:', e);
                // Fallback: Entferne Marker und füge Icon normal hinzu
                if (marker.parentNode) {
                  marker.parentNode.removeChild(marker);
                }
                targetElement.insertBefore(indicator, targetElement.firstChild);
              }
            });
            
            return;
          } catch (e) {
            console.warn('[QUOTE-INDICATOR] Fehler bei Range-Positionierung, verwende Fallback:', e);
          }
        }
      }
    } catch (e) {
      console.warn('[QUOTE-INDICATOR] Fehler bei Positionierung, verwende Fallback:', e);
    }
  }
  
  // Fallback: Füge am Anfang des Absatzes hinzu (wenn keine Offsets vorhanden)
  targetElement.insertBefore(indicator, targetElement.firstChild);
}

/**
 * Fügt ein Notiz-Icon zu einem Absatz hinzu
 */
function addBookmarkNoteIndicator(paraId, lectureId, notesResult) {
  console.log('[MB-NOTES-ICON] Versuche Icon hinzuzufügen für paraId:', paraId);
  
  const paraElement = document.getElementById(`para-${paraId}`);
  if (!paraElement) {
    console.log('[MB-NOTES-ICON] Element para-' + paraId + ' nicht gefunden');
    return;
  }
  
  console.log('[MB-NOTES-ICON] Element gefunden:', paraElement.tagName, paraElement.id);
  
  // Prüfe ob Icon bereits vorhanden ist
  let targetElement = paraElement;
  let existingIndicator = paraElement.querySelector('.bookmark-note-indicator');
  
  // Bei Büchern: para- IDs sind in versteckten Spans, finde das Parent-Element
  if (paraElement.style.display === 'none' || paraElement.tagName.toLowerCase() === 'span') {
    console.log('[MB-NOTES-ICON] Suche nach Parent-Element für verstecktes span');
    let parent = paraElement.parentElement;
    while (parent && parent !== document.body) {
      const tagName = parent.tagName.toLowerCase();
      if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
        targetElement = parent;
        existingIndicator = parent.querySelector('.bookmark-note-indicator');
        console.log('[MB-NOTES-ICON] Parent gefunden:', tagName);
        break;
      }
      parent = parent.parentElement;
    }
  }
  
  if (existingIndicator) {
    console.log('[MB-NOTES-ICON] Icon bereits vorhanden');
    return;
  }
  
  // Prüfe ob Notiz vorhanden
  const notes = notesResult && notesResult.success ? notesResult.data.filter(n => {
    if (!n.ga_references || !Array.isArray(n.ga_references)) return false;
    const matchesGA = n.ga_references.some(ga => {
      if (ga === lectureId) return true;
      const baseMatch = ga.match(/^(GA\d{3})/i);
      const lectureBase = lectureId.match(/^(GA\d{3})/i);
      return baseMatch && lectureBase && baseMatch[1].toUpperCase() === lectureBase[1].toUpperCase();
    });
    return matchesGA && n.paragraph_id === paraId;
  }) : [];
  
  console.log('[MB-NOTES-ICON] Passende Notizen:', notes.length);
  
  if (notes.length === 0) {
    console.log('[MB-NOTES-ICON] Keine passende Notiz gefunden');
    return;
  }
  
  const firstNote = notes[0];
  console.log('[MB-NOTES-ICON] Erstelle Icon für Notiz:', firstNote.id, 'Farbe:', firstNote.marker_color);
  
  // Erstelle Markierung - Notiz-Icon mit der Farbe der Notiz
  const noteColor = firstNote.marker_color || 'blue';
  const noteColorHex = getNoteColor(noteColor);
  const indicator = document.createElement('span');
  indicator.className = 'bookmark-note-indicator';
  indicator.setAttribute('data-para-id', paraId);
  indicator.setAttribute('data-note-id', firstNote.id);
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
      jumpToNoteById(firstNote.id);
    }
  };
  
  // Stelle sicher, dass targetElement relativ positioniert ist
  targetElement.style.position = 'relative';
  
  // Positioniere das Icon absolut links neben dem Absatz (wie bei Zitaten)
  const textStartOffset = firstNote.text_start_offset;
  
  if (textStartOffset !== null && textStartOffset !== undefined) {
    try {
      // Hole den Text ohne Highlights für die Berechnung
      const elementTextWithoutHighlights = typeof getTextContentWithoutHighlights === 'function' 
        ? getTextContentWithoutHighlights(targetElement) 
        : targetElement.textContent;
      
      if (elementTextWithoutHighlights && elementTextWithoutHighlights.length > textStartOffset) {
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
            // Setze Range auf die Position des Notiz-Beginns
            range.setStart(targetNode, Math.min(targetOffset, targetNode.textContent.length));
            range.setEnd(targetNode, Math.min(targetOffset, targetNode.textContent.length));
            
            // Erstelle einen unsichtbaren Marker-Span an dieser Position
            const marker = document.createElement('span');
            marker.style.display = 'inline';
            marker.style.width = '0';
            marker.style.height = '0';
            marker.style.visibility = 'hidden';
            marker.style.pointerEvents = 'none';
            marker.setAttribute('data-note-marker', 'true');
            
            // Füge Marker ein
            range.insertNode(marker);
            
            // Warte kurz, damit der DOM aktualisiert ist
            requestAnimationFrame(() => {
              try {
                // Hole Positionen
                const markerRect = marker.getBoundingClientRect();
                const targetRect = targetElement.getBoundingClientRect();
                const relativeTop = markerRect.top - targetRect.top;
                
                // Setze Position des Icons absolut links neben dem Absatz
                indicator.style.position = 'absolute';
                indicator.style.left = '-20px';
                indicator.style.top = relativeTop + 'px';
                
                // Füge Icon zum targetElement hinzu
                targetElement.appendChild(indicator);
                
                // Entferne Marker
                setTimeout(() => {
                  if (marker.parentNode) {
                    marker.parentNode.removeChild(marker);
                  }
                }, 100);
                
                console.log('[NOTE-INDICATOR] Icon auf Höhe des Notiz-Beginns positioniert:', textStartOffset, 'top:', relativeTop);
              } catch (e) {
                console.warn('[NOTE-INDICATOR] Fehler bei Icon-Positionierung:', e);
                if (marker.parentNode) {
                  marker.parentNode.removeChild(marker);
                }
                // Fallback: Position oben links
                indicator.style.position = 'absolute';
                indicator.style.left = '-20px';
                indicator.style.top = '0px';
                targetElement.appendChild(indicator);
              }
            });
            
            return;
          } catch (e) {
            console.warn('[NOTE-INDICATOR] Fehler bei Range-Positionierung:', e);
          }
        }
      }
    } catch (e) {
      console.warn('[NOTE-INDICATOR] Fehler bei Text-Offset-Berechnung:', e);
    }
  }
  
  // Fallback: Position oben links neben dem Absatz
  indicator.style.position = 'absolute';
  indicator.style.left = '-20px';
  indicator.style.top = '0px';
  targetElement.appendChild(indicator);
}

/**
 * Springt zum Notizen-Tab und scrollt zur Notiz mit der gegebenen ID
 */
async function jumpToNoteById(noteId) {
  try {
    // Öffne MB falls nicht offen
    if (!membersPanelActive) {
      if (typeof openMembersPanel === 'function') {
        await openMembersPanel();
      }
    }
    
    // Wechsle zum Notes-Tab
    if (typeof switchMembersTab === 'function') {
      await switchMembersTab('notes');
    }
    
    // Warte kurz, dann scrolle zum Item - mehrere Versuche für robustere Navigation
    let scrollAttempts = 0;
    const maxScrollAttempts = 10;
    
    const tryScrollToNote = () => {
      scrollAttempts++;
      const targetItem = document.querySelector(`.member-item[data-id="${noteId}"]`);
      if (targetItem) {
        // Scrolle nur den Content-Bereich, nicht das gesamte Panel
        const membersContent = document.querySelector('.members-content');
        if (membersContent) {
          // Berechne Position relativ zum scrollbaren Container
          const containerRect = membersContent.getBoundingClientRect();
          const itemRect = targetItem.getBoundingClientRect();
          
          // Berechne die relative Position: Item-Position minus Container-Position plus aktueller Scroll
          const relativeTop = itemRect.top - containerRect.top + membersContent.scrollTop;
          
          // Scrolle so, dass das Item oben erscheint (mit etwas Abstand)
          membersContent.scrollTo({
            top: Math.max(0, relativeTop - 20), // 20px Abstand oben
            behavior: 'smooth'
          });
        } else {
          // Fallback: Nur Content scrollen, nicht das gesamte Panel
          const membersTabContent = document.getElementById('members-tab-content');
          if (membersTabContent) {
            const containerRect = membersTabContent.getBoundingClientRect();
            const itemRect = targetItem.getBoundingClientRect();
            const relativeTop = itemRect.top - containerRect.top + membersTabContent.scrollTop;
            
            membersTabContent.scrollTo({
              top: Math.max(0, relativeTop - 20),
              behavior: 'smooth'
            });
          }
        }
        // Highlighte kurz (gleiche CSS-Klasse wie bei Zitaten)
        targetItem.classList.add('member-item-highlighted');
        setTimeout(() => {
          targetItem.classList.remove('member-item-highlighted');
        }, 2000);
        return; // Erfolgreich gescrollt
      } else if (scrollAttempts < maxScrollAttempts) {
        // Item noch nicht gefunden, versuche es erneut
        setTimeout(() => tryScrollToNote(), 200 + (scrollAttempts * 50));
      } else {
        console.warn('[NOTE-JUMP] Notiz mit ID', noteId, 'nicht gefunden nach', maxScrollAttempts, 'Versuchen');
      }
    };
    
    // Starte den ersten Versuch
    setTimeout(() => tryScrollToNote(), 500);
  } catch (error) {
    console.error('[MB-NOTE-JUMP] Fehler:', error);
  }
}

// Global verfügbar machen
window.jumpToNoteById = jumpToNoteById;

/**
 * Fügt Click-Event-Listener zu allen Unterstreichungen hinzu, die noch keinen haben
 */
// Event-Delegation für Highlights (funktioniert auch wenn Elemente später hinzugefügt werden)
let highlightDelegationListenerAttached = false;
function attachHighlightDelegationListener() {
  // Prüfe ob bereits angehängt - aber erlaube erneutes Anhängen für Robustheit
  if (highlightDelegationListenerAttached) {
    // Prüfe ob Listener noch aktiv ist
    const viewer = document.getElementById('viewer');
    if (viewer && viewer.hasAttribute('data-highlight-listener-attached')) {
      return; // Bereits angehängt und aktiv
    }
  }
  
  const viewer = document.getElementById('viewer');
  if (!viewer) {
    console.warn('[HIGHLIGHT-DELEGATION] Viewer nicht gefunden');
    return;
  }
  
  // Markiere als angehängt
  viewer.setAttribute('data-highlight-listener-attached', 'true');
  
  viewer.addEventListener('click', function(e) {
    // Prüfe ob Klick auf ein Highlight-Element
    const highlightElement = e.target.closest('[data-highlight-id]');
    if (highlightElement && highlightElement.hasAttribute('data-highlight-id')) {
      const highlightId = highlightElement.getAttribute('data-highlight-id');
      const gaNumber = highlightElement.getAttribute('data-ga-number');
      const paragraphId = highlightElement.getAttribute('data-paragraph-id');
      
      // Wenn Attribute fehlen, versuche sie aus cachedHighlightsData zu holen
      if (!gaNumber || !paragraphId) {
        if (cachedHighlightsData && cachedHighlightsData.success && cachedHighlightsData.data) {
          const highlight = cachedHighlightsData.data.find(h => h.id === highlightId);
          if (highlight) {
            e.stopPropagation();
            e.preventDefault();
            console.log('[HIGHLIGHT-DELEGATION] Klick auf Unterstreichung:', highlight.id, highlight.ga_number, highlight.paragraph_id);
            jumpToHighlight(highlight.ga_number, highlight.paragraph_id, highlight.id);
            return;
          }
        }
      } else {
        e.stopPropagation();
        e.preventDefault();
        console.log('[HIGHLIGHT-DELEGATION] Klick auf Unterstreichung:', highlightId, gaNumber, paragraphId);
        jumpToHighlight(gaNumber, paragraphId, highlightId);
        return;
      }
    }
    
    // Prüfe ob Klick auf ein Quote-Element oder Quote-Icon
    const quoteElement = e.target.closest('[data-quote-id]');
    if (quoteElement && quoteElement.hasAttribute('data-quote-id')) {
      e.stopPropagation();
      e.preventDefault();
      const quoteId = quoteElement.getAttribute('data-quote-id');
      console.log('[QUOTE-DELEGATION] Klick auf Zitat:', quoteId);
      if (typeof jumpToQuoteById === 'function') {
        jumpToQuoteById(quoteId);
      } else {
        console.warn('[QUOTE-DELEGATION] jumpToQuoteById Funktion nicht verfügbar');
      }
      return;
    }
    
    // Prüfe ob Klick auf Bookmark-Icon im Absatz
    const bookmarkIndicator = e.target.closest('.bookmark-quote-indicator');
    if (bookmarkIndicator && bookmarkIndicator.hasAttribute('data-quote-id')) {
      e.stopPropagation();
      e.preventDefault();
      const quoteId = bookmarkIndicator.getAttribute('data-quote-id');
      console.log('[QUOTE-DELEGATION] Klick auf Bookmark-Icon:', quoteId);
      if (typeof jumpToQuoteById === 'function') {
        jumpToQuoteById(quoteId);
      } else {
        console.warn('[QUOTE-DELEGATION] jumpToQuoteById Funktion nicht verfügbar');
      }
      return;
    }
  }, true); // useCapture = true für frühe Erfassung
  
  // Event-Listener für Rechtsklick auf Highlights und Zitate im Viewer
  viewer.addEventListener('contextmenu', function(e) {
    // Prüfe ob Rechtsklick auf ein Highlight-Element
    const highlightElement = e.target.closest('[data-highlight-id]');
    if (highlightElement && highlightElement.hasAttribute('data-highlight-id')) {
      e.preventDefault();
      e.stopPropagation();
      
      const highlightId = highlightElement.getAttribute('data-highlight-id');
      
      // Zeige Kontextmenü zum Farbwechsel
      showHighlightColorContextMenu(e.clientX, e.clientY, highlightId);
      return;
    }
    
    // Prüfe ob Rechtsklick auf ein Quote-Element oder Quote-Icon
    const quoteElement = e.target.closest('[data-quote-id]');
    if (quoteElement && quoteElement.hasAttribute('data-quote-id')) {
      e.preventDefault();
      e.stopPropagation();
      
      const quoteId = quoteElement.getAttribute('data-quote-id');
      
      // Zeige Kontextmenü zum Farbwechsel
      showQuoteColorContextMenu(e.clientX, e.clientY, quoteId);
      return;
    }
    
    // Prüfe ob Rechtsklick auf Bookmark-Icon im Absatz
    const bookmarkIndicator = e.target.closest('.bookmark-quote-indicator');
    if (bookmarkIndicator && bookmarkIndicator.hasAttribute('data-quote-id')) {
      e.preventDefault();
      e.stopPropagation();
      
      const quoteId = bookmarkIndicator.getAttribute('data-quote-id');
      
      // Zeige Kontextmenü zum Farbwechsel
      showQuoteColorContextMenu(e.clientX, e.clientY, quoteId);
      return;
    }
  }, true); // useCapture = true für frühe Erfassung
  
  // Event-Listener für Linksklick auf Zitate im main-Container (falls vorhanden)
  const mainContainer = document.getElementById('main');
  if (mainContainer) {
    mainContainer.addEventListener('click', function(e) {
      // Prüfe ob Klick auf ein Quote-Element oder Quote-Icon
      const quoteElement = e.target.closest('[data-quote-id]');
      if (quoteElement && quoteElement.hasAttribute('data-quote-id')) {
        e.stopPropagation();
        e.preventDefault();
        const quoteId = quoteElement.getAttribute('data-quote-id');
        console.log('[QUOTE-DELEGATION-MAIN] Klick auf Zitat:', quoteId);
        if (typeof jumpToQuoteById === 'function') {
          jumpToQuoteById(quoteId);
        } else {
          console.warn('[QUOTE-DELEGATION-MAIN] jumpToQuoteById Funktion nicht verfügbar');
        }
        return;
      }
      
      // Prüfe ob Klick auf Bookmark-Icon im Absatz
      const bookmarkIndicator = e.target.closest('.bookmark-quote-indicator');
      if (bookmarkIndicator && bookmarkIndicator.hasAttribute('data-quote-id')) {
        e.stopPropagation();
        e.preventDefault();
        const quoteId = bookmarkIndicator.getAttribute('data-quote-id');
        console.log('[QUOTE-DELEGATION-MAIN] Klick auf Bookmark-Icon:', quoteId);
        if (typeof jumpToQuoteById === 'function') {
          jumpToQuoteById(quoteId);
        } else {
          console.warn('[QUOTE-DELEGATION-MAIN] jumpToQuoteById Funktion nicht verfügbar');
        }
        return;
      }
    }, true); // useCapture = true für frühe Erfassung
    
    mainContainer.addEventListener('contextmenu', function(e) {
      // Prüfe ob Rechtsklick auf ein Highlight-Element
      const highlightElement = e.target.closest('[data-highlight-id]');
      if (highlightElement && highlightElement.hasAttribute('data-highlight-id')) {
        e.preventDefault();
        e.stopPropagation();
        
        const highlightId = highlightElement.getAttribute('data-highlight-id');
        
        // Zeige Kontextmenü zum Farbwechsel
        showHighlightColorContextMenu(e.clientX, e.clientY, highlightId);
        return;
      }
      
      // Prüfe ob Rechtsklick auf ein Quote-Element oder Quote-Icon
      const quoteElement = e.target.closest('[data-quote-id]');
      if (quoteElement && quoteElement.hasAttribute('data-quote-id')) {
        e.preventDefault();
        e.stopPropagation();
        
        const quoteId = quoteElement.getAttribute('data-quote-id');
        
        // Zeige Kontextmenü zum Farbwechsel
        showQuoteColorContextMenu(e.clientX, e.clientY, quoteId);
        return;
      }
      
      // Prüfe ob Rechtsklick auf Bookmark-Icon im Absatz
      const bookmarkIndicator = e.target.closest('.bookmark-quote-indicator');
      if (bookmarkIndicator && bookmarkIndicator.hasAttribute('data-quote-id')) {
        e.preventDefault();
        e.stopPropagation();
        
        const quoteId = bookmarkIndicator.getAttribute('data-quote-id');
        
        // Zeige Kontextmenü zum Farbwechsel
        showQuoteColorContextMenu(e.clientX, e.clientY, quoteId);
        return;
      }
    }, true); // useCapture = true für frühe Erfassung
  }
  
  // Event-Listener für Rechtsklick auf Zitate im Viewer
  viewer.addEventListener('contextmenu', function(e) {
    // Prüfe ob Rechtsklick auf ein Quote-Element oder Quote-Icon
    const quoteElement = e.target.closest('[data-quote-id]');
    if (quoteElement && quoteElement.hasAttribute('data-quote-id')) {
      e.preventDefault();
      e.stopPropagation();
      
      const quoteId = quoteElement.getAttribute('data-quote-id');
      
      // Zeige Kontextmenü zum Farbwechsel
      showQuoteColorContextMenu(e.clientX, e.clientY, quoteId);
      return;
    }
    
    // Prüfe ob Rechtsklick auf Bookmark-Icon im Absatz
    const bookmarkIndicator = e.target.closest('.bookmark-quote-indicator');
    if (bookmarkIndicator && bookmarkIndicator.hasAttribute('data-quote-id')) {
      e.preventDefault();
      e.stopPropagation();
      
      const quoteId = bookmarkIndicator.getAttribute('data-quote-id');
      
      // Zeige Kontextmenü zum Farbwechsel
      showQuoteColorContextMenu(e.clientX, e.clientY, quoteId);
      return;
    }
  }, true); // useCapture = true für frühe Erfassung
  
  highlightDelegationListenerAttached = true;
  console.log('[ATTACH-LISTENERS] Event-Delegation-Listener angehängt');
}

function attachClickListenersToHighlights(gaNumber) {
  console.log('[ATTACH-LISTENERS] Starte für GA:', gaNumber);
  
  // Stelle sicher, dass Event-Delegation aktiviert ist
  attachHighlightDelegationListener();
  
  if (!cachedHighlightsData || !cachedHighlightsData.success || !cachedHighlightsData.data) {
    console.log('[ATTACH-LISTENERS] Keine Highlight-Daten verfügbar');
    return;
  }
  
  const highlights = cachedHighlightsData.data.filter(h => h.ga_number === gaNumber);
  console.log('[ATTACH-LISTENERS] Gefundene Highlights:', highlights.length);
  
  highlights.forEach(highlight => {
    const highlightElement = document.querySelector(`[data-highlight-id="${highlight.id}"]`);
    console.log('[ATTACH-LISTENERS] Prüfe Highlight', highlight.id, 'Element gefunden:', !!highlightElement, 'Listener vorhanden:', highlightElement?.hasAttribute('data-listener-attached'));
    
    if (highlightElement) {
      // Setze zusätzliche Attribute für Event-Delegation
      highlightElement.setAttribute('data-ga-number', highlight.ga_number);
      highlightElement.setAttribute('data-paragraph-id', highlight.paragraph_id);
      
      // Entferne alte Event-Listener falls vorhanden (durch Klonen des Elements)
      if (highlightElement.hasAttribute('data-listener-attached')) {
        // Erstelle neues Element ohne Event-Listener
        const newSpan = document.createElement('span');
        newSpan.className = highlightElement.className;
        newSpan.innerHTML = highlightElement.innerHTML;
        Array.from(highlightElement.attributes).forEach(attr => {
          if (attr.name !== 'data-listener-attached') {
            newSpan.setAttribute(attr.name, attr.value);
          }
        });
        // Kopiere Styles
        newSpan.style.cssText = highlightElement.style.cssText;
        highlightElement.parentNode.replaceChild(newSpan, highlightElement);
        // Verwende das neue Element
        const updatedElement = document.querySelector(`[data-highlight-id="${highlight.id}"]`);
        if (updatedElement) {
          updatedElement.addEventListener('click', function(e) {
            e.stopPropagation();
            e.preventDefault();
            console.log('[HIGHLIGHT] Klick auf Unterstreichung (attachClickListenersToHighlights):', highlight.id, highlight.ga_number, highlight.paragraph_id);
            jumpToHighlight(highlight.ga_number, highlight.paragraph_id, highlight.id);
          });
          updatedElement.setAttribute('data-listener-attached', 'true');
          updatedElement.setAttribute('data-ga-number', highlight.ga_number);
          updatedElement.setAttribute('data-paragraph-id', highlight.paragraph_id);
          updatedElement.style.setProperty('cursor', 'pointer', 'important');
          updatedElement.setAttribute('title', 'Klicken zum Öffnen im Member Panel');
          console.log('[ATTACH-LISTENERS] Event-Listener für Highlight', highlight.id, 'hinzugefügt (ersetzt)');
        }
      } else {
        highlightElement.addEventListener('click', function(e) {
          e.stopPropagation();
          e.preventDefault();
          console.log('[HIGHLIGHT] Klick auf Unterstreichung (attachClickListenersToHighlights):', highlight.id, highlight.ga_number, highlight.paragraph_id);
          jumpToHighlight(highlight.ga_number, highlight.paragraph_id, highlight.id);
        });
        highlightElement.setAttribute('data-listener-attached', 'true');
        highlightElement.setAttribute('data-ga-number', highlight.ga_number);
        highlightElement.setAttribute('data-paragraph-id', highlight.paragraph_id);
        highlightElement.style.setProperty('cursor', 'pointer', 'important');
        if (!highlightElement.getAttribute('title')) {
          highlightElement.setAttribute('title', 'Klicken zum Öffnen im Member Panel');
        }
        console.log('[ATTACH-LISTENERS] Event-Listener für Highlight', highlight.id, 'hinzugefügt');
      }
    } else {
      console.warn('[ATTACH-LISTENERS] Highlight-Element nicht gefunden für Highlight', highlight.id);
    }
  });
  
  console.log('[ATTACH-LISTENERS] Abgeschlossen für GA:', gaNumber);
}

/**
 * Hilfsfunktion: Extrahiert Text-Inhalt ohne vorhandene Highlight-Spans
 * Dies ist wichtig, um Offsets korrekt zu berechnen, wenn bereits Highlights vorhanden sind
 */
function getTextContentWithoutHighlights(element) {
  if (!element) return '';
  
  // Klone das Element, um es zu modifizieren
  const clone = element.cloneNode(true);
  
  // Entferne alle Highlight-Spans aus dem Klon
  const highlightSpans = clone.querySelectorAll('[data-highlight-id]');
  highlightSpans.forEach(span => {
    const parent = span.parentNode;
    if (parent) {
      // Ersetze den Span durch seinen Text-Inhalt
      while (span.firstChild) {
        parent.insertBefore(span.firstChild, span);
      }
      parent.removeChild(span);
    }
  });
  
  return clone.textContent || '';
}

/**
 * Hilfsfunktion: Wendet Unterstreichung auf ein Element an (vereinheitlicht für Bücher und Vorträge)
 */
function applyHighlightToElement(targetElement, highlight) {
  if (!targetElement) {
    console.warn('[HIGHLIGHT] targetElement ist null');
    return;
  }
  
  console.log('[HIGHLIGHT] applyHighlightToElement aufgerufen:', {
    highlightId: highlight.id,
    paragraphId: highlight.paragraph_id,
    gaNumber: highlight.ga_number,
    targetElement: targetElement.tagName,
    targetElementText: targetElement.textContent?.substring(0, 100)
  });
  
  // Prüfe ob bereits unterstrichen
  const existingHighlight = targetElement.querySelector(`[data-highlight-id="${highlight.id}"]`);
  if (existingHighlight) {
    console.log('[HIGHLIGHT] Bereits vorhanden, prüfe Event-Listener');
    // Stelle sicher, dass Event-Listener vorhanden ist
    if (!existingHighlight.hasAttribute('data-listener-attached')) {
      existingHighlight.addEventListener('click', function(e) {
        e.stopPropagation();
        e.preventDefault();
        console.log('[HIGHLIGHT] Klick auf Unterstreichung (nachträglich):', highlight.id, highlight.ga_number, highlight.paragraph_id);
        jumpToHighlight(highlight.ga_number, highlight.paragraph_id, highlight.id);
      });
      existingHighlight.setAttribute('data-listener-attached', 'true');
      console.log('[HIGHLIGHT] Event-Listener nachträglich hinzugefügt');
    }
    return; // Bereits vorhanden
  }
  
  // Hole den Text OHNE vorhandene Highlights (für die Suche)
  const elementTextWithoutHighlights = getTextContentWithoutHighlights(targetElement);
  
  console.log('[HIGHLIGHT] Element-Text (ohne Highlights):', elementTextWithoutHighlights ? elementTextWithoutHighlights.substring(0, 200) : '(leer)');
  console.log('[HIGHLIGHT] Gespeicherter Text:', highlight.paragraph_text?.substring(0, 200));
  console.log('[HIGHLIGHT] Offsets:', highlight.text_start_offset, highlight.text_end_offset);
  
  // Prüfe ob elementText leer ist
  if (!elementTextWithoutHighlights || elementTextWithoutHighlights.length === 0) {
    console.warn('[HIGHLIGHT] Element-Text ist leer, kann Unterstreichung nicht anwenden');
    return;
  }
  
  // Verwende den gespeicherten Text, um die Position zu finden
  // Das ist viel einfacher und robuster als die Offset-Berechnung
  if (highlight.paragraph_text && highlight.text_start_offset !== null && highlight.text_end_offset !== null) {
    const textToHighlight = highlight.paragraph_text.substring(
      highlight.text_start_offset,
      highlight.text_end_offset
    );
    
    // Prüfe ob textToHighlight gültig ist
    if (!textToHighlight || textToHighlight.length === 0) {
      console.warn('[HIGHLIGHT] textToHighlight ist leer, kann Unterstreichung nicht anwenden');
      return;
    }
    
    // Verwende Text ohne Highlights für die Suche
    if (elementTextWithoutHighlights && elementTextWithoutHighlights.includes(textToHighlight)) {
      // Erstelle Range für die Unterstreichung (mehrzeilig unterstützt)
      // Prüfe ob bereits andere Highlights vorhanden sind
      const existingOtherHighlights = targetElement.querySelectorAll(`[data-highlight-id]:not([data-highlight-id="${highlight.id}"])`);
      const hasOtherHighlights = existingOtherHighlights.length > 0;
      
      const range = document.createRange();
      const walker = document.createTreeWalker(
        targetElement,
        NodeFilter.SHOW_TEXT,
        hasOtherHighlights ? {
          acceptNode: function(node) {
            // Überspringe Text-Knoten, die innerhalb von anderen Highlight-Spans sind
            let parent = node.parentNode;
            while (parent && parent !== targetElement) {
              if (parent.hasAttribute && parent.hasAttribute('data-highlight-id')) {
                const highlightId = parent.getAttribute('data-highlight-id');
                if (highlightId !== highlight.id) {
                  return NodeFilter.FILTER_REJECT;
                }
              }
              parent = parent.parentNode;
            }
            return NodeFilter.FILTER_ACCEPT;
          }
        } : null, // Kein Filter wenn keine anderen Highlights vorhanden sind
        false
      );
      
      // Suche nach dem Text über mehrere Knoten hinweg
      // Sammle alle Text-Knoten und ihren akkumulierten Offset
      const textNodes = [];
      let accumulatedOffset = 0;
      let node;
      
      while (node = walker.nextNode()) {
        const nodeText = node.textContent;
        textNodes.push({
          node: node,
          startOffset: accumulatedOffset,
          endOffset: accumulatedOffset + nodeText.length,
          text: nodeText
        });
        accumulatedOffset += nodeText.length;
      }
      
      // Finde die Position des Textes im akkumulierten Text
      const fullText = textNodes.map(n => n.text).join('');
      const textIndex = fullText.indexOf(textToHighlight);
      
      if (textIndex !== -1) {
        const textEndIndex = textIndex + textToHighlight.length;
        
        // Finde Start- und End-Knoten basierend auf den Offsets
        let startNode = null;
        let startOffsetInNode = 0;
        let endNode = null;
        let endOffsetInNode = 0;
        
        for (const textNodeInfo of textNodes) {
          // Prüfe ob Start in diesem Knoten liegt
          if (!startNode && textIndex >= textNodeInfo.startOffset && textIndex < textNodeInfo.endOffset) {
            startNode = textNodeInfo.node;
            startOffsetInNode = textIndex - textNodeInfo.startOffset;
          }
          
          // Prüfe ob Ende in diesem Knoten liegt
          if (textEndIndex > textNodeInfo.startOffset && textEndIndex <= textNodeInfo.endOffset) {
            endNode = textNodeInfo.node;
            endOffsetInNode = textEndIndex - textNodeInfo.startOffset;
            break;
          }
        }
        
        // Fallback: Wenn nicht gefunden, versuche einfache Suche innerhalb eines Knotens
        if (!startNode || !endNode) {
          // Erstelle neuen Walker für Fallback
          const existingOtherHighlightsFallback = targetElement.querySelectorAll(`[data-highlight-id]:not([data-highlight-id="${highlight.id}"])`);
          const hasOtherHighlightsFallback = existingOtherHighlightsFallback.length > 0;
          
          const fallbackWalker = document.createTreeWalker(
            targetElement,
            NodeFilter.SHOW_TEXT,
            hasOtherHighlightsFallback ? {
              acceptNode: function(node) {
                let parent = node.parentNode;
                while (parent && parent !== targetElement) {
                  if (parent.hasAttribute && parent.hasAttribute('data-highlight-id')) {
                    const highlightId = parent.getAttribute('data-highlight-id');
                    if (highlightId !== highlight.id) {
                      return NodeFilter.FILTER_REJECT;
                    }
                  }
                  parent = parent.parentNode;
                }
                return NodeFilter.FILTER_ACCEPT;
              }
            } : null, // Kein Filter wenn keine anderen Highlights vorhanden sind
            false
          );
          
          while (node = fallbackWalker.nextNode()) {
            const nodeText = node.textContent;
            const index = nodeText.indexOf(textToHighlight);
            
            if (index !== -1) {
              startNode = node;
              startOffsetInNode = index;
              endNode = node;
              endOffsetInNode = index + textToHighlight.length;
              break;
            }
          }
        }
        
        if (startNode && endNode) {
          try {
            range.setStart(startNode, startOffsetInNode);
            range.setEnd(endNode, endOffsetInNode);
            
            const highlightColor = getHighlightColor(highlight.color || 'blue');
            const span = document.createElement('span');
            span.className = 'member-highlight';
            span.style.setProperty('text-decoration', 'underline', 'important');
            span.style.setProperty('text-decoration-color', highlightColor, 'important');
            span.style.setProperty('-webkit-text-decoration-color', highlightColor, 'important');
            span.style.setProperty('text-decoration-thickness', '1.5px', 'important');
            span.style.setProperty('cursor', 'pointer', 'important');
            span.setAttribute('data-highlight-id', highlight.id);
            span.setAttribute('data-highlight', 'true');
            span.setAttribute('data-highlight-color', highlight.color || 'blue');
            span.setAttribute('data-ga-number', highlight.ga_number);
            span.setAttribute('data-paragraph-id', highlight.paragraph_id);
            span.setAttribute('title', 'Klicken zum Öffnen im Member Panel');
            span.setAttribute('data-listener-attached', 'true');
            
            span.addEventListener('click', function(e) {
              e.stopPropagation();
              e.preventDefault();
              console.log('[HIGHLIGHT] Klick auf Unterstreichung:', highlight.id, highlight.ga_number, highlight.paragraph_id);
              jumpToHighlight(highlight.ga_number, highlight.paragraph_id, highlight.id);
            });
            
            const contents = range.extractContents();
            span.appendChild(contents);
            range.insertNode(span);
            console.log('[HIGHLIGHT] Unterstreichung erfolgreich angewendet (mit Text-Suche)');
            return;
          } catch (e) {
            console.error('[HIGHLIGHT] Fehler beim Anwenden der Unterstreichung (mit Text-Suche):', e);
          }
        }
      }
    }
  }
}

/**
 * Entfernt alle Zitat-Markierungen (beim Klick auf ein neues Zitat)
 * Analog zu Unterstreichungen: nur eine Markierung gleichzeitig sichtbar
 */
function removeAllQuoteHighlights() {
  // Entferne normale Zitat-Spans
  const allQuoteHighlights = document.querySelectorAll('[data-quote="true"]:not([data-quote-overlay-marker])');
  allQuoteHighlights.forEach(span => {
    if (span.parentNode) {
      const parent = span.parentNode;
      while (span.firstChild) {
        parent.insertBefore(span.firstChild, span);
      }
      parent.removeChild(span);
    }
  });
  
  // Entferne Overlay-Marker
  const overlayMarkers = document.querySelectorAll('[data-quote-overlay-marker]');
  overlayMarkers.forEach(marker => {
    if (marker.parentNode) {
      marker.parentNode.removeChild(marker);
    }
  });
  
  // NICHT mehr entfernen: Senkrechte Linien sollen dauerhaft angezeigt werden
  // Die Linien werden beim Laden des Vortrags erstellt und bleiben sichtbar
  // const verticalLines = document.querySelectorAll('.member-quote-vertical-line');
  // verticalLines.forEach(line => {
  //   if (line.parentNode) {
  //     line.parentNode.removeChild(line);
  //   }
  // });
  
  // Entferne Hintergrundfarbe von Unterstreichungen, die als Overlay markiert sind
  const overlayHighlights = document.querySelectorAll('[data-quote-overlay]');
  overlayHighlights.forEach(highlight => {
    highlight.style.removeProperty('background-color');
    highlight.removeAttribute('data-quote-overlay');
  });
  
  console.log('[QUOTE-HIGHLIGHT] Alle Zitat-Markierungen entfernt');
}

/**
 * Erstellt eine senkrechte Linie rechts neben dem Absatz für ein Zitat
 * @param {HTMLElement} targetElement - Der Absatz-Container
 * @param {Range} range - Die Range des Zitats
 * @param {Object} quote - Das Quote-Objekt
 */
function createQuoteVerticalLine(targetElement, range, quote) {
  if (!targetElement || !range) return null;
  
  try {
    // Stelle sicher, dass targetElement relativ positioniert ist
    const computedStyle = window.getComputedStyle(targetElement);
    if (computedStyle.position === 'static') {
      targetElement.style.position = 'relative';
    }
    
    // Berechne Position des Zitats relativ zum Container
    const rangeRect = range.getBoundingClientRect();
    const containerRect = targetElement.getBoundingClientRect();
    
    // Berechne relative Position innerhalb des Containers (ohne Scroll-Offset)
    const topOffset = rangeRect.top - containerRect.top;
    const bottomOffset = rangeRect.bottom - containerRect.top;
    const lineHeight = bottomOffset - topOffset;
    
    // Hole Quote-Farbe
    const quoteColor = quote.marker_color || 'blue';
    const quoteColorHex = getHighlightColor(quoteColor);
    
    // Prüfe ob bereits eine Linie für dieses Zitat existiert
    const existingLine = targetElement.querySelector(`.member-quote-vertical-line[data-quote-id="${quote.id}"]`);
    if (existingLine) {
      // Aktualisiere bestehende Linie
      existingLine.style.top = `${topOffset}px`;
      existingLine.style.height = `${Math.max(lineHeight, 1)}px`;
      existingLine.style.backgroundColor = quoteColorHex;
      existingLine.style.left = '-5px';
      existingLine.style.width = '1.5px';
      existingLine.setAttribute('data-quote-color', quoteColor);
      return existingLine;
    }
    
    // Erstelle Linien-Element
    const lineElement = document.createElement('div');
    lineElement.className = 'member-quote-vertical-line';
    lineElement.setAttribute('data-quote-id', quote.id);
    lineElement.setAttribute('data-quote', 'true');
    lineElement.setAttribute('data-quote-color', quoteColor);
    lineElement.style.position = 'absolute';
    lineElement.style.left = '-5px';
    lineElement.style.top = `${topOffset}px`;
    lineElement.style.width = '1.5px';
    lineElement.style.height = `${Math.max(lineHeight, 1)}px`;
    lineElement.style.backgroundColor = quoteColorHex;
    lineElement.style.cursor = 'pointer';
    lineElement.style.zIndex = '10';
    lineElement.title = 'Klick zum Zitat im Members Panel';
    
    // Klick-Handler: Öffne Members Panel und scrolle zum Zitat
    lineElement.onclick = (e) => {
      e.stopPropagation();
      e.preventDefault();
      if (typeof jumpToQuoteById === 'function') {
        jumpToQuoteById(quote.id);
      }
    };
    
    // Füge Linie zum Container hinzu
    targetElement.appendChild(lineElement);
    
    console.log('[QUOTE-LINE] Senkrechte Linie erstellt:', {
      top: topOffset,
      height: lineHeight,
      color: quoteColorHex
    });
    
    return lineElement;
  } catch (e) {
    console.error('[QUOTE-LINE] Fehler beim Erstellen der Linie:', e);
    return null;
  }
}

/**
 * Wendet eine gespeicherte Zitat-Linie beim Laden des Vortrags an
 * @param {Object} quote - Das Quote-Objekt aus der Datenbank
 */
function applyStoredQuoteLine(quote) {
  try {
    if (!quote.paragraph_id || quote.text_start_offset === null || quote.text_start_offset === undefined) {
      return; // Nicht genug Daten für Linien-Positionierung
    }
    
    // Normalisiere paragraph_id: Entferne ^ am Anfang falls vorhanden (für Bücher)
    const normalizedParaId = String(quote.paragraph_id || '').replace(/^\^/, '');
    let paraElement = document.getElementById(`para-${normalizedParaId}`);
    
    // Falls nicht gefunden, versuche mit Original-ID
    if (!paraElement) {
      paraElement = document.getElementById(`para-${quote.paragraph_id}`);
    }
    
    // Falls immer noch nicht gefunden, versuche für Bücher mit data-index
    if (!paraElement) {
      const bookParaElement = document.querySelector(`[data-index="${quote.paragraph_id}"], [data-index="^${normalizedParaId}"]`);
      if (bookParaElement) {
        paraElement = bookParaElement;
      }
    }
    
    if (!paraElement) {
      return; // Paragraph nicht gefunden
    }
    
    // Finde das tatsächliche Text-Element
    let targetElement = paraElement;
    
    // Wenn paraElement versteckt ist oder ein span, suche nach dem Parent-Element mit Text
    if (paraElement.style.display === 'none' || paraElement.tagName.toLowerCase() === 'span') {
      let parent = paraElement.parentElement;
      while (parent && parent !== document.body) {
        const tagName = parent.tagName.toLowerCase();
        if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
          targetElement = parent;
          break;
        }
        parent = parent.parentElement;
      }
    }
    
    // Stelle sicher, dass targetElement relativ positioniert ist
    const computedStyle = window.getComputedStyle(targetElement);
    if (computedStyle.position === 'static') {
      targetElement.style.position = 'relative';
    }
    
    // Prüfe ob bereits eine Linie für dieses Zitat existiert
    const existingLine = targetElement.querySelector(`.member-quote-vertical-line[data-quote-id="${quote.id}"]`);
    if (existingLine) {
      return; // Bereits vorhanden
    }
    
    // Berechne Position basierend auf text_start_offset und text_end_offset
    const textStartOffset = quote.text_start_offset;
    const textEndOffset = quote.text_end_offset || (textStartOffset + (quote.quote_text ? quote.quote_text.length : 50));
    
    // Erstelle Range für die Position
    const walker = document.createTreeWalker(
      targetElement,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    let currentOffset = 0;
    let startNode = null;
    let startOffset = 0;
    let endNode = null;
    let endOffset = 0;
    let node;
    
    while (node = walker.nextNode()) {
      const nodeLength = node.textContent.length;
      
      // Finde Start-Knoten
      if (!startNode && currentOffset + nodeLength > textStartOffset) {
        startNode = node;
        startOffset = textStartOffset - currentOffset;
      }
      
      // Finde End-Knoten
      if (currentOffset + nodeLength >= textEndOffset) {
        endNode = node;
        endOffset = Math.min(textEndOffset - currentOffset, nodeLength);
        break;
      }
      
      currentOffset += nodeLength;
    }
    
    if (!startNode) {
      return; // Start-Position nicht gefunden
    }
    
    // Falls kein End-Knoten gefunden wurde, verwende den Start-Knoten
    if (!endNode) {
      endNode = startNode;
      endOffset = startNode.textContent.length;
    }
    
    try {
      // Erstelle Range
      const range = document.createRange();
      range.setStart(startNode, Math.min(startOffset, startNode.textContent.length));
      range.setEnd(endNode, Math.min(endOffset, endNode.textContent.length));
      
      // Erstelle die senkrechte Linie
      createQuoteVerticalLine(targetElement, range, quote);
      
      // Prüfe ob bereits ein klickbarer Span für dieses Zitat existiert
      const existingSpan = targetElement.querySelector(`.quote-text-link[data-quote-id="${quote.id}"]`);
      if (!existingSpan) {
        // Umschließe den Zitattext mit einem klickbaren Span
        try {
          const quoteSpan = document.createElement('span');
          quoteSpan.className = 'quote-text-link';
          quoteSpan.setAttribute('data-quote-id', quote.id);
          quoteSpan.style.cursor = 'pointer';
          quoteSpan.title = 'Klick zum Zitat im Members Panel';
          
          // Klick-Handler
          quoteSpan.onclick = (e) => {
            e.stopPropagation();
            if (typeof jumpToQuoteById === 'function') {
              jumpToQuoteById(quote.id);
            }
          };
          
          // Umschließe den Range-Inhalt mit dem Span
          range.surroundContents(quoteSpan);
        } catch (spanError) {
          // Falls surroundContents fehlschlägt (z.B. bei übergreifenden Elementen),
          // ignoriere still - die senkrechte Linie ist weiterhin klickbar
          console.warn('[STORED-QUOTE-LINE] Text-Link konnte nicht erstellt werden:', spanError.message);
        }
      }
    } catch (e) {
      console.warn('[STORED-QUOTE-LINE] Fehler beim Erstellen der Range:', e);
    }
    
  } catch (e) {
    console.error('[STORED-QUOTE-LINE] Fehler:', e);
  }
}

/**
 * Wendet Zitat-Hervorhebung auf ein Element an (senkrechte Linie rechts neben Absatz)
 * WICHTIG: Diese Markierung ist TEMPORÄR und wird nur beim Klick angezeigt
 */
function applyQuoteHighlightToElement(targetElement, quote) {
  if (!targetElement) {
    console.warn('[QUOTE-HIGHLIGHT] targetElement ist null');
    return;
  }
  
  // WICHTIG: Prüfe ZUERST ob dieses Zitat bereits hervorgehoben ist
  const existingQuoteHighlight = document.querySelector(`[data-quote-id="${quote.id}"][data-quote="true"]`);
  if (existingQuoteHighlight) {
    console.log('[QUOTE-HIGHLIGHT] Bereits vorhanden, überspringe');
    return; // Bereits vorhanden - nichts tun
  }
  
  // Entferne alle vorherigen Zitat-Markierungen (nur wenn wir ein neues anwenden)
  removeAllQuoteHighlights();
  
  console.log('[QUOTE-HIGHLIGHT] applyQuoteHighlightToElement aufgerufen:', {
    quoteId: quote.id,
    paragraphId: quote.paragraph_id,
    gaReference: quote.ga_reference,
    targetElement: targetElement.tagName,
    targetElementText: targetElement.textContent?.substring(0, 100)
  });
  
  // Hole den Text OHNE vorhandene Highlights/Quotes (für die Suche)
  const elementTextWithoutHighlights = getTextContentWithoutHighlights(targetElement);
  
  console.log('[QUOTE-HIGHLIGHT] Element-Text (ohne Highlights):', elementTextWithoutHighlights ? elementTextWithoutHighlights.substring(0, 200) : '(leer)');
  console.log('[QUOTE-HIGHLIGHT] Gespeicherter Text:', quote.paragraph_text?.substring(0, 200));
  console.log('[QUOTE-HIGHLIGHT] Offsets:', quote.text_start_offset, quote.text_end_offset);
  
  // Prüfe ob elementText leer ist
  if (!elementTextWithoutHighlights || elementTextWithoutHighlights.length === 0) {
    console.warn('[QUOTE-HIGHLIGHT] Element-Text ist leer, kann Hervorhebung nicht anwenden');
    return;
  }
  
  // WICHTIG: Verwende den exakten quote_text, der im MB gespeichert ist
  // Das ist der Text, den der Benutzer ursprünglich markiert hat
  let textToHighlight = quote.quote_text;
  
  // Fallback 1: Falls quote_text nicht verfügbar ist, verwende paragraph_text mit Offsets
  if (!textToHighlight && quote.paragraph_text && quote.text_start_offset !== null && quote.text_end_offset !== null) {
    textToHighlight = quote.paragraph_text.substring(
      quote.text_start_offset,
      quote.text_end_offset
    );
  }
  
  // Kein Fallback mehr mit context_before - verwende nur quote_text für die Suche
  // Die exakten Offsets sollten vorhanden sein (nach Migration)
  
  // Prüfe ob textToHighlight gültig ist
  if (!textToHighlight || textToHighlight.length === 0) {
    console.warn('[QUOTE-HIGHLIGHT] textToHighlight ist leer, kann Hervorhebung nicht anwenden');
    return;
  }
  
  console.log('[QUOTE-HIGHLIGHT] Suche nach exaktem quote_text:', textToHighlight.substring(0, 100));
  console.log('[QUOTE-HIGHLIGHT] Element-Text Länge:', elementTextWithoutHighlights.length);
  
  // Verwende Text ohne Highlights für die Suche
  // Versuche zuerst exakte Übereinstimmung mit dem gespeicherten quote_text
  if (elementTextWithoutHighlights && elementTextWithoutHighlights.includes(textToHighlight)) {
    // Erstelle Range für die Hervorhebung (mehrzeilig unterstützt)
    // WICHTIG: Akzeptiere ALLE Text-Knoten, auch die in Unterstreichungen
    // So können Zitate und Unterstreichungen überlappen (doppelte Markierung)
    
    const range = document.createRange();
    const walker = document.createTreeWalker(
        targetElement,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode: function(node) {
            // Nur andere Zitate ablehnen, Unterstreichungen erlauben
            let parent = node.parentNode;
            while (parent && parent !== targetElement) {
              if (parent.hasAttribute && parent.hasAttribute('data-quote-id')) {
                const quoteId = parent.getAttribute('data-quote-id');
                if (quoteId && quoteId !== quote.id) {
                  return NodeFilter.FILTER_REJECT;
                }
              }
              parent = parent.parentNode;
            }
            return NodeFilter.FILTER_ACCEPT;
          }
        },
        false
    );
    
    // Suche nach dem Text über mehrere Knoten hinweg
    // Sammle alle Text-Knoten und ihren akkumulierten Offset
    const textNodes = [];
    let accumulatedOffset = 0;
    let node;
    
    while (node = walker.nextNode()) {
      const nodeText = node.textContent;
      textNodes.push({
        node: node,
        startOffset: accumulatedOffset,
        endOffset: accumulatedOffset + nodeText.length,
        text: nodeText
      });
      accumulatedOffset += nodeText.length;
    }
    
    // Finde die Position des Textes im akkumulierten Text
    const fullText = textNodes.map(n => n.text).join('');
    const textIndex = fullText.indexOf(textToHighlight);
    
    if (textIndex !== -1) {
      const textEndIndex = textIndex + textToHighlight.length;
      
      // Finde Start- und End-Knoten basierend auf den Offsets
      let startNode = null;
      let startOffsetInNode = 0;
      let endNode = null;
      let endOffsetInNode = 0;
      
      for (const textNodeInfo of textNodes) {
        // Prüfe ob Start in diesem Knoten liegt
        if (!startNode && textIndex >= textNodeInfo.startOffset && textIndex < textNodeInfo.endOffset) {
          startNode = textNodeInfo.node;
          startOffsetInNode = textIndex - textNodeInfo.startOffset;
        }
        
        // Prüfe ob Ende in diesem Knoten liegt
        if (textEndIndex > textNodeInfo.startOffset && textEndIndex <= textNodeInfo.endOffset) {
          endNode = textNodeInfo.node;
          endOffsetInNode = textEndIndex - textNodeInfo.startOffset;
          break;
        }
      }
      
      // Fallback: Wenn nicht gefunden, versuche einfache Suche innerhalb eines Knotens
      if (!startNode || !endNode) {
        // Erstelle neuen Walker für Fallback - akzeptiere auch Text in Unterstreichungen
        const fallbackWalker = document.createTreeWalker(
          targetElement,
          NodeFilter.SHOW_TEXT,
          {
            acceptNode: function(node) {
              // Nur andere Zitate ablehnen, Unterstreichungen erlauben
              let parent = node.parentNode;
              while (parent && parent !== targetElement) {
                if (parent.hasAttribute && parent.hasAttribute('data-quote-id')) {
                  const quoteId = parent.getAttribute('data-quote-id');
                  if (quoteId && quoteId !== quote.id) {
                    return NodeFilter.FILTER_REJECT;
                  }
                }
                parent = parent.parentNode;
              }
              return NodeFilter.FILTER_ACCEPT;
            }
          },
          false
        );
        
        while (node = fallbackWalker.nextNode()) {
          const nodeText = node.textContent;
          const index = nodeText.indexOf(textToHighlight);
          
          if (index !== -1) {
            startNode = node;
            startOffsetInNode = index;
            endNode = node;
            endOffsetInNode = index + textToHighlight.length;
            break;
          }
        }
      }
      
      if (startNode && endNode) {
        try {
          range.setStart(startNode, startOffsetInNode);
          range.setEnd(endNode, endOffsetInNode);
          
          // Prüfe ob der Range über Unterstreichungen geht
          const rangeContents = range.cloneContents();
          const hasHighlightsInRange = rangeContents.querySelectorAll('[data-highlight-id]').length > 0;
          
          if (hasHighlightsInRange) {
            // SPEZIALFALL: Range enthält Unterstreichungen
            // Wende Hintergrundfarbe auf alle betroffenen Elemente an
            console.log('[QUOTE-HIGHLIGHT] Range enthält Unterstreichungen, wende gemischte Markierung an');
            
            // Finde alle Text-Knoten im Range und ihre Parent-Elemente
            const nodesToProcess = [];
            for (const textNodeInfo of textNodes) {
              const nodeStart = textNodeInfo.startOffset;
              const nodeEnd = textNodeInfo.endOffset;
              
              // Prüfe ob dieser Knoten im Zitat-Bereich liegt
              if (nodeEnd > textIndex && nodeStart < textEndIndex) {
                // Berechne welcher Teil des Knotens im Zitat liegt
                const quoteStartInNode = Math.max(0, textIndex - nodeStart);
                const quoteEndInNode = Math.min(textNodeInfo.text.length, textEndIndex - nodeStart);
                nodesToProcess.push({
                  ...textNodeInfo,
                  quoteStartInNode,
                  quoteEndInNode
                });
              }
            }
            
            // Sammle Knoten, die nicht in Unterstreichungen sind (müssen gewrappt werden)
            const nodesToWrap = [];
            
            // Für jeden betroffenen Knoten
            for (const nodeInfo of nodesToProcess) {
              const node = nodeInfo.node;
              let parent = node.parentNode;
              
              // Prüfe ob der Knoten in einer Unterstreichung ist
              let highlightParent = null;
              while (parent && parent !== targetElement) {
                if (parent.hasAttribute && parent.hasAttribute('data-highlight-id')) {
                  highlightParent = parent;
                  break;
                }
                parent = parent.parentNode;
              }
              
              if (highlightParent) {
                // Markiere Unterstreichung als Quote-Overlay
                highlightParent.setAttribute('data-quote-overlay', quote.id);
                highlightParent.setAttribute('data-quote-color', quote.marker_color || 'blue');
                console.log('[QUOTE-HIGHLIGHT] Quote-Overlay zu Unterstreichung hinzugefügt');
              } else {
                // Knoten ist NICHT in einer Unterstreichung -> muss gewrappt werden
                nodesToWrap.push(nodeInfo);
              }
            }
            
            // Wrappe alle nicht-unterstrichenen Knoten im Zitat-Bereich
            // WICHTIG: Von hinten nach vorne, um Offset-Probleme zu vermeiden
            nodesToWrap.reverse();
            for (const nodeInfo of nodesToWrap) {
              const node = nodeInfo.node;
              const quoteStart = nodeInfo.quoteStartInNode;
              const quoteEnd = nodeInfo.quoteEndInNode;
              
              try {
                // Erstelle einen Range für den Zitat-Teil dieses Knotens
                const nodeRange = document.createRange();
                nodeRange.setStart(node, quoteStart);
                nodeRange.setEnd(node, quoteEnd);
                
                const span = document.createElement('span');
                span.className = 'member-quote-highlight';
                span.setAttribute('data-quote-id', quote.id);
                span.setAttribute('data-quote', 'true');
                span.setAttribute('data-quote-part', 'true');
                span.setAttribute('data-ga-reference', quote.ga_reference);
                span.setAttribute('data-paragraph-id', quote.paragraph_id);
                span.setAttribute('data-quote-color', quote.marker_color || 'blue');
                
                nodeRange.surroundContents(span);
                console.log('[QUOTE-HIGHLIGHT] Nicht-unterstrichenen Teil gewrappt');
              } catch (e) {
                console.warn('[QUOTE-HIGHLIGHT] Konnte Knoten nicht wrappen:', e);
              }
            }
            
            // Erstelle senkrechte Linie rechts neben dem Absatz für das gesamte Zitat
            // Verwende die ursprüngliche Range für die Linienposition
            const originalRange = document.createRange();
            originalRange.setStart(startNode, startOffsetInNode);
            originalRange.setEnd(endNode, endOffsetInNode);
            createQuoteVerticalLine(targetElement, originalRange, quote);
            
            console.log('[QUOTE-HIGHLIGHT] Zitat-Hervorhebung mit gemischter Markierung erfolgreich angewendet');
            return;
          }
          
          // Normaler Fall: Keine Unterstreichungen im Range
          // Wrappe Text mit span (ohne border-right)
          const span = document.createElement('span');
          span.className = 'member-quote-highlight';
          span.setAttribute('data-quote-id', quote.id);
          span.setAttribute('data-quote', 'true');
          span.setAttribute('data-ga-reference', quote.ga_reference);
          span.setAttribute('data-paragraph-id', quote.paragraph_id);
          span.setAttribute('data-quote-color', quote.marker_color || 'blue');
          
          const contents = range.extractContents();
          span.appendChild(contents);
          range.insertNode(span);
          
          // Erstelle senkrechte Linie rechts neben dem Absatz
          createQuoteVerticalLine(targetElement, range, quote);
          
          console.log('[QUOTE-HIGHLIGHT] Zitat-Hervorhebung erfolgreich angewendet (mit senkrechter Linie)');
          
          return;
        } catch (e) {
          console.error('[QUOTE-HIGHLIGHT] Fehler beim Anwenden der Hervorhebung:', e);
        }
      }
    } else {
      console.warn('[QUOTE-HIGHLIGHT] quote_text nicht im Element-Text gefunden');
    }
  } else {
    console.warn('[QUOTE-HIGHLIGHT] quote_text nicht im Element-Text enthalten');
  }
}

/**
 * Fügt Bookmark-Icons zu allen bestehenden Zitaten im DOM hinzu (falls noch nicht vorhanden)
 * DEAKTIVIERT: Icons werden nur noch am Absatzanfang (bookmark-quote-indicator) angezeigt
 */
function addBookmarkIconsToExistingQuotes() {
  // Funktion deaktiviert - Icons werden nur noch am Absatzanfang angezeigt
  return;
  
  // Alte Implementierung (auskommentiert):
  // const quoteHighlights = document.querySelectorAll('[data-quote="true"][data-quote-id]');
  // quoteHighlights.forEach(quoteSpan => {
  //   // ... Icon-Erstellung entfernt
  // });
}

/**
 * @deprecated Verwende stattdessen applyHighlightToElement
 * Hilfsfunktion: Wendet Unterstreichung auf ein Buch-Element an
 */
function applyHighlightToBookElement(targetElement, highlight) {
  console.log('[HIGHLIGHT-BOOK] applyHighlightToBookElement aufgerufen:', {
    highlightId: highlight.id,
    paragraphId: highlight.paragraph_id,
    gaNumber: highlight.ga_number,
    targetElement: targetElement.tagName,
    targetElementText: targetElement.textContent?.substring(0, 100)
  });
  
  // Prüfe ob bereits unterstrichen
  const existingHighlight = targetElement.querySelector(`[data-highlight-id="${highlight.id}"]`);
  if (existingHighlight) {
    console.log('[HIGHLIGHT-BOOK] Bereits vorhanden, prüfe Event-Listener');
    // Stelle sicher, dass Event-Listener vorhanden ist
    if (!existingHighlight.hasAttribute('data-listener-attached')) {
      existingHighlight.addEventListener('click', function(e) {
        e.stopPropagation();
        e.preventDefault();
        console.log('[HIGHLIGHT-BOOK] Klick auf Unterstreichung (nachträglich):', highlight.id, highlight.ga_number, highlight.paragraph_id);
        jumpToHighlight(highlight.ga_number, highlight.paragraph_id, highlight.id);
      });
      existingHighlight.setAttribute('data-listener-attached', 'true');
      console.log('[HIGHLIGHT-BOOK] Event-Listener nachträglich hinzugefügt');
    }
    return; // Bereits vorhanden
  }
  
  // Hole den Text des Elements
  const elementText = targetElement.textContent || targetElement.innerText || '';
  console.log('[HIGHLIGHT-BOOK] Element-Text:', elementText ? elementText.substring(0, 200) : '(leer)');
  console.log('[HIGHLIGHT-BOOK] Gespeicherter Text:', highlight.paragraph_text?.substring(0, 200));
  console.log('[HIGHLIGHT-BOOK] Offsets:', highlight.text_start_offset, highlight.text_end_offset);
  
  // Prüfe ob elementText leer ist
  if (!elementText || elementText.length === 0) {
    console.warn('[HIGHLIGHT-BOOK] Element-Text ist leer, kann Unterstreichung nicht anwenden');
    return;
  }
  
  // Versuche mit den Offsets
  if (highlight.text_start_offset !== null && highlight.text_end_offset !== null) {
    const startOffset = highlight.text_start_offset;
    const endOffset = highlight.text_end_offset;
    
    // Prüfe ob die Offsets innerhalb der Textlänge liegen
    if (startOffset >= 0 && endOffset <= elementText.length && startOffset < endOffset) {
      console.log('[HIGHLIGHT-BOOK] Versuche Unterstreichung mit Offsets anzuwenden');
      // Erstelle Range für die Unterstreichung
      const range = document.createRange();
      const walker = document.createTreeWalker(
        targetElement,
        NodeFilter.SHOW_TEXT,
        null,
        false
      );
      
      let currentOffset = 0;
      let startNode = null;
      let startOffsetInNode = 0;
      let endNode = null;
      let endOffsetInNode = 0;
      
      let node;
      while (node = walker.nextNode()) {
        const nodeLength = node.textContent.length;
        
        if (!startNode && currentOffset + nodeLength > startOffset) {
          startNode = node;
          startOffsetInNode = startOffset - currentOffset;
        }
        
        if (currentOffset + nodeLength >= endOffset) {
          endNode = node;
          endOffsetInNode = endOffset - currentOffset;
          break;
        }
        
        currentOffset += nodeLength;
      }
      
      console.log('[HIGHLIGHT-BOOK] Range gefunden:', {
        startNode: startNode ? startNode.textContent.substring(0, 50) : null,
        endNode: endNode ? endNode.textContent.substring(0, 50) : null,
        startOffsetInNode,
        endOffsetInNode
      });
      
      if (startNode && endNode) {
        try {
          range.setStart(startNode, startOffsetInNode);
          range.setEnd(endNode, endOffsetInNode);
          
          const highlightColor = getHighlightColor(highlight.color || 'blue');
          const span = document.createElement('span');
          span.className = 'member-highlight';
          span.style.setProperty('text-decoration', 'underline', 'important');
          span.style.setProperty('text-decoration-color', highlightColor, 'important');
          span.style.setProperty('-webkit-text-decoration-color', highlightColor, 'important');
          span.style.setProperty('text-decoration-thickness', '1.5px', 'important');
          span.style.setProperty('cursor', 'pointer', 'important'); // Zeige Pointer-Cursor für Klick-Funktionalität
          span.setAttribute('data-highlight-id', highlight.id);
          span.setAttribute('data-highlight', 'true');
          span.setAttribute('data-highlight-color', highlight.color || 'blue');
          span.setAttribute('data-ga-number', highlight.ga_number);
          span.setAttribute('data-paragraph-id', highlight.paragraph_id);
          span.setAttribute('title', 'Klicken zum Öffnen im Member Panel'); // Tooltip hinzufügen
          span.setAttribute('data-listener-attached', 'true'); // Markiere dass Event-Listener gesetzt wurde
          // Verwende addEventListener statt onclick für bessere Kompatibilität
          span.addEventListener('click', function(e) {
            e.stopPropagation();
            e.preventDefault();
            console.log('[HIGHLIGHT-BOOK] Klick auf Unterstreichung:', highlight.id, highlight.ga_number, highlight.paragraph_id);
            jumpToHighlight(highlight.ga_number, highlight.paragraph_id, highlight.id);
          });
          
          const contents = range.extractContents();
          span.appendChild(contents);
          range.insertNode(span);
          console.log('[HIGHLIGHT-BOOK] Unterstreichung erfolgreich angewendet (mit Offsets)');
          return;
        } catch (e) {
          console.error('[HIGHLIGHT-BOOK] Fehler beim Anwenden der Unterstreichung (mit Offsets):', e);
        }
      }
    }
  }
  
  // Fallback: Versuche den Text zu finden und zu unterstreichen
  if (highlight.paragraph_text) {
    const textToHighlight = highlight.paragraph_text.substring(
      highlight.text_start_offset || 0,
      highlight.text_end_offset || highlight.paragraph_text.length
    );
    
    // Prüfe ob textToHighlight gültig ist
    if (!textToHighlight || textToHighlight.length === 0) {
      console.warn('[HIGHLIGHT-BOOK] textToHighlight ist leer, kann Unterstreichung nicht anwenden');
      return;
    }
    
    if (elementText && elementText.includes(textToHighlight)) {
      const range = document.createRange();
      const walker = document.createTreeWalker(
        targetElement,
        NodeFilter.SHOW_TEXT,
        null,
        false
      );
      
      let node;
      while (node = walker.nextNode()) {
        const nodeText = node.textContent;
        const index = nodeText.indexOf(textToHighlight);
        
        if (index !== -1) {
          try {
            range.setStart(node, index);
            range.setEnd(node, index + textToHighlight.length);
            
            const highlightColor = getHighlightColor(highlight.color || 'blue');
            const span = document.createElement('span');
            span.className = 'member-highlight';
            span.style.setProperty('text-decoration', 'underline', 'important');
            span.style.setProperty('text-decoration-color', highlightColor, 'important');
            span.style.setProperty('-webkit-text-decoration-color', highlightColor, 'important');
            span.style.setProperty('text-decoration-thickness', '1.5px', 'important');
            span.style.setProperty('cursor', 'pointer', 'important'); // Zeige Pointer-Cursor für Klick-Funktionalität
            span.setAttribute('data-highlight-id', highlight.id);
            span.setAttribute('data-highlight', 'true');
            span.setAttribute('data-highlight-color', highlight.color || 'blue');
            span.setAttribute('title', 'Klicken zum Öffnen im Member Panel'); // Tooltip hinzufügen
            // Verwende addEventListener statt onclick für bessere Kompatibilität
            span.addEventListener('click', function(e) {
              e.stopPropagation();
              e.preventDefault();
              console.log('[HIGHLIGHT-BOOK] Klick auf Unterstreichung:', highlight.id, highlight.ga_number, highlight.paragraph_id);
              jumpToHighlight(highlight.ga_number, highlight.paragraph_id, highlight.id);
            });
            
            const contents = range.extractContents();
            span.appendChild(contents);
            range.insertNode(span);
            console.log('[HIGHLIGHT-BOOK] Unterstreichung erfolgreich angewendet (mit Text-Suche)');
            return;
          } catch (e) {
            console.error('[HIGHLIGHT-BOOK] Fehler beim Anwenden der Unterstreichung (mit Text-Suche):', e);
          }
        }
      }
    }
  }
}

/**
 * Wendet eine gespeicherte Unterstreichung auf den Text an
 * Vereinheitlicht für Bücher und Vorträge - verwendet dieselbe Logik
 */
function applyStoredHighlight(highlight) {
  try {
    // Normalisiere paragraph_id: Entferne ^ am Anfang falls vorhanden (für Bücher)
    const normalizedParaId = String(highlight.paragraph_id || '').replace(/^\^/, '');
    let paraElement = document.getElementById(`para-${normalizedParaId}`);
    
    // Falls nicht gefunden, versuche mit Original-ID
    if (!paraElement) {
      paraElement = document.getElementById(`para-${highlight.paragraph_id}`);
    }
    
    // Falls immer noch nicht gefunden, versuche für Bücher mit data-index
    if (!paraElement) {
      const bookParaElement = document.querySelector(`[data-index="${highlight.paragraph_id}"], [data-index="^${normalizedParaId}"]`);
      if (bookParaElement) {
        paraElement = bookParaElement;
      }
    }
    
    if (!paraElement) {
      console.warn('[HIGHLIGHT] Paragraph nicht gefunden:', highlight.paragraph_id);
      return;
    }
    
    // Finde das tatsächliche Text-Element
    // Für Bücher kann paraElement ein verstecktes <span> Element sein
    // Für Vorträge ist es normalerweise das Element selbst
    let targetElement = paraElement;
    
    // Wenn paraElement versteckt ist oder ein span, suche nach dem Parent-Element mit Text
    if (paraElement.style.display === 'none' || paraElement.tagName.toLowerCase() === 'span') {
      let parent = paraElement.parentElement;
      let foundTextElement = null;
      
      // Gehe durch alle Parent-Elemente und suche nach einem Element mit Text
      while (parent && parent !== document.body) {
        const tagName = parent.tagName.toLowerCase();
        
        if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
          // Prüfe ob dieses Element den gespeicherten Text enthält
          if (highlight.paragraph_text && parent.textContent && parent.textContent.includes(highlight.paragraph_text.substring(0, 50))) {
            foundTextElement = parent;
            break;
          } else if (parent.textContent && parent.textContent.trim().length > 0 && !foundTextElement) {
            // Fallback: Nimm das erste Element mit Text
            foundTextElement = parent;
          }
        }
        parent = parent.parentElement;
      }
      
      if (foundTextElement) {
        targetElement = foundTextElement;
      } else {
        // Fallback: Versuche das nächste Parent-Element zu finden
        parent = paraElement.parentElement;
        while (parent && parent !== document.body) {
          const tagName = parent.tagName.toLowerCase();
          if (['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'].includes(tagName)) {
            targetElement = parent;
            break;
          }
          parent = parent.parentElement;
        }
      }
    }
    
    // Verwende die vereinheitlichte Funktion für Bücher und Vorträge
    applyHighlightToElement(targetElement, highlight);
  } catch (error) {
    console.error('Fehler beim Anwenden der Unterstreichung:', error);
  }
}

/**
 * Stellt Icons wieder her, die durch DOM-Manipulationen verloren gegangen sind
 */
function restoreBookmarkQuoteIndicators() {
  if (!lastMarkedLectureId || !lastQuotesData) return;
  
  // Sammle alle paragraph_ids für diesen Vortrag
  const paragraphIds = new Set();
  
  if (lastQuotesData.success && lastQuotesData.data) {
    lastQuotesData.data
      .filter(q => q.ga_reference === lastMarkedLectureId && q.paragraph_id)
      .forEach(q => paragraphIds.add(q.paragraph_id));
  }
  
  // Stelle Icons wieder her
  paragraphIds.forEach(paraId => {
    const paraElement = document.getElementById(`para-${paraId}`);
    if (paraElement && !paraElement.querySelector('.bookmark-quote-indicator')) {
      addBookmarkQuoteIndicator(paraId, lastMarkedLectureId, null, lastQuotesData);
    }
  });
}

/**
 * Springe zu einer Unterstreichung
 */
async function jumpToHighlight(lectureId, paragraphId, highlightId) {
  try {
    // Öffne MB falls nicht offen
    if (!membersPanelActive) {
      if (typeof openMembersPanel === 'function') {
        await openMembersPanel();
      }
    }
    
    // Wechsle zum Highlights-Tab
    if (typeof switchMembersTab === 'function') {
      await switchMembersTab('highlights');
    }
    
    // Warte kurz, dann scrolle zum Item - mehrere Versuche für robustere Navigation
    let scrollAttempts = 0;
    const maxScrollAttempts = 10;
    
    const tryScrollToHighlight = async () => {
      scrollAttempts++;
      const targetItem = document.querySelector(`[data-id="${highlightId}"][data-type="highlight"]`);
      if (targetItem) {
        // Scrolle nur den Content-Bereich, nicht das gesamte Panel
        const membersContent = document.querySelector('.members-content');
        if (membersContent) {
          // Berechne Position relativ zum scrollbaren Container
          const containerRect = membersContent.getBoundingClientRect();
          const itemRect = targetItem.getBoundingClientRect();
          
          // Berechne die relative Position: Item-Position minus Container-Position plus aktueller Scroll
          const relativeTop = itemRect.top - containerRect.top + membersContent.scrollTop;
          
          // Scrolle so, dass das Item in der Mitte des sichtbaren Bereichs erscheint (mit etwas Abstand)
          const containerHeight = membersContent.clientHeight;
          const itemHeight = itemRect.height;
          const targetScrollTop = relativeTop - (containerHeight / 2) + (itemHeight / 2);
          
          membersContent.scrollTo({
            top: Math.max(0, targetScrollTop),
            behavior: 'smooth'
          });
        } else {
          // Fallback: Nur Content scrollen, nicht das gesamte Panel
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
        return; // Erfolgreich gescrollt
      } else if (scrollAttempts < maxScrollAttempts) {
        // Item noch nicht gefunden, versuche es erneut
        setTimeout(() => tryScrollToHighlight(), 200 + (scrollAttempts * 50));
      } else {
        console.warn('[JUMP-TO-HIGHLIGHT] Highlight mit ID', highlightId, 'nicht gefunden nach', maxScrollAttempts, 'Versuchen');
      }
    };
    
    // Starte den ersten Versuch
    setTimeout(() => tryScrollToHighlight(), 300);
    
    // Lade Highlight-Daten, um Offsets zu bekommen
    let highlightData = null;
    if (typeof getHighlights === 'function') {
      const highlightsResult = await getHighlights();
      if (highlightsResult.success && highlightsResult.data) {
        highlightData = highlightsResult.data.find(h => h.id === highlightId);
        console.log('[JUMP-TO-HIGHLIGHT] Highlight-Daten geladen:', {
          highlightId,
          paragraphId,
          textStartOffset: highlightData?.text_start_offset,
          textEndOffset: highlightData?.text_end_offset
        });
      }
    }
    
    // WICHTIG: Prüfe ob der Text bereits geladen ist
    const isTextAlreadyLoaded = typeof currentLectureData !== 'undefined' && 
                                 currentLectureData && 
                                 currentLectureData.ID === lectureId;
    
    console.log('[JUMP-TO-HIGHLIGHT] Text bereits geladen?', isTextAlreadyLoaded, 'LectureId:', lectureId);
    
    if (isTextAlreadyLoaded) {
      // Text ist bereits geladen - scrolle zum unterstrichenen Text
      // WICHTIG: Versuche mehrfach, das Highlight-Element zu finden (mit Verzögerungen)
      // Die Highlights könnten noch nicht im DOM sein
      let attempts = 0;
      const maxAttempts = 10;
      
      const tryScrollToHighlight = () => {
        attempts++;
        const highlightElement = document.querySelector(`[data-highlight-id="${highlightId}"]`);
        
        if (highlightElement) {
          console.log('[JUMP-TO-HIGHLIGHT] Unterstrichenes Element gefunden (Versuch', attempts, '), scrolle direkt dazu');
          const mainContainer = document.getElementById('main');
          if (mainContainer) {
            const header = document.getElementById('viewer-header');
            const headerHeight = header ? header.offsetHeight + 5 : 5;
            const mainRect = mainContainer.getBoundingClientRect();
            const highlightRect = highlightElement.getBoundingClientRect();
            
            // Berechne Position im oberen Viertel des sichtbaren Bereichs
            const viewportHeight = mainRect.height - headerHeight;
            const upperQuarterOffset = Math.round(viewportHeight * 0.02); // 2% vom oberen Rand = knapp unter Header
            
            const currentScrollTop = mainContainer.scrollTop;
            const highlightTopRelativeToViewport = highlightRect.top - mainRect.top;
            const targetScrollTop = currentScrollTop + highlightTopRelativeToViewport - headerHeight - upperQuarterOffset;
            
            mainContainer.scrollTop = Math.max(0, targetScrollTop);
            console.log('[JUMP-TO-HIGHLIGHT] Gescrollt zu unterstrichenem Element (knapp unter Header), scrollTop:', mainContainer.scrollTop);
            return true; // Erfolg
          }
        } else if (attempts < maxAttempts) {
          // Element noch nicht gefunden, versuche es erneut
          setTimeout(tryScrollToHighlight, 100);
          return false; // Noch nicht erfolgreich
        } else {
          // Nach maxAttempts Versuchen nicht gefunden - verwende Offsets
          console.log('[JUMP-TO-HIGHLIGHT] Unterstrichenes Element nach', maxAttempts, 'Versuchen nicht gefunden, verwende Offsets');
          if (highlightData && highlightData.text_start_offset !== null && highlightData.text_start_offset !== undefined) {
            if (typeof scrollToTextPositionInParagraph === 'function') {
              scrollToTextPositionInParagraph(
                paragraphId, 
                highlightData.text_start_offset, 
                highlightData.text_end_offset, 
                false, // Keine Absatz-Markierung für Unterstreichungen
                highlightId // Übergib highlightId für direkten Zugriff auf Highlight-Element
              );
            } else {
              console.error('[JUMP-TO-HIGHLIGHT] scrollToTextPositionInParagraph Funktion nicht verfügbar');
            }
          } else {
            console.log('[JUMP-TO-HIGHLIGHT] Keine Offsets verfügbar, scrolle zum Absatz (knapp unter Header)');
            // Fallback: Scrolle zum Absatz
            const cleanIndex = String(paragraphId || '').replace(/^para-/, '').replace(/^\^/, '');
            const paraElement = document.getElementById(`para-${cleanIndex}`);
            console.log('[JUMP-TO-HIGHLIGHT] Suche nach paraElement:', `para-${cleanIndex}`, 'gefunden:', !!paraElement);
            if (paraElement) {
              const mainContainer = document.getElementById('main');
              if (mainContainer) {
                const header = document.getElementById('viewer-header');
                const headerHeight = header ? header.offsetHeight + 5 : 5;
                const mainRect = mainContainer.getBoundingClientRect();
                const paraRect = paraElement.getBoundingClientRect();
                
                // Berechne Position im oberen Viertel des sichtbaren Bereichs
                const viewportHeight = mainRect.height - headerHeight;
                const upperQuarterOffset = Math.round(viewportHeight * 0.02); // 2% vom oberen Rand = knapp unter Header
                
                const relativeTop = paraRect.top - mainRect.top + mainContainer.scrollTop - headerHeight - upperQuarterOffset;
                mainContainer.scrollTop = Math.max(0, relativeTop);
                console.log('[JUMP-TO-HIGHLIGHT] Gescrollt zu Absatz (knapp unter Header), scrollTop:', mainContainer.scrollTop);
              }
            } else {
              console.warn('[JUMP-TO-HIGHLIGHT] paraElement nicht gefunden');
            }
          }
          return false; // Nicht erfolgreich
        }
      };
      
      // Starte den ersten Versuch sofort, dann mit Verzögerungen
      setTimeout(tryScrollToHighlight, 100);
      return;
    }
    
    // Text ist nicht geladen - lade ihn neu MIT Scrollen zum unterstrichenen Text
    console.log('[JUMP-TO-HIGHLIGHT] Text nicht geladen, lade neu');
    if (typeof navigateToLectureFromMembersPanel === 'function') {
      // Navigiere zum Vortrag/Buch und scrolle zum unterstrichenen Text
      if (highlightData && highlightData.text_start_offset !== null && highlightData.text_start_offset !== undefined) {
        console.log('[JUMP-TO-HIGHLIGHT] Navigiere mit Offsets:', highlightData.text_start_offset, highlightData.text_end_offset);
        await navigateToLectureFromMembersPanel(
          lectureId, 
          paragraphId, 
          highlightData.text_start_offset, 
          highlightData.text_end_offset, 
          false // Keine Absatz-Markierung für Unterstreichungen
        );
      } else {
        console.log('[JUMP-TO-HIGHLIGHT] Navigiere ohne Offsets');
        // Fallback: Scrolle nur zum Absatz
        await navigateToLectureFromMembersPanel(lectureId, paragraphId, null, null, false);
      }
    } else {
      console.error('[JUMP-TO-HIGHLIGHT] navigateToLectureFromMembersPanel Funktion nicht verfügbar');
    }
  } catch (error) {
    console.error('Fehler beim Springen zur Unterstreichung:', error);
  }
}

/**
 * Springe direkt zu einem Zitat im Members Panel anhand der quoteId
 */
async function jumpToQuoteById(quoteId) {
  try {
    // Öffne MB falls nicht offen
    if (!membersPanelActive) {
      if (typeof openMembersPanel === 'function') {
        await openMembersPanel();
      }
    }
    
    // Wechsle zum Quotes-Tab
    const targetTab = 'quotes';
    
    // Wechsle zum entsprechenden Tab
    if (typeof switchMembersTab === 'function') {
      await switchMembersTab(targetTab);
    }
    
    // Warte kurz, dann scrolle zum Item - mehrere Versuche für robustere Navigation
    let scrollAttempts = 0;
    const maxScrollAttempts = 10;
    
    const tryScrollToQuote = () => {
      scrollAttempts++;
      const targetItem = document.querySelector(`.member-item[data-id="${quoteId}"]`);
      if (targetItem) {
        // Scrolle nur den Content-Bereich, nicht das gesamte Panel
        const membersContent = document.querySelector('.members-content');
        if (membersContent) {
          // Berechne Position relativ zum scrollbaren Container
          const containerRect = membersContent.getBoundingClientRect();
          const itemRect = targetItem.getBoundingClientRect();
          
          // Berechne die relative Position: Item-Position minus Container-Position plus aktueller Scroll
          const relativeTop = itemRect.top - containerRect.top + membersContent.scrollTop;
          
          // Scrolle so, dass das Item oben erscheint (mit etwas Abstand)
          membersContent.scrollTo({
            top: Math.max(0, relativeTop - 20), // 20px Abstand oben
            behavior: 'smooth'
          });
        } else {
          // Fallback: Nur Content scrollen, nicht das gesamte Panel
          const membersTabContent = document.getElementById('members-tab-content');
          if (membersTabContent) {
            const containerRect = membersTabContent.getBoundingClientRect();
            const itemRect = targetItem.getBoundingClientRect();
            const relativeTop = itemRect.top - containerRect.top + membersTabContent.scrollTop;
            
            membersTabContent.scrollTo({
              top: Math.max(0, relativeTop - 20),
              behavior: 'smooth'
            });
          }
        }
        // Highlighte kurz
        targetItem.classList.add('member-item-highlighted');
        setTimeout(() => {
          targetItem.classList.remove('member-item-highlighted');
        }, 2000);
        return; // Erfolgreich gescrollt
      } else if (scrollAttempts < maxScrollAttempts) {
        // Item noch nicht gefunden, versuche es erneut
        setTimeout(() => tryScrollToQuote(), 200 + (scrollAttempts * 50));
      } else {
        console.warn('[QUOTE-JUMP] Zitat mit ID', quoteId, 'nicht gefunden nach', maxScrollAttempts, 'Versuchen');
      }
    };
    
    // Starte den ersten Versuch
    setTimeout(() => tryScrollToQuote(), 500);
  } catch (error) {
    console.error('[QUOTE-JUMP] Fehler beim Springen zum Zitat:', error);
  }
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
    
    // Wechsle zum Quotes-Tab
    const targetTab = 'quotes';
    
    // Wechsle zum entsprechenden Tab
    if (typeof switchMembersTab === 'function') {
      await switchMembersTab(targetTab);
    }
    
    // Warte kurz, dann scrolle zum Item
    setTimeout(async () => {
      // Lade Zitate erneut, um die IDs zu bekommen
      let targetItemId = null;
      
      if (hasQuote) {
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
    window.currentUser = data.user; // Setze auch global
    messageDiv.innerHTML = '<div class="success-msg">✓ Erfolgreich angemeldet!</div>';
    
    // Initialisiere Chat-Realtime-Listener sofort nach Login
    initializeChatRealtimeListener();
    // Aktualisiere Badge sofort
    setTimeout(() => {
      updateChatBadge();
    }, 100);
    
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
  const privacyCheckbox = document.getElementById('members-privacy-checkbox');
  const messageDiv = document.getElementById('login-message');
  
  if (!email || !password) {
    messageDiv.innerHTML = '<div class="error-msg">Bitte alle Felder ausfüllen</div>';
    return;
  }
  
  if (password.length < 6) {
    messageDiv.innerHTML = '<div class="error-msg">Passwort muss mindestens 6 Zeichen haben</div>';
    return;
  }
  
  if (!privacyCheckbox || !privacyCheckbox.checked) {
    messageDiv.innerHTML = '<div class="error-msg">Bitte stimmen Sie der Datenschutzerklärung zu</div>';
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
  document.getElementById('password-reset-form-content').style.display = 'none';
  document.querySelector('.members-header h2').textContent = 'Mitglieder Login';
  document.getElementById('login-message').innerHTML = '';
}

function showMembersRegister() {
  document.getElementById('login-form-content').style.display = 'none';
  document.getElementById('register-form-content').style.display = 'block';
  document.getElementById('password-reset-form-content').style.display = 'none';
  document.querySelector('.members-header h2').textContent = 'Registrierung';
  document.getElementById('login-message').innerHTML = '';
  // Setze Privacy-Checkbox zurück
  const privacyCheckbox = document.getElementById('members-privacy-checkbox');
  if (privacyCheckbox) {
    privacyCheckbox.checked = false;
  }
}

function showPasswordReset() {
  document.getElementById('login-form-content').style.display = 'none';
  document.getElementById('register-form-content').style.display = 'none';
  document.getElementById('password-reset-form-content').style.display = 'block';
  document.querySelector('.members-header h2').textContent = 'Passwort zurücksetzen';
  document.getElementById('login-message').innerHTML = '';
  
  // Übernehme E-Mail-Adresse aus Login-Formular, falls vorhanden
  const loginEmailInput = document.getElementById('members-email');
  const resetEmailInput = document.getElementById('members-reset-email');
  if (resetEmailInput && loginEmailInput && loginEmailInput.value) {
    resetEmailInput.value = loginEmailInput.value;
  } else if (resetEmailInput) {
    resetEmailInput.value = '';
  }
}

async function handlePasswordReset() {
  const email = document.getElementById('members-reset-email').value;
  const messageDiv = document.getElementById('login-message');
  
  if (!email) {
    messageDiv.innerHTML = '<div class="error-msg">Bitte geben Sie Ihre E-Mail-Adresse ein</div>';
    return;
  }
  
  // Validiere E-Mail-Format
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    messageDiv.innerHTML = '<div class="error-msg">Bitte geben Sie eine gültige E-Mail-Adresse ein</div>';
    return;
  }
  
  try {
    // Prüfe zuerst, ob die E-Mail registriert ist
    // Supabase sendet auch bei nicht registrierten E-Mails eine Bestätigung (aus Sicherheitsgründen)
    // aber wir können trotzdem versuchen zu prüfen
    const { error } = await supabaseClient.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/members.html`
    });
    
    if (error) throw error;
    
    // Erfolgsmeldung - auch wenn E-Mail nicht registriert ist, zeigen wir die gleiche Meldung
    // (aus Sicherheitsgründen sollte man nicht verraten, welche E-Mails registriert sind)
    messageDiv.innerHTML = '<div class="success-msg">✓ Falls diese E-Mail-Adresse registriert ist, wurde ein Passwort-Reset-Link an Ihre E-Mail-Adresse gesendet.<br><br>Bitte schauen Sie auch in Ihren Spam-Ordner, falls Sie keine E-Mail erhalten.</div>';
    
    // Setze E-Mail-Feld zurück
    document.getElementById('members-reset-email').value = '';
    
  } catch (error) {
    messageDiv.innerHTML = `<div class="error-msg">✗ ${error.message}</div>`;
  }
}

/**
 * Erstellt das Privacy-Modal im body (falls noch nicht vorhanden)
 */
function ensurePrivacyModalExists() {
  let modal = document.getElementById('members-privacy-modal');
  if (!modal) {
    // Stelle sicher, dass CSS-Stile vorhanden sind
    if (!document.getElementById('members-privacy-modal-styles')) {
      const style = document.createElement('style');
      style.id = 'members-privacy-modal-styles';
      style.textContent = `
        /* Privacy Modal Styles */
        .members-privacy-modal {
          display: none;
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(0, 0, 0, 0.5);
          z-index: 10001 !important;
          align-items: center;
          justify-content: center;
          opacity: 1 !important;
        }

        .members-privacy-modal.active {
          display: flex !important;
        }

        .members-privacy-modal-content {
          background: #ffffff !important;
          background-color: #ffffff !important;
          padding: 2rem;
          border-radius: 8px;
          max-width: 700px;
          width: 90%;
          max-height: 85vh;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
          display: flex;
          flex-direction: column;
          color: #333333;
          opacity: 1 !important;
          z-index: 10002 !important;
          position: relative;
        }

        .members-privacy-modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
          padding-bottom: 1rem;
          border-bottom: 1px solid #e0e0e0;
          flex-shrink: 0;
        }

        .members-privacy-modal-header h3 {
          color: #333333;
          font-size: 1.3rem;
          font-weight: normal;
          margin: 0;
        }

        .members-privacy-modal-close {
          background: none;
          border: none;
          font-size: 1.5rem;
          color: #666666;
          cursor: pointer;
          padding: 0;
          width: 30px;
          height: 30px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: color 0.2s;
        }

        .members-privacy-modal-close:hover {
          color: #333333;
        }

        .members-privacy-modal-body {
          flex: 1;
          overflow-y: auto;
          padding-right: 0.5rem;
        }

        .members-privacy-modal-body h4 {
          color: #333333;
          font-size: 1.1rem;
          font-weight: normal;
          margin-top: 1.5rem;
          margin-bottom: 0.5rem;
        }

        .members-privacy-modal-body h4:first-child {
          margin-top: 0;
        }

        .members-privacy-modal-body p {
          margin-bottom: 1rem;
          line-height: 1.6;
        }

        .members-privacy-modal-body ul {
          margin-bottom: 1rem;
          padding-left: 1.5rem;
        }

        .members-privacy-modal-body li {
          margin-bottom: 0.5rem;
          line-height: 1.6;
        }
      `;
      document.head.appendChild(style);
    }
    
    // Erstelle Modal direkt im body
    modal = document.createElement('div');
    modal.id = 'members-privacy-modal';
    modal.className = 'members-privacy-modal';
    modal.innerHTML = `
      <div class="members-privacy-modal-content">
        <div class="members-privacy-modal-header">
          <h3>Datenschutzerklärung</h3>
          <button class="members-privacy-modal-close" onclick="closeMembersPrivacyModal()">&times;</button>
        </div>
        <div class="members-privacy-modal-body">
          <h4>1. Datenerhebung und -speicherung</h4>
          <p>Bei der Registrierung im Mitgliederbereich werden folgende Daten erfasst und gespeichert:</p>
          <ul>
            <li>E-Mail-Adresse (für die Authentifizierung)</li>
            <li>Passwort (verschlüsselt gespeichert)</li>
            <li>Anzeigename (optional)</li>
            <li>Von Ihnen erstellte Bookmarks, Zitate und Notizen</li>
          </ul>

          <h4>2. Zweck der Datenerhebung</h4>
          <p>Die erhobenen Daten dienen ausschließlich dazu, Ihnen die Funktionen des Mitgliederbereichs zur Verfügung zu stellen:</p>
          <ul>
            <li>Speicherung Ihrer persönlichen Bookmarks und Zitate</li>
            <li>Verwaltung Ihrer Notizen und Schlagwörter</li>
            <li>Kommunikation mit anderen Mitgliedern (falls Chat-Funktion genutzt wird)</li>
          </ul>

          <h4>3. Datenverarbeitung</h4>
          <p>Ihre Daten werden auf Servern von Supabase (supabase.com) gespeichert und verarbeitet. Die Datenübertragung erfolgt verschlüsselt über HTTPS.</p>

          <h4>4. Ihre Rechte</h4>
          <p>Sie haben jederzeit das Recht:</p>
          <ul>
            <li>Auskunft über Ihre gespeicherten Daten zu erhalten</li>
            <li>Ihre Daten zu korrigieren oder zu löschen</li>
            <li>Ihren Account komplett zu löschen (über "Mein Account" → "Account löschen")</li>
            <li>Der Datenverarbeitung zu widersprechen</li>
          </ul>

          <h4>5. Cookies und Tracking</h4>
          <p>Diese Website verwendet keine Tracking-Cookies oder Analyse-Tools. Es werden lediglich technisch notwendige Cookies für die Authentifizierung verwendet.</p>

          <h4>6. Kontakt</h4>
          <p>Bei Fragen zum Datenschutz können Sie uns über die Kontaktmöglichkeiten im Impressum erreichen.</p>

          <h4>7. Änderungen der Datenschutzerklärung</h4>
          <p>Wir behalten uns vor, diese Datenschutzerklärung anzupassen. Über wesentliche Änderungen werden Sie per E-Mail informiert.</p>

          <p style="margin-top: 2rem; font-size: 0.85rem; color: #666666;">
            Stand: Januar 2025
          </p>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    
    // Event-Listener hinzufügen
    const privacyModalClose = modal.querySelector('.members-privacy-modal-close');
    if (privacyModalClose) {
      privacyModalClose.addEventListener('click', closeMembersPrivacyModal);
    }
    
    // Schließe Modal bei Klick außerhalb
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeMembersPrivacyModal();
      }
    });
    
    // ESC-Taste zum Schließen
    const handleEscape = (e) => {
      if (e.key === 'Escape' && modal.classList.contains('active')) {
        closeMembersPrivacyModal();
      }
    };
    document.addEventListener('keydown', handleEscape);
  }
  return modal;
}

/**
 * Zeigt das Privacy-Modal an
 */
function showMembersPrivacyModal() {
  const modal = ensurePrivacyModalExists();
  if (modal) {
    modal.classList.add('active');
  }
}

/**
 * Schließt das Privacy-Modal
 */
function closeMembersPrivacyModal() {
  const modal = document.getElementById('members-privacy-modal');
  if (modal) {
    modal.classList.remove('active');
  }
}

/**
 * Panel schließen
 */
function closeMembersPanel() {
  membersPanelActive = false;
  
  // Aktualisiere Button-Status
  updateMembersButtonStatus();
  
  // WICHTIG: Stoppe Scroll-Position-Schutz und setze Navigation-Flag zurück
  stopScrollPositionProtection();
  window.membersNavigating = false;
  document.body.classList.remove('members-navigating');
  
  // Stoppe Panel-Visibility Observer falls aktiv
  if (window.panelVisibilityObserver) {
    window.panelVisibilityObserver.disconnect();
    window.panelVisibilityObserver = null;
  }
  
  // Stoppe Width-Check Interval falls aktiv
  if (window.panelWidthCheckInterval) {
    clearInterval(window.panelWidthCheckInterval);
    window.panelWidthCheckInterval = null;
  }
  
  const summaryPanel = document.getElementById('summary-panel');
  const summaryContent = document.getElementById('summary-content');
  const resizeHandle = document.getElementById('verticalResizeHandle');
  
  if (summaryPanel) {
    // Stelle CSS-Transition wieder her
    summaryPanel.style.removeProperty('transition');
    
    summaryPanel.classList.remove('visible');
    if (resizeHandle) {
      resizeHandle.classList.remove('visible');
    }
    document.body.classList.add('summary-panel-collapsed');
    summaryPanel.style.width = '0';
    summaryPanel.style.minWidth = '0';
    
    // Zurück zur Standard-TOC-Ansicht
    summaryPanel.classList.remove('has-members-panel');
    if (summaryContent) {
      summaryContent.classList.remove('has-members-panel');
      summaryContent.innerHTML = '<div id="toc-list"></div>';
    }
  }
  
  // Chat-Channel NICHT beenden - bleibt aktiv für Badge-Updates auch wenn Panel geschlossen ist
  // Der Listener wird nur beim Abmelden oder Seitenwechsel entfernt
  
  // RH positionieren: Verwende zentrale Funktion wenn verfügbar
  if (typeof updateResizeHandle === 'function') {
    setTimeout(() => {
      updateResizeHandle();
    }, 50);
  }
  
  // TOC neu laden falls Funktion vorhanden
  // WICHTIG: Warte bis DOM aktualisiert ist, bevor TOC gebaut wird
  if (typeof buildTableOfContents === 'function') {
    setTimeout(() => {
      buildTableOfContents();
      // Stelle sicher, dass Scroll-Events wieder funktionieren
      const mainContainer = document.getElementById('main');
      if (mainContainer && typeof updateActiveTocItem === 'function') {
        mainContainer.removeEventListener('scroll', updateActiveTocItem);
        mainContainer.addEventListener('scroll', updateActiveTocItem);
        updateActiveTocItem();
      }
    }, 150);
  }
}

/**
 * Wechselt vom Mitgliederbereich zum TOC (Panel bleibt offen)
 */
function switchFromMembersPanelToTOC() {
  const summaryPanel = document.getElementById('summary-panel');
  const summaryContent = document.getElementById('summary-content');
  const resizeHandle = document.getElementById('verticalResizeHandle');
  const mainContainer = document.getElementById('main-container');
  
  // WICHTIG: Setze Flags ZUERST zurück, damit innerHTML Setter nicht blockiert
  membersPanelActive = false;
  window.membersNavigating = false;
  document.body.classList.remove('members-navigating');
  
  // WICHTIG: Stoppe Scroll-Position-Schutz
  stopScrollPositionProtection();
  
  // WICHTIG: Stelle innerHTML Setter wieder her, falls er überschrieben wurde
  if (summaryContent) {
    try {
      // Prüfe ob innerHTML überschrieben wurde
      const proto = Object.getPrototypeOf(summaryContent);
      const currentDescriptor = Object.getOwnPropertyDescriptor(summaryContent, 'innerHTML');
      const protoDescriptor = Object.getOwnPropertyDescriptor(proto, 'innerHTML');
      
      // Wenn innerHTML direkt auf summaryContent definiert ist (überschrieben), entferne es
      if (currentDescriptor && currentDescriptor.configurable) {
        delete summaryContent.innerHTML;
      }
    } catch (e) {
      // Ignoriere Fehler beim Zurücksetzen
      console.warn('[MB-TOC] Fehler beim Zurücksetzen des innerHTML Setters:', e);
    }
  }
  
  // Stoppe Panel-Visibility Observer falls aktiv
  if (window.panelVisibilityObserver) {
    window.panelVisibilityObserver.disconnect();
    window.panelVisibilityObserver = null;
  }
  
  // Entferne Members-Panel-Klassen
  if (summaryPanel) {
    summaryPanel.classList.remove('has-members-panel');
  }
  if (summaryContent) {
    summaryContent.classList.remove('has-members-panel');
  }
  
  // Chat-Channel NICHT beenden - bleibt aktiv für Badge-Updates auch wenn Panel geschlossen ist
  // Der Listener wird nur beim Abmelden oder Seitenwechsel entfernt
  
  // WICHTIG: Stelle sicher, dass das Panel geöffnet ist (auch wenn es vorher geschlossen war)
  if (summaryPanel) {
    const tocWidth = 280; // Standard-Breite für TOC (statt 400px vom MB)
    
    // Panel explizit öffnen falls nicht bereits sichtbar
    if (!summaryPanel.classList.contains('visible')) {
      summaryPanel.classList.add('visible');
      if (resizeHandle) {
        resizeHandle.classList.add('visible');
      }
      summaryPanel.style.display = 'block';
      summaryPanel.style.opacity = '1';
      summaryPanel.style.visibility = 'visible';
      document.body.classList.remove('summary-panel-collapsed');
    }
    
    // Breite auf TOC-Standard anpassen
    summaryPanel.style.width = tocWidth + 'px';
    summaryPanel.style.minWidth = tocWidth + 'px';
    summaryPanel.style.marginRight = '0px';
    
    // WICHTIG: Setze Inhalt auf TOC zurück NACH dem Setzen der Flags
    // (damit innerHTML Setter nicht blockiert)
    if (summaryContent) {
      // Verwende direkte DOM-Manipulation um sicherzustellen, dass es funktioniert
      summaryContent.textContent = ''; // Leere zuerst
      const tocDiv = document.createElement('div');
      tocDiv.id = 'toc-list';
      summaryContent.appendChild(tocDiv);
    }
    
    // WICHTIG: Verwende zentrale Synchronisationsfunktion für Main-Container und RH
    // (keine manuelle Setzung - wie in allen anderen Fällen auch)
    if (typeof resetPanelSync === 'function') {
      resetPanelSync(); // Setze Sync zurück, damit neue Breite erkannt wird
    }
    
    // Main-Container SOFORT anpassen
    if (mainContainer) {
      mainContainer.style.marginRight = tocWidth + 'px';
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
  }
  
  // TOC neu laden falls Funktion vorhanden
  // WICHTIG: Warte bis DOM aktualisiert ist, bevor TOC gebaut wird
  if (typeof buildTableOfContents === 'function') {
    setTimeout(() => {
      buildTableOfContents();
      // Stelle sicher, dass Scroll-Events wieder funktionieren
      const mainContainer = document.getElementById('main');
      if (mainContainer && typeof updateActiveTocItem === 'function') {
        mainContainer.removeEventListener('scroll', updateActiveTocItem);
        mainContainer.addEventListener('scroll', updateActiveTocItem);
        updateActiveTocItem();
      }
    }, 150);
  }
  
}

/**
 * Prüft ob MB aktiv ist
 */
function isMembersPanelActive() {
  return membersPanelActive;
}

/**
 * Lädt alle Keywords aus Quotes und Highlights und aktualisiert das Dropdown
 */
async function updateKeywordFilterDropdownWithAllKeywords() {
  if (typeof getQuotes !== 'function' || typeof getHighlights !== 'function') {
    console.warn('[MB-KEYWORDS] API-Funktionen nicht verfügbar');
    return;
  }
  
  try {
    // Verwende Cache wenn verfügbar, sonst lade neu
    const now = Date.now();
    const cacheValid = cachedQuotesData && cachedHighlightsData && 
                     bookmarksQuotesCacheTimestamp && 
                     (now - bookmarksQuotesCacheTimestamp) < BOOKMARKS_QUOTES_CACHE_TTL;
    
    let quotesResult, highlightsResult, notesResult;
    
    if (cacheValid) {
      quotesResult = cachedQuotesData;
      highlightsResult = cachedHighlightsData;
    } else {
      // Lade Quotes- und Highlights-Daten
      [quotesResult, highlightsResult] = await Promise.all([
        getQuotes(),
        getHighlights()
      ]);
      // Aktualisiere Cache
      cachedQuotesData = quotesResult;
      cachedHighlightsData = highlightsResult;
      bookmarksQuotesCacheTimestamp = now;
    }
    
    // Lade auch Notes-Daten (wenn verfügbar)
    if (typeof getNotes === 'function') {
      try {
        notesResult = await getNotes();
      } catch (error) {
        console.warn('[MB-KEYWORDS] Fehler beim Laden der Notes:', error);
        notesResult = { success: false, data: [] };
      }
    }
    
    // Sammle alle Keywords aus Quotes, Highlights und Notes
    const allKeywords = new Set();
    
    if (quotesResult.success && quotesResult.data) {
      quotesResult.data.forEach(quote => {
        if (quote.tags && Array.isArray(quote.tags)) {
          quote.tags.forEach(tag => allKeywords.add(tag));
        }
      });
    }
    
    if (highlightsResult.success && highlightsResult.data) {
      highlightsResult.data.forEach(highlight => {
        if (highlight.tags && Array.isArray(highlight.tags)) {
          highlight.tags.forEach(tag => allKeywords.add(tag));
        }
      });
    }
    
    if (notesResult && notesResult.success && notesResult.data) {
      notesResult.data.forEach(note => {
        if (note.tags && Array.isArray(note.tags)) {
          note.tags.forEach(tag => allKeywords.add(tag));
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
  
  if (typeof getQuotes !== 'function' || typeof getHighlights !== 'function') {
    return null;
  }
  
  try {
    // Verwende Cache wenn verfügbar
    const now = Date.now();
    const cacheValid = cachedQuotesData && cachedHighlightsData && 
                     bookmarksQuotesCacheTimestamp && 
                     (now - bookmarksQuotesCacheTimestamp) < BOOKMARKS_QUOTES_CACHE_TTL;
    
    let quotesResult, highlightsResult;
    
    if (cacheValid) {
      quotesResult = cachedQuotesData;
      highlightsResult = cachedHighlightsData;
    } else {
      [quotesResult, highlightsResult] = await Promise.all([
        getQuotes(),
        getHighlights()
      ]);
    }
    
    // Prüfe Quotes
    let hasInQuotes = false;
    if (quotesResult.success && quotesResult.data) {
      hasInQuotes = quotesResult.data.some(quote => 
        quote.tags && Array.isArray(quote.tags) && quote.tags.includes(keyword)
      );
    }
    
    // Prüfe Highlights
    let hasInHighlights = false;
    if (highlightsResult.success && highlightsResult.data) {
      hasInHighlights = highlightsResult.data.some(highlight => 
        highlight.tags && Array.isArray(highlight.tags) && highlight.tags.includes(keyword)
      );
    }
    
    // Wenn in Quotes vorhanden, wechsle zu Quotes-Tab (Priorität)
    if (hasInQuotes) return 'quotes';
    
    // Wenn nur in Highlights vorhanden, wechsle zu Highlights-Tab
    if (hasInHighlights) return 'highlights';
    
    return null;
  } catch (error) {
    console.error('[MB-KEYWORDS] Fehler beim Prüfen des Keywords:', error);
    return null;
  }
}

/**
 * Handler für Keyword-Filter - zeigt Items aus beiden Tabs (Quotes und Highlights)
 */
async function handleKeywordFilter(keyword) {
  if (!keyword) {
    // Kein Keyword ausgewählt - lade den normalen Tab-Inhalt wieder
    await loadMembersTab(currentMembersTab);
    return;
  }
  
  // Lade und zeige Items aus beiden Tabs (Quotes und Highlights) mit diesem Keyword
  await showKeywordFilteredItems(keyword);
}

/**
 * Behandelt die Auswahl eines GA-Bandes im Filter-Dropdown
 */
async function handleGAFilter(gaNumber) {
  selectedGAFilter = gaNumber || '';
  
  // Setze den Dropdown-Wert
  const gaFilterSelect = document.getElementById('ga-filter-select');
  if (gaFilterSelect) {
    gaFilterSelect.value = selectedGAFilter;
  }
  
  // Lade den aktuellen Tab neu, um die Filterung anzuwenden
  if (currentMembersTab === 'quotes' || currentMembersTab === 'highlights' || currentMembersTab === 'notes') {
    await loadMembersTab(currentMembersTab);
  }
}

/**
 * Aktualisiert das GA-Filter-Dropdown mit allen verfügbaren GA-Nummern
 */
function updateGAFilterDropdown(gaNumbers) {
  const gaFilterSelect = document.getElementById('ga-filter-select');
  if (!gaFilterSelect) return;
  
  // Sammle alle eindeutigen GA-Nummern (nur Basis-Nummern wie GA001, GA002, etc.)
  const uniqueGABases = new Set();
  gaNumbers.forEach(gaNum => {
    if (gaNum) {
      // Extrahiere Basis-GA-Nummer (z.B. GA001 aus GA001/01)
      const baseMatch = gaNum.match(/^(GA\d{3})/i);
      if (baseMatch) {
        uniqueGABases.add(baseMatch[1].toUpperCase());
      }
    }
  });
  
  // Sortiere GA-Nummern numerisch
  const sortedGABases = Array.from(uniqueGABases).sort((a, b) => {
    const numA = parseInt(a.replace('GA', ''));
    const numB = parseInt(b.replace('GA', ''));
    return numA - numB;
  });
  
  // Speichere aktuellen Wert
  const currentValue = gaFilterSelect.value;
  
  // Leere Dropdown und füge Optionen hinzu
  gaFilterSelect.innerHTML = '<option value="">GA</option>';
  sortedGABases.forEach(gaBase => {
    const option = document.createElement('option');
    option.value = gaBase;
    option.textContent = gaBase;
    gaFilterSelect.appendChild(option);
  });
  
  // Stelle vorherigen Wert wieder her
  gaFilterSelect.value = currentValue;
}

/**
 * Zeigt Items aus beiden Tabs (Quotes und Highlights) mit dem ausgewählten Keyword
 */
async function showKeywordFilteredItems(keyword) {
  const container = document.getElementById('members-tab-content');
  if (!container) return;
  
  // Zeige Ladeanzeige
  container.innerHTML = '<div class="empty-state"><em>Lade gefilterte Items...</em></div>';
  
  try {
    // Lade Quotes, Highlights und Notes parallel
    const now = Date.now();
    const cacheValid = cachedQuotesData && cachedHighlightsData && 
                     bookmarksQuotesCacheTimestamp && 
                     (now - bookmarksQuotesCacheTimestamp) < BOOKMARKS_QUOTES_CACHE_TTL;
    
    let quotesResult, highlightsResult, notesResult;
    
    if (cacheValid) {
      quotesResult = cachedQuotesData;
      highlightsResult = cachedHighlightsData;
    } else {
      [quotesResult, highlightsResult] = await Promise.all([
        getQuotes(),
        getHighlights()
      ]);
      cachedQuotesData = quotesResult;
      cachedHighlightsData = highlightsResult;
      bookmarksQuotesCacheTimestamp = now;
    }
    
    // Lade auch Notes (wenn verfügbar)
    if (typeof getNotes === 'function') {
      try {
        notesResult = await getNotes();
      } catch (error) {
        console.warn('[MB-KEYWORDS] Fehler beim Laden der Notes:', error);
        notesResult = { success: false, data: [] };
      }
    }
    
    // Filtere Items mit dem Keyword
    const filteredQuotes = quotesResult.success && quotesResult.data
      ? quotesResult.data.filter(quote => 
          quote.tags && Array.isArray(quote.tags) && quote.tags.includes(keyword)
        )
      : [];
    
    const filteredHighlights = highlightsResult.success && highlightsResult.data
      ? highlightsResult.data.filter(highlight => 
          highlight.tags && Array.isArray(highlight.tags) && highlight.tags.includes(keyword)
        )
      : [];
    
    const filteredNotes = notesResult && notesResult.success && notesResult.data
      ? notesResult.data.filter(note => 
          note.tags && Array.isArray(note.tags) && note.tags.includes(keyword)
        )
      : [];
    
    if (filteredQuotes.length === 0 && filteredHighlights.length === 0 && filteredNotes.length === 0) {
      container.innerHTML = `<div class="empty-state">Keine Items mit Schlagwort "${keyword}" gefunden</div>`;
      return;
    }
    
    // Rendere Quotes und Highlights kombiniert
    let combinedHtml = '';
    
    // Rendere Quotes
    if (filteredQuotes.length > 0) {
      const quotesHtml = filteredQuotes.map(quote => {
        const lectureDate = getLectureDate(quote);
        const dateDisplay = lectureDate ? `<span data-lecture-date="true" style="font-size: 0.85rem; font-weight: normal; color: var(--text-color);">${lectureDate}</span>` : '';
        const isBook = isBookGANumber(quote.ga_reference);
        const shouldShowLink = quote.paragraph_id || isBook;
        
        return `
          <div class="member-item" data-keywords="${quote.tags ? quote.tags.join(',') : ''}" data-id="${quote.id}" data-type="quote" data-ga-reference="${quote.ga_reference}">
            <div style="flex: 1;">
              <div class="member-item-header">
                ${shouldShowLink
                  ? `<strong><a href="#" onclick="saveMembersScrollPosition(); navigateToQuoteById('${quote.id}'); return false;" style="color: var(--link-color); text-decoration: none;">${quote.ga_reference}</a>${dateDisplay ? ', ' + dateDisplay : ''}</strong>`
                  : `<strong>${quote.ga_reference}${dateDisplay ? ', ' + dateDisplay : ''}</strong>`
                }
                <span class="member-item-date">${new Date(quote.created_at).toLocaleDateString('de-DE')}</span>
              </div>
              ${quote.lecture_title ? `<div class="member-item-subtitle">${quote.lecture_title}</div>` : ''}
              <div class="member-item-quote">"${quote.quote_text.substring(0, 150)}${quote.quote_text.length > 150 ? '...' : ''}"</div>
              ${quote.personal_note ? `<div class="member-item-note">${quote.personal_note}</div>` : ''}
              ${quote.tags && quote.tags.length > 0 ? `<div class="member-item-tags">${quote.tags.map(tag => `<span class="tag clickable-tag" onclick="handleKeywordFilter('${tag.replace(/'/g, "\\'")}'); return false;" style="cursor: pointer;" title="Nach diesem Schlagwort filtern">#${tag}</span>`).join(' ')}</div>` : ''}
              <div class="member-item-actions">
                <button class="edit-btn" onclick="editMemberQuote('${quote.id}')" title="Bearbeiten">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                  </svg>
                </button>
                <button class="delete-btn" onclick="deleteMemberQuote('${quote.id}')" title="Löschen">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        `;
      }).join('');
      combinedHtml += quotesHtml;
    }
    
    // Rendere Highlights
    if (filteredHighlights.length > 0) {
      const highlightsHtml = filteredHighlights.map(highlight => {
        const lectureDate = getLectureDate(highlight);
        const dateDisplay = lectureDate ? `<span data-lecture-date="true" style="font-size: 0.85rem; font-weight: normal; color: var(--text-color);">${lectureDate}</span>` : '';
        const isBook = isBookGANumber(highlight.ga_number);
        // Link immer anzeigen, auch ohne paragraph_id (springt dann zum Vortrag ohne spezifische Stelle)
        const shouldShowLink = true; // Immer Link anzeigen, auch wenn kein paragraph_id vorhanden ist
        
        const highlightedText = highlight.paragraph_text && highlight.text_start_offset !== null && highlight.text_end_offset !== null
          ? highlight.paragraph_text.substring(highlight.text_start_offset, highlight.text_end_offset)
          : highlight.paragraph_text || '';
        
        const highlightColor = getHighlightColor(highlight.color || 'blue');
        
        return `
          <div class="member-item" data-keywords="${highlight.tags ? highlight.tags.join(',') : ''}" data-id="${highlight.id}" data-type="highlight" data-ga-reference="${highlight.ga_number}">
            <div style="flex: 1;">
              <div class="member-item-header">
                ${shouldShowLink
                  ? `<strong><a href="#" onclick="saveMembersScrollPosition(); navigateToLectureFromMembersPanel('${highlight.ga_number}', ${highlight.paragraph_id ? `'${highlight.paragraph_id}'` : 'null'}, ${highlight.text_start_offset !== null && highlight.text_start_offset !== undefined ? highlight.text_start_offset : 'null'}, ${highlight.text_end_offset !== null && highlight.text_end_offset !== undefined ? highlight.text_end_offset : 'null'}); return false;" style="color: var(--link-color); text-decoration: none;">${highlight.ga_number}</a>${dateDisplay ? ', ' + dateDisplay : ''}</strong>`
                  : `<strong>${highlight.ga_number}${dateDisplay ? ', ' + dateDisplay : ''}</strong>`
                }
                <span class="member-item-date">${new Date(highlight.created_at).toLocaleDateString('de-DE')}</span>
              </div>
              ${highlight.lecture_title ? `<div class="member-item-subtitle">${highlight.lecture_title}</div>` : ''}
              ${shouldShowLink
                ? `<div class="member-item-text"><a href="#" onclick="saveMembersScrollPosition(); navigateToLectureFromMembersPanel('${highlight.ga_number}', ${highlight.paragraph_id ? `'${highlight.paragraph_id}'` : 'null'}, ${highlight.text_start_offset !== null && highlight.text_start_offset !== undefined ? highlight.text_start_offset : 'null'}, ${highlight.text_end_offset !== null && highlight.text_end_offset !== undefined ? highlight.text_end_offset : 'null'}); return false;" style="text-decoration: underline; text-decoration-color: ${highlightColor}; text-decoration-thickness: 1.5px; font-style: normal; color: var(--text-color); cursor: pointer;">${highlightedText.substring(0, 150)}${highlightedText.length > 150 ? '...' : ''}</a></div>`
                : `<div class="member-item-text" style="text-decoration: underline; text-decoration-color: ${highlightColor}; text-decoration-thickness: 1.5px; font-style: normal;">${highlightedText.substring(0, 150)}${highlightedText.length > 150 ? '...' : ''}</div>`
              }
              ${highlight.personal_note ? `<div class="member-item-note">${highlight.personal_note}</div>` : ''}
              ${highlight.tags && highlight.tags.length > 0 ? `<div class="member-item-tags">${highlight.tags.map(tag => `<span class="tag clickable-tag" onclick="handleKeywordFilter('${tag.replace(/'/g, "\\'")}'); return false;" style="cursor: pointer;" title="Nach diesem Schlagwort filtern">#${tag}</span>`).join(' ')}</div>` : ''}
              <div class="member-item-actions">
                <button class="edit-btn" onclick="editMemberHighlight('${highlight.id}')" title="Bearbeiten">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                  </svg>
                </button>
                <button class="delete-btn" onclick="deleteMemberHighlight('${highlight.id}')" title="Löschen">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        `;
      }).join('');
      combinedHtml += highlightsHtml;
    }
    
    // Rendere Notes
    if (filteredNotes.length > 0) {
      const notesHtml = filteredNotes.map(note => {
        const gaReference = note.ga_references && note.ga_references.length > 0 ? note.ga_references[0] : null;
        const paragraphId = note.paragraph_id || null;
        const textStartOffset = note.text_start_offset !== null ? note.text_start_offset : null;
        const textEndOffset = note.text_end_offset !== null ? note.text_end_offset : null;
        const dateDisplay = new Date(note.created_at).toLocaleDateString('de-DE');
        
        // Bereinige Text: Entferne Präfixe wie "Aus [[GA001]]:" oder "Aus [[GA001]] - Titel:"
        let cleanedContent = note.content;
        // Entferne "Aus [[GA...]]:" oder "Aus [[GA...]] - Titel:" am Anfang (mit optionalen Leerzeichen)
        cleanedContent = cleanedContent.replace(/^Aus\s*\[\[[^\]]+\]\]\s*[-:]\s*/i, '');
        // Entferne auch Varianten wie "Aus [[GA...]] - " oder "Aus [[GA...]]: "
        cleanedContent = cleanedContent.replace(/^Aus\s*\[\[[^\]]+\]\]\s*[-:]\s*/i, '');
        // Entferne führende Anführungszeichen und Leerzeichen
        cleanedContent = cleanedContent.replace(/^["']\s*/, '').trim();
        // Entferne auch mehrfache Leerzeichen am Anfang
        cleanedContent = cleanedContent.replace(/^\s+/, '');
        
        // Text auf zwei Zeilen begrenzen (ca. 150 Zeichen)
        const contentPreview = cleanedContent.substring(0, 150);
        const hasMore = cleanedContent.length > 150;
        
        // Prüfe ob Navigation möglich ist (mindestens GA-Referenz vorhanden)
        const canNavigate = gaReference !== null;
        
        return `
          <div class="member-item">
            <div style="flex: 1;">
              <div class="member-item-header">
                <div style="display: flex; align-items: center; gap: 0.25rem;">
                  ${canNavigate
                    ? `<strong><a href="#" onclick="saveMembersScrollPosition(); navigateToNoteFromMembersPanel('${note.id}', '${gaReference}', ${paragraphId ? `'${paragraphId}'` : 'null'}, ${textStartOffset !== null ? textStartOffset : 'null'}, ${textEndOffset !== null ? textEndOffset : 'null'}); return false;" style="color: var(--link-color); text-decoration: none;">${gaReference}${dateDisplay ? ', ' + dateDisplay : ''}</a></strong>`
                    : `<strong>${gaReference || 'Notiz'}${dateDisplay ? ', ' + dateDisplay : ''}</strong>`
                  }
                </div>
                <span class="member-item-date">${dateDisplay}</span>
              </div>
              ${canNavigate
                ? `<div class="member-item-quote"><a href="#" onclick="saveMembersScrollPosition(); navigateToNoteFromMembersPanel('${note.id}', '${gaReference}', ${paragraphId ? `'${paragraphId}'` : 'null'}, ${textStartOffset !== null ? textStartOffset : 'null'}, ${textEndOffset !== null ? textEndOffset : 'null'}); return false;" style="color: var(--text-color); text-decoration: none; cursor: pointer;" title="Zur Textstelle springen">"${contentPreview}${hasMore ? '...' : ''}"</a></div>`
                : `<div class="member-item-quote">"${contentPreview}${hasMore ? '...' : ''}"</div>`
              }
              ${note.tags && Array.isArray(note.tags) && note.tags.length > 0 ? `<div class="member-item-tags">${note.tags.map(tag => `<span class="tag clickable-tag" onclick="handleKeywordFilter('${tag.replace(/'/g, "\\'")}'); return false;" style="cursor: pointer;" title="Nach diesem Schlagwort filtern">#${tag}</span>`).join(' ')}</div>` : ''}
            </div>
            <div class="member-item-actions">
              <button class="edit-btn" onclick="editMemberNote('${note.id}')" title="Bearbeiten">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
              </button>
              <button class="delete-btn" onclick="deleteMemberNote('${note.id}')" title="Löschen">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                </svg>
              </button>
            </div>
          </div>
        `;
      }).join('');
      combinedHtml += notesHtml;
    }
    
    container.innerHTML = combinedHtml;
    
  } catch (error) {
    console.error('[MB-KEYWORDS] Fehler beim Laden gefilterter Items:', error);
    container.innerHTML = '<div class="empty-state">Fehler beim Laden der gefilterten Items</div>';
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
window.toggleMembersPanel = toggleMembersPanel;
window.updateMembersButtonStatus = updateMembersButtonStatus;
window.switchFromMembersPanelToTOC = switchFromMembersPanelToTOC;
window.isMembersPanelActive = isMembersPanelActive;

// Initialisiere Button-Status beim Laden
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      updateMembersButtonStatus();
    });
  } else {
    // DOM bereits geladen
    updateMembersButtonStatus();
  }
}
window.switchMembersTab = switchMembersTab;
window.loadSavedNotes = loadSavedNotes;
window.addBookmarkNoteIndicator = addBookmarkNoteIndicator;
window.getNoteColor = getNoteColor;
window.handleMembersLogin = handleMembersLogin;
window.handleMembersRegister = handleMembersRegister;
window.showMembersLogin = showMembersLogin;
window.showMembersRegister = showMembersRegister;
window.showPasswordReset = showPasswordReset;
window.handlePasswordReset = handlePasswordReset;
window.updateChatBadge = updateChatBadge;
window.initializeChatRealtimeListener = initializeChatRealtimeListener;
window.showMembersPrivacyModal = showMembersPrivacyModal;
window.closeMembersPrivacyModal = closeMembersPrivacyModal;
window.editMemberQuote = editMemberQuote;
window.editMemberHighlight = editMemberHighlight;
window.editMemberNote = editMemberNote;
window.deleteMemberQuote = deleteMemberQuote;
window.deleteMemberNote = deleteMemberNote;
window.toggleSortOrder = toggleSortOrder;
window.toggleMultiDeleteMode = toggleMultiDeleteMode;
window.updateMultiDeleteButton = updateMultiDeleteButton;
window.deleteSelectedItems = deleteSelectedItems;
window.saveMemberNote = saveMemberNote;
window.sendMemberChatMessage = sendMemberChatMessage;
window.handleKeywordFilter = handleKeywordFilter;
window.handleGAFilter = handleGAFilter;
window.navigateToLectureFromMembersPanel = navigateToLectureFromMembersPanel;
window.updateChatBadge = updateChatBadge;
window.markChatAsRead = markChatAsRead;
window.getUnreadChatCount = getUnreadChatCount;
window.initializeChatRealtimeListener = initializeChatRealtimeListener;
window.saveMembersScrollPosition = saveMembersScrollPosition;
window.restoreMembersScrollPosition = restoreMembersScrollPosition;
window.markParagraphsWithBookmarksAndQuotes = markParagraphsWithBookmarksAndQuotes;
window.jumpToBookmarkOrQuote = jumpToBookmarkOrQuote;
window.jumpToQuoteById = jumpToQuoteById;
window.jumpToHighlight = jumpToHighlight;
window.addBookmarkIconsToExistingQuotes = addBookmarkIconsToExistingQuotes;
window.loadMembersTab = loadMembersTab;
window.changeHighlightColor = changeHighlightColor;
window.changeQuoteColor = changeQuoteColor;
window.showNoteColorContextMenu = showNoteColorContextMenu;
window.changeNoteColor = changeNoteColor;

/**
 * Invalidiert den Cache für Zitate und/oder Unterstreichungen
 * @param {string} type - 'quotes', 'highlights' oder 'all' (Standard: 'all')
 */
function invalidateMembersCache(type = 'all') {
  if (type === 'quotes' || type === 'all') {
    cachedQuotesData = null;
  }
  if (type === 'highlights' || type === 'all') {
    cachedHighlightsData = null;
  }
  // Setze Timestamp auf 0, damit Cache als ungültig gilt
  bookmarksQuotesCacheTimestamp = 0;
}

/**
 * Aktualisiert den Mitgliederbereich, falls er offen ist
 * @param {string} tabName - 'quotes' oder 'highlights' (optional, verwendet aktuellen Tab wenn nicht angegeben)
 * @param {boolean} forceUpdate - Wenn true, aktualisiert auch wenn Tab nicht aktiv ist (nur Cache invalidation, Tab wird nicht geladen)
 */
async function updateMembersPanelIfOpen(tabName = null, forceUpdate = false) {
  // Prüfe ob Mitgliederbereich aktiv ist
  if (typeof membersPanelActive === 'undefined' || !membersPanelActive) {
    return;
  }
  
  // Verwende angegebenen Tab oder aktuellen Tab
  const tabToUpdate = tabName || currentMembersTab;
  
  // Aktualisiere nur Quotes- oder Highlights-Tab
  if (tabToUpdate === 'quotes' || tabToUpdate === 'highlights') {
    try {
      // Invalidiere Cache für den entsprechenden Tab, damit Daten neu geladen werden
      invalidateMembersCache(tabToUpdate);
      
      // Wenn der Tab aktiv ist, lade ihn neu (bei forceUpdate wird nur Cache invalidiert)
      if (tabToUpdate === currentMembersTab) {
        await loadMembersTab(tabToUpdate);
      }
      // Bei forceUpdate wird nur Cache invalidiert, Tab wird nicht geladen (verhindert Tab-Wechsel)
    } catch (error) {
      console.error('[MB-UPDATE] Fehler beim Aktualisieren:', error);
    }
  }
}

window.updateMembersPanelIfOpen = updateMembersPanelIfOpen;
window.invalidateMembersCache = invalidateMembersCache;


