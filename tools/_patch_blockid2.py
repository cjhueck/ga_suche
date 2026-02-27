import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

apath = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
with open(apath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Zeilen 31018-31065 (0-indexed: 31017-31064) ersetzen
start = 31017  # 0-indexed
end = 31065    # 0-indexed (exclusive)

new_block = '''      // GA-Links nach Zitat-Absätzen einfügen: öffnen Vortrag im rechten Panel
      var apiBase = typeof API_BASE !== 'undefined' ? API_BASE : (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:3003' : '');
      resultsDiv.querySelectorAll('#maps-obsidian-content p').forEach(function(p) {
        var bidSpan = p.querySelector('.blkref[data-bid]');
        var blockId = bidSpan ? bidSpan.dataset.bid : null;
        var gotoLink = p.querySelector('a[href*="goto.html"]');
        var bareCiteM = p.textContent.match(/\\[GA\\s+(\\d+),\\s*S\\.\\s*[\\d\\u2013\\-]+;\\s*(\\d{2})\\.(\\d{2})\\.(\\d{4})\\]/);
        if (!blockId && !gotoLink && !bareCiteM) return;
        var capturedBlockId = blockId;
        function addLink(lectureId, gaLabel) {
          var link = document.createElement('a');
          link.href = '#';
          link.className = 'ga-keyword-link';
          link.title = 'Abschnitt im rechten Panel öffnen';
          link.textContent = gaLabel;
          link.style.marginLeft = '0.4em';
          link.addEventListener('click', function(e) {
            e.preventDefault();
            if (typeof window.showLectureFromAdvancedSearch === 'function') {
              window.showLectureFromAdvancedSearch(lectureId, '', capturedBlockId ? '^' + capturedBlockId : '');
            }
          });
          p.appendChild(link);
        }
        if (blockId) {
          fetch(apiBase + '/api/resolve-block-id?id=' + encodeURIComponent(blockId))
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
              if (data && data.success && data.lectureId) {
                addLink(data.lectureId, 'GA\u00a0' + (data.gaNumber || '').replace(/^GA/i, ''));
              }
            })
            .catch(function() {});
        } else {
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
          var capturedGa = ga;
          fetch(apiBase + '/api/resolve-lecture?ga=' + encodeURIComponent(ga) + '&date=' + encodeURIComponent(isoDate))
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
              if (data && data.success && data.lectureId) {
                addLink(data.lectureId, 'GA\u00a0' + capturedGa);
              }
            })
            .catch(function() {});
        }
      });
'''

# Prüfe ob der Bereich korrekt ist
print(f'Ersetze Zeilen {start+1}-{end}:')
print(f'  Erste: {repr(lines[start].rstrip()[:60])}')
print(f'  Letzte: {repr(lines[end-1].rstrip()[:60])}')

lines[start:end] = [new_block]

with open(apath, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('OK: Frontend aktualisiert')
