import os
import json
import random
from collections import Counter
from pathlib import Path

try:
    import ctypes
    ctypes.CDLL('libc.so.6').setlocale(1, b'C')
except Exception:
    pass

from textual.app import App, ComposeResult
from textual.containers import Grid, Vertical, Horizontal, Container
from textual.widgets import Input, Label, DataTable, ProgressBar, OptionList
from textual.binding import Binding
from textual.screen import ModalScreen
from textual import work

from core.api import TusicAPI
from core.resolver import StreamResolver
from core.player import Player
from core.database import Database

class HelpScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "dismiss", "Close Help"),
        Binding("q", "dismiss", "Close Help"),
        Binding("?", "dismiss", "Close Help"),
    ]

    def compose(self) -> ComposeResult:
        with Grid(id="help_dialog"):
            yield Label("Tusic Keybindings", id="help_title")
            yield Label(" Navigation ", classes="help_header")
            yield Label("h / l : Switch between Library and Songs\nj / k : Move up/down lists", classes="help_text")
            yield Label(" Playback ", classes="help_header")
            yield Label("Space : Play / Pause", classes="help_text")
            yield Label(" General ", classes="help_header")
            yield Label("/ : Search\ns : Save highlighted song to Playlist\n? : Toggle Help\nq : Quit Tusic", classes="help_text")
            yield Label("\nPress Escape or ? to close", id="help_footer")

    def on_mount(self) -> None:
        primary_color = self.app.pywal_colors.get("color6", "#B5EAD7")
        self.query_one("#help_dialog").styles.border = ("solid", primary_color)
        for header in self.query(".help_header"):
            header.styles.color = primary_color

    def action_dismiss(self) -> None:
        self.app.pop_screen()


