from difflib import get_close_matches
from typing import Callable, Optional, NoReturn

try:
    from colorama import Fore
except ImportError:
    Fore = None

from .command_logic.model_logic import ModelLogic
from Data.storage_data.storage import Note, Record
from Data.storage_data.validation import split_text_and_tags


GRAY = getattr(Fore, "LIGHT" + "BLACK_EX", "") if Fore else ""


# ── Parser / Help ────────────────────────────────────────────────────────────

def parse_input(user_input: str) -> tuple[str, list[str]]:
    parts = user_input.split()
    if not parts:
        return "", []
    command, *args = parts
    return command.strip().lower(), args


def show_help() -> str:
    return f"""
{GRAY}----------
Available commands:

add [name] [phone] [birthday] [email] [address]
add note [title] [text] #tag
add note contact [name] [title] [text] #tag

update phone [name] [phone]
update phone [name] [old_phone] [new_phone]
update birthday [name] [DD.MM.YYYY]
update email [name] [email]
update address [name] [address]
update note [title] [new text] #tag
update note contact [name] [title] [new text] #tag

search contact [name|phone|birthday|email|address|all] [query]
search note [title|text|tag|all] [query]
search note contact [title|text|tag|all] [query]

show all
show notes
show birthdays [days]

delete contact [name]
delete phone [name] [phone]
delete birthday [name]
delete email [name]
delete address [name]
delete note [title]
delete note contact [name] [title]

help
close / exit
----------
"""


def suggest_command(user_input: str, commands: dict[str, Callable[[list[str]], str]]) -> Optional[str]:
    parts = user_input.split()
    if not parts:
        return None
    matches = get_close_matches(parts[0].lower(), list(commands.keys()), n=1, cutoff=0.4)
    return matches[0] if matches else None


# ── Errors / Helpers ─────────────────────────────────────────────────────────

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as error:
            return str(error)
        except KeyError:
            return "Not found."
        except IndexError:
            return "Not enough arguments. Check help."
    return inner


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
    )
    return isinstance(message, str) and message.startswith(errors)


def ask_optional(prompt: str) -> Optional[str]:
    user_value = input(prompt).strip()
    return user_value if user_value else None


def raise_value(message: str) -> NoReturn:
    raise ValueError(message)


def format_contacts(records: list[Record]) -> str:
    return "\n".join(str(record) for record in records) if records else "No contacts found."


def format_notes(notes: list[Note] | list[str]) -> str:
    return "\n".join(str(note) for note in notes) if notes else "No notes found."


