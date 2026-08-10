console.log("[Grammar Addon] Serverless analysis script is ready.");

let minedItems = [];
let analysisMatches = [];
let uniqueIdCounter = 0;
let cachedGrammarData = null;

// Status tracking for the exports of both table views
let exportedTabs = {
  single: false,
  update: false
};

// ==========================================
// CACHING SYSTEM (GREEN BOX)
// ==========================================
chrome.storage.local.get(['cachedMinedItems'], (result) => {
  if (result.cachedMinedItems && Array.isArray(result.cachedMinedItems)) {
    minedItems = result.cachedMinedItems;
    updateFloatingHubState();
  }
});

function saveMinedItems() {
  chrome.storage.local.set({ cachedMinedItems: minedItems });
}

// Helper function to reset the export status for new entries
function resetExportStatus() {
  exportedTabs.single = false;
  exportedTabs.update = false;
}

// ==========================================
// AUDIO MANAGER (GAMIFICATION SYSTEM)
// ==========================================
const AudioManager = {
  enabled: true,
  countLookups: true,
  comboCount: 0,
  comboTimer: null,
  comboTimeoutMs: 90000, 
  warnTimer: null, 
  lookupCount: 0, 

  init: async function() {
    const storage = await chrome.storage.local.get(['gamifySounds', 'countLookups']);
    this.enabled = storage.gamifySounds !== false;
    this.countLookups = storage.countLookups !== false;

    chrome.storage.onChanged.addListener((changes, areaName) => {
      if (areaName === 'local') {
        if (changes.gamifySounds) {
          this.enabled = changes.gamifySounds.newValue !== false;
        }
        if (changes.countLookups) {
          this.countLookups = changes.countLookups.newValue !== false;
        }
      }
    });
  },

  play: function(soundName) {
    if (!this.enabled) return;
    const url = chrome.runtime.getURL(`sounds/${soundName}.mp3`);
    const audio = new Audio(url);
    audio.volume = 0.6;
    audio.play().catch(err => console.log("Audio blocked by browser:", err));
  },

  playLookup: function() {
    clearTimeout(this.comboTimer);
    clearTimeout(this.warnTimer);

    this.comboCount++;
    
    if (this.comboCount % 10 === 0) {
      const baseSounds2 = ['square-removed1', 'square-removed2', 'frosting-cleared1', 'frosting-cleared2', 'colour-bomb-created', 'wrapped-candy-created1', 'swoosh-ut', 'liqourice-lock-broken'];
      let pool1 = [...baseSounds2];
      const pick2 = pool1[Math.floor(Math.random() * pool1.length)];
      this.play(pick2);
    } else {
      const baseSounds3 = ['square-removed1', 'square-removed2', 'frosting-cleared1', 'frosting-cleared2', 'colour-bomb-created', 'wrapped-candy-created1', 'swoosh-ut', 'liqourice-lock-broken'];
      let pool2 = [...baseSounds3];
      const pick3 = pool2[Math.floor(Math.random() * pool2.length)];
      this.play(pick3);
    }
    
    const currentCombo = Math.min(this.comboCount, 12);
    setTimeout(() => {
      this.play(`combo-sound${currentCombo}`);
    }, 300);

    this.warnTimer = setTimeout(() => {
      if (this.comboCount > 0) {
        this.play('chocolate-grows');
      }
    }, 75000);

    this.comboTimer = setTimeout(() => {
      this.comboCount = 0;
    }, this.comboTimeoutMs);
  },

  playLShift: function() {
    this.playLookup();
  },

  playForceLookup: function() {
    this.play('liqourice-lock-broken');
  },

  playClosePopup: function() {
    this.lookupCount++;
    const cycleIndex = ((this.lookupCount - 1) % 30) + 1;
    
    const baseSounds = ['square-removed1', 'square-removed2', 'frosting-cleared1', 'frosting-cleared2', 'colour-bomb-created', 'wrapped-candy-created1', 'swoosh-ut', 'liqourice-lock-broken'];
    let pool = [...baseSounds];

    if (cycleIndex <= 10) {
      pool.push('sweet');
    } else if (cycleIndex <= 20) {
      pool.push('sweet');
      pool.push('delicious');
    } else {
      pool.push('delicious');
      pool.push('divine');
    }

    const pick = pool[Math.floor(Math.random() * pool.length)];
    this.play(pick);
  },

  playAddAnki: function() {
    this.lookupCount++;
    const cycleIndex = ((this.lookupCount - 1) % 30) + 1;
    
    const baseSounds = ['square-removed1', 'square-removed2', 'frosting-cleared1', 'frosting-cleared2', 'colour-bomb-created', 'wrapped-candy-created1', 'swoosh-ut', 'liqourice-lock-broken'];
    let pool = [...baseSounds];

    if (cycleIndex <= 10) {
      pool.push('sweet');
    } else if (cycleIndex <= 20) {
      pool.push('sweet');
      pool.push('delicious');
    } else {
      pool.push('delicious');
      pool.push('divine');
    }

    const pick = pool[Math.floor(Math.random() * pool.length)];
    this.play(pick);
  },

  playExport: function() {
    this.play('sugar-crush');
  }
};

// ==========================================
// INCREMENT COUNTER PERSISTENCE
// ==========================================
async function incrementLookups() {
  if (!AudioManager.countLookups) return;
  chrome.storage.local.get(['allTimeLookups', 'sessionLookups'], (result) => {
    const allTime = (result.allTimeLookups || 0) + 1;
    const session = (result.sessionLookups || 0) + 1;
    chrome.storage.local.set({
      allTimeLookups: allTime,
      sessionLookups: session
    });
  });
}

document.addEventListener('keydown', function(event) {
  if (event.code === 'ShiftLeft') {
    if (event.repeat) return; 
    
    AudioManager.playLShift();
    incrementLookups();
  }
});

AudioManager.init();

