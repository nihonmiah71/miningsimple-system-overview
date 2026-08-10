let regexAnalysisMatches = [];
let regexUniqueIdCounter = 0;
let cachedQueryString = ""; // Cache for the active search query
let regexStatsSummary = {
    totalUnique: 0,
    foundUnique: 0,
    once: 0,
    rare: 0,
    sometimes: 0,
    frequent: 0,
    veryFrequent: 0
};

// Shared, synchronized positioning system for both add-ons
function alignAllHubs() {
  const ids = [
    'grammar-miner-hub',  // 1. Green
    'grammar-stats-hub',  // 2. Yellow
    'grammar-force-hub',  // 3. Purple (Force Mark)
    'regex-stats-hub',    // 4. Blue
    'regex-winered-hub'   // 5. Wine-Red
  ];
  let currentTop = 20;
  const gap = 10;
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.style.position = 'fixed';
      el.style.right = '20px';
      el.style.left = 'auto';
      if (el.style.width === '20px' || !el.style.width) {
        el.style.top = currentTop + 'px';
        currentTop += 20 + gap;
      } else {
        el.style.top = currentTop + 'px';
        currentTop += 20 + gap;
      }
    }
  });
}

window.addEventListener('resize', alignAllHubs);
window.addEventListener('scroll', alignAllHubs);
setInterval(alignAllHubs, 1000);

const SCALES = {
    BLUE: [
        ["#f0f5ff", "#cbd5e0"], 
        ["#e0ebff", "#a0c4ff"], 
        ["#c2d9ff", "#709dff"], 
        ["#99bcff", "#00215e"], 
        ["#3772ff", "#ffffff"], 
        ["#00215e", "#ffffff"]  
    ],
    GREEN: [
        ["#f2fdf9", "#a8e6cf"], 
        ["#e6f9f1", "#82d1b1"], 
        ["#c8f2e2", "#4cae8a"], 
        ["#a8e6cf", "#1b4d3e"], 
        ["#2d7a5f", "#ffffff"], 
        ["#1b4d3e", "#ffffff"]  
    ],
    RED: [
        ["#fdf0ed", "#f4978e"], 
        ["#fbc4ab", "#f08080"], 
        ["#f8ad9d", "#e63946"], 
        ["#f4978e", "#7a0000"], 
        ["#b30000", "#ffffff"], 
        ["#7a0000", "#ffffff"]  
    ],
    GOLD: [
        ["#fffdf0", "#d4af37"], 
        ["#fff9db", "#b8860b"], 
        ["#fff3b3", "#996515"], 
        ["#ffe066", "#593e10"], 
        ["#ffd700", "#ffffff"], 
        ["#b8860b", "#ffffff"]  
    ]
};

function getPatternStyle(count, scaleName) {
    const idx = Math.min(Math.max(count - 1, 0), 5);
    return SCALES[scaleName][idx];
}

function determineScale(word, isRegexPattern) {
    if (isRegexPattern) return "GOLD";
    if (/^[\u4E00-\u9FAF]+$/.test(word)) return "RED";
    if (/^[\u3040-\u309F\u30A0-\u30FF]+$/.test(word)) return "GREEN";
    return "BLUE";
}

function isDangerousKana(word) {
    if (/[\.\*\+\?\{\}\[\]\^\|\$\\]/.test(word)) return false;
    const onlyKana = /^[\u3040-\u309F\u30A0-\u30FF]+$/;
    return onlyKana.test(word) && word.length < 3;
}

function jumpToNextOccurrence(currentElement, word) {
    const matches = Array.from(document.querySelectorAll(`span[data-mark-word="${word}"]`));
    if (matches.length <= 1) return;
    const index = matches.indexOf(currentElement);
    const next = matches[(index + 1) % matches.length];
    next.scrollIntoView({ behavior: 'smooth', block: 'center' });
    next.style.outline = "2px solid currentColor";
    setTimeout(() => next.style.outline = "none", 600);
}