class CommandHandler:
    def __init__(self, book, notebook):
        self.logic = ModelLogic(book, notebook)

        self.commands: dict[str, Callable[[list[str]], str]] = {
            "help": self.help,
            "add": self.add,
            "update": self.update,
            "search": self.search,
            "show": self.show,
            "delete": self.delete,
        }
        self.add_actions: dict[str, Callable[[list[str]], str]] = {
            "contact": self.add_contact,
            "note": self.add_note_router,
        }
        self.update_actions: dict[str, Callable[[list[str]], str]] = {
            "phone": self.update_phone,
            "birthday": lambda payload: self.update_contact_field(payload, "birthday"),
            "email": lambda payload: self.update_contact_field(payload, "email"),
            "address": lambda payload: self.update_contact_field(payload, "address"),
            "note": self.update_note_router,
        }
        self.search_actions: dict[str, Callable[[list[str]], str]] = {
            "contact": self.search_contacts,
            "note": self.search_note_router,
        }
        self.show_actions: dict[str, Callable[[list[str]], str]] = {
            "all": self.show_all_contacts,
            "notes": self.show_all_notes,
            "birthdays": self.show_birthdays,
        }
        self.delete_actions: dict[str, Callable[[list[str]], str]] = {
            "contact": self.delete_contact,
            "phone": lambda payload: self.delete_contact_data(payload, "phone"),
            "birthday": lambda payload: self.delete_contact_data(payload, "birthday"),
            "email": lambda payload: self.delete_contact_data(payload, "email"),
            "address": lambda payload: self.delete_contact_data(payload, "address"),
            "note": self.delete_note_router,
        }

    def execute(self, command: str, args: list[str]) -> Optional[str]:
        action = self.commands.get(command)
        if action is None:
            return None
        return action(args)

    @staticmethod
    def help(_args: Optional[list[str]] = None) -> str:
        return show_help()

    # ── ADD ─────────────────────────────────────────────────────────────────

    @input_error
    def add(self, args: list[str]) -> str:
        keyword = args[0] if args and args[0] == "note" else "contact"
        command_args = args if keyword == "contact" else args[1:]
        return self.add_actions[keyword](command_args)

    def add_contact(self, args: list[str]) -> str:
        if len(args) < 2:
            return "Usage: add [name] [phone] [birthday] [email] [address]"
        name, phone, *optional = args
        record = self.logic.book.data.get(name)
        message = "Contact updated."
        if record is None:
            record = Record(name)
            self.logic.add_record(record)
            message = "Contact added."
        self.logic.add_phone(record, phone)
        birthday = optional[0] if len(optional) > 0 else ask_optional("Birthday DD.MM.YYYY, Enter to skip: ")
        email = optional[1] if len(optional) > 1 else ask_optional("Email, Enter to skip: ")
        address = " ".join(optional[2:]) if len(optional) > 2 else ask_optional("Address, Enter to skip: ")
        optional_values = {
            "birthday": birthday,
            "email": email,
            "address": address,
        }
        for field_name, input_value in optional_values.items():
            if input_value:
                self.logic.set_contact_field(record, field_name, input_value)
        return message

    def add_note_router(self, args: list[str]) -> str:
        note_type = args[0] if args and args[0] == "contact" else "general"
        note_actions: dict[str, Callable[[list[str]], str]] = {
            "general": self.add_general_note,
            "contact": self.add_contact_note,
        }
        note_args = args if note_type == "general" else args[1:]
        return note_actions[note_type](note_args)

    def add_general_note(self, args: list[str]) -> str:
        if not args:
            return "Usage: add note [title] [text] #tag"
        title, *parts = args
        text, tags = split_text_and_tags(parts)
        self.logic.add_notebook_note(title, text, tags)
        return "Note added."

    def add_contact_note(self, args: list[str]) -> str:
        if len(args) < 2:
            return "Usage: add note contact [name] [title] [text] #tag"
        name, title, *parts = args
        record = self.logic.get_contact(name)
        text, tags = split_text_and_tags(parts)
        self.logic.add_record_note(record, title, text, tags)
        return "Contact note added."

    # ── UPDATE ──────────────────────────────────────────────────────────────

    @input_error
    def update(self, args: list[str]) -> str:
        if not args:
            return "Usage: update [phone|birthday|email|address|note] ..."
        field = args[0]
        action = self.update_actions.get(field)
        if action is None:
            return "Unknown update field."
        return action(args[1:])

    def update_phone(self, args: list[str]) -> str:
        if len(args) < 2:
            return "Usage: update phone [name] [phone] or update phone [name] [old_phone] [new_phone]"
        name, *phones = args
        record = self.logic.get_contact(name)
        phone_actions: dict[int, Callable[[], str]] = {
            1: lambda: self.add_phone_to_contact(record, phones[0]),
            2: lambda: self.replace_contact_phone(record, phones[0], phones[1]),
        }
        action = phone_actions.get(len(phones))
        if action is None:
            return "Usage: update phone [name] [phone] or update phone [name] [old_phone] [new_phone]"
        return action()

    def add_phone_to_contact(self, record: Record, phone: str) -> str:
        self.logic.add_phone(record, phone)
        return "Phone added."

    def replace_contact_phone(self, record: Record, old_phone: str, new_phone: str) -> str:
        self.logic.replace_phone(record, old_phone, new_phone)
        return "Phone updated."

    def update_contact_field(self, args: list[str], field: str) -> str:
        if len(args) < 2:
            return f"Usage: update {field} [name] [value]"
        name, *value_parts = args
        record = self.logic.get_contact(name)
        input_value = " ".join(value_parts)
        self.logic.set_contact_field(record, field, input_value)
        return f"{field.capitalize()} updated."

    def update_note_router(self, args: list[str]) -> str:
        note_type = args[0] if args and args[0] == "contact" else "general"
        note_actions: dict[str, Callable[[list[str]], str]] = {
            "general": self.update_general_note,
            "contact": self.update_contact_note,
        }
        note_args = args if note_type == "general" else args[1:]
        return note_actions[note_type](note_args)

    def update_general_note(self, args: list[str]) -> str:
        if not args:
            return "Usage: update note [title] [new text] #tag"
        title, *parts = args
        text, tags = split_text_and_tags(parts)
        self.logic.edit_notebook_note(title, text, tags)
        return "Note updated."

    def update_contact_note(self, args: list[str]) -> str:
        if len(args) < 2:
            return "Usage: update note contact [name] [title] [new text] #tag"
        name, title, *parts = args
        record = self.logic.get_contact(name)
        text, tags = split_text_and_tags(parts)
        self.logic.edit_record_note(record, title, text, tags)
        return "Contact note updated."

    # ── SEARCH ──────────────────────────────────────────────────────────────

    @input_error
    def search(self, args: list[str]) -> str:
        if not args:
            return "Usage: search [contact|note] ..."
        target = args[0]
        action = self.search_actions.get(target)
        if action is None:
            return "Unknown search target."
        return action(args[1:])

    def search_contacts(self, args: list[str]) -> str:
        allowed_fields = {"name", "phone", "birthday", "email", "address", "all"}
        field = args[0] if args and args[0] in allowed_fields else "all"
        query_parts = args[1:] if field != "all" or (args and args[0] == "all") else args
        query = " ".join(query_parts)
        return format_contacts(self.logic.find_contacts(query, field))

    def search_note_router(self, args: list[str]) -> str:
        note_type = args[0] if args and args[0] == "contact" else "general"
        note_actions: dict[str, Callable[[list[str]], str]] = {
            "general": self.search_general_notes,
            "contact": self.search_contact_notes,
        }
        note_args = args if note_type == "general" else args[1:]
        return note_actions[note_type](note_args)

    def search_general_notes(self, args: list[str]) -> str:
        allowed_fields = {"name", "title", "text", "tag", "all"}
        field = args[0] if args and args[0] in allowed_fields else "all"
        query_parts = args[1:] if field != "all" or (args and args[0] == "all") else args
        query = " ".join(query_parts)
        return format_notes(self.logic.find_notebook_notes(query, field))

    def search_contact_notes(self, args: list[str]) -> str:
        allowed_fields = {"name", "title", "text", "tag", "all"}
        field = args[0] if args and args[0] in allowed_fields else "all"
        query_parts = args[1:] if field != "all" or (args and args[0] == "all") else args
        query = " ".join(query_parts)
        results = []
        for record in self.logic.book.data.values():
            for note in record.notes:
                if self.logic.note_matches(note, query, field):
                    results.append(f"{record.name.value} -> {note}")
        return "\n".join(results) if results else "No contact notes found."

    # ── SHOW ────────────────────────────────────────────────────────────────

    @input_error
    def show(self, args: list[str]) -> str:
        if not args:
            return "Usage: show [all|notes|birthdays]"
        action = self.show_actions.get(args[0])
        if action is None:
            return "Unknown show command."
        return action(args[1:])

    def show_all_contacts(self, _args: Optional[list[str]] = None) -> str:
        if not self.logic.book.data:
            return "Address book is empty."
        return "\n".join(str(record) for record in self.logic.book.data.values())

    def show_all_notes(self, _args: Optional[list[str]] = None) -> str:
        notes = list(self.logic.notebook.data.values())
        if not notes:
            return "Notebook is empty."
        return "\n".join(str(note) for note in notes)

    def show_birthdays(self, args: list[str]) -> str:
        days = int(args[0]) if args else 7
        records = self.logic.upcoming_birthdays(days)
        return format_contacts(records) if records else f"No birthdays in the next {days} day(s)."

    # ── DELETE ──────────────────────────────────────────────────────────────

    @input_error
    def delete(self, args: list[str]) -> str:
        if not args:
            return "Usage: delete [contact|phone|birthday|email|address|note] ..."
        target = args[0]
        action = self.delete_actions.get(target)
        if action is None:
            return "Unknown delete target."
        return action(args[1:])

    def delete_contact(self, args: list[str]) -> str:
        if not args:
            return "Usage: delete contact [name]"
        name = args[0]
        self.logic.delete_record(name)
        return f"Contact {name} deleted."

    def delete_contact_data(self, args: list[str], target: str) -> str:
        if not args:
            return f"Usage: delete {target} [name]"
        name = args[0]
        record = self.logic.get_contact(name)
        delete_actions: dict[str, Callable[[], None]] = {
            "phone": lambda: self.logic.delete_phone(record, args[1]) if len(args) > 1 else raise_value("Usage: delete phone [name] [phone]"),
            "birthday": lambda: self.logic.delete_contact_field(record, "birthday"),
            "email": lambda: self.logic.delete_contact_field(record, "email"),
            "address": lambda: self.logic.delete_contact_field(record, "address"),
        }
        delete_actions[target]()
        return f"{target.capitalize()} deleted."

    def delete_note_router(self, args: list[str]) -> str:
        note_type = args[0] if args and args[0] == "contact" else "general"
        note_actions: dict[str, Callable[[list[str]], str]] = {
            "general": self.delete_general_note,
            "contact": self.delete_contact_note,
        }
        note_args = args if note_type == "general" else args[1:]
        return note_actions[note_type](note_args)

    def delete_general_note(self, args: list[str]) -> str:
        if not args:
            return "Usage: delete note [title]"
        title = args[0]
        self.logic.delete_notebook_note(title)
        return "Note deleted."

    def delete_contact_note(self, args: list[str]) -> str:
        if len(args) < 2:
            return "Usage: delete note contact [name] [title]"
        name, title = args
        record = self.logic.get_contact(name)
        self.logic.delete_record_note(record, title)
        return "Contact note deleted."
