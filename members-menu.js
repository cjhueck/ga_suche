// ============================================
// GA-Suche - Mitglieder Menu
// Simples 3-Stufen-System
// ============================================

let menuState = 'closed'; // closed, login-open, menu-open
let memberMenuContainer = null;

/**
 * Initialisiert das Mitglieder-Menu
 */
async function initMemberMenu(gaNumber, lectureTitle) {
  currentContext = { gaNumber, lectureTitle };
  await initSupabase();
  
  // Menu-Container erstellen
  createMemberMenu();
  
  // Styles hinzufügen
  addMenuStyles();
  
  // User-Status aktualisieren
  await updateMemberMenuState();
  
  console.log('✓ Member Menu aktiviert');
}

/**
 * Erstellt das Menu
 */
function createMemberMenu() {
  if (memberMenuContainer) return;
  
  memberMenuContainer = document.createElement('div');
  memberMenuContainer.id = 'member-menu';
  memberMenuContainer.innerHTML = `
    <!-- Main Icon (immer sichtbar) -->
    <button id="member-icon" class="member-icon" onclick="handleMemberIconClick()">
      <svg width="50" height="50" viewBox="0 0 24 24" fill="currentColor">
        <circle cx="12" cy="8" r="4"/>
        <path d="M12 14c-6.1 0-8 4-8 4v3h16v-3s-1.9-4-8-4z"/>
      </svg>
    </button>
    
    <!-- Action Icons (nur wenn eingeloggt & menu-open) -->
    <div id="action-icons" class="action-icons">
      <button class="action-btn" onclick="quickSaveQuote()" title="Zitat speichern">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </button>
      <button class="action-btn" onclick="quickSaveBookmark()" title="Bookmark speichern">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
        </svg>
      </button>
      <button class="action-btn" onclick="openQuickNote()" title="Notiz erstellen">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="12" y1="18" x2="12" y2="12"/>
          <line x1="9" y1="15" x2="15" y2="15"/>
        </svg>
      </button>
    </div>
    
    <!-- Login Modal -->
    <div id="login-modal" class="login-modal">
      <div class="login-modal-content">
        <button class="login-close" onclick="closeLoginModal()">×</button>
        <h2>Anmelden</h2>
        
        <div id="login-form">
          <input type="email" id="login-email" placeholder="E-Mail" />
          <input type="password" id="login-password" placeholder="Passwort" />
          <button onclick="handleLogin()">Anmelden</button>
          <button onclick="showRegisterForm()" class="secondary">Registrieren</button>
        </div>
        
        <div id="register-form" style="display:none;">
          <input type="email" id="register-email" placeholder="E-Mail" />
          <input type="password" id="register-password" placeholder="Passwort" />
          <button onclick="handleRegister()">Registrieren</button>
          <button onclick="showLoginForm()" class="secondary">Zurück zum Login</button>
        </div>
        
        <div id="login-message"></div>
      </div>
    </div>
  `;
  
  document.body.appendChild(memberMenuContainer);
  
  // Click außerhalb schließt Menu
  document.addEventListener('click', handleOutsideClick);
  
  // Text-Selektion tracken
  document.addEventListener('mouseup', trackSelection);
}

/**
 * Handler für Member-Icon Klick
 */
async function handleMemberIconClick() {
  await initSupabase();
  
  if (!currentUser) {
    // Nicht eingeloggt → Login-Modal öffnen
    openLoginModal();
  } else {
    // Eingeloggt → Mitgliederbereich öffnen
    window.location.href = 'members.html?tab=bookmarks';
  }
}

/**
 * Login-Modal öffnen
 */
function openLoginModal() {
  menuState = 'login-open';
  document.getElementById('login-modal').classList.add('open');
}

/**
 * Login-Modal schließen
 */
function closeLoginModal() {
  menuState = 'closed';
  document.getElementById('login-modal').classList.remove('open');
}

/**
 * User-Status für CSS-Klasse
 */
async function updateMemberMenuState() {
  await initSupabase();
  
  if (currentUser) {
    memberMenuContainer.classList.add('logged-in');
  } else {
    memberMenuContainer.classList.remove('logged-in');
  }
}

/**
 * Click außerhalb schließt Modal
 */
function handleOutsideClick(e) {
  if (!memberMenuContainer) return;
  
  const modal = document.getElementById('login-modal');
  
  // Wenn Login-Modal offen und Click außerhalb
  if (menuState === 'login-open' && modal.classList.contains('open')) {
    if (!modal.querySelector('.login-modal-content').contains(e.target) && 
        !document.getElementById('member-icon').contains(e.target)) {
      closeLoginModal();
    }
  }
}

/**
 * Login-Form anzeigen
 */
function showLoginForm() {
  document.getElementById('login-form').style.display = 'block';
  document.getElementById('register-form').style.display = 'none';
  document.querySelector('.login-modal-content h2').textContent = 'Anmelden';
}

/**
 * Register-Form anzeigen
 */
function showRegisterForm() {
  document.getElementById('login-form').style.display = 'none';
  document.getElementById('register-form').style.display = 'block';
  document.querySelector('.login-modal-content h2').textContent = 'Registrieren';
}