async function getGrammarData() {
  if (cachedGrammarData) return cachedGrammarData;
  try {
    const grammarUrl = chrome.runtime.getURL('data/grammar_data.json');
    const response = await fetch(grammarUrl);
    cachedGrammarData = await response.json();
    return cachedGrammarData;
  } catch (e) {
    console.error("Failed to load grammar data", e);
    return {};
  }
}

function alignAllHubs() {
  const ids = [
    'grammar-miner-hub',  
    'grammar-stats-hub',  
    'grammar-force-hub',  
    'regex-stats-hub',    
    'regex-winered-hub'   
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

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "analyzeSelection") {
    console.log("[Grammar Addon] Starting analysis...");
    processPage(); 
  }
});

function getAllTextNodes(container, targetRange = null) {
  const textNodes = [];
  const walk = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
    acceptNode: function(node) {
      const parent = node.parentNode;
      if (!parent) return NodeFilter.FILTER_REJECT;
      
      const tagName = parent.tagName.toUpperCase();
      if (['SCRIPT', 'STYLE', 'TEXTAREA', 'INPUT', 'NOSCRIPT'].includes(tagName)) {
        return NodeFilter.FILTER_REJECT;
      }
      
      if (parent.classList.contains('grammar-match-highlight') || parent.closest('.grammar-match-highlight')) {
        return NodeFilter.FILTER_REJECT;
      }
      
      if (targetRange && !targetRange.intersectsNode(node)) {
        return NodeFilter.FILTER_REJECT;
      }
      
      return NodeFilter.FILTER_ACCEPT;
    }
  });

  while (walk.nextNode()) {
    textNodes.push(walk.currentNode);
  }
  return textNodes;
}

function extractSentenceContext(span) {
  const container = span.closest('p, div, li, td, section, article') || span.parentNode;
  let textBefore = "";
  let textAfter = "";
  let foundTarget = false;

  const walk = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
  let currentNode;
  
  while (currentNode = walk.nextNode()) {
    if (currentNode.parentNode === span || span.contains(currentNode)) {
      foundTarget = true;
      continue;
    }
    if (!foundTarget) {
      textBefore += currentNode.nodeValue;
    } else {
      textAfter += currentNode.nodeValue;
    }
  }

  const cleanBefore = textBefore.replace(/\s+/g, ' ');
  const cleanAfter = textAfter.replace(/\s+/g, ' ');
  const targetWord = span.textContent.trim();

  return `${cleanBefore}<b>${targetWord}</b>${cleanAfter}`.trim();
}

async function processPage() {
  try {
    const patternsUrl = chrome.runtime.getURL('data/patterns_data.json');
    const grammarUrl = chrome.runtime.getURL('data/grammar_data.json');

    const [patternsRes, grammarRes, storage] = await Promise.all([
      fetch(patternsUrl),
      fetch(grammarUrl),
      chrome.storage.local.get(['selectedNids'])
    ]);

    const sortedPatterns = await patternsRes.json();
    const grammarData = await grammarRes.json();
    cachedGrammarData = grammarData; 
    const selectedNids = storage.selectedNids || [];

    const selection = window.getSelection();
    let targetRange = null;
    if (selection && selection.rangeCount > 0 && selection.toString().trim().length > 0) {
      targetRange = selection.getRangeAt(0).cloneRange();
    }

    const textNodes = getAllTextNodes(document.body, targetRange);
    
    let totalTextLength = 0;
    const nodeEntries = textNodes.map(node => {
      const startOffsetInTotal = totalTextLength;
      totalTextLength += node.nodeValue.length;
      return {
        node: node,
        text: node.nodeValue,
        startOffsetInTotal: startOffsetInTotal,
        matches: []
      };
    });

    function isOverlapping(start, end, existingMatches) {
      for (const m of existingMatches) {
        if (start < m.end && end > m.start) return true;
      }
      return false;
    }

    for (const pObj of sortedPatterns) {
      const hasActiveNid = pObj.nids.some(nid => selectedNids.includes(String(nid)));
      if (!hasActiveNid) continue;

      let regex;
      try {
        regex = new RegExp(pObj.pattern, 'g');
      } catch (e) {
        continue;
      }

      const nidsString = pObj.nids.join(',');

      for (const entry of nodeEntries) {
        let match;
        regex.lastIndex = 0;
        if (!regex.test(entry.text)) continue;
        regex.lastIndex = 0;

        while ((match = regex.exec(entry.text)) !== null) {
          const start = match.index;
          const end = regex.lastIndex;
          if (!isOverlapping(start, end, entry.matches)) {
            entry.matches.push({ start, end, text: match[0], nidsString });
          }
          if (match[0].length === 0) regex.lastIndex++;
        }
      }
    }

    let localNewMatchesCount = 0;

    for (const entry of nodeEntries) {
      if (entry.matches.length === 0) continue;
      entry.matches.sort((a, b) => a.start - b.start);

      const fragment = document.createDocumentFragment();
      let lastIdx = 0;

      for (const m of entry.matches) {
        if (m.start > lastIdx) {
          fragment.appendChild(document.createTextNode(entry.text.substring(lastIdx, m.start)));
        }

        uniqueIdCounter++;
        const uniqueMatchId = `grammar-match-${uniqueIdCounter}`;

        const span = document.createElement('span');
        span.id = uniqueMatchId;
        span.className = 'grammar-match-highlight';
        span.setAttribute('data-nids', m.nidsString);
        span.textContent = m.text;

        span.style.backgroundColor = '#ffeaa7';
        span.style.color = '#2d3436';
        span.style.padding = '2px 4px';
        span.style.borderRadius = '4px';
        span.style.cursor = 'pointer';
        span.style.fontWeight = '500';
        span.style.transition = 'background-color 0.2s';

        span.addEventListener('mouseenter', () => span.style.backgroundColor = '#fdcb6e');
        span.addEventListener('mouseleave', () => span.style.backgroundColor = '#ffeaa7');

        fragment.appendChild(span);

        const absoluteCharPos = entry.startOffsetInTotal + m.start;
        const relativePercentage = totalTextLength > 0 ? ((absoluteCharPos / totalTextLength) * 100).toFixed(2) : "0.00";

        const firstNid = m.nidsString.split(',')[0];
        const gInfo = grammarData[firstNid];
        const grammarName = gInfo ? (gInfo.level_and_point || gInfo.Level_And_Grammar_Point || 'Unknown') : 'Unknown';

        analysisMatches.push({
          elementId: uniqueMatchId,
          text: m.text,
          grammarName: grammarName,
          percentage: relativePercentage,
          absolutePos: absoluteCharPos
        });

        lastIdx = m.end;
        localNewMatchesCount++;
      }

      if (lastIdx < entry.text.length) {
        fragment.appendChild(document.createTextNode(entry.text.substring(lastIdx)));
      }

      const parent = entry.node.parentNode;
      if (parent) {
        parent.insertBefore(fragment, entry.node);
        parent.removeChild(entry.node);
      }
    }

    analysisMatches.sort((a, b) => a.absolutePos - b.absolutePos);

    attachPopupEvents(grammarData);

    if (!document.getElementById('grammar-miner-hub')) {
      setupFloatingHub();
    } else {
      updateFloatingHubState();
    }

    if (!document.getElementById('grammar-stats-hub')) {
      setupStatsHub();
    } else {
      alignAllHubs();
    }

    setupForceHub();

  } catch (error) {
    console.error("[Grammar Addon] Critical error during analysis:", error);
  }
}

