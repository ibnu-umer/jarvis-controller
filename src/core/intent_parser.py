from dataclasses import dataclass, field
from typing import Any, Dict, Tuple
from pathlib import Path
import joblib, re, datetime, pytz, numpy

from core.logger import logger
from core.intent_classifier import classify_intent, KEYWORD_VALUES, MODE_PATTERNS, IntentClassifier
from core.templates import TEMPLATE_REGISTRY
from core.registry import file_registry, module_registry
from core.patterns import WHEN_PATTERNS





@dataclass
class Intent:
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


class IntentParser:
    CONF_THRESHOLD = 0.3
    EXECUTABLE_SUFFIXES = {".exe", ".com", ".bat", ".cmd", ".msi"}
    
    intent_model = joblib.load("models/intent_predictor_model.pkl")
    vectorizer = joblib.load("models/vectorizer.pkl")
    label_encoder = joblib.load("models/label_encoder.pkl")


    def parse_intent(self, user_input: str):
        pred_intent, conf = self.predict_intent(user_input)
        logger.info(f"Predicted: {pred_intent} | Confidence: {int(conf*100)}")

        if conf > 0.30:

            if pred_intent == "open":
                action, args = self._handle_open(user_input)
                return Intent(action, params=args)
            
            if pred_intent == "close":
                app, _ = self._match_registry_key(user_input, app=True)
                return Intent("close_app", params={"app_name": app})
            
            if pred_intent == "brightness" or pred_intent == "volume":
                mode, value = None, None
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

                return Intent(
                    pred_intent,
                    params={"value": value, "mode": mode[:3]}
                )
            
            if pred_intent == "battery_status":
                get = "level"

                if "plugged" in user_input and "level" not in user_input:
                    get = "is_plugged"
                elif "status" in user_input:
                    get = "status"
                return Intent("get_battery_status", params={"get": get})
                
            if pred_intent in ("get_date", "get_time", "get_day"):
                get = pred_intent.split("_")[-1]
                day = "today"
                if "yesterday" in user_input:
                    day = "yesterday"
                elif "tomorrow" in user_input:
                    day = "tomorrow"
                return Intent("get_datetime", params={"get": get, "day": day})

            if pred_intent in ("shutdown", "sleep", "lock", "logout", "restart"):
                return Intent(pred_intent)

            if pred_intent == "reminder":
                when = self.extract_when(user_input)
                if when:
                    return Intent("set_reminder", params={"user_input": user_input, "when_data": when})

        return Intent("fallback")


        # if all(w in user_input for w in ("start", "work")) or all(w in user_input for w in ("prepare", "work")):
        #     return TEMPLATE_REGISTRY.get("prepare_work_environment")
        
        # if "watch" in user_input and any(w in user_input for w in ("movie", "anime")):
        #     graph = TEMPLATE_REGISTRY.get("setup_video_player")
        #     graph["params"] = {"folder_name": "anime" if "anime" in user_input else "movie"}
        #     return graph
        
        # if all(w in user_input for w in ("open", "copied", "path")):
        #     return TEMPLATE_REGISTRY.get("open_copied_path")

        

        # return Intent("fallback")

    
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
        return Intent("set_reminder", params={"user_input": user_input})


    # ---------------- Intent Handlers ----------------

    def _handle_open(self, text: str):
        file_key, file_path = self._match_registry_key(text)
        if not file_key:
            return "fallback"

        if file_path.startswith(("http://", "https://")):
            return "open_app", {"app_name": file_key}

        path = Path(file_path)

        if path.is_dir():
            return "open_folder", {"folder_name": file_key}

        if path.is_file():
            if path.suffix.lower() in self.EXECUTABLE_SUFFIXES:
                if "new" in text:
                    return "open_app", {"app_name": file_key}
                return "open_focus_app", {"app_name": file_key}
            return "open_file", {"file_name": file_key}

        return "fallback"
    

    def extract_when(self, user_input: str):
        text = user_input.lower().strip()

        for kind, pattern in WHEN_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue

            args = match.groupdict()

            # ---- validation for time-like patterns ----
            if kind in {"at_time", "dot_time", "space_time", "weekday_time", "date_time"}:
                hour = args.get("hour")
                minute = args.get("minute") or "0"

                if hour is not None:
                    hour = int(hour)
                    minute = int(minute)

                    if not (0 <= hour <= 23 and 0 <= minute <= 59):
                        continue  # invalid time → ignore match

            # ---- validation for relative duration ----
            # if kind == "after":
            #     print(match)
            #     value = int(args.get("value", 0))
            #     if value <= 0:
            #         continue

            return {
                "type": kind,
                "raw": match.group(0),
                "args": args,
            }

        return None




    # ---------------- Helpers ----------------

    def _match_registry_key(self, text: str, app=False) -> str | None:
        name, path = file_registry.match_key(text)
        if app and not path.endswith(".exe"):
            return None, None
        return name, path
    
   
    # ---------------- ML Model ----------------

    def predict_intent(self, text: str):
        X = self.vectorizer.transform([text])
        scores = self.intent_model.decision_function(X)[0]    
        pred_idx = scores.argmax()
        pred_label = self.label_encoder.inverse_transform([pred_idx])[0]
        confidence = 1 / (1 + numpy.exp(-scores[pred_idx]))

        return pred_label, float(confidence)
    


