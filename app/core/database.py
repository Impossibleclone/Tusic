import sqlite3
from pathlib import Path

class Database:
    def __init__(self):
        self.db_dir = Path.home() / ".local" / "share" / "tusic"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        # Keep the full path to the .db file
        self.db_path = self.db_dir / "tusic.db"
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.setup_tables()

    def setup_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                title TEXT,
                artist TEXT,
                duration TEXT,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlist (
                video_id TEXT PRIMARY KEY,
                title TEXT,
                artist TEXT,
                duration TEXT
            )
        """)
        self.conn.commit()

    def add_to_history(self, video_id, title, artist, duration):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO history (video_id, title, artist, duration) VALUES (?, ?, ?, ?)",
            (video_id, title, artist, duration)
        )
        self.conn.commit()

    def get_history(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT video_id, title, artist, duration FROM history ORDER BY played_at DESC LIMIT 50")
        return [{"id": row[0], "title": row[1], "artist": row[2], "duration": row[3]} for row in cursor.fetchall()]

    def add_to_playlist(self, video_id, title, artist, duration):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO playlist (video_id, title, artist, duration) VALUES (?, ?, ?, ?)",
            (video_id, title, artist, duration)
        )
        self.conn.commit()

    def get_playlist(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT video_id, title, artist, duration FROM playlist")
        return [{"id": row[0], "title": row[1], "artist": row[2], "duration": row[3]} for row in cursor.fetchall()]

    # FIX: Use self.conn instead of opening a new connection to a directory path
    def remove_from_playlist(self, video_id: str) -> bool:
        try:
            cursor = self.conn.cursor()
            clean_id = video_id.strip()
            cursor.execute("DELETE FROM playlist WHERE video_id = ?", (clean_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"DEBUG DB: {e}") 
            return False

    def remove_song_completely(self, video_id: str) -> bool:
        try:
            cursor = self.conn.cursor()
            clean_id = video_id.strip()
            
            cursor.execute("DELETE FROM playlist WHERE video_id = ?", (clean_id,))
            p_deleted = cursor.rowcount
            
            cursor.execute("DELETE FROM history WHERE video_id = ?", (clean_id,))
            h_deleted = cursor.rowcount
            
            self.conn.commit()
            return (p_deleted + h_deleted) > 0
        except Exception as e:
            print(f"DB Error: {e}")
            return False

    def remove_by_title(self, title: str, artist: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM playlist WHERE title = ? AND artist = ?", (title, artist))
            p_deleted = cursor.rowcount
            
            cursor.execute("DELETE FROM history WHERE title = ? AND artist = ?", (title, artist))
            h_deleted = cursor.rowcount
            
            self.conn.commit()
            return (p_deleted + h_deleted) > 0
        except Exception:
            return False
