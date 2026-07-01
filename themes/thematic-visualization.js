/**
 * Thematic Visualization II for Rudolf Steiner's Work
 * Visualizes theme intensity between 1879 and 1925
 */

console.log('[THEME2] Script loaded');

// Hilfsfunktion: Splittet Query-String, ersetzt Unterstriche durch Leerzeichen
// z.B. 'Schlaf Tod Nachtodliches_Leben' → ['Schlaf', 'Tod', 'Nachtodliches Leben']
function splitKeywords(queryString) {
    var words = queryString.split(/\s+/).filter(function(k) { return k.length > 0; });
    return words.map(function(word) {
        // Ersetze Unterstriche durch Leerzeichen für mehrteilige Begriffe
        return word.replace(/_/g, ' ');
    });
}

// SteinerThemesData wird jetzt aus themes/themes-data.js geladen


// Dynamische Theme-Daten mit berechneten Zeiträumen
var dynamicThemesData = null;
var themeRangesCache = null;

// Cache für KI-Zuordnungen (welche Themen haben Einträge)
var aiAssignmentsStatus = null;

async function loadThemeRangesAndRender(container) {
    console.log('[THEME2] Lade KI-Zuordnungen Status...');
    
    // Lade KI-Zuordnungen Status
    try {
        var aiResponse = await fetch('/api/theme-assignments-status');
        if (aiResponse.ok) {
            aiAssignmentsStatus = await aiResponse.json();
            console.log('[THEME2] KI-Zuordnungen Status geladen:', aiAssignmentsStatus.totalAssignments, 'Texte zugeordnet');
        }
    } catch (e) {
        console.log('[THEME2] Keine KI-Zuordnungen verfügbar:', e.message);
        aiAssignmentsStatus = { themeCounts: {} };
    }
    
    // Filtere Themen: Nur Themen mit KI-Zuordnungen anzeigen
    var themesWithAssignments = SteinerThemesData.filter(function(theme) {
        var count = aiAssignmentsStatus.themeCounts[theme.theme] || 0;
        return count > 0;
    });
    
    console.log('[THEME2] Themen mit KI-Zuordnungen:', themesWithAssignments.length, 'von', SteinerThemesData.length);
    
    if (themesWithAssignments.length === 0) {
        container.innerHTML = [
            '<div style="padding: 3rem; text-align: center;">',
            '  <h3 style="color: var(--heading-color);">Keine KI-Zuordnungen vorhanden</h3>',
            '  <p style="color: var(--secondary-text);">Bitte erst Texte zuordnen mit /api/assign-themes-batch</p>',
            '</div>'
        ].join('');
        return;
    }
    
    // Erstelle dynamische Theme-Daten basierend auf KI-Zuordnungen mit echten Jahren
    dynamicThemesData = themesWithAssignments.map(function(theme) {
        var count = aiAssignmentsStatus.themeCounts[theme.theme] || 0;
        var rangeData = aiAssignmentsStatus.themeRanges[theme.theme];
        
        // Verwende echte Ranges aus den KI-Zuordnungen
        var ranges = [];
        if (rangeData && rangeData.ranges && rangeData.ranges.length > 0) {
            ranges = rangeData.ranges;
        } else {
            // Fallback falls keine Jahresdaten
            ranges = [{ start: 1900, end: 1910, intensity: 0.5 }];
        }
        
        return {
            theme: theme.theme,
            ranges: ranges,
            query: theme.query,
            totalMatches: count
        };
    });
    
    // Jetzt rendern (nur Themen mit KI-Zuordnungen)
    renderThematicChart(container);
}

function updateSpinner(container, message) {
    var spinner = container.querySelector('#thematic2-loading-spinner');
    if (spinner) {
        spinner.innerHTML = [
            '<div style="margin-bottom: 1.5rem; font-size: 3rem;">⏳</div>',
            '<em style="font-size: 1.3rem;">' + message + '</em>'
        ].join('');
    }
}

function initThematicVisualization() {
    console.log('[THEME2] initThematicVisualization starting');
    console.log('[THEME2] D3 available:', typeof d3 !== 'undefined');
    console.log('[THEME2] SteinerThemesData available:', typeof SteinerThemesData !== 'undefined', SteinerThemesData ? SteinerThemesData.length : 0);
    
    var viewer = document.getElementById('viewer');
    if (!viewer) {
        console.warn('[THEME2] Viewer element not found');
        return;
    }
    console.log('[THEME2] Viewer found:', viewer.id);
    
    // Prepare viewer content
    viewer.innerHTML = [
        '<div id="thematic2-viewer-container" style="padding: 1rem 2rem; min-height: 100%; overflow-y: auto; background: var(--background-color, #FAF8F3); box-sizing: border-box;">',
        '  <div id="thematic2-visualization-main" style="min-height: 650px; background: transparent; padding: 0; border: none; overflow-x: auto; box-sizing: border-box;">',
        '    <div id="thematic2-loading-spinner" style="padding: 5rem; text-align: center; color: var(--secondary-text, #666);">',
        '      <div style="margin-bottom: 1.5rem; font-size: 3rem;">⏳</div>',
        '      <em style="font-size: 1.3rem;">Zeiträume werden geladen...</em>',
        '    </div>',
        '  </div>',
        '</div>'
    ].join('');

    // Start checking for D3 and container ready
    var checkInterval = setInterval(function() {
        var container = document.getElementById('thematic2-visualization-main');
        if (container && typeof d3 !== 'undefined') {
            clearInterval(checkInterval);
            // Lade Cache und rendere dann
            loadThemeRangesAndRender(container);
        }
    }, 100);
    
    // Stop checking after 10 seconds
    setTimeout(function() { clearInterval(checkInterval); }, 10000);
}

function renderThematicChart(container) {
    try {
        // Verwende dynamische Daten wenn verfügbar, sonst statische
        var themesData = dynamicThemesData || SteinerThemesData;
        
        // Sortiere Themen alphabetisch für konsistente Anzeige
        themesData = themesData.slice().sort(function(a, b) {
            return a.theme.localeCompare(b.theme, 'de');
        });
        
        console.log('[THEME2] Rendering chart...');
        console.log('[THEME2] Container:', container ? container.id : 'null');
        console.log('[THEME2] Themes count:', themesData.length);
        console.log('[THEME2] Using dynamic data:', !!dynamicThemesData);
        
        // Ensure spinner is gone
        container.innerHTML = '';
        
        // Legende erstellen - dynamisch basierend auf globalem Maximum
        var globalMax = aiAssignmentsStatus ? (aiAssignmentsStatus.globalMaxCount || 10) : 10;
        var legendDiv = document.createElement('div');
        legendDiv.style.cssText = 'margin-bottom: 1rem; padding: 0.8rem 1rem; background: transparent; border-radius: 6px; display: flex; align-items: center; gap: 1.5rem; flex-wrap: wrap;';
        
        // Dynamische Schwellwerte basierend auf globalMax (logarithmische Skala)
        // Bei log-Skala: intensity = log(count+1) / log(globalMax+1)
        var logMax = Math.log(globalMax + 1);
        function countToOpacity(count) {
            return Math.max(0.25, Math.log(count + 1) / logMax * 0.85);
        }
        
        // Erstelle Legende mit relevanten Stufen (keine Duplikate)
        var legendSteps = [1];
        if (globalMax >= 3) legendSteps.push(3);
        if (globalMax >= 10) legendSteps.push(10);
        if (globalMax >= 20) legendSteps.push(20);
        if (globalMax > 20) legendSteps.push(globalMax);
        
        var legendHtml = '<span style="font-weight: 600; color: var(--text-color, #333); font-size: 0.9rem;">Texte pro Jahr:</span>';
        legendSteps.forEach(function(count) {
            legendHtml += '<div style="display: flex; align-items: center; gap: 0.5rem;">' +
                '<div style="width: 20px; height: 14px; background: rgba(70,120,134,' + countToOpacity(count) + '); border-radius: 2px;"></div>' +
                '<span style="font-size: 0.85rem; color: var(--secondary-text, #666);">' + count + '</span>' +
                '</div>';
        });
        
        legendDiv.innerHTML = legendHtml;
        container.appendChild(legendDiv);
        
        var margin = { top: 35, right: 60, bottom: 60, left: 235 };
        var containerWidth = container.getBoundingClientRect().width || 1000;
        
        var width = Math.max(800, containerWidth - margin.left - margin.right);
        var height = themesData.length * 32 + margin.top + margin.bottom;

        var svg = d3.select(container)
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height)
            .style('display', 'block')
            .style('overflow', 'visible')
            .append('g')
            .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');
            
        var x = d3.scaleLinear()
            .domain([1879, 1925])
            .range([0, width]);

        var y = d3.scaleBand()
            .domain(themesData.map(function(d) { return d.theme; }))
            .range([0, height - margin.top - margin.bottom])
            .padding(0.3);

        // X Axis (unten)
        var xAxis = svg.append('g')
            .attr('transform', 'translate(0,' + (height - margin.top - margin.bottom) + ')')
            .call(d3.axisBottom(x).ticks(15).tickFormat(d3.format('d')));
            
        // Textfarbe basierend auf Dark Mode
        var textColor = document.body.classList.contains('dark-mode') ? '#b8b8b8' : '#333';
        
        xAxis.selectAll('text')
            .style('font-size', '13px')
            .style('fill', textColor);
            
        // X Axis (oben)
        var xAxisTop = svg.append('g')
            .attr('transform', 'translate(0,0)')
            .call(d3.axisTop(x).ticks(15).tickFormat(d3.format('d')));
            
        xAxisTop.selectAll('text')
            .style('font-size', '13px')
            .style('fill', textColor);

        // Y Axis
        var yAxis = svg.append('g')
            .call(d3.axisLeft(y));
            
        yAxis.selectAll('text')
            .style('font-size', '14px')
            .style('font-weight', '700')
            .style('fill', '#467886')
            .style('cursor', 'pointer')
            .style('text-decoration', 'none')
            .on('click', function(event) {
                var themeName = d3.select(this).text();
                if (typeof loadThemeSummary === 'function') {
                    loadThemeSummary(themeName);
                }
            })
            .on('mouseover', function() {
                d3.select(this).style('opacity', '0.7');
            })
            .on('mouseout', function() {
                d3.select(this).style('opacity', '1');
            });

        // Grid lines
        svg.append('g')
            .attr('class', 'grid')
            .attr('transform', 'translate(0,' + (height - margin.top - margin.bottom) + ')')
            .call(d3.axisBottom(x)
                .ticks(15)
                .tickSize(-(height - margin.top - margin.bottom))
                .tickFormat('')
            )
            .style('stroke', '#ccc')
            .style('stroke-dasharray', '3,3')
            .style('stroke-opacity', 0.4);
        
        // Heatmap-Rechtecke für jedes Jahr mit Daten
        var themeGroups = svg.selectAll('.theme-group')
            .data(themesData)
            .enter()
            .append('g')
            .attr('class', 'theme-group')
            .attr('transform', function(d) { return 'translate(0, ' + y(d.theme) + ')'; });

        themeGroups.each(function(d, themeIndex) {
            var group = d3.select(this);
            
            // Erstelle Intensitäts-Map für jedes Jahr (nur Jahre mit Daten)
            var yearIntensity = {};
            d.ranges.forEach(function(r) {
                // Jeder Range hat start === end (einzelnes Jahr)
                yearIntensity[r.start] = Math.max(yearIntensity[r.start] || 0, r.intensity);
            });
            
            // Zeichne ein separates Rechteck für jedes Jahr mit Daten
            var years = Object.keys(yearIntensity).map(Number).sort(function(a, b) { return a - b; });
            
            years.forEach(function(year) {
                var intensity = yearIntensity[year];
                if (intensity <= 0) return; // Keine Anzeige bei Intensität 0
                
                var alpha = Math.max(0.25, intensity * 0.85);
                var rectX = x(year);
                var rectWidth = x(year + 1) - x(year);
                
                group.append('rect')
                    .attr('x', rectX)
                    .attr('y', 0)
                    .attr('width', rectWidth)
                    .attr('height', y.bandwidth())
                    .attr('fill', '#467886')
                    .attr('fill-opacity', alpha)
                    .attr('rx', 2)
                    .style('cursor', 'pointer')
                    .on('click', function(event) {
                        selectThemeInDropdown(d.theme);
                        var currentQuery = d.query;
                        if (themeKeywordSettings[d.theme] && themeKeywordSettings[d.theme].activeKeywords.length > 0) {
                            currentQuery = themeKeywordSettings[d.theme].activeKeywords.join(' ');
                        }
                        openThematicLectureList(d.theme, years[0], years[years.length - 1], currentQuery, year);
                    });
            });
        });

        console.log('[THEME2] Chart rendered successfully');
    } catch (error) {
        console.error('[THEME2] Render error:', error);
        container.innerHTML = '<div style="padding: 2rem; text-align: center; color: #dc2626;">Fehler beim Zeichnen der Grafik: ' + error.message + '</div>';
    }
}