function attachPopupEvents(grammarData) {
  document.querySelectorAll('.grammar-match-highlight:not(.has-popup-event)').forEach(span => {
    span.classList.add('has-popup-event');
    span.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      AudioManager.playLookup(); 
      const nids = span.getAttribute('data-nids').split(',');
      showModalPopup(nids, grammarData, span);
    });
  });
}

// 1. Green Box (Mining Hub)
function setupFloatingHub() {
  if (document.getElementById('grammar-miner-hub')) return;

  const hub = document.createElement('div');
  hub.id = 'grammar-miner-hub';
  hub.style.position = 'fixed';
  hub.style.width = '20px';
  hub.style.height = '20px';
  hub.style.backgroundColor = '#27ae60';
  hub.style.borderRadius = '4px';
  hub.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
  hub.style.zIndex = '9999999a';
  hub.style.cursor = 'pointer';
  hub.style.transition = 'width 0.2s, height 0.2s';
  hub.style.display = 'block';

  const shadow = hub.attachShadow({ mode: 'open' });
  const style = document.createElement('style');
  style.textContent = `
    .badge { position: absolute; top: -8px; left: -8px; background: #e74c3c; color: white; font-size: 10px; font-weight: bold; border-radius: 50%; padding: 2px 5px; min-width: 10px; text-align: center; }
    .panel-container { display: none; width: 100%; height: 100%; flex-direction: column; background: #dfe6e9; box-sizing: border-box; font-family: sans-serif; color: #2d3436; }
    .panel-header { background: #27ae60; color: white; padding: 6px 10px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
    .tab-bar { display: flex; background: #b2bec3; gap: 2px; padding: 2px 2px 0 2px; }
    .tab-btn { border: none; background: #f8f9fa; padding: 6px 12px; cursor: pointer; font-weight: bold; font-size: 12px; border-radius: 4px 4px 0 0; }
    .tab-btn.active { background: white; color: #27ae60; }
    .table-wrapper { flex: 1; overflow: auto; padding: 6px; background: white; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th { background: #f1f2f6; border: 1px solid #ced6e0; padding: 6px; text-align: left; position: sticky; top: 0; }
    td { border: 1px solid #ced6e0; padding: 6px; white-space: pre-wrap; word-break: break-all; }
    .footer-actions { padding: 6px; background: #f1f2f6; display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid #ced6e0; }
    .action-btn { background: #27ae60; color: white; border: none; padding: 5px 12px; font-weight: bold; border-radius: 4px; cursor: pointer; font-size: 12px; }
    .action-btn.danger-btn { background: #e74c3c; }
    .action-btn.danger-btn:hover { background: #c0392b; }
    .delete-btn { background: #e74c3c; color: white; border: none; padding: 2px 6px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 11px; }
    .delete-btn:hover { background: #c0392b; }
    .close-panel-btn { background: none; border: none; color: white; font-size: 16px; cursor: pointer; }
  `;
  shadow.appendChild(style);

  const badge = document.createElement('div');
  badge.className = 'badge';
  badge.id = 'miner-badge';
  badge.textContent = minedItems.length;
  shadow.appendChild(badge);

  const container = document.createElement('div');
  container.className = 'panel-container';
  container.id = 'miner-panel';
  container.innerHTML = `
    <div class="panel-header">
      <span>Anki Mining Hub</span>
      <button class="close-panel-btn">✕</button>
    </div>
    <div class="tab-bar">
      <button class="tab-btn active" id="btn-tab-single">Individual Cards</button>
      <button class="tab-btn" id="btn-tab-update">Grammar Updates</button>
    </div>
    <div class="table-wrapper">
      <table id="miner-table">
        <thead id="miner-thead"></thead>
        <tbody id="miner-tbody"></tbody>
      </table>
    </div>
    <div class="footer-actions">
      <button class="action-btn danger-btn" id="btn-clear-all">Clear All</button>
      <button class="action-btn" id="btn-export">Export TSV</button>
    </div>
  `;
  shadow.appendChild(container);
  document.body.appendChild(hub);

  let currentTab = "single";

  hub.addEventListener('click', (e) => {
    if (hub.style.width === '20px') {
      e.stopPropagation();
      hub.style.width = '700px';
      hub.style.height = '420px';
      hub.style.cursor = 'default';
      hub.style.resize = 'both';
      hub.style.overflow = 'hidden';
      badge.style.display = 'none';
      container.style.display = 'flex';
      renderMinerTable(shadow, currentTab);
    }
  });

  shadow.querySelector('.close-panel-btn').addEventListener('click', (e) => {
    e.stopPropagation();
    hub.style.width = '20px';
    hub.style.height = '20px';
    hub.style.cursor = 'pointer';
    hub.style.resize = 'none';
    hub.style.overflow = 'hidden';
    badge.style.display = 'block';
    container.style.display = 'none';
    alignAllHubs();
  });

  shadow.querySelector('#btn-tab-single').addEventListener('click', () => {
    currentTab = "single";
    shadow.querySelector('#btn-tab-single').classList.add('active');
    shadow.querySelector('#btn-tab-update').classList.remove('active');
    renderMinerTable(shadow, currentTab);
  });

  shadow.querySelector('#btn-tab-update').addEventListener('click', () => {
    currentTab = "update";
    shadow.querySelector('#btn-tab-update').classList.add('active');
    shadow.querySelector('#btn-tab-single').classList.remove('active');
    renderMinerTable(shadow, currentTab);
  });

  shadow.querySelector('#btn-clear-all').addEventListener('click', () => {
    if (confirm("Are you sure you want to clear both tables completely? This cannot be undone.")) {
      minedItems = [];
      resetExportStatus();
      saveMinedItems(); 
      updateFloatingHubState();
      renderMinerTable(shadow, currentTab);
    }
  });

  shadow.querySelector('#btn-export').addEventListener('click', () => {
    AudioManager.playExport(); 
    triggerTSVExport(shadow, currentTab);
    
    // Set status flag for the current tab
    if (currentTab === "single") {
      exportedTabs.single = true;
    } else if (currentTab === "update") {
      exportedTabs.update = true;
    }

    // The array is only cleared once both views have been exported
    if (exportedTabs.single && exportedTabs.update) {
      minedItems = [];
      resetExportStatus();
      saveMinedItems();
      updateFloatingHubState();
    }
    
    renderMinerTable(shadow, currentTab);
  });

  const tbody = shadow.getElementById('miner-tbody');
  tbody.addEventListener('focusout', (e) => {
    const target = e.target;
    if (target.hasAttribute('data-field')) {
      const field = target.getAttribute('data-field');
      const val = target.innerText.trim();
      const tr = target.closest('tr');

      if (currentTab === "single") {
        const index = parseInt(tr.getAttribute('data-index'), 10);
        if (minedItems[index]) {
          minedItems[index][field] = val;
          resetExportStatus();
          saveMinedItems(); 
        }
      } else if (currentTab === "update") {
        const oldNid = tr.getAttribute('data-nid');
        if (field === "nid") {
          minedItems.forEach(item => {
            if (String(item.nid) === String(oldNid)) {
              item.nid = val;
            }
          });
          tr.setAttribute('data-nid', val);
          resetExportStatus();
          saveMinedItems(); 
        } else if (field === "sentences") {
          const lines = target.innerText.split('\n');
          lines.forEach(line => {
            const match = line.match(/(.*)\s+\[([^\]]+)\]$/);
            if (match) {
              const newSentence = match[1].trim();
              const nidindiv = match[2].trim();
              const item = minedItems.find(i => i.nidindiv === nidindiv);
              if (item) {
                item.sentence = newSentence;
              }
            }
          });
          resetExportStatus();
          saveMinedItems(); 
        }
      }
    }
  });

  tbody.addEventListener('click', (e) => {
    if (e.target.classList.contains('delete-btn')) {
      e.stopPropagation();
      if (currentTab === "single") {
        const index = parseInt(e.target.getAttribute('data-index'), 10);
        minedItems.splice(index, 1);
        resetExportStatus();
        saveMinedItems(); 
        updateFloatingHubState();
        renderMinerTable(shadow, "single");
      } else if (currentTab === "update") {
        const nid = e.target.getAttribute('data-nid');
        minedItems = minedItems.filter(item => String(item.nid) !== String(nid));
        resetExportStatus();
        saveMinedItems(); 
        updateFloatingHubState();
        renderMinerTable(shadow, "update");
      }
    }
  });

  alignAllHubs();
}