/**
 * Login Handler
 */
async function handleLogin() {
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const messageDiv = document.getElementById('login-message');
  
  if (!email || !password) {
    messageDiv.innerHTML = '<span class="error">Bitte alle Felder ausfüllen</span>';
    return;
  }
  
  try {
    const { data, error } = await supabaseClient.auth.signInWithPassword({
      email: email,
      password: password
    });
    
    if (error) throw error;
    
    currentUser = data.user;
    messageDiv.innerHTML = '<span class="success">✓ Erfolgreich angemeldet!</span>';
    
    setTimeout(() => {
      closeLoginModal();
      updateMemberMenuState();
    }, 1000);
    
  } catch (error) {
    messageDiv.innerHTML = `<span class="error">✗ ${error.message}</span>`;
  }
}

/**
 * Register Handler
 */
async function handleRegister() {
  const email = document.getElementById('register-email').value;
  const password = document.getElementById('register-password').value;
  const messageDiv = document.getElementById('login-message');
  
  if (!email || !password) {
    messageDiv.innerHTML = '<span class="error">Bitte alle Felder ausfüllen</span>';
    return;
  }
  
  if (password.length < 6) {
    messageDiv.innerHTML = '<span class="error">Passwort muss mindestens 6 Zeichen haben</span>';
    return;
  }
  
  try {
    const { data, error } = await supabaseClient.auth.signUp({
      email: email,
      password: password
    });
    
    if (error) throw error;
    
    messageDiv.innerHTML = '<span class="success">✓ Registrierung erfolgreich!<br>Bitte bestätigen Sie Ihre E-Mail.</span>';
    
  } catch (error) {
    messageDiv.innerHTML = `<span class="error">✗ ${error.message}</span>`;
  }
}

/**
 * Text-Selektion tracken
 */
let lastSelection = '';
let lastSelectionContext = null;

function trackSelection() {
  const selection = window.getSelection().toString().trim();
  if (selection.length > 10) {
    lastSelection = selection;
    lastSelectionContext = {
      before: getContextBefore(selection, 100),
      after: getContextAfter(selection, 100)
    };
  }
}

/**
 * Quick-Save Funktionen
 */
async function quickSaveQuote() {
  if (!lastSelection) {
    showNotification('Bitte zuerst Text markieren!', 'info');
    return;
  }
  
  await initSupabase();
  
  if (!currentUser) {
    showNotification('Bitte zuerst anmelden!', 'info');
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
    
    showNotification('✓ Zitat gespeichert!', 'success');
    highlightLastSelection('#ffffcc');
  } catch (error) {
    console.error('Fehler:', error);
    showNotification('✗ Fehler beim Speichern', 'error');
  }
}

async function quickSaveBookmark() {
  if (!lastSelection) {
    showNotification('Bitte zuerst Text markieren!', 'info');
    return;
  }
  
  await initSupabase();
  
  if (!currentUser) {
    showNotification('Bitte zuerst anmelden!', 'info');
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
    
    showNotification('✓ Bookmark gespeichert!', 'success');
    highlightLastSelection('#ccffcc');
  } catch (error) {
    console.error('Fehler:', error);
    showNotification('✗ Fehler beim Speichern', 'error');
  }
}

function openQuickNote() {
  if (lastSelection) {
    const noteData = encodeURIComponent(JSON.stringify({
      content: `Aus [[${currentContext.gaNumber || 'Unbekannt'}]]:\n\n"${lastSelection}"\n\n`,
      title: `Notiz zu ${currentContext.gaNumber || 'Vortrag'}`
    }));
    window.location.href = `members.html?tab=notes&prefill=${noteData}`;
  } else {
    window.location.href = 'members.html?tab=notes';
  }
}

// Helper-Funktionen
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
 * Notification
 */
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `member-notification ${type}`;
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.opacity = '0';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

/**
 * Styles
 */