class TusicApp(App):
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = "ui/styles.css"

    BINDINGS = [
        Binding("h", "focus_sidebar", "Sidebar", show=False),
        Binding("l", "focus_table", "Table", show=False),
        Binding("j", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("/", "focus_search", "Search"),
        Binding("escape", "blur_search", "Normal Mode", show=False),
        Binding("space", "play_pause", "Play/Pause"),
        Binding("s", "save_song", "Save Song", show=False),
        Binding("?", "show_help", "Help", show=False),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.user_config = self.load_config()
        self.pywal_colors = self.load_pywal()
        self.api = TusicAPI()
        self.resolver = StreamResolver()
        self.player = Player()
        self.db = Database()

    def load_config(self) -> dict:
        config_path = Path.home() / ".config" / "tusic" / "config.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                return json.load(f)
        return {}

    def load_pywal(self) -> dict:
        wal_path = Path.home() / ".cache" / "wal" / "colors.json"
        if wal_path.exists():
            with open(wal_path, "r") as f:
                return json.load(f).get("colors", {})
        return {}

    def compose(self) -> ComposeResult:
        with Grid(id="main_grid"):
            with Horizontal(id="top_bar"):
                yield Input(placeholder="Search Tusic...", id="search_input")
                yield Label("Help\nType ?", id="help_box")
            
            with Vertical(id="sidebar"):
                yield OptionList(
                    "Made For You",
                    "Recently Played",
                    "My Playlist",
                    id="library_menu"
                )

            with Container(id="main_content"):
                yield DataTable(id="songs_table", cursor_type="row")

            with Vertical(id="player_bar"):
                yield Label("🎵 Nothing playing", id="track_info")
                yield ProgressBar(total=100, show_eta=False, id="progress_bar")

    def on_mount(self) -> None:
        primary_color = self.pywal_colors.get("color6", "#B5EAD7")

        for element_id in ["#sidebar", "#main_content", "#player_bar", "#search_input", "#help_box"]:
            self.query_one(element_id).styles.border = ("solid", primary_color)

        self.query_one("#progress_bar").styles.color = primary_color
        self.query_one("#sidebar").border_title = "Library"
        self.query_one("#main_content").border_title = "Songs"
        self.query_one("#player_bar").border_title = "Player"

        table = self.query_one("#songs_table")
        table.add_columns("Title", "Artist", "Album", "Length")
        
        # Load the default mix and focus the table on startup
        self.load_made_for_you()

    def load_made_for_you(self) -> None:
        history = self.db.get_history()
        
        if not history:
            self.notify("Play some songs first! Fetching default mix...")
            query = "synthwave mix"
        else:
            artists = []
            for song in history:
                if song['artist'] != "Unknown":
                    artists.extend([a.strip() for a in song['artist'].split(',') if a.strip()])
            
            if artists:
                top_artists = [artist for artist, count in Counter(artists).most_common(3)]
                chosen_artist = random.choice(top_artists)
                query = f"{chosen_artist} radio"
                self.notify(f"Curating mix based on: {chosen_artist}...")
            else:
                query = "synthwave mix"
                
        self.fetch_results(query) 
        self.action_focus_table()

    def action_focus_sidebar(self) -> None:
        self.query_one("#library_menu").focus()

    def action_focus_table(self) -> None:
        self.query_one("#songs_table").focus()

    def action_move_down(self) -> None:
        if self.query_one("#songs_table").has_focus:
            self.query_one("#songs_table").action_cursor_down()
        elif self.query_one("#library_menu").has_focus:
            self.query_one("#library_menu").action_cursor_down()

    def action_move_up(self) -> None:
        if self.query_one("#songs_table").has_focus:
            self.query_one("#songs_table").action_cursor_up()
        elif self.query_one("#library_menu").has_focus:
            self.query_one("#library_menu").action_cursor_up()

    def action_focus_search(self) -> None:
        self.query_one("#search_input").focus()

    def action_blur_search(self) -> None:
        self.query_one("#songs_table").focus()

    def action_play_pause(self) -> None:
        if not hasattr(self, "current_track"):
            return
            
        is_paused = self.player.toggle_pause()
        status = "⏸️ Paused" if is_paused else "▶️ Playing"
        self.query_one("#track_info").update(f"{status}: {self.current_track}")

    def action_save_song(self) -> None:
        table = self.query_one("#songs_table")
        if not table.has_focus:
            return
            
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            row_data = table.get_row(row_key)
            video_id = row_key.value
            
            self.db.add_to_playlist(video_id, row_data[0], row_data[1], row_data[3])
            self.notify(f"Saved: {row_data[0]}")
        except Exception:
            pass

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value
        self.notify(f"Searching for: {query}...")
        
        event.input.value = ""
        self.action_blur_search() 
        self.fetch_results(query)

    @work(exclusive=True, thread=True)
    def fetch_results(self, query: str) -> None:
        results = self.api.search_songs(query)
        self.call_from_thread(self.update_table, results)

    def update_table(self, results: list) -> None:
        table = self.query_one("#songs_table")
        table.clear()

        for song in results:
            table.add_row(
                song['title'], 
                song['artist'], 
                "Unknown", 
                song['duration'], 
                key=song['id'] 
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        video_id = event.row_key.value
        row_data = self.query_one("#songs_table").get_row(event.row_key)
        song_title = f"{row_data[0]} - {row_data[1]}"
        self.current_track = song_title
        
        self.db.add_to_history(video_id, row_data[0], row_data[1], row_data[3])
        
        self.query_one("#track_info").update(f"⏳ Loading: {song_title}")
        self.play_track(video_id, song_title)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        selected_menu = str(event.option.prompt)
        
        if selected_menu == "Made For You":
            self.load_made_for_you()
            
        elif selected_menu == "Recently Played":
            results = self.db.get_history()
            self.update_table(results)
            self.action_focus_table()
            
        elif selected_menu == "My Playlist":
            results = self.db.get_playlist()
            self.update_table(results)
            self.action_focus_table()

    @work(exclusive=True, thread=True)
    def play_track(self, video_id: str, song_title: str) -> None:
        stream_url = self.resolver.get_stream_url(video_id)
        self.player.play(stream_url)
        self.call_from_thread(self.set_now_playing, song_title)

    def set_now_playing(self, song_title: str) -> None:
        self.query_one("#track_info").update(f"▶️ Playing: {song_title}")
        self.query_one("#player_bar").border_title = "Playing"

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = TusicApp()
    app.run()
