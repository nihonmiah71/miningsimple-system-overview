# miningsimple-system-overview
Connects several repos of this profile together and introduces an efficient and experience-based learning system with multiple mining workflows to acquire the Japanese language most efficiently.

---

# Core Philosophy & Mindset

The main idea of this system is to **shift away from using Anki as a traditional learning scheduler and instead treat it primarily as a database**. 

While reviewing cards is important, relying solely on Anki’s default scheduling algorithm can lead to massive time waste. Your time is far better spent actively reading and immersing in new material. 

## The 3 Core Strategies
Instead of brute-force memorization, this system proposes three interconnected strategies:

1. **Visual Recognition Over Memorization:** Every card you look up today is added to your vocabulary list. When you encounter the word again during reading, a visual indicator alerts you that you’ve seen it before. This also immediately shows you the word's actual importance based on how frequently you run into it.
2. **Zero-Effort Mining:** You don't waste time manually creating cards. With just a few clicks, audio, accurate translations, context, and visuals are automatically generated for your mined card using either the **Light Novel** or **Anime** framework. You should generally look at these cards only once and access them later *on demand*, rather than forcing yourself to memorize them. Save your mental energy for deep Japanese concepts.
3. **Hyper-Selective Long-Term Reviewing:** If you choose to use Anki's scheduler, you must be **highly selective**. Understand exactly *why* you want to learn a specific card long-term. Aim for **at most 5 new cards daily**. This system introduces a framework that helps you filter out the noise, providing both shallow and deep reviewing mechanisms.

> 💡 **Note to Users:** You probably already have a running Anki system. You don't have to abandon it. Simply finish reviewing the remaining cards left in your current stack, but stop adding new cards using your old system. Shift your focus here.
---

$${\\color{red}Remember \\space that \\space you \\space have \\space to \\space do \\space the \\space installation \\space only \\space once \\space and \\space that \\space the \\space actual \\space workflows \\space are \\space very \\space quick. \\space For \\space example, \\space while \\space previously \\space the \\space ratio \\space of \\space reading:preparing:reviewing \\space was \\space 1:1:1, \\space after \\space you \\space have \\space finished \\space the \\space setup \\space and \\space use \\space the \\space workflows \\space it \\space will \\space be \\space 8:1:1.}$$


## 🛠️ Anki Setup & Add-ons

To ensure the **miningsimple** system works correctly, specific Anki add-ons are required for card rendering, database maintenance, and workflow automation. 

### 🌟 Custom Developed Add-ons
These are my own specialized add-ons designed explicitly to power the workflows and database connections of this system.

