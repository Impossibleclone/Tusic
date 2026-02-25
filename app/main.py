import os
import json
import random
import time
from collections import Counter
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Grid, Vertical, Horizontal, Container
from textual.widgets import Input, Label, DataTable, ProgressBar, OptionList, ContentSwitcher
from textual.binding import Binding
from textual.screen import ModalScreen
from textual import work

from core.api import TusicAPI
from core.resolver import StreamResolver
from core.database import Database

import locale
locale.setlocale(locale.LC_ALL, 'C')
locale.setlocale(locale.LC_NUMERIC, 'C')
from core.player import Player

class HelpScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "dismiss", "Close Help"),
        Binding("q", "dismiss", "Close Help"),
        Binding("?", "dismiss", "Close Help"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help_dialog"):
            yield Label("Tusic Keybindings", id="help_title")
            
            yield Label(" Navigation ", classes="help_header")
            yield Label("h / l : Focus Sidebar / Songs\nH / L : View Search / View Up Next\nj / k : Move up / down", classes="help_text")
            
            yield Label(" Playback ", classes="help_header")
            yield Label("Space : Play / Pause\nn : Next Track\n+ / - : Volume Control", classes="help_text")
            
            yield Label(" General ", classes="help_header")
            yield Label("/ : Search\ns : Save to Playlist\nd : Delete from Playlist\nr : Refresh Recommendations", classes="help_text")
            
            yield Label("Press Escape or ? to close", id="help_footer")

    def on_mount(self) -> None:
        primary_color = self.app.pywal_colors.get("color6", "#B5EAD7")
        self.query_one("#help_dialog").styles.border = ("solid", primary_color)
        for header in self.query(".help_header"):
            header.styles.color = primary_color

    def action_dismiss(self) -> None:
        self.app.pop_screen()

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
        Binding("H", "show_search_view", "Search View", show=False),
        Binding("L", "show_up_next_view", "Up Next View", show=False),
        Binding("j", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("/", "focus_search", "Search"),
        Binding("escape", "blur_search", "Normal Mode", show=False),
        Binding("space", "play_pause", "Play/Pause"),
        Binding("r", "refresh_recommendations", "Refresh Mix", show=False),
        Binding("n", "play_next", "Next Track", show=False),
        Binding("s", "save_song", "Save Song", show=False),
        Binding("d", "remove_song", "Remove Song", show=False), 
        Binding("?", "show_help", "Help", show=False),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.user_config = self.load_config()
        self.pywal_colors = self.load_pywal()
        self.api = TusicAPI()
        self.resolver = StreamResolver()
        self.db = Database()
        
        self.player = Player()
        self.player.on_track_end = self.trigger_next_song

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
                yield OptionList("Made For You", "Recently Played", "My Playlist", id="library_menu")

            with Container(id="main_content"):
                with ContentSwitcher(initial="search_table", id="table_switcher"):
                    yield DataTable(id="search_table", cursor_type="row")
                    yield DataTable(id="up_next_table", cursor_type="row")

            with Vertical(id="player_bar"):
                yield Label("🎵 Nothing playing", id="track_info")
                yield ProgressBar(total=100, show_eta=False, id="progress_bar")

    def on_mount(self) -> None:
        primary_color = self.pywal_colors.get("color6", "#B5EAD7")

        for element_id in ["#sidebar", "#main_content", "#player_bar", "#search_input", "#help_box"]:
            self.query_one(element_id).styles.border = ("solid", primary_color)

        self.query_one("#progress_bar").styles.color = primary_color
        self.query_one("#sidebar").border_title = "Library"
        self.query_one("#main_content").border_title = "Search Results"
        self.query_one("#player_bar").border_title = "Player"

        search_table = self.query_one("#search_table")
        search_table.add_columns("Title", "Artist", "Album", "Length")

        up_next_table = self.query_one("#up_next_table")
        up_next_table.add_columns("Title", "Artist", "Length")

        self.set_interval(1.0, self.update_progress)

        self.load_made_for_you()
        self.query_one("#search_table").focus()

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def load_made_for_you(self) -> None:
        history = self.db.get_history()
        
        if not history:
            query = "synthwave mix"
            self.notify("Welcome! Fetching some starter recommendations...")
        else:
            artists = []
            for song in history:
                if song['artist'] != "Unknown":
                    artists.extend([a.strip() for a in song['artist'].split(',') if a.strip()])
            
            if artists:
                top_artists = [artist for artist, count in Counter(artists).most_common(3)]
                query = f"{random.choice(top_artists)} radio"
                self.notify("Fetching recommendations based on your taste...")
            else:
                query = "synthwave mix"
                self.notify("Fetching top picks for you...")
                
        self.fetch_results(query)

    def action_focus_sidebar(self) -> None:
        self.query_one("#library_menu").focus()

    def action_focus_table(self) -> None:
        active_table_id = self.query_one("#table_switcher").current
        if active_table_id:
            self.query_one(f"#{active_table_id}").focus()

    def action_show_search_view(self) -> None:
        self.query_one("#table_switcher").current = "search_table"
        
        main_content = self.query_one("#main_content")
        
        # If the title was 'Up Next', we should probably reset it
        if main_content.border_title == "Up Next (Radio)":
            main_content.border_title = "Search Results"
            
        self.query_one("#search_table").focus()

    def action_show_up_next_view(self) -> None:
        if self.query_one("#up_next_table").row_count > 0:
            self.query_one("#table_switcher").current = "up_next_table"
            self.query_one("#main_content").border_title = "Up Next (Radio)"
            self.query_one("#up_next_table").focus()
        else:
            self.notify("Up Next queue is empty. Play a song first!", severity="warning")

    def action_move_down(self) -> None:
        if self.query_one("#search_table").has_focus:
            self.query_one("#search_table").action_cursor_down()
        elif self.query_one("#up_next_table").has_focus:
            self.query_one("#up_next_table").action_cursor_down()
        elif self.query_one("#library_menu").has_focus:
            self.query_one("#library_menu").action_cursor_down()

    def action_move_up(self) -> None:
        if self.query_one("#search_table").has_focus:
            self.query_one("#search_table").action_cursor_up()
        elif self.query_one("#up_next_table").has_focus:
            self.query_one("#up_next_table").action_cursor_up()
        elif self.query_one("#library_menu").has_focus:
            self.query_one("#library_menu").action_cursor_up()

    def action_focus_search(self) -> None:
        self.query_one("#search_input").focus()

    def action_blur_search(self) -> None:
        self.action_focus_table()

    def action_play_pause(self) -> None:
        if not hasattr(self, "current_track"):
            return
        is_paused = self.player.toggle_pause()
        status = "⏸️ Paused" if is_paused else "▶️ Playing"
        self.query_one("#track_info").update(f"{status}: {self.current_track}")

    def trigger_next_song(self) -> None:
        self.call_from_thread(self._do_play_next, True)

    def action_play_next(self) -> None:
        # Immediately disarm auto-play on the UI thread to prevent double-skips
        self.player.auto_play_enabled = False
        self._do_play_next(False)

    def _do_play_next(self, is_auto_play: bool) -> None:
        active_table_id = self.query_one("#table_switcher").current
        if not active_table_id:
            return
            
        table = self.query_one(f"#{active_table_id}")
        if not table.row_count:
            return

        next_row = table.cursor_coordinate.row + 1
        if next_row >= table.row_count:
            next_row = 0

        table.move_cursor(row=next_row)
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        video_id = row_key.value.split("||")[0]
        row_data = table.get_row(row_key)
        
        song_title = f"{row_data[0]} - {row_data[1]}"
        self.current_track = song_title
        
        self.db.add_to_history(video_id, row_data[0], row_data[1], row_data[-1])
        self.query_one("#track_info").update(f"⏳ Loading: {song_title}")
        
        self.play_track(video_id, song_title, manual_interrupt=not is_auto_play, fetch_radio=False)

    def action_save_song(self) -> None:
        active_table_id = self.query_one("#table_switcher").current
        if not active_table_id:
            return
            
        table = self.query_one(f"#{active_table_id}")
        if not table.has_focus:
            return
            
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            row_data = table.get_row(row_key)
            video_id = row_key.value.split("||")[0]
            
            self.db.add_to_playlist(video_id, row_data[0], row_data[1], row_data[-1])
            self.notify(f"Saved: {row_data[0]}")
        except Exception:
            pass
    def action_remove_song(self) -> None:
        active_table_id = self.query_one("#table_switcher").current
        table = self.query_one(f"#{active_table_id}")
        
        if not table.has_focus:
            return
            
        try:
            coord = table.cursor_coordinate
            row_key = table.coordinate_to_cell_key(coord).row_key
            row_data = table.get_row(row_key)
            video_id = str(row_key.value).split("||")[0]
            
            # Use the consolidated removal logic
            res1 = self.db.remove_song_completely(video_id)
            res2 = self.db.remove_by_title(row_data[0], row_data[1])
            
            if res1 or res2:
                self.notify(f"Permanently Removed: {row_data[0]}")
                table.remove_row(row_key)
            else:
                self.notify("Could not find record in DB", severity="error")
                
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
                
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value
        if not query.strip():
            return
            
        self.query_one("#main_content").border_title = f"Search: {query}"
        
        self.notify(f"Searching for: {query}...")
        event.input.value = ""
        self.action_blur_search() 
        self.fetch_results(query)

    @work(exclusive=True, thread=True)
    def fetch_results(self, query: str) -> None:
        results = self.api.search_songs(query)
        self.call_from_thread(self.update_search_table, results)

    def update_search_table(self, results: list, reset_title: bool = True) -> None:
        # Only switch to search view if we aren't already there
        self.query_one("#table_switcher").current = "search_table"
        
        if reset_title:
            self.query_one("#main_content").border_title = "Search Results"
            
        table = self.query_one("#search_table")
        table.clear()
        for idx, song in enumerate(results):
            unique_key = f"{song['id']}||{idx}"
            table.add_row(song['title'], song['artist'], "Unknown", song['duration'], key=unique_key)
        self.action_focus_table()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.player.auto_play_enabled = False
        video_id = event.row_key.value.split("||")[0]
        row_data = event.control.get_row(event.row_key)
        song_title = f"{row_data[0]} - {row_data[1]}"
        self.current_track = song_title
        
        self.db.add_to_history(video_id, row_data[0], row_data[1], row_data[-1])
        self.query_one("#track_info").update(f"⏳ Loading: {song_title}")

        should_fetch_radio = (event.control.id == "search_table")
        self.play_track(video_id, song_title, manual_interrupt=True, fetch_radio=should_fetch_radio)

    @work(exclusive=True, thread=True)
    def play_track(self, video_id: str, song_title: str, manual_interrupt: bool = True, fetch_radio: bool = False) -> None:
        self.player.auto_play_enabled = False
        
        try:
            if manual_interrupt:
                self.player.stop()
                
            stream_url = self.resolver.get_stream_url(video_id)
            
            if stream_url:
                self.player.play(stream_url)
                self.call_from_thread(self.set_now_playing, song_title)
                
                if fetch_radio:
                    self.call_from_thread(self.fetch_radio, video_id)
            else:
                self.call_from_thread(self.notify, "Failed to resolve stream.", severity="error")
        finally:
            time.sleep(1.0)
            self.player.auto_play_enabled = True

    @work(exclusive=True, thread=True)
    def fetch_radio(self, video_id: str) -> None:
        self.call_from_thread(self.notify, "Generating Up Next radio...")
        results = self.api.get_radio_songs(video_id)
        self.call_from_thread(self.populate_up_next, results)

    def populate_up_next(self, results: list) -> None:
        table = self.query_one("#up_next_table")
        table.clear()
        
        if not results:
            self.notify("YouTube could not generate a radio for this track.", severity="warning")
            return
            
        if len(results) == 1 and "error" in results[0]:
            self.notify(f"API Error: {results[0]['error']}", severity="error")
            return
            
        for idx, song in enumerate(results):
            unique_key = f"{song['id']}||{idx}"
            table.add_row(song['title'], song['artist'], song['duration'], key=unique_key)
        
        self.action_show_up_next_view()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        selected_menu = str(event.option.prompt)
        self.query_one("#main_content").border_title = selected_menu
        
        if selected_menu == "Made For You":
            # Just switch the view, don't trigger a new fetch
            self.action_show_search_view()
        elif selected_menu == "Recently Played":
            self.update_search_table(self.db.get_history(), reset_title=False)
        elif selected_menu == "My Playlist":
            self.update_search_table(self.db.get_playlist(), reset_title=False)

    def action_refresh_recommendations(self) -> None:
        # This is the ONLY place that triggers a new 'Made For You' fetch
        self.notify("Refreshing your mix...")
        self.query_one("#main_content").border_title = "Made For You"
        self.load_made_for_you()

    def set_now_playing(self, song_title: str) -> None:
        self.query_one("#track_info").update(f"▶️ Playing: {song_title}")
        self.query_one("#player_bar").border_title = "Playing"

    def update_progress(self) -> None:
        if not hasattr(self, "current_track"):
            return
            
        try:
            current_time = self.player.time_pos
            duration = self.player.duration
            
            if duration > 0:
                progress_widget = self.query_one("#progress_bar")
                progress_widget.update(total=duration, progress=current_time)
                
                cur_m, cur_s = divmod(int(current_time), 60)
                dur_m, dur_s = divmod(int(duration), 60)
                time_str = f"[{cur_m:02d}:{cur_s:02d} / {dur_m:02d}:{dur_s:02d}]"
                
                status = "⏸️ Paused" if self.player.mpv.pause else "▶️ Playing"
                self.query_one("#track_info").update(f"{status} {time_str} : {self.current_track}")
            
            # Check if the player is permanently idle, not just a split-second EOF flash
            if self.player.is_idle and self.player.auto_play_enabled:
                # Immediately disarm the tripwire so it doesn't double-skip
                self.player.auto_play_enabled = False 
                
                # Trigger the next song internally, passing True for auto-play!
                self._do_play_next(is_auto_play=True)
                
        except Exception:
            pass

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = TusicApp()
    app.run()
