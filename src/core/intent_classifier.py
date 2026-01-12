import re
from enum import Enum, auto


class IntentType(Enum):
    ACTION = auto()
    QUERY = auto()
    SEARCH = auto()
    TASK = auto()
    REMINDER = auto()
    REJECT = auto()


ACTION_VERBS = {
    "shutdown", "restart", "open", "close", "start", "create", "delete", "brightness", "volume", "watch"
}

INTERNAL_DOMAINS = {
    "charge", "battery", "time", "date"
}

TASK_CONNECTORS = {
    "and", "then", "after", "before", "also", "if", "when"
}

QUESTION_STARTS = (
    "what is", "what's", "whats", "show me", "tell me",
    "check", "get", "who", "which", "why", "how"
)

REMINDER_KEYWORDS = {
    "remind", "reminder", "remember", "notify", "alert"
}

TIME_PATTERNS = [
    r"\b(at|on|in|after)\s+\d+",          # at 5, in 10
    r"\b(tomorrow|today|tonight)\b",
    r"\b(am|pm)\b",
    r"\b\d{1,2}:\d{2}\b"            # 10:30
]

KEYWORD_VALUES = {
    "mute": 0, "silent": 0,
    "half": 50, "medium": 50,
    "full": 100, "max": 100
}

MODE_PATTERNS = {
    "increase": re.compile(r"\b(increase|raise|up|boost|higher|more|louder|brighter)\b", re.I),
    "decrease": re.compile(r"\b(decrease|reduce|down|lower|less|quieter|dimmer)\b", re.I),
    "set": re.compile(r"\b(set|to|at|make)\b", re.I),
}


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def has_multiple_clauses(text: str) -> bool:
    for c in TASK_CONNECTORS:
        if f" {c} " in text:
            return True
    return False


def has_action_verb(text: str) -> bool:
    for v in ACTION_VERBS:
        if text.startswith(v) or f" {v} " in text:
            return True
    return False


def is_question(text: str) -> bool:
    return text.startswith(QUESTION_STARTS) or text.endswith("?")


def is_internal_domain(text: str) -> bool:
    for d in INTERNAL_DOMAINS:
        if d in text:
            return True
    return False

def has_reminder_intent(text: str) -> bool:
    if any(k in text for k in REMINDER_KEYWORDS):
        for p in TIME_PATTERNS:
            if re.search(p, text):
                return True
    return False


def classify_intent(text: str) -> IntentType:
    if not text or not text.strip():
        return IntentType.REJECT

    t = normalize(text)

    if not t:
        return IntentType.REJECT
    
    if has_reminder_intent(t):
        return IntentType.REMINDER

    if has_multiple_clauses(t):
        return IntentType.TASK

    if has_action_verb(t):
        return IntentType.ACTION

    if is_question(t) and is_internal_domain(t):
        return IntentType.QUERY

    return IntentType.SEARCH






if __name__ == "__main__":
    while True:
        user = input(">>>")
        intent_type = classify_intent(user)
        print(intent_type.name)
