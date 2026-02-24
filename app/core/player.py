import locale

locale.setlocale(locale.LC_ALL, 'C')
locale.setlocale(locale.LC_NUMERIC, 'C')

import mpv

class Player:
    def __init__(self):
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.mpv = mpv.MPV(ytdl=False, video=False)

    def play(self, stream_url: str):
        self.mpv.play(stream_url)

    def toggle_pause(self):
        self.mpv.pause = not self.mpv.pause
        return self.mpv.pause
