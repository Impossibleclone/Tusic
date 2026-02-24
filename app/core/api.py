from ytmusicapi import YTMusic

class TusicAPI:
    def __init__(self):
        self.ytm = YTMusic()

    def search_songs(self, query: str, limit: int = 1) -> list[dict]:
        """Searches the public YouTube Music catalog."""
        raw_results = self.ytm.search(query, filter="songs", limit=limit)
        
        songs = []
        for r in raw_results:
            songs.append({
                "id": r["videoId"],
                "title": r["title"],
                "artist": ", ".join([a["name"] for a in r["artists"]]),
                "duration": r.get("duration", "N/A")
            })
        return songs
