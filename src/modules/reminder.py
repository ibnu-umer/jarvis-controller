import json
import uuid, re
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

from core.base_module import BaseModule
from core.registry import action
from configs.config import REMINDERS_PATH
from core.logger import logger



class Reminder(BaseModule):
    def __init__(self):
        self.path = REMINDERS_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.trigger = None

        if not self.path.exists():
            self.path.write_text("[]")

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread.start()


    def set_trigger(self, func):
        self.trigger = func


    # ---------- STORE -----------

    @action("load_reminders")
    def load_reminders(self):
        with self._lock:
            text = self.path.read_text().strip()
            if not text:
                return []
            return json.loads(text)


    def add_reminder(self, message: str, when: datetime) -> dict:
        with self._lock:
            reminders = self.load_reminders()
            reminder = {
                "id": str(uuid.uuid4()),
                "message": message,
                "when": when.isoformat(),
                "done": False,
            }
            reminders.append(reminder)
            self.path.write_text(json.dumps(reminders, indent=2))
            return reminder


    def mark_reminder_done(self, reminder_id: str):
        with self._lock:
            reminders = self.load_reminders()
            for r in reminders:
                if r["id"] == reminder_id:
                    r["done"] = True
            self.path.write_text(json.dumps(reminders, indent=2))


    # ---------- HELPERS ----------

    def resolve_when(self, when_data: dict) -> datetime:
        now = datetime.now()
        kind = when_data["type"]
        args = when_data["args"]

        if kind == "after":
            hours = int(args.get("hours") or 0)
            minutes = int(args.get("minutes") or 0)
            
            target = now + timedelta(hours=hours, minutes=minutes)
            tr_mins = target.strftime("%M")

            display_time = f"{target.hour % 12 or 12} {tr_mins if tr_mins != "00" else ""} {target.strftime('%p')}"
            return target, display_time

        if kind == "at_time":
            hour = int(args.get("hour") or 0)
            minute = int(args.get("minute") or 0)

            mer = args.get("meridiem")
            if mer == "pm" and hour != 12:
                hour += 12
            if mer == "am" and hour == 12:
                hour = 0

            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)

            tr_mins = target.strftime("%M")
            display_time = f"{target.hour % 12 or 12} {tr_mins if tr_mins != "00" else ""} {target.strftime('%p')}"
            return target, display_time

        raise ValueError(f"Unsupported reminder type: {kind}")
    

    def resolve_message(self, user_input, when_str):
        REMIND_MESSAGE_PATTERN = re.compile(
            r"""
            (?:remind\s+me\s+(?:to\s+)?)   # remind me / remind me to
            (?P<message>.*?)               # capture message lazily
            (?=\s+(?:at|after)\b|$)        # stop before time part or end
            """,
            re.IGNORECASE | re.VERBOSE
        )
        m = REMIND_MESSAGE_PATTERN.search(user_input)
        if not m:
            return f"its {when_str}, you told me to remind you"
        return f"its {when_str}, you told me to remind you to {m.group("message").strip()}"


    @action("set_reminder", params={"user_input", "when_data"})
    def set_reminder(self, user_input: str, when_data: dict):
        when, when_string = self.resolve_when(when_data)
        message = self.resolve_message(user_input, when_string)
        self.add_reminder(message, when)
        return self.success(f"reminder set at {when_string}")


    # ---------- SCHEDULER ----------

    def _run(self):
        while True:
            now = datetime.now()
            reminders = self.load_reminders()

            for r in reminders:
                if r["done"]:
                    continue

                when = datetime.fromisoformat(r["when"])
                if when <= now:
                    self.mark_reminder_done(r["id"])
                    self.on_trigger(r)

            self._stop_event.wait(1)


    def shutdown(self,timeout=5):
        self._stop_event.set()
        self._thread.join(timeout=timeout)
        logger.info("Reminder Thread shutting down")


    def on_trigger(self, result):
        if not self.trigger:
            logger.info("No Trigger funciton set for reminder")
            return
        self.trigger(result)
            



if __name__ == "__main__":
    def test_trigger(reminder):
        print("TRIGGERED:", reminder["message"])

    r = Reminder(on_trigger=test_trigger)

    r.set_reminder(
        "drink water",
        {
            "type": "after_minutes",
            "args": {"minutes": "1"}
        }
    )

    print("Reminder set. Waiting...")
    r._thread.join()