function runMarking(inputString, onlyKanji, kanjiTolerance = 0) {
    cachedQueryString = inputString; // Synchronize with the Wine-Red panel
    
    let rawEntries = inputString.split(/[@＠]/).map(w => w.trim()).filter(w => w.length > 0);
    
    // Filter terms if onlyKanji option is active
    if (onlyKanji) {
        rawEntries = rawEntries.filter(w => {
            const nonKanjiMatches = w.match(/[^\u4E00-\u9FAF]/g);
            const nonKanjiCount = nonKanjiMatches ? nonKanjiMatches.length : 0;
            const hasKanji = /[\u4E00-\u9FAF]/.test(w);
            // It must contain at least one kanji, and the non-kanji count must not exceed the tolerance
            return hasKanji && nonKanjiCount <= kanjiTolerance;
        });
    }

    rawEntries = rawEntries.filter(w => !isDangerousKana(w));
    if (rawEntries.length === 0) return;

    regexAnalysisMatches = [];

    // Filter unique queries to accurately build the statistics summary
    const uniqueQueryTerms = [...new Set(rawEntries)];

    const compiledPatterns = rawEntries.map(entry => {
        const isRegex = /[\.\*\+\?\{\}\[\]\^\|\$\\]/.test(entry);
        try {
            const finalStr = isRegex ? entry : entry.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            return { 
                original: entry, 
                regex: new RegExp(finalStr, 'g'),
                isRegex: isRegex 
            };
        } catch(e) {
            console.error("Malformed regex skipped: " + entry);
            return null;
        }
    }).filter(p => p !== null);

    const textContent = document.body.innerText;
    const counts = {};
    compiledPatterns.forEach(p => {
        const matches = textContent.match(p.regex);
        counts[p.original] = matches ? matches.length : 0;
    });

    // Calculate dynamic classification statistics for unique search terms
    let uniqueTermsFound = 0;
    let countOnce = 0;
    let countRare = 0;
    let countSometimes = 0;
    let countFrequent = 0;
    let countVeryFrequent = 0;

    uniqueQueryTerms.forEach(term => {
        const hitCount = counts[term] || 0;
        if (hitCount > 0) {
            uniqueTermsFound++;
            if (hitCount === 1) countOnce++;
            else if (hitCount === 2) countRare++;
            else if (hitCount === 3) countSometimes++;
            else if (hitCount === 4 || hitCount === 5) countFrequent++;
            else if (hitCount >= 6) countVeryFrequent++;
        }
    });

    regexStatsSummary = {
        totalUnique: uniqueQueryTerms.length,
        foundUnique: uniqueTermsFound,
        once: countOnce,
        rare: countRare,
        sometimes: countSometimes,
        frequent: countFrequent,
        veryFrequent: countVeryFrequent
    };

    const sortedPatterns = [...compiledPatterns].sort((a, b) => b.original.length - a.original.length);
    if (sortedPatterns.length === 0) return;

    const masterRegexStr = sortedPatterns.map(p => `(?:${p.regex.source})`).join('|');
    const masterRegex = new RegExp(masterRegexStr, 'g');

    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
    let node, nodesToReplace = [];
    while (node = walker.nextNode()) {
        if (node.parentElement.tagName.match(/SCRIPT|STYLE|TEXTAREA|INPUT|NOSCRIPT/)) continue;
        
        masterRegex.lastIndex = 0;
        if (masterRegex.test(node.nodeValue)) {
            nodesToReplace.push(node);
        }
    }

    nodesToReplace.forEach(textNode => {
        const parent = textNode.parentNode;
        if (!parent) return;
        
        masterRegex.lastIndex = 0;
        const wrapper = document.createElement('span');
        const safeText = textNode.nodeValue.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

        wrapper.innerHTML = safeText.replace(masterRegex, (match) => {
            const passendesPattern = sortedPatterns.find(p => {
                const testRegex = new RegExp(p.regex.source);
                return testRegex.test(match);
            }) || sortedPatterns[0];

            const trefferAnzahl = counts[passendesPattern.original] || 1;
            const skala = determineScale(match, passendesPattern.isRegex);
            
            const [originalBg, originalFg] = getPatternStyle(trefferAnzahl, skala);
            const bg = originalBg; 
            const fg = trefferAnzahl <= 4 ? '#000000' : '#ffffff';
            const weight = trefferAnzahl >= 4 ? '700' : '400';

            regexUniqueIdCounter++;
            const uniqueMatchId = `regex-match-${regexUniqueIdCounter}`;

            regexAnalysisMatches.push({
                elementId: uniqueMatchId,
                text: match,
                patternName: passendesPattern.original,
                percentage: "0.00"
            });

            return `<span class="gemini-mark" id="${uniqueMatchId}" data-mark-word="${passendesPattern.original.replace(/"/g, '&quot;')}" style="background-color: ${bg}; color: ${fg}; padding: 1px 3px; border-radius: 2px; cursor: pointer; font-weight: ${weight}; line-height: 1.4;">${match}</span>`;
        });

        wrapper.querySelectorAll('.gemini-mark').forEach(el => {
            el.addEventListener('dblclick', function(e) {
                e.stopPropagation();
                const word = this.getAttribute('data-mark-word');
                jumpToNextOccurrence(this, word);
            });
        });

        while (wrapper.firstChild) parent.insertBefore(wrapper.firstChild, textNode);
        parent.removeChild(textNode);
    });

    const totalMatchesCount = regexAnalysisMatches.length;
    regexAnalysisMatches.forEach((m, idx) => {
        m.percentage = totalMatchesCount > 0 ? ((idx / totalMatchesCount) * 100).toFixed(2) : "0.00";
    });

    // Create / Update the Stats & Maintenance Panels
    setupRegexStatsHub();
    setupWineRedHub();
}