// Rendere die Ergebnisliste (für semantische und keyword-basierte Suche)
function renderThematic2Results(container, theme, results, isSemantic, isCached, source, scrollToYear) {
    if (results.length === 0) {
        container.innerHTML = [
            '<div style="padding: 2rem; text-align: center; color: var(--secondary-text);">',
            '  Keine Inhalte zum Thema <strong>' + theme + '</strong> gefunden.',
            '</div>'
        ].join('');
        return;
    }
    
    // Hilfsfunktion: Extrahiere sortierbares Datum (YYYY-MM-DD) aus verschiedenen Quellen
    function extractSortDate(item) {
        // 1. Vollständiges Datum im Format YYYY-MM-DD
        if (item.date && item.date.match(/^\d{4}-\d{2}-\d{2}/)) {
            return item.date.substring(0, 10);
        }
        // 2. Jahr + Dummy-Datum für korrekte Sortierung
        var year = null;
        // Aus year-Feld
        if (item.year) year = String(item.year);
        // Aus fileName extrahieren (z.B. "(1900)" am Ende)
        if (!year && item.fileName) {
            var match = String(item.fileName).match(/\((\d{4})\)\s*$/);
            if (match) year = match[1];
        }
        // Aus title extrahieren
        if (!year && item.title) {
            var match = String(item.title).match(/\((\d{4})\)/);
            if (match) year = match[1];
        }
        // Aus lectureTitle extrahieren
        if (!year && item.lectureTitle) {
            var match = String(item.lectureTitle).match(/\((\d{4})\)/);
            if (match) year = match[1];
        }
        // Aus date-Feld (nur Jahr)
        if (!year && item.date) {
            var match = String(item.date).match(/(\d{4})/);
            if (match) year = match[1];
        }
        if (year) return year + '-06-15'; // Mitte des Jahres als Fallback
        return '9999-12-31'; // Ganz ans Ende
    }
    
    // Hilfsfunktion: Extrahiere Jahr für die Navigation
    function extractYear(item) {
        var sortDate = extractSortDate(item);
        return sortDate.substring(0, 4);
    }
    
    // Sortiere chronologisch nach vollständigem Datum
    results.sort(function(a, b) {
        var dateA = extractSortDate(a);
        var dateB = extractSortDate(b);
        return dateA.localeCompare(dateB);
    });

    // Quelle nicht mehr anzeigen
    var sourceLabel = '';

    // Finde die Jahre in den Ergebnissen (als Zahlen)
    var yearsInResults = {};
    results.forEach(function(res) {
        var year = extractYear(res);
        if (year && year !== '9999') yearsInResults[parseInt(year)] = true;
    });
    
    // Wenn scrollToYear nicht in den Ergebnissen ist, finde das nächste verfügbare Jahr
    var scrollYearNum = scrollToYear ? parseInt(scrollToYear) : null;
    var targetYear = scrollYearNum;
    
    if (scrollYearNum && !yearsInResults[scrollYearNum]) {
        var availableYears = Object.keys(yearsInResults).map(Number).sort(function(a, b) { return a - b; });
        // Finde das nächste Jahr >= scrollToYear, oder das letzte davor
        targetYear = availableYears.find(function(y) { return y >= scrollYearNum; }) || availableYears[availableYears.length - 1];
    }

    var html = [
        '<div class="ga-lectures-container" style="padding: 1.5rem; background: var(--background-color);">',
        '  <h3 style="margin-top: 0; color: var(--heading-color); border-bottom: 2px solid var(--accent-color); padding-bottom: 0.8rem; font-size: 1.2rem;">',
        '    ' + theme + sourceLabel,
        '  </h3>',
        '  <p style="font-size: 0.85rem; color: var(--secondary-text); margin: 0.8rem 0 1.2rem 0;">',
        '    ' + results.length + ' Texte chronologisch',
        '  </p>',
        '  <div class="thematic-lecture-list">'
    ].join('');

    var firstEntryForYear = {};
    
    results.forEach(function(res) {
        var displayId = res.id;
        if (typeof formatLectureId === 'function') displayId = formatLectureId(res.id);
        
        // Prüfe, ob das Jahr bereits im Titel oder Location vorkommt
        var yearStr = res.year ? String(res.year) : '';
        var yearInTitle = yearStr && res.title && res.title.indexOf(yearStr) !== -1;
        var yearInLocation = yearStr && res.location && res.location.indexOf(yearStr) !== -1;
        var yearAlreadyShown = yearInTitle || yearInLocation;
        
        // Datum: Echtes Datum anzeigen (wenn vorhanden), Jahr nur wenn nicht schon angezeigt
        var dateStr = '';
        if (res.date && res.date.length >= 10 && res.date !== (res.year + '-01-01')) {
            // Echtes Datum formatieren (z.B. "1905-10-04" -> "4.10.1905")
            dateStr = new Date(res.date).toLocaleDateString('de-DE');
        } else if (res.year && !yearAlreadyShown) {
            // Nur Jahr anzeigen, wenn nicht schon im Titel oder Location
            dateStr = '(' + res.year + ')';
        }
        
        var shortSummary = res.shortSummary || res.summary || '';

        // Format: GA101/1 - Titel, Ort, Datum oder (Jahr)
        var linkText = displayId;
        if (res.title) linkText += ' - ' + res.title;
        if (res.location) linkText += ', ' + res.location;
        if (dateStr) linkText += ' ' + dateStr;

        // ID für Scroll-Ziel setzen (erster Eintrag pro Jahr)
        var yearId = '';
        var resYear = parseInt(res.year);
        
        if (resYear && !firstEntryForYear[resYear]) {
            firstEntryForYear[resYear] = true;
            yearId = 'id="theme-year-' + resYear + '"';
        }

        html += [
            '<div ' + yearId + ' style="margin-bottom: 1rem;">',
            '  <div style="margin-bottom: 0.3rem;">',
            '    <a href="#" ',
            '       class="ga-lecture-link"',
            '       onclick="if(typeof navigateToLectureInTexteTab === \'function\') { navigateToLectureInTexteTab(\'' + res.id + '\'); } else { switchTab(\'texte\'); if(typeof showLecture === \'function\') showLecture(\'' + res.id + '\'); } return false;" ',
            '       style="font-weight: bold; font-size: 0.85rem; text-decoration: none;"',
            '       onmouseover="this.style.textDecoration=\'underline\'" ',
            '       onmouseout="this.style.textDecoration=\'none\'">',
            '      ' + linkText,
            '    </a>',
            '  </div>',
            (shortSummary ? 
                '  <div class="ga-lecture-text" style="line-height: 1.4; font-size: 0.85rem; text-align: left; font-style: italic;">' + shortSummary + '</div>' : 
                '  <div class="ga-missing-text" style="font-style: italic; font-size: 0.85rem;">Keine Kurzzusammenfassung verfügbar</div>'
            ),
            '</div>'
        ].join('');
    });

    html += '  </div>\n</div>';
    container.innerHTML = html;
    
    // Scrolle zum angeklickten Jahr nach dem Rendern
    if (targetYear) {
        setTimeout(function() {
            var targetElement = document.getElementById('theme-year-' + parseInt(targetYear));
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 100);
    }
}

// KI-Zusammenfassung eines Themas im linken Panel anzeigen (in #results, unterhalb des Resize Handles)
async function loadThemeSummary(themeName, forceRegenerate) {
    console.log('[THEME-SUMMARY] Lade Zusammenfassung für:', themeName, forceRegenerate ? '(force)' : '');

    var resultsDiv = document.getElementById('results');
    if (!resultsDiv) {
        console.error('[THEME-SUMMARY] #results nicht gefunden');
        return;
    }

    // Ladeanzeige
    resultsDiv.innerHTML = [
        '<div style="padding: 0.8rem 0.5rem;">',
        '  <h4 style="margin: 0 0 0.8rem 0; color: var(--heading-color); font-size: 1rem;">',
        '    ' + themeName,
        '  </h4>',
        '  <div style="display: flex; align-items: center; gap: 8px; color: var(--secondary-text); font-size: 0.85rem;">',
        '    <span class="loading-spinner" style="display: inline-block; width: 16px; height: 16px; border: 2px solid var(--border-color); border-top-color: var(--accent-color); border-radius: 50%; animation: spin 0.8s linear infinite;"></span>',
        '    KI-Zusammenfassung wird ' + (forceRegenerate ? 'neu ' : '') + 'erstellt...',
        '  </div>',
        '  <style>@keyframes spin { to { transform: rotate(360deg); } }</style>',
        '</div>'
    ].join('');

    try {
        var requestBody = { themeName: themeName };
        if (forceRegenerate) requestBody.forceRegenerate = true;

        var response = await fetch('/api/theme-summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            var errData = await response.json().catch(function() { return {}; });
            throw new Error(errData.error || 'Server-Fehler ' + response.status);
        }

        var data = await response.json();

        if (!data.summary) {
            resultsDiv.innerHTML = [
                '<div style="padding: 0.8rem 0.5rem;">',
                '  <h4 style="margin: 0 0 0.5rem 0; color: var(--heading-color); font-size: 1rem;">' + themeName + '</h4>',
                '  <p style="color: var(--secondary-text); font-size: 0.85rem;">Keine Zusammenfassung verfügbar.</p>',
                '</div>'
            ].join('');
            return;
        }

        // Markdown-artige Formatierung in HTML konvertieren
        var htmlContent = convertThemeSummaryToHtml(data.summary);

        var isLocalEnv = document.body.classList.contains('is-local');
        var regenerateBtn = isLocalEnv
            ? '<button onclick="loadThemeSummary(\'' + themeName.replace(/'/g, "\\'") + '\', true)" ' +
              'style="margin-top: 0.8rem; padding: 4px 10px; font-size: 0.78rem; cursor: pointer; ' +
              'background: var(--bg-secondary, #f5f5f5); border: 1px solid var(--border-color, #ddd); ' +
              'border-radius: 4px; color: var(--secondary-text, #666);" ' +
              'onmouseover="this.style.background=\'var(--accent-color, #467886)\'; this.style.color=\'#fff\'" ' +
              'onmouseout="this.style.background=\'var(--bg-secondary, #f5f5f5)\'; this.style.color=\'var(--secondary-text, #666)\'">' +
              '&#x21bb; Neu generieren</button>'
            : '';

        resultsDiv.innerHTML = [
            '<div class="maps-sidepanel-content theme-summary-content" style="padding: 0.1rem 0.5rem 0.8rem 0.5rem;">',
            '  ' + regenerateBtn,
            '  <h1 style="margin: 0 0 0.6rem 0;">' + themeName + '</h1>',
            '  ' + htmlContent,
            '</div>'
        ].join('');

        console.log('[THEME-SUMMARY] Zusammenfassung angezeigt für:', themeName, data.fromCache ? '(Cache)' : '(neu)');

    } catch (error) {
        console.error('[THEME-SUMMARY] Fehler:', error);
        resultsDiv.innerHTML = [
            '<div style="padding: 0.8rem 0.5rem;">',
            '  <h4 style="margin: 0 0 0.5rem 0; color: var(--heading-color); font-size: 1rem;">' + themeName + '</h4>',
            '  <p style="color: #dc2626; font-size: 0.85rem;">Fehler: ' + error.message + '</p>',
            '</div>'
        ].join('');
    }
}

// Inline-Formatierung (fett, GA-Links) für Themen-Zusammenfassungen
function formatThemeSummaryInline(text) {
    var s = String(text || '');
    s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\[([^\]]*?GA\d{1,3}[a-z]?\/\d{1,3}[^\]]*?)\]/g, function(match, inner) {
        var refs = inner.split(/,\s*/);
        var links = refs.map(function(ref) {
            ref = ref.trim();
            var gaMatch = ref.match(/^(GA\d{1,3}[a-z]?)\/(\d{1,3})$/);
            if (gaMatch) {
                var lectureId = gaMatch[1] + '/' + gaMatch[2];
                return '<a href="#" class="theme-summary-ga-link" ' +
                    'onclick="openLectureFromThemeSummary(\'' + lectureId + '\'); return false;" ' +
                    'style="color: var(--accent-color); text-decoration: none; font-weight: 500;" ' +
                    'onmouseover="this.style.textDecoration=\'underline\'" ' +
                    'onmouseout="this.style.textDecoration=\'none\'">' + ref + '</a>';
            }
            return ref;
        });
        return '(' + links.join(', ') + ')';
    });
    return s;
}

