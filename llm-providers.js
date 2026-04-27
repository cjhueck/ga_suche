// ============================================================================
// LLM PROVIDER ABSTRACTION
// ============================================================================
// 
// Unterstützt mehrere LLM-Anbieter: Claude, OpenAI, Gemini
// Ermöglicht flexible Provider-Auswahl per Umgebungsvariable

// Node.js 18+ hat fetch built-in, für ältere Versionen:
const fetch = globalThis.fetch || require('node-fetch');

function resolveClaudeApiKey() {
  const preferredAccount = (process.env.CLAUDE_API_KEY_ACTIVE || 'primary').toLowerCase();
  const prioritizedKeys = preferredAccount === 'secondary'
    ? [process.env.CLAUDE_API_KEY_SECONDARY, process.env.CLAUDE_API_KEY_PRIMARY]
    : [process.env.CLAUDE_API_KEY_PRIMARY, process.env.CLAUDE_API_KEY_SECONDARY];

  return prioritizedKeys.find(Boolean)
    || process.env.CLAUDE_API_KEY
    || process.env.ANTHROPIC_API_KEY
    || '';
}

// ============================================================================
// RATE-LIMIT TRACKING
// ============================================================================

// Speichert Provider die Rate-Limited sind mit Timeout
const rateLimitedProviders = new Map();
// Format: Map<providerName, { until: timestamp, reason: string }>

/**
 * Markiere einen Provider als Rate-Limited
 * @param {string} providerName - Name des Providers
 * @param {number} cooldownMinutes - Wie lange warten (Standard: 5 Minuten)
 */
function markProviderRateLimited(providerName, cooldownMinutes = 5) {
  const until = Date.now() + (cooldownMinutes * 60 * 1000);
  rateLimitedProviders.set(providerName.toLowerCase(), {
    until: until,
    reason: 'Rate Limit erreicht'
  });
  
  const untilDate = new Date(until).toLocaleTimeString('de-DE');
}

/**
 * Prüfe ob ein Provider aktuell Rate-Limited ist
 * @param {string} providerName
 * @returns {boolean}
 */
function isProviderRateLimited(providerName) {
  const entry = rateLimitedProviders.get(providerName.toLowerCase());
  
  if (!entry) return false;
  
  // Prüfe ob Cooldown abgelaufen
  if (Date.now() > entry.until) {
    // Cooldown vorbei - entferne aus Liste
    rateLimitedProviders.delete(providerName.toLowerCase());
    return false;
  }
  
  return true;
}

/**
 * Zeige Status aller Rate-Limited Provider (nur wenn es welche gibt)
 */
function showRateLimitStatus() {
  if (rateLimitedProviders.size === 0) {
    // Kein Log wenn alle verfügbar (zu viel Spam)
    return;
  }
  
  rateLimitedProviders.forEach((entry, name) => {
    const remaining = Math.ceil((entry.until - Date.now()) / 60000);
  });
}

// ============================================================================
// BASE PROVIDER CLASS
// ============================================================================

class LLMProvider {
  constructor(name) {
    this.name = name;
  }

  /**
   * Generiere eine Completion von einem Prompt
   * @param {string} prompt - Der Prompt-Text
   * @param {object} options - Optionen (maxTokens, temperature, etc.)
   * @returns {Promise<string>} - Die generierte Antwort
   */
  async generateCompletion(prompt, options = {}) {
    throw new Error('generateCompletion() must be implemented by subclass');
  }

  /**
   * Prüfe ob der Provider verfügbar ist (API-Key gesetzt)
   * @returns {boolean}
   */
  isAvailable() {
    throw new Error('isAvailable() must be implemented by subclass');
  }
}

// ============================================================================
// CLAUDE PROVIDER (Anthropic)
// ============================================================================

class ClaudeProvider extends LLMProvider {
  constructor() {
    super('Claude');
    this.apiKey = resolveClaudeApiKey();
  }

  isAvailable() {
    return !!this.apiKey;
  }

