# Ruby Remover

**Ruby Remover** is a lightweight Chrome extension (Manifest V3) specifically designed for use with **Tsuu Reader**. It prepares Light Novel text so that other text-scanning extensions (such as pop-up dictionaries) can function flawlessly without being interrupted by Furigana (ruby tags) or fragmented text nodes.

---

## Demo

https://github.com/user-attachments/assets/12daaa9e-3880-402e-a733-e8d38e6a2822

---

## Key Features

* **Furigana Removal (Ruby Tags):** The extension scans the document, removes all `<rt>` and `<rp>` elements, and preserves only the original Kanji or base text. The structural integrity of the layout remains perfectly intact.


* **Text Normalization (`DOM Normalize`):** After removing the ruby tags, fragmented text nodes (e.g., `"可愛"` + `"いい〜。"`) are automatically fused back into a single, cohesive string within the DOM. This step is critical for ensuring that downstream text-scanning addons can accurately recognize vocabulary.


* **Middle-Block Cleanup:** Paragraphs carrying the `p.middle-block` class are automatically processed. Stray quotation marks and brackets (such as `"`, `„`, `“`, `「`, `」`) are stripped out, and multiple consecutive whitespaces are collapsed into a single space.



---

## How It Works Under the Hood

When you click the extension's icon in your browser toolbar, it triggers a sequence via the background components:

1. **Event Listening:** The service worker in `background.js` listens for the extension icon click.


2. **Script Injection:** It dynamically injects and executes `content.js` onto your active browser tab.


3. **DOM Manipulation:** The injected script in `content.js` isolates and deletes the Furigana markup, invokes `document.body.normalize()` to merge fractured strings, and formats text inside `.middle-block` elements.



---

## Installation & Usage

Since this project is currently hosted on GitHub, you can install it as a developer extension on any Chromium-based browser (Google Chrome, Brave, Microsoft Edge, Vivaldi):

### 1. Download the Extension

* Clone this repository using Git, or download the source code as a ZIP file directly from GitHub and extract it into a local directory.

### 2. Enable Developer Mode

* Open your browser's extension management page by navigating to `chrome://extensions/`.
* Toggle the **Developer mode** switch in the top-right corner.

### 3. Load the Unpacked Folder

* Click the **"Load unpacked"** button in the top-left corner.
* Select the local folder containing your `manifest.json`, `background.js`, and `content.js` files.



### 4. Running on Tsuu Reader

* Navigate to your Light Novel reader inside **Tsuu Reader**.
* Click the **Ruby Remover** icon in your browser toolbar (hint: pin the icon for quicker access).
* The script instantly cleans the page in the background, allowing you to scan text freely with your target dictionary tools.

---

## Technical Details

The extension is built adhering to the modern **Manifest V3** standard:

* **`activeTab` Permission:** Grants the extension temporary, secure access to the active tab only when you explicitly click its icon, ensuring user privacy.


* **`scripting` API:** Allows `content.js` to be injected on-demand by the `background.js` service worker, eliminating the need for a persistent background script that wastes system resources.



---

What additional information or features would you like to add next? Let me know, and we can refine it further!