// Konvertiert die KI-Zusammenfassung (Markdown-ähnlich) in HTML mit klickbaren GA-Links
function convertThemeSummaryToHtml(text) {
    var lines = String(text || '').replace(/\r\n/g, '\n').split('\n');
    var parts = [];
    var paraLines = [];

    function flushParagraph() {
        if (!paraLines.length) return;
        var joined = paraLines.join(' ').replace(/\s+/g, ' ').trim();
        paraLines = [];
        if (!joined) return;
        parts.push('<p class="paragraph">' + formatThemeSummaryInline(joined) + '</p>');
    }

    lines.forEach(function(line) {
        var trimmed = line.trim();
        if (!trimmed) {
            flushParagraph();
            return;
        }
        if (/^# .+$/.test(trimmed)) return;
        var h2 = trimmed.match(/^## (.+)$/);
        if (h2) {
            flushParagraph();
            parts.push('<h2>' + formatThemeSummaryInline(h2[1]) + '</h2>');
            return;
        }
        var h3 = trimmed.match(/^### (.+)$/);
        if (h3) {
            flushParagraph();
            parts.push('<h3>' + formatThemeSummaryInline(h3[1]) + '</h3>');
            return;
        }
        paraLines.push(trimmed);
    });
    flushParagraph();

    return parts.join('\n');
}

// GA-Link aus der Zusammenfassung: Vortrag im Main Viewer des aktuellen Tabs öffnen (kein Tab-Wechsel)
function openLectureFromThemeSummary(lectureId) {
    console.log('[THEME-SUMMARY] Öffne Vortrag im Themen-Tab:', lectureId);
    // GA028-Kapitel abfangen: auf korrekten Abschnitt umleiten
    if (typeof resolveGA028ChapterId === 'function') {
        var resolved = resolveGA028ChapterId(lectureId);
        if (resolved) {
            console.log('[THEME-SUMMARY] GA028-Kapitel aufgelöst:', lectureId, '->', resolved.parentLectureId, 'para:', resolved.paragraphIndex);
            if (typeof showBookChapter === 'function') {
                showBookChapter(resolved.parentLectureId, resolved.paragraphIndex);
                return;
            }
        }
    }
    if (typeof showLecture === 'function') {
        showLecture(lectureId, null, [], [], false);
    }
}

window.loadThemeSummary = loadThemeSummary;
window.openLectureFromThemeSummary = openLectureFromThemeSummary;

async function openThematicLectureList(theme, startYear, endYear, query, clickedYear) {
    console.log('[THEME2] Opening lecture list for:', theme, startYear, '-', endYear, 'clicked year:', clickedYear);
    
    // 1. Setup summary panel
    var summaryPanel = document.getElementById('summary-panel');
    var summaryContent = document.getElementById('summary-content');
    if (!summaryPanel || !summaryContent) {
        console.error('[THEME2] Summary panel not found');
        return;
    }
    
    // Open panel logic
    summaryPanel.classList.remove('has-members-panel');
    summaryContent.classList.remove('has-members-panel');
    document.body.classList.remove('summary-panel-collapsed');
    summaryPanel.classList.add('visible');
    summaryPanel.style.display = 'block';
    summaryPanel.style.opacity = '1';
    summaryPanel.style.visibility = 'visible';
    
    if (!summaryPanel.style.width || summaryPanel.style.width === '0px') {
        summaryPanel.style.width = '450px';
        var mainContainer = document.getElementById('main-container');
        if (mainContainer) mainContainer.style.marginRight = '450px';
    }

    var verticalResizeHandleWrapper = document.getElementById('verticalResizeHandleWrapper');
    if (verticalResizeHandleWrapper) {
        verticalResizeHandleWrapper.classList.add('visible');
        verticalResizeHandleWrapper.style.display = 'grid';
        if (typeof updateHeaderPosition === 'function') {
            setTimeout(updateHeaderPosition, 50);
        }
    }
    
    // Close-Button im Header anzeigen (nur im Themen-Tab)
    if (typeof updateCloseSummaryPanelButton === 'function') {
        setTimeout(updateCloseSummaryPanelButton, 60);
    }
    
    summaryContent.innerHTML = '';

    // NUR KI-Zuordnungen anzeigen
    try {
        console.log('[THEME2] Lade KI-Zuordnungen für:', theme);
        
        var aiResponse = await fetch('/api/get-theme-results-ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ themeName: theme })
        });
        
        if (aiResponse.ok) {
            var aiData = await aiResponse.json();
            if (aiData.totalResults > 0) {
                console.log('[THEME2] KI-Zuordnungen geladen:', aiData.totalResults, 'Texte');
                
                // Konvertiere Ergebnisse ins erwartete Format
                var results = aiData.results.map(function(r) {
                    return {
                        id: r.id,
                        title: r.title,
                        shortSummary: r.shortSummary,
                        year: r.year,
                        location: r.location,
                        date: r.date,
                        isBookChapter: r.isBookChapter,
                        source: 'ai'
                    };
                });
                
                renderThematic2Results(summaryContent, theme, results, true, true, 'KI-Zuordnung', clickedYear);
                return;
            } else {
                // Keine KI-Zuordnungen vorhanden - Meldung anzeigen
                summaryContent.innerHTML = [
                    '<div style="padding: 2rem; text-align: center;">',
                    '  <h3 style="color: var(--heading-color); margin-bottom: 1rem;">' + theme + '</h3>',
                    '  <p style="color: var(--secondary-text);">Noch keine KI-Zuordnungen für dieses Thema.</p>',
                    '  <p style="color: var(--secondary-text); font-size: 0.85rem; margin-top: 0.5rem;">',
                    '    Bisher wurden nur GA046 und GA051-060 zugeordnet.',
                    '  </p>',
                    '</div>'
                ].join('');
                return;
            }
        }
    } catch (e) {
        console.error('[THEME2] Fehler beim Laden der KI-Zuordnungen:', e);
        summaryContent.innerHTML = '<div style="padding: 2rem; text-align: center; color: #dc2626;">Fehler beim Laden der KI-Zuordnungen</div>';
        return;
    }
}

// Global reference
window.initThematicVisualization = initThematicVisualization;

// Auto-init logic
function autoInitThematic2() {
    if (window.location.hash.includes('thematic2')) {
        console.log('[THEME2] Auto-init triggered by hash');
        initThematicVisualization();
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInitThematic2);
} else {
    autoInitThematic2();
}

// ============================================================
// Schlagwort-Verwaltung
// ============================================================

// Speichert die aktuellen Schlagwort-Einstellungen pro Theme (persistent in localStorage)
var themeKeywordSettings = {};
var keywordSettingsInitialized = false;
var KEYWORD_STORAGE_KEY = 'steiner_theme_keywords';

// Lade gespeicherte Einstellungen aus localStorage
function loadKeywordSettingsFromStorage() {
    try {
        var stored = localStorage.getItem(KEYWORD_STORAGE_KEY);
        if (stored) {
            return JSON.parse(stored);
        }
    } catch (e) {
        console.warn('[THEME2] Could not load keyword settings from storage:', e);
    }
    return null;
}

// Speichere Einstellungen in localStorage
function saveKeywordSettingsToStorage() {
    try {
        localStorage.setItem(KEYWORD_STORAGE_KEY, JSON.stringify(themeKeywordSettings));
        localStorage.setItem(KEYWORD_STORAGE_KEY + '_version', '2'); // Version für Unterstrich-Migration
        console.log('[THEME2] Keyword settings saved to localStorage');
    } catch (e) {
        console.warn('[THEME2] Could not save keyword settings to storage:', e);
    }
}

// Initialisiere themeKeywordSettings aus SteinerThemesData oder localStorage
function initKeywordSettings() {
    if (!keywordSettingsInitialized) {
        console.log('[THEME2] Initializing keyword settings...');
        
        // Prüfe Version - bei alter Version einmalig zurücksetzen (Unterstrich-Migration)
        var currentVersion = '2';
        var storedVersion = null;
        try {
            storedVersion = localStorage.getItem(KEYWORD_STORAGE_KEY + '_version');
        } catch (e) { /* ignore */ }
        
        if (storedVersion !== currentVersion) {
            console.log('[THEME2] Alte Version erkannt, setze Einstellungen zurück...');
            try {
                localStorage.removeItem(KEYWORD_STORAGE_KEY);
                localStorage.setItem(KEYWORD_STORAGE_KEY + '_version', currentVersion);
            } catch (e) { /* ignore */ }
        }
        
        // Versuche gespeicherte Einstellungen zu laden
        var storedSettings = loadKeywordSettingsFromStorage();
        
        for (var i = 0; i < SteinerThemesData.length; i++) {
            var theme = SteinerThemesData[i];
            var keywords = splitKeywords(theme.query);
            
            // Prüfe ob es gespeicherte Einstellungen für dieses Theme gibt
            if (storedSettings && storedSettings[theme.theme]) {
                var stored = storedSettings[theme.theme];
                // Migriere gespeicherte Keywords: Unterstriche durch Leerzeichen ersetzen
                var migratedActive = (stored.activeKeywords || []).map(function(kw) {
                    return kw.replace(/_/g, ' ');
                });
                var migratedAdded = (stored.addedKeywords || []).map(function(kw) {
                    return kw.replace(/_/g, ' ');
                });
                // Filtere nur gültige Keywords (die in original oder added vorkommen)
                var validActive = migratedActive.filter(function(kw) {
                    return keywords.indexOf(kw) !== -1 || migratedAdded.indexOf(kw) !== -1;
                });
                // Falls keine gültigen aktiven Keywords, verwende alle original
                if (validActive.length === 0) {
                    validActive = keywords.slice();
                }
                themeKeywordSettings[theme.theme] = {
                    originalKeywords: keywords.slice(),
                    activeKeywords: validActive,
                    addedKeywords: migratedAdded.filter(function(kw) { return keywords.indexOf(kw) === -1; })
                };
                console.log('[THEME2] Loaded stored settings for:', theme.theme);
            } else {
                themeKeywordSettings[theme.theme] = {
                    originalKeywords: keywords.slice(),
                    activeKeywords: keywords.slice(),
                    addedKeywords: []
                };
            }
        }
        keywordSettingsInitialized = true;
        console.log('[THEME2] Keyword settings initialized for', Object.keys(themeKeywordSettings).length, 'themes');
    }
}

// Befülle das Dropdown mit allen Themenschwerpunkten
function populateThemeSelector() {
    initKeywordSettings();
    var selector = document.getElementById('themeKeywordSelector');
    if (!selector) return;
    
    // Sortiere SteinerThemesData alphabetisch (falls noch nicht sortiert)
    SteinerThemesData.sort(function(a, b) {
        return a.theme.localeCompare(b.theme, 'de');
    });
    
    // Behalte die erste Option
    selector.innerHTML = '<option value="">-- Bitte wählen --</option>';
    
    for (var i = 0; i < SteinerThemesData.length; i++) {
        var option = document.createElement('option');
        option.value = SteinerThemesData[i].theme;
        option.textContent = SteinerThemesData[i].theme;
        selector.appendChild(option);
    }
}

// Zeige die Schlagwörter des ausgewählten Themes als Chips an
function displayThemeKeywords() {
    console.log('[THEME2] displayThemeKeywords called');
    initKeywordSettings();
    
    var selector = document.getElementById('themeKeywordSelector');
    var container = document.getElementById('keywordChipsContainer');
    var chipsDiv = document.getElementById('keywordChips');
    
    if (!selector || !container || !chipsDiv) {
        console.log('[THEME2] Required elements not found');
        return;
    }
    
    var selectedTheme = selector.value;
    console.log('[THEME2] Selected theme:', selectedTheme);
    
    if (!selectedTheme) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    chipsDiv.innerHTML = '';
    
    var settings = themeKeywordSettings[selectedTheme];
    if (!settings) {
        console.log('[THEME2] No settings found for theme:', selectedTheme);
        return;
    }
    
    console.log('[THEME2] Settings:', JSON.stringify(settings));
    
    // Zeige alle Keywords (original + hinzugefügte), Duplikate vermeiden
    var allKeywords = [];
    var seen = {};
    
    // Erst Original-Keywords
    for (var i = 0; i < settings.originalKeywords.length; i++) {
        var kw = settings.originalKeywords[i];
        if (!seen[kw]) {
            allKeywords.push(kw);
            seen[kw] = true;
        }
    }
    
    // Dann hinzugefügte Keywords
    for (var j = 0; j < settings.addedKeywords.length; j++) {
        var akw = settings.addedKeywords[j];
        if (!seen[akw]) {
            allKeywords.push(akw);
            seen[akw] = true;
        }
    }
    
    console.log('[THEME2] All keywords:', allKeywords);
    console.log('[THEME2] Active keywords:', settings.activeKeywords);
    
    for (var k = 0; k < allKeywords.length; k++) {
        var keyword = allKeywords[k];
        var isActive = settings.activeKeywords.indexOf(keyword) !== -1;
        var isAdded = settings.addedKeywords.indexOf(keyword) !== -1;
        
        var chip = document.createElement('span');
        chip.className = 'keyword-chip' + (isActive ? ' active' : ' inactive');
        chip.setAttribute('data-keyword', keyword);
        chip.setAttribute('data-theme', selectedTheme);
        chip.innerHTML = keyword + (isAdded ? ' <span style="opacity:0.6;">+</span>' : '');
        chip.style.cssText = 'padding: 4px 10px; border-radius: 15px; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 4px;';
        
        if (isActive) {
            chip.style.background = 'var(--primary-color, #4a90a4)';
            chip.style.color = 'white';
        } else {
            chip.style.background = 'var(--border-color, #ddd)';
            chip.style.color = 'var(--secondary-text, #666)';
            chip.style.textDecoration = 'line-through';
        }
        
        // Closure für korrekten Scope
        (function(kw, th) {
            chip.onclick = function() {
                toggleKeyword(th, kw);
            };
        })(keyword, selectedTheme);
        
        chipsDiv.appendChild(chip);
    }
    
    // Lucide Icons aktualisieren
    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        lucide.createIcons();
    }
}

// Toggle ein Schlagwort aktiv/inaktiv
function toggleKeyword(themeName, keyword) {
    console.log('[THEME2] toggleKeyword called:', themeName, keyword);
    initKeywordSettings(); // Sicherstellen, dass Settings initialisiert sind
    
    var settings = themeKeywordSettings[themeName];
    if (!settings) {
        console.log('[THEME2] Settings not found for theme:', themeName);
        return;
    }
    
    var index = settings.activeKeywords.indexOf(keyword);
    if (index !== -1) {
        // Deaktivieren
        settings.activeKeywords.splice(index, 1);
        console.log('[THEME2] Deactivated keyword:', keyword);
    } else {
        // Aktivieren
        settings.activeKeywords.push(keyword);
        console.log('[THEME2] Activated keyword:', keyword);
    }
    
    displayThemeKeywords();
}

// Neues Schlagwort hinzufügen (für Themenschwerpunkte)
function addThemeKeyword() {
    console.log('[THEME2] addThemeKeyword called');
    initKeywordSettings(); // Sicherstellen, dass Settings initialisiert sind
    
    var input = document.getElementById('themeNewKeywordInput');
    var selector = document.getElementById('themeKeywordSelector');
    
    if (!input || !selector) {
        console.log('[THEME2] Input or selector not found. Input:', input, 'Selector:', selector);
        return;
    }
    
    var keyword = input.value.trim();
    var selectedTheme = selector.value;
    
    console.log('[THEME2] Adding keyword:', keyword, 'to theme:', selectedTheme);
    
    if (!keyword) {
        alert('Bitte geben Sie ein Schlagwort ein.');
        return;
    }
    
    if (!selectedTheme) {
        alert('Bitte wählen Sie zuerst einen Themenschwerpunkt.');
        return;
    }
    
    var settings = themeKeywordSettings[selectedTheme];
    if (!settings) {
        console.log('[THEME2] Settings not found for theme:', selectedTheme);
        return;
    }
    
    // Prüfe ob Schlagwort bereits existiert
    if (settings.originalKeywords.indexOf(keyword) !== -1 || settings.addedKeywords.indexOf(keyword) !== -1) {
        alert('Dieses Schlagwort existiert bereits.');
        return;
    }
    
    // Hinzufügen
    settings.addedKeywords.push(keyword);
    settings.activeKeywords.push(keyword);
    
    console.log('[THEME2] Keyword added. Active keywords:', settings.activeKeywords);
    
    input.value = '';
    displayThemeKeywords();
}

// Setze die Schlagwörter eines Themes auf Original zurück
function resetThemeKeywords() {
    console.log('[THEME2] resetThemeKeywords called');
    initKeywordSettings(); // Sicherstellen, dass Settings initialisiert sind
    
    var selector = document.getElementById('themeKeywordSelector');
    if (!selector) return;
    
    var selectedTheme = selector.value;
    if (!selectedTheme) {
        alert('Bitte wählen Sie zuerst einen Themenschwerpunkt.');
        return;
    }
    
    var settings = themeKeywordSettings[selectedTheme];
    if (!settings) return;
    
    // Originale Keywords aus der ursprünglichen SteinerThemesData-Definition holen
    var themeData = SteinerThemesData.find(function(t) { return t.theme === selectedTheme; });
    if (themeData) {
        // Hole die Original-Query aus dem ursprünglichen Daten-Array
        var originalQuery = getOriginalThemeQuery(selectedTheme);
        var originalFromData = splitKeywords(originalQuery);
        settings.originalKeywords = originalFromData.slice();
    }
    
    settings.activeKeywords = settings.originalKeywords.slice();
    settings.addedKeywords = [];
    
    // Speichere die Zurücksetzung in localStorage
    saveKeywordSettingsToStorage();
    
    console.log('[THEME2] Reset keywords for:', selectedTheme, settings.activeKeywords);
    displayThemeKeywords();
}

// Hole die ursprüngliche Query für ein Theme (vor allen Änderungen)
function getOriginalThemeQuery(themeName) {
    var originalQueries = {
        "Abstammung / Evolution": "Abstammung Evolution Haeckel",
        "Anthroposophische Künste": "Eurythmie Sprachgestaltung Schauspielkunst Malerei Materie Bildhauerei Architektur",
        "Medizin / Heilkunde": "Medizin Heilkunde Heilmittel Pathologie Therapie",
        "Bibel / Evangelien": "Bibel Evangelium",
        "Böses (Luzifer, Ahriman)": "Luzifer Ahriman Böses",
        "Christengemeinschaft": "Christengemeinschaft",
        "Christus / Golgatha": "Christus Golgatha",
        "Darwinismus": "Darwinismus Darwin",
        "Erkenntnistheorie / Philosophie": "Erkenntnistheorie Philosophie",
        "Freiheitsphilosophie": "Philosophie der Freiheit",
        "Geistige Hierarchien": "Geistige Hierarchien",
        "Geistige Weltbereiche": "Geistige Welt Astralwelt Devachan",
        "geistiges Naturerkennen": "Naturerkennen",
        "Geschichte / Kulturentwicklung": "Geschichte Kulturentwicklung",
        "Goethe (Faust, Märchen)": "Goethe Faust Märchen",
        "Goethe & Goetheanismus": "Goethe & Goetheanismus",
        "Kosmologie / Kosmogonie": "Kosmologie Kosmogonie",
        "Ernährung / Landwirtschaft": "Ernährung / Landwirtschaft",
        "Meditation / Schulungsweg": "Meditation Schulungsweg",
        "Menschenkunde & Dreigliederung": "Menschenkunde Dreigliederung",
        "Menschheitsentwicklung": "Menschheitsentwicklung",
        "Michael": "Michael Michael-Briefe",
        "Mysteriendramen": "Mysteriendramen",
        "Mysterienwesen / Einweihung": "Mysterienwesen Einweihung",
        "Naturreiche": "Naturreiche Mineralreich Pflanzenreich Tierreich Menschenreich",
        "Naturwissenschaft": "Naturwissenschaft",
        "Pädagogik / Heilpädagogik": "Pädagogik Heilpädagogik",
        "Reinkarnation und Karma": "Reinkarnation Karma",
        "Religionen / Weisheitslehren": "Religionen Weisheitslehren Buddhismus Hinduismus Islam Judentum",
        "Rosenkreuzer": "Rosenkreuzer Rosenkreuzertum Christian Rosenkreutz",
        "Schlaf & Tod": "Schlaf Tod",
        "Seelenfähigkeiten": "Denken Fühlen Wollen Gedächtnis",
        "Sinneslehre": "Sinneslehre Sinnesorganisation",
        "Soziale Dreigliederung": "Soziale Dreigliederung",
        "Elemente / Ätherarten": "Elemente Feuer Luft Wasser Erde Äther Ätherarten",
        "Wesensglieder": "Wesensglieder",
        "West-Ost-Gegensatz": "West-Ost-Gegensatz Orient Okzident"
    };
    return originalQueries[themeName] || "";
}

// Speichere die Schlagwort-Änderungen (persistent in Datei via Backend-API)
async function saveKeywordChanges() {
    var selector = document.getElementById('themeKeywordSelector');
    if (!selector) return;
    
    var selectedTheme = selector.value;
    if (!selectedTheme) {
        alert('Bitte wählen Sie zuerst einen Themenschwerpunkt.');
        return;
    }
    
    var settings = themeKeywordSettings[selectedTheme];
    if (!settings || settings.activeKeywords.length === 0) {
        alert('Mindestens ein Schlagwort muss aktiv sein.');
        return;
    }
    
    var newQuery = settings.activeKeywords.join(' ');
    
    // Finde das Theme-Objekt und aktualisiere die Query lokal
    for (var i = 0; i < SteinerThemesData.length; i++) {
        if (SteinerThemesData[i].theme === selectedTheme) {
            SteinerThemesData[i].query = newQuery;
            break;
        }
    }
    
    // Speichere in localStorage als Backup
    saveKeywordSettingsToStorage();
    
    // Zeige Lade-Status
    var container = document.getElementById('keywordChipsContainer');
    var statusMsg = document.createElement('div');
    statusMsg.className = 'keyword-save-status';
    statusMsg.style.cssText = 'margin-top: 0.8rem; padding: 8px 12px; background: var(--info-bg, #d1ecf1); color: var(--info-text, #0c5460); border-radius: 4px; font-size: 0.85rem; text-align: center;';
    statusMsg.innerHTML = '⏳ Speichere...';
    
    if (container) {
        var oldStatus = container.querySelector('.keyword-save-status');
        if (oldStatus) oldStatus.remove();
        container.appendChild(statusMsg);
    }
    
    // Speichere über Backend-API in die Datei
    try {
        var response = await fetch('/api/save-theme-keywords', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                themeName: selectedTheme,
                newQuery: newQuery
            })
        });
        
        var result = await response.json();
        
        if (response.ok && result.success) {
            // Erfolg - aktualisiere die Original-Keywords auf die aktiven
            settings.originalKeywords = settings.activeKeywords.slice();
            settings.addedKeywords = []; // Hinzugefügte sind jetzt Teil der Originale
            
            // Speichere aktualisierten Zustand in localStorage
            saveKeywordSettingsToStorage();
            
            // UI neu rendern (entfernt gelöschte Schlagwörter aus der Anzeige)
            displayThemeKeywords();
            
            statusMsg.style.background = 'var(--info-bg, #d1ecf1)';
            statusMsg.style.color = 'var(--info-text, #0c5460)';
            statusMsg.innerHTML = '⏳ Zeitraum wird neu berechnet...';
            
            // Berechne den Zeitraum für dieses Thema neu
            try {
                var rangeResponse = await fetch('/api/calculate-theme-ranges', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ themeName: selectedTheme })
                });
                
                if (rangeResponse.ok) {
                    var rangeResult = await rangeResponse.json();
                    themeRangesCache = rangeResult.cache;
                    
                    // Aktualisiere dynamische Daten
                    dynamicThemesData = SteinerThemesData.map(function(theme) {
                        var cached = themeRangesCache[theme.theme];
                        if (cached && cached.ranges) {
                            return {
                                theme: theme.theme,
                                ranges: cached.ranges,
                                query: theme.query,
                                totalMatches: cached.totalMatches || 0
                            };
                        }
                        return theme;
                    });
                    
                    // Grafik neu rendern
                    var chartContainer = document.getElementById('thematic2-visualization-main');
                    if (chartContainer) {
                        renderThematicChart(chartContainer);
                    }
                    
                    console.log('[THEME2] Zeitraum aktualisiert für:', selectedTheme);
                }
            } catch (e) {
                console.warn('[THEME2] Zeitraum-Update fehlgeschlagen:', e);
            }
            
            // Invalidiere den Suchergebnis-Cache für dieses Thema
            try {
                await fetch('/api/invalidate-theme-cache', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ themeName: selectedTheme })
                });
                console.log('[THEME2] Suchergebnis-Cache invalidiert für:', selectedTheme);
            } catch (e) {
                console.warn('[THEME2] Cache-Invalidierung fehlgeschlagen:', e);
            }
            
            statusMsg.style.background = 'var(--success-bg, #d4edda)';
            statusMsg.style.color = 'var(--success-text, #155724)';
            statusMsg.innerHTML = '✓ Schlagwörter und Zeitraum für <strong>' + selectedTheme + '</strong> aktualisiert!';
            console.log('[THEME2] Schlagwörter erfolgreich in Datei gespeichert:', selectedTheme);
        } else {
            // Fehler vom Server
            statusMsg.style.background = 'var(--warning-bg, #fff3cd)';
            statusMsg.style.color = 'var(--warning-text, #856404)';
            statusMsg.innerHTML = '⚠ Lokal gespeichert (Datei-Update fehlgeschlagen: ' + (result.error || 'Unbekannter Fehler') + ')';
            console.warn('[THEME2] Datei-Update fehlgeschlagen:', result.error);
        }
    } catch (error) {
        // Netzwerk-Fehler - nur lokal gespeichert
        statusMsg.style.background = 'var(--warning-bg, #fff3cd)';
        statusMsg.style.color = 'var(--warning-text, #856404)';
        statusMsg.innerHTML = '⚠ Nur lokal gespeichert (Server nicht erreichbar)';
        console.warn('[THEME2] Server nicht erreichbar:', error);
    }
    
    // Entferne Statusmeldung nach 5 Sekunden
    setTimeout(function() {
        if (statusMsg.parentNode) statusMsg.remove();
    }, 5000);
}

