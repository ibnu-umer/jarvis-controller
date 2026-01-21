import subprocess, os, requests
from pathlib import Path
from core.base_module import BaseModule
from core.registry import file_registry, action
from difflib import SequenceMatcher




class VLCController(BaseModule):
    def __init__(self):
        self.file_registry = file_registry
        self.vlc_url = "http://127.0.0.1:8080"
        self.vlc_password = "user"
        self.videos_folder_path = r"D:\user\Videos"


    def _vlc_request(self, command: str, **params):
        try:
            auth = ("", self.vlc_password) if self.vlc_password else None
            r = requests.get(
                f"{self.vlc_url}/requests/status.xml",
                params={"command": command, **params},
                auth=auth,
                timeout=2
            )
            return r.ok
        except Exception:
            return False


    # ------------------------- OPEN / PLAY ------------------------- #

    @action(name="open_vlc", params={"folder_name", "folder_path"})
    def open_vlc(self, folder_name=None, folder_path=None):
        """Launch VLC without media."""
        vlc_path = [self.file_registry.get_path("vlc")]

        if folder_name:
            choices = list(entry.name for entry in os.scandir(self.videos_folder_path))
            match_folder = self.best_match(folder_name, choices)
            folder_path = Path(self.videos_folder_path) / match_folder if match_folder else None

            if folder_path:
                vlc_path.append(str(folder_path))

        
        if folder_name and not folder_path:
            return self.success("No matching folder found to load")

        try:
            subprocess.Popen(vlc_path)
            return self.success("VLC opened")
        except Exception as e:
            return self.failure("Failed to open VLC", data={"error": str(e)})
            


    @action(name="play_media", params={"path", "path_name"})
    def play_media(self, path: str = None, path_name: str = None):
        """Play file or folder in VLC."""
        try:
            vlc_path = self.file_registry.get_path("vlc")
            if path_name:
                path = self.file_registry.get_path(path_name)
            path = Path(path).expanduser().resolve()

            if not path.exists():
                return self.failure("Media path does not exist")

            subprocess.Popen([vlc_path, str(path)])
            return self.success("Media started", data={"path": str(path)})
        except Exception as e:
            return self.failure("Failed to play media", data={"error": str(e)})


    # ------------------------- PLAYBACK CONTROLS ------------------------- #

    @action(name="vlc_play_pause")
    def play_pause(self):
        return self.success("Toggled play/pause") if self._vlc_request("pl_pause") else self.failure("VLC not responding")


    @action(name="vlc_stop")
    def stop(self):
        return self.success("Stopped") if self._vlc_request("pl_stop") else self.failure("VLC not responding")


    @action(name="vlc_next")
    def next(self):
        return self.success("Next track") if self._vlc_request("pl_next") else self.failure("VLC not responding")


    @action(name="vlc_prev")
    def previous(self):
        return self.success("Previous track") if self._vlc_request("pl_previous") else self.failure("VLC not responding")


    # ------------------------- SEEK / VOLUME / SPEED ------------------------- #

    @action(name="vlc_seek", params={"seconds"})
    def seek(self, seconds: int):
        return self.success("Seeked") if self._vlc_request("seek", val=seconds) else self.failure("Seek failed")


    @action(name="vlc_volume", params={"level"})
    def volume(self, level: int):
        """
        VLC volume: 0–512
        """
        return self.success("Volume set") if self._vlc_request("volume", val=level) else self.failure("Volume failed")


    @action(name="vlc_rate", params={"rate"})
    def rate(self, rate: float):
        return self.success("Playback rate set") if self._vlc_request("rate", val=rate) else self.failure("Rate change failed")


    # ------------------------- MODES ------------------------- #

    @action(name="vlc_fullscreen")
    def fullscreen(self):
        return self.success("Fullscreen toggled") if self._vlc_request("fullscreen") else self.failure("Fullscreen failed")


    @action(name="vlc_loop")
    def loop(self):
        return self.success("Loop toggled") if self._vlc_request("pl_loop") else self.failure("Loop failed")


    @action(name="vlc_random")
    def random(self):
        return self.success("Random toggled") if self._vlc_request("pl_random") else self.failure("Random failed")



    # ------------- HELPERS ------------------ #
    def best_match(self, query, choices, min_score=0.6):

        def similarity(a, b):
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()
        
        def token_score(a, b):
            a_tokens = set(a.lower().split())
            b_tokens = set(b.lower().split())
            return len(a_tokens & b_tokens) / max(len(a_tokens), 1)


        scored = []
        for c in choices:
            score = (
                0.6 * similarity(query, c) +
                0.4 * token_score(query, c)
            )
            scored.append((score, c))

        score, match = max(scored)
        return match if score >= min_score else None
