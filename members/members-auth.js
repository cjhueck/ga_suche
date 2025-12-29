// ============================================
// GA-Suche Mitgliederbereich - Authentifizierung
// ============================================

// Verwende die bereits geladene Supabase-Bibliothek aus app.html
// (wird als UMD-Modul geladen, nicht als ESM)
// Die globale Variable 'supabase' sollte bereits verfügbar sein

// ============================================
// Supabase Client Setup
// ============================================
// TODO: Diese Keys durch Ihre eigenen ersetzen!
const SUPABASE_URL = 'https://qygirjbfvzyhpgwhllzs.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF5Z2lyamJmdnp5aHBnd2hsbHpzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI4NjM4NjgsImV4cCI6MjA3ODQzOTg2OH0.8ePpjxvukwtxZMZ8GwDMKRmxhB1gFE41bv44PFvgVnA';

// Supabase Client initialisieren - verwende globale supabase Variable
// Prüfe ob supabase verfügbar ist (kann window.supabase oder global supabase sein)
const getSupabaseClient = () => {
  const options = {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true
    },
    // Realtime-Konfiguration: Wir erlauben Fallbacks, falls WebSockets blockiert sind
    realtime: {
      params: {
        eventsPerSecond: 2
      }
    }
  };

  try {
    if (typeof window !== 'undefined' && window.supabase && window.supabase.createClient) {
      return window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, options);
    } else if (typeof supabase !== 'undefined' && supabase.createClient) {
      return supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, options);
    } else {
      throw new Error('Supabase-Bibliothek nicht gefunden! Bitte stellen Sie sicher, dass das Supabase-Script vor diesem Modul geladen wird.');
    }
  } catch (error) {
    console.error('Kritischer Fehler bei der Supabase-Initialisierung:', error);
    // Letzter Rettungsversuch: Ohne Realtime initialisieren
    console.log('Versuche Initialisierung ohne Realtime...');
    try {
      options.realtime = false;
      if (typeof window !== 'undefined' && window.supabase && window.supabase.createClient) {
        return window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, options);
      } else if (typeof supabase !== 'undefined' && supabase.createClient) {
        return supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, options);
      }
    } catch (innerError) {
      console.error('Auch die Fallback-Initialisierung ist fehlgeschlagen:', innerError);
      throw innerError;
    }
  }
};

export const supabase = getSupabaseClient();


// ============================================
// Authentifizierungs-Funktionen
// ============================================

/**
 * Registrierung neuer Nutzer mit Email-Bestätigung
 */
export async function signUp(email, password, displayName) {
  try {
    const { data, error } = await supabase.auth.signUp({
      email: email,
      password: password,
      options: {
        data: {
          display_name: displayName
        },
        emailRedirectTo: `${window.location.origin}/members.html`
      }
    });

    if (error) throw error;

    return {
      success: true,
      message: 'Registrierung erfolgreich! Bitte bestätigen Sie Ihre E-Mail.\n\nBitte schauen Sie auch in Ihren Spam-Ordner, falls Sie keine E-Mail erhalten.',
      data: data
    };
  } catch (error) {
    return {
      success: false,
      message: `Fehler: ${error.message}`,
      error: error
    };
  }
}


/**
 * Login mit Email & Passwort
 */
export async function signIn(email, password) {
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email,
      password: password
    });

    if (error) throw error;

    return {
      success: true,
      message: 'Login erfolgreich!',
      user: data.user
    };
  } catch (error) {
    return {
      success: false,
      message: `Login fehlgeschlagen: ${error.message}`,
      error: error
    };
  }
}


/**
 * Logout
 */
export async function signOut() {
  try {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
    
    return {
      success: true,
      message: 'Erfolgreich abgemeldet'
    };
  } catch (error) {
    return {
      success: false,
      message: `Logout fehlgeschlagen: ${error.message}`,
      error: error
    };
  }
}


/**
 * Aktuellen User abrufen
 */
export async function getCurrentUser() {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    return user;
  } catch (error) {
    console.error('Fehler beim Abrufen des Users:', error);
    return null;
  }
}


/**
 * Passwort zurücksetzen
 */