// KI-Neu-Zuordnung für ausgewähltes Thema
async function reassignThemeWithAI() {
    var selector = document.getElementById('themeKeywordSelector');
    var statusDiv = document.getElementById('reassignThemeStatus');
    
    if (!selector || !selector.value) {
        alert('Bitte wählen Sie zuerst ein Thema aus.');
        return;
    }
    
    var themeName = selector.value;
    
    // Erst Kandidaten zählen (schnelle Anfrage)
    statusDiv.style.display = 'block';
    statusDiv.style.cssText = 'margin-top: 0.5rem; padding: 8px 12px; background: var(--info-bg, #d1ecf1); color: var(--info-text, #0c5460); border-radius: 4px; font-size: 0.85rem; text-align: center;';
    statusDiv.innerHTML = 'Zähle Kandidaten...';
    
    try {
        var countResponse = await fetch('/api/reassign-single-theme', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ themeName: themeName, countOnly: true })
        });
        var countResult = await countResponse.json();
        
        if (!countResponse.ok) {
            statusDiv.style.background = 'var(--danger-bg, #f8d7da)';
            statusDiv.style.color = 'var(--danger-text, #721c24)';
            statusDiv.innerHTML = '✗ Fehler: ' + (countResult.error || 'Unbekannt');
            return;
        }
        
        var candidateCount = countResult.candidates || 0;
        var skippedCount = countResult.skippedAlreadyProcessed || 0;
        
        if (candidateCount === 0) {
            if (skippedCount > 0) {
                statusDiv.style.background = 'var(--success-bg, #d4edda)';
                statusDiv.style.color = 'var(--success-text, #155724)';
                statusDiv.innerHTML = '✓ Alle ' + skippedCount + ' Kandidaten wurden bereits verarbeitet.';
            } else {
                statusDiv.style.background = 'var(--warning-bg, #fff3cd)';
                statusDiv.style.color = 'var(--warning-text, #856404)';
                statusDiv.innerHTML = 'Keine Kandidaten gefunden. Prüfen Sie die Schlagwörter.';
            }
            return;
        }
        
        // Bestätigung mit Kandidatenzahl
        var estimatedTime = Math.ceil(candidateCount / 10 * 0.7); // ca. 0.7s pro 10 Texte
        var estimatedCost = (candidateCount * 0.0001).toFixed(3); // ca. $0.0001 pro Text
        
        var skippedInfo = skippedCount > 0 ? '\n⏭️ ' + skippedCount + ' bereits verarbeitet (übersprungen)' : '';
        
        if (!confirm('Thema "' + themeName + '" mit KI neu zuordnen?\n\n' +
            '📊 ' + candidateCount + ' neue Kandidaten' + skippedInfo + '\n' +
            '⏱️ Geschätzte Zeit: ~' + estimatedTime + ' Sekunden\n' +
            '💰 Geschätzte Kosten: ~$' + estimatedCost + '\n\n' +
            'Fortfahren?')) {
            statusDiv.style.display = 'none';
            return;
        }
        
    } catch (e) {
        statusDiv.style.background = 'var(--danger-bg, #f8d7da)';
        statusDiv.style.color = 'var(--danger-text, #721c24)';
        statusDiv.innerHTML = '✗ Fehler beim Zählen: ' + e.message;
        return;
    }
    
    // Status anzeigen
    statusDiv.style.cssText = 'margin-top: 0.5rem; padding: 8px 12px; background: var(--info-bg, #d1ecf1); color: var(--info-text, #0c5460); border-radius: 4px; font-size: 0.85rem; text-align: center;';
    statusDiv.innerHTML = '<i data-lucide="loader" class="spin" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle; margin-right: 6px;"></i> KI-Zuordnung läuft (0/' + candidateCount + ')...';
    
    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        lucide.createIcons();
    }
    
    try {
        var response = await fetch('/api/reassign-single-theme', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ themeName: themeName })
        });
        
        var result = await response.json();
        
        if (response.ok && result.success) {
            statusDiv.style.background = 'var(--success-bg, #d4edda)';
            statusDiv.style.color = 'var(--success-text, #155724)';
            statusDiv.innerHTML = '✓ <strong>' + result.processed + '</strong> Texte geprüft: <strong>+' + result.added + '</strong> hinzugefügt, <strong>-' + result.removed + '</strong> entfernt';
            
            // Heatmap neu laden
            try {
                var rangeResponse = await fetch('/api/theme-assignments-status');
                if (rangeResponse.ok) {
                    var rangeResult = await rangeResponse.json();
                    themeRangesCache = rangeResult.themeRanges || {};
                    
                    // Aktualisiere dynamische Daten
                    dynamicThemesData = SteinerThemesData.map(function(theme) {
                        var cached = themeRangesCache[theme.theme];
                        if (cached && cached.ranges) {
                            return {
                                theme: theme.theme,
                                ranges: cached.ranges,
                                query: theme.query,
                                totalMatches: cached.totalMatches || 0
                            };
                        }
                        return theme;
                    });
                    
                    // Grafik neu rendern
                    var chartContainer = document.getElementById('thematic2-visualization-main');
                    if (chartContainer) {
                        renderThematicChart(chartContainer);
                    }
                }
            } catch (e) {
                console.warn('[THEME2] Heatmap-Update fehlgeschlagen:', e);
            }
            
        } else {
            statusDiv.style.background = 'var(--danger-bg, #f8d7da)';
            statusDiv.style.color = 'var(--danger-text, #721c24)';
            statusDiv.innerHTML = '✗ Fehler: ' + (result.error || 'Unbekannter Fehler');
        }
        
    } catch (error) {
        statusDiv.style.background = 'var(--danger-bg, #f8d7da)';
        statusDiv.style.color = 'var(--danger-text, #721c24)';
        statusDiv.innerHTML = '✗ Netzwerkfehler: ' + error.message;
    }
    
    // Status nach 10 Sekunden ausblenden
    setTimeout(function() {
        statusDiv.style.display = 'none';
    }, 10000);
}

