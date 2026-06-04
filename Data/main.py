import pickle
from pathlib import Path

try:
    from colorama import Fore, init
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = ""
        GREEN = ""
        BLUE = ""

from Data.storage_data.storage import AddressBook, NoteBook
from Data.command.commands import CommandHandler, parse_input, suggest_command, is_error_message


RED = Fore.RED
GREEN = Fore.GREEN
BLUE = Fore.BLUE

DATA_DIR = Path("SaveData")
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "addressbook.pkl"
NOTES_FILE = DATA_DIR / "notebook.pkl"


def save_data(book, filename=DATA_FILE):
    with open(filename, "wb") as file:
        pickle.dump(book, file)


def save_notes(notes, filename=NOTES_FILE):
    with open(filename, "wb") as file:
        pickle.dump(notes, file)


def load_data(filename=DATA_FILE):
    try:
        with open(filename, "rb") as file:
            book = pickle.load(file)
        for record in book.data.values():
            record.email = getattr(record, "email", None)
            record.address = getattr(record, "address", None)
            record.notes = getattr(record, "notes", [])
        return book
    except FileNotFoundError:
        return AddressBook()


def load_notes(filename=NOTES_FILE):
    try:
        with open(filename, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return NoteBook()


def main():
    book = load_data()
    notebook = load_notes()
    handler = CommandHandler(book, notebook)

    print(f"\n{BLUE}Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        if not user_input.strip():
            print(f"{RED}Please enter a command.")
            continue

        command, args = parse_input(user_input)

        if command in ("close", "exit"):
            save_data(book)
            save_notes(notebook)
            print(f"{BLUE}Good bye!")
            break

        result = handler.execute(command, args)

        if result is None:
            suggestion = suggest_command(user_input, handler.commands)
            print(f"Did you mean: {suggestion}?" if suggestion else f"{RED}Invalid command.")
            continue

        if command == "help":
            print(result)
        elif is_error_message(result):
            print(f"{RED}{result}")
        else:
            print(f"{GREEN}{result}")


if __name__ == "__main__":
    main()
