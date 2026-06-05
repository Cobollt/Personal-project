from typing import Callable

try:
    from colorama import Fore
except ImportError:
    Fore = None

from Data.servise.contact_service import ContactService
from Data.servise.note_service import NoteService
from Data.storage_data.storage import AddressBook, NoteBook

GRAY = getattr(Fore, "LIGHT" + "BLACK_EX", "") if Fore else ""


def show_help(_args: list[str] | None = None) -> str:
    return f"""
{GRAY}----------
Available commands:

add [name] [phone] [birthday] [email] [address]
add note [contact] [title] [text] #tag

update phone [name] [phone]
update phone [name] [old_phone] [new_phone]
update birthday [name] [DD.MM.YYYY]
update email [name] [email]
update address [name] [address]
update note [contact] [title] [new text] #tag

search contact [name|phone|birthday|email|address|all] [query]
search note [contact|title|text|tag|all] [query]

show all
show notes
show birthdays [days]

delete contact [name]
delete phone [name] [phone]
delete birthday [name]
delete email [name]
delete address [name]
delete note [contact] [title]

help
close / exit
----------
"""


class CommandHandler:
    def __init__(self, book: AddressBook, notebook: NoteBook):
        self.contact_service = ContactService(book)
        self.note_service = NoteService(notebook, self.contact_service)
        self.commands: dict[str, Callable[[list[str]], str]] = self._build_commands()

    def _build_commands(self) -> dict[str, Callable[[list[str]], str]]:
        return {
            "help": show_help,
            "add": self.add,
            "update": self.update,
            "search": self.search,
            "show": self.show,
            "delete": self.delete,
        }

    def add(self, args: list[str]) -> str:
        actions = {
            "note": lambda payload: self.note_service.add_command(payload),
            "contact": lambda payload: self.contact_service.add_command(payload),
        }
        keyword = "note" if args and args[0] == "note" else "contact"
        payload = args[1:] if keyword == "note" else args
        return actions[keyword](payload)

    def update(self, args: list[str]) -> str:
        if not args:
            return "Usage: update [phone|birthday|email|address|note] ..."

        actions = {
            "phone": lambda payload: self.contact_service.update_phone_command(payload),
            "birthday": lambda payload: self.contact_service.update_field_command(payload, "birthday"),
            "email": lambda payload: self.contact_service.update_field_command(payload, "email"),
            "address": lambda payload: self.contact_service.update_field_command(payload, "address"),
            "note": lambda payload: self.note_service.update_command(payload),
        }
        action = actions.get(args[0])
        return action(args[1:]) if action else "Unknown update field."

    def search(self, args: list[str]) -> str:
        if not args:
            return "Usage: search [contact|note] ..."

        actions = {
            "contact": lambda payload: self.contact_service.search_command(payload),
            "note": lambda payload: self.note_service.search_command(payload),
        }
        action = actions.get(args[0])
        return action(args[1:]) if action else "Unknown search target."

    def show(self, args: list[str]) -> str:
        if not args:
            return "Usage: show [all|notes|birthdays]"

        actions = {
            "all": lambda payload: self.contact_service.show_all_command(payload),
            "notes": lambda payload: self.note_service.show_all_command(payload),
            "birthdays": lambda payload: self.contact_service.show_birthdays_command(payload),
        }
        action = actions.get(args[0])
        return action(args[1:]) if action else "Unknown show command."

    def delete(self, args: list[str]) -> str:
        if not args:
            return "Usage: delete [contact|phone|birthday|email|address|note] ..."

        actions = {
            "contact": lambda payload: self.contact_service.delete_contact_command(payload),
            "phone": lambda payload: self.contact_service.delete_data_command(payload, "phone"),
            "birthday": lambda payload: self.contact_service.delete_data_command(payload, "birthday"),
            "email": lambda payload: self.contact_service.delete_data_command(payload, "email"),
            "address": lambda payload: self.contact_service.delete_data_command(payload, "address"),
            "note": lambda payload: self.note_service.delete_command(payload),
        }
        action = actions.get(args[0])
        return action(args[1:]) if action else "Unknown delete target."