// 4. Blue Box (Regex Analytics Hub)
function setupRegexStatsHub() {
    if (document.getElementById('regex-stats-hub')) {
        alignAllHubs();
        return;
    }

    const hub = document.createElement('div');
    hub.id = 'regex-stats-hub';
    hub.style.position = 'fixed';
    hub.style.width = '20px';
    hub.style.height = '20px';
    hub.style.backgroundColor = '#2980b9'; 
    hub.style.borderRadius = '4px';
    hub.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
    hub.style.zIndex = '9999999c'; 
    hub.style.cursor = 'pointer';
    hub.style.transition = 'width 0.2s, height 0.2s';
    hub.style.display = 'block'; 

    const shadow = hub.attachShadow({ mode: 'open' });
    const style = document.createElement('style');
    style.textContent = `
        .panel-container { display: none; width: 100%; height: 100%; flex-direction: column; background: #dfe6e9; box-sizing: border-box; font-family: sans-serif; color: #2d3436; }
        .panel-header { background: #2980b9; color: white; padding: 6px 10px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
        .tab-bar { display: flex; background: #b2bec3; gap: 2px; padding: 2px 2px 0 2px; }
        .tab-btn { border: none; background: #f8f9fa; padding: 6px 12px; cursor: pointer; font-weight: bold; font-size: 12px; border-radius: 4px 4px 0 0; }
        .tab-btn.active { background: white; color: #2980b9; }
        .table-wrapper { flex: 1; overflow: auto; padding: 6px; background: white; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th { background: #f1f2f6; border: 1px solid #ced6e0; padding: 6px; text-align: left; position: sticky; top: 0; }
        td { border: 1px solid #ced6e0; padding: 6px; white-space: pre-wrap; word-break: break-all; }
        .jump-link { color: #2980b9; text-decoration: underline; cursor: pointer; font-weight: bold; }
        .jump-link:hover { color: #1c5980; }
        .close-panel-btn { background: none; border: none; color: white; font-size: 16px; cursor: pointer; }
        .summary-card { background: #f1f2f6; padding: 10px; border-radius: 6px; margin-bottom: 10px; border: 1px solid #ced6e0; font-size: 13px; }
        .summary-title { font-weight: bold; color: #2980b9; margin-bottom: 6px; }
        .summary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }
    `;
    shadow.appendChild(style);

    const container = document.createElement('div');
    container.className = 'panel-container';
    container.id = 'regex-stats-panel';
    container.innerHTML = `
        <div class="panel-header">
          <span>Regex Finder Analysis & Navigation</span>
          <button class="close-panel-btn">✕</button>
        </div>
        <div class="tab-bar">
          <button class="tab-btn active" id="btn-regex-tab-freq">Frequency</button>
          <button class="tab-btn" id="btn-regex-tab-chrono">Chronological</button>
          <button class="tab-btn" id="btn-regex-tab-sorted">Sorted</button>
        </div>
        <div class="table-wrapper" id="regex-table-container">
          <div id="regex-summary-wrapper"></div>
          <table id="regex-stats-table">
            <thead id="regex-stats-thead"></thead>
            <tbody id="regex-stats-tbody"></tbody>
          </table>
        </div>
    `;
    shadow.appendChild(container);
    document.body.appendChild(hub);

    let currentTab = "freq";

    hub.addEventListener('click', (e) => {
        if (hub.style.width === '20px') {
            e.stopPropagation();
            hub.style.width = '550px';
            hub.style.height = '420px';
            hub.style.cursor = 'default';
            hub.style.resize = 'both';
            hub.style.overflow = 'hidden';
            container.style.display = 'flex';
            renderRegexStatsTable(shadow, currentTab);
        }
    });

    shadow.querySelector('.close-panel-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        hub.style.width = '20px';
        hub.style.height = '20px';
        hub.style.cursor = 'pointer';
        hub.style.resize = 'none';
        hub.style.overflow = 'hidden';
        container.style.display = 'none';
        alignAllHubs();
    });

    shadow.querySelector('#btn-regex-tab-freq').addEventListener('click', (e) => {
        e.stopPropagation(); currentTab = "freq";
        setRegexActiveTabStyle(shadow, '#btn-regex-tab-freq');
        renderRegexStatsTable(shadow, currentTab);
    });

    shadow.querySelector('#btn-regex-tab-chrono').addEventListener('click', (e) => {
        e.stopPropagation(); currentTab = "chrono";
        setRegexActiveTabStyle(shadow, '#btn-regex-tab-chrono');
        renderRegexStatsTable(shadow, currentTab);
    });

    shadow.querySelector('#btn-regex-tab-sorted').addEventListener('click', (e) => {
        e.stopPropagation(); currentTab = "sorted";
        setRegexActiveTabStyle(shadow, '#btn-regex-tab-sorted');
        renderRegexStatsTable(shadow, currentTab);
    });

    alignAllHubs();
}

