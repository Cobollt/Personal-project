# Нахуй разнести весь блок по add, update, search, show, delete

from datetime import datetime
from typing import Callable, Optional

from Data.storage_data.storage import Address, Birthday, Email, Note, Phone, Record
from Data.storage_data.validation import normalize_query


class ModelLogic:
    def __init__(self, book, notebook):
        self.book = book
        self.notebook = notebook

    FIELD_CLASSES: dict[str, Callable[[str], object]] = {
        "birthday": Birthday,
        "email": Email,
        "address": Address,
    }

    def get_contact(self, name: str) -> Record:
        record = self.book.data.get(name)
        if record is None:
            raise ValueError("No contact.")
        return record

    def add_record(self, record: Record) -> None:
        self.book.data[record.name.value] = record

    def delete_record(self, name: str) -> None:
        if name not in self.book.data:
            raise KeyError
        del self.book.data[name]

    def add_notebook_note(self, title: str, text: str, tags: list[str]) -> None:
        self.notebook.data[title] = Note(title=title, text=text, tags=tags)

    def edit_notebook_note(self, title: str, text: str, tags: list[str]) -> None:
        note = self.notebook.data.get(title)
        if note is None:
            raise KeyError
        note.text = text
        note.tags = tags

    def delete_notebook_note(self, title: str) -> None:
        if title not in self.notebook.data:
            raise KeyError
        del self.notebook.data[title]

    @staticmethod
    def find_phone(record: Record, phone: str) -> Optional[Phone]:
        return next((item for item in record.phones if item.value == phone), None)

    def add_phone(self, record: Record, phone: str) -> None:
        if self.find_phone(record, phone):
            raise ValueError("Phone already exists.")
        record.phones.append(Phone(phone))

    def replace_phone(self, record: Record, old_phone: str, new_phone: str) -> None:
        if self.find_phone(record, new_phone):
            raise ValueError("Phone already exists.")
        current_phone = self.find_phone(record, old_phone)
        if current_phone is None:
            raise ValueError("Phone not found")
        current_phone.value = Phone(new_phone).value

    def delete_phone(self, record: Record, phone: str) -> None:
        current_phone = self.find_phone(record, phone)
        if current_phone is None:
            raise ValueError("Phone not found")
        if len(record.phones) <= 1:
            raise ValueError("Cannot delete the only phone number.")
        record.phones.remove(current_phone)

    def set_contact_field(self, record: Record, field_name: str, field_value: str) -> None:
        field_class = self.FIELD_CLASSES.get(field_name)
        if field_class is None:
            raise ValueError("Unknown contact field.")
        setattr(record, field_name, field_class(field_value))

    @staticmethod
    def delete_contact_field(record: Record, field_name: str) -> None:
        allowed_fields = {"birthday", "email", "address"}
        if field_name not in allowed_fields:
            raise ValueError("Unknown contact field.")
        setattr(record, field_name, None)

    @staticmethod
    def find_record_note(record: Record, title: str) -> Optional[Note]:
        return next((note for note in record.notes if note.title == title), None)

    @staticmethod
    def add_record_note(record: Record, title: str, text: str, tags: list[str]) -> None:
        record.notes.append(Note(title=title, text=text, tags=tags, name=record.name.value))

    def edit_record_note(self, record: Record, title: str, text: str, tags: list[str]) -> None:
        note = self.find_record_note(record, title)
        if note is None:
            raise KeyError
        note.text = text
        note.tags = tags

    def delete_record_note(self, record: Record, title: str) -> None:
        note = self.find_record_note(record, title)
        if note is None:
            raise KeyError
        record.notes.remove(note)

    @staticmethod
    def note_matches(note: Note, query: str, search_field: str = "all") -> bool:
        normalized_query = normalize_query(query)
        search_actions: dict[str, Callable[[], bool]] = {
            "name": lambda: bool(note.name and normalized_query in note.name.lower()),
            "title": lambda: normalized_query in note.title.lower(),
            "text": lambda: normalized_query in note.text.lower(),
            "tag": lambda: any(normalized_query == tag.lower() for tag in note.tags),
            "all": lambda: (
                bool(note.name and normalized_query in note.name.lower())
                or normalized_query in note.title.lower()
                or normalized_query in note.text.lower()
                or any(normalized_query == tag.lower() for tag in note.tags)
            ),
        }
        return search_actions.get(search_field, search_actions["all"])()

    @staticmethod
    def birthday_formats(record: Record) -> list[str]:
        if record.birthday is None:
            return []
        birthday = record.birthday.value
        return [
            birthday.strftime("%d.%m.%Y"),
            birthday.strftime("%d.%m"),
            birthday.strftime("%m.%Y"),
            birthday.strftime("%Y"),
            birthday.strftime("%m"),
            birthday.strftime("%d"),
            str(birthday.month),
            str(birthday.day),
        ]

    def record_matches(self, record: Record, query: str, search_field: str = "all") -> bool:
        normalized_query = query.lower()
        birthday_values = self.birthday_formats(record)
        search_actions: dict[str, Callable[[], bool]] = {
            "name": lambda: normalized_query in record.name.value.lower(),
            "phone": lambda: any(normalized_query in phone.value for phone in record.phones),
            "birthday": lambda: any(normalized_query == item.lower() for item in birthday_values),
            "email": lambda: bool(record.email and normalized_query in record.email.value.lower()),
            "address": lambda: bool(record.address and normalized_query in record.address.value.lower()),
            "note": lambda: any(self.note_matches(note, normalized_query) for note in record.notes),
            "all": lambda: (
                normalized_query in record.name.value.lower()
                or any(normalized_query in phone.value for phone in record.phones)
                or any(normalized_query == item.lower() for item in birthday_values)
                or bool(record.email and normalized_query in record.email.value.lower())
                or bool(record.address and normalized_query in record.address.value.lower())
                or any(self.note_matches(note, normalized_query) for note in record.notes)
            ),
        }
        return search_actions.get(search_field, search_actions["all"])()

    def find_contacts(self, query: str, search_field: str = "all") -> list[Record]:
        return [record for record in self.book.data.values() if self.record_matches(record, query, search_field)]

    def find_notebook_notes(self, query: str, search_field: str = "all") -> list[Note]:
        return [note for note in self.notebook.data.values() if self.note_matches(note, query, search_field)]

    def upcoming_birthdays(self, days: int = 7) -> list[Record]:
        today = datetime.today().date()
        result = []
        for record in self.book.data.values():
            if record.birthday is None:
                continue
            birthday = record.birthday.value
            birthday_this_year = birthday.replace(year=today.year)
            next_birthday = birthday_this_year if birthday_this_year >= today else birthday.replace(year=today.year + 1)
            if (next_birthday - today).days <= days:
                result.append(record)
        return result