// Beim Klick auf einen Balken in der Grafik: Theme im Dropdown auswählen
function selectThemeInDropdown(themeName) {
    var selector = document.getElementById('themeKeywordSelector');
    if (selector) {
        selector.value = themeName;
        displayThemeKeywords();
    }
}

// Initialisiere das Dropdown beim Tab-Wechsel
function initKeywordManagement() {
    console.log('[THEME2] initKeywordManagement called');
    console.log('[THEME2] SteinerThemesData length:', SteinerThemesData.length);
    console.log('[THEME2] themeKeywordSelector exists:', !!document.getElementById('themeKeywordSelector'));
    populateThemeSelector();
}

// Exportiere alle Schlagwort-Änderungen als Code für permanente Speicherung
function exportKeywordChanges() {
    initKeywordSettings();
    
    var changes = [];
    var hasChanges = false;
    
    // Vergleiche aktuelle Einstellungen mit Originalen
    for (var themeName in themeKeywordSettings) {
        var settings = themeKeywordSettings[themeName];
        var originalQuery = getOriginalThemeQuery(themeName);
        var originalKeywords = splitKeywords(originalQuery);
        var currentKeywords = settings.activeKeywords.slice().sort();
        var origSorted = originalKeywords.slice().sort();
        
        // Prüfe ob es Unterschiede gibt
        var isDifferent = currentKeywords.length !== origSorted.length;
        if (!isDifferent) {
            for (var i = 0; i < currentKeywords.length; i++) {
                if (currentKeywords[i] !== origSorted[i]) {
                    isDifferent = true;
                    break;
                }
            }
        }
        
        if (isDifferent) {
            hasChanges = true;
            var added = settings.addedKeywords.slice();
            var removed = [];
            
            // Finde entfernte Keywords
            for (var j = 0; j < originalKeywords.length; j++) {
                if (settings.activeKeywords.indexOf(originalKeywords[j]) === -1) {
                    removed.push(originalKeywords[j]);
                }
            }
            
            changes.push({
                theme: themeName,
                newQuery: settings.activeKeywords.join(' '),
                added: added,
                removed: removed
            });
        }
    }
    
    if (!hasChanges) {
        alert('Keine Änderungen vorhanden.');
        return;
    }
    
    // Erstelle Export-Text
    var exportText = '=== SCHLAGWORT-ÄNDERUNGEN FÜR PERMANENTE SPEICHERUNG ===\n\n';
    exportText += 'Bitte diese Änderungen an den Entwickler senden:\n\n';
    
    for (var k = 0; k < changes.length; k++) {
        var change = changes[k];
        exportText += '----------------------------------------\n';
        exportText += 'THEMA: ' + change.theme + '\n';
        exportText += 'NEUE QUERY: "' + change.newQuery + '"\n';
        if (change.added.length > 0) {
            exportText += 'HINZUGEFÜGT: ' + change.added.join(', ') + '\n';
        }
        if (change.removed.length > 0) {
            exportText += 'ENTFERNT: ' + change.removed.join(', ') + '\n';
        }
        exportText += '\n';
    }
    
    exportText += '----------------------------------------\n';
    exportText += '\nCODE ZUM EINFÜGEN IN SteinerThemesData:\n\n';
    
    for (var m = 0; m < changes.length; m++) {
        var c = changes[m];
        exportText += '// ' + c.theme + '\n';
        exportText += 'query: "' + c.newQuery + '"\n\n';
    }
    
    // Zeige Export-Dialog
    var dialog = document.createElement('div');
    dialog.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 10000; display: flex; align-items: center; justify-content: center;';
    dialog.innerHTML = [
        '<div style="background: var(--bg-color, white); border-radius: 8px; padding: 1.5rem; max-width: 600px; width: 90%; max-height: 80vh; overflow: hidden; display: flex; flex-direction: column;">',
        '  <h3 style="margin: 0 0 1rem 0; color: var(--heading-color, #333);">Schlagwort-Änderungen exportieren</h3>',
        '  <textarea readonly style="flex: 1; min-height: 300px; padding: 1rem; font-family: monospace; font-size: 0.85rem; border: 1px solid var(--border-color, #ddd); border-radius: 4px; resize: none; background: var(--input-bg, #f5f5f5); color: var(--text-color, #333);">' + exportText.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</textarea>',
        '  <div style="margin-top: 1rem; display: flex; gap: 8px; justify-content: flex-end;">',
        '    <button class="depth-btn" onclick="this.closest(\'div[style*=position]\').remove()" style="padding: 8px 16px;">Schließen</button>',
        '    <button class="depth-btn primary" onclick="navigator.clipboard.writeText(this.closest(\'div\').querySelector(\'textarea\').value); this.textContent=\'✓ Kopiert!\'; setTimeout(function(btn){btn.textContent=\'In Zwischenablage kopieren\';}.bind(null,this), 2000);" style="padding: 8px 16px;">In Zwischenablage kopieren</button>',
        '  </div>',
        '</div>'
    ].join('');
    
    document.body.appendChild(dialog);
    
    // Klick außerhalb schließt Dialog
    dialog.addEventListener('click', function(e) {
        if (e.target === dialog) dialog.remove();
    });
}