function setRegexActiveTabStyle(shadow, activeId) {
    shadow.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    shadow.querySelector(activeId).classList.add('active');
}

function renderRegexStatsTable(shadow, tab) {
    const thead = shadow.getElementById('regex-stats-thead');
    const tbody = shadow.getElementById('regex-stats-tbody');
    const summaryWrapper = shadow.getElementById('regex-summary-wrapper');
    
    thead.innerHTML = '';
    tbody.innerHTML = '';
    summaryWrapper.innerHTML = '';

    // Render the statistics block at the top of the Frequency tab
    if (tab === "freq") {
        summaryWrapper.innerHTML = `
          <div class="summary-card">
            <div class="summary-title">Search Term Summary:</div>
            <div class="summary-grid">
              <div>Unique terms found: <b>${regexStatsSummary.foundUnique}/${regexStatsSummary.totalUnique} unique</b></div>
              <div>Once (1 hit): <b>${regexStatsSummary.once}/once</b></div>
              <div>Rare (2 hits): <b>${regexStatsSummary.rare}/rare</b></div>
              <div>Sometimes (3 hits): <b>${regexStatsSummary.sometimes}/sometimes</b></div>
              <div>Frequent (4-5 hits): <b>${regexStatsSummary.frequent}/frequent</b></div>
              <div>Very Frequent (6+ hits): <b>${regexStatsSummary.veryFrequent}/very frequent</b></div>
            </div>
          </div>
        `;

        thead.innerHTML = `
          <tr>
            <th style="width: 70%;">Search Word / Pattern</th>
            <th style="width: 30%;">Hit Count</th>
          </tr>
        `;
        
        const counts = {};
        regexAnalysisMatches.forEach(m => {
            counts[m.patternName] = (counts[m.patternName] || 0) + 1;
        });

        const sortedFreq = Object.entries(counts).sort((a, b) => b[1] - a[1]);

        if (sortedFreq.length === 0) {
            tbody.innerHTML = `<tr><td colspan="2" style="text-align:center; color:#7f8c8d;">No hits analyzed.</td></tr>`;
            return;
        }

        let statsHtml = "";
        sortedFreq.forEach(([name, count]) => {
            statsHtml += `<tr><td>${name}</td><td><b>${count}x</b></td></tr>`;
        });
        tbody.innerHTML = statsHtml;

    } else if (tab === "chrono") {
        thead.innerHTML = `
          <tr>
            <th style="width: 30%;">Match (Anchor)</th>
            <th style="width: 50%;">Pattern / Word</th>
            <th style="width: 20%;">Position</th>
          </tr>
        `;

        if (regexAnalysisMatches.length === 0) {
            tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; color:#7f8c8d;">No matches available.</td></tr>`;
            return;
        }

        let statsHtml = "";
        regexAnalysisMatches.forEach(m => {
            statsHtml += `
            <tr>
              <td><span class="jump-link" data-target="${m.elementId}">${m.text}</span></td>
              <td>${m.patternName}</td>
              <td>${m.percentage}%</td>
            </tr>
          `;
        });
        tbody.innerHTML = statsHtml;
        attachRegexJumpLinks(tbody);

    } else if (tab === "sorted") {
        thead.innerHTML = `
          <tr>
            <th style="width: 40%;">Match (Anchor)</th>
            <th style="width: 60%;">Position in Text</th>
          </tr>
        `;

        const counts = {};
        regexAnalysisMatches.forEach(m => {
            counts[m.patternName] = (counts[m.patternName] || 0) + 1;
        });
        const sortedPatternNames = Object.entries(counts)
            .sort((a, b) => b[1] - a[1])
            .map(entry => entry[0]);

        if (sortedPatternNames.length === 0) {
            tbody.innerHTML = `<tr><td colspan="2" style="text-align:center; color:#7f8c8d;">No matches available.</td></tr>`;
            return;
        }

        let statsHtml = "";
        sortedPatternNames.forEach(pName => {
            statsHtml += `<tr><td colspan="2" style="background: #2980b9; color: white; font-weight: bold; padding: 4px 8px;">${pName} (${counts[pName]}x)</td></tr>`;
            const groupMatches = regexAnalysisMatches.filter(m => m.patternName === pName);
          
            groupMatches.forEach(m => {
                statsHtml += `
              <tr>
                <td><span class="jump-link" data-target="${m.elementId}">${m.text}</span></td>
                <td>${m.percentage}%</td>
              </tr>
            `;
            });
        });
        tbody.innerHTML = statsHtml;
        attachRegexJumpLinks(tbody);
    }
}

