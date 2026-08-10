chrome.runtime.onInstalled.addListener(() => {
  // Clear the session lookup statistics when the extension installs or updates
  chrome.storage.local.set({ sessionLookups: 0 });

  // Prevents duplicate ID errors by removing the existing menu item first
  chrome.contextMenus.remove("analyzeGrammarSelection", () => {
    if (chrome.runtime.lastError) {
      // Ignore if the item does not exist on the very first run
    }
    
    chrome.contextMenus.create({
      id: "analyzeGrammarSelection",
      title: "Start Japanese Grammar Analysis",
      contexts: ["page", "selection"]
    });
  });
});

chrome.runtime.onStartup.addListener(() => {
  // Reset the session lookup counter when browser starts up
  chrome.storage.local.set({ sessionLookups: 0 });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "analyzeGrammarSelection") {
    // Sends the activation signal to content.js on the active page
    chrome.tabs.sendMessage(tab.id, { 
      action: "analyzeSelection"
    });
  }
});