function updateFloatingHubState() {
  const hub = document.getElementById('grammar-miner-hub');
  if (!hub) return;
  const badge = hub.shadowRoot.getElementById('miner-badge');
  if (badge) badge.textContent = minedItems.length;
  alignAllHubs();
}

function renderMinerTable(shadow, tab) {
  const thead = shadow.getElementById('miner-thead');
  const tbody = shadow.getElementById('miner-tbody');
  thead.innerHTML = '';
  tbody.innerHTML = '';

  if (tab === "single") {
    thead.innerHTML = `
      <tr>
        <th>Note ID</th>
        <th>Word</th>
        <th>SentencePlain</th>
        <th>English Definition Overview</th>
        <th>Frequency</th>
        <th>Correct Japanese Definition</th>
        <th>Actions</th>
      </tr>
    `;
    let tableHtml = "";
    minedItems.forEach((item, index) => {
      tableHtml += `
        <tr data-index="${index}">
          <td contenteditable="true" data-field="nidindiv">${item.nidindiv}</td>
          <td contenteditable="true" data-field="match">${item.match}</td>
          <td contenteditable="true" data-field="sentence">${item.sentence}</td>
          <td contenteditable="true" data-field="level_and_point">${item.level_and_point}</td>
          <td contenteditable="true" data-field="construction">${item.construction}</td>
          <td contenteditable="true" data-field="regexpattern">${item.regexpattern}</td>
          <td><button class="delete-btn" data-index="${index}">Delete</button></td>
        </tr>
      `;
    });
    tbody.innerHTML = tableHtml;
  } else {
    thead.innerHTML = `
      <tr>
        <th style="width: 20%;">NID</th>
        <th style="width: 65%;">Collected Sentences (with ID)</th>
        <th style="width: 15%;">Actions</th>
      </tr>
    `;
    const grouped = {};
    minedItems.forEach(item => {
      if (!grouped[item.nid]) grouped[item.nid] = [];
      grouped[item.nid].push(`${item.sentence} [${item.nidindiv}]`);
    });

    let tableHtml = "";
    Object.keys(grouped).forEach(nid => {
      const combinedSentences = grouped[nid].join('\n');
      tableHtml += `
        <tr data-nid="${nid}">
          <td contenteditable="true" data-field="nid">${nid}</td>
          <td contenteditable="true" data-field="sentences">${combinedSentences}</td>
          <td><button class="delete-btn" data-nid="${nid}">Delete</button></td>
        </tr>
      `;
    });
    tbody.innerHTML = tableHtml;
  }
}