// Schwerpunkte-Infobox Sichtbarkeit + themenInfoBtn (Viewer-Header) bei View-/Tab-Wechsel
(function() {
    function updateThemenInfoBtn(view) {
        var btn = document.getElementById('themenInfoBtn');
        if (!btn) return;
        if (view === 'schwerpunkte' || view === 'timeline' || view === 'sammlungen') {
            window._themenInfoType = view;
            var titles = { schwerpunkte: 'Themenschwerpunkte – Info', timeline: 'Timeline – Info', sammlungen: 'Sammlungen – Info' };
            btn.setAttribute('title', titles[view] || 'Info');
            btn.style.display = 'inline-flex';
        } else {
            btn.style.display = 'none';
        }
    }

    function patchSwitchThemenView() {
        if (window._schwerpunkteInfoPatchDone) return;
        var origSwitch = window.switchThemenView;
        if (origSwitch) {
            window.switchThemenView = function(view) {
                var infoDiv = document.getElementById('thematic2-schwerpunkte-info');
                if (infoDiv) infoDiv.style.display = view === 'schwerpunkte' ? '' : 'none';
                updateThemenInfoBtn(view);
                return origSwitch.apply(this, arguments);
            };
            window._schwerpunkteInfoPatchDone = true;
        }
    }

    function patchSwitchTab() {
        if (window._switchTabThemenInfoPatchDone) return;
        var orig = window.switchTab;
        if (orig) {
            window.switchTab = function(mode) {
                var btn = document.getElementById('themenInfoBtn');
                if (btn) {
                    if (mode === 'thematic2') {
                        var v = window._themenView || 'schwerpunkte';
                        updateThemenInfoBtn(v);
                    } else {
                        btn.style.display = 'none';
                    }
                }
                return orig.apply(this, arguments);
            };
            window._switchTabThemenInfoPatchDone = true;
        }
    }

    function runPatches() {
        patchSwitchThemenView();
        patchSwitchTab();
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', runPatches);
    } else {
        setTimeout(runPatches, 0);
    }
})();

