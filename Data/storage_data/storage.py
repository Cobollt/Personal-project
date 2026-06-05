from datetime import date
from typing import Optional

from .validation import parse_birthday, validate_email, validate_phone


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value: str):
        super().__init__(validate_phone(value))


class Birthday(Field):
    def __init__(self, value: str | date):
        super().__init__(parse_birthday(value))


class Email(Field):
    def __init__(self, value: str):
        super().__init__(validate_email(value))


class Address(Field):
    pass


class Note:
    def __init__(
        self,
        title: str,
        text: str = "",
        tags: Optional[list[str]] = None,
        contact: Optional[str] = None,
    ):
        self.contact = contact
        self.title = title
        self.text = text
        self.tags = tags if tags else []

    def __str__(self) -> str:
        tags = ", ".join(self.tags) if self.tags else "not added"
        return (
            "Notebook:\n"
            f"  contact: {self.contact if self.contact else 'not added'}\n"
            f"  title: {self.title}\n"
            f"  text: {self.text if self.text else 'not added'}\n"
            f"  tag: {tags}"
        )


class Record:
    def __init__(self, name: Name | str):
        self.name = name if isinstance(name, Name) else Name(name)
        self.phones: list[Phone] = []
        self.birthday: Optional[Birthday] = None
        self.email: Optional[Email] = None
        self.address: Optional[Address] = None

    def __str__(self) -> str:
        birthday = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "not added"
        email = self.email.value if self.email else "not added"
        address = self.address.value if self.address else "not added"
        phones = ", ".join(phone.value for phone in self.phones) if self.phones else "not added"
        return (
            "AddressBook:\n"
            f"  name: {self.name.value}\n"
            f"  phone: {phones}\n"
            f"  birthday: {birthday}\n"
            f"  email: {email}\n"
            f"  address: {address}"
        )


class AddressBook:
    def __init__(self):
        self.data: dict[str, Record] = {}

    def __str__(self) -> str:
        if not self.data:
            return "AddressBook: empty"
        return "\n\n".join(str(record) for record in self.data.values())


class NoteBook:
    def __init__(self):
        self.data: dict[str, Note] = {}

    def __str__(self) -> str:
        if not self.data:
            return "Notebook: empty"
        return "\n\n".join(str(note) for note in self.data.values())