function triggerTSVExport(shadow, tab) {
  let outputText = "";
  let filename = "";

  const escapeTSVField = (text) => {
    if (!text) return '""';
    let escaped = String(text).replace(/"/g, '""');
    return `"${escaped}"`;
  };

  if (tab === "single") {
    filename = "anki_individual_cards.tsv";
    outputText = ["Note ID", "Word", "SentencePlain", "English Definition Overview", "Frequency", "Correct Japanese Definition"].join('\t') + '\n';
    minedItems.forEach(item => {
      const rowData = [
        escapeTSVField(item.nidindiv),
        escapeTSVField(item.match),
        escapeTSVField(item.sentence),
        escapeTSVField(item.level_and_point),
        escapeTSVField(item.construction),
        escapeTSVField(item.regexpattern)
      ];
      outputText += rowData.join('\t') + '\n';
    });
  } else {
    filename = "anki_grammar_updates.tsv";
    outputText = ["nid", "collected_sentences"].join('\t') + '\n';
    const grouped = {};
    minedItems.forEach(item => {
      if (!grouped[item.nid]) grouped[item.nid] = [];
      grouped[item.nid].push(`${item.sentence} [${item.nidindiv}]`);
    });
    Object.keys(grouped).forEach(nid => {
      const combinedSentences = grouped[nid].join('<br>');
      outputText += `${nid}\t${escapeTSVField(combinedSentences)}\n`;
    });
  }

  const blob = new Blob([new Uint8Array([0xEF, 0xBB, 0xBF]), outputText], { type: 'text/tab-separated-values;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// 2. Yellow Box (Navigation & Statistics)
function setupStatsHub() {
  if (document.getElementById('grammar-stats-hub')) {
    alignAllHubs();
    return;
  }

  const hub = document.createElement('div');
  hub.id = 'grammar-stats-hub';
  hub.style.position = 'fixed';
  hub.style.width = '20px';
  hub.style.height = '20px';
  hub.style.backgroundColor = '#f1c40f'; 
  hub.style.borderRadius = '4px';
  hub.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
  hub.style.zIndex = '9999999b';
  hub.style.cursor = 'pointer';
  hub.style.transition = 'width 0.2s, height 0.2s';
  hub.style.display = 'block';

  const shadow = hub.attachShadow({ mode: 'open' });
  const style = document.createElement('style');
  style.textContent = `
    .panel-container { display: none; width: 100%; height: 100%; flex-direction: column; background: #dfe6e9; box-sizing: border-box; font-family: sans-serif; color: #2d3436; }
    .panel-header { background: #f1c40f; color: #2d3436; padding: 6px 10px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
    .tab-bar { display: flex; background: #b2bec3; gap: 2px; padding: 2px 2px 0 2px; }
    .tab-btn { border: none; background: #f8f9fa; padding: 6px 12px; cursor: pointer; font-weight: bold; font-size: 12px; border-radius: 4px 4px 0 0; }
    .tab-btn.active { background: white; color: #b7950b; }
    .table-wrapper { flex: 1; overflow: auto; padding: 6px; background: white; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th { background: #f1f2f6; border: 1px solid #ced6e0; padding: 6px; text-align: left; position: sticky; top: 0; }
    td { border: 1px solid #ced6e0; padding: 6px; white-space: pre-wrap; word-break: break-all; }
    .jump-link { color: #b7950b; text-decoration: underline; cursor: pointer; font-weight: bold; }
    .jump-link:hover { color: #7d6608; }
    .close-panel-btn { background: none; border: none; color: #2d3436; font-size: 16px; cursor: pointer; }
  `;
  shadow.appendChild(style);

  const container = document.createElement('div');
  container.className = 'panel-container';
  container.id = 'stats-panel';
  container.innerHTML = `
    <div class="panel-header">
      <span>Grammar Analysis & Navigation</span>
      <button class="close-panel-btn">✕</button>
    </div>
    <div class="tab-bar">
      <button class="tab-btn active" id="btn-tab-freq">Frequency</button>
      <button class="tab-btn" id="btn-tab-chrono">Chronological</button>
      <button class="tab-btn" id="btn-tab-sorted">Sorted</button>
    </div>
    <div class="table-wrapper">
      <table id="stats-table">
        <thead id="stats-thead"></thead>
        <tbody id="stats-tbody"></tbody>
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
      hub.style.height = '380px';
      hub.style.cursor = 'default';
      hub.style.resize = 'both';
      hub.style.overflow = 'hidden';
      container.style.display = 'flex';
      renderStatsTable(shadow, currentTab);
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

  shadow.querySelector('#btn-tab-freq').addEventListener('click', (e) => {
    e.stopPropagation(); currentTab = "freq";
    setActiveTabStyle(shadow, '#btn-tab-freq');
    renderStatsTable(shadow, currentTab);
  });

  shadow.querySelector('#btn-tab-chrono').addEventListener('click', (e) => {
    e.stopPropagation(); currentTab = "chrono";
    setActiveTabStyle(shadow, '#btn-tab-chrono');
    renderStatsTable(shadow, currentTab);
  });

  shadow.querySelector('#btn-tab-sorted').addEventListener('click', (e) => {
    e.stopPropagation(); currentTab = "sorted";
    setActiveTabStyle(shadow, '#btn-tab-sorted');
    renderStatsTable(shadow, currentTab);
  });

  alignAllHubs();
}

function setActiveTabStyle(shadow, activeId) {
  shadow.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  shadow.querySelector(activeId).classList.add('active');
}

function renderStatsTable(shadow, tab) {
  const thead = shadow.getElementById('stats-thead');
  const tbody = shadow.getElementById('stats-tbody');
  thead.innerHTML = '';
  tbody.innerHTML = '';

  if (tab === "freq") {
    thead.innerHTML = `
      <tr>
        <th style="width: 70%;">Grammar ("Level And Grammar Point")</th>
        <th style="width: 30%;">Hit Count</th>
      </tr>
    `;
    
    const counts = {};
    analysisMatches.forEach(m => {
      counts[m.grammarName] = (counts[m.grammarName] || 0) + 1;
    });

    const sortedFreq = Object.entries(counts).sort((a, b) => b[1] - a[1]);

    if (sortedFreq.length === 0) {
      tbody.innerHTML = `<tr><td colspan="2" style="text-align:center; color:#7f8c8d;">No matches analyzed.</td></tr>`;
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
        <th style="width: 50%;">Grammar Point</th>
        <th style="width: 20%;">Position</th>
      </tr>
    `;

    if (analysisMatches.length === 0) {
      tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; color:#7f8c8d;">No matches available.</td></tr>`;
      return;
    }

    let statsHtml = "";
    analysisMatches.forEach(m => {
      statsHtml += `
        <tr>
          <td><span class="jump-link" data-target="${m.elementId}">${m.text}</span></td>
          <td>${m.grammarName}</td>
          <td>${m.percentage}%</td>
        </tr>
      `;
    });
    tbody.innerHTML = statsHtml;
    attachJumpLinks(tbody);

  } else if (tab === "sorted") {
    thead.innerHTML = `
      <tr>
        <th style="width: 40%;">Match (Anchor)</th>
        <th style="width: 60%;">Position in Text</th>
      </tr>
    `;

    const counts = {};
    analysisMatches.forEach(m => {
      counts[m.grammarName] = (counts[m.grammarName] || 0) + 1;
    });
    const sortedGrammarNames = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(entry => entry[0]);

    if (sortedGrammarNames.length === 0) {
      tbody.innerHTML = `<tr><td colspan="2" style="text-align:center; color:#7f8c8d;">No matches available.</td></tr>`;
      return;
    }

    let statsHtml = "";
    sortedGrammarNames.forEach(gName => {
      statsHtml += `<tr><td colspan="2" style="background: #e1b12c; color: white; font-weight: bold; padding: 4px 8px;">${gName} (${counts[gName]}x)</td></tr>`;
      const groupMatches = analysisMatches.filter(m => m.grammarName === gName);
      
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
    attachJumpLinks(tbody);
  }
}

function attachJumpLinks(tbody) {
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
          targetEl.style.color = '#2d3436';
        }, 1000);
      }
    });
  });
}