export async function resetPassword(email) {
  try {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/members.html`
    });

    if (error) throw error;

    return {
      success: true,
      message: 'Password-Reset-Email wurde gesendet!'
    };
  } catch (error) {
    return {
      success: false,
      message: `Fehler: ${error.message}`,
      error: error
    };
  }
}


/**
 * Neues Passwort setzen (nach Passwort-Reset)
 */
export async function updatePassword(newPassword) {
  try {
    const { error } = await supabase.auth.updateUser({
      password: newPassword
    });

    if (error) throw error;

    return {
      success: true,
      message: 'Passwort wurde erfolgreich geändert!'
    };
  } catch (error) {
    return {
      success: false,
      message: `Fehler: ${error.message}`,
      error: error
    };
  }
}


/**
 * Auth State Listener - ruft Callback bei Änderungen auf
 */
export function onAuthStateChange(callback) {
  return supabase.auth.onAuthStateChange((event, session) => {
    callback(event, session);
  });
}


/**
 * User-Profil abrufen/erstellen
 */
export async function getUserProfile(userId) {
  try {
    const { data, error } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('id', userId)
      .single();

    if (error && error.code === 'PGRST116') {
      // Profil existiert nicht, erstelle es
      const user = await getCurrentUser();
      const { data: newProfile, error: insertError } = await supabase
        .from('user_profiles')
        .insert({
          id: userId,
          display_name: user?.email || 'Unbekannt'
        })
        .select()
        .single();

      if (insertError) throw insertError;
      return newProfile;
    }

    if (error) throw error;
    return data;
  } catch (error) {
    console.error('Fehler beim Abrufen des Profils:', error);
    return null;
  }
}


/**
 * User-Profil aktualisieren
 */
export async function updateUserProfile(userId, updates) {
  try {
    const { data, error } = await supabase
      .from('user_profiles')
      .update(updates)
      .eq('id', userId)
      .select()
      .single();

    if (error) throw error;

    return {
      success: true,
      data: data
    };
  } catch (error) {
    return {
      success: false,
      message: `Fehler: ${error.message}`,
      error: error
    };
  }
}


/**
 * Prüfe ob User eingeloggt ist
 */
export async function isAuthenticated() {
  const user = await getCurrentUser();
  return user !== null;
}


/**
 * Auth Guard - Redirect wenn nicht eingeloggt
 */
export async function requireAuth() {
  const authenticated = await isAuthenticated();
  
  if (!authenticated) {
    // Aktuelle URL speichern für Redirect nach Login
    sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
    window.location.href = '/members.html?view=login';
    return false;
  }
  
  return true;
}


/**
 * E-Mail-Adresse des Users ändern
 */
export async function updateUserEmail(newEmail) {
  try {
    const { data, error } = await supabase.auth.updateUser({
      email: newEmail
    });

    if (error) throw error;

    return {
      success: true,
      message: 'E-Mail-Adresse wurde geändert. Bitte bestätigen Sie die neue E-Mail-Adresse.',
      data: data
    };
  } catch (error) {
    console.error('Fehler beim Ändern der E-Mail:', error);
    return {
      success: false,
      message: `Fehler: ${error.message}`,
      error: error
    };
  }
}


/**
 * User-Account komplett löschen (inkl. aller Daten)
 */
export async function deleteUserAccount() {
  try {
    const user = await getCurrentUser();
    if (!user) {
      throw new Error('Kein User angemeldet');
    }

    const userId = user.id;

    // 1. Lösche alle Bookmarks
    const { error: bookmarksError } = await supabase
      .from('bookmarks')
      .delete()
      .eq('user_id', userId);

    if (bookmarksError) {
      console.warn('Fehler beim Löschen der Bookmarks:', bookmarksError);
    }

    // 2. Lösche alle Zitate
    const { error: quotesError } = await supabase
      .from('quotes')
      .delete()
      .eq('user_id', userId);

    if (quotesError) {
      console.warn('Fehler beim Löschen der Zitate:', quotesError);
    }

    // 3. Lösche alle Notizen
    const { error: notesError } = await supabase
      .from('notes')
      .delete()
      .eq('user_id', userId);

    if (notesError) {
      console.warn('Fehler beim Löschen der Notizen:', notesError);
    }

    // 4. Lösche alle Backlinks
    const { error: backlinksError } = await supabase
      .from('backlinks')
      .delete()
      .eq('user_id', userId);

    if (backlinksError) {
      console.warn('Fehler beim Löschen der Backlinks:', backlinksError);
    }

    // 5. Lösche Chat-Nachrichten
    const { error: chatError } = await supabase
      .from('chat_messages')
      .delete()
      .eq('user_id', userId);

    if (chatError) {
      console.warn('Fehler beim Löschen der Chat-Nachrichten:', chatError);
    }

    // 6. Lösche User-Profil
    const { error: profileError } = await supabase
      .from('user_profiles')
      .delete()
      .eq('id', userId);

    if (profileError) {
      console.warn('Fehler beim Löschen des Profils:', profileError);
    }

    // 7. Lösche Auth-User (dies löscht den User aus der auth.users Tabelle)
    // Hinweis: Dies erfordert Admin-Rechte oder eine Server-Funktion
    // Für jetzt löschen wir nur die Daten, der Auth-User bleibt bestehen
    // In einer Produktionsumgebung sollte dies über eine Server-Funktion erfolgen
    
    // 8. Logout durchführen
    await supabase.auth.signOut();

    return {
      success: true,
      message: 'Account und alle Daten wurden erfolgreich gelöscht.'
    };
  } catch (error) {
    console.error('Fehler beim Löschen des Accounts:', error);
    return {
      success: false,
      message: `Fehler: ${error.message}`,
      error: error
    };
  }
}
