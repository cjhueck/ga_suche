/**
 * THEMATIC CHAT UI for ga_suche Abfrage tab
 *
 * REVERT (3 steps):
 *   1. Set THEMATIC_CHAT_UI_ENABLED = false below (or delete this file)
 *   2. Remove <link> + <script> tags for thematic-chat-ui.* in app.html
 *   3. Remove // THEMATIC-CHAT-UI hooks block in app.js + backend.js conversationHistory
 */
(function () {
  'use strict';

  /** Master switch — set to false to restore the legacy textarea UI instantly */
  const THEMATIC_CHAT_UI_ENABLED = true;

  if (!THEMATIC_CHAT_UI_ENABLED) return;

  const state = {
    turns: [],
    activeTurnId: null,
    pendingLoadingId: null,
    isRunning: false
  };

  const CHAT_INPUT_MIN_H = 96;
  const CHAT_INPUT_MAX_H = 200;

  const MODE_LABELS = {
    chat: 'Chat',
    deep: 'Tiefe',
    broad: 'Breite',
    quote: 'Zitat',
    essay: 'Essay',
    recherche: 'Recherche',
    internet: '+ Internet'
  };

  function $(id) { return document.getElementById(id); }

  function getSelectedModeRadio() {
    return document.querySelector('input[name="thematicMode"]:checked');
  }

  function getHeaderAnalysisMode() {
    const radio = getSelectedModeRadio();
    return radio ? radio.value : 'deep';
  }

  function isChatOutputModeActive() {
    const radio = getSelectedModeRadio();
    return !radio || radio.value === 'chat';
  }

  function onThematicModeChange() {
    updateChatInternetToggleState();
    if (typeof updateRechercheControlsVisibility === 'function') {
      updateRechercheControlsVisibility();
    }
  }

  function selectThematicMode(mode) {
    const radio = document.querySelector(`input[name="thematicMode"][value="${mode}"]`);
    if (radio) radio.checked = true;
    onThematicModeChange();
  }

  function activateChat(options = {}) {
    selectThematicMode('chat');
    const cb = $('thematicChatInternet');
    if (cb && options.internet) cb.checked = true;
    updateChatInternetToggleState();
  }

  function syncHeaderModeFromMode(mode) {
    if (!mode || mode === 'chat') return;
    const headerMode = mode === 'internet' ? 'deep' : mode;
    selectThematicMode(headerMode);
  }

  function syncModeForTurn(turnData) {
    if (!turnData) return;
    const mode = turnData.mode || 'chat';
    if (mode === 'chat' || mode === 'internet') {
      activateChat({ internet: mode === 'internet' });
    } else {
      syncHeaderModeFromMode(mode);
    }
  }

  function isChatInternetEnabled() {
    const cb = $('thematicChatInternet');
    return !!(cb && cb.checked && !cb.disabled);
  }

  function updateChatInternetToggleState() {
    const cb = $('thematicChatInternet');
    const label = $('thematicChatInternetLabel');
    if (!cb || !label) return;
    const chatActive = isChatOutputModeActive();
    cb.disabled = !chatActive;
    label.classList.toggle('is-disabled', !chatActive);
    if (!chatActive) cb.checked = false;
  }

  /** Effektiver API-Modus: Chat aktiv → 'chat' oder 'internet'; sonst Modus oben */
  function getEffectiveSearchMode() {
    if (!isChatOutputModeActive()) {
      const headerMode = getHeaderAnalysisMode();
      return headerMode === 'internet' ? 'deep' : headerMode;
    }
    if (isChatInternetEnabled()) return 'internet';
    return 'chat';
  }

  function getDisplayModeLabel(mode) {
    if (mode === 'internet' && isChatOutputModeActive()) return 'Chat · + Internet';
    return MODE_LABELS[mode] || mode;
  }

  function getSelectedMode() {
    return getEffectiveSearchMode();
  }

  function getGaFilterLabel() {
    if (typeof getThematicGAFilterValue !== 'function') return '';
    const arr = getThematicGAFilterValue();
    return arr && arr.length ? arr.join(', ') : '';
  }

  function makePreview(text, maxLen = 220) {
    let s = String(text || '')
      .replace(/<[^>]+>/g, ' ')
      .replace(/[#*_`]/g, '')
      .replace(/\s+/g, ' ')
      .trim();
    if (s.length > maxLen) s = s.substring(0, maxLen) + '…';
    return s || '(Keine Antwort)';
  }

  function scrollMessagesToBottom() {
    const el = $('thematic-chat-messages');
    if (el) el.scrollTop = el.scrollHeight;
  }

  function renderMessages() {
    const container = $('thematic-chat-messages');
    if (!container) return;

    if (!state.turns.length && !state.pendingLoadingId) {
      container.innerHTML = '';
      return;
    }

    let html = '';
    for (const turn of state.turns) {
      if (turn.role === 'user') {
        const chips = [
          turn.mode ? `<span class="thematic-chat-chip">${escapeHtml(getDisplayModeLabel(turn.mode))}</span>` : '',
          turn.gaFilter ? `<span class="thematic-chat-chip">${escapeHtml(turn.gaFilter)}</span>` : ''
        ].join('');
        html += `<div class="thematic-chat-bubble user" data-turn-id="${turn.id}">
          ${chips ? `<div class="thematic-chat-bubble-meta">${chips}</div>` : ''}
          <div>${escapeHtml(turn.content)}</div>
        </div>`;
      } else if (turn.role === 'assistant') {
        const active = turn.id === state.activeTurnId ? ' active-turn' : '';
        html += `<div class="thematic-chat-bubble assistant${active}" data-turn-id="${turn.id}" role="button" tabindex="0" title="Im Hauptfenster anzeigen">
          <div class="thematic-chat-bubble-meta">${escapeHtml(turn.modeLabel || '')}</div>
          <div class="thematic-chat-bubble-preview">${escapeHtml(turn.preview)}</div>
          <div class="thematic-chat-bubble-hint">→ Im Hauptfenster anzeigen</div>
        </div>`;
      } else if (turn.role === 'error') {
        html += `<div class="thematic-chat-bubble error" data-turn-id="${turn.id}">
          <div>${escapeHtml(turn.content)}</div>
        </div>`;
      }
    }

    if (state.pendingLoadingId) {
      html += `<div class="thematic-chat-bubble assistant loading" id="${state.pendingLoadingId}">Antwort wird erstellt…</div>`;
    }

    container.innerHTML = html;
    scrollMessagesToBottom();
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function addUserTurn(query, mode, gaFilter) {
    const turn = {
      id: 'u-' + Date.now(),
      role: 'user',
      content: query,
      mode,
      gaFilter
    };
    state.turns.push(turn);
    renderMessages();
    return turn;
  }

  function startLoading() {
    state.pendingLoadingId = 'loading-' + Date.now();
    renderMessages();
  }

  function stopLoading() {
    state.pendingLoadingId = null;
    const el = state.pendingLoadingId && $(state.pendingLoadingId);
    if (el) el.remove();
    state.pendingLoadingId = null;
    renderMessages();
  }

  function addAssistantTurn(data) {
    state.pendingLoadingId = null;
    const turn = {
      id: 'a-' + Date.now(),
      role: 'assistant',
      preview: makePreview(data.content),
      modeLabel: data.modeLabel || '',
      viewerData: data.viewerData
    };
    if (turn.viewerData) turn.viewerData.turnId = turn.id;
    state.turns.push(turn);
    state.activeTurnId = turn.id;
    renderMessages();
    return turn;
  }

  function addErrorTurn(message) {
    state.pendingLoadingId = null;
    state.turns.push({
      id: 'e-' + Date.now(),
      role: 'error',
      content: message
    });
    renderMessages();
  }

  function getConversationHistory() {
    const history = [];
    let turns = state.turns;
    // Laufende Anfrage: letzten User-Turn nicht mitschicken (steht separat als query)
    if (state.pendingLoadingId && turns.length && turns[turns.length - 1].role === 'user') {
      turns = turns.slice(0, -1);
    }
    for (const turn of turns) {
      if (turn.role === 'user') {
        history.push({ role: 'user', content: turn.content });
      } else if (turn.role === 'assistant' && turn.viewerData?.content) {
        history.push({ role: 'assistant', content: turn.viewerData.content });
      }
    }
    return history.slice(-6);
  }

  function updateActionButton() {
    const sendBtn = $('thematicChatSendBtn');
    const input = $('thematicChatInput');
    if (!sendBtn) return;

    const hasText = !!(input && input.value.trim());
    sendBtn.classList.toggle('is-running', state.isRunning);

    if (state.isRunning) {
      sendBtn.disabled = false;
      sendBtn.title = 'Stoppen';
      sendBtn.setAttribute('aria-label', 'Stoppen');
    } else {
      sendBtn.disabled = !hasText;
      sendBtn.title = hasText ? 'Senden' : 'Nachricht eingeben';
      sendBtn.setAttribute('aria-label', hasText ? 'Senden' : 'Nachricht eingeben');
    }
  }

  function setRunning(running) {
    state.isRunning = !!running;
    updateActionButton();
  }

  function getQueryText() {
    const input = $('thematicChatInput');
    return input ? input.value.trim() : '';
  }

  function clearInput() {
    const input = $('thematicChatInput');
    if (input) {
      input.value = '';
      input.style.height = CHAT_INPUT_MIN_H + 'px';
      updateActionButton();
    }
  }

  function syncLegacyTextarea(query) {
    const legacy = $('thematicQuery');
    if (legacy) legacy.value = query;
  }

  function getActiveViewerData() {
    const turn = state.turns.find(t => t.id === state.activeTurnId);
    return turn?.viewerData || null;
  }

  function setActiveTurnByViewerData(data) {
    if (!data) return;
    const match = data.turnId
      ? state.turns.find(t => t.id === data.turnId)
      : state.turns.find(t => t.role === 'assistant' && t.viewerData?.query === data.query);
    if (match) {
      state.activeTurnId = match.id;
      renderMessages();
    }
  }

  function replayTurn(turnId) {
    const turn = state.turns.find(t => t.id === turnId);
    if (!turn || !turn.viewerData) return;
    const wasAlreadyActive = state.activeTurnId === turnId;
    const previousViewerData = wasAlreadyActive ? null : getActiveViewerData();
    state.activeTurnId = turnId;
    renderMessages();
    syncModeForTurn(turn.viewerData);
    if (typeof window.replayThematicTurn === 'function') {
      window.replayThematicTurn(turn.viewerData, {
        skipPush: wasAlreadyActive,
        force: true,
        previousViewerData
      });
    }
  }

  function bindMessageClicks() {
    if (document.body.dataset.thematicChatClickBound === '1') return;
    document.body.dataset.thematicChatClickBound = '1';

    document.addEventListener('click', (e) => {
      if (!THEMATIC_CHAT_UI_ENABLED || !window.ThematicChatUI?.enabled) return;
      const bubble = e.target.closest('#thematic-chat-panel .thematic-chat-bubble.assistant:not(.loading)');
      if (!bubble) return;
      e.preventDefault();
      e.stopPropagation();
      const turnId = bubble.getAttribute('data-turn-id');
      if (turnId) replayTurn(turnId);
    });

    document.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      if (!THEMATIC_CHAT_UI_ENABLED || !window.ThematicChatUI?.enabled) return;
      const bubble = e.target.closest('#thematic-chat-panel .thematic-chat-bubble.assistant:focus-within, #thematic-chat-panel .thematic-chat-bubble.assistant[tabindex="0"]:focus');
      if (!bubble || bubble.classList.contains('loading')) return;
      e.preventDefault();
      const turnId = bubble.getAttribute('data-turn-id');
      if (turnId) replayTurn(turnId);
    });
  }

  function clearChat() {
    if (state.turns.length && !confirm('Chat-Verlauf löschen?')) return;
    state.turns = [];
    state.activeTurnId = null;
    state.pendingLoadingId = null;
    renderMessages();
  }

  function getSaveableViewerData() {
    const active = getActiveViewerData();
    if (active) return active;
    for (let i = state.turns.length - 1; i >= 0; i--) {
      const turn = state.turns[i];
      if (turn.role === 'assistant' && turn.viewerData && !turn.error) {
        return turn.viewerData;
      }
    }
    return null;
  }

  function syncSavePayloadFromActiveTurn() {
    const vd = getSaveableViewerData();
    if (!vd || typeof window.syncThematicSavePayload !== 'function') return false;

    const gaFilterRaw = vd.gaFilter || '';
    window.syncThematicSavePayload({
      query: vd.query,
      mode: vd.mode,
      gaFilter: gaFilterRaw.replace(/,\s+/g, ','),
      sources: vd.sources || [],
      rechercheData: vd.rechercheData || null,
      rechercheScope: vd.rechercheScope || null
    });

    if (typeof window.replayThematicTurn === 'function') {
      window.replayThematicTurn(vd, { skipPush: true, force: true });
    }
    return true;
  }

  async function toggleMenu() {
    const menu = $('thematic-chat-menu');
    if (!menu) return;
    const willOpen = !menu.classList.contains('open');
    if (willOpen) {
      if (typeof window.ensureThematicMemberSaveAccess === 'function') {
        const hasAccess = await window.ensureThematicMemberSaveAccess({ showNotice: true });
        if (!hasAccess) return;
      }
    }
    menu.classList.toggle('open');
    if (willOpen && typeof window.onThematicChatMenuOpen === 'function') {
      window.onThematicChatMenuOpen();
    }
  }

  function updateMenuMemberAccess(hasAccess) {
    const menuBtn = $('thematic-chat-menu-btn');
    if (menuBtn) {
      menuBtn.disabled = !hasAccess;
      menuBtn.classList.toggle('is-disabled', !hasAccess);
      menuBtn.title = hasAccess ? 'Funktionsmenü' : 'Funktionsmenü (Mitglieder-Anmeldung erforderlich)';
    }
    if (!hasAccess) closeMenu();
  }

  function updateMemberSaveHint(show) {
    updateMenuMemberAccess(!show);
  }

  async function handleMenuSave() {
    closeMenu();
    if (typeof window.ensureThematicMemberSaveAccess === 'function') {
      if (!(await window.ensureThematicMemberSaveAccess({ showNotice: true }))) return;
    }
    syncSavePayloadFromActiveTurn();
    if (typeof window.saveCurrentThematicSearch === 'function') {
      await window.saveCurrentThematicSearch();
    }
  }

  async function handleMenuSaved() {
    closeMenu();
    if (typeof window.ensureThematicMemberSaveAccess === 'function') {
      if (!(await window.ensureThematicMemberSaveAccess({ showNotice: true }))) return;
    }
    if (typeof window.showSavedThematicSearches === 'function') {
      await window.showSavedThematicSearches();
    }
  }

  async function handleMenuClear() {
    closeMenu();
    if (typeof window.ensureThematicMemberSaveAccess === 'function') {
      if (!(await window.ensureThematicMemberSaveAccess({ showNotice: true }))) return;
    }
    clearChat();
  }

  function closeMenu() {
    const menu = $('thematic-chat-menu');
    if (menu) menu.classList.remove('open');
  }

  function displaySavedSearches(searches) {
    const overlay = $('thematic-chat-saved-overlay');
    const list = $('thematic-chat-saved-list');
    if (!overlay || !list) {
      return false;
    }

    closeMenu();
    overlay.classList.add('open');

    if (!searches.length) {
      list.innerHTML = '<p style="color: var(--secondary-text); font-size: 0.84rem;">Keine gespeicherten Abfragen.</p>';
      return true;
    }

    let html = '<ul class="thematic-saved-list">';
    searches.forEach(search => {
      const date = new Date(search.created_at).toLocaleDateString('de-DE', {
        day: '2-digit', month: '2-digit', year: 'numeric'
      });
      const q = search.query.length > 55 ? search.query.substring(0, 55) + '…' : search.query;
      const safeId = escapeHtml(String(search.id || ''));
      html += `<li class="thematic-saved-item">
        <div class="thematic-saved-item-row">
          <a href="#" class="thematic-saved-link" data-id="${safeId}">${escapeHtml(q)}</a>
          <button type="button" class="thematic-saved-delete-btn" data-id="${safeId}" title="Abfrage löschen" aria-label="Abfrage löschen">
            <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" focusable="false">
              <path fill="currentColor" d="M9 3h6l1 2h4v2H4V5h4l1-2zm1 6h2v9h-2V9zm4 0h2v9h-2V9zM7 9h2v9H7V9z"/>
            </svg>
          </button>
        </div>
        <div class="thematic-saved-date">${escapeHtml(date)}</div>
      </li>`;
    });
    html += '</ul>';
    list.innerHTML = html;
    bindSavedListActions();
    return true;
  }

  function bindSavedListActions() {
    const list = $('thematic-chat-saved-list');
    if (!list || list.dataset.actionsBound === '1') return;
    list.dataset.actionsBound = '1';
    list.addEventListener('click', (e) => {
      const btn = e.target.closest('.thematic-saved-delete-btn');
      if (btn) {
        e.preventDefault();
        e.stopPropagation();
        const id = btn.getAttribute('data-id');
        if (id && typeof window.deleteSavedThematicSearch === 'function') {
          window.deleteSavedThematicSearch(id);
        }
        return;
      }
      const link = e.target.closest('.thematic-saved-link');
      if (link) {
        e.preventDefault();
        const id = link.getAttribute('data-id');
        if (id && typeof window.loadSavedThematicSearch === 'function') {
          window.loadSavedThematicSearch(id);
          closeSavedOverlay();
        }
      }
    });
  }

  function closeSavedOverlay() {
    const overlay = $('thematic-chat-saved-overlay');
    if (overlay) overlay.classList.remove('open');
  }

  function handleActionClick() {
    if (state.isRunning) {
      if (typeof window.cancelThematicSearch === 'function') {
        window.cancelThematicSearch();
      }
      return;
    }
    handleSend();
  }

  function handleSend() {
    const fn = window.performThematicSearch;
    if (typeof fn !== 'function') return;
    const query = getQueryText();
    if (!query) return;
    syncLegacyTextarea(query);
    clearInput();
    fn(false, query);
  }

  function handleInputKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (state.isRunning) return;
      handleSend();
    }
  }

  function autoResizeInput() {
    const input = $('thematicChatInput');
    if (!input) return;
    input.style.height = 'auto';
    input.style.height = Math.max(CHAT_INPUT_MIN_H, Math.min(input.scrollHeight, CHAT_INPUT_MAX_H)) + 'px';
    updateActionButton();
  }

  function onSearchStart(query) {
    if (typeof window.clearThematicViewerStack === 'function') {
      window.clearThematicViewerStack();
    }
    const mode = getSelectedMode();
    addUserTurn(query, mode, getGaFilterLabel());
    startLoading();
    setRunning(true);
  }

  function onSearchComplete(payload) {
    setRunning(false);

    const mode = payload.mode || getSelectedMode();
    let modeLabel = getDisplayModeLabel(mode);
    if (payload.gaFilter) modeLabel += ' · ' + payload.gaFilter;

    addAssistantTurn({
      content: payload.content,
      modeLabel,
      viewerData: {
        query: payload.query,
        content: payload.content,
        sources: payload.sources || [],
        gaFilter: payload.gaFilter || '',
        mode,
        rechercheData: payload.rechercheData || null,
        rechercheScope: payload.rechercheScope || null
      }
    });
  }

  function onSearchError(message) {
    setRunning(false);
    addErrorTurn(message || 'Suche fehlgeschlagen.');
  }

  function onSearchCancelled() {
    state.pendingLoadingId = null;
    setRunning(false);
    renderMessages();
  }

  let eventsBound = false;

  function bindElementEvents() {
    if (eventsBound) {
      onThematicModeChange();
      return;
    }
    eventsBound = true;
    const sendBtn = $('thematicChatSendBtn');
    const input = $('thematicChatInput');
    const menuBtn = $('thematic-chat-menu-btn');
    const menuSave = $('thematic-chat-menu-save');
    const menuSaved = $('thematic-chat-menu-saved');
    const menuClear = $('thematic-chat-menu-clear');
    const savedBack = $('thematic-chat-saved-back');

    if (sendBtn) sendBtn.addEventListener('click', handleActionClick);
    if (input) {
      input.addEventListener('keydown', handleInputKeydown);
      input.addEventListener('input', autoResizeInput);
    }
    updateActionButton();
    if (menuBtn) menuBtn.addEventListener('click', (e) => { e.stopPropagation(); toggleMenu(); });
    if (menuSave) menuSave.addEventListener('click', () => { handleMenuSave(); });
    if (menuSaved) menuSaved.addEventListener('click', () => { handleMenuSaved(); });
    if (menuClear) menuClear.addEventListener('click', () => { handleMenuClear(); });
    if (savedBack) savedBack.addEventListener('click', closeSavedOverlay);

    bindSavedListActions();

    document.querySelectorAll('input[name="thematicMode"]').forEach((radio) => {
      radio.addEventListener('change', onThematicModeChange);
    });

    onThematicModeChange();
  }

  let panelHome = null;

  function mountChatToSidebar() {
    const panel = $('thematic-chat-panel');
    const sidebarContent = $('sidebar-content');
    if (!panel || !sidebarContent || panel.dataset.mounted === '1') return;

    panelHome = {
      parent: panel.parentElement,
      next: panel.nextElementSibling
    };
    sidebarContent.insertBefore(panel, sidebarContent.firstChild);
    panel.dataset.mounted = '1';

    const results = $('results');
    if (results) {
      results.dataset.chatPrevDisplay = results.style.display || '';
      results.style.display = 'none';
    }
  }

  function unmountChatFromSidebar() {
    const panel = $('thematic-chat-panel');
    if (!panel || !panelHome) return;

    if (panelHome.next) {
      panelHome.parent.insertBefore(panel, panelHome.next);
    } else {
      panelHome.parent.appendChild(panel);
    }
    delete panel.dataset.mounted;
    panelHome = null;

    const results = $('results');
    if (results && results.dataset.chatPrevDisplay !== undefined) {
      results.style.display = results.dataset.chatPrevDisplay;
      delete results.dataset.chatPrevDisplay;
    }
  }

  /** Call before tab innerHTML snapshots (switchTabExtended). */
  function prepareTabSwitch() {
    eventsBound = false;
    unmountChatFromSidebar();
  }

  function onTabActivate() {
    document.body.classList.add('thematic-chat-enabled');
    mountChatToSidebar();
    eventsBound = false;
    bindElementEvents();
    bindMessageClicks();
    if (typeof updateRechercheControlsVisibility === 'function') {
      updateRechercheControlsVisibility();
    }
    if (!getSelectedModeRadio()) activateChat();
    else onThematicModeChange();
    autoResizeInput();
    renderMessages();
  }

  function onTabDeactivate() {
    eventsBound = false;
    unmountChatFromSidebar();
    document.body.classList.remove('thematic-chat-enabled');
    closeMenu();
    closeSavedOverlay();
  }

  function init() {
    document.addEventListener('click', () => closeMenu());
    bindMessageClicks();

    const thematicTab = $('thematic-tab');
    if (thematicTab && thematicTab.classList.contains('active')) {
      onTabActivate();
    }

    renderMessages();
    console.log('[THEMATIC-CHAT] UI aktiv (Revert: THEMATIC_CHAT_UI_ENABLED=false)');
  }

  window.ThematicChatUI = {
    enabled: true,
    getQueryText,
    getConversationHistory,
    shouldSkipRecentQueries: () => true,
    onSearchStart,
    onSearchComplete,
    onSearchError,
    onSearchCancelled,
    onTabActivate,
    onTabDeactivate,
    prepareTabSwitch,
    displaySavedSearches,
    replayTurn,
    getActiveViewerData,
    setActiveTurnByViewerData,
    getEffectiveSearchMode,
    isChatOutputModeActive,
    activateChat,
    syncModeForTurn,
    updateMemberSaveHint,
    updateMenuMemberAccess,
    syncSavePayloadFromActiveTurn,
    closeSavedOverlay,
    clearChat
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