  async generateCompletion(prompt, options = {}) {
    if (!this.isAvailable()) {
      throw new Error('Claude API Key nicht gesetzt (CLAUDE_API_KEY_PRIMARY / CLAUDE_API_KEY_SECONDARY / CLAUDE_API_KEY)');
    }

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': this.apiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: options.model || 'claude-sonnet-4-20250514',
        max_tokens: options.maxTokens || 16384,  // Erhöht von 4096 auf 16384
        temperature: options.temperature || 0.7,
        messages: [{
          role: 'user',
          content: prompt
        }]
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch (e) {
        errorData = { error: { message: errorText } };
      }
      
      // Spezielle Fehlerbehandlung
      if (response.status === 429) {
        throw new Error(`[Claude] Rate Limit erreicht. Details: ${errorText}`);
      } else if (response.status === 402) {
        throw new Error(`[Claude] Budget aufgebraucht. Details: ${errorText}`);
      } else if (response.status === 401) {
        throw new Error(`[Claude] API-Key ungültig. Details: ${errorText}`);
      } else if (response.status === 400 && errorData?.error?.message?.includes('usage limits')) {
        // API-Nutzungslimit erreicht (Status 400 mit spezieller Meldung)
        const limitMessage = errorData.error.message;
        throw new Error(`[Claude] API-Nutzungslimit erreicht: ${limitMessage}`);
      } else if (response.status === 400 && errorData?.error?.message?.includes('prompt is too long')) {
        // Prompt zu lang - spezielle Behandlung
        const tokenCount = errorData.error.message.match(/(\d+) tokens/)?.[1] || 'unbekannt';
        throw new Error(`[Claude] Prompt zu lang: ${tokenCount} Tokens überschreiten das Maximum von 200.000 Tokens. Bitte die Suche spezifischer formulieren oder weniger Ergebnisse verwenden.`);
      }
      
      throw new Error(`[Claude] API Fehler ${response.status}: ${errorText}`);
    }

    const result = await response.json();
    return result.content[0].text;
  }
}

// ============================================================================
// GEMINI PROVIDER (Google AI Studio)
// ============================================================================

class GeminiProvider extends LLMProvider {
  constructor() {
    super('Gemini');
    this.apiKey = process.env.GEMINI_API_KEY;
  }

  isAvailable() {
    return !!this.apiKey;
  }

