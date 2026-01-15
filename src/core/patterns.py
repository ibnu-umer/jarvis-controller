import re


AFTER_PATTERN = re.compile(
    r"\bafter\s+"
    r"(?:(?P<hours>\d+)\s*(?:hour|hours))?\s*"
    r"(?:(?P<minutes>\d+)\s*(?:minute|minutes))?\b",
    re.IGNORECASE
)

AT_TIME_PATTERN = re.compile(
    r"(?:\bat\s+)?(?P<hour>\d{1,2})(?:[:.\s](?P<minute>\d{2}))?\s*(?P<meridiem>am|pm)\b",
    re.IGNORECASE
)

ON_DATE_TIME_PATTERN = re.compile(
    r"\bon\s+(?P<day>\d{1,2})\s+(?P<month>[a-zA-Z]+)\s+at\s+"
    r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<meridiem>am|pm)\b",
    re.IGNORECASE
)

ON_DATE_TIME_PATTERN = re.compile(
    r"\bon\s+(?P<day>\d{1,2})\s+(?P<month>[a-zA-Z]+)\s+at\s+"
    r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<meridiem>am|pm)\b",
    re.IGNORECASE
)

DAY_KEYWORD_PATTERN = re.compile(
    r"\b(today|tomorrow|tonight|this\s+evening|tomorrow\s+evening)\b",
    re.IGNORECASE
)

WEEKDAY_TIME_PATTERN = re.compile(
    r"\bon\s+(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
    r"\s+at\s+(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<meridiem>am|pm)\b",
    re.IGNORECASE
)

RELATIVE_DATE_PATTERN = re.compile(
    r"\b(next\s+month|this\s+weekend|next\s+week)\b",
    re.IGNORECASE
)

SPACE_SEP_TIME_PATTERN = re.compile(
    r"\b(?P<hour>\d{1,2})\s+(?P<minute>\d{2})\b"
)

DOT_SEP_TIME_PATTERN = re.compile(
    r"\b(?P<hour>\d{1,2})\.(?P<minute>\d{2})\b"
)


WHEN_PATTERNS = [
    ("date_time", ON_DATE_TIME_PATTERN),
    ("weekday_time", WEEKDAY_TIME_PATTERN),
    ("after", AFTER_PATTERN),
    ("at_time", AT_TIME_PATTERN),
    ("day_keyword", DAY_KEYWORD_PATTERN),
    ("relative_date", RELATIVE_DATE_PATTERN),
]