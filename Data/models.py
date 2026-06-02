import re
from collections import UserDict
from datetime import datetime


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must be 10 digits")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            value = datetime.strptime(value, "%d.%m.%Y").date()
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Email(Field):
    def __init__(self, value):
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(pattern, value):
            raise ValueError("Invalid email format.")
        super().__init__(value)


class Address(Field):
    pass


class Note:
    def __init__(self, title, text, tags=None):
        self.title = title
        self.text = text
        self.tags = tags if tags else []

    def edit(self, new_text, tags=None):
        self.text = new_text
        self.tags = tags if tags else []

    def matches(self, query, field="all"):
        query = query.lower().lstrip("#")
        search_actions = {
            "title": lambda: query in self.title.lower(),
            "text": lambda: query in self.text.lower(),
            "tag": lambda: any(query == tag.lower() for tag in self.tags),
            "all": lambda: (
                query in self.title.lower()
                or query in self.text.lower()
                or any(query == tag.lower() for tag in self.tags)
            ),
        }
        return search_actions.get(field, search_actions["all"])()

    def __str__(self):
        tags = ", ".join(self.tags) if self.tags else "no tags"
        return f"{self.title}: {self.text} | tags: {tags}"


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None
        self.email = None
        self.address = None
        self.notes = []

    def add_phone(self, phone) -> None:
        if self.find_phone(phone):
            raise ValueError("Phone already exists.")
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        if self.find_phone(new_phone):
            raise ValueError("Phone already exists.")
        for phone in self.phones:
            if phone.value == old_phone:
                phone.value = Phone(new_phone).value
                return
        raise ValueError("Phone not found")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def delete_birthday(self):
        self.birthday = None

    def add_email(self, email):
        self.email = Email(email)

    def add_address(self, address):
        self.address = Address(address)

    def add_note(self, title, text, tags=None):
        self.notes.append(Note(title, text, tags))

    def delete_email(self):
        self.email = None

    def delete_address(self):
        self.address = None

    def delete_phone(self, phone):
        if self.find_phone(phone) is None:
            raise ValueError("Phone not found")
        if len(self.phones) <= 1:
            raise ValueError("Cannot delete the only phone number.")
        self.remove_phone(phone)

    def delete_note(self, title):
        for note in self.notes:
            if note.title == title:
                self.notes.remove(note)
                return
        raise KeyError

    def edit_note(self, title, new_text, tags=None):
        for note in self.notes:
            if note.title == title:
                note.edit(new_text, tags)
                return
        raise KeyError

    def matches(self, query, field="all"):
        query = query.lower()
        birthday_formats = []

        if self.birthday is not None:
            birthday = self.birthday.value
            birthday_formats = [
                birthday.strftime("%d.%m.%Y"),
                birthday.strftime("%d.%m"),
                birthday.strftime("%m.%Y"),
                birthday.strftime("%Y"),
                birthday.strftime("%m"),
                birthday.strftime("%d"),
                str(birthday.month),
                str(birthday.day),
            ]
        search_actions = {
            "name": lambda: query in self.name.value.lower(),
            "phone": lambda: any(query in phone.value for phone in self.phones),
            "birthday": lambda: any(query == value.lower() for value in birthday_formats),
            "email": lambda: self.email and query in self.email.value.lower(),
            "address": lambda: self.address and query in self.address.value.lower(),
            "note": lambda: any(note.matches(query) for note in self.notes),
            "all": lambda: (
                query in self.name.value.lower()
                or any(query in phone.value for phone in self.phones)
                or any(query == value.lower() for value in birthday_formats)
                or bool(self.email and query in self.email.value.lower())
                or bool(self.address and query in self.address.value.lower())
                or any(note.matches(query) for note in self.notes)
            ),
        }
        return bool(search_actions.get(field, search_actions["all"])())

    def __str__(self):
        birthday = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "not added"
        email = self.email.value if self.email else "not added"
        address = self.address.value if self.address else "not added"
        phones = "; ".join(p.value for p in self.phones) if self.phones else "none"
        return (
            f"Contact name: {self.name.value}, "
            f"phones: {phones}, "
            f"birthday: {birthday}, "
            f"email: {email}, "
            f"address: {address}"
        )


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name not in self.data:
            raise KeyError
        del self.data[name]

    def search(self, query, field="all"):
        return [record for record in self.data.values() if record.matches(query, field)]

    def upcoming_birthdays(self, days=7):
        today = datetime.today().date()
        birthdays = []
        for record in self.data.values():
            if record.birthday:
                birthday = record.birthday.value
                next_birthday = birthday.replace(
                    year=today.year
                    if birthday.replace(year=today.year) >= today
                    else today.year + 1
                )
                if (next_birthday - today).days <= days:
                    birthdays.append(record)
        return birthdays


class NoteBook(UserDict):
    def add_note(self, title, text, tags=None):
        self.data[title] = Note(title, text, tags)

    def find_note(self, query, field="all"):
        return [note for note in self.data.values() if note.matches(query, field)]

    def edit_note(self, title, new_text, tags=None):
        if title not in self.data:
            raise KeyError
        self.data[title].edit(new_text, tags)

    def delete_note(self, title):
        if title not in self.data:
            raise KeyError
        del self.data[title]

    def all_notes(self):
        return list(self.data.values())
