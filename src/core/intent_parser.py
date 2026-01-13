from dataclasses import dataclass, field
from typing import Any, Dict, Tuple
from pathlib import Path
import joblib, re, datetime, pytz

from core.logger import logger
from core.intent_classifier import classify_intent, KEYWORD_VALUES, MODE_PATTERNS
from core.templates import TEMPLATE_REGISTRY
from core.registry import file_registry, module_registry





@dataclass
class Intent:
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


class IntentParser:
    CONF_THRESHOLD = 0.3
    EXECUTABLE_SUFFIXES = {".exe", ".com", ".bat", ".cmd", ".msi"}


    def parse_action(self, user_input: str):
        if all(w in user_input for w in ("start", "work")) or all(w in user_input for w in ("prepare", "work")):
            return TEMPLATE_REGISTRY.get("prepare_work_environment")
        
        if "watch" in user_input and any(w in user_input for w in ("movie", "anime")):
            graph = TEMPLATE_REGISTRY.get("setup_video_player")
            graph["params"] = {"folder_name": "anime" if "anime" in user_input else "movie"}
            return graph
        
        if all(w in user_input for w in ("open", "copied", "path")):
            return TEMPLATE_REGISTRY.get("open_copied_path")

        if "open" in user_input:
            return self._handle_open(user_input)
        
        if "close" in user_input:
            app, _ = self._match_registry_key(user_input, app=True)
            return Intent("close_app", params={"app_name": app})

        if "brightness" in user_input or "volume" in user_input:
            mode = value = None
            for key, pattern in MODE_PATTERNS.items():
                if pattern.search(user_input):
                    mode = key

                    for key, val in KEYWORD_VALUES.items():
                        if key in user_input:
                            value = val

                    if not value:
                        value_match = re.compile(r"\b(\d{1,3})\b").search(user_input)
                        if value_match:
                            value = int(value_match.group(1))

            action = "brightness" if "brightness" in user_input else "volume"
            return Intent(
                action,
                params={"value": value, "mode": mode[:3]}
            )

        return Intent("fallback")

    
    def parse_query(self, user_input: str):
        if "time" in user_input or "date" in user_input:
            if all(w in user_input for w in ("time", "date")):
                get = "all"
            elif "time" in user_input:
                get = "time"
            else:
                get = "date"
            return Intent("get_datetime", params={"result": get})
            
        if "charge" in user_input or "battery" in user_input:
            if any(w in user_input for w in ("level", "percentage", "left")):
                get = "level"
            elif any(w in user_input for w in ("plugged", "charging")):
                get = "plugged"
            return Intent("get_battery_status", params={"result": get})

        return Intent("fallback")
    

    def parse_search(self, user_input: str):
        return Intent("search")
    

    def parse_reminder(self, user_input: str):
        return Intent("reminder")


    # ---------------- Intent Handlers ----------------

    def _handle_open(self, text: str, confidence: float=.5) -> Intent:
        file_key, file_path = self._match_registry_key(text)
        if not file_key:
            return Intent("fallback")

        if file_path.startswith(("http://", "https://")):
            return Intent("open_app", {"app_name": file_key}, confidence)

        path = Path(file_path)

        if path.is_dir():
            return Intent("open_folder", {"folder_name": file_key}, confidence)

        if path.is_file():
            if path.suffix.lower() in self.EXECUTABLE_SUFFIXES:
                return Intent("open_app", {"app_name": file_key}, confidence)
            return Intent("open_file", {"file_name": file_key}, confidence)

        return Intent("fallback")


    # ---------------- Helpers ----------------

    def _match_registry_key(self, text: str, app=False) -> str | None:
        name, path = file_registry.match_key(text)
        if app and not path.endswith(".exe"):
            return None, None
        return name, path
    
   
    # ---------------- ML Model ----------------

    def predict_intent(self, text: str) -> Tuple[str, float]:
        vect = self.vectorizer.transform([text])
        pred = self.intent_model.decision_function(vect)
        idx = pred.argmax()

        intent = self.label_encoder.inverse_transform([idx])[0]
        confidence = float(abs(pred[0][idx]))

        return intent, confidence


