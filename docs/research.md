# Comprehensive Keyboard Accessibility & Media Shortcuts Reference

A structured reference guide analyzing keyboard controls, player settings, subtitle synchronization, audio stream switching, and web navigation across all major streaming services, media players, and desktop browsers.

---

## 1. Key Insights & Architecture

* **The POUR Accessibility Mandate**: WCAG 2.1 requires all media playback functions to be operable by keyboard without keyboard traps.
* **The Focus Dichotomy**:
  * **Global Webpage Focus**: Keystrokes scroll the page or navigate tabs (`Spacebar` = page down, `/` = focus search, `Ctrl+L` = address bar).
  * **Player Container Focus**: Keystrokes control media (`Spacebar`/`K` = play/pause, `J`/`L` = $\pm 10\text{s}$ seek, `C` = captions, `M` = mute).
* **High-Value Triggers for Remote Deck**:
  * **Search**: `/` (in-page video search) & `Ctrl+L` (browser address bar).
  * **Subtitles**: `C` (toggle captions), `+`/`-` (font size), `G`/`H` & `z`/`Z` (sync delay).
  * **Audio**: `A` (cycle audio track), `J`/`K` & `Ctrl+`/`Ctrl-` (audio sync delay), `M` (mute).
  * **Speed**: `Shift+>` / `Shift+<` (YouTube/Web), `[` / `]` (VLC/MPV).
  * **Stream Features**: `S` (skip intro / recap), `T` (theater mode), `I` (miniplayer / PiP).
  * **Navigation**: `Arrow Keys` + `Enter` (browse cards/dropdowns), `Tab` / `Shift+Tab`, `Esc`.

---

## 2. Platform Comparison Matrix

| Platform | Play / Pause | Seek ($\pm 10\text{s}$) | Seek (Fine $\pm 5\text{s}$) | Subtitles Toggle | Audio Selector | Speed Control | Search Focus | Skip Intro | Fullscreen |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **YouTube** | `K` / `Space` | `J` / `L` | `Left` / `Right` | `C` | Menu (`Tab`) | `Shift+>` / `Shift+<` | `/` | *Ext* | `F` |
| **Netflix** | `Space` / `Enter` | `Left` / `Right` | — | Menu / *Ext (`C`)* | Menu / *Ext (`A`)* | *Ext (`<` `>`)* | `Enter` | `S` | `F` |
| **Prime Video** | `Space` | `Left` / `Right` | — | `C` | `A` | *Ext* | `Tab` | *Ext* | `F` |
| **Disney+ Hotstar** | `Space` / `Enter` | `Left` / `Right` | — | Menu | Menu | *Ext* | `Tab` | — | `F` |
| **Twitch** | `Space` / `K` | — | — | — | — | — | `Alt+Enter` (Chat) | — | `F` |
| **Crunchyroll** | `Space` / `K` | `J` / `L` | `Shift+<` / `Shift+>` (Frame) | `C` | Menu | — | `Tab` | `S` | `F` |
| **VLC Player** | `Space` | `Alt+Left` / `Alt+Right` | `Shift+Left` / `Shift+Right` | `V` (Cycle) / `G`/`H` (Sync) | `B` (Cycle) / `J`/`K` (Sync) | `[` / `]` | — | — | `F` |
| **MPV Player** | `Space` / `p` | `Left` / `Right` (5s) | `Shift+Left` / `Shift+Right` (1s) | `j`/`J` (Cycle) / `z`/`Z` (Sync) | `#` (Cycle) / `Ctrl+`/`Ctrl-` (Sync) | `[` / `]` | `o` / `P` (OSD) | — | `f` |
| **Browsers (General)** | `Space` (Page) | — | — | — | `Ctrl+M` (Tab Mute - FF) | — | `Ctrl+L` / `Ctrl+K` | — | `F11` |

---

## 3. Subtitles, Audio & Player Settings Deep Dive

### Subtitle & Caption Controls
* **YouTube**:
  * `C`: Toggle Closed Captions on/off.
  * `+` / `-`: Increase / decrease caption font size.
  * `O`: Cycle text opacity / brightness.
  * `W`: Cycle background window opacity.
* **Prime Video**:
  * `C`: Toggle subtitles on/off and cycle available language tracks.
* **VLC Media Player**:
  * `V`: Cycle subtitle tracks.
  * `G` / `H`: Subtitle delay sync ($\pm 50\text{ms}$ stepping backward/forward).
* **MPV Player**:
  * `v`: Toggle subtitle visibility on/off.
  * `j` / `J`: Cycle subtitle tracks forward/backward.
  * `z` / `Z`: Subtitle delay sync by $\pm 100\text{ms}$.
  * `G` / `F`: Scale subtitle font size up/down by 10%.
  * `r` / `u`: Move subtitle vertical positioning up/down.

### Audio Stream & Language Controls
* **Prime Video**:
  * `A`: Cycle alternative audio dubs and Audio Descriptions (AD).
* **VLC Media Player**:
  * `B`: Cycle audio tracks.
  * `J` / `K`: Audio delay sync ($\pm 50\text{ms}$ stepping backward/forward).
* **MPV Player**:
  * `#`: Cycle audio tracks (dubs, commentary).
  * `Ctrl + +` / `Ctrl + -`: Audio delay sync by $\pm 100\text{ms}$.

---

## 4. Web Navigation & Focus Shortcuts

* **`/` (Forward Slash)**: Universal search focus shortcut on YouTube, GitHub, Reddit, Notion, Wikipedia.
* **`Ctrl + L` / `Alt + D` / `F6`**: Universal browser address bar focus across Chrome, Edge, Firefox, Brave.
* **`Tab` / `Shift + Tab`**: Navigate interactive cards, video carousels, and player control buttons.
* **`Enter`**: Open focused video/movie or submit search query.
* **`Arrow Keys` ($\uparrow \downarrow \leftarrow \rightarrow$)**: Navigate autocomplete search dropdowns and content grids.
* **`Esc`**: Dismiss search dropdowns, close overlays (Prime X-Ray, modal details), exit fullscreen.
* **`Ctrl + Tab` / `Ctrl + Shift + Tab`**: Cycle forward/backward through browser tabs.
* **`Ctrl + Shift + T`**: Reopen accidentally closed video tab.
