import locale

locale.setlocale(locale.LC_NUMERIC, "C")

import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, ListView, ListItem, Label
from textual.binding import Binding
from textual import work

from core.api import TusicAPI
from core.resolver import StreamResolver
from core.player import Player


class TusicApp(App):
    """A Vim-driven TUI for streaming music."""
    ENABLE_COMMAND_PALETTE = False

    # Load the external stylesheet
    CSS_PATH = "ui/styles.css"

    # ⌨️ Global Vim Keymap
    BINDINGS = [
        Binding("j", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("g", "move_top", "Top", show=False),
        Binding("G", "move_bottom", "Bottom", show=False),
        Binding("/", "toggle_search", "Search", show=False),
        Binding("escape", "blur_search", "Normal Mode", show=False),
        Binding("space", "play_pause", "Play/Pause", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.api = TusicAPI()
        self.resolver = StreamResolver()
        self.player = Player()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield ListView(id="track_list")
        yield Input(placeholder="Search Tusic...", id="search_input")

    # --- Vim Action Handlers ---
    def action_move_down(self) -> None:
        self.query_one("#track_list").action_cursor_down()

    def action_move_up(self) -> None:
        self.query_one("#track_list").action_cursor_up()

    def action_move_top(self) -> None:
        self.query_one("#track_list").index = 0

    def action_move_bottom(self) -> None:
        track_list = self.query_one("#track_list")
        track_list.index = len(track_list.children) - 1

    def action_toggle_search(self) -> None:
        search_bar = self.query_one("#search_input")
        search_bar.add_class("-active")
        search_bar.focus()

    def action_blur_search(self) -> None:
        search_bar = self.query_one("#search_input")
        search_bar.remove_class("-active")
        search_bar.value = ""
        self.query_one("#track_list").focus()

    def action_play_pause(self) -> None:
        is_paused = self.player.toggle_pause()
        state = "Paused" if is_paused else "Playing"
        self.notify(f"Playback {state}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Fired when user submits a search query."""
        query = event.value
        self.notify(f"Searching for: {query}...")
        self.action_blur_search()
        self.fetch_results(query)

    @work(exclusive=True, thread=True)
    def fetch_results(self, query: str) -> None:
        """Background worker for YouTube Music API."""
        results = self.api.search_songs(query)
        self.call_from_thread(self.update_list, results)

    def update_list(self, results: list) -> None:
        """Safely updates the UI thread with search results."""
        track_list = self.query_one("#track_list")
        track_list.clear()

        for idx, song in enumerate(results, 1):
            label = f"{idx}. {song['title']} - {song['artist']} [{song['duration']}]"
            # The 'id' of the ListItem contains the video ID prefixed with 'song_'
            track_list.append(ListItem(Label(label), id=f"song_{song['id']}"))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Fired when user hits Enter on a track in the list."""
        # Extract the video ID from the ListItem's ID (e.g., "song_dQw4w9WgXcQ" -> "dQw4w9WgXcQ")
        video_id = event.item.id.replace("song_", "")
        self.notify("Resolving stream... (this takes a second)")
        self.play_track(video_id)

    @work(exclusive=True, thread=True)
    def play_track(self, video_id: str) -> None:
        """Background worker to extract stream and play audio."""
        stream_url = self.resolver.get_stream_url(video_id)
        # We can call the player directly from the thread since python-mpv handles its own C-thread
        self.player.play(stream_url)
        self.call_from_thread(self.notify, "Playing track!")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = TusicApp()
    app.run()
