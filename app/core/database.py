import sqlite3
from pathlib import Path

class Database:
    def __init__(self):
        self.db_path = Path.home() / ".local" / "share" / "tusic"
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path / "tusic.db", check_same_thread=False)
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
