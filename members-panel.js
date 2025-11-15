// ============================================
// GA-Suche - Mitglieder Panel Integration
// Zeigt Mitgliederbereich im Summary Panel
// ============================================

let membersPanelActive = false;
let currentMembersTab = 'bookmarks';

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
  
  // Login-Form HTML
  summaryContent.innerHTML = `
    <div class="members-panel">
      <div class="members-header">
        <h2>Mitglieder Login</h2>
        <button class="close-btn" onclick="closeMembersPanel()">×</button>
      </div>
      
      <div class="members-login-form">
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
  
  // Main-Container anpassen für breiteres MB Panel
  if (mainContainer) {
    mainContainer.style.marginRight = mbWidth + 'px';
  }
  
  // Resize-Handle EXAKT an Panel-Grenze positionieren
  const verticalResizeHandle = document.getElementById('verticalResizeHandle');
  if (verticalResizeHandle) {
    verticalResizeHandle.style.display = 'block'; // Auch Handle sichtbar machen
    const offset = 10; // Standard-Offset für MB
    verticalResizeHandle.style.right = (mbWidth - offset) + 'px';
    console.log('[MB-OPEN] Resize-Handle positioniert bei:', (mbWidth - offset) + 'px');
  }
  
  // Content HTML
  summaryContent.innerHTML = `
    <div class="members-panel">
      <div class="members-header">
        <h2>Mitgliederbereich</h2>
        <button class="close-btn" onclick="closeMembersPanel()">×</button>
      </div>
      
      <div class="members-tabs">
        <button class="members-tab ${currentMembersTab === 'bookmarks' ? 'active' : ''}" onclick="switchMembersTab('bookmarks')">🔖 Bookmarks</button>
        <button class="members-tab ${currentMembersTab === 'quotes' ? 'active' : ''}" onclick="switchMembersTab('quotes')">💬 Zitate</button>
        <button class="members-tab ${currentMembersTab === 'notes' ? 'active' : ''}" onclick="switchMembersTab('notes')">📝 Notizen</button>
        <button class="members-tab ${currentMembersTab === 'graph' ? 'active' : ''}" onclick="switchMembersTab('graph')">🕸️ Graph</button>
        <button class="members-tab ${currentMembersTab === 'chat' ? 'active' : ''}" onclick="switchMembersTab('chat')">💭 Chat</button>
      </div>
      
      <div class="members-content" id="members-tab-content">
        <!-- Content wird dynamisch geladen -->
      </div>
    </div>
  `;
  
  // Aktuellen Tab laden
  await loadMembersTab(currentMembersTab);
  
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
    console.log('[MB-OPEN] Panel und Content-Sichtbarkeit nachkorrigiert');
  }, 100);
}

/**
 * Tab wechseln
 */
async function switchMembersTab(tabName) {
  currentMembersTab = tabName;
  
  // Tab-Buttons aktualisieren
  document.querySelectorAll('.members-tab').forEach(tab => {
    tab.classList.remove('active');
  });
  event.target.classList.add('active');
  
  // Content laden
  await loadMembersTab(tabName);
}

/**
 * Tab-Content laden
 */
async function loadMembersTab(tabName) {
  const content = document.getElementById('members-tab-content');
  if (!content) return;
  
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
  }
}

/**
 * Bookmarks Tab
 */
async function loadBookmarksTab(container) {
  const result = await getBookmarks();
  
  if (!result.success || result.data.length === 0) {
    container.innerHTML = '<div class="empty-state">📑<br>Noch keine Bookmarks</div>';
    return;
  }
  
  const html = result.data.map(bookmark => `
    <div class="member-item">
      <div class="member-item-header">
        <strong>${bookmark.ga_number}</strong>
        <span class="member-item-date">${new Date(bookmark.created_at).toLocaleDateString('de-DE')}</span>
      </div>
      ${bookmark.lecture_title ? `<div class="member-item-subtitle">${bookmark.lecture_title}</div>` : ''}
      <div class="member-item-text">${bookmark.paragraph_text.substring(0, 150)}${bookmark.paragraph_text.length > 150 ? '...' : ''}</div>
      ${bookmark.note ? `<div class="member-item-note">📌 ${bookmark.note}</div>` : ''}
      ${bookmark.paragraph_id ? `<div class="member-item-link"><a href="#" onclick="showLecture('${bookmark.ga_number}', '${bookmark.paragraph_id}', []); return false;">🔗 Zur Stelle</a></div>` : ''}
      <button class="delete-btn" onclick="deleteMemberBookmark('${bookmark.id}')">🗑️</button>
    </div>
  `).join('');
  
  container.innerHTML = html;
}

/**
 * Quotes Tab
 */
async function loadQuotesTab(container) {
  const result = await getQuotes();
  
  if (!result.success || result.data.length === 0) {
    container.innerHTML = '<div class="empty-state">💬<br>Noch keine Zitate</div>';
    return;
  }
  
  const html = result.data.map(quote => `
    <div class="member-item">
      <div class="member-item-header">
        <strong>${quote.ga_reference}</strong>
        <span class="member-item-date">${new Date(quote.created_at).toLocaleDateString('de-DE')}</span>
      </div>
      <div class="member-item-quote">"${quote.quote_text.substring(0, 150)}${quote.quote_text.length > 150 ? '...' : ''}"</div>
      ${quote.personal_note ? `<div class="member-item-note">📌 ${quote.personal_note}</div>` : ''}
      ${quote.tags.length > 0 ? `<div class="member-item-tags">${quote.tags.map(tag => `<span class="tag">#${tag}</span>`).join(' ')}</div>` : ''}
      ${quote.paragraph_id ? `<div class="member-item-link"><a href="#" onclick="handleQuoteLink('${quote.ga_reference}', '${quote.paragraph_id}'); return false;">🔗 Zur Stelle</a></div>` : ''}
      <button class="delete-btn" onclick="deleteMemberQuote('${quote.id}')">🗑️</button>
    </div>
  `).join('');
  
  container.innerHTML = html;
}

// Handle Quote Link
function handleQuoteLink(gaReference, paragraphId) {
  try {
    if (typeof showLecture === 'function') {
      showLecture(gaReference, paragraphId, []);
    } else {
      console.error('showLecture nicht verfügbar');
    }
  } catch (err) {
    console.error('Fehler:', err);
  }
}
window.handleQuoteLink = handleQuoteLink;

/**
 * Notes Tab
 */
function loadNotesTab(container) {
  container.innerHTML = `
    <div class="notes-editor">
      <textarea id="members-note-content" placeholder="Schreibe deine Notiz hier...

Verwende:
- [[Wiki Links]] für Verknüpfungen
- #Tags für Kategorien
- GA123/4 für GA-Referenzen"></textarea>
      <button class="primary-btn" onclick="saveMemberNote()">💾 Notiz speichern</button>
      <div id="notes-list"></div>
    </div>
  `;
  
  loadSavedNotes();
}

async function loadSavedNotes() {
  const result = await getNotes();
  const list = document.getElementById('notes-list');
  
  if (!result.success || result.data.length === 0) {
    list.innerHTML = '<div class="empty-state" style="margin-top: 1rem;">📝<br>Noch keine Notizen</div>';
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
  container.innerHTML = `
    <div class="graph-placeholder">
      <div class="empty-state">
        🕸️<br>
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
      <div>📝 ${result.data.nodes.filter(n => n.type === 'note').length} Notizen</div>
      <div>🔗 ${result.data.links.length} Verbindungen</div>
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
    container.innerHTML = '<div class="empty-state">💭<br>Noch keine Nachrichten</div>';
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
    
    messageDiv.innerHTML = '<div class="success-msg">✓ Registrierung erfolgreich!<br>Bitte bestätigen Sie Ihre E-Mail.</div>';
    
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
    if (summaryContent) {
      summaryContent.innerHTML = '<div id="toc-list"></div>';
    }
  }
  
  // Chat-Channel beenden
  if (window.chatChannel) {
    unsubscribeFromChat(window.chatChannel);
    window.chatChannel = null;
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
    
    // Main-Container SOFORT anpassen (nicht mit Timeout)
    if (mainContainer) {
      mainContainer.style.marginRight = tocWidth + 'px';
      console.log('[MB→TOC] Main-Container margin-right angepasst auf:', tocWidth + 'px');
    }
    
    // Resize-Handle EXAKT an Panel-Grenze positionieren
    const resizeHandle = document.getElementById('verticalResizeHandle');
    if (resizeHandle) {
      const offset = 10; // Standard-Offset für TOC
      resizeHandle.style.right = (tocWidth - offset) + 'px';
      console.log('[MB→TOC] Resize-Handle positioniert bei:', (tocWidth - offset) + 'px');
    }
    
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

// Global verfügbar machen
window.openMembersPanel = openMembersPanel;
window.closeMembersPanel = closeMembersPanel;
window.switchFromMembersPanelToTOC = switchFromMembersPanelToTOC;
window.isMembersPanelActive = isMembersPanelActive;
window.switchMembersTab = switchMembersTab;
window.handleMembersLogin = handleMembersLogin;
window.handleMembersRegister = handleMembersRegister;
window.showMembersLogin = showMembersLogin;
window.showMembersRegister = showMembersRegister;
window.deleteMemberBookmark = deleteMemberBookmark;
window.deleteMemberQuote = deleteMemberQuote;
window.deleteMemberNote = deleteMemberNote;
window.saveMemberNote = saveMemberNote;
window.generateMemberGraph = generateMemberGraph;
window.sendMemberChatMessage = sendMemberChatMessage;

