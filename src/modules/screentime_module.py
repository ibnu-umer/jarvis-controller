from core.registry import action
import threading
import time
import json
import os
from datetime import datetime, timedelta
import win32gui, win32process, win32api
import psutil
from configs.config import SCREENTIME_DATA, SCREENTIME_TIMEOUT, SCREENTIME_POLL_INTERVAL, SCREENTIME_SAVE_INTERVAL 
from core.base_module import BaseModule
from core.logger import logger






class ScreenTimeModule(BaseModule):
    def __init__(self):
        self.storage_path = SCREENTIME_DATA
        self.poll_interval = SCREENTIME_POLL_INTERVAL
        self._lock = threading.RLock()
        self._idle_timeout_seconds = SCREENTIME_TIMEOUT

        # runtime state
        self._watcher_thread = None
        self._watcher_stop = threading.Event()
        self._current_app = None  
        self._current_start = None  
        self._last_save = time.time()
        self._pid_cache = {}

        self.usage = {}
        os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
        self._load()
        self.start_tracking()


    # ----------------------- PERSISTANCE -----------------------
    def _load(self):
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.usage = json.load(f)
            else:
                self.usage = {}
        except Exception as e:
            self.usage = {}
            logger.error(f"Error loading screentime data: {e}")


    def _save(self):
        try:
            tmp = self.storage_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.usage, f, indent=2)
            os.replace(tmp, self.storage_path)
        except Exception as e:
            logger.error(f"Error while saving screentime data: {e}")

    # ----------------------- HELPERS -----------------------
    def _today_key(self):
        return datetime.now().strftime("%Y-%m-%d")
    

    def _week_keys(self):
        today = datetime.now().date()
        monday = today - timedelta(days=today.weekday())  

        keys = []
        for i in range(7):
            d = monday + timedelta(days=i)
            keys.append(d.strftime("%Y-%m-%d"))

        return keys
    

    def _month_keys(self):
        today = datetime.now().date()
        year, month = today.year, today.month

        keys = []
        day = 1

        while True:
            try:
                d = datetime(year, month, day).date()
                keys.append(d.strftime("%Y-%m-%d"))
                day += 1
            except ValueError:
                break

        return keys


    def _to_hms_str(self, s: int):
        h = s // 3600
        m = (s % 3600) // 60
        sec = s % 60
        return f"{h:02}:{m:02}:{sec:02}"


    def _add_seconds(self, app_name: str, seconds: float):

        key = self._today_key()
        with self._lock:
            day = self.usage.setdefault(key, {})
            day[app_name] = int(day.get(app_name, 0) + round(seconds))
            # self._save()


    def _get_foreground_process_name(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if not pid:
                return None

            if pid not in self._pid_cache:
                try:
                    self._pid_cache[pid] = psutil.Process(pid).name()
                except Exception:
                    self._pid_cache[pid] = None

            return self._pid_cache[pid]

        except Exception:
            return None
        

    # ----------------------- WATCHER LOGIC -----------------------
    def _watch_loop(self):
        is_tracking = False
        while not self._watcher_stop.is_set():
            try:
                idle = self._get_idle_seconds()
                now = time.time()
   
                if idle >= self._idle_timeout_seconds and self._current_app:
                    if self._current_app in ("vlc.exe"):
                        continue

                    if self._current_app and self._current_start:
                        elapsed = now - self._current_start
                        self._add_seconds(self._current_app, elapsed)
                        self._current_app = None
                        self._current_start = None
                    time.sleep(self.poll_interval)
                    continue

                proc_name = self._get_foreground_process_name()


                if proc_name and proc_name != self._current_app:
                    if self._current_app and self._current_start:
                        elapsed = now - self._current_start
                        self._add_seconds(self._current_app, elapsed)
                    self._current_app = proc_name
                    self._current_start = now

                if proc_name is None and self._current_app and self._current_start:
                    elapsed = now - self._current_start
                    self._add_seconds(self._current_app, elapsed)
                    self._current_app = None
                    self._current_start = None

                is_tracking = True

                now = time.time()
                if now - self._last_save >= SCREENTIME_SAVE_INTERVAL:
                    with self._lock:
                        self._save()
                    self._last_save = now

            except Exception as e:
                if is_tracking:
                    logger.error(f"Error while tracking screentime: {e}")
                    is_tracking = False

            time.sleep(self.poll_interval)


    def _start_watcher_thread(self):
        if self._watcher_thread and self._watcher_thread.is_alive():
            return
        self._watcher_stop.clear()
        self._watcher_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._watcher_thread.start()

    
    def _stop_watcher_thread(self):
        if not self._watcher_thread:
            return
        self._watcher_stop.set()
        self._watcher_thread.join(timeout=2)
        # flush any open session
        if self._current_app and self._current_start:
            elapsed = time.time() - self._current_start
            self._add_seconds(self._current_app, elapsed)
            self._current_app = None
            self._current_start = None


    def _get_idle_seconds(self):
        last_input_info = win32api.GetLastInputInfo()
        return (win32api.GetTickCount() - last_input_info) / 1000.0


    def start_tracking(self):
        """Start the background watcher that tracks focused application usage."""
        if not win32gui or not win32process or not psutil:
            return self.failure("Foreground tracking unavailable on this platform or missing dependencies")
        self._start_watcher_thread()
        logger.info("ScreenTime tracking started")


    def shutdown(self):
        self._watcher_stop.set()

        if self._watcher_thread and self._watcher_thread.is_alive():
            self._watcher_thread.join(timeout=3)

        now = time.time()
        with self._lock:
            if self._current_app and self._current_start:
                elapsed = now - self._current_start
                self._add_seconds(self._current_app, elapsed)
                self._current_app = None
                self._current_start = None

            self._save()
        logger.info("ScreenTime module shutting down")

    
    def get(self, date):
        date = date.strftime("%Y-%m-%d")
        return self.usage.get(date, {})
    

    # ----------------------- MODULE ACTIONS -----------------------
    @action(name="stop_screenusage_tracking")
    def stop_tracking(self):
        """Stop the watcher and flush current session to storage."""
        self._stop_watcher_thread()
        logger.info("ScreenTime tracking stopped")


    @action(name="get_daily_breakdown", params={"range"})
    def get_daily_breakdown(self, range="day"):

        if range == "day":
            keys = self._today_key()
        elif range == "week":
            keys = self._week_keys()
        elif range == "month":
            keys = self._month_keys()
        else:
            return self.failure("Invalid range, must be week/month")

        result = {}

        with self._lock:
            for key in keys:
                day_data = self.usage.get(key, {})
                per_day = []

                # Convert to sorted list
                sorted_items = sorted(
                    day_data.items(),
                    key=lambda x: x[1],
                    reverse=True
                )

                # Format each app into HMS
                for app, sec in sorted_items:
                    per_day.append({
                        "app": app,
                        "usage": self._to_hms_str(sec)
                    })

                result[key] = per_day
                range = f"{keys[0]} - {keys[-1]}"

        return self.success("Daily breakdown generated", data={"range": range, "breakdown": result})


    @action(name="get_raw_usage_today")
    def get_raw_usage_today(self):
        """Return a dict of application -> seconds for today."""
        key = self._today_key()
        with self._lock:
            day = dict(self.usage.get(key, {}))
            # include current running session if applicable
            if self._current_app and self._current_start:
                elapsed = int(round(time.time() - self._current_start))
                day[self._current_app] = day.get(self._current_app, 0) + elapsed
        return self.success(f"Fetched {key} screen usage data", data=day)
    

    @action(name="list_screentracked_apps")
    def list_tracked_apps(self):
        """Return a set/list of apps that have recorded usage (all-time)."""
        apps = set()
        with self._lock:
            for daydata in self.usage.values():
                apps.update(daydata.keys())
        return self.success("Listed Tracked apps", data=sorted(apps))
    

    @action(name="reset_todays_screentime")
    def reset_today(self):
        """Clear today's usage data."""
        key = self._today_key()
        with self._lock:
            if key in self.usage:
                self.usage.pop(key)
                self._save()
        return self.success("Today\'s usage cleared")
    
