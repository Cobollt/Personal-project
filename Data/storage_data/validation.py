import re
from datetime import date, datetime
from difflib import get_close_matches
from typing import Callable, Optional

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
    except ValueError as error:
        raise ValueError("Invalid date format. Use DD.MM.YYYY") from error


def validate_email(value: str) -> str:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(pattern, value):
        raise ValueError("Invalid email format.")
    return value


def normalize_query(value: str) -> str:
    return value.lower().lstrip("#")


def split_text_and_tags(parts: list[str]) -> tuple[str, list[str]]:
    text_parts: list[str] = []
    tags: list[str] = []

    for part in parts:
        if part.startswith("#"):
            tags.append(part[1:])
        else:
            text_parts.append(part)

    return " ".join(text_parts), tags


def run_user_command(user_input: str, commands: dict[str, Callable[[list[str]], str]]) -> Optional[str]:
    """Parse user input and immediately execute the matching command."""
    parts = user_input.split()
    if not parts:
        return "Please enter a command."

    command = parts[0].strip().lower()
    args = parts[1:]

    action = commands.get(command)
    if action is None:
        suggestion = get_close_matches(command, list(commands.keys()), n=1, cutoff=0.4)
        return f"Did you mean: {suggestion[0]}?" if suggestion else "Invalid command."

    try:
        return action(args)
    except ValueError as error:
        return str(error)
    except KeyError:
        return "Not found."
    except IndexError:
        return "Not enough arguments. Check help."


def is_error_message(message: str) -> bool:
    errors = (
        "No contact",
        "No note",
        "Not found",
        "Phone not found",
        "Phone already exists",
        "Cannot delete",
        "Invalid",
        "Not enough",
        "Unknown",
        "Usage",
        "Address book is empty",
        "Notebook is empty",
        "Please enter",
    )
    return isinstance(message, str) and message.startswith(errors)