async function loadAndRenderForceList(shadow, listContainer) {
  listContainer.innerHTML = '<div class="empty-msg" style="padding: 10px; color: #7f8c8d;">Loading force list...</div>';
  
  chrome.storage.local.get(['selectedForceNids'], async (storageData) => {
    const forceNids = storageData.selectedForceNids || [];
    
    if (forceNids.length === 0) {
      listContainer.innerHTML = '<div class="empty-msg">No grammar points selected for Force Mark in settings.</div>';
      return;
    }

    try {
      const grammarData = await getGrammarData();
      listContainer.innerHTML = '';

      forceNids.forEach(nid => {
        const item = grammarData[nid];
        if (!item) return;

        const label = document.createElement('label');
        label.className = 'force-item';
        label.innerHTML = `
          <input type="checkbox" class="force-cb" data-nid="${nid}">
          <span>${item.level_and_point || item.Level_And_Grammar_Point || 'Unknown'}</span>
        `;
        listContainer.appendChild(label);

        let hoverTimeout;
        label.addEventListener('mouseenter', () => {
          hoverTimeout = setTimeout(() => {
            showModalPopup([nid], grammarData);
          }, 3000);
        });
        label.addEventListener('mouseleave', () => {
          clearTimeout(hoverTimeout);
        });
      });
    } catch (err) {
      console.error("Error loading Force list grammar data:", err);
      listContainer.innerHTML = '<div class="empty-msg" style="color: red;">Error loading grammar data.</div>';
    }
  });
}