  async generateCompletion(prompt, options = {}) {
    if (!this.isAvailable()) {
      throw new Error('Gemini API Key nicht gesetzt (GEMINI_API_KEY)');
    }

    // Gemini 2.5 Flash - höheres Output-Limit (65k Tokens) und aktuelleres Modell
    const model = options.model || 'gemini-2.5-flash';
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${this.apiKey}`;
    

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text: prompt
          }]
        }],
        generationConfig: {
          temperature: options.temperature || 0.7,
          maxOutputTokens: options.maxTokens || 16384, // Erhöht von 8192 auf 16384
          topP: options.topP || 0.95
        }
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      
      // Gemini-spezifische Fehlerbehandlung
      if (response.status === 429) {
        throw new Error(`[Gemini] Rate Limit erreicht. Free Tier: 15 req/min, 1500 req/day. Details: ${errorText}`);
      } else if (response.status === 400) {
        throw new Error(`[Gemini] Ungültige Anfrage. Details: ${errorText}`);
      } else if (response.status === 403) {
        throw new Error(`[Gemini] API-Key ungültig oder Quota überschritten. Details: ${errorText}`);
      }
      
      throw new Error(`[Gemini] API Fehler ${response.status}: ${errorText}`);
    }

    const result = await response.json();
    
    // Gemini-Response-Struktur auspacken
    if (!result.candidates || result.candidates.length === 0) {
      throw new Error('[Gemini] Keine Antwort generiert (candidates leer)');
    }

    const candidate = result.candidates[0];
    
    // DEBUG: Zeige finishReason
    
    // Sicherheitsfilter prüfen
    if (candidate.finishReason === 'SAFETY') {
      throw new Error('[Gemini] Antwort durch Sicherheitsfilter blockiert');
    }
    
    // MAX_TOKENS prüfen (abgeschnitten!)
    if (candidate.finishReason === 'MAX_TOKENS') {
      console.warn('[Gemini] WARNUNG: Antwort wurde wegen Token-Limit abgeschnitten!');
      console.warn('[Gemini] maxOutputTokens war:', options.maxTokens || 8192);
      console.warn('[Gemini] Erhöhe maxTokens oder reduziere Themenanzahl!');
    }

    if (!candidate.content || !candidate.content.parts || candidate.content.parts.length === 0) {
      throw new Error('[Gemini] Ungültige Response-Struktur');
    }

    return candidate.content.parts[0].text;
  }
}

// ============================================================================
// OPENAI PROVIDER
// ============================================================================

class OpenAIProvider extends LLMProvider {
  constructor() {
    super('OpenAI');
    this.apiKey = process.env.OPENAI_API_KEY;
  }

  isAvailable() {
    return !!this.apiKey;
  }

  async generateCompletion(prompt, options = {}) {
    if (!this.isAvailable()) {
      throw new Error('OpenAI API Key nicht gesetzt (OPENAI_API_KEY)');
    }

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        model: options.model || 'gpt-4o',
        messages: [{
          role: 'user',
          content: prompt
        }],
        max_tokens: options.maxTokens || 16384,  // Erhöht von 4096 auf 16384
        temperature: options.temperature || 0.7
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      
      // OpenAI-spezifische Fehlerbehandlung
      if (response.status === 429) {
        throw new Error(`[OpenAI] Rate Limit erreicht. Details: ${errorText}`);
      } else if (response.status === 401) {
        throw new Error(`[OpenAI] API-Key ungültig. Details: ${errorText}`);
      } else if (response.status === 402) {
        throw new Error(`[OpenAI] Budget/Quota überschritten. Details: ${errorText}`);
      }
      
      throw new Error(`[OpenAI] API Fehler ${response.status}: ${errorText}`);
    }

    const result = await response.json();
    return result.choices[0].message.content;
  }
}

// ============================================================================
// PROVIDER FACTORY
// ============================================================================

/**
 * Erstelle einen LLM-Provider basierend auf Name
 * @param {string} providerName - 'claude', 'gemini', oder 'openai'
 * @returns {LLMProvider}
 */
function createProvider(providerName) {
  const name = (providerName || 'claude').toLowerCase();
  
  switch(name) {
    case 'claude':
      return new ClaudeProvider();
    case 'gemini':
      return new GeminiProvider();
    case 'openai':
      return new OpenAIProvider();
    default:
      throw new Error(`Unbekannter LLM Provider: ${providerName}`);
  }
}

/**
 * Hole den konfigurierten Provider für eine bestimmte Aufgabe
 * Fallback-Chain: Spezifischer Provider → Claude (default) → OpenAI → Gemini
 * @param {string} task - Aufgabentyp ('summary', 'keywords', 'themes', 'batch', 'analysis')
 * @returns {LLMProvider}
 */
function getProviderForTask(task) {
  // Task-spezifische Provider-Konfiguration aus .env
  const taskProviderMap = {
    'summary': process.env.LLM_PROVIDER_SUMMARY,
    'keywords': process.env.LLM_PROVIDER_KEYWORDS,
    'themes': process.env.LLM_PROVIDER_THEMES,
    'batch': process.env.LLM_PROVIDER_BATCH,
    'analysis': process.env.LLM_PROVIDER_ANALYSIS
  };

  const specificProvider = taskProviderMap[task];

  // Versuche task-spezifischen Provider
  if (specificProvider) {
    try {
      const provider = createProvider(specificProvider);
      if (provider.isAvailable()) {
        return provider;
      }
    } catch (error) {
      console.warn(`[LLM-PROVIDER] Task '${task}': Provider ${specificProvider} nicht verfügbar:`, error.message);
    }
  }

  // Fallback-Chain: Claude → OpenAI → Gemini
  const fallbackChain = ['claude', 'openai', 'gemini'];
  
  for (const providerName of fallbackChain) {
    try {
      const provider = createProvider(providerName);
      if (provider.isAvailable()) {
        return provider;
      }
    } catch (error) {
      console.warn(`[LLM-PROVIDER] Provider ${providerName} nicht verfügbar:`, error.message);
    }
  }

  throw new Error(`[LLM-PROVIDER] Kein verfügbarer LLM-Provider gefunden. Bitte API-Keys konfigurieren.`);
}

/**
 * NEU: Hole alle verfügbaren Provider in Prioritäts-Reihenfolge
 * Filtert Rate-Limited Provider automatisch heraus
 * @param {string} task - Aufgabentyp
 * @returns {LLMProvider[]} - Array von Providern (sortiert nach Priorität)
 */
function getAllAvailableProviders(task) {
  const providers = [];
  
  // Task-spezifischer Provider (höchste Priorität)
  const taskProviderMap = {
    'summary': process.env.LLM_PROVIDER_SUMMARY,
    'keywords': process.env.LLM_PROVIDER_KEYWORDS,
    'themes': process.env.LLM_PROVIDER_THEMES,
    'batch': process.env.LLM_PROVIDER_BATCH,
    'analysis': process.env.LLM_PROVIDER_ANALYSIS
  };
  
  const specificProviderName = taskProviderMap[task];
  
  // Prioritätsliste: Spezifisch → Claude (default) → OpenAI → Gemini
  const providerPriority = [];
  if (specificProviderName) providerPriority.push(specificProviderName.toLowerCase());
  // Fallback-Chain
  ['claude', 'openai', 'gemini'].forEach(name => {
    if (!providerPriority.includes(name)) {
      providerPriority.push(name);
    }
  });
  
  // Erstelle Provider-Instanzen für verfügbare
  // WICHTIG: Rate-Limited Provider werden NICHT mehr automatisch gefiltert,
  // damit sie trotzdem versucht werden können (falls Rate-Limit abgelaufen ist)
  for (const name of providerPriority) {
    try {
      const provider = createProvider(name);
      if (provider.isAvailable()) {
        // Prüfe Rate-Limit, aber füge trotzdem hinzu (mit Warnung)
        if (isProviderRateLimited(name)) {
          const entry = rateLimitedProviders.get(name.toLowerCase());
          const remaining = Math.ceil((entry.until - Date.now()) / 60000);
        }
        providers.push(provider);
      } else {
      }
    } catch (error) {
      // Provider nicht verfügbar - überspringen
    }
  }
  
  return providers;
}

/**
 * NEU: Intelligente Completion mit automatischem Fallback bei Rate-Limits
 * Versucht alle verfügbaren Provider nacheinander
 * @param {string} prompt - Der Prompt
 * @param {object} options - Optionen (maxTokens, temperature)
 * @param {string} task - Aufgabentyp für Provider-Auswahl
 * @returns {Promise<{text: string, provider: string}>}
 */
async function generateCompletionWithFallback(prompt, options = {}, task = 'keywords') {
  const providers = getAllAvailableProviders(task);
  
  if (providers.length === 0) {
    throw new Error('[LLM-FALLBACK] Keine verfügbaren Provider gefunden');
  }
  
  
  let lastError = null;
  
  for (let i = 0; i < providers.length; i++) {
    const provider = providers[i];
    
    try {
      
      const text = await provider.generateCompletion(prompt, options);
      
      
      return {
        text: text,
        provider: provider.name
      };
      
    } catch (error) {
      lastError = error;
      
      // Prüfe ob es ein Rate-Limit-Fehler ist
      const isRateLimit = error.message.includes('Rate Limit') || 
                         error.message.includes('429') ||
                         error.message.includes('quota');
      
      if (isRateLimit) {
        // Markiere Provider als Rate-Limited (5 Minuten Cooldown)
        markProviderRateLimited(provider.name, 5);
        console.warn(`[LLM-FALLBACK] 🔴 ${provider.name} Rate Limit → gesperrt für 5 Min`);
      } else {
        console.warn(`[LLM-FALLBACK] ⚠️ ${provider.name} Fehler: ${error.message}`);
      }
      
      // Wenn nicht der letzte Provider, versuche den nächsten
      if (i < providers.length - 1) {
        // Keine Pause nötig - Provider ist schon gefiltert
      }
    }
  }
  
  // Alle Provider fehlgeschlagen
  throw new Error(`[LLM-FALLBACK] Alle ${providers.length} Provider fehlgeschlagen. Letzter Fehler: ${lastError?.message}`);
}

// ============================================================================
// GET SPECIFIC PROVIDER (für explizite Auswahl)
// ============================================================================

/**
 * Hole einen spezifischen Provider (für explizite Nutzer-Auswahl)
 * @param {string} providerName - 'openai', 'claude', oder 'gemini'
 * @returns {LLMProvider}
 */
function getSpecificProvider(providerName) {
  const name = providerName.toLowerCase();
  
  // Prüfe ob Rate-Limited
  if (isProviderRateLimited(name)) {
    const entry = rateLimitedProviders.get(name);
    const minutesRemaining = Math.ceil((entry.until - Date.now()) / 60000);
    console.warn(`[PROVIDER] ⚠️ ${name} ist Rate-Limited (noch ${minutesRemaining} Min)`);
  }
  
  const provider = createProvider(name);
  
  if (!provider.isAvailable()) {
    throw new Error(`Provider ${name} ist nicht verfügbar (kein API-Key)`);
  }
  
  return provider;
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  LLMProvider,
  ClaudeProvider,
  GeminiProvider,
  OpenAIProvider,
  createProvider,
  getProviderForTask,
  getSpecificProvider,
  getAllAvailableProviders,
  generateCompletionWithFallback,
  markProviderRateLimited,
  isProviderRateLimited,
  showRateLimitStatus
};

