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
</details>
