import io, sys, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# === PATCH 1: Backend - neuer /api/resolve-block-id Endpoint ===
bpath = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\backend.js'
with open(bpath, 'r', encoding='utf-8') as f:
    bcontent = f.read()

new_endpoint = '''
// Block-ID -> Lecture-ID Lookup
app.get('/api/resolve-block-id', (req, res) => {
  try {
    const { id } = req.query;
    if (!id) return res.status(400).json({ error: 'Parameter id erforderlich' });
    const searchId = id.startsWith('^') ? id : '^' + id;
    for (const [lectureId, lecture] of Object.entries(fullLectures)) {
      if (!lecture.paragraphs) continue;
      const found = lecture.paragraphs.find(p => p.index === searchId);
      if (found) {
        return res.json({ success: true, lectureId, title: lecture.title || '', date: lecture.date || '', gaNumber: lecture.gaNumber || '' });
      }
    }
    res.status(404).json({ error: `Kein Vortrag gefunden fuer Block-ID ${id}` });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

'''

# Einfügen nach /api/resolve-lecture Endpoint
insert_after = 'res.status(404).json({ error: `Kein Vortrag gefunden für GA ${ga}, Datum ${date}` });\n  } catch (error) {\n    console.error(\'[RESOLVE-LECTURE] Fehler:\', error);\n    res.status(500).json({ error: error.message });\n  }\n});'

if insert_after in bcontent:
    shutil.copy2(bpath, bpath + '.bak_blockid')
    bcontent = bcontent.replace(insert_after, insert_after + new_endpoint, 1)
    with open(bpath, 'w', encoding='utf-8') as f:
        f.write(bcontent)
    print('PATCH 1 OK: /api/resolve-block-id hinzugefügt')
else:
    print('FEHLER PATCH 1: Einfügepunkt nicht gefunden')

# === PATCH 2: Frontend - Block-ID Lookup zuerst, dann GA+Date als Fallback ===
apath = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.js'
with open(apath, 'r', encoding='utf-8') as f:
    acontent = f.read()

old2 = '''      // GA-Links nach Zitat-Absätzen einfügen: öffnen Vortrag im rechten Panel
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
            link.textContent = 'GA\\u00a0' + capturedGa;
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

new2 = '''      // GA-Links nach Zitat-Absätzen einfügen: öffnen Vortrag im rechten Panel
      var apiBase = typeof API_BASE !== 'undefined' ? API_BASE : (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:3003' : '');
      resultsDiv.querySelectorAll('#maps-obsidian-content p').forEach(function(p) {
        var bidSpan = p.querySelector('.blkref[data-bid]');
        var blockId = bidSpan ? bidSpan.dataset.bid : null;
        // Fallback: GA+Datum aus Zitationslink
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
          // Direkter Lookup per Block-ID
          fetch(apiBase + '/api/resolve-block-id?id=' + encodeURIComponent(blockId))
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
              if (data && data.success && data.lectureId) {
                addLink(data.lectureId, 'GA\\u00a0' + (data.gaNumber || '').replace(/^GA/i,''));
              }
            })
            .catch(function() {});
        } else {
          // Fallback: GA+Datum
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
                addLink(data.lectureId, 'GA\\u00a0' + capturedGa);
              }
            })
            .catch(function() {});
        }
      });'''

if old2 in acontent:
    acontent = acontent.replace(old2, new2, 1)
    with open(apath, 'w', encoding='utf-8') as f:
        f.write(acontent)
    print('PATCH 2 OK: Frontend Block-ID Lookup')
else:
    print('FEHLER PATCH 2: Block nicht gefunden')

# Version in app.html updaten
hpath = r'C:\Users\chuec\OneDrive\GitHub\ga_suche\app.html'
with open(hpath, 'r', encoding='utf-8') as f:
    hcontent = f.read()
import re
hcontent_new = re.sub(r'<script src="app\.js\?[^"]*">', '<script src="app.js?v=20260227c">', hcontent)
if hcontent_new != hcontent:
    with open(hpath, 'w', encoding='utf-8') as f:
        f.write(hcontent_new)
    print('PATCH 3 OK: app.html Version aktualisiert')
