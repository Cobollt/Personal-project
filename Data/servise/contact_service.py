from datetime import datetime
from typing import Callable, Optional

from Data.storage_data.storage import Address, AddressBook, Birthday, Email, Phone, Record
from Data.storage_data.validation import normalize_query


class ContactService:
    FIELD_CLASSES: dict[str, Callable[[str], object]] = {
        "birthday": Birthday,
        "email": Email,
        "address": Address,
    }

    def __init__(self, book: AddressBook):
        self.book = book

    def add_command(self, args: list[str]) -> str:
        if len(args) < 2:
            return "Usage: add [name] [phone] [birthday] [email] [address]"

        name, phone, *optional = args
        birthday = optional[0] if len(optional) > 0 else self._ask_optional("Birthday DD.MM.YYYY, Enter to skip: ")
        email = optional[1] if len(optional) > 1 else self._ask_optional("Email, Enter to skip: ")
        address = " ".join(optional[2:]) if len(optional) > 2 else self._ask_optional("Address, Enter to skip: ")

        _record, is_created = self.create_contact(name, phone, birthday, email, address)
        return "Contact added." if is_created else "Contact updated."

    def update_phone_command(self, args: list[str]) -> str:
        if len(args) < 2:
            return "Usage: update phone [name] [phone] or update phone [name] [old_phone] [new_phone]"

        name, *phones = args
        record = self.get_contact(name)
        phone_actions: dict[int, Callable[[], str]] = {
            1: lambda: self.add_phone_command_result(record, phones[0]),
            2: lambda: self.replace_phone_command_result(record, phones[0], phones[1]),
        }
        action = phone_actions.get(len(phones))
        if action is None:
            return "Usage: update phone [name] [phone] or update phone [name] [old_phone] [new_phone]"
        return action()

    def update_field_command(self, args: list[str], field_name: str) -> str:
        if len(args) < 2:
            return f"Usage: update {field_name} [name] [value]"

        name, *value_parts = args
        record = self.get_contact(name)
        self.set_contact_field(record, field_name, " ".join(value_parts))
        return f"{field_name.capitalize()} updated."

    def search_command(self, args: list[str]) -> str:
        allowed_fields = {"name", "phone", "birthday", "email", "address", "all"}
        field_name = args[0] if args and args[0] in allowed_fields else "all"
        query_parts = args[1:] if field_name != "all" or (args and args[0] == "all") else args
        contacts = self.search_contacts(" ".join(query_parts), field_name)
        return self.format_contacts(contacts)

    def show_all_command(self, _args: list[str] | None = None) -> str:
        return str(self.book) if self.book.data else "Address book is empty."

    def show_birthdays_command(self, args: list[str]) -> str:
        days = int(args[0]) if args else 7
        records = self.upcoming_birthdays(days)
        return self.format_contacts(records) if records else f"No birthdays in the next {days} day(s)."

    def delete_contact_command(self, args: list[str]) -> str:
        if not args:
            return "Usage: delete contact [name]"
        self.delete_contact(args[0])
        return f"Contact {args[0]} deleted."

    def delete_data_command(self, args: list[str], field_name: str) -> str:
        if not args:
            return f"Usage: delete {field_name} [name]"

        record = self.get_contact(args[0])
        if field_name == "phone":
            if len(args) < 2:
                return "Usage: delete phone [name] [phone]"
            self.delete_phone(record, args[1])
        else:
            self.delete_contact_field(record, field_name)

        return f"{field_name.capitalize()} deleted."

    def create_contact(
        self,
        name: str,
        phone: str,
        birthday: str | None = None,
        email: str | None = None,
        address: str | None = None,
    ) -> tuple[Record, bool]:
        record = self.book.data.get(name)
        is_created = record is None

        if record is None:
            record = Record(name)
            self.book.data[record.name.value] = record

        self.add_phone(record, phone)

        optional_fields = {
            "birthday": birthday,
            "email": email,
            "address": address,
        }
        for field_name, field_value in optional_fields.items():
            if field_value:
                self.set_contact_field(record, field_name, field_value)

        return record, is_created

    def get_contact(self, name: str) -> Record:
        record = self.book.data.get(name)
        if record is None:
            raise ValueError("No contact.")
        return record

    @staticmethod
    def find_phone(record: Record, phone: str) -> Optional[Phone]:
        return next((item for item in record.phones if item.value == phone), None)

    def add_phone(self, record: Record, phone: str) -> None:
        if self.find_phone(record, phone):
            raise ValueError("Phone already exists.")
        record.phones.append(Phone(phone))

    def add_phone_command_result(self, record: Record, phone: str) -> str:
        self.add_phone(record, phone)
        return "Phone added."

    def replace_phone(self, record: Record, old_phone: str, new_phone: str) -> None:
        if self.find_phone(record, new_phone):
            raise ValueError("Phone already exists.")

        current_phone = self.find_phone(record, old_phone)
        if current_phone is None:
            raise ValueError("Phone not found")

        current_phone.value = Phone(new_phone).value

    def replace_phone_command_result(self, record: Record, old_phone: str, new_phone: str) -> str:
        self.replace_phone(record, old_phone, new_phone)
        return "Phone updated."

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

    def delete_contact(self, name: str) -> None:
        if name not in self.book.data:
            raise KeyError
        del self.book.data[name]

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

    def contact_matches(self, record: Record, query: str, search_field: str = "all") -> bool:
        normalized_query = normalize_query(query)
        birthday_values = self.birthday_formats(record)

        search_actions: dict[str, Callable[[], bool]] = {
            "name": lambda: normalized_query in record.name.value.lower(),
            "phone": lambda: any(normalized_query in phone.value for phone in record.phones),
            "birthday": lambda: any(normalized_query == item.lower() for item in birthday_values),
            "email": lambda: bool(record.email and normalized_query in record.email.value.lower()),
            "address": lambda: bool(record.address and normalized_query in record.address.value.lower()),
            "all": lambda: (
                normalized_query in record.name.value.lower()
                or any(normalized_query in phone.value for phone in record.phones)
                or any(normalized_query == item.lower() for item in birthday_values)
                or bool(record.email and normalized_query in record.email.value.lower())
                or bool(record.address and normalized_query in record.address.value.lower())
            ),
        }
        return search_actions.get(search_field, search_actions["all"])()

    def search_contacts(self, query: str, search_field: str = "all") -> list[Record]:
        return [record for record in self.book.data.values() if self.contact_matches(record, query, search_field)]

    def upcoming_birthdays(self, days: int = 7) -> list[Record]:
        today = datetime.today().date()
        result: list[Record] = []

        for record in self.book.data.values():
            if record.birthday is None:
                continue

            birthday = record.birthday.value
            birthday_this_year = birthday.replace(year=today.year)
            next_birthday = birthday_this_year if birthday_this_year >= today else birthday.replace(year=today.year + 1)
            if (next_birthday - today).days <= days:
                result.append(record)

        return result

    @staticmethod
    def format_contacts(records: list[Record]) -> str:
        return "\n\n".join(str(record) for record in records) if records else "No contacts found."

    @staticmethod
    def _ask_optional(prompt: str) -> str | None:
        user_value = input(prompt).strip()
        return user_value if user_value else None
