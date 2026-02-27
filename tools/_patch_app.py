with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'r', encoding='utf-8') as f:
    src = f.read()

# ── Änderung 1: Block-IDs als unsichtbare Spans einbetten statt löschen ─────────
old1 = "      // Block-IDs (^pfr5w5) aus Anzeige entfernen \u2013 sie bleiben in den Daten, nicht im Panel\n      md = md.replace(/ \\^[a-z0-9]+(?=[ \\[;])/g, '');"

new1 = "      // Block-IDs als unsichtbare Spans einbetten (für Navigation, nicht sichtbar)\n      md = md.replace(/ \\^([a-z0-9]+)(?=[ \\[;])/g, ' <span class=\"blkref\" data-bid=\"$1\"></span>');"

if old1 not in src:
    print('FEHLER: Block 1 nicht gefunden')
    exit(1)
src = src.replace(old1, new1, 1)
print('Schritt 1 OK: Block-IDs zu Spans umgewandelt')

# ── Änderung 2: h4-Click-Handler ersetzen ────────────────────────────────────────
old2 = """      // Zitat-Überschriften (h4/h5/h6) klickbar: öffnet GA-Vortrag mit Absatz-Hervorhebung
      resultsDiv.querySelectorAll('#maps-obsidian-content h4, #maps-obsidian-content h5, #maps-obsidian-content h6').forEach(function(heading) {
        var next = heading.nextElementSibling;
        while (next && next.tagName !== 'P' && next.tagName !== 'BLOCKQUOTE') next = next.nextElementSibling;
        if (!next) return;
        var gotoLink = next.querySelector('a[href*="goto.html"]');
        var bareCiteM = next.textContent.match(/\\[GA\\s+(\\d+),\\s*S\\.\\s*[\\d\\u2013\\-]+;\\s*(\\d{2})\\.(\\d{2})\\.(\\d{4})\\]/);
        if (!gotoLink && !bareCiteM) return;
        heading.style.cursor = 'pointer';
        heading.title = 'Vortrag mit diesem Abschnitt öffnen';
        heading.addEventListener('click', function(e) {
          e.stopPropagation();
          if (typeof navigateToGAPage !== 'function') return;
          if (gotoLink) {
            var href = gotoLink.getAttribute('href');
            var hi = href.indexOf('#');
            if (hi < 0) return;
            var params = {};
            href.substring(hi + 1).split('&').forEach(function(kv) {
              var eq = kv.indexOf('=');
              if (eq > 0) params[kv.slice(0, eq)] = decodeURIComponent(kv.slice(eq + 1)).replace(/\\+/g, ' ');
            });
            if (params.ga && params.date) navigateToGAPage(params.ga, params.date, params.page || '', params.text || '');
          } else if (bareCiteM) {
            var ga = bareCiteM[1];
            var date = bareCiteM[4] + '-' + bareCiteM[3] + '-' + bareCiteM[2];
            var paraText = next.textContent.replace(/\\[GA[^\\]]+\\]/g, '').replace(/\\^[a-z0-9]+/g, '').trim().slice(0, 120);
            navigateToGAPage(ga, date, '', paraText);
          }
        });
      });"""

new2 = """      // Zitat-Überschriften (h4/h5/h6) klickbar: öffnet Vortrag im rechten Side-Panel
      resultsDiv.querySelectorAll('#maps-obsidian-content h4, #maps-obsidian-content h5, #maps-obsidian-content h6').forEach(function(heading) {
        var next = heading.nextElementSibling;
        while (next && next.tagName !== 'P' && next.tagName !== 'BLOCKQUOTE') next = next.nextElementSibling;
        if (!next) return;
        var gotoLink = next.querySelector('a[href*="goto.html"]');
        var bareCiteM = next.textContent.match(/\\[GA\\s+(\\d+),\\s*S\\.\\s*[\\d\\u2013\\-]+;\\s*(\\d{2})\\.(\\d{2})\\.(\\d{4})\\]/);
        if (!gotoLink && !bareCiteM) return;
        heading.style.cursor = 'pointer';
        heading.title = 'Abschnitt im rechten Panel öffnen';
        heading.addEventListener('click', function(e) {
          e.stopPropagation();
          // Block-ID aus unsichtbarem Span holen
          var bidSpan = next.querySelector('.blkref[data-bid]');
          var blockId = bidSpan ? bidSpan.dataset.bid : null;
          // GA-Nummer und Datum aus Citation ermitteln
          var ga = null, isoDate = null;
          if (gotoLink) {
            var href = gotoLink.getAttribute('href');
            var hi = href.indexOf('#');
            if (hi >= 0) {
              var params = {};
              href.substring(hi + 1).split('&').forEach(function(kv) {
                var eq = kv.indexOf('=');
                if (eq > 0) params[kv.slice(0, eq)] = decodeURIComponent(kv.slice(eq + 1)).replace(/\\+/g, ' ');
              });
              ga = params.ga; isoDate = params.date;
            }
          }
          if ((!ga || !isoDate) && bareCiteM) {
            ga = bareCiteM[1];
            isoDate = bareCiteM[4] + '-' + bareCiteM[3] + '-' + bareCiteM[2];
          }
          if (!ga || !isoDate) return;
          // Lecture-ID per API ermitteln, dann im rechten Panel mit Absatz-Highlight anzeigen
          var apiBase = typeof API_BASE !== 'undefined' ? API_BASE : 'http://localhost:3003';
          fetch(apiBase + '/api/resolve-lecture?ga=' + encodeURIComponent(ga) + '&date=' + encodeURIComponent(isoDate))
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
              if (!data || !data.success || !data.lectureId) return;
              if (typeof showLectureFromAdvancedSearch === 'function') {
                showLectureFromAdvancedSearch(data.lectureId, '', blockId ? '^' + blockId : '');
              }
            })
            .catch(function(err) { console.warn('[KARTEN] Navigation fehlgeschlagen:', err); });
        });
      });"""

if old2 not in src:
    print('FEHLER: Block 2 nicht gefunden')
    exit(1)
src = src.replace(old2, new2, 1)
print('Schritt 2 OK: h4-Handler auf showLectureFromAdvancedSearch umgestellt')

with open(r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js', 'w', encoding='utf-8') as f:
    f.write(src)
print('Gespeichert.')
