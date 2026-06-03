import re
from datetime import date, datetime


DATE_FORMAT = "%d.%m.%Y"


def validate_phone(value: str) -> str:
    if not value.isdigit() or len(value) != 10:
        raise ValueError("Phone number must be 10 digits")
    return value


def parse_birthday(value: str | date) -> date:
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError:
        raise ValueError("Invalid date format. Use DD.MM.YYYY")


def validate_email(value: str) -> str:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(pattern, value):
        raise ValueError("Invalid email format.")
    return value


def normalize_query(value: str) -> str:
    return value.lower().lstrip("#")


def split_text_and_tags(parts: list[str]) -> tuple[str, list[str]]:
    text_parts = []
    tags = []
    for part in parts:
        if part.startswith("#"):
            tags.append(part[1:])
        else:
            text_parts.append(part)
    return " ".join(text_parts), tags