// Themen-Info-Panel: Schwerpunkte / Timeline (analog zu Bibliographie-Infopanel im Texte-Tab)
function showThemenInfoPanel(type) {
    var popup = document.getElementById('themenInfoPopup');
    var titleEl = document.getElementById('themenInfoTitle');
    var contentEl = document.getElementById('themenInfoContent');
    if (!popup || !titleEl || !contentEl) return;

    if (type === 'schwerpunkte') {
        titleEl.textContent = 'Themenschwerpunkte – Info';
        contentEl.innerHTML = '<p style="margin: 0 0 0.6rem 0;">Die Zuordnung von Texten (Bücher, Aufsätze, Vorträge, Briefe) zu einem bestimmten Thema erfolgte durch Claude (KI). Die KI ordnete Zusammenfassungen der Texte zu den passenden Themen, welche jeweils eine Reihe von Schlagwörtern umfassen. Die Darstellung gibt eine gute Orientierung, ist aber nicht vollständig, da durch dieses Verfahren nicht jede thematisch relevante Passage erfasst werden kann. Bei Klick auf ein Feld werden die entsprechenden Text-Zusammenfassungen angezeigt.</p>';
    } else if (type === 'timeline') {
        titleEl.textContent = 'Timeline – Info';
        contentEl.innerHTML = '<p style="margin: 0 0 0.6rem 0;">Die Timeline basiert auf thematischen Gliederungen der einzelnen Texte (Bücher, Aufsätze, Vorträge, Briefe, u.a.) sowie auf einer Stichwortsuche in diesen Texten mit hoher Relevanz.</p><p style="margin: 0 0 0.6rem 0;">Nach Auswahl eines Themas / Schlagworts werden die entsprechenden Texte chronologisch nach Jahr dargestellt. Bei Klick auf einen Eintrag werden die entsprechenden Textstellen angezeigt. Die Darstellung gibt eine gute Orientierung, ist aber nicht vollständig.</p>';
    } else if (type === 'sammlungen') {
        titleEl.textContent = 'Sammlungen – Info';
        contentEl.innerHTML = '<p style="margin: 0 0 0.6rem 0;">Die Zitatsammlungen wurden von Mitarbeitern der Akanthos-Akademie durch ausführliche Suche in der Rudolf Steiner Gesamtausgabe erarbeitet. Sie können als nahezu vollständig zu dem jeweiligen Thema angesehen werden.</p>';
    } else {
        return;
    }
    popup.style.display = 'flex';
}

function closeThemenInfoPopup(event) {
    if (event && event.target.id === 'themenInfoPopup') {
        document.getElementById('themenInfoPopup').style.display = 'none';
    } else if (!event) {
        document.getElementById('themenInfoPopup').style.display = 'none';
    }
}

// Auto-init keyword management when thematic2 tab becomes active
(function() {
    var origInit = window.initThematicVisualization;
    window.initThematicVisualization = function() {
        if (origInit) origInit();
        initKeywordManagement();
    };
})();