function addMenuStyles() {
  if (document.querySelector('#member-menu-styles')) return;
  
  const style = document.createElement('style');
  style.id = 'member-menu-styles';
  style.textContent = `
    /* Member Menu Container */
    #member-menu {
      position: fixed;
      top: 10px;
      right: 10px;
      z-index: 10000;
    }
    
    /* Member Icon (immer sichtbar) */
    .member-icon {
      width: 40px;
      height: 40px;
      background: transparent;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
      padding: 0;
      color: #467886;
      opacity: 0.75;
    }
    
    .member-icon:hover {
      transform: scale(1.15);
      opacity: 1;
    }
    
    /* Dark Mode */
    @media (prefers-color-scheme: dark) {
      .member-icon {
        color: #6BA3B8;
      }
    }
    
    /* Action Icons */
    .action-icons {
      position: absolute;
      top: 38px;
      right: 0;
      display: none;
      flex-direction: column;
      gap: 6px;
      background: white;
      padding: 6px;
      padding-top: 18px;
      margin-top: -10px;
      border-radius: 6px;
      border: 1px solid #467886;
      box-shadow: 0 2px 8px rgba(70, 120, 134, 0.15);
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.2s ease;
    }
    
    /* Nur bei eingeloggtem User anzeigen */
    #member-menu.logged-in:hover .action-icons {
      display: flex;
      pointer-events: auto;
      opacity: 1;
    }
    
    /* Action Icons bleiben offen wenn man über sie hovert */
    .action-icons:hover {
      display: flex;
      pointer-events: auto;
      opacity: 1;
    }
    
    /* Dark Mode für Panel */
    @media (prefers-color-scheme: dark) {
      .action-icons {
        background: #1a1a1a;
        border-color: #6BA3B8;
        box-shadow: 0 2px 8px rgba(107, 163, 184, 0.15);
      }
    }
    
    .action-btn {
      width: 36px;
      height: 36px;
      background: transparent;
      border: 1px solid #467886;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
      color: #467886;
      opacity: 0.8;
    }
    
    .action-btn:hover {
      background: rgba(70, 120, 134, 0.1);
      opacity: 1;
      transform: scale(1.08);
    }
    
    /* Dark Mode für Buttons */
    @media (prefers-color-scheme: dark) {
      .action-btn {
        border-color: #6BA3B8;
        color: #6BA3B8;
      }
      .action-btn:hover {
        background: rgba(107, 163, 184, 0.15);
      }
    }
    
    /* Login Modal */
    .login-modal {
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.5);
      z-index: 9999;
      justify-content: center;
      align-items: center;
    }
    
    .login-modal.open {
      display: flex;
    }
    
    .login-modal-content {
      background: white;
      padding: 30px;
      border-radius: 12px;
      max-width: 400px;
      width: 90%;
      position: relative;
      box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }
    
    .login-close {
      position: absolute;
      top: 10px;
      right: 10px;
      background: transparent;
      border: none;
      font-size: 32px;
      cursor: pointer;
      color: #999;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .login-close:hover {
      color: #333;
    }
    
    .login-modal-content h2 {
      margin: 0 0 20px 0;
      color: #467886;
      font-family: Georgia, serif;
    }
    
    @media (prefers-color-scheme: dark) {
      .login-modal-content {
        background: #1a1a1a;
        color: #b8b8b8;
      }
      .login-modal-content h2 {
        color: #6BA3B8;
      }
      .login-modal-content input {
        background: #2a2a2a;
        border-color: #6BA3B8;
        color: #b8b8b8;
      }
    }
    
    .login-modal-content input {
      width: 100%;
      padding: 12px;
      margin-bottom: 12px;
      border: 1px solid #ddd;
      border-radius: 6px;
      font-size: 1rem;
      font-family: Georgia, serif;
      box-sizing: border-box;
    }
    
    .login-modal-content button {
      width: 100%;
      padding: 12px;
      margin-bottom: 8px;
      background: #467886;
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 1rem;
      cursor: pointer;
      font-family: Georgia, serif;
      transition: background 0.2s;
    }
    
    .login-modal-content button:hover {
      background: #3a6270;
    }
    
    .login-modal-content button.secondary {
      background: transparent;
      color: #467886;
      border: 1px solid #467886;
    }
    
    .login-modal-content button.secondary:hover {
      background: #f5f5f5;
    }
    
    @media (prefers-color-scheme: dark) {
      .login-modal-content button {
        background: #6BA3B8;
      }
      .login-modal-content button:hover {
        background: #5a8fa0;
      }
      .login-modal-content button.secondary {
        background: transparent;
        border-color: #6BA3B8;
        color: #6BA3B8;
      }
      .login-modal-content button.secondary:hover {
        background: rgba(107, 163, 184, 0.15);
      }
      .login-close:hover {
        color: #b8b8b8;
      }
    }
    
    #login-message {
      margin-top: 15px;
      font-size: 0.9rem;
      text-align: center;
    }
    
    #login-message .error {
      color: #f44336;
    }
    
    #login-message .success {
      color: #4CAF50;
    }
    
    /* Notification */
    .member-notification {
      position: fixed;
      top: 60px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 8px;
      font-size: 0.9rem;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 10001;
      transition: opacity 0.3s;
      font-family: Georgia, serif;
    }
    
    .member-notification.success {
      background: #4CAF50;
      color: white;
    }
    
    .member-notification.error {
      background: #f44336;
      color: white;
    }
    
    .member-notification.info {
      background: #2196F3;
      color: white;
    }
    
    /* Dark Mode für Notifications */
    @media (prefers-color-scheme: dark) {
      .member-notification {
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
      }
    }
  `;
  document.head.appendChild(style);
}

// Global verfügbar machen
window.initMemberMenu = initMemberMenu;
window.handleMemberIconClick = handleMemberIconClick;
window.closeLoginModal = closeLoginModal;
window.showLoginForm = showLoginForm;
window.showRegisterForm = showRegisterForm;
window.handleLogin = handleLogin;
window.handleRegister = handleRegister;
window.quickSaveQuote = quickSaveQuote;
window.quickSaveBookmark = quickSaveBookmark;
window.openQuickNote = openQuickNote;

