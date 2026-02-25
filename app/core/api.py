from ytmusicapi import YTMusic

class TusicAPI:
    def __init__(self):
        self.ytmusic = YTMusic()

    def search_songs(self, query: str) -> list:
        try:
            results = self.ytmusic.search(query, filter="songs", limit=50)
            tracks = []
            for item in results:
                artists = ", ".join([a['name'] for a in item.get('artists', [])])
                tracks.append({
                    'id': item['videoId'],
                    'title': item['title'],
                    'artist': artists,
                    'duration': item.get('duration', 'Unknown')
                })
            return tracks
        except Exception:
            return []

    def get_radio_songs(self, video_id: str) -> list:
        try:
            # The RDAMVM prefix forces YouTube to generate an endless algorithmic radio mix
            playlist = self.ytmusic.get_watch_playlist(videoId=video_id, playlistId=f"RDAMVM{video_id}")
            tracks = []
            
            for item in playlist.get('tracks', []):
                current_id = item.get('videoId')
                
                if not current_id or current_id == video_id:
                    continue 
                
                artists_list = item.get('artists', [])
                artists = ", ".join([a['name'] for a in artists_list if 'name' in a]) if artists_list else "Unknown Artist"
                
                tracks.append({
                    'id': current_id,
                    'title': item.get('title', 'Unknown Title'),
                    'artist': artists,
                    'duration': item.get('length', 'Unknown')
                })
            return tracks
        except Exception as e:
            # Pass the error string back so the UI can display it
            return [{"error": str(e)}]