// Ausgewählten Themenschwerpunkt umbenennen
async function renameSelectedTheme() {
    var selector = document.getElementById('themeKeywordSelector');
    var renameInput = document.getElementById('renameThemeInput');
    var statusDiv = document.getElementById('renameThemeStatus');
    
    if (!selector || !renameInput) return;
    
    var oldName = selector.value;
    var newName = renameInput.value.trim();
    
    if (!oldName) {
        alert('Bitte wählen Sie zuerst einen Themenschwerpunkt aus dem Dropdown oben.');
        return;
    }
    
    if (!newName) {
        alert('Bitte geben Sie einen neuen Namen ein.');
        return;
    }
    
    if (oldName === newName) {
        alert('Der neue Name ist identisch mit dem alten.');
        return;
    }
    
    // Prüfe ob neuer Name bereits existiert (aber erlaube Groß-/Kleinschreibung-Änderung)
    for (var i = 0; i < SteinerThemesData.length; i++) {
        if (SteinerThemesData[i].theme === newName) {
            alert('Ein Themenschwerpunkt mit exakt diesem Namen existiert bereits.');
            return;
        }
    }
    
    // Zeige Lade-Status
    if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.style.cssText = 'margin-top: 0.8rem; padding: 8px 12px; background: var(--info-bg, #d1ecf1); color: var(--info-text, #0c5460); border-radius: 4px; font-size: 0.85rem; text-align: center;';
        statusDiv.innerHTML = '⏳ Benenne um...';
    }
    
    try {
        var response = await fetch('/api/rename-theme', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ oldName: oldName, newName: newName })
        });
        
        var result = await response.json();
        
        if (response.ok && result.success) {
            // Lokal umbenennen
            for (var j = 0; j < SteinerThemesData.length; j++) {
                if (SteinerThemesData[j].theme === oldName) {
                    SteinerThemesData[j].theme = newName;
                    break;
                }
            }
            
            // Keyword-Settings umbenennen
            if (themeKeywordSettings[oldName]) {
                themeKeywordSettings[newName] = themeKeywordSettings[oldName];
                delete themeKeywordSettings[oldName];
            }
            
            // Neu sortieren
            SteinerThemesData.sort(function(a, b) {
                return a.theme.localeCompare(b.theme, 'de');
            });
            
            // Dropdown aktualisieren
            populateThemeSelector();
            selector.value = newName;
            displayThemeKeywords();
            
            // Grafik neu laden
            if (typeof initThematicVisualization === 'function') {
                initThematicVisualization();
            }
            
            renameInput.value = '';
            
            if (statusDiv) {
                statusDiv.style.background = 'var(--success-bg, #d4edda)';
                statusDiv.style.color = 'var(--success-text, #155724)';
                statusDiv.innerHTML = '✓ Umbenannt: <strong>' + oldName + '</strong> → <strong>' + newName + '</strong>';
            }
        } else {
            if (statusDiv) {
                statusDiv.style.background = 'var(--danger-bg, #f8d7da)';
                statusDiv.style.color = 'var(--danger-text, #721c24)';
                statusDiv.innerHTML = '✗ Fehler: ' + (result.error || 'Unbekannter Fehler');
            }
        }
    } catch (error) {
        if (statusDiv) {
            statusDiv.style.background = 'var(--danger-bg, #f8d7da)';
            statusDiv.style.color = 'var(--danger-text, #721c24)';
            statusDiv.innerHTML = '✗ Server nicht erreichbar';
        }
    }
    
    setTimeout(function() {
        if (statusDiv) statusDiv.style.display = 'none';
    }, 5000);
}

// Ausgewählten Themenschwerpunkt löschen
async function deleteSelectedTheme() {
    var selector = document.getElementById('themeKeywordSelector');
    var statusDiv = document.getElementById('renameThemeStatus');
    
    if (!selector) return;
    
    var themeName = selector.value;
    
    if (!themeName) {
        alert('Bitte wählen Sie zuerst einen Themenschwerpunkt aus dem Dropdown oben.');
        return;
    }
    
    // Bestätigung
    if (!confirm('Möchten Sie den Themenschwerpunkt "' + themeName + '" wirklich löschen?\n\nDiese Aktion kann nicht rückgängig gemacht werden.')) {
        return;
    }
    
    // Zeige Lade-Status
    if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.style.cssText = 'margin-top: 0.8rem; padding: 8px 12px; background: var(--info-bg, #d1ecf1); color: var(--info-text, #0c5460); border-radius: 4px; font-size: 0.85rem; text-align: center;';
        statusDiv.innerHTML = '⏳ Lösche...';
    }
    
    try {
        var response = await fetch('/api/delete-theme', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ themeName: themeName })
        });
        
        var result = await response.json();
        
        if (response.ok && result.success) {
            // Lokal löschen
            for (var j = 0; j < SteinerThemesData.length; j++) {
                if (SteinerThemesData[j].theme === themeName) {
                    SteinerThemesData.splice(j, 1);
                    break;
                }
            }
            
            // Keyword-Settings löschen
            if (themeKeywordSettings[themeName]) {
                delete themeKeywordSettings[themeName];
            }
            
            // Dropdown aktualisieren
            populateThemeSelector();
            
            // Chips-Container ausblenden
            var container = document.getElementById('keywordChipsContainer');
            if (container) container.style.display = 'none';
            
            // Grafik neu laden
            if (typeof initThematicVisualization === 'function') {
                initThematicVisualization();
            }
            
            if (statusDiv) {
                statusDiv.style.background = 'var(--success-bg, #d4edda)';
                statusDiv.style.color = 'var(--success-text, #155724)';
                statusDiv.innerHTML = '✓ Themenschwerpunkt <strong>' + themeName + '</strong> gelöscht';
            }
        } else {
            if (statusDiv) {
                statusDiv.style.background = 'var(--danger-bg, #f8d7da)';
                statusDiv.style.color = 'var(--danger-text, #721c24)';
                statusDiv.innerHTML = '✗ Fehler: ' + (result.error || 'Unbekannter Fehler');
            }
        }
    } catch (error) {
        if (statusDiv) {
            statusDiv.style.background = 'var(--danger-bg, #f8d7da)';
            statusDiv.style.color = 'var(--danger-text, #721c24)';
            statusDiv.innerHTML = '✗ Server nicht erreichbar';
        }
    }
    
    setTimeout(function() {
        if (statusDiv) statusDiv.style.display = 'none';
    }, 5000);
}

// Neuen Themenschwerpunkt hinzufügen (Zeitraum wird automatisch ermittelt)
async function addNewTheme() {
    var nameInput = document.getElementById('newThemeName');
    var keywordsInput = document.getElementById('newThemeKeywords');
    var statusDiv = document.getElementById('newThemeStatus');
    
    if (!nameInput || !keywordsInput) {
        alert('Formularfelder nicht gefunden');
        return;
    }
    
    var themeName = nameInput.value.trim();
    var keywords = keywordsInput.value.trim();
    
    if (!themeName) {
        alert('Bitte geben Sie einen Namen für den Themenschwerpunkt ein.');
        return;
    }
    
    if (!keywords) {
        alert('Bitte geben Sie mindestens ein Schlagwort ein.');
        return;
    }
    
    // Prüfe ob Theme bereits existiert
    for (var i = 0; i < SteinerThemesData.length; i++) {
        if (SteinerThemesData[i].theme.toLowerCase() === themeName.toLowerCase()) {
            alert('Ein Themenschwerpunkt mit diesem Namen existiert bereits.');
            return;
        }
    }
    
    // Zeige Lade-Status
    if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.style.cssText = 'margin-top: 0.8rem; padding: 8px 12px; background: var(--info-bg, #d1ecf1); color: var(--info-text, #0c5460); border-radius: 4px; font-size: 0.85rem; text-align: center;';
        statusDiv.innerHTML = '⏳ Analysiere Texte und füge hinzu...';
    }
    
    try {
        var response = await fetch('/api/add-theme', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                themeName: themeName,
                query: keywords
            })
        });
        
        var result = await response.json();
        
        if (response.ok && result.success) {
            // Erfolg - füge lokal hinzu mit ermitteltem Zeitraum
            var newTheme = {
                theme: themeName,
                ranges: [{ start: result.startYear || 1904, end: result.endYear || 1924, intensity: 0.8 }],
                query: keywords
            };
            
            // Alphabetisch einsortieren
            SteinerThemesData.push(newTheme);
            SteinerThemesData.sort(function(a, b) {
                return a.theme.localeCompare(b.theme, 'de');
            });
            
            // Keyword-Settings initialisieren
            var keywordList = splitKeywords(keywords);
            themeKeywordSettings[themeName] = {
                originalKeywords: keywordList.slice(),
                activeKeywords: keywordList.slice(),
                addedKeywords: []
            };
            
            // Dropdown aktualisieren
            populateThemeSelector();
            
            // Grafik neu laden
            if (typeof initThematicVisualization === 'function') {
                initThematicVisualization();
            }
            
            // Formular leeren
            nameInput.value = '';
            keywordsInput.value = '';
            
            if (statusDiv) {
                statusDiv.style.background = 'var(--success-bg, #d4edda)';
                statusDiv.style.color = 'var(--success-text, #155724)';
                statusDiv.innerHTML = '✓ <strong>' + themeName + '</strong> hinzugefügt (Zeitraum: ' + (result.startYear || '?') + '–' + (result.endYear || '?') + ', ' + (result.matchCount || 0) + ' Texte)';
            }
            
            console.log('[THEME2] Neuer Themenschwerpunkt hinzugefügt:', themeName, 'Zeitraum:', result.startYear, '-', result.endYear);
        } else {
            if (statusDiv) {
                statusDiv.style.background = 'var(--danger-bg, #f8d7da)';
                statusDiv.style.color = 'var(--danger-text, #721c24)';
                statusDiv.innerHTML = '✗ Fehler: ' + (result.error || 'Unbekannter Fehler');
            }
        }
    } catch (error) {
        if (statusDiv) {
            statusDiv.style.background = 'var(--danger-bg, #f8d7da)';
            statusDiv.style.color = 'var(--danger-text, #721c24)';
            statusDiv.innerHTML = '✗ Server nicht erreichbar';
        }
        console.error('[THEME2] Fehler beim Hinzufügen:', error);
    }
    
    // Status nach 5 Sekunden ausblenden
    setTimeout(function() {
        if (statusDiv) statusDiv.style.display = 'none';
    }, 5000);
}

// Export functions to global scope for HTML event handlers
window.displayThemeKeywords = displayThemeKeywords;
window.addThemeKeyword = addThemeKeyword;
window.resetThemeKeywords = resetThemeKeywords;
window.saveKeywordChanges = saveKeywordChanges;
window.toggleKeyword = toggleKeyword;
window.selectThemeInDropdown = selectThemeInDropdown;
window.initKeywordSettings = initKeywordSettings;
window.populateThemeSelector = populateThemeSelector;
window.exportKeywordChanges = exportKeywordChanges;
window.addNewTheme = addNewTheme;
window.renameSelectedTheme = renameSelectedTheme;
window.deleteSelectedTheme = deleteSelectedTheme;
window.reassignThemeWithAI = reassignThemeWithAI;