function attachRegexJumpLinks(tbody) {
    tbody.querySelectorAll('.jump-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.stopPropagation();
            const targetId = link.getAttribute('data-target');
            const targetEl = document.getElementById(targetId);
            if (targetEl) {
                targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                const originalBg = targetEl.style.backgroundColor;
                targetEl.style.backgroundColor = '#9b59b6';
                targetEl.style.color = '#ffffff';
                setTimeout(() => {
                    targetEl.style.backgroundColor = originalBg;
                    targetEl.style.color = "";
                }, 1000);
            }
        });
    });
}

// 5. Wine-Red Box (Query List Deleter)
function setupWineRedHub() {
  if (document.getElementById('regex-winered-hub')) {
    alignAllHubs();
    return;
  }

  const hub = document.createElement('div');
  hub.id = 'regex-winered-hub';
  hub.style.position = 'fixed';
  hub.style.width = '20px';
  hub.style.height = '20px';
  hub.style.backgroundColor = '#800020'; // Wine-Red
  hub.style.borderRadius = '4px';
  hub.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
  hub.style.zIndex = '9999999e';
  hub.style.cursor = 'pointer';
  hub.style.transition = 'width 0.2s, height 0.2s';
  hub.style.display = 'block';

  const shadow = hub.attachShadow({ mode: 'open' });
  const style = document.createElement('style');
  style.textContent = `
    .panel-container { display: none; width: 100%; height: 100%; flex-direction: column; background: #dfe6e9; box-sizing: border-box; font-family: sans-serif; color: #2d3436; }
    .panel-header { background: #800020; color: white; padding: 6px 10px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
    .body-wrapper { flex: 1; padding: 10px; background: white; display: flex; flex-direction: column; gap: 8px; }
    textarea { width: 100%; height: 200px; font-family: monospace; font-size: 12px; padding: 8px; box-sizing: border-box; resize: none; border: 1px solid #ced6e0; border-radius: 4px; }
    .footer-actions { padding: 6px; background: #f1f2f6; display: flex; gap: 8px; align-items: center; border-top: 1px solid #ced6e0; }
    .footer-actions input { flex: 1; padding: 6px; font-size: 12px; border: 1px solid #ced6e0; border-radius: 4px; }
    .action-btn { background: #800020; color: white; border: none; padding: 6px 12px; font-weight: bold; border-radius: 4px; cursor: pointer; font-size: 12px; white-space: nowrap; }
    .action-btn:hover { background: #600018; }
    .close-panel-btn { background: none; border: none; color: white; font-size: 16px; cursor: pointer; }
  `;
  shadow.appendChild(style);

  const container = document.createElement('div');
  container.className = 'panel-container';
  container.id = 'winered-panel';
  container.innerHTML = `
    <div class="panel-header">
      <span>Query List Deleter</span>
      <button class="close-panel-btn">✕</button>
    </div>
    <div class="body-wrapper">
      <textarea id="winered-display" readonly placeholder="No active marking list yet. Please run Mark first."></textarea>
      <button class="action-btn" id="btn-copy-winered" style="align-self: flex-end;">Copy Text</button>
    </div>
    <div class="footer-actions">
      <input type="text" id="winered-delete-input" placeholder="Strings to delete (comma-separated)...">
      <button class="action-btn" id="btn-winered-delete">Delete</button>
    </div>
  `;
  shadow.appendChild(container);
  document.body.appendChild(hub);

  const displayArea = container.querySelector('#winered-display');
  const deleteInput = container.querySelector('#winered-delete-input');

  hub.addEventListener('click', (e) => {
    if (hub.style.width === '20px') {
      e.stopPropagation();
      hub.style.width = '550px';
      hub.style.height = '380px';
      hub.style.cursor = 'default';
      hub.style.resize = 'both';
      hub.style.overflow = 'hidden';
      container.style.display = 'flex';
      
      displayArea.value = cachedQueryString;
    }
  });

  shadow.querySelector('.close-panel-btn').addEventListener('click', (e) => {
    e.stopPropagation();
    hub.style.width = '20px';
    hub.style.height = '20px';
    hub.style.cursor = 'pointer';
    hub.style.resize = 'none';
    hub.style.overflow = 'hidden';
    container.style.display = 'none';
    alignAllHubs();
  });

  container.querySelector('#btn-copy-winered').addEventListener('click', () => {
    displayArea.select();
    navigator.clipboard.writeText(displayArea.value);
    alert("Copied to clipboard!");
  });

  container.querySelector('#btn-winered-delete').addEventListener('click', () => {
    const delVal = deleteInput.value.trim();
    if (!delVal) return;

    // Splits input by commas and filters out empty values
    const stringsToDel = delVal.split(',').map(s => s.trim()).filter(s => s.length > 0);
    let entries = cachedQueryString.split(/[@＠]/).map(s => s.trim()).filter(s => s.length > 0);
    entries = entries.filter(entry => !stringsToDel.includes(entry));

    cachedQueryString = entries.join('@');
    displayArea.value = cachedQueryString;
    deleteInput.value = "";
  });

  alignAllHubs();
}

chrome.runtime.onMessage.addListener((request) => {
    if (request.action === "mark") {
        const tolerance = typeof request.kanjiTolerance !== 'undefined' ? parseInt(request.kanjiTolerance, 10) : 0;
        runMarking(request.query, request.onlyKanji, tolerance);
    }
});