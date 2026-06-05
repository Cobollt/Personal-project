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

from .command.commands import CommandHandler
from .storage_data.storage import AddressBook, NoteBook
from .storage_data.validation import is_error_message, run_user_command

RED = Fore.RED
GREEN = Fore.GREEN
BLUE = Fore.BLUE

DATA_DIR = Path("SaveData")
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "addressbook.pkl"
NOTES_FILE = DATA_DIR / "notebook.pkl"


def save_data(book: AddressBook, filename=DATA_FILE) -> None:
    with open(filename, "wb") as file:
        pickle.dump(book, file)


def save_notes(notes: NoteBook, filename=NOTES_FILE) -> None:
    with open(filename, "wb") as file:
        pickle.dump(notes, file)


def load_data(filename=DATA_FILE) -> AddressBook:
    try:
        with open(filename, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return AddressBook()


def load_notes(filename=NOTES_FILE) -> NoteBook:
    try:
        with open(filename, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return NoteBook()


def main() -> None:
    book = load_data()
    notebook = load_notes()
    handler = CommandHandler(book, notebook)

    print(f"\n{BLUE}Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command = user_input.split()[0].lower() if user_input.split() else ""

        if command in ("close", "exit"):
            save_data(book)
            save_notes(notebook)
            print(f"{BLUE}Good bye!")
            break

        result = run_user_command(user_input, handler.commands)
        if result is None:
            continue

        if command == "help":
            print(result)
        elif is_error_message(result):
            print(f"{RED}{result}")
        else:
            print(f"{GREEN}{result}")


if __name__ == "__main__":
    main()
