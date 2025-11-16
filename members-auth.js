// ============================================
// GA-Suche Mitgliederbereich - Authentifizierung
// ============================================

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';

// ============================================
// Supabase Client Setup
// ============================================
// TODO: Diese Keys durch Ihre eigenen ersetzen!
const SUPABASE_URL = 'https://qygirjbfvzyhpgwhllzs.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF5Z2lyamJmdnp5aHBnd2hsbHpzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI4NjM4NjgsImV4cCI6MjA3ODQzOTg2OH0.8ePpjxvukwtxZMZ8GwDMKRmxhB1gFE41bv44PFvgVnA';

// Supabase Client initialisieren
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);


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