// 3. Purple Box (Force Mark)
function setupForceHub() {
  if (document.getElementById('grammar-force-hub')) {
    alignAllHubs();
    return;
  }

  const hub = document.createElement('div');
  hub.id = 'grammar-force-hub';
  hub.style.position = 'fixed';
  hub.style.width = '20px';
  hub.style.height = '20px';
  hub.style.backgroundColor = '#8A2BE2'; 
  hub.style.borderRadius = '4px';
  hub.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
  hub.style.zIndex = '9999999d';
  hub.style.cursor = 'pointer';
  hub.style.transition = 'width 0.2s, height 0.2s';
  hub.style.display = 'block';

  const shadow = hub.attachShadow({ mode: 'open' });
  const style = document.createElement('style');
  style.textContent = `
    .panel-container { display: none; width: 100%; height: 100%; flex-direction: column; background: #dfe6e9; box-sizing: border-box; font-family: sans-serif; color: #2d3436; }
    .panel-header { background: #8A2BE2; color: white; padding: 6px 10px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
    .list-wrapper { flex: 1; overflow-y: auto; padding: 10px; background: white; display: flex; flex-direction: column; gap: 6px; }
    .force-item { display: flex; align-items: center; gap: 8px; font-size: 12px; padding: 6px; background: #f1f2f6; border-radius: 4px; cursor: pointer; border: 1px solid #dfe4ea; user-select: none; }
    .force-item:hover { background: #dfe4ea; }
    .footer-actions { padding: 6px; background: #f1f2f6; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #ced6e0; }
    .action-btn { background: #8A2BE2; color: white; border: none; padding: 6px 12px; font-weight: bold; border-radius: 4px; cursor: pointer; font-size: 12px; }
    .action-btn:hover { background: #7B1FA2; }
    .close-panel-btn { background: none; border: none; color: white; font-size: 16px; cursor: pointer; }
    .empty-msg { font-size: 12px; color: #7f8c8d; text-align: center; margin-top: 20px; }
  `;
  shadow.appendChild(style);

  const container = document.createElement('div');
  container.className = 'panel-container';
  container.id = 'force-panel';
  container.innerHTML = `
    <div class="panel-header">
      <span>Force Mark ("Grammar points")</span>
      <button class="close-panel-btn">✕</button>
    </div>
    <div class="list-wrapper" id="force-list-container"></div>
    <div class="footer-actions">
      <span style="font-size: 11px; color: #7f8c8d;">Highlight text, select points & click force</span>
      <button class="action-btn" id="btn-force-mark-submit">Force Mark</button>
    </div>
  `;
  shadow.appendChild(container);
  document.body.appendChild(hub);

  const listContainer = container.querySelector('#force-list-container');

  loadAndRenderForceList(shadow, listContainer);

  container.querySelector('#btn-force-mark-submit').addEventListener('click', async () => {
    const selectedText = window.getSelection().toString().trim();
    if (!selectedText) {
      alert("Please select some text on the web page first!");
      return;
    }

    const checkedCbs = shadow.querySelectorAll('.force-cb:checked');
    if (checkedCbs.length === 0) {
      alert("Please select at least one grammar point from the list!");
      return;
    }

    const forcedNids = Array.from(checkedCbs).map(cb => cb.getAttribute('data-nid'));
    const grammarData = await getGrammarData();

    const selection = window.getSelection();
    if (selection.rangeCount > 0) {
      const range = selection.getRangeAt(0);
      const span = document.createElement('span');
      span.className = 'grammar-match-highlight forced-highlight';
      
      uniqueIdCounter++;
      const uniqueMatchId = `grammar-match-force-${uniqueIdCounter}`;
      span.id = uniqueMatchId;
      span.setAttribute('data-nids', forcedNids.join(','));
      span.textContent = selectedText;

      span.style.backgroundColor = '#8A2BE2';
      span.style.color = '#000000';
      span.style.padding = '2px 4px';
      span.style.borderRadius = '4px';
      span.style.cursor = 'pointer';
      span.style.fontWeight = '500';
      span.style.transition = 'background-color 0.2s';

      span.addEventListener('mouseenter', () => span.style.backgroundColor = '#7B1FA2');
      span.addEventListener('mouseleave', () => span.style.backgroundColor = '#8A2BE2');

      span.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        AudioManager.playForceLookup(); 
        showModalPopup(forcedNids, grammarData, span);
      });

      range.deleteContents();
      range.insertNode(span);
      selection.removeAllRanges();

      forcedNids.forEach(nid => {
        const targetGrammar = grammarData[nid];
        if (targetGrammar) {
          const randomSuffix = Math.random().toString(36).substring(2, 6).toUpperCase();
          const sentenceContext = extractSentenceContext(span);
          
          const newMinedItem = {
            nidindiv: `${nid}-${randomSuffix}`,
            nid: nid,
            match: selectedText,
            sentence: sentenceContext,
            level_and_point: targetGrammar.level_and_point || targetGrammar.Level_And_Grammar_Point || '',
            construction: targetGrammar.construction || '',
            regexpattern: targetGrammar.regexpattern || ''
          };

          minedItems.push(newMinedItem);
          resetExportStatus();
          saveMinedItems(); 
        }
      });

      updateFloatingHubState();

      const statsHub = document.getElementById('grammar-stats-hub');
      if (statsHub) {
        const statsShadow = statsHub.shadowRoot;
        const activeBtn = statsShadow.querySelector('.tab-btn.active');
        let currentStatsTab = "freq";
        if (activeBtn) {
          if (activeBtn.id === 'btn-tab-chrono') currentStatsTab = "chrono";
          if (activeBtn.id === 'btn-tab-sorted') currentStatsTab = "sorted";
        }
        renderStatsTable(statsShadow, currentStatsTab);
      }
    }
  });

  hub.addEventListener('click', (e) => {
    if (hub.style.width === '20px') {
      e.stopPropagation();
      hub.style.width = '550px';
      hub.style.height = '380px';
      hub.style.cursor = 'default';
      hub.style.resize = 'both';
      hub.style.overflow = 'hidden';
      container.style.display = 'flex';
      
      loadAndRenderForceList(shadow, listContainer);
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

  alignAllHubs();
}

function showModalPopup(nids, grammarData, clickedSpan) {
  const existingModal = document.getElementById('grammar-analysis-modal');
  if (existingModal) existingModal.remove();

  const modal = document.createElement('div');
  modal.id = 'grammar-analysis-modal';
  modal.style.position = 'fixed';
  modal.style.top = '100px';
  modal.style.right = '20px';
  modal.style.width = '320px';          
  modal.style.height = '350px';         
  modal.style.minWidth = '250px';       
  modal.style.minHeight = '200px';      
  modal.style.resize = 'both';          
  modal.style.overflow = 'hidden';      
  modal.style.backgroundColor = '#dfe6e9';
  modal.style.boxShadow = '0 8px 20px rgba(0,0,0,0.2)';
  modal.style.borderRadius = '10px';
  modal.style.zIndex = '99999999';
  modal.style.display = 'flex';
  modal.style.flexDirection = 'column';
  modal.style.fontFamily = 'sans-serif';

  const shadow = modal.attachShadow({ mode: 'open' });
  const style = document.createElement('style');
  style.textContent = `
    :host { --base-font-size: 14px; }
    .modal-container { display: flex; flex-direction: column; height: 100%; background: #dfe6e9; color: #2d3436; box-sizing: border-box; }
    .drag-handle { background: #0984e3; color: #ffffff; padding: 8px 12px; cursor: move; display: flex; justify-content: space-between; align-items: center; font-size: var(--base-font-size); font-weight: bold; flex-shrink: 0; }
    .close-btn { cursor: pointer; font-size: 18px; border: none; background: none; color: #ffffff; padding: 0; line-height: 1; }
    .modal-content-scroll { padding: 10px; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 12px; }
    .card-container { background-color: white; border-radius: 6px; width: 100%; padding: 12px; border: 1px solid #d1d8e0; box-sizing: border-box; position: relative; }
    .grammar-header-wrapper { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px; gap: 8px; }
    .grammar-header { font-size: var(--base-font-size); font-weight: bold; color: #0984e3; text-align: left; }
    .add-anki-btn { background: #27ae60; color: white; border: none; padding: 3px 8px; font-size: 11px; font-weight: bold; border-radius: 4px; cursor: pointer; transition: background 0.1s; flex-shrink: 0; }
    .add-anki-btn:hover { background: #219653; }
    .tags-badge { font-size: 11px; color: #636e72; margin-bottom: 8px; display: block; }
    .separator { border: none; height: 1px; background: #eee; margin: 8px 0; }
    .content-section { margin-bottom: 10px; }
    .label { font-size: var(--base-font-size); font-weight: bold; color: #b2bec3; margin-bottom: 2px; }
    .text-content { font-size: var(--base-font-size); color: #2d3436; line-height: 1.4; word-break: break-word; white-space: pre-line; }
    .box-style { background: #f8f9fa; padding: 6px; border-radius: 4px; border-left: 3px solid #0984e3; }
    .link-box a { font-size: var(--base-font-size); color: #0984e3; text-decoration: none; font-weight: bold; }
  `;
  shadow.appendChild(style);

  const container = document.createElement('div');
  container.className = 'modal-container';

  const header = document.createElement('div');
  header.className = 'drag-handle';
  header.innerHTML = `<span>Match (${nids.length})</span><button class="close-btn">✕</button>`;
  container.appendChild(header);

  const scrollArea = document.createElement('div');
  scrollArea.className = 'modal-content-scroll';

  nids.forEach(nid => {
    const g = grammarData[nid];
    if (!g) return;

    const card = document.createElement('div');
    card.className = 'card-container';
    card.innerHTML = `
      <div class="grammar-header-wrapper">
        <div class="grammar-header">${g.level_and_point || g.Level_And_Grammar_Point || ''}</div>
        <button class="add-anki-btn" data-nid="${nid}">+ Anki</button>
      </div>
      <span class="tags-badge">${g.tags || ''}</span>
      <hr class="separator">
      
      <div class="content-section">
        <div class="label">Construction</div>
        <div class="text-content">${g.construction || ''}</div>
      </div>
      
      <div class="content-section">
        <div class="label">Examples</div>
        <div class="text-content box-style">${g.examplesentences || ''}</div>
      </div>
      
      <div class="content-section">
        <div class="link-box">
          <a href="${g.link || g.Link || '#'}" target="_blank">→ JLPT Sensei</a>
        </div>
      </div>

      <div class="content-section">
        <div class="label">Regexpatterns</div>
        <div class="text-content">${g.regexpattern || ''}</div>
      </div>
    `;

    card.querySelector('.add-anki-btn').addEventListener('click', (e) => {
      const targetNid = e.target.getAttribute('data-nid');
      const targetGrammar = grammarData[targetNid];
      
      if (targetGrammar) {
        AudioManager.playAddAnki(); 
        
        const sentenceContext = clickedSpan ? extractSentenceContext(clickedSpan) : "";
        const randomSuffix = Math.random().toString(36).substring(2, 6).toUpperCase();
        
        const newMinedItem = {
          nidindiv: `${targetNid}-${randomSuffix}`,
          nid: targetNid,
          match: clickedSpan ? clickedSpan.textContent.trim() : "",
          sentence: sentenceContext,
          level_and_point: targetGrammar.level_and_point || targetGrammar.Level_And_Grammar_Point || '',
          construction: targetGrammar.construction || '',
          regexpattern: targetGrammar.regexpattern || ''
        };

        minedItems.push(newMinedItem);
        resetExportStatus();
        saveMinedItems(); 
        updateFloatingHubState();
        
        e.target.textContent = "✓ Added";
        e.target.style.backgroundColor = "#219653";
        setTimeout(() => {
          e.target.textContent = "+ Anki";
          e.target.style.backgroundColor = "#27ae60";
        }, 1500);
      }
    });

    scrollArea.appendChild(card);
  });

  container.appendChild(scrollArea);
  shadow.appendChild(container);

  header.querySelector('.close-btn').addEventListener('click', () => {
    AudioManager.playClosePopup(); 
    modal.remove();
  });
  
  document.body.appendChild(modal);

  let isDragging = false;
  let offsetX, offsetY;
  header.addEventListener('mousedown', (e) => {
    if (e.target.className === 'close-btn') return;
    isDragging = true;
    const rect = modal.getBoundingClientRect();
    offsetX = e.clientX - rect.left;
    offsetY = e.clientY - rect.top;
  });
  window.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    modal.style.right = 'auto';
    modal.style.left = (e.clientX - offsetX) + 'px';
    modal.style.top = (e.clientY - offsetY) + 'px';
  });
  window.addEventListener('mouseup', () => { isDragging = false; });
}