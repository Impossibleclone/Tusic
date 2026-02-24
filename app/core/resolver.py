import yt_dlp

class StreamResolver:
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False, 
        }

    def get_stream_url(self, video_id: str) -> str:
        """Uses yt-dlp to get the direct audio stream."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['url']