| Add-on Name | Code / Link | Status | Description |
| :--- | :---: | :---: | :--- |
| **field_extraction_injection** | [207985417](https://ankiweb.net/shared/info/207985417) | 🔴 **Essential** | Required for every single mining workflow and general database maintenance. |
| **grammarmininghub** | [984445827](https://ankiweb.net/shared/info/984445827) | 🔴 **Essential** | *(Also referred to as GrammarMinerLinker)* Connects the GrammarHub web addon to Anki; handles adding and updating cards in the database. |
| **JLPT Database graph relation crawler** | [1321136162](https://ankiweb.net/shared/info/1321136162) | ⚡ *Recommended* | Creates clusters for grammar cards to visualize them via the Note Linker graph (generates tags used for filtering). |
| **grammar_simple_linker** | [787429252](https://ankiweb.net/shared/info/787429252) | 🔹 Optional | Manually connects base grammar notes together (not for individual mined sentence notes). |
| **miningsimple_linker** | [1444428697](https://ankiweb.net/shared/info/1444428697) | 🔹 Optional | Connects notes of the `miningsimple` type together for cross-access. |
| **nplus1scan** | [1389423810](https://ankiweb.net/shared/info/1389423810) | 🔹 Optional | Analyzes filtered cards (sorted by term cardtype) to find unique audio files in the `soundfront` field, validating contexts where only one card was mined. |
| **siblingsync** | [1383490780](https://ankiweb.net/shared/info/1383490780) | 🔹 Optional | Manages the term/pronunciation system to help you focus exclusively on what you want to learn. |

---

### 🏛️ Essential Public Add-ons
You **must** install these public add-ons for the note types, Yomitan integration, and automated parsing to function.

*   **Toggle front and back card in Anki 2.1** ([1240106570](https://ankiweb.net/shared/info/1240106570))
    *   *Why:* Necessary for the correct rendering of the `miningsimple` note type.
*   **AnkiConnect** ([2055492159](https://ankiweb.net/shared/info/2055492159))
    *   *Why:* Indispensable for mining; acts as the bridge to **Yomitan**.
*   **🔗 Anki Note Linker** ([1077002392](https://ankiweb.net/shared/info/1077002392))
    *   *Why:* Essential for rendering the note types and enabling core linking functionalities.
*   **AJT Japanese for JP Mining Note** ([200813220](https://ankiweb.net/shared/info/200813220))
    *   *Why:* Automatically generates Furigana for mined sentences and creates the Japanese definition overview. Also handles custom name readings.
*   **Auto-refresh browser** ([746398558](https://ankiweb.net/shared/info/746398558))
    *   *Why:* Essential when mining. Forces newly created cards to appear on top of the stack for instant editing.
*   **AutoReorder** ([757527607](https://ankiweb.net/shared/info/757527607))
    *   *Why:* Important for prioritizing cards based on frequency fields (study common words first).
*   **Additional Card Fields (Fork for 2.1)** ([744725736](https://ankiweb.net/shared/info/744725736))
    *   *Why:* Necessary to correctly render statistics for grammar cards during review.

---

### ⚙️ Recommended & Optional Utilities
These add-ons are not strictly mandatory but highly recommended to optimize your Anki Browser, statistics, and editing workflow.

<details>
<summary>📊 Statistics & Progress Tracking</summary>

*   **Study Time Stats** ([1247171202](https://ankiweb.net/shared/info/1247171202)) – Detailed insights into study time metrics.
*   **Review Heatmap** ([1771074083](https://ankiweb.net/shared/info/1771074083)) – Visualizes daily study consistency. *(Tip: Great for tracking active mining time frames, e.g., cards added within the last hour).*
*   **More Overview Stats 2.1** ([738807903](https://ankiweb.net/shared/info/738807903)) – Extra analytical overview elements on the main deck screen.
</details>

<details>
<summary>🔍 Browser Optimization & View Enhancements</summary>

*   **Link Cards Notes and Preview them** ([1423933177](https://ankiweb.net/shared/info/1423933177)) – Important extension of the *Note Linker* ecosystem to preview linked notes in a separate window.
*   **⏩ Preview Slideshow (Fixed by Shigeඞ)** ([1621302762](https://ankiweb.net/shared/info/1621302762)) – Advanced previewing capabilities within the Anki Browser.
*   **Advanced Browser** ([874215009](https://ankiweb.net/shared/info/874215009)) – Makes sorting and navigating the Anki browser layout significantly more comfortable.
*   **Browser Maximize/Hide Table/Editor/Sidebar** ([1819291495](https://ankiweb.net/shared/info/1819291495)) – Dynamic flexibility for your browser workspace layout.
</details>

<details>
<summary>✍️ Editor & Management Utilities</summary>

*   **Batch Editing** ([291119185](https://ankiweb.net/shared/info/291119185)) – Highly recommended tool to modify multiple selected cards at once across various fields.
*   **AJT Card Management** ([1021636467](https://ankiweb.net/shared/info/1021636467)) – Bulk reset, learn, and grade cards directly from the Browser interface.
*   **CSS Injector** ([181103283](https://ankiweb.net/shared/info/181103283)) – Modifies default editor styles; can impact card rendering layouts.
*   **Advanced Copy Fields** ([1898445115](https://ankiweb.net/shared/info/1898445115)) – Allows rapid field relocation and copy operations.
*   **Opening the same window multiple time** ([354407385](https://ankiweb.net/shared/info/354407385)) – Grants more freedom to open multiple editor windows simultaneously.
*   **strikethrough_in_editor** ([698524645](https://ankiweb.net/shared/info/698524645)) – Quick formatting utility to use strikethrough text inside fields.
*   **google translate** ([1536291224](https://ankiweb.net/shared/info/1536291224)) – Quickly batch add transaltions to your mined sentences.
</details>

## Yomitan and Ankiconnect Configuration

Except the workflow most of the installation and set ups steps must only be done on time

### How to connect anki with yomitan?
<details>
Connecting Yomitan with Anki via the **AnkiConnect** add-on is the absolute gold standard for mining vocabulary efficiently. It allows you to transform words directly from your browser into fully formatted Anki cards with a single click.

Since AnkiConnect acts as a local API, we need to ensure that Anki's backend permissions and your browser's extension settings are perfectly aligned.

Here is the step-by-step setup guide.

---

## 1. Install AnkiConnect in Anki

First, you need to install the add-on in Anki so that external programs (like your browser) are permitted to communicate with your database.

1. **Copy the Code:** Copy the official AnkiConnect code: **2055492159**.
2. **Install in Anki:** Open Anki. In the top menu, go to **Tools** -> **Add-ons**. Click **Get Add-ons...** in the top right, paste the code into the text field, and click **OK**.
3. **Restart Anki:** Close Anki completely and reopen it. The local AnkiConnect server (running on port `8765` by default) will only initialize after a fresh launch.

---

## 2. Configure Yomitan in the Browser

Now, we link the browser extension to the running AnkiConnect interface.

1. **Open Settings:** Click the Yomitan icon in your browser extension bar and open the **Settings** (the gear icon).
2. **Enable Integration:** Scroll down the left sidebar menu to the **Anki** section. Toggle the switch for **Enable Anki integration**.
3. **Verify Connection:** Yomitan will automatically attempt to reach the local server (`[http://127.0.0.1:8765](http://127.0.0.1:8765)`). If Anki is running properly in the background, the status will change to **Connected** within a few seconds.

---

## 3. Download the dictionaries

See as a reference the picture which dictionaries you should use, you can find those dictionaries on the official yomitan website https://yomitan.wiki/dictionaries/, or with a google prompt

<img width="817" height="543" alt="image" src="https://github.com/user-attachments/assets/9c8437c5-e144-4170-bd72-121957bc6461" />


---

## 4. Map Note Types and Fields

Once connected, Yomitan directly fetches your Anki decks and note types. Just import the yomitansettings which are enclosed in the attachments and you can start to mine, also make sure that you call the deck you want to mine from mining or configure the settings in the yomitan options manualy.


Once configured, simply hold your activation key (usually `Shift`) over any word in your browser, and click the green **`+`** icon in the Yomitan pop-up to instantly create a card in the background.

</details>

---

## Local Chrome Extension Installation 

### For the mining process, you want to install several Chrome extensions locally using source files that are already downloaded onto your computer (rather than using the official Web Store).

* [Japanese Learners Optimized Multitextmarker Browser Addon](https://github.com/nihonmiah71/japanese-learners-optimized-multitextmarker-browseraddon)
* [Japanese GrammarHub Browser Addon](https://github.com/nihonmiah71/japanese-grammarhub-browseraddon)
* [Ruby Furigana Remover for Tsuu Reader Browser Addon](https://github.com/nihonmiah71/Ruby-Furigana-remover-for-tsuu-reader-browseraddon)

<details>
   
### General Installation Procedure

### Step 1: Prepare the Files

* Load all the files you downloaded in one folder

### Step 2: Open the Extensions Menu in Chrome

1. Open Google Chrome.
2. Click on the **three vertical dots** (Menu) in the top-right corner.
3. Hover over **Extensions** and select **Manage Extensions**.
*(Alternatively, type `chrome://extensions/` directly into the address bar and press Enter).*

### Step 3: Enable Developer Mode

In the top-right corner of the Extensions management screen, find the toggle switch labeled **Developer mode**.

* Flip this switch to the **ON** position.
* Once enabled, a secondary utility bar will instantly appear on the top-left side of the interface displaying three operational buttons: *Load unpacked*, *Pack extension*, and *Update*.

### Step 4: Load the Local Extension

1. Click the **Load unpacked** button on the far-left side of the Developer menu bar.
2. A system file explorer window will pop up.
3. Navigate to the local folder where your extracted extension files reside.

### Step 5: Reloading After Source Changes

If you modify any source code files (such as background scripts, stylesheets, or configuration objects) within your local directory, Chrome does not track updates in real-time. You must manually force a refresh:

1. Save all file edits within your code editor.
2. Return to `chrome://extensions/`.
3. Locate the respective extension's interface card.
4. Click the circular **Reload arrow icon** located in the bottom-right corner of that card.
5. *Note: If your local extension interacts with a specific website or tab, remember to refresh that target webpage (F5) for the changes to apply.*
</details>
---

##  Further Add-on Configurations

### Configuration of AJT Japanese and AutoReorder

<details>

### 1. AJT Japanese (for JP Mining Note) Profile Setup

To customize sentence parsing and target fields, configure two distinct profiles at the beginning of your configuration process:

1. Open your Anki dashboard layout.
2. Look at the top menu bar directly at the top of your card dashboard area.
3. Navigate into the **Japanese Options** menu selection.
4. Add exactly **2 new profiles** using your specific parameters to align text mapping scripts correctly with your database note properties.

<img width="1304" height="775" alt="image" src="https://github.com/user-attachments/assets/5e4cbcdc-5040-4bcc-a530-a73eb551a75a" />
<img width="1303" height="780" alt="image" src="https://github.com/user-attachments/assets/4c2dde30-8507-4880-87af-be3c16a8854f" />


### 2. AutoReorder Automation Script

To ensure cards containing frequent terms are systematically prioritized during active review loops, update the scheduling layout properties:

1. From the top main menu toolbar in Anki, click on **Tools**.
2. Select **AutoReorder** from the drop-down list.
3. Navigate directly to the **Config** tab.
4. Replace or insert the following configuration text into the editor window:

```
{
    "search_to_sort": "deck:mining is:new",
    "shift_existing": true,
    "sort_field": "Frequency",
    "sort_reverse": false
}

```
</details>
---
