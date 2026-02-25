# Tusic

A lightning-fast, Vim-driven Terminal User Interface (TUI) for streaming Music. 

Built with Python and the [Textual](https://textual.textualize.io/) framework, Tusic strips away the bloat of modern electron apps, giving you a clean, keyboard-centric grid layout with dynamic styling that respects your system's Pywal colors.

![Project Screenshot](./ss/startup.png)

![Project Screenshot](./ss/playing.png)

![Project Screenshot](./ss/helpscreen.png)

## Features

* **Vim-Native Navigation:** Keep your hands on the home row. Navigate panes, scroll lists, and search entirely via standard Vim keybindings (`h`, `j`, `k`, `l`, `/`).
* **Pywal Integration:** Tusic dynamically reads `~/.cache/wal/colors.json` on startup and accents the UI using your system's `color6`. It falls back to a clean pastel mint if Pywal isn't running.
* **Smart "Made For You":** Analyzes your local listening history, calculates your top artists, and automatically curates a YouTube Music radio mix on startup.
* **Local Database:** Fully private, local SQLite database stores your listening history and custom saved playlists.
* **Gapless MPV Playback:** Audio is handled asynchronously via a hidden `libmpv` background process for zero-latency playback.
* **Bypass Protections:** Uses `yt-dlp` under the hood to reliably extract and resolve high-quality audio streams directly from YouTube's servers.

## Requirements

### System Dependencies
You need the `mpv` media player installed on your system for the audio engine to work.
* **Arch Linux:** `sudo pacman -S mpv`
* **Debian/Ubuntu:** `sudo apt install mpv`
* **macOS:** `brew install mpv`

### Python Dependencies
* `python >= 3.10`
* `textual`
* `ytmusicapi`
* `yt-dlp`
* `python-mpv`

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/impossibleclone/tusic.git
   cd tusic
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install textual ytmusicapi yt-dlp python-mpv
   ```

4. **Run the app:**
   ```bash
   python app/main.py
   ```

## ⌨️ Keybindings

Tusic is designed to be used entirely without a mouse.

| Key | Action | Context |
| :--- | :--- | :--- |
| `h` | Focus Left (Library Pane) | Normal Mode |
| `l` | Focus Right (Songs Table) | Normal Mode |
| `H` | Focus Left (Search Results) | Up Next Table |
| `L` | Focus Right (Up Next Table) | Search Results |
| `j` | Move Cursor Down | Normal Mode |
| `k` | Move Cursor Up | Normal Mode |
| `/` | Focus Search Bar | Normal Mode |
| `Enter` | Play Selected Track / Submit Search | Normal/Search Mode |
| `Space` | Play / Pause Audio | Global |
| `s` | Save Song to Local Playlist | Focused on Songs Table |
| `d` | Delete Song from Local Playlist | Focused on Songs Table |
| `r` | Refresh Recommendations | Normal Mode |
| `?` | Toggle Help Menu | Global |
| `Esc` | Unfocus Search / Close Help | Search/Help Mode |
| `q` | Quit Tusic | Global |

## Project Structure

```text
tusic/
├── app/
│   ├── core/
│   │   ├── api.py        # ytmusicapi wrapper and search logic
│   │   ├── database.py   # SQLite logic for History and Playlists
│   │   ├── player.py     # python-mpv audio engine
│   │   └── resolver.py   # yt-dlp stream extraction
│   ├── ui/
│   │   └── styles.css    # Textual stylesheet (Black background, solid borders)
│   └── main.py           # Main Textual App, UI layout, and Event Loop
├── venv/                 # Python Virtual Environment
└── README.md
```

## Roadmap / TODO
- [x] Grid Layout
- [x] Local SQLite History & Playlists
- [x] Dynamic "Made For You" Curation
- [x] Pywal Color Injection
- [x] Timestamps can be seen
- [x] Windows for search results and song recommendations to play next in "Up Next".
- [x] Auto-play functionality (play next song from "Up Next" when current finishes)
- [ ] going back and forward in song timeline.
