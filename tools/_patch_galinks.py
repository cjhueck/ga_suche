import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

apath = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
with open(apath, 'r', encoding='utf-8') as f:
    content = f.read()

# Ersetze den bestehenden GA-Links-Block
old = '''      // GA-Links nach Zitat-Absätzen einfügen: öffnen Vortrag im rechten Panel
      var apiBase = typeof API_BASE !== 'undefined' ? API_BASE : (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:3003' : '');
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
            link.textContent = 'GA\xa0' + capturedGa;
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

new = '''      // Block-IDs in klickbare GA-Links umwandeln (GA307/5:pfr5w5)
      var apiBase = typeof API_BASE !== 'undefined' ? API_BASE : (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:3003' : '');
      resultsDiv.querySelectorAll('#maps-obsidian-content .blkref[data-bid]').forEach(function(span) {
        var blockId = span.dataset.bid;
        if (!blockId) return;
        fetch(apiBase + '/api/resolve-block-id?id=' + encodeURIComponent(blockId))
          .then(function(r) { return r.ok ? r.json() : null; })
          .then(function(data) {
            if (!data || !data.success || !data.lectureId) return;
            var lectureId = data.lectureId;
            var a = document.createElement('a');
            a.href = '#';
            a.textContent = lectureId + ':' + blockId;
            a.title = 'Abschnitt im rechten Panel öffnen';
            a.addEventListener('click', function(e) {
              e.preventDefault();
              if (typeof window.showLectureFromAdvancedSearch === 'function') {
                window.showLectureFromAdvancedSearch(lectureId, '', '^' + blockId);
              }
            });
            span.parentNode.replaceChild(a, span);
          })
          .catch(function() {});
      });'''

if old in content:
    content = content.replace(old, new, 1)
    with open(apath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK: Block-IDs zu GA-Links konvertiert')
else:
    print('FEHLER: Block nicht gefunden')
    if 'GA-Links nach Zitat' in content:
        print('(GA-Links-Kommentar existiert, evtl. anderer Text)')
