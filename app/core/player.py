import locale

locale.setlocale(locale.LC_ALL, 'C')
locale.setlocale(locale.LC_NUMERIC, 'C')

import mpv

class Player:
    def __init__(self):
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.mpv = mpv.MPV(video=False, ytdl=False)
        self.auto_play_enabled = True

    def play(self, url: str):
        self.mpv.play(url)

    def stop(self):
        self.mpv.command('stop')

    def toggle_pause(self) -> bool:
        self.mpv.pause = not self.mpv.pause
        return self.mpv.pause

    @property
    def time_pos(self) -> float:
        try:
            return self.mpv.time_pos or 0.0
        except Exception:
            return 0.0

    @property
    def duration(self) -> float:
        try:
            return self.mpv.duration or 0.0
        except Exception:
            return 0.0

    @property
    def is_idle(self) -> bool:
        try:
            # 'idle_active' remains True whenever MPV is sitting empty after a song finishes
            return getattr(self.mpv, 'idle_active', True)
        except Exception:
            return True
