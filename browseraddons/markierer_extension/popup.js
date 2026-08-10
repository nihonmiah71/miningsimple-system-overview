// Helper to enable or disable the tolerance input depending on the checkbox state
function updateToleranceState() {
    const onlyKanjiChecked = document.getElementById('onlyKanji').checked;
    document.getElementById('kanjiTolerance').disabled = !onlyKanjiChecked;
}

// On popup load: Retrieve the last saved state from Chrome Storage
document.addEventListener('DOMContentLoaded', async () => {
    const data = await chrome.storage.local.get(['savedWords', 'onlyKanji', 'kanjiTolerance']);
    if (data.savedWords) {
        document.getElementById('words').value = data.savedWords;
    }
    if (data.onlyKanji !== undefined) {
        document.getElementById('onlyKanji').checked = data.onlyKanji;
    }
    if (data.kanjiTolerance !== undefined) {
        document.getElementById('kanjiTolerance').value = data.kanjiTolerance;
    }
    updateToleranceState();
});

// Save words, mode, and tolerance to local storage dynamically when they change
document.getElementById('words').addEventListener('input', (e) => {
    chrome.storage.local.set({ savedWords: e.target.value });
});

document.getElementById('onlyKanji').addEventListener('change', (e) => {
    chrome.storage.local.set({ onlyKanji: e.target.checked });
    updateToleranceState();
});

document.getElementById('kanjiTolerance').addEventListener('input', (e) => {
    const parsedVal = parseInt(e.target.value, 10);
    const valueToSave = isNaN(parsedVal) || parsedVal < 0 ? 0 : parsedVal;
    chrome.storage.local.set({ kanjiTolerance: valueToSave });
});

// Send marking request to the content script of the active tab
document.getElementById('btn').addEventListener('click', async () => {
    const query = document.getElementById('words').value;
    const onlyKanjiChecked = document.getElementById('onlyKanji').checked;
    
    const parsedTolerance = parseInt(document.getElementById('kanjiTolerance').value, 10);
    const kanjiToleranceVal = isNaN(parsedTolerance) || parsedTolerance < 0 ? 0 : parsedTolerance;
    
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (tab) {
        chrome.tabs.sendMessage(tab.id, { 
            action: "mark", 
            query: query, 
            onlyKanji: onlyKanjiChecked,
            kanjiTolerance: kanjiToleranceVal
        });
    }
});

// DATABASE FUNCTION: Export active word list as a text file
document.getElementById('btnSave').addEventListener('click', () => {
    const text = document.getElementById('words').value;
    if (!text.trim()) return;
    
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `textfinder_db_${new Date().toISOString().slice(0,10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
});

// DATABASE FUNCTION: Import word list from a text file
document.getElementById('fileInput').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(evt) {
        const content = evt.target.result;
        document.getElementById('words').value = content;
        chrome.storage.local.set({ savedWords: content });
    };
    reader.readAsText(file, 'UTF-8');
});

// Trigger the hidden file input element when the Import button is clicked
document.getElementById('btnLoad').addEventListener('click', () => {
    document.getElementById('fileInput').click();
});