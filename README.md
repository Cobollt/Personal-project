# One Bot To Save 'Em All

## Team

- Rudem Yusupov
- Viktor Paranych
- Mykyta Ihnatenko

A command-line personal assistant written in Python for managing contacts, birthdays, notes, email addresses, physical addresses, and tags.

All data is stored locally and automatically saved between sessions.

---

## Features

### Contacts
- Add, edit, search, and delete contacts
- Store multiple phone numbers per contact
- Search by name, phone number, email, address, or notes

### Contact Information
- Birthdays
- Email addresses
- Physical addresses

### Notes
- Create and manage notes
- Attach notes to contacts
- Add custom tags
- Search by title, content, or tag
- Edit and delete notes

### Birthday Reminders
- View upcoming birthdays
- Choose how many days ahead to check

### User-Friendly CLI
- Interactive help menu
- Input validation
- Automatic data persistence
- Suggestions for mistyped commands

---

## Installation

### Linux / macOS

```bash
git clone <[repository-url](https://github.com/Cobollt/One_bot_to_save_em_all)>
cd One_bot_to_save_em_all

python3 -m venv .venv
source .venv/bin/activate

chmod +x install.sh
./install.sh
```

### Windows

```cmd
python -m venv .venv
.venv\Scripts\activate

install.bat
```

---

## Running the Assistant

Start the assistant using:

```bash
assistant-bot
```

Alternatively:

```bash
python Data/main.py
```

---

## Getting Started

After launching the assistant, type:

```text
help
```

This command displays all available commands and usage examples.

---

## Commands

### Contacts

```text
add contact John 1234567890
add contact John 0987654321
change contact John 1234567890 1112223333
delete contact John
find contact John
show all
```

### Birthdays

```text
add birthday John 15.06.1995
show birthday John
show birthdays
show birthdays 30
```

### Email Addresses

```text
add email John john@example.com
change email John newmail@example.com
```

### Addresses

```text
add address John 221B Baker Street London
change address John New York USA
```

### General Notes

```text
add note Shopping Buy milk eggs bread #home #shopping
find note milk
find tag shopping
change note Shopping Buy milk eggs bread and butter
delete note Shopping
show notes
```

### Contact Notes

```text
add contact-note John Meeting Discuss project details #work
show contact-notes John
find contact-tag work
```

---

## Data Storage

All data is automatically saved using Python's built-in `pickle` module.

---

## Requirements

- Python 3.10+
- No external dependencies required

---

## Exit

```text
exit
```

or

```text
close
```