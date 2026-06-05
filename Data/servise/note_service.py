from typing import Callable

from Data.storage_data.storage import Note, NoteBook
from Data.storage_data.validation import normalize_query, split_text_and_tags


class NoteService:
    def __init__(self, notebook: NoteBook, contact_service=None):
        self.notebook = notebook
        self.contact_service = contact_service

    def add_command(self, args: list[str]) -> str:
        contact, title, note_parts = self._parse_note_args(args, "Usage: add note [contact] [title] [text] #tag")
        text, tags = split_text_and_tags(note_parts)
        self.add_note(title, text, tags, contact)
        return "Note added."

    def update_command(self, args: list[str]) -> str:
        contact, title, note_parts = self._parse_note_args(args, "Usage: update note [contact] [title] [new text] #tag")
        text, tags = split_text_and_tags(note_parts)
        self.edit_note(title, text, tags, contact)
        return "Note updated."

    def search_command(self, args: list[str]) -> str:
        allowed_fields = {"contact", "title", "text", "tag", "all"}
        field_name = args[0] if args and args[0] in allowed_fields else "all"
        query_parts = args[1:] if field_name != "all" or (args and args[0] == "all") else args
        notes = self.search_notes(" ".join(query_parts), field_name)
        return self.format_notes(notes)

    def show_all_command(self, _args: list[str] | None = None) -> str:
        return str(self.notebook) if self.notebook.data else "Notebook is empty."

    def delete_command(self, args: list[str]) -> str:
        if not args:
            return "Usage: delete note [contact] [title]"

        contact, title, _note_parts = self._parse_note_args(args, "Usage: delete note [contact] [title]", allow_text=False)
        self.delete_note(title, contact)
        return "Note deleted."

    def add_note(self, title: str, text: str, tags: list[str], contact: str | None = None) -> None:
        self._validate_contact_if_present(contact)
        key = self._note_key(title, contact)
        self.notebook.data[key] = Note(title=title, text=text, tags=tags, contact=contact)

    def edit_note(self, title: str, text: str, tags: list[str], contact: str | None = None) -> None:
        note = self.get_note(title, contact)
        note.text = text
        note.tags = tags

    def delete_note(self, title: str, contact: str | None = None) -> None:
        key = self._note_key(title, contact)
        if key not in self.notebook.data:
            raise KeyError
        del self.notebook.data[key]

    def get_note(self, title: str, contact: str | None = None) -> Note:
        note = self.notebook.data.get(self._note_key(title, contact))
        if note is None:
            raise KeyError
        return note

    def note_matches(self, note: Note, query: str, search_field: str = "all") -> bool:
        normalized_query = normalize_query(query)
        search_actions: dict[str, Callable[[], bool]] = {
            "contact": lambda: bool(note.contact and normalized_query in note.contact.lower()),
            "title": lambda: normalized_query in note.title.lower(),
            "text": lambda: normalized_query in note.text.lower(),
            "tag": lambda: any(normalized_query == tag.lower() for tag in note.tags),
            "all": lambda: (
                bool(note.contact and normalized_query in note.contact.lower())
                or normalized_query in note.title.lower()
                or normalized_query in note.text.lower()
                or any(normalized_query == tag.lower() for tag in note.tags)
            ),
        }
        return search_actions.get(search_field, search_actions["all"])()

    def search_notes(self, query: str, search_field: str = "all") -> list[Note]:
        return [note for note in self.notebook.data.values() if self.note_matches(note, query, search_field)]

    def _parse_note_args(self, args: list[str], usage: str, allow_text: bool = True) -> tuple[str | None, str, list[str]]:
        if not args:
            raise ValueError(usage)

        if self.contact_service and args[0] in self.contact_service.book.data:
            if len(args) < 2:
                raise ValueError(usage)
            contact = args[0]
            title = args[1]
            parts = args[2:]
        else:
            contact = None
            title = args[0]
            parts = args[1:]

        if not allow_text and parts:
            parts = []

        return contact, title, parts

    def _validate_contact_if_present(self, contact: str | None) -> None:
        if contact and self.contact_service:
            self.contact_service.get_contact(contact)

    @staticmethod
    def _note_key(title: str, contact: str | None = None) -> str:
        return f"{contact or ''}::{title}"

    @staticmethod
    def format_notes(notes: list[Note]) -> str:
        return "\n\n".join(str(note) for note in notes) if notes else "No notes found."
