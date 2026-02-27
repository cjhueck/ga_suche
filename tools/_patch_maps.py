import io, sys, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
backup = path + '.bak_maps'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# =========================================================
# PATCH 1: window.showLectureFromAdvancedSearch nach Ende der Funktion (nach Zeile 12608)
# =========================================================
old1 = '    }\n    \n    // Funktion: Zeigt ein Buch im rechten Panel'
new1 = '    }\n    window.showLectureFromAdvancedSearch = showLectureFromAdvancedSearch;\n    \n    // Funktion: Zeigt ein Buch im rechten Panel'

if old1 in content:
    content = content.replace(old1, new1, 1)
    print('PATCH 1 OK: window.showLectureFromAdvancedSearch gesetzt')
else:
    print('FEHLER PATCH 1: Nicht gefunden!')

# =========================================================
# PATCH 2: Heading-Click durch Paragraph-Link ersetzen
# =========================================================
old2 = '''      // Zitat-Überschriften (h4/h5/h6) klickbar: öffnet Vortrag im rechten Side-Panel
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
      });'''

new2 = '''      // GA-Links nach Zitat-Absätzen einfügen: öffnen Vortrag im rechten Panel
      resultsDiv.querySelectorAll('#maps-obsidian-content p').forEach(function(p) {
        var gotoLink = p.querySelector('a[href*="goto.html"]');
        var bareCiteM = p.textContent.match(/\\[GA\\s+(\\d+),\\s*S\\.\\s*[\\d\\u2013\\-]+;\\s*(\\d{2})\\.(\\d{2})\\.(\\d{4})\\]/);
        if (!gotoLink && !bareCiteM) return;
        var bidSpan = p.querySelector('.blkref[data-bid]');
        var blockId = bidSpan ? bidSpan.dataset.bid : null;
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
        var apiBase = typeof API_BASE !== 'undefined' ? API_BASE : (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:3003' : '');
        var capturedGa = ga, capturedDate = isoDate, capturedBlockId = blockId;
        fetch(apiBase + '/api/resolve-lecture?ga=' + encodeURIComponent(capturedGa) + '&date=' + encodeURIComponent(capturedDate))
          .then(function(r) { return r.ok ? r.json() : null; })
          .then(function(data) {
            if (!data || !data.success || !data.lectureId) return;
            var lid = data.lectureId;
            var link = document.createElement('a');
            link.href = '#';
            link.className = 'ga-keyword-link';
            link.title = 'Abschnitt im rechten Panel öffnen';
            link.textContent = 'GA\u00a0' + capturedGa;
            link.style.marginLeft = '0.4em';
            link.addEventListener('click', function(e) {
              e.preventDefault();
              if (typeof window.showLectureFromAdvancedSearch === 'function') {
                window.showLectureFromAdvancedSearch(lid, '', capturedBlockId ? '^' + capturedBlockId : '');
              }
            });
            p.appendChild(link);
          })
          .catch(function() {});
      });'''

if old2 in content:
    content = content.replace(old2, new2, 1)
    print('PATCH 2 OK: Paragraph-Links eingefügt')
else:
    # Zeige was tatsächlich im Bereich ist
    idx = content.find('Zitat-Überschriften (h4/h5/h6)')
    if idx >= 0:
        print('FEHLER PATCH 2: Kontext gefunden aber exakter Match nicht:')
        print(repr(content[idx:idx+200]))
    else:
        print('FEHLER PATCH 2: Kontext nicht gefunden')

# Backup + Speichern
shutil.copy2(path, backup)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Gespeichert.')
