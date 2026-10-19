// Leitet Supabase-Auth-Callbacks (Passwort-Reset, Magic Link) von beliebigen Seiten auf members.html weiter.
(function () {
  try {
    var path = (window.location.pathname || '').split('/').pop();
    if (path === 'members.html') return;

    var hash = window.location.hash || '';
    var search = window.location.search || '';
    if (!hash && !search) return;

    var hashBody = hash.charAt(0) === '#' ? hash.slice(1) : hash;
    var hashParams = new URLSearchParams(hashBody);
    var searchParams = new URLSearchParams(search);
    var type = hashParams.get('type') || searchParams.get('type');
    var isRecovery = type === 'recovery';
    var hasAccessToken = hashParams.has('access_token');
    var hasCode = searchParams.has('code');
    var hasAuthError = hashParams.has('error') || searchParams.has('error');

    if (!isRecovery && !hasAccessToken && !hasCode && !hasAuthError) return;

    window.location.replace('members.html' + search + hash);
  } catch (e) {
    // Weiterleitung darf die Seite nicht blockieren
  }
})